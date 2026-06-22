---
name: create-pr
description: >
  Creates a GitHub Pull Request after validating that tests, linter, and coverage pass. Pushes the branch,
  generates an English PR title and description from the commits, and integrates with Jira (links the ticket,
  updates status). Use this skill when the user says "create PR", "crear PR", "open PR", "push and create PR",
  "make a pull request", "abre un PR", "sube el PR", "/create-pr", or any variation of wanting to submit their
  work as a pull request. Also triggers when the user says they're done with a task and want to send it for review.
  Works with any project stack (Django, Next.js, Node, etc.).
---

# Create PR Skill

Automates the full flow from local branch to an open GitHub Pull Request, ensuring quality gates pass before anything gets pushed.

## Why this flow matters

Pushing code that breaks tests or lint wastes reviewers' time and clogs CI. This skill runs validations locally first, so the PR arrives clean. It also keeps Jira in sync automatically — no context switching to update ticket status.

## Flow overview

```
1. Detect project stack  →  2. Run lint + tests + coverage
         |                              |
         v                              v (all pass?)
3. Push branch           →  4. Create PR (English, linked to Jira)
         |
         v
5. Update Jira → "Code Review"
```

If any validation fails, stop and help the user fix the issue before retrying. Never push code that doesn't pass.

---

## Phase 1: Pre-flight checks

Before running any validations, gather context:

### 1.1 Branch and commit analysis
```bash
# Current branch (must not be main/master)
git branch --show-current

# Base branch (usually main or master)
git remote show origin | grep 'HEAD branch'

# Uncommitted changes — warn the user if any exist
git status --short

# All commits since diverging from base
git log <base>..HEAD --oneline

# Full diff for PR description
git diff <base>...HEAD --stat
```

If on `main`/`master`, stop and tell the user they need to be on a feature branch.
If there are uncommitted changes, ask the user if they want to commit first.

### 1.2 Extract Jira ticket from branch name
Parse the branch name for a Jira key pattern (`[A-Z]+-\d+`):
- `feature/IRB-365-restrict-payment-filter` → `IRB-365`
- `fix/PROJ-42-login-bug` → `PROJ-42`
- `IRB-100-some-feature` → `IRB-100`

If no ticket ID found, ask the user if there's a Jira ticket to link.

### 1.3 Detect project stack
Look for configuration files to determine what commands to run:

| File present | Stack | Lint command | Test command | Coverage |
|---|---|---|---|---|
| `docker-compose*.yml` + `manage.py` | Django (Docker) | `docker compose exec web flake8` or project linter | `docker compose exec web python manage.py test` | `docker compose exec web coverage run ... && coverage report` |
| `manage.py` (no Docker) | Django | `flake8` or project linter | `python manage.py test` | `coverage run ... && coverage report` |
| `package.json` + `next.config.*` | Next.js | `npm run lint` | `npm run test -- --coverage` | from test output |
| `package.json` | Node/React | `npm run lint` | `npm run test` | `npm run test -- --coverage` |
| `Cargo.toml` | Rust | `cargo clippy` | `cargo test` | `cargo tarpaulin` |
| `go.mod` | Go | `golangci-lint run` | `go test ./...` | `go test -cover ./...` |

Check `package.json` scripts, `Makefile`, `docker-compose*.yml`, and project README/AGENTS.md for project-specific commands. Project-specific commands always take precedence over defaults.

---

## Phase 2: Quality gates

Run validations sequentially — stop at first failure.

### 2.1 Linter
Run the detected lint command. If it fails:
- Show the errors to the user
- Offer to fix them
- Do NOT proceed to tests until lint passes

### 2.2 Tests
Run the detected test command. If it fails:
- Show which tests failed
- Offer to investigate and fix
- Do NOT proceed until all tests pass

### 2.3 Coverage check
Run coverage and parse the output for the total percentage. Minimum threshold: **80%**.

If below 80%:
- Show the coverage report
- Identify uncovered files/functions
- Offer to write additional tests
- Do NOT proceed until coverage meets the threshold

Report results to the user:
```
Lint: PASS
Tests: PASS (42 passed, 0 failed)
Coverage: 87% (minimum: 80%)
```

---

## Phase 3: Push and create PR

### 3.1 Push the branch
```bash
git push -u origin <branch-name>
```

If the push fails (e.g., rejected), diagnose and help the user resolve it.

### 3.2 Fetch Jira ticket details
If a Jira key was found in Phase 1, fetch the ticket to enrich the PR description:
```
mcp__atlassian__jira_get_issue(issue_key)
```
Extract: title, description summary, and acceptance criteria.

### 3.3 Create the PR

Analyze all commits between base and HEAD (not just the latest — all of them) to generate the PR content.

**PR title format**: Short (under 72 chars), in English. Include the Jira key if available.
```
[IRB-365] Restrict payment method filter by user permissions
```

**PR body format** — use a heredoc for correct formatting:
```bash
gh pr create --title "<title>" --body "$(cat <<'EOF'
## Summary
- <1-3 bullet points describing what changed and why>

## Jira
[<TICKET-KEY>](<jira-url>/browse/<TICKET-KEY>)

## Changes
<brief description of files/areas modified>

## Test plan
- [ ] <verification steps for reviewers>

## Coverage
- Coverage: <XX>% (threshold: 80%)

---
Generated with [Codex](https://Codex.ai/Codex)
EOF
)"
```

If no Jira ticket, omit the `## Jira` section.

### 3.4 Output the PR URL
After creation, display the PR URL so the user can click through to it.

---

## Phase 4: Update Jira

If a Jira ticket was linked, transition it to "Code Review" (or equivalent status):
```
mcp__atlassian__jira_transition_issue(issue_key, transition_name="Code Review")
```

Also add a comment with the PR link:
```
mcp__atlassian__jira_add_comment(issue_key, body="PR created: <pr-url>")
```

If the transition fails (e.g., "Code Review" doesn't exist in this project's workflow), list available transitions and ask the user which one to use. Don't silently skip it.

---

## Edge cases

- **Multiple Jira tickets in branch name**: Use the first match, confirm with user
- **Branch already has an open PR**: Detect with `gh pr list --head <branch>` — if one exists, ask if user wants to update it instead
- **No test command found**: Ask the user what command runs the tests. Don't skip testing
- **Docker not running**: If Docker-based commands fail because Docker isn't running, tell the user and suggest the non-Docker alternative if available
- **Coverage tool not installed**: Warn and ask user if they want to proceed without coverage check, or install it first
