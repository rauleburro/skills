#!/usr/bin/env bash
set -euo pipefail

skill_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

grep -q '^name: daily-standup-reconciler$' "$skill_dir/SKILL.md"
grep -q '^description:' "$skill_dir/SKILL.md"
grep -q 'read_only: true' "$skill_dir/config.example.yaml"
grep -q 'scheduled_run_auto_send: false' "$skill_dir/config.example.yaml"

if grep -RniE '(token|secret|password):[[:space:]]*[^#[:space:]]+' "$skill_dir" --exclude='validate.sh'; then
  echo "Potential secret-like value found" >&2
  exit 1
fi

echo "daily-standup-reconciler: validation passed"
