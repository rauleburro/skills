# Dataset — synthetic PRs for evaluating the 4R reviewer

Each fixture is a tiny, self-contained PR with **known, seeded issues** so we can measure whether the
reviewer applies the rubric correctly before trusting it on real code.

A fixture directory contains:

- `diff.patch` — a unified diff (a new file or change) with the seeded issue(s).
- `expected.json` — the ground truth: which findings should appear (by R + severity, matched by a
  case-insensitive substring) and what the overall verdict should be.

| Fixture | Gate exercised | Seeded issue | Expected verdict |
|---------|----------------|--------------|------------------|
| `pr-001-sql-injection` | Risk | `%`-formatted user id in SQL | ❌ changes requested (blocking) |
| `pr-002-magic-numbers` | Readability | unexplained `8.0` weight | ✅ approved (minor doesn't block) |
| `pr-003-missing-tests` | Reliability | new billing logic, no test | ❌ changes requested (major) |
| `pr-004-no-timeout` | Resilience | remote HTTP call, no timeout | ❌ changes requested (major) |
| `pr-005-clean-pr` | (control) | none — well-named, tested | ✅ approved (no findings) |
| `pr-006-mixed-multi-R` | all four | SQLi + magic + unbounded + no timeout | ❌ changes requested |
| `pr-007-safe-parameterized` | Risk precision trap | parameterized SQL query is safe | ✅ approved (forbid SQLi false positive) |
| `pr-008-named-constants` | Readability precision trap | weights extracted to named constants | ✅ approved (forbid magic-number false positive) |
| `pr-009-timeout-retry` | Resilience precision trap | HTTP call has timeout, retry/backoff, and tests | ✅ approved (forbid timeout/retry false positives) |
| `pr-010-hardcoded-secret` | Risk | hardcoded API key committed in source | ❌ changes requested (blocking) |
| `pr-011-swallowed-exception` | Reliability | payment-gateway exception swallowed as success | ❌ changes requested (major) |

`pr-005` is the most important negative case: a reviewer that flags it is producing **false
positives**, which trains the team to ignore the tool. `pr-006` is the comprehensive end-to-end
fixture — the same shape as the example in the source video.

## Running the evaluator

```bash
# score one fixture
scripts/eval_runner.py dataset/pr-001-sql-injection

# score all of them
scripts/eval_runner.py dataset/pr-*

# inspect the prompt without calling the model
scripts/eval_runner.py dataset/pr-001-sql-injection --dry-run
```

See `../evals/assertions.md` for exactly what is scored and the known limitations of substring
matching.

## Adding a fixture

1. Make a directory `pr-NNN-short-slug/`.
2. Write `diff.patch` (keep it small and focused on one or two gates).
3. Write `expected.json` with `expected_verdict` and the `findings` you expect, each with a `matcher`
   that is highly likely to appear in a correct reviewer's wording (lean on the rubric's own terms:
   "sql", "magic", "timeout", "limit", "test").
