#!/usr/bin/env bash
# open_warp_agent.sh — open a new agent session (claude/codex/opencode/pi) in Warp
# as a tab, window, or split pane, with an optional initial prompt.
#
# Mechanism: writes the prompt to a file, generates a small runner script and a
# Warp Tab Config (TOML), then opens it via the warp:// URI scheme.
#   tab    -> warp://tab_config/<name>                  (tab in the active window)
#   window -> warp://tab_config/<name>?new_window=true  (new window)
#   pane   -> AppleScript CMD+D split (needs Accessibility); falls back to tab
#
# The prompt never travels inside the TOML or through AppleScript keystrokes,
# so no escaping issues: the runner does  <agent> "$(cat prompt-file)".
set -euo pipefail

STATE_DIR="${WARP_AGENT_STATE_DIR:-$HOME/.cache/warp-agent-sessions}"
TAB_CONFIG_DIR="${WARP_TAB_CONFIG_DIR:-$HOME/.warp/tab_configs}"
CONFIG_PREFIX="agent-session"

usage() {
  cat <<'EOF'
Usage: open_warp_agent.sh [options] [PROMPT]

Open a new AI-agent session in Warp with an optional initial prompt.

Options:
  -a, --agent NAME       claude | codex | opencode | pi   (default: claude)
  -t, --target KIND      tab | window | pane              (default: tab)
  -d, --cwd DIR          working directory for the session (default: $PWD)
  -T, --title TITLE      tab title (default: "<agent> · <cwd basename>")
  -f, --prompt-file F    read the prompt from file F ("-" = stdin).
                         Preferred over positional PROMPT for long/multiline text.
      --agent-args ARGS  extra flags appended to the agent CLI (single string)
      --exec CMD         run an arbitrary shell command instead of an agent
      --dry-run          print the generated files and URI without opening Warp
  -h, --help             show this help

Examples:
  open_warp_agent.sh "fix the failing tests in packages/core"
  open_warp_agent.sh -a codex -t window -d ~/Develop/api -f /tmp/prompt.md
  open_warp_agent.sh -a opencode -t pane "review the diff on this branch"
  open_warp_agent.sh --exec 'npm run dev' -T "dev server"
EOF
}

err() { printf 'open_warp_agent: %s\n' "$*" >&2; exit 1; }

AGENT="claude"
TARGET="tab"
CWD="$PWD"
TITLE=""
PROMPT=""
PROMPT_FILE=""
AGENT_ARGS=""
EXEC_CMD=""
DRY_RUN=0

while [ $# -gt 0 ]; do
  case "$1" in
    -a|--agent)      AGENT="${2:?missing value for $1}"; shift 2 ;;
    -t|--target)     TARGET="${2:?missing value for $1}"; shift 2 ;;
    -d|--cwd)        CWD="${2:?missing value for $1}"; shift 2 ;;
    -T|--title)      TITLE="${2:?missing value for $1}"; shift 2 ;;
    -f|--prompt-file) PROMPT_FILE="${2:?missing value for $1}"; shift 2 ;;
    --agent-args)    AGENT_ARGS="${2:?missing value for $1}"; shift 2 ;;
    --exec)          EXEC_CMD="${2:?missing value for $1}"; shift 2 ;;
    --dry-run)       DRY_RUN=1; shift ;;
    -h|--help)       usage; exit 0 ;;
    --)              shift; PROMPT="${*:-}"; break ;;
    -*)              err "unknown option: $1 (see --help)" ;;
    *)               PROMPT="$1"; shift ;;
  esac
done

case "$TARGET" in tab|window|pane) ;; *) err "invalid --target '$TARGET' (tab|window|pane)";; esac
[ -d "$CWD" ] || err "cwd does not exist: $CWD"
CWD="$(cd "$CWD" && pwd)"   # absolute path; Warp requires absolute directory

# --- resolve prompt ---------------------------------------------------------
if [ -n "$PROMPT_FILE" ]; then
  if [ "$PROMPT_FILE" = "-" ]; then PROMPT="$(cat)"; else
    [ -f "$PROMPT_FILE" ] || err "prompt file not found: $PROMPT_FILE"
    PROMPT="$(cat "$PROMPT_FILE")"
  fi
fi

# --- build the agent command ------------------------------------------------
resolve_bin() { command -v "$1" 2>/dev/null || echo "$1"; }

