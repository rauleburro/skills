# Portabilidad entre runtimes

Este skill usa la convención abierta de Agent Skills e instrucciones basadas en capacidades:
describe *qué* necesita cada paso, no *qué herramienta* concreta usarlo. Así corre en Codex,
Claude Code o agentes open-source, mapeando cada capacidad al conector disponible.

| Capacidad            | Implementaciones posibles |
|----------------------|---------------------------|
| sesiones de agente   | API del runtime, MCP, logs JSONL autorizados |
| git                  | `git` local |
| GitHub               | MCP de GitHub, REST/GraphQL, `gh` |
| issue tracker        | MCP de Atlassian/Jira, aima-roadmap MCP, Linear API, REST |
| mensajería           | MCP de Slack/Teams, API del proveedor, webhook aprobado |
| mail                 | Apple Mail (AppleScript), Gmail API/MCP |
| calendario           | Apple Calendar (AppleScript), Google Calendar API |
| histórico            | SQLite local (`scripts/standup_db.sh`) |
| scheduling           | automatización del runtime, cron, systemd timer, CI |

## Instalación

Instalá en Codex o Claude Code vía un CLI de skills compatible, o copiá el directorio a la
carpeta de skills del runtime. Los agentes open-source pueden cargar `SKILL.md` directamente
si no tienen descubrimiento automático.

## Configuración y secretos

- La config vive en `~/.daily-standup/config.yaml` (override con `$DAILY_STANDUP_HOME`).
  Generala con el skill `daily-standup-setup` o copiando `config.example.yaml`.
- Los **secretos** (tokens, API keys) nunca van en el config: usá el gestor de secretos del
  runtime o variables de entorno. `config.yaml` solo describe identidad y preferencias.
- Mantené nombres de organización, IDs de tenant, destinatarios e IDs de canal en la config
  local no versionada.

## Degradación

Cuando una fuente no está disponible, seguí adelante con el resto y reportá **menor confianza**
localmente. Nunca simules que una entrega tuvo éxito.
