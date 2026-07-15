---
name: daily-standup-reconciler
description: Generate an evidence-based daily standup by reconciling agent-session history, GitHub commits and pull requests, and Jira work, then optionally deliver it through a configured messaging destination. Use whenever a user asks for a daily, standup, yesterday/today update, automated weekday report, or a work recap based on coding-agent activity.
compatibility: Works with Codex, Claude Code, and open-source agents that support Agent Skills. Requires access to one or more work sources; delivery requires a configured messaging connector.
---

# Daily Standup Reconciler

Create a concise first-person standup from verifiable work evidence. Reconcile agent sessions, GitHub, and Jira instead of trusting a single source.

Read `config.example.yaml`, `references/PORTABILITY.md`, `references/SOURCE_QUERIES.md`, and `references/REPORT_TEMPLATE.md` before running the workflow.

## Rules

1. Use the configured timezone for every reporting boundary.
2. On Tuesday–Friday, `yesterday` is the previous calendar day. On Monday, use the previous Friday.
3. Exclude personal topics unless the user explicitly requests them.
4. Report only supported claims and deduplicate the same outcome across sources.
5. Keep Jira read-only: never mutate issues, comments, worklogs, or assignments.
6. GitHub default-branch commit search is incomplete; inspect relevant pull requests and their branch commits.
7. Never expose secrets, raw session prompts, customer data, tenant identifiers, or tool output.
8. Use concise first-person outcome language.

## Workflow

### 1. Establish windows

Resolve the current time in the configured timezone and compute the previous-workday and today windows. Honor explicit date ranges when supplied.

### 2. Inspect agent sessions

Use the runtime's authorized session-history capability. Read every session created or updated in either window and capture only the objective, verified outcome, project, linked PR/Jira key, and unfinished next step. Do not copy private prompts into the report.

### 3. Inspect GitHub

- Resolve the authenticated user and configured organization or repositories.
- Query authored commits in each window.
- Query authored or materially updated pull requests.
- Inspect commits on relevant PR branches so unmerged work is included.
- Capture concrete outcomes such as tests, coverage, review state, and merge status.

### 4. Inspect Jira

Use read-only queries for issues updated or resolved in each window and active assigned issues for today's plan. Read issue keys referenced by sessions or PRs even if the assignee changed. Do not infer completion from an old resolution date on an issue merely edited yesterday.

### 5. Reconcile

Create a private evidence table with one row per outcome and source columns for sessions, GitHub, and Jira. Prefer corroborated outcomes; omit duplicates, vague intent, personal activity, and unsupported inference.

### 6. Render

Use `references/REPORT_TEMPLATE.md`. Summarize previous-workday outcomes under `yesterday`. Under `today`, include verified work already performed plus concrete plans derived from unfinished sessions, active PRs, and Jira work.

### 7. Validate

Check that every bullet is concise, first-person, non-duplicative, supported, and free of secrets. Verify that PR-branch work was considered and Jira remained read-only.

### 8. Deliver

Follow the configured delivery policy:

- Scheduled runs may auto-send only when explicitly enabled in local configuration.
- Manual runs require confirmation unless the user explicitly asked to send.
- Resolve the exact destination before writing.
- Use the configured content format. For Microsoft Teams HTML, send through the connector's HTML field and use Teams-safe semantic tags rather than raw Markdown.
- Send only the standup; keep source diagnostics local.
- If delivery fails, preserve the draft and report the blocker without claiming success.

## Local completion response

Return the final standup, counts of inspected sessions/commits/PRs/issues, delivery status, and any unavailable source that reduced confidence.
