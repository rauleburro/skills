#!/usr/bin/env bash
# Post the final 4R review summary as a comment on the GitHub PR.
#
# Usage:
#   scripts/post_github_summary.sh <id>             # comment on the current branch's PR
#   scripts/post_github_summary.sh <id> --pr <n>    # comment on an explicit PR number
#
# Reads:  docs/code-review-4r/<id>/summary.md
set -euo pipefail

ID="${1:-}"
[ -z "$ID" ] && { echo "Usage: $0 <id> [--pr <n>]" >&2; exit 2; }
shift || true

PR=""
while [ $# -gt 0 ]; do
  case "$1" in
    --pr) PR="${2:-}"; shift 2 ;;
    *) echo "Unknown arg: $1" >&2; exit 2 ;;
  esac
done

SUMMARY="docs/code-review-4r/${ID}/summary.md"
[ -f "$SUMMARY" ] || { echo "Summary not found: $SUMMARY" >&2; exit 1; }
command -v gh >/dev/null 2>&1 || { echo "gh CLI not found." >&2; exit 1; }

if [ -n "$PR" ]; then
  TARGET="$PR"
else
  # Resolve the PR for the current branch; if there is none, fail gracefully.
  TARGET="$(gh pr view --json number --jq .number 2>/dev/null || true)"
  if [ -z "$TARGET" ]; then
    echo "No open PR found for the current branch. Open the PR, then re-run:" >&2
    echo "  $0 $ID --pr <number>" >&2
    exit 3
  fi
fi

gh pr comment "$TARGET" --body-file "$SUMMARY"
echo "Posted 4R review summary to PR #$TARGET"
