---
name: pr-deep-review-agent
description: Launch a clean-context subagent to perform a deep pull request review. Use when the user asks to launch/run/spawn another agent for PR review, final approval review, clean-context code review, or a review that compares code against local documentation and official internet documentation before reporting whether the PR is approved or changes are required.
---

# PR Deep Review Agent

## Purpose

Launch one fresh subagent that reviews the current PR independently. The subagent must inspect code, tests, local docs, and official/current internet documentation for the technologies touched by the PR, then return a complete approval report.

## Workflow

1. Identify PR context locally:
   - Current working directory.
   - Current branch and HEAD SHA.
   - Base branch and PR number, using `gh pr view --json number,baseRefName,headRefName,url,title` when available.
   - Changed files, using `git diff --name-only origin/<base>...HEAD` or the closest available base.
2. Launch exactly one clean-context subagent with `spawn_agent`.
   - Use `agent_type: "explorer"` for read-only review.
   - Set `fork_context: false` unless the user explicitly asks to pass current conversation context.
   - Do not ask the subagent to modify files.
3. While the subagent runs, optionally gather non-overlapping local context only if useful. Do not duplicate the whole review.
4. Wait for the subagent when its result is needed for the user-facing answer.
5. Relay the report clearly, preserving verdict and severity.

## Subagent Prompt Template

Use this prompt, filling brackets with discovered values:

```text
You are a clean-context PR review agent. Do not modify files.

Repository: [absolute repo path]
PR: [PR number and URL if known]
Branch: [current branch]
HEAD: [HEAD SHA]
Base: [base branch]

Task:
Perform a deep review of this PR and decide whether it is APPROVED or CHANGES REQUESTED.

Required review scope:
1. Analyze the PR diff and the surrounding implementation code.
2. Analyze relevant tests and identify meaningful test gaps.
3. Read relevant local documentation in the repository and compare it to the implementation.
4. Research official/current internet documentation for external technologies or APIs used by the changed code. Prefer primary sources: official docs, official API references, standards, or upstream repos. Include source links in the report.
5. Identify mismatches between implementation, local docs, and official docs.
6. Identify security, data integrity, race condition, compatibility, and regression risks.
7. Identify what should NOT be changed or added if a requested/reviewed change would be unnecessary, risky, or out of scope.

Constraints:
- Read-only review only. Do not edit files, commit, push, or comment on GitHub.
- Do not rely only on prior conversation context. Rebuild facts from repo, PR metadata, local docs, and official docs.
- If internet access or GitHub access is unavailable, say exactly what could not be verified and lower confidence accordingly.
- Treat local tests passing as useful but not sufficient for approval.

Report format:
# PR Deep Review Report

## Verdict
APPROVED or CHANGES REQUESTED

## Confidence
High / Medium / Low, with one sentence why.

## Sources Checked
- Local files/docs inspected.
- Official internet docs inspected, with links.

## Findings
Group findings by severity:
- Blocking
- Should-fix
- Minor / Nits
- Test gaps
For each finding include: title, affected files/lines when possible, why it matters, evidence, and recommended action.

## Documentation Gaps
List mismatches between local docs and implementation or official docs.

## What Not To Do
List changes that should be avoided because they are unsafe, unnecessary, or out of scope.

## Validation Notes
Mention commands or checks run, if any, and their results.

## Final Recommendation
One concise paragraph stating whether the PR can merge or what must happen first.
```

## Review Standards

- Prefer correctness over politeness. Report real blockers even when CI passes.
- Separate verified facts from assumptions.
- Use severity strictly:
  - **Blocking**: merge would likely break production, create a security/access-control issue, corrupt data, or violate official API behavior.
  - **Should-fix**: important risk or maintainability issue that should be resolved before merge unless explicitly accepted.
  - **Minor / Nits**: low-risk polish, clarity, or cleanup.
  - **Test gaps**: missing coverage that matters; do not call every uncovered branch a gap.
- If no actionable issues are found, return `APPROVED` and still list sources checked and residual risks.

## Parent Agent Response

After the subagent returns:

- Summarize verdict first.
- List blocking/should-fix items, if any.
- Say whether the PR is approved.
- If the subagent found issues, ask or proceed according to the user's latest instruction; do not silently change files unless the user asked to correct them.
