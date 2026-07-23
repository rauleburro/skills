#!/usr/bin/env bash
#
# standup_db.sh — histórico de dailys en SQLite (genérico y portable).
# DB por defecto: ~/.daily-standup/history.db
# Overrides (en orden de prioridad):
#   1. $STANDUP_DB              → ruta explícita al .db
#   2. $DAILY_STANDUP_HOME/history.db
#   3. ~/.daily-standup/history.db
#
# Uso:
#   standup_db.sh init
#   standup_db.sh save <YYYY-MM-DD> <archivo_md> ["notas"]
#   standup_db.sh get <YYYY-MM-DD>
#   standup_db.sh last [n]
#   standup_db.sh add-commitment <YYYY-MM-DD> "<texto>"
#   standup_db.sh pending
#   standup_db.sh resolve <id> <done|carried|dropped> ["evidencia"]
#
set -euo pipefail

HOME_DIR="${DAILY_STANDUP_HOME:-$HOME/.daily-standup}"
DB="${STANDUP_DB:-$HOME_DIR/history.db}"
mkdir -p "$(dirname "$DB")"

command -v sqlite3 >/dev/null 2>&1 || { echo "sqlite3 no está instalado" >&2; exit 1; }

q() { printf "%s" "$1" | sed "s/'/''/g"; }          # escape para SQL
d() {                                                # valida fecha
  [[ "$1" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]] || { echo "fecha inválida: $1" >&2; exit 1; }
}

init() {
  sqlite3 "$DB" <<'SQL'
CREATE TABLE IF NOT EXISTS reports (
  date       TEXT PRIMARY KEY,
  full_md    TEXT NOT NULL,
  notes      TEXT,
  created_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS commitments (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  report_date   TEXT NOT NULL,
  text          TEXT NOT NULL,
  status        TEXT NOT NULL DEFAULT 'open',   -- open | done | carried | dropped
  resolved_date TEXT,
  resolution    TEXT
);
SQL
}

cmd="${1:-help}"
case "$cmd" in
  init)
    init; echo "ok: $DB" ;;

  save)
    init; d "$2"
    [[ -f "$3" ]] || { echo "no existe el archivo: $3" >&2; exit 1; }
    sqlite3 "$DB" "INSERT INTO reports(date, full_md, notes)
                   VALUES ('$2', CAST(readfile('$3') AS TEXT), '$(q "${4:-}")')
                   ON CONFLICT(date) DO UPDATE
                   SET full_md=excluded.full_md, notes=excluded.notes,
                       created_at=datetime('now');"
    echo "guardado: $2" ;;

  get)
    d "$2"
    sqlite3 "$DB" "SELECT full_md FROM reports WHERE date='$2';" ;;

  last)
    n="${2:-1}"
    sqlite3 -separator $'\n' "$DB" \
      "SELECT '=== ' || date || ' ===', full_md FROM reports
       ORDER BY date DESC LIMIT $((n));" ;;

  add-commitment)
    init; d "$2"
    sqlite3 "$DB" "INSERT INTO commitments(report_date, text)
                   VALUES ('$2', '$(q "$3")');"
    echo "compromiso añadido ($2)" ;;

  pending)
    init
    sqlite3 -column -header "$DB" \
      "SELECT id, report_date, text FROM commitments
       WHERE status IN ('open','carried') ORDER BY report_date;" ;;

  resolve)
    [[ "$3" =~ ^(done|carried|dropped)$ ]] || { echo "status inválido: $3" >&2; exit 1; }
    sqlite3 "$DB" "UPDATE commitments
                   SET status='$3', resolved_date=date('now'),
                       resolution='$(q "${4:-}")'
                   WHERE id=$(($2));"
    echo "compromiso $2 → $3" ;;

  *)
    grep '^#   standup_db.sh' "$0" | sed 's/^# *//' ;;
esac