mkdir -p "$STATE_DIR" "$TAB_CONFIG_DIR"
# prune artifacts older than 3 days so the "+" menu and cache stay clean
find "$STATE_DIR" -type f -mtime +3 -delete 2>/dev/null || true
find "$TAB_CONFIG_DIR" -maxdepth 1 -name "${CONFIG_PREFIX}-*.toml" -mtime +3 -delete 2>/dev/null || true

ID="$(date +%s)-$$"
RUNNER="$STATE_DIR/runner-$ID.sh"
PROMPT_PATH="$STATE_DIR/prompt-$ID.txt"

if [ -n "$EXEC_CMD" ]; then
  AGENT_LABEL="cmd"
  AGENT_CMD="$EXEC_CMD"
else
  BIN="$(resolve_bin "$AGENT")"
  case "$AGENT" in
    claude|codex|pi)
      if [ -n "$PROMPT" ]; then AGENT_CMD="\"$BIN\" $AGENT_ARGS \"\$(cat '$PROMPT_PATH')\""
      else AGENT_CMD="\"$BIN\" $AGENT_ARGS"; fi ;;
    opencode)
      if [ -n "$PROMPT" ]; then AGENT_CMD="\"$BIN\" $AGENT_ARGS --prompt \"\$(cat '$PROMPT_PATH')\""
      else AGENT_CMD="\"$BIN\" $AGENT_ARGS"; fi ;;
    *)  # unknown agent: assume claude-style positional prompt
      if [ -n "$PROMPT" ]; then AGENT_CMD="\"$BIN\" $AGENT_ARGS \"\$(cat '$PROMPT_PATH')\""
      else AGENT_CMD="\"$BIN\" $AGENT_ARGS"; fi ;;
  esac
  AGENT_LABEL="$AGENT"
fi

[ -n "$PROMPT" ] && printf '%s' "$PROMPT" > "$PROMPT_PATH"

cat > "$RUNNER" <<EOF
#!/usr/bin/env bash
cd '$CWD' || exit 1
$AGENT_CMD
EOF
chmod +x "$RUNNER"

[ -n "$TITLE" ] || TITLE="$AGENT_LABEL · $(basename "$CWD")"
TITLE="${TITLE//\"/}"   # double quotes would break the TOML string

# --- pane: split the current Warp tab via AppleScript ------------------------
open_pane() {
  /usr/bin/osascript <<EOF 2>/dev/null
tell application "Warp" to activate
delay 0.5
tell application "System Events" to tell process "Warp"
  keystroke "d" using command down
  delay 0.8
  keystroke "bash '$RUNNER'"
  key code 36
end tell
EOF
}

# --- tab / window: Warp Tab Config + warp:// URI -----------------------------
CONFIG_NAME="${CONFIG_PREFIX}-${ID}"
CONFIG_PATH="$TAB_CONFIG_DIR/${CONFIG_NAME}.toml"

write_config() {
  cat > "$CONFIG_PATH" <<EOF
name = "Agent session (auto)"
title = "$TITLE"
color = "cyan"

[[panes]]
id = "main"
type = "terminal"
directory = "$CWD"
commands = ["bash '$RUNNER'"]
is_focused = true
EOF
}

URI="warp://tab_config/$CONFIG_NAME"
[ "$TARGET" = "window" ] && URI="$URI?new_window=true"

if [ "$DRY_RUN" -eq 1 ]; then
  write_config
  echo "--- runner: $RUNNER"; cat "$RUNNER"
  echo "--- tab config: $CONFIG_PATH"; cat "$CONFIG_PATH"
  echo "--- target: $TARGET"
  [ "$TARGET" = "pane" ] && echo "(pane mode would use AppleScript CMD+D; fallback URI below)"
  echo "--- uri: $URI"
  exit 0
fi

if [ "$TARGET" = "pane" ]; then
  if open_pane; then
    echo "Opened $AGENT_LABEL session in a new Warp pane (cwd: $CWD)"
    exit 0
  fi
  echo "warn: AppleScript pane split failed (Accessibility permission?). Falling back to a new tab." >&2
  TARGET="tab"
  URI="warp://tab_config/$CONFIG_NAME"
fi

write_config
open "$URI" || err "could not open $URI — is Warp installed?"
echo "Opened $AGENT_LABEL session in a new Warp $TARGET (cwd: $CWD)"
[ -n "$PROMPT" ] && echo "Prompt: $PROMPT_PATH"
