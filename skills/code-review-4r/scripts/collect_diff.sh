#!/usr/bin/env bash
# Collect the diff + metadata for a PR/branch to review with the 4R loop.
#
# Usage:
#   scripts/collect_diff.sh              # diff current branch vs merge-base with base branch
#   scripts/collect_diff.sh --pr <n>     # gh pr checkout <n> first, then diff
#
# Writes:  docs/code-review-4r/<id>/diff.patch  and  meta.json
# Prints:  the absolute path of the run directory (so the orchestrator can find the files).
set -euo pipefail

PR=""
while [ $# -gt 0 ]; do
  case "$1" in
    --pr) PR="${2:-}"; shift 2 ;;
    -h|--help) sed -n '2,9p' "$0"; exit 0 ;;
    *) echo "Unknown arg: $1" >&2; exit 2 ;;
  esac
done

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Not inside a git repository." >&2; exit 1
fi

# In --pr mode, check out the PR branch locally so auto-commit works.
if [ -n "$PR" ]; then
  command -v gh >/dev/null 2>&1 || { echo "gh CLI not found (needed for --pr)." >&2; exit 1; }
  gh pr checkout "$PR" >/dev/null 2>&1 || { echo "gh pr checkout $PR failed." >&2; exit 1; }
fi

HEAD_BRANCH="$(git rev-parse --abbrev-ref HEAD)"

# Resolve the base branch: prefer develop, then main, then master. Prefer the origin ref if present.
BASE=""
for cand in develop main master; do
  if git rev-parse --verify --quiet "origin/$cand" >/dev/null; then BASE="origin/$cand"; break; fi
  if git rev-parse --verify --quiet "$cand" >/dev/null; then BASE="$cand"; break; fi
done
if [ -z "$BASE" ]; then
  echo "Could not find a base branch (develop/main/master)." >&2; exit 1
fi

MERGE_BASE="$(git merge-base "$BASE" HEAD)"

# Resolve a stable run id and a human title.
if [ -n "$PR" ]; then
  ID="pr-${PR}"
  TITLE="$(gh pr view "$PR" --json title --jq .title 2>/dev/null || echo "PR #$PR")"
else
  ID="$(echo "$HEAD_BRANCH" | tr '/' '-' | tr -cd '[:alnum:]._-')"
  TITLE="$(git log -1 --pretty=%s)"
fi

RUN_DIR="docs/code-review-4r/${ID}"
mkdir -p "$RUN_DIR"

# The diff under review: merge-base..HEAD (what this branch adds on top of base).
git diff "$MERGE_BASE" HEAD > "$RUN_DIR/diff.patch"

# LOC stats from numstat (binary files report '-' and are skipped).
read -r FILES ADDED REMOVED <<<"$(git diff --numstat "$MERGE_BASE" HEAD | awk '
  $1 != "-" { a += $1 } $2 != "-" { r += $2 } { f += 1 }
  END { printf "%d %d %d", f, a, r }')"

# Escape the title for JSON.
TITLE_JSON="$(printf '%s' "$TITLE" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))' 2>/dev/null || printf '"%s"' "$TITLE")"

cat > "$RUN_DIR/meta.json" <<EOF
{
  "id": "${ID}",
  "pr": ${PR:-null},
  "title": ${TITLE_JSON},
  "base": "${BASE}",
  "head": "${HEAD_BRANCH}",
  "merge_base": "${MERGE_BASE}",
  "changed_files": ${FILES},
  "added_loc": ${ADDED},
  "removed_loc": ${REMOVED}
}
EOF

echo "$(cd "$RUN_DIR" && pwd)"
