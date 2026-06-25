#!/usr/bin/env python3
"""Benchmark the 4R reviewer against a golden set, with variance and a baseline comparison.

Why this exists (grounded in the literature):
  * LLM reviewers are limited mostly by PRECISION, not recall — high false-positive rates are what
    make a reviewer useless in practice (SWR-Bench, arXiv:2509.01494). So we measure false positives
    on cases where we KNOW the answer is "clean", not just recall on seeded bugs.
  * LLM output is non-deterministic even at temperature 0; single-run scores swing several points
    (arXiv:2602.07150, scale.com/blog/smoothing-out-llm-variance). So we run each fixture K times and
    report mean ± stddev.
  * A skill's value is its LIFT over no skill. So we run two conditions — `with-skill` (the full 4R
    rubric + reviewer prompt) and `baseline` (a generic "review this diff" prompt that emits the same
    JSON) — and compare (the skill-creator with/without pattern).

Metrics (per condition, mean ± stddev across K runs over all fixtures):
  * recall            — of the seeded `findings`, how many the reviewer caught (by R + matcher).
  * verdict_accuracy  — approved == expected_verdict.
  * false_positive_rate — on fixtures whose correct verdict is "approve", the fraction of runs that
                          raised any blocking/major finding (the precision proxy).
  * forbidden_hit_rate  — fraction of runs that raised an explicitly-forbidden finding (the traps).
  * verdict_consistency — per fixture, fraction of runs agreeing with that fixture's modal verdict,
                          averaged (1.0 = perfectly stable).

Usage:
  scripts/benchmark.py                       # golden set = dataset/, K=3, both conditions
  scripts/benchmark.py --runs 5 --workers 8
  scripts/benchmark.py --conditions with-skill   # skip the baseline
  scripts/benchmark.py --dataset dataset --out ../code-review-4r-workspace/iteration-1
"""
import argparse
import json
import statistics
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
RUBRIC = SKILL_DIR / "reference" / "4r-rubric.md"
REVIEWER = SKILL_DIR / "reference" / "reviewer-agent.md"

VERDICT_SHAPE = (
    'Output ONLY a single valid JSON object (no prose, no markdown fences) of the form:\n'
    '{"approved": <bool>, "findings": [{"r": "Risk|Readability|Reliability|Resilience", '
    '"severity": "blocking|major|minor|nit", "file": "<path>", "line": <int|null>, '
    '"summary": "<one sentence>"}]}\n'
    'Set "approved" to true if and only if there are zero blocking and zero major findings.'
)


def prompt_with_skill(diff: str) -> str:
    return (f"{REVIEWER.read_text()}\n\n---\nEVALUATION MODE: do not write files. {VERDICT_SHAPE}\n\n"
            f"# Rubric\n{RUBRIC.read_text()}\n\n# Diff under review\n```diff\n{diff}\n```\n")


def prompt_baseline(diff: str) -> str:
    # Deliberately generic: a competent reviewer with NO 4R rubric. Isolates the rubric's contribution.
    return ("You are a senior software engineer doing a code review of the diff below. Identify the "
            f"real problems. {VERDICT_SHAPE}\n\n# Diff under review\n```diff\n{diff}\n```\n")


def extract_json(text: str):
    depth, start, candidate = 0, None, None
    for i, ch in enumerate(text):
        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}" and depth > 0:
            depth -= 1
            if depth == 0:
                candidate = text[start:i + 1]
    if candidate is None:
        return None
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        return None


def run_claude(prompt: str, model: str, attempts: int = 2) -> str:
    """Run the review once, retrying on a transient failure/empty output (matters at high --runs,
    where a single rate-limited call would otherwise tank a fixture's score)."""
    for _ in range(attempts):
        try:
            p = subprocess.run(["claude", "-p", prompt, "--model", model],
                               capture_output=True, text=True, timeout=600)
        except FileNotFoundError:
            sys.exit("error: `claude` CLI not found on PATH.")
        except subprocess.TimeoutExpired:
            continue
        if p.returncode == 0 and p.stdout.strip():
            return p.stdout
    return ""


