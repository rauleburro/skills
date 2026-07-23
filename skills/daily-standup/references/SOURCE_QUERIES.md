# Comandos por fuente

Adaptá estos ejemplos al conector disponible en tu runtime. `SINCE`/`UNTIL` en `YYYY-MM-DD`.
Todas las consultas de lectura; nada muta estado. Corré solo las fuentes con `enabled: true`.

## 1. Sesiones de agentes de código

```bash
# Transcripts tocados en la ventana (Claude Code)
find ~/.claude/projects -name '*.jsonl' -newermt "$SINCE" ! -newermt "$UNTIL" | head -20

# Primer prompt del usuario de una sesión (objetivo)
jq -r 'select(.type=="user" and (.message.content|type)=="string") | .message.content' "$f" \
  | grep -v '^<' | head -2 | cut -c1-300

# Cierre de la sesión (qué quedó hecho/pendiente)
jq -r 'select(.type=="assistant") | .message.content[]? | select(.type=="text") | .text' "$f" | tail -c 2500
```

Codex u otros agentes guardan sus sesiones en otra ruta (`sources.agent_sessions.paths`); ajustá el `find`. **Nunca** copies prompts crudos al reporte: solo objetivo + resultado.

## 2. Git local (todos los repos bajo `sources.git.roots`)

```bash
AUTHOR="${GIT_AUTHOR_MATCH:-$(git config user.name | cut -d' ' -f1)}"  # 1er nombre cubre acentos
for ROOT in $ROOTS; do
  find "$ROOT" -maxdepth 3 -name .git -type d 2>/dev/null | while read -r g; do
    repo="$(dirname "$g")"
    out=$(git -C "$repo" log --all --author="$AUTHOR" \
          --since="$SINCE 00:00" --until="$UNTIL 00:00" \
          --pretty=format:"%h %ad %s" --date=format:"%H:%M" 2>/dev/null)
    [ -n "$out" ] && echo "=== $repo" && echo "$out"
  done
done
```

## 3. GitHub

```bash
LOGIN=$(gh api user --jq .login)

# Eventos del usuario en la ventana (pushes, PRs, reviews, comments)
gh api "users/$LOGIN/events" --paginate --jq \
  '.[] | select(.created_at >= "'$SINCE'T00:00:00Z" and .created_at < "'$UNTIL'T00:00:00Z")
   | "\(.created_at[11:16]) \(.type) \(.repo.name)"' | sort

# Estado REAL de una PR (¡verificar antes de decir "merged"!)
gh pr view <n> --repo <org>/<repo> \
  --json state,title,author,mergedAt,mergedBy,baseRefName,reviewDecision
```

Gotchas:
- `search/commits?author=` no indexa bien repos privados de una org — usá events + `repos/<org>/<repo>/commits?since=&until=`.
- Una PR puede mergearse a una rama que no es la default; mirá `baseRefName`.
- Búsqueda por rango: `org:ORG author:LOGIN author-date:SINCE..UNTIL` / `updated:SINCE..UNTIL`.

## 4. Issue tracker (`sources.issue_tracker.provider`)

### Jira (MCP de Atlassian o REST) — JQL, solo lectura

```jql
assignee = currentUser() AND updated >= "SINCE" AND updated < "UNTIL" ORDER BY updated DESC
assignee = currentUser() AND resolved >= "SINCE" AND resolved < "UNTIL" ORDER BY resolved DESC
assignee = currentUser() AND statusCategory != Done ORDER BY priority DESC, updated DESC
```

### Roadmap (aima-roadmap MCP) — si `provider: roadmap`

Usá el MCP `aima-roadmap` si está conectado; si no, un helper HTTP JSON-RPC contra su endpoint:

```bash
list_org_members {}                                   # resolver mi userId por email
list_tasks {"assigneeId":"<uuid>","status":"todo"}
list_tasks {"assigneeId":"<uuid>","status":"in_review"}
list_tasks {"status":"in_progress","limit":50}        # ownerId ≠ assignee: revisar ambos
list_briefings {"sinceDays":1,"limit":5}              # narrativa de riesgo del día
```

Gotchas:
- `list_tasks` con `assigneeId` **no** trae tareas donde solo sos `owner` — cruzá con la query global de `in_progress` mirando `ownerEmail`.
- Tareas con `endDate` vencida → candidatas prioritarias a Today.

## 5. Mensajería (`sources.messaging.provider`)

Leé **tus propios mensajes** en los canales configurados durante la ventana (evidencia de decisiones/avisos/bloqueos).

### Slack (MCP de Slack)

```text
# Buscar mis mensajes en la ventana
search: from:@me after:SINCE before:UNTIL in:#daily
# o por canal: leer historia del canal y filtrar por mi user id
conversations.history(channel=<id>, oldest=<ts_since>, latest=<ts_until>)
```

### Teams

Usá el conector de Teams para listar mensajes propios en los canales/chats configurados dentro de la ventana. Capturá decisiones y acuerdos, no charla.

No cites mensajes de terceros salvo contexto mínimo imprescindible.

## 6. Mail (`sources.mail.provider`)

Evidencia = correos que **enviaste** en la ventana (`only_sent_by_me: true`).

### Apple Mail (macOS)

```bash
osascript -e '
tell application "Mail"
  set out to ""
  set since to (current date) - 1 * days   -- ajustá a la ventana real
  repeat with m in (messages of sent mailbox whose date sent ≥ since)
    set out to out & (date sent of m as string) & " | " & (subject of m) & linefeed
  end repeat
  return out
end tell'
```

Para Gmail usá su API/MCP con `in:sent after:SINCE before:UNTIL`. Nunca vuelques cuerpos con datos sensibles al canal: solo el hecho ("envié X a Y").

## 7. Calendario (`sources.calendar.provider`)

Eventos de **hoy** para detectar bloqueos de agenda (los personales solo van en la nota privada).

### Apple Calendar (macOS)

```bash
osascript -e '
set output to ""
tell application "Calendar"
  set todayStart to current date
  set hours of todayStart to 0
  set minutes of todayStart to 0
  set seconds of todayStart to 0
  set todayEnd to todayStart + 1 * days
  repeat with cal in calendars
    set evs to (every event of cal whose start date ≥ todayStart and start date < todayEnd)
    repeat with ev in evs
      set output to output & (start date of ev as string) & " | " & (summary of ev) & linefeed
    end repeat
  end repeat
end tell
return output'
```

Gotcha: los eventos recurrentes pueden no expandirse por AppleScript; si falta la reunión periódica del equipo, no asumas que no existe.

## 8. Histórico (SQLite)

Ver `scripts/standup_db.sh` y `references/HISTORY.md`.

```bash
scripts/standup_db.sh init
scripts/standup_db.sh pending
scripts/standup_db.sh last 3
scripts/standup_db.sh get 2026-07-22
scripts/standup_db.sh save 2026-07-22 /path/daily.md "nota opcional"
scripts/standup_db.sh add-commitment 2026-07-22 "Aplicar fix y re-correr benchmark"
scripts/standup_db.sh resolve 4 done "PR #40 merged"
```
