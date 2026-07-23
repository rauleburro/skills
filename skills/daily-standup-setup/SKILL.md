---
name: daily-standup-setup
description: Configura de forma interactiva el skill daily-standup. Detecta lo que puede (login de GitHub, zona horaria, autor de git, rutas de sesiones) y pregunta el resto (organización, proveedor de mensajería y canales, issue tracker, mail, calendario, destino de entrega), y escribe ~/.daily-standup/config.yaml. Úsalo cuando el usuario diga "configura mi daily", "setup del standup", "configurar daily-standup", o cuando el daily-standup no encuentre su config.
compatibility: Funciona con Codex, Claude Code y agentes open-source. Escribe un único archivo de config; no toca secretos.
---

# Daily Standup Setup

Guía al usuario para crear `~/.daily-standup/config.yaml`, la configuración que consume el skill
`daily-standup`. **Nunca** pidas ni escribas tokens o API keys: eso va en el gestor de secretos
del runtime o en variables de entorno. Este skill solo captura identidad y preferencias.

## Paso 1 — Detectar

```bash
scripts/detect.sh
```

Esto imprime valores por defecto (SO, timezone, autor de git, login de GitHub, rutas de sesiones
de agentes, posibles carpetas de repos, si hay `sqlite3`, y si ya existe config). Usalos como
defaults en las preguntas del Paso 2; no vuelvas a preguntar lo que ya se detectó salvo para
confirmar.

Si `config_exists=yes`, avisá que vas a **sobrescribir** (se guarda un `.bak`) y confirmá antes.
Si `sqlite3=no`, avisá que el histórico de compromisos no funcionará hasta instalarlo.

## Paso 2 — Preguntar lo que falta

Preguntá de forma conversacional (agrupá para no abrumar). Para cada fuente, ofrecé
**activarla o no** y, si aplica, el proveedor. Ítems:

- **Identidad**: nombre visible, login de GitHub (detectado), email, usuario del tracker.
- **Tiempo**: timezone (detectado), ¿el lunes cubre el viernes? (sí por defecto).
- **git**: carpetas raíz donde están los repos (detectadas), nombre de autor a matchear.
- **GitHub**: organización (vacío = todos los repos del usuario).
- **Issue tracker**: proveedor (`jira` | `roadmap` | `linear` | `none`) y sitio/host.
- **Mensajería**: proveedor (`slack` | `teams` | `none`) y canales a revisar como evidencia.
- **Mail**: proveedor (`apple_mail` | `gmail` | `none`).
- **Calendario**: proveedor (`apple_calendar` | `google_calendar` | `none`).
- **Entrega**: proveedor y destino (canal/chat), formato (`markdown` | `html`),
  ¿auto-enviar en corridas agendadas? (no por defecto).
- **Salida**: idioma (`es` por defecto).

En macOS, `apple_mail`/`apple_calendar` son buenos defaults; en otros SO ofrecé `gmail`/
`google_calendar`/`none`. Si el usuario no usa alguna fuente, marcala `enabled: false` en vez de
inventar valores.

## Paso 3 — Escribir la config

Pasá las respuestas como variables de entorno a `write_config.sh` (ver la cabecera del script
para la lista completa de `DS_*`). Ejemplo:

```bash
DS_NAME="Raul" DS_GH_LOGIN="rauleburro" DS_EMAIL="raulb@aima.chat" \
DS_TZ="Europe/Madrid" DS_GIT_ROOTS="~/Develop" DS_GIT_AUTHOR="Raul" \
DS_GH_ORG="aima-beyond-ai" DS_TRACKER_PROVIDER="roadmap" \
DS_MSG_PROVIDER="slack" DS_MSG_CHANNELS="#daily, #dev" \
DS_MAIL_PROVIDER="apple_mail" DS_CAL_PROVIDER="apple_calendar" \
DS_DELIVERY_PROVIDER="slack" DS_DELIVERY_DEST="#daily" DS_LANG="es" \
scripts/write_config.sh
```

El script hace backup del config previo, escribe el YAML y respeta `$DAILY_STANDUP_HOME`.
Listas (`DS_GIT_ROOTS`, `DS_MSG_CHANNELS`, `DS_SESSIONS_PATHS`) aceptan valores separados por
coma o espacio.

## Paso 4 — Verificar

```bash
cat ~/.daily-standup/config.yaml
```

Mostrale al usuario el resultado. Recordale que:
- Los **secretos** de cada conector (Slack, tracker, etc.) se configuran aparte en el runtime.
- Puede correr `daily-standup` cuando quiera generar el reporte.
- Puede re-ejecutar este setup para cambiar la config (siempre queda un `.bak`).