def score_run(expected: dict, verdict: dict) -> dict:
    """Score one reviewer output against one fixture's ground truth."""
    exp = expected.get("findings", [])
    forb = expected.get("forbidden", [])
    act = verdict.get("findings", []) if verdict else []

    def matches(af, spec):
        m = spec["matcher"].lower()
        return af.get("r") == spec["r"] and (
            m in str(af.get("summary", "")).lower() or m in str(af.get("file", "")).lower())

    recall = (sum(any(matches(af, ef) for af in act) for ef in exp) / len(exp)) if exp else None
    forbidden_hit = any(matches(af, fb) for fb in forb for af in act) if forb else False
    # false positive: this fixture should be approved, but a blocking/major was raised.
    is_approve_case = bool(expected.get("expected_verdict"))
    fp = is_approve_case and any(af.get("severity") in ("blocking", "major") for af in act)
    verdict_ok = verdict is not None and bool(verdict.get("approved")) == is_approve_case
    return {"recall": recall, "verdict_ok": verdict_ok, "false_positive": fp,
            "forbidden_hit": forbidden_hit, "is_approve_case": is_approve_case,
            "parsed": verdict is not None, "approved": bool(verdict.get("approved")) if verdict else None}


def mean_std(xs):
    xs = [x for x in xs if x is not None]
    if not xs:
        return None, None
    return statistics.mean(xs), (statistics.stdev(xs) if len(xs) > 1 else 0.0)


def aggregate(per_run, fixtures, runs):
    """per_run: list of (fixture_name, run_idx, score dict). Returns the condition summary."""
    fixtures_by_name = {f["name"]: f for f in fixtures}

    # First reduce each benchmark repetition to one suite-level value. Only then compute
    # mean/stddev across K runs, so a metric's variance reflects run-to-run instability of
    # the whole suite rather than mixing fixture-level and run-level samples.
    suite_recalls = []
    suite_verdicts = []
    suite_fps = []
    suite_forbids = []
    suite_parsed = []
    for run_idx in range(runs):
        run_scores = [(n, s) for n, r, s in per_run if r == run_idx]
        if not run_scores:
            continue

        expected_findings = sum(len(fixtures_by_name[n].get("findings", [])) for n, _ in run_scores)
        caught_findings = sum(s["recall"] * len(fixtures_by_name[n].get("findings", []))
                              for n, s in run_scores if s["recall"] is not None)
        suite_recalls.append(caught_findings / expected_findings if expected_findings else None)

        suite_verdicts.append(sum(1.0 if s["verdict_ok"] else 0.0 for _, s in run_scores) /
                              len(run_scores))

        approve_scores = [s for _, s in run_scores if s["is_approve_case"]]
        suite_fps.append(sum(1.0 if s["false_positive"] else 0.0 for s in approve_scores) /
                         len(approve_scores) if approve_scores else None)

        forbidden_scores = [(n, s) for n, s in run_scores if fixtures_by_name[n].get("forbidden")]
        suite_forbids.append(sum(1.0 if s["forbidden_hit"] else 0.0
                                 for _, s in forbidden_scores) / len(forbidden_scores)
                             if forbidden_scores else None)

        suite_parsed.append(sum(1.0 if s["parsed"] else 0.0 for _, s in run_scores) /
                            len(run_scores))

    # verdict consistency: per fixture, agreement with that fixture's modal verdict.
    cons = []
    for f in fixtures:
        verds = [s["approved"] for n, _, s in per_run if n == f["name"] and s["approved"] is not None]
        if verds:
            modal = max(set(verds), key=verds.count)
            cons.append(verds.count(modal) / len(verds))

    rec_m, rec_s = mean_std(suite_recalls)
    fp_m, fp_s = mean_std(suite_fps)
    forbid_m, forbid_s = mean_std(suite_forbids)
    verdict_m, verdict_s = mean_std(suite_verdicts)
    parsed_m, _ = mean_std(suite_parsed)
    return {
        "recall": {"mean": rec_m, "std": rec_s},
        "verdict_accuracy": {"mean": verdict_m, "std": verdict_s},
        "false_positive_rate": {"mean": fp_m, "std": fp_s,
                                "n_cases": sum(1 for f in fixtures if f.get("expected_verdict"))},
        "forbidden_hit_rate": {"mean": forbid_m, "std": forbid_s,
                               "n_cases": sum(1 for f in fixtures if f.get("forbidden"))},
        "parse_rate": {"mean": parsed_m},
        "verdict_consistency": {"mean": (statistics.mean(cons) if cons else None)},
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default=str(SKILL_DIR / "dataset"))
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--model", default="opus")
    ap.add_argument("--conditions", default="with-skill,baseline")
    ap.add_argument("--out", default=str(SKILL_DIR.parent / "code-review-4r-workspace" / "benchmark"))
    args = ap.parse_args()

    fixtures = []
    for d in sorted(Path(args.dataset).glob("pr-*")):
        if (d / "diff.patch").exists() and (d / "expected.json").exists():
            exp = json.loads((d / "expected.json").read_text())
            fixtures.append({"name": d.name, "diff": (d / "diff.patch").read_text(), **exp})
    if not fixtures:
        sys.exit(f"no fixtures found under {args.dataset}")

    conditions = [c.strip() for c in args.conditions.split(",")]
    builders = {"with-skill": prompt_with_skill, "baseline": prompt_baseline}

    # Build the full job list: (condition, fixture, run_idx)
    jobs = [(c, f, r) for c in conditions for f in fixtures for r in range(args.runs)]
    print(f"Running {len(jobs)} reviews "
          f"({len(fixtures)} fixtures × {args.runs} runs × {len(conditions)} conditions), "
          f"{args.workers} parallel, model={args.model}…", file=sys.stderr)

    def execute(job):
        cond, f, r = job
        out = run_claude(builders[cond](f["diff"]), args.model)
        verdict = extract_json(out)
        return (cond, f["name"], r, score_run(f, verdict))

    results = {c: [] for c in conditions}
    done = 0
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        for cond, name, r, s in ex.map(execute, jobs):
            results[cond].append((name, r, s))
            done += 1
            print(f"  [{done}/{len(jobs)}] {cond} {name} run{r}: "
                  f"recall={s['recall']} verdict_ok={s['verdict_ok']} fp={s['false_positive']}",
                  file=sys.stderr)

    summary = {c: aggregate(results[c], fixtures, args.runs) for c in conditions}

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    bench = {"config": {"runs": args.runs, "model": args.model, "fixtures": len(fixtures),
                        "conditions": conditions},
             "summary": summary,
             "per_fixture": {c: [{"fixture": n, "run": r, **s} for n, r, s in results[c]]
                             for c in conditions}}
    (out_dir / "benchmark.json").write_text(json.dumps(bench, indent=2))
    (out_dir / "benchmark.md").write_text(render_md(bench, fixtures))
    print(f"\nWrote {out_dir/'benchmark.json'} and {out_dir/'benchmark.md'}", file=sys.stderr)
    return 0


