#!/usr/bin/env bash
#
# write_config.sh — escribe ~/.daily-standup/config.yaml a partir de variables de entorno.
# El skill de setup completa estas vars con lo detectado + las respuestas del usuario.
#
# Vars (con defaults):
#   DS_NAME DS_GH_LOGIN DS_EMAIL DS_TRACKER_USER
#   DS_TZ DS_MONDAY_FRIDAY(true)
#   DS_SESSIONS_ENABLED(true) DS_SESSIONS_PATHS('~/.claude/projects')
#   DS_GIT_ENABLED(true) DS_GIT_ROOTS('~/Develop') DS_GIT_AUTHOR
#   DS_GH_ENABLED(true) DS_GH_ORG
#   DS_TRACKER_ENABLED(true) DS_TRACKER_PROVIDER(jira) DS_TRACKER_SITE
#   DS_MSG_ENABLED(true) DS_MSG_PROVIDER(slack) DS_MSG_CHANNELS('#daily')
#   DS_MAIL_ENABLED(true) DS_MAIL_PROVIDER(apple_mail)
#   DS_CAL_ENABLED(true) DS_CAL_PROVIDER(apple_calendar)
#   DS_DELIVERY_PROVIDER(slack) DS_DELIVERY_DEST('#daily') DS_DELIVERY_FORMAT(markdown)
#   DS_AUTO_SEND(false) DS_LANG(es)
#
set -euo pipefail

HOME_DIR="${DAILY_STANDUP_HOME:-$HOME/.daily-standup}"
OUT="$HOME_DIR/config.yaml"
mkdir -p "$HOME_DIR"

# Convierte "a, b" o "a b" en lista YAML inline ["a", "b"]
yaml_list() {
  local IFS=', '; read -ra items <<< "$1"
  local out=""
  for i in "${items[@]}"; do [ -n "$i" ] && out="$out\"$i\", "; done
  echo "[${out%, }]"
}

if [ -f "$OUT" ]; then
  cp "$OUT" "$OUT.bak.$(date +%Y%m%d%H%M%S 2>/dev/null || echo prev)"
fi

cat > "$OUT" <<YAML
# Generado por daily-standup-setup. Editá a mano cuando quieras.
# Secretos (tokens/API keys) NO van acá: usá el gestor de secretos o env vars.
version: 2

identity:
  display_name: "${DS_NAME:-TU_NOMBRE}"
  github_login: "${DS_GH_LOGIN:-}"
  email: "${DS_EMAIL:-}"
  issue_tracker_user: "${DS_TRACKER_USER:-currentUser()}"

time:
  timezone: "${DS_TZ:-UTC}"
  schedule:
    weekdays: [monday, tuesday, wednesday, thursday, friday]
    local_time: "09:00"
  monday_uses_previous_friday: ${DS_MONDAY_FRIDAY:-true}

scope:
  exclude_personal_topics: true

sources:
  agent_sessions:
    enabled: ${DS_SESSIONS_ENABLED:-true}
    paths: $(yaml_list "${DS_SESSIONS_PATHS:-~/.claude/projects}")
  git:
    enabled: ${DS_GIT_ENABLED:-true}
    roots: $(yaml_list "${DS_GIT_ROOTS:-~/Develop}")
    author_match: "${DS_GIT_AUTHOR:-}"
  github:
    enabled: ${DS_GH_ENABLED:-true}
    organization: "${DS_GH_ORG:-}"
  issue_tracker:
    enabled: ${DS_TRACKER_ENABLED:-true}
    provider: "${DS_TRACKER_PROVIDER:-jira}"
    site: "${DS_TRACKER_SITE:-}"
    read_only: true
    prefer_active_sprint_parent_issues: true
  messaging:
    enabled: ${DS_MSG_ENABLED:-true}
    provider: "${DS_MSG_PROVIDER:-slack}"
    read_own_messages: true
    channels: $(yaml_list "${DS_MSG_CHANNELS:-#daily}")
  mail:
    enabled: ${DS_MAIL_ENABLED:-true}
    provider: "${DS_MAIL_PROVIDER:-apple_mail}"
    only_sent_by_me: true
  calendar:
    enabled: ${DS_CAL_ENABLED:-true}
    provider: "${DS_CAL_PROVIDER:-apple_calendar}"

delivery:
  provider: "${DS_DELIVERY_PROVIDER:-slack}"
  destination_type: "channel"
  destination_name: "${DS_DELIVERY_DEST:-#daily}"
  content_format: "${DS_DELIVERY_FORMAT:-markdown}"
  scheduled_run_auto_send: ${DS_AUTO_SEND:-false}
  manual_run_requires_confirmation: true

history:
  enabled: true
  db_path: "$HOME_DIR/history.db"

output:
  language: "${DS_LANG:-es}"
  headings: ["yesterday", "today"]
  voice: "first_person_singular"
  max_bullets_per_section: 6
YAML

echo "escrito: $OUT"
