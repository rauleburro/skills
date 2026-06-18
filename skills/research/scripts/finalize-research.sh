#!/usr/bin/env bash
set -euo pipefail

SLUG="${1:-}"
if [ -z "$SLUG" ]; then
  echo "Usage: $0 <topic-slug>" >&2
  exit 1
fi

DIR="docs/${SLUG}"
MASTER="${DIR}/RESEARCH_CONSOLIDADO.md"

if [ ! -f "$MASTER" ]; then
  echo "Error: ${MASTER} not found" >&2
  exit 1
fi

echo "Finalized ${MASTER}"
