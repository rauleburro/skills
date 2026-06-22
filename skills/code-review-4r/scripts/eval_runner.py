#!/usr/bin/env python3
"""Score the 4R reviewer against a dataset fixture.

For a fixture directory containing `diff.patch` and `expected.json`, this runs the *review phase*
headlessly (via the `claude` CLI), captures the reviewer's verdict, and compares it to the expected
findings. It measures, per fixture:

  * recall per R   — did the reviewer catch the seeded issues?
  * false positives — for a clean PR, did it stay quiet?
  * verdict match  — approved == expected_verdict?

This is the cheap, automatable check that the reviewer applies the rubric correctly. The full
review→plan→fix→re-review loop is validated by running the skill itself on a sandbox repo.

Usage:
  scripts/eval_runner.py dataset/pr-001-sql-injection
  scripts/eval_runner.py dataset/*            # score every fixture, print a table
  scripts/eval_runner.py dataset/pr-001-... --dry-run   # print the prompt, don't call claude
  scripts/eval_runner.py dataset/pr-001-... --model opus

expected.json schema:
  {
    "expected_verdict": false,            # what `approved` should be
    "findings": [
      {"r": "Risk", "severity": "blocking", "matcher": "sql"}   # matcher: case-insensitive
    ]                                                            # substring in summary OR file
  }
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
RUBRIC = SKILL_DIR / "reference" / "4r-rubric.md"
REVIEWER = SKILL_DIR / "reference" / "reviewer-agent.md"


def build_prompt(diff_text: str) -> str:
    rubric = RUBRIC.read_text()
    reviewer = REVIEWER.read_text()
    return f"""{reviewer}

---
You are running in evaluation mode. Instead of writing files, **respond with ONLY the verdict.json
object** described below — a single valid JSON object, no prose, no markdown fences.

# Rubric
{rubric}

# Diff under review
```diff
{diff_text}
```

Now output the verdict JSON object and nothing else.
"""


def extract_json(text: str):
    """Return the last balanced {...} object in text, parsed. None if not found."""
    depth = 0
    start = None
    candidate = None
    for i, ch in enumerate(text):
        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            if depth > 0:
                depth -= 1
                if depth == 0 and start is not None:
                    candidate = text[start : i + 1]
    if candidate is None:
        return None
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        return None


def run_review(prompt: str, model: str) -> str:
    try:
        proc = subprocess.run(
            ["claude", "-p", prompt, "--model", model],
            capture_output=True, text=True, timeout=600,
        )
    except FileNotFoundError:
        sys.exit("error: `claude` CLI not found on PATH (needed to run the review).")
    if proc.returncode != 0:
        sys.exit(f"error: claude exited {proc.returncode}\n{proc.stderr}")
    return proc.stdout


def score(expected: dict, verdict: dict) -> dict:
    exp_findings = expected.get("findings", [])
    act_findings = verdict.get("findings", []) if verdict else []

    matched = []
    for ef in exp_findings:
        m = ef["matcher"].lower()
        hit = any(
            af.get("r") == ef["r"]
            and (m in str(af.get("summary", "")).lower() or m in str(af.get("file", "")).lower())
            for af in act_findings
        )
        matched.append((ef, hit))

    recall = sum(1 for _, h in matched if h) / len(exp_findings) if exp_findings else 1.0
    # On a clean fixture (no expected findings), any blocking/major is a false positive.
    false_pos = (
        sum(1 for af in act_findings if af.get("severity") in ("blocking", "major"))
        if not exp_findings else 0
    )
    verdict_ok = verdict is not None and bool(verdict.get("approved")) == bool(expected.get("expected_verdict"))
    return {"recall": recall, "matched": matched, "false_pos": false_pos,
            "verdict_ok": verdict_ok, "act_count": len(act_findings)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("fixtures", nargs="+", help="fixture dir(s) with diff.patch + expected.json")
    ap.add_argument("--model", default="opus")
    ap.add_argument("--dry-run", action="store_true", help="print the prompt, do not call claude")
    args = ap.parse_args()

    all_pass = True
    for fx in args.fixtures:
        d = Path(fx)
        diff_p, exp_p = d / "diff.patch", d / "expected.json"
        if not diff_p.exists() or not exp_p.exists():
            print(f"  SKIP {d.name}: missing diff.patch or expected.json")
            continue
        prompt = build_prompt(diff_p.read_text())
        if args.dry_run:
            print(f"===== prompt for {d.name} =====\n{prompt}")
            continue

        expected = json.loads(exp_p.read_text())
        out = run_review(prompt, args.model)
        verdict = extract_json(out)
        if verdict is None:
            print(f"✗ {d.name}: could not parse a verdict JSON from the reviewer output")
            all_pass = False
            continue

        s = score(expected, verdict)
        ok = s["recall"] == 1.0 and s["verdict_ok"] and s["false_pos"] == 0
        all_pass = all_pass and ok
        mark = "✓" if ok else "✗"
        print(f"{mark} {d.name}: recall={s['recall']:.0%}  verdict_ok={s['verdict_ok']}  "
              f"false_pos={s['false_pos']}  (reviewer raised {s['act_count']} finding(s))")
        for ef, hit in s["matched"]:
            print(f"      [{'hit ' if hit else 'MISS'}] {ef['r']}/{ef['severity']} ~ '{ef['matcher']}'")

    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
