#!/usr/bin/env bash
set -euo pipefail

skill_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# --- estructura y metadata ---
grep -q '^name: daily-standup$' "$skill_dir/SKILL.md"
grep -q '^description:' "$skill_dir/SKILL.md"

# --- config de ejemplo: invariantes de seguridad ---
grep -q 'version: 2' "$skill_dir/config.example.yaml"
grep -q 'read_only: true' "$skill_dir/config.example.yaml"
grep -q 'scheduled_run_auto_send: false' "$skill_dir/config.example.yaml"
grep -q 'manual_run_requires_confirmation: true' "$skill_dir/config.example.yaml"

# --- todas las fuentes presentes ---
for src in agent_sessions git github issue_tracker messaging mail calendar; do
  grep -q "  $src:" "$skill_dir/config.example.yaml" || { echo "falta fuente: $src" >&2; exit 1; }
done

# --- referencias esperadas ---
for ref in PORTABILITY SOURCE_QUERIES REPORT_TEMPLATE HISTORY; do
  [ -f "$skill_dir/references/$ref.md" ] || { echo "falta reference: $ref.md" >&2; exit 1; }
done

# --- scripts ejecutables ---
[ -x "$skill_dir/scripts/standup_db.sh" ] || { echo "standup_db.sh no ejecutable" >&2; exit 1; }

# --- evals es JSON válido ---
python3 -c "import json,sys; json.load(open('$skill_dir/evals/test-cases.json'))"

# --- sin valores tipo secreto ---
if grep -RniE '(token|secret|password|api[_-]?key):[[:space:]]*[^#[:space:]"]+' "$skill_dir" --exclude='validate.sh'; then
  echo "Potential secret-like value found" >&2
  exit 1
fi

echo "daily-standup: validation passed"
