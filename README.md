# skills

A personal collection of agent skills for [Claude Code](https://claude.com/claude-code) and other agent runtimes that support the [open agent skills ecosystem](https://skills.sh).

Maintained by [@rauleburro](https://github.com/rauleburro).

---

## Available skills

| Skill | Description | Install command |
|-------|-------------|-----------------|
| [`warp-session`](./skills/warp-session) | Opens a new AI-agent session (claude, codex, opencode, or pi) in the Warp terminal — as a tab, split pane, or window — with an initial prompt and working directory. Harness-agnostic: a bundled bash script does all the work via Warp Tab Configs + the `warp://` URI scheme. | `npx skills add rauleburro/skills@warp-session` |
| [`apple-mail`](./skills/apple-mail) | Send, read, search, reply to, archive, and delete emails through Apple Mail on macOS. Supports attachments and requires explicit user confirmation before destructive or outbound actions. | `npx skills add rauleburro/skills@apple-mail` |
| [`daily-standup`](./skills/daily-standup) | Generates evidence-based daily standups by reconciling agent sessions, git, GitHub, the issue tracker (Jira/roadmap/Linear), team messaging (Slack/Teams), mail, and calendar. Persists each report in SQLite and reconciles the previous day's commitments against real evidence, then optionally delivers through the configured messaging destination. Portable across Codex, Claude Code, and open-source Agent Skills runtimes. | `npx skills add rauleburro/skills@daily-standup` |
| [`daily-standup-setup`](./skills/daily-standup-setup) | Interactive setup for the `daily-standup` skill: detects what it can (GitHub login, timezone, git author, session paths) and asks for the rest (org, messaging provider and channels, issue tracker, mail, calendar, delivery), then writes `~/.daily-standup/config.yaml`. | `npx skills add rauleburro/skills@daily-standup-setup` |
| [`research`](./skills/research) | Focused technical deep-dive using 3 parallel agents (codebase + web). Produces a consolidated report and persistent notes with minimal token overhead. | `npx skills add rauleburro/skills@research` |
| [`code-review-4r`](./skills/code-review-4r) | Autonomous, looping code review for a finished PR using the 4R framework (Risk, Readability, Reliability, Resilience). Spawns clean-context Opus reviewer + planner and Sonnet implementers, iterates review → plan → fix → re-review until approved, auto-commits each round, and posts a summary comment on the GitHub PR. Ships a synthetic-PR dataset and a scoring evaluator. | `npx skills add rauleburro/skills@code-review-4r` |
| [`auto-review-dispatch`](./skills/auto-review-dispatch) | Auto-detects branch, PR number, base commit, modified files, and project stack, then dispatches a fresh-context code review subagent with the full brief pre-filled. Triggers on "revisá mi PR", "code review this", "review before merging". | `npx skills add rauleburro/skills@auto-review-dispatch` |
| [`pr-deep-review-agent`](./skills/pr-deep-review-agent) | Launches a clean-context subagent for a deep pull request review, comparing code against local and official online documentation before reporting whether the PR is approved or changes are required. | `npx skills add rauleburro/skills@pr-deep-review-agent` |
| [`create-pr`](./skills/create-pr) | Creates a GitHub PR after validating tests, linter, and coverage. Pushes the branch, generates an English title/description from commits, and integrates with Jira (links ticket, updates status). Works with any stack. | `npx skills add rauleburro/skills@create-pr` |
| [`jira-task-workflow`](./skills/jira-task-workflow) | Complete workflow to implement a single Jira ticket: fetches it, analyzes code/docs, draws ASCII architecture diagrams, discusses the approach interactively, plans, implements, and verifies 80%+ test coverage. | `npx skills add rauleburro/skills@jira-task-workflow` |
| [`epic-plan-executor`](./skills/epic-plan-executor) | Executes multi-story Jira implementation plans (epics) in structured phases. Coordinates sequential and parallel work, manages Jira transitions, creates per-story branches, merges at the end, and validates with lint/test/build. | `npx skills add rauleburro/skills@epic-plan-executor` |
| [`feature-flow-auditor`](./skills/feature-flow-auditor) | Analyzes a feature or module end-to-end with parallel subagents, source-code introspection, Mermaid/UML diagrams, and an independent critical audit. Maps flows across models/views/controllers/APIs/jobs/integrations. | `npx skills add rauleburro/skills@feature-flow-auditor` |

---

## Installation

Each skill in this repo can be installed individually with the [skills CLI](https://skills.sh).

### Install a single skill globally (user-level)

```bash
npx skills add rauleburro/skills@<skill-name> -g
```

This makes the skill available across all your Claude Code projects.

### Install in a specific project

```bash
cd /path/to/your/project
npx skills add rauleburro/skills@<skill-name>
```

The skill becomes available only inside that project.

### Manual installation

If you prefer not to use the CLI, copy the relevant skill directory directly into your Claude Code skills folder:

```bash
cp -R skills/apple-mail ~/.claude/skills/apple-mail
chmod +x ~/.claude/skills/apple-mail/scripts/*.sh
```

---

## Repo layout

This repository follows the canonical multi-skill marketplace pattern used by [vercel-labs/agent-skills](https://github.com/vercel-labs/agent-skills) and recognized by the `skills` CLI auto-discovery:

```
.
├── skills/                  # CLI-discovered skills root
│   └── apple-mail/
│       ├── SKILL.md         # YAML frontmatter + agent instructions
│       ├── scripts/         # Executable shell scripts the agent invokes
│       └── reference/       # Optional reference docs the agent reads on demand
├── LICENSE
└── README.md
```

Every `SKILL.md` carries the `name` and `description` fields the agent uses to decide when the skill should trigger. The `scripts/` directory is the deterministic side; `reference/` is progressive disclosure for the agent — heavier documentation it can load only when needed.

---

## Contributing

These skills are primarily for personal use, but PRs and issues are welcome. If you find a bug, a UX rough edge, or have a suggestion, open an issue.

---

## Publishing on skills.sh

This repo follows the structure expected by the [skills CLI](https://github.com/vercel-labs/skills): a top-level `skills/` directory with each skill in its own subdirectory containing `SKILL.md`. Once the repo is public on GitHub, the CLI can resolve installs via `npx skills add rauleburro/skills@<skill-name>` without any manual submission. Indexing on the skills.sh leaderboard is driven by install counts; the listing appears automatically as the skill is installed by users.

---

## Attributions

### `apple-mail`

The `apple-mail` skill is a **fork of [`rbouschery/marketplace`](https://github.com/rbouschery/marketplace) `apple-mail`** (originally distributed via [skills.sh](https://skills.sh/rbouschery/marketplace/apple-mail)). The upstream version is **published publicly without an explicit license** at the time of forking; this fork is created in good faith under the implicit usage license of public skill distribution. If you are the upstream author and would like to discuss attribution or licensing, please open an issue.

Modifications introduced by this fork:

1. **Attachment support** in `send-email.sh`, `create-draft.sh`, and `create-reply-draft.sh` (extra trailing argument for comma-separated absolute file paths, with existence validation before invoking AppleScript).
2. **Mandatory confirmation flow** documented in `SKILL.md`: the agent must confirm sender, recipients, subject, body, and attachments with the user before invoking any script that sends mail or deletes from the mailbox.
3. **Description rewrite** for better triggering accuracy on Mac-specific email tasks.
4. **`delete-email.sh` elevated to the confirmation-required set** alongside outbound mail scripts.

Modifications introduced by this fork are released under the MIT License (see `LICENSE`). Portions originating from the upstream skill retain whatever rights the original author holds.

---

## License

MIT — see [`LICENSE`](./LICENSE) for the full text. Applies to modifications and original content authored in this repository.
