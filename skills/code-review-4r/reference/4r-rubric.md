# The 4R rubric

Four quality gates a change must pass. The point is to apply criteria **defined in advance** —
not to invent opinions per PR. A finding must be a real, defensible problem in *this diff*, with a
concrete `file:line`. When in doubt whether something is a problem, it is a `nit`, not a `blocking`.

## The four gates

### R1 — Risk
Could this change hurt us in production or open a security hole?
- Injection: SQL/again any query or command built by string interpolation/concatenation of input
  (e.g. an f-string `f"... {user_value} ..."` reaching a SQL/shell/eval sink) → `blocking`.
- Secrets, tokens, or keys hardcoded or logged → `blocking`.
- Touches a sensitive zone (auth, payments, data deletion, migrations) without guardrails → `major`.
- Can break prod: unhandled new failure mode on a hot path, breaking API/schema change → `major`.

### R2 — Readability
Can the next person understand this without archaeology?
- **Complexity budget**: a function/branch nest that blew up in size or depth ("ball of mud") → `major`/`minor`.
- **Magic numbers/values**: a literal carrying meaning (a threshold like `8.0`, a limit, a timeout)
  passed with no named constant and no comment → `minor` (`major` if it drives a security/limit decision).
- Misleading or non-descriptive names, dead code, copy-paste blocks → `minor`/`nit`.

### R3 — Reliability
Is it actually tested and does it handle the unhappy path?
- **Vanity coverage**: tests that execute lines but assert nothing meaningful, or no test at all for
  new behavior → `major`.
- Edge cases not explicit (empty/null, boundary, duplicate, unicode) → `minor`/`major`.
- Errors swallowed or not handled; results not validated → `major`.
- **Unbounded query**: a DB/collection read that iterates all rows with no `LIMIT`/ops-limit/pagination
  → `major` (can OOM or melt the DB under real data).

### R4 — Resilience
What happens when a dependency fails or is slow?
- **No timeout** on a costly/remote operation (HTTP, DB, RPC) → `major` (one slow call cascades into outage).
- No retry / no backoff on a transient-failure-prone call where it matters → `minor`/`major`.
- No graceful degradation: a non-critical dependency failure takes down the whole path → `major`.
- No observability: a new failure path with no log/metric to diagnose it → `minor`.

## PR size budget
The ideal human review unit is **200–400 changed LOC**; **600 is the hard ceiling**. Read the LOC
stats from `meta.json`. Over 400 → add one `minor` finding suggesting a split; over 600 → `major`.
This is not a code defect but a reviewability defect, and it is real.

## Severity & verdict

| Severity | Meaning | Blocks approval? |
|----------|---------|------------------|
| `blocking` | Must not merge: security hole, prod-breaker, data loss. | Yes |
| `major` | Should fix before merge: missing tests, no timeout, unbounded query. | Yes |
| `minor` | Worth fixing; won't block. | No |
| `nit` | Style/preference. | No |

**Verdict rule:** `approved == true` if and only if there are **zero `blocking` and zero `major`**
findings. `minor`/`nit` are reported but do not block.

## verdict.json contract
Emit exactly this shape (the orchestrator reads only this file to decide the loop):

```json
{
  "approved": false,
  "summary": "one sentence overall",
  "findings": [
    {
      "id": 1,
      "r": "Risk",
      "severity": "blocking",
      "file": "src/db.py",
      "line": 42,
      "summary": "SQL query built via f-string interpolation of ttl_boost_flow — SQL injection.",
      "fix_hint": "Use a parameterized query / bound parameters."
    }
  ]
}
```

`r` ∈ `Risk | Readability | Reliability | Resilience`. `severity` ∈ `blocking | major | minor | nit`.
Always include `file` and `summary`; include `line` and `fix_hint` whenever you can.
