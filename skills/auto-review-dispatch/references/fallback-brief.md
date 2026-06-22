# Fallback brief template

Use this template to dispatch a direct independent code-review subagent.

## When to use this fallback

Use this template in both cases:

1. **Normal path** — you have access to subagent dispatch, so you launch a fresh-context reviewer directly.
2. **Task tool not available** — you're running as a subagent yourself, and subagents don't inherit the Task tool. Further dispatch is impossible. You fill this template anyway and apply it *inline* — you become the reviewer. Announce the limitation at the top of the output so the user knows the review wasn't produced by a context-fresh subagent; suggest re-running from the parent session for a cleaner review.

## How to use

- **If you have subagent dispatch:** dispatch a code review subagent with a prompt built from this template. Replace the `{{...}}` variables with values from Step 1 of the parent skill.
- **If you don't have the Task tool (subagent context):** treat the filled template as your own instructions. Read the listed files, run the git commands, and produce the report yourself in the requested format. Include a one-line preface acknowledging the inlined review.

---

```
Review the branch/PR described below. Evaluate it impartially: look for bugs, inconsistencies with project conventions, and improvement opportunities. Don't assume the code is good — critique where criticism is warranted.

## Project context

**Worktree:** {{WORKTREE_PATH}}

**Stack:** {{STACK_FROM_CLAUDE_MD}}

**Project conventions from CLAUDE.md:**
{{CONVENTIONS_EXTRACT}}

## What to review

**Branch:** {{BRANCH_NAME}}
**Base:** {{BASE_BRANCH}} (SHA {{BASE_SHA}})
**Head SHA:** {{HEAD_SHA}}
**PR:** {{PR_URL_OR_NONE}}

**Commits ({{N_COMMITS}}):**
{{COMMIT_LIST_WITH_SUBJECTS}}

**Modified files ({{N_FILES}}):**
{{FILE_STAT}}

**What was implemented (from PR title + commits):**
{{WHAT_WAS_IMPLEMENTED}}

**Requirements / intent (from PR body or inferred):**
{{PLAN_OR_REQUIREMENTS}}

## Specific concerns from the requester

{{USER_CONCERNS_OR_GENERAL_REVIEW}}

## Questions to answer

Go into the worktree (`cd {{WORKTREE_PATH}}`) and inspect with git:

1. **Correctness of the main change** — does the fix/feature actually solve the stated problem? Are all the required parts present?
2. **Regression tests** — do any new tests actually exercise the changed behavior, or are they trivially passing?
3. **Scope creep** — are there changes in the diff that don't belong to the stated goal?
4. **Consistency with project conventions** (from CLAUDE.md) — naming, path aliases, package manager, test patterns, etc.
5. **Subtle bugs** — off-by-one, missed edge cases, dependency array issues in React hooks, async race conditions.
6. **Anything else suspicious** — unused imports, leftover console.logs, `any` types, TODO comments, swallowed errors.

## Report format

Respond in this structure:

**Verdict:** APPROVE / APPROVE_WITH_SUGGESTIONS / REQUEST_CHANGES

**Main change analysis:** [2-3 sentences on whether the core change is correct]

**Scope creep assessment:** [if applicable]

**Issues** (ordered by severity):
- 🔴 Blocker: [file:line] [issue] — [why it matters]
- 🟡 Should fix: [file:line] [issue] — [why]
- 🔵 Nice to have: [file:line] [issue] — [why]

**Strengths (2-3 specific wins):** [what's genuinely well done]

Be concise (~500 words max). If you find nothing wrong, say so clearly — don't invent issues.
```

---

## Notes for the skill

- Always pass the **worktree path absolute** so the subagent can `cd` there. Subagents don't inherit the parent's cwd reliably.
- Include the full list of commits so the subagent sees the scope breakdown, not just the final diff.
- Include CLAUDE.md conventions even if you have to truncate — project conventions prevent the biggest class of false positives ("should use npm" when the project uses bun, "should use camelCase" when the table is snake_case).
