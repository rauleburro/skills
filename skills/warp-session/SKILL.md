---
name: warp-session
description: >-
  Open a new AI-agent session (claude, codex, opencode, or pi) in the Warp
  terminal — as a new tab, split pane, or window — with an initial prompt and
  working directory. Use this whenever the user asks to "open a new session",
  "spawn another agent", "abrime una sesión/tab/panel/ventana con claude/codex
  para que haga X", "lanzá otro claude con este prompt", "delegate this to a
  fresh session", or wants to hand a task to a parallel interactive agent in
  their terminal — even if they don't mention Warp explicitly, as long as they
  are on macOS with Warp. Works from any harness (Claude Code, Codex, opencode,
  pi): everything is done by a bundled bash script.
compatibility: macOS with Warp installed. The target agent CLI (claude, codex, opencode, pi) must be on PATH.
---

# warp-session

Open a new interactive agent session in Warp with an initial prompt, so the
user can keep working here while another agent works there.

## How it works (so you can debug it)

The bundled script writes the prompt to a file under
`~/.cache/warp-agent-sessions/`, generates a tiny runner script plus a Warp
**Tab Config** (TOML in `~/.warp/tab_configs/`), and opens it via Warp's URI
scheme:

- `tab` → `warp://tab_config/<name>` — new tab **in the user's active Warp window**
- `window` → `warp://tab_config/<name>?new_window=true` — new window
- `pane` → AppleScript `CMD+D` split of the current tab (needs Accessibility
  permission for the calling terminal); if that fails it falls back to a tab
  and says so on stderr.

The prompt never travels through TOML or keystrokes — the runner does
`<agent> "$(cat prompt-file)"` — so multiline prompts, quotes, and backticks
are all safe.

## Usage

Run the bundled script (path is relative to this skill's directory):

```bash
scripts/open_warp_agent.sh [options] [PROMPT]
```

| Option | Meaning | Default |
|---|---|---|
| `-a, --agent` | `claude` \| `codex` \| `opencode` \| `pi` | `claude` |
| `-t, --target` | `tab` \| `pane` \| `window` | `tab` |
| `-d, --cwd` | working directory for the new session | current dir |
| `-T, --title` | tab title | `<agent> · <dir>` |
| `-f, --prompt-file` | read prompt from a file (`-` = stdin) | — |
| `--agent-args` | extra flags for the agent CLI, as one string | — |
| `--exec` | run an arbitrary command instead of an agent | — |
| `--dry-run` | print generated files + URI, don't open Warp | — |

## Workflow

1. **Compose the prompt for the new session.** The new agent starts with zero
   context: make the prompt self-contained (goal, relevant paths, branch,
   constraints, definition of done). Don't just forward the user's words if
   they reference things only you can see — inline that context.
2. **Write it to a temp file** and pass `--prompt-file` (avoids any quoting or
   argv-length issues). A short one-liner can go as a positional arg instead.
3. **Pick agent and target** from the user's request. If they don't name an
   agent, use the one you are (claude if you're Claude Code, codex if you're
   Codex, etc.); otherwise default to `claude`. If they don't name a target,
   use `tab`.
4. **Run the script and relay its output.** It prints what it opened and where
   the prompt file lives.

### Examples

User: *"abrime otra sesión de claude que arregle los tests de packages/core"*

```bash
cat > /tmp/ws-prompt.md <<'EOF'
Fix the failing tests under packages/core. Run `npm test -w packages/core`
first to see the failures, fix root causes (not the assertions), and leave
the suite green. Repo: ~/Develop/acme/api, branch develop.
EOF
scripts/open_warp_agent.sh -a claude -d ~/Develop/acme/api -f /tmp/ws-prompt.md
```

User: *"lanzame un codex en una ventana nueva con este mismo prompt"*

```bash
scripts/open_warp_agent.sh -a codex -t window -f /tmp/ws-prompt.md
```

User: *"partime la pantalla con un opencode mirando los logs"*

```bash
scripts/open_warp_agent.sh -a opencode -t pane "tail the app logs and summarize errors as they appear"
```

## Notes & edge cases

- **`pane` needs Accessibility**: System Settings → Privacy & Security →
  Accessibility must include the app driving the keystrokes. On failure the
  script falls back to `tab` automatically — mention the fallback to the user.
- **`tab` opens in whichever Warp window is active**; if Warp isn't running,
  Warp launches and the tab becomes the first window.
- Generated TOML/prompt/runner files are pruned automatically after 3 days.
- To open a plain command (dev server, logs) instead of an agent, use
  `--exec 'npm run dev'`.
- If the user asks for an agent this table doesn't know, the script assumes a
  claude-style positional prompt — check `<agent> --help` if that fails.
