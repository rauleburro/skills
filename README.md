# skills

A personal collection of agent skills for [Claude Code](https://claude.com/claude-code) and other agent runtimes that support the [open agent skills ecosystem](https://skills.sh).

Maintained by [@rauleburro](https://github.com/rauleburro).

---

## Available skills

| Skill | Description | Install command |
|-------|-------------|-----------------|
| [`apple-mail`](./skills/apple-mail) | Send, read, search, reply to, archive, and delete emails through Apple Mail on macOS. Supports attachments and requires explicit user confirmation before destructive or outbound actions. | `npx skills add rauleburro/skills@apple-mail` |

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