def pct(d):
    if d is None or d.get("mean") is None:
        return "—"
    m = d["mean"] * 100
    s = d.get("std")
    return f"{m:.0f}% ± {s*100:.0f}" if s is not None else f"{m:.0f}%"


def render_md(bench, fixtures) -> str:
    cfg = bench["config"]
    s = bench["summary"]
    conds = cfg["conditions"]
    lines = [
        "# Code Review 4R — Benchmark", "",
        f"- **Model:** {cfg['model']}  ·  **Runs per fixture:** {cfg['runs']}  ·  "
        f"**Fixtures:** {cfg['fixtures']}  ·  **Conditions:** {', '.join(conds)}",
        "- Each metric is mean ± stddev across runs. Higher is better except "
        "**false-positive rate** and **forbidden-hit rate** (lower is better).", "",
        "## Headline metrics", "",
        "| Metric | " + " | ".join(conds) + " |",
        "|---|" + "---|" * len(conds),
    ]
    rows = [
        ("Recall (seeded findings) ↑", "recall"),
        ("Verdict accuracy ↑", "verdict_accuracy"),
        ("Verdict consistency ↑", "verdict_consistency"),
        ("False-positive rate ↓", "false_positive_rate"),
        ("Forbidden-hit rate ↓", "forbidden_hit_rate"),
        ("JSON parse rate ↑", "parse_rate"),
    ]
    for label, key in rows:
        lines.append(f"| {label} | " + " | ".join(pct(s[c].get(key)) for c in conds) + " |")
    lines += ["", "## Per-fixture verdict (modal across runs)", "",
              "| Fixture | expected | " + " | ".join(conds) + " |",
              "|---|---|" + "---|" * len(conds)]
    for f in fixtures:
        exp_v = "approve" if f.get("expected_verdict") else "reject"
        cells = []
        for c in conds:
            verds = [r["approved"] for r in bench["per_fixture"][c] if r["fixture"] == f["name"]]
            verds = [v for v in verds if v is not None]
            if not verds:
                cells.append("?")
            else:
                modal = max(set(verds), key=verds.count)
                cells.append("approve" if modal else "reject")
        lines.append(f"| {f['name']} | {exp_v} | " + " | ".join(cells) + " |")
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    sys.exit(main())
