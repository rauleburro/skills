---
name: code-review-4r
description: >
  Autonomous, looping code review for a finished PR using the 4R framework (Risk, Readability,
  Reliability, Resilience). Spawns clean-context agents — an Opus reviewer, an Opus fix-planner,
  and Sonnet implementers — and iterates review → plan → fix → re-review until the PR is approved,
  then posts a summary comment on the GitHub PR. Use this whenever the user finishes a PR or branch
  and says "review my PR", "code review", "revisá la PR", "revisá con 4R", "terminé la PR",
  "valida este branch antes de merge", or wants automated pre-review that fixes the small stuff so
  the human reviewer only has to look at what matters. Trigger it even when the user just says they
  are done with a branch and want it checked before merging.
---

# Code Review 4R — autonomous review loop

Run a finished PR through a self-correcting review loop so the human reviewer only spends time on
what actually matters. You are the **orchestrator** running in the main session. Each phase is done
by a **fresh subagent with clean context** — you hand it only file paths, never your own history.
This is deliberate: the reviewer must judge the code on its own, and the planner must work from the
written review, not from your reasoning.

The loop:

```
collect diff ─▶ Review (Opus) ─▶ approved? ──yes──▶ Finalize ─▶ PR comment
                   ▲                  │no
                   │                  ▼
                   └── Implement ◀── Plan (Opus)
                       (Sonnet) + auto-commit
```

## 0. Resolve target & prepare workspace

Run `scripts/collect_diff.sh` to capture what to review:

- **Current branch (default):** `scripts/collect_diff.sh` — diffs the checked-out branch against its
  merge-base with the base branch (`develop` if it exists, else `main`).
- **A specific PR:** `scripts/collect_diff.sh --pr <number>` — runs `gh pr checkout <number>` first so
  the branch is local and auto-commit works, then diffs.

The script writes everything under `docs/code-review-4r/<id>/` (`<id>` = sanitized branch name, or
`pr-<number>`): `diff.patch` and `meta.json` (title, base, head, changed files, added/removed LOC).
Read `meta.json` — note the PR number (if any) for the final comment, and the LOC stats for the
review context. Changed LOC and PR size are informational only and must never create a finding or
affect the verdict.

### Repository merge-policy override

Before starting the loop, inspect the repository's trusted review policy when present (for example
`.github/codex/prompts/code-review-4r.md`). If it explicitly declares the exact-head tests/coverage
quality gate as the only mandatory merge gate:

- record `merge_policy: "coverage-only"` and the exact-head quality-gate evidence in `meta.json`;
- run a single report-only review — do not enter Plan/Implement, modify files, or auto-commit;
- keep 4R findings as advisory;
- mark the PR approved when that exact-head quality gate passed, even when advisory P0/P1 or
  blocking/major findings are reported;
- request changes only when the mandatory test/coverage gate is missing or failed.

Set `MAX_ITERATIONS=4`. The loop is bounded so a non-converging review can never run forever.

## 1. Review (clean-context Opus)

For iteration `N` (starting at 1), spawn one subagent with the **Agent tool**, `model: "opus"`,
`subagent_type: general-purpose`. Build its prompt from `reference/reviewer-agent.md`, and pass it
**only these paths** (it reads them itself — do not paste contents into your own context):

- the diff: `docs/code-review-4r/<id>/diff.patch`
- the rubric: `<skill-dir>/reference/4r-rubric.md`
- the repository review policy, when present
- where to write: `docs/code-review-4r/<id>/iteration-<N>/review.md` and `.../verdict.json`

When it returns, **read only `verdict.json`** — not `review.md`. Keeping the reviewer's prose out of
your context is what makes the next review independent.

`verdict.json` contract (defined in the rubric):

```json
{ "approved": false,
  "findings": [ {"r":"Risk","severity":"blocking","file":"db.py","line":42,"summary":"..."} ] }
```

## 2. Gate

- `merge_policy == "coverage-only"` → do not run Plan/Implement. Finalize after the single
  report-only review; exact-head quality-gate status controls approval.
- `approved == true` (no `blocking` or `major` findings remain) → go to **Finalize** (§5).
- Otherwise, if `N == MAX_ITERATIONS` → go to **Finalize** and clearly mark the unresolved findings
  as residual (do not loop past the cap).
- Otherwise → continue to Plan.

## 3. Plan the fixes (clean-context Opus)

Spawn a subagent with the **Agent tool**, `model: "opus"`, `subagent_type: general-purpose`, prompt
from `reference/planner-agent.md`. Pass it only:

- the review: `docs/code-review-4r/<id>/iteration-<N>/review.md`
- where to write: `docs/code-review-4r/<id>/iteration-<N>/fix-plan.md`

The plan addresses every `blocking`/`major` finding (and `minor` when cheap) as small, ordered,
test-first steps.

## 4. Implement (clean-context Sonnet) + auto-commit

Spawn implementer subagent(s) with the **Agent tool**, `model: "sonnet"`,
`subagent_type: general-purpose`, prompt from `reference/implementer-agent.md`. Pass only:

- the plan: `docs/code-review-4r/<id>/iteration-<N>/fix-plan.md`
- where to write its report: `docs/code-review-4r/<id>/iteration-<N>/impl-report.md`

The implementer modifies the working tree following TDD (failing test first, then the fix). Run
several in parallel **only** when the plan's steps touch disjoint files; if they could collide, run
one. Use `isolation: "worktree"` only when parallel implementers would otherwise conflict.

When implementers finish, **you** commit (they don't), so commit scope stays controlled — one commit
per iteration, **no push** (push/merge stays a human decision):

```bash
git add -A && git commit -m "fix(review-4r): iteration <N> — <one-line summary of what was fixed>"
```

Then increment `N` and go back to **§1 (Review)** with a fresh reviewer.

## 5. Finalize

Aggregate every iteration into `docs/code-review-4r/<id>/summary.md`. ALWAYS use this structure:

```markdown
# Code Review 4R — <id>

**Verdict:** ✅ Approved after N iteration(s)   <!-- or: ⚠️ N findings unresolved (hit iteration cap) -->

## TL;DR for the human reviewer
<2–4 sentences: what the loop already handled, and the 1–2 spots — if any — that still need human judgment>

## Findings & resolution
| # | R | Severity | File:line | Finding | Status |
|---|---|----------|-----------|---------|--------|
| 1 | Risk | blocking | db.py:42 | SQL built by string interpolation | ✅ Fixed (iter 1) |
...

## What changed
- <commit subject per iteration, + one line each>

## Residual / needs human judgment
- <anything left, or "None — all blocking/major findings resolved.">
```

Then post it on the PR:

```bash
scripts/post_github_summary.sh <id>            # uses the current branch's PR
scripts/post_github_summary.sh <id> --pr <n>   # explicit PR number
```

If no PR exists yet, the script says so — tell the user the summary is ready locally and they can
open the PR and re-run the post step.

Finally, report to the user in chat (keep it short — detail lives in `summary.md`): the verdict,
iterations run, count of findings fixed by R, and any residual that needs them.

## Notes

- **Why clean context per phase.** Reusing one agent across review/plan/fix lets the writer grade its
  own work. Fresh subagents that see only the handed-off file are the same principle as a separate
  reviewer with no stake in the code.
- **The gate is objective on purpose.** "Approved" = zero `blocking`/`major` in `verdict.json`. Without
  a binary gate an AI loop can oscillate; `MAX_ITERATIONS` is the backstop.
- **Validate the flow before trusting it.** `dataset/` holds synthetic PRs with known issues and
  `scripts/eval_runner.py` scores whether the reviewer catches them. See `evals/assertions.md`.
