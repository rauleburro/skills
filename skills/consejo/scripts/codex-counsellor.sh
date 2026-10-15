#!/usr/bin/env bash
# Run one Codex counsellor of the consejo, read-only, on a question brief.
#
#   codex-counsellor.sh check
#       exit 0 when Codex can run, 2 when it cannot (prints the reason).
#   codex-counsellor.sh run <stance> <brief-file> <out-file> [workdir]
#       stance: adversary | premortem
#       exit 0 with a VOTE line in <out-file>; 2 when Codex is unavailable
#       (not installed, not logged in, usage limit); 1 on any other failure.
#
# Env: CONSEJO_CODEX_MODEL (default gpt-6.1-sol), CONSEJO_CODEX_EFFORT (default xhigh).
set -uo pipefail

MODEL="${CONSEJO_CODEX_MODEL:-gpt-6.1-sol}"
EFFORT="${CONSEJO_CODEX_EFFORT:-xhigh}"
LIMIT_RE='usage limit|rate limit|quota|exceeded your|429|Too Many Requests|not logged in|Not logged in|login required|401 Unauthorized'

check() {
  command -v codex >/dev/null 2>&1 || { echo "codex: not installed"; return 2; }
  local status
  status="$(codex login status 2>&1)" || { echo "codex: $status"; return 2; }
  echo "$status" | grep -qi 'logged in' || { echo "codex: $status"; return 2; }
  echo "codex: $(codex --version 2>/dev/null), $status"
}

stance_text() {
  case "$1" in
    adversary) cat <<'S'
You are an adversarial counsellor. Your job is to break confidence in the option that looks
most obvious or that the brief leans toward, not to validate it. Default to skepticism: look for
the hidden cost, the failure under real conditions, the assumption that stops being true. Vote
for the option that survives your attack best; if the obvious one survives, say so and vote for it.
S
    ;;
    premortem) cat <<'S'
You are an adversarial counsellor running a pre-mortem. Assume each option was chosen and,
six months later, it turned out to be the wrong call. For each option, write the most plausible
story of how it failed and how expensive that failure was. Vote for the option whose failure
story is least likely or cheapest to recover from.
S
    ;;
    *) echo "unknown stance: $1" >&2; return 1 ;;
  esac
}

run() {
  local stance="$1" brief="$2" out="$3" workdir="${4:-$PWD}"
  [[ -f "$brief" ]] || { echo "brief not found: $brief" >&2; return 1; }
  check >/dev/null || { check; return 2; }

  local prompt log rc
  prompt="$(stance_text "$stance")" || return 1
  prompt+=$'\n\n'"$(cat <<'R'
Rules: you are read-only. You may read files and run read-only commands to check facts; never
edit, create, commit or push anything, and take no action beyond answering. Argue independently.
Ground every claim in the brief or in what you read; mark inferences as inferences.
Answer in the language the question is written in.

End your answer with exactly these three lines, nothing after them:
VOTE: <one option, spelled exactly as listed in the brief>
CONFIDENCE: <0.0-1.0>
RATIONALE: <one paragraph>
R
)"
  prompt+=$'\n\n<brief>\n'"$(cat "$brief")"$'\n</brief>'

  log="${out%.*}.log"
  codex exec --ignore-user-config --ephemeral --skip-git-repo-check \
    -s read-only -C "$workdir" -m "$MODEL" -c "model_reasoning_effort=\"$EFFORT\"" \
    -o "$out" "$prompt" </dev/null >"$log" 2>&1
  rc=$?

  if grep -Eqi "$LIMIT_RE" "$log" && ! grep -q '^VOTE:' "$out" 2>/dev/null; then
    echo "codex unavailable: $(grep -Eim1 "$LIMIT_RE" "$log")"; return 2
  fi
  if [[ $rc -ne 0 ]] || ! grep -q '^VOTE:' "$out" 2>/dev/null; then
    echo "codex failed (rc=$rc), see $log"; return 1
  fi
  grep -E '^(VOTE|CONFIDENCE):' "$out"
}

case "${1:-}" in
  check) check ;;
  run) shift; [[ $# -ge 3 ]] || { echo "usage: $0 run <stance> <brief-file> <out-file> [workdir]" >&2; exit 1; }; run "$@" ;;
  *) echo "usage: $0 check | run <stance> <brief-file> <out-file> [workdir]" >&2; exit 1 ;;
esac
