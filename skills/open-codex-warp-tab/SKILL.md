---
name: open-codex-warp-tab
description: Open a real, visible Codex CLI session in a new Warp tab with its prompt submitted automatically, while keeping the new tab in the same active Warp window/tab group as the requesting session. Use when the user asks to "open a new Codex session", "abre una nueva sesión de Codex", launch an interactive Codex tab in Warp, or create a separate visible Codex session rather than an internal subagent. Default to the active group; create a separate Warp window only when the user explicitly requests one.
---

# Open Codex in a Warp Tab

Launch Codex through a Warp Tab Config instead of simulating keystrokes. The Tab
Config starts the command reliably and Warp places it in the currently active
window/group.

## Workflow

1. Extract the Codex prompt, working directory, and a short tab title from the
   request. Default the directory to the requesting session's project directory.
2. Keep the requesting Warp window/group active:
   - Do not run AppleScript that activates Warp or selects a window.
   - Do not focus another Warp window before opening the Tab Config.
3. Run `scripts/open_codex_warp_tab.py` with the exact prompt and directory.
   Opening a GUI URI may require an escalated command approval; request only the
   narrow permission needed to open the Warp Tab Config.
4. Omit `--new-window` by default. Add it only when the user explicitly asks for
   a separate Warp window.
5. Report that Warp was asked to open the tab. Do not claim visual placement was
   verified unless it was actually inspected.

## Commands

Open a session in the same active Warp window/group:

```bash
python3 scripts/open_codex_warp_tab.py \
  --directory /absolute/project/path \
  --title "Short task name" \
  "The exact prompt for the new Codex session"
```

Open a separate window only when explicitly requested:

```bash
python3 scripts/open_codex_warp_tab.py \
  --directory /absolute/project/path \
  --new-window \
  "The exact prompt"
```

Preview the generated Tab Config without writing or opening anything:

```bash
python3 scripts/open_codex_warp_tab.py \
  --directory /absolute/project/path \
  --print-only \
  "The exact prompt"
```

## Guardrails

- Use this skill for a standalone visible Codex CLI session, not for an internal
  subagent. Internal subagents remain inside the current Codex session.
- Never implement the launch by typing into Warp with `osascript`, `Cmd+T`, or a
  simulated Enter key; focus races can leave the command unsubmitted or target
  the wrong group.
- Never use `?new_window=true` unless requested.
- Do not close an existing tab or session automatically when correcting
  placement; ask first because it may contain active work.
- The generated Tab Config stores the latest prompt as plaintext under Warp's
  user configuration directory. Do not put credentials or secrets in prompts.
- If placement is wrong, ask the user to focus the intended Warp group and retry
  without activating Warp programmatically.

## Script behavior

`scripts/open_codex_warp_tab.py`:

- validates the project directory and prompt;
- atomically writes one reusable `codex_session_launcher.toml` Tab Config;
- shell-quotes the directory and prompt;
- launches `warp://tab_config/codex_session_launcher`;
- supports macOS, Linux, and Windows Warp URI handlers;
- preserves the active group by avoiding window-selection automation.
