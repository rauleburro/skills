---
name: auto-review-dispatch
description: Use when the user asks for a code review of their current work — phrases like "revisá mi PR", "quiero un review imparcial", "lanzá un review con contexto limpio", "code review this", "review before merging", "que otro Codex revise esto", or after they finish a chunk of work and mention merge/PR/review/listo. Auto-detects branch, PR number, base commit, modified files, and project stack from AGENTS.md, then dispatches a fresh-context code review subagent with the full brief pre-filled. Saves the user from typing out context every time they want a review.
---

# Auto Review Dispatch

The user wants a code review by a subagent with fresh context (no bias from the current conversation). This skill does the grunt work of detecting *what to review* and *what the PR is about* automatically, then launches an independent review subagent directly so the user just says "revisá mi PR" and gets a proper review.

## The one-line summary

Gather git + PR + AGENTS.md context in parallel → fill the direct review brief → dispatch an independent review subagent → relay findings with an action plan.

## Why this exists

Last time the user asked "revisá mi PR", the assistant manually constructed a 40-line brief with branch paths, stack notes, commit hashes, and domain context. That works once, but it's tedious and easy to miss pieces (e.g. forgetting to mention the worktree path, or that the stack is React Native not plain React). This skill makes that automatic and consistent.

## Flow

### Step 1 — Gather context in parallel

Run these Bash commands in a single message (parallel tool calls):

```bash
git branch --show-current
git rev-parse HEAD
git status --short                                    # uncommitted changes (see Red flags)
gh pr list --head "$(git branch --show-current)" --json number,title,body,url,isDraft,mergeStateStatus 2>/dev/null
```

Then determine the base branch. Try, in order:
1. `origin/main` if it exists
2. `origin/develop` if it exists
3. The merge-base of `HEAD` with the tracking branch

Once you have the base, gather:

```bash
git log <base>..HEAD --oneline
git log <base>..HEAD --format="%H%n%s%n%b%n---"    # full commit bodies
git diff <base>..HEAD --stat
git merge-base HEAD <base>                          # for BASE_SHA
```

And read `AGENTS.md` files:
- Worktree root (walk up from cwd until `.git` is found — if a `.Codex/worktrees/` path is present, that's the worktree root, NOT the main repo root)
- Any directory-level AGENTS.md covering modified files (optional, only if Step 3 needs it)

If the branch has zero commits ahead of base, stop and tell the user there's nothing to review.

### Step 2 — Compose the brief

Fill the direct review brief placeholders:

- **`{WHAT_WAS_IMPLEMENTED}`** — Synthesize: PR title (if it exists) + the first commit's subject + 1-line summary of modified areas. Example: *"Fix for SubscriptionContext useCallback dep — adds regression tests in `__tests__/contexts/` and touches `eas.json`."*
- **`{PLAN_OR_REQUIREMENTS}`** — Priority order: (a) PR body, (b) full commit bodies concatenated, (c) branch name inference ("Branch `fix/TP-104-...` suggests a fix for the described bug"). If the PR body references a ticket (TP-XXX, PROJ-NNN), mention it but don't fetch unless the user asked.
- **`{BASE_SHA}`** — `git merge-base HEAD <base>` output.
- **`{HEAD_SHA}`** — `git rev-parse HEAD` output.
- **`{DESCRIPTION}`** — Compact summary: `<N> commits, <M> files, <overall intent>`.

### Step 3 — Extract project context from AGENTS.md

From the worktree-root AGENTS.md, extract and pass to the subagent so it evaluates against the right conventions:

- Stack (language, framework, package manager — `bun` vs `npm` matters)
- Testing conventions (target coverage, test file paths)
- Naming conventions (snake_case DB vs camelCase TS, path aliases)
- Any lines flagged `IMPORTANT` or `Gotchas`
- Release/deploy policies if the changes touch version/config files

Append to the brief under `## Project context`.

### Step 4 — Ask the user about specific concerns (optional but valuable)

Before dispatching, ask briefly:

> "¿Querés que preste atención especial a algo? (e.g. manejo de errores, performance, API changes). Si no, procedo con review general."

If the user replies with concerns, append to the brief under `## Specific concerns from requester`. If they skip or say "general", proceed.

Skip this step if the user's original message already listed specific concerns (e.g. "revisá especialmente el manejo de errores del nuevo servicio") — you already have them.

### Step 5 — Dispatch

Use `references/fallback-brief.md` as the direct review brief template. Dispatch an independent review subagent with that filled prompt. If the subagent/Task tool is not available at all (for example you are already running as a subagent), fill the same brief and apply it inline; announce this limitation at the top of the output so the user knows the review is not from a fresh-context subagent.

### Step 6 — Relay findings with an action plan

When the subagent returns, present the report verbatim first (don't rewrite the reviewer's words), then add:

```markdown
## Action plan

- 🔴 **Blockers** (must fix): [list Critical issues with 1-line summaries]
- 🟡 **Should fix**: [list Important issues]
- 🔵 **Nice to have**: [list Minor issues]

**Minimum path to merge:** [which subset of fixes is required to unblock]

¿Cómo querés proceder? (A) solo blockers, (B) blockers + should-fix, (C) todo, (D) mergeá como está e ignorá, (E) otro.
```

This lets the user pick the scope without re-reading all the issues.

## Language

Mirror the user's language. If they asked in Spanish, your framing/action-plan is in Spanish. The subagent's report may come back in mixed language — don't translate it, just relay.

## Red flags

- **Don't fabricate `{PLAN_OR_REQUIREMENTS}`** when signal is weak (empty PR body, vague commits like "wip"). Ask the user: *"¿Qué debería estar implementado? No tengo señal clara del PR ni de los commits."*
- **Don't skip the AGENTS.md read** — it's the single biggest source of project conventions. Without it, the reviewer flags false positives (e.g. "should use npm" when the project uses bun).
- **Don't run review on zero-commit branches** — report that and exit.
- **Don't guess the base branch** — if `origin/main` and `origin/develop` both exist and the default is ambiguous, ask.
- **Don't paste the raw `git diff` into the brief** — the subagent will read the diff itself via the SHAs.
- **Don't ignore uncommitted changes** — if `git status --short` shows output, the diff the reviewer sees (via BASE_SHA..HEAD_SHA) misses those files. Either stash/commit them first, or mention them explicitly in the brief under a `## Uncommitted working-tree changes` section so the reviewer knows they're in scope.

## When NOT to use this skill

- User pastes a snippet inline and asks "any issues?" — answer directly, no subagent.
- User asks for a review of someone else's repo/PR — different scope (use `code-review:code-review` if they want a GitHub comment).
- User wants the review posted to the PR as a comment — use `code-review:code-review`.
- User is mid-implementation and just wants a sanity check on a single function — direct answer is faster.

## Example

**User:** "revisá mi PR antes de mergear"

**Assistant:**
1. Runs parallel git/gh commands.
2. Detects: branch `fix/TP-104-subscription-context-usecallback-deps`, PR #52, 3 commits, 4 files modified, AGENTS.md says React Native + Expo + bun.
3. Asks: "¿Preocupaciones específicas? Si no, general."
4. User: "mirá sobre todo las deps del useCallback".
5. Dispatches an independent review subagent with the filled brief + that concern.
6. Subagent returns Strengths/Critical/Important/Minor/Assessment.
7. Assistant relays report + action plan options.

## Related skills

- `code-review:code-review` — automated review that comments on the PR in GitHub (different workflow)
