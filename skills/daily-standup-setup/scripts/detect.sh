#!/usr/bin/env bash
#
# detect.sh — detecta valores por defecto para la config del daily-standup.
# Imprime pares clave=valor. Vacío = no detectado (preguntar al usuario).
#
set -uo pipefail

echo "os=$(uname -s)"
echo "timezone=$( (readlink /etc/localtime 2>/dev/null | sed 's#.*/zoneinfo/##') || true )"
echo "git_author=$(git config user.name 2>/dev/null | cut -d' ' -f1)"
echo "git_email=$(git config user.email 2>/dev/null)"

if command -v gh >/dev/null 2>&1; then
  echo "github_login=$(gh api user --jq .login 2>/dev/null || true)"
else
  echo "github_login="
fi

# ¿Existen sesiones de agentes conocidas?
sess=""
[ -d "$HOME/.claude/projects" ] && sess="$sess ~/.claude/projects"
[ -d "$HOME/.codex/sessions" ] && sess="$sess ~/.codex/sessions"
echo "agent_sessions=$(echo "$sess" | xargs)"

# ¿Dónde viven los repos? (heurística)
roots=""
for d in "$HOME/Develop" "$HOME/dev" "$HOME/code" "$HOME/src" "$HOME/Projects"; do
  [ -d "$d" ] && roots="$roots $(echo "$d" | sed "s#$HOME#~#")"
done
echo "git_roots=$(echo "$roots" | xargs)"

command -v sqlite3 >/dev/null 2>&1 && echo "sqlite3=yes" || echo "sqlite3=no"
echo "config_exists=$( [ -f "${DAILY_STANDUP_HOME:-$HOME/.daily-standup}/config.yaml" ] && echo yes || echo no )"
