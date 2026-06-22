# What the evaluator checks

`scripts/eval_runner.py` runs the **review phase only** (the cheap, deterministic part of the loop)
against each fixture and scores three things:

### 1. Recall per R
For every finding in `expected.json`, does the reviewer's `verdict.json` contain a finding with the
**same `r`** whose `summary` or `file` contains the expected `matcher` (case-insensitive substring)?
`recall = matched / expected`. A correct reviewer scores `100%`.

### 2. False positives (clean fixture)
For `pr-005-clean-pr` (no expected findings), any `blocking`/`major` finding the reviewer raises is a
false positive. The target is `0`. This is the guardrail against a reviewer that invents problems.

### 3. Verdict match
`verdict.approved` must equal `expected.expected_verdict`. This confirms the reviewer applies the
binary verdict rule correctly: approve iff zero `blocking`/`major`. Note `pr-002` expects
`approved: true` *with* a `minor` finding present — proving minor findings are reported but do not block.

A fixture **passes** when `recall == 100%`, `verdict_ok`, and `false_pos == 0`. The runner exits
non-zero if any fixture fails, so it can gate CI.

## Known limitations

- **Substring matching is fuzzy.** A reviewer may phrase a real finding in words that don't contain
  the chosen `matcher` (e.g. "unbounded read" vs the matcher `limit`). A MISS here can mean a wording
  mismatch, not a missed issue. When tuning, read the reviewer's `summary` and either broaden the
  matcher or accept the wording. Lean on the rubric's own vocabulary for matchers.
- **Review quality ≠ loop correctness.** This evaluator does not run the plan/implement/re-review
  loop. The full loop is validated by running the skill on a sandbox repo (see below).

## Validating the full loop (manual, end-to-end)

The review-quality eval above is automatable. The complete review→plan→fix→re-review loop is
validated by running the skill itself:

1. Create a throwaway git repo and commit the *base* state, then apply a fixture's `diff.patch` on a
   branch (e.g. `git checkout -b test-pr && git apply .../pr-006-mixed-multi-R/diff.patch && git add -A && git commit`).
2. Invoke the skill on that branch.
3. Confirm: it iterates, auto-commits one commit per iteration, converges to `approved` within
   `MAX_ITERATIONS`, writes `summary.md`, and (against a real test PR) posts the GitHub comment.

`pr-006` is the recommended fixture for this because it spans all four gates and forces at least one
fix iteration.
