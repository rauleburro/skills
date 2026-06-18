#!/usr/bin/env bash
set -euo pipefail

SLUG="${1:-}"
if [ -z "$SLUG" ]; then
  echo "Usage: $0 <topic-slug>" >&2
  exit 1
fi

DIR="docs/${SLUG}"
mkdir -p "$DIR"

cat > "$DIR/NOTAS.md" <<EOF
# ${SLUG} — Notas de investigación

## Raw findings

## URLs

## Code snippets

## Open questions
EOF

echo "Initialized ${DIR}/NOTAS.md"
