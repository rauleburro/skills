---
name: daily-standup
description: Genera un daily/standup basado en evidencia real reconciliando sesiones de agentes de código, git local, GitHub, el issue tracker (Jira/roadmap/Linear), la mensajería del equipo (Slack/Teams), el mail y el calendario del usuario. Persiste cada reporte en SQLite y cruza los compromisos del daily anterior contra la evidencia para detectar lo que quedó sin hacer. Puede entregarlo por el conector de mensajería configurado. Úsalo cuando el usuario pida "daily", "standup", "qué hice ayer", "yesterday/today", "prepara mi daily", o un recap de trabajo. Trigger words: daily, standup, yesterday, today, recap.
argument-hint: "[fecha opcional YYYY-MM-DD]"
compatibility: Funciona con Codex, Claude Code y agentes open-source compatibles con Agent Skills. Requiere ~/.daily-standup/config.yaml (genéralo con el skill daily-standup-setup). Cada fuente y la entrega son opcionales y degradan con elegancia.
---

# Daily Standup

Genera un daily conciso en primera persona a partir de **evidencia verificable**, reconciliando múltiples fuentes en vez de confiar en una sola. Cada reporte aprobado se persiste en SQLite para **auditar los compromisos** en dailys futuros.

**Antes de correr el workflow**, leé la configuración y las referencias:

1. `~/.daily-standup/config.yaml` (si no existe, avisá al usuario que corra el skill `daily-standup-setup`; mientras tanto usá `config.example.yaml` como defaults).
2. `references/SOURCE_QUERIES.md` — comandos exactos por fuente.
3. `references/HISTORY.md` — ciclo de compromisos (SQLite).
4. `references/REPORT_TEMPLATE.md` — plantilla de salida.
5. `references/PORTABILITY.md` — cómo mapear cada capacidad a distintos runtimes.

## Reglas

1. Usá la zona horaria configurada (`time.timezone`) para todos los límites del reporte.
2. De martes a viernes, `yesterday` es el día calendario anterior. El lunes cubre el viernes anterior y el finde (`monday_uses_previous_friday`).
3. Excluí temas personales del canal salvo que el usuario los pida; los bloqueos personales van solo en la nota privada al usuario.
4. Reportá solo afirmaciones respaldadas por evidencia; **deduplicá** el mismo resultado que aparece en varias fuentes.
5. El issue tracker es **solo lectura**: nunca mutar issues, comentarios, worklogs ni asignaciones.
6. Verificá antes de afirmar: no digas "merged" si la PR sigue abierta; no atribuyas PRs ajenas. La búsqueda de commits en la rama default de GitHub es incompleta — mirá las PRs y sus ramas.
7. Nunca expongas secretos, prompts crudos de sesiones, datos de clientes ni identificadores de tenant.
8. Lenguaje conciso, primera persona, un hecho o plan concreto por bullet. Sin relleno.

## Workflow

### 0. Fechas

Fecha del daily: `$ARGUMENTS` si viene, si no hoy. Resolvé la hora actual en la zona configurada y calculá las ventanas `yesterday` (día hábil anterior) y `today`. Honrá rangos explícitos si el usuario los da.

### 1. Histórico y compromisos abiertos

```bash
scripts/standup_db.sh pending        # compromisos abiertos de dailys anteriores
scripts/standup_db.sh last 1         # último reporte completo
```

Anotá cada compromiso abierto: hay que verificarlo contra la evidencia del Paso 2. Detalle en `references/HISTORY.md`.

### 2. Recolectar evidencia (en paralelo)

Recorré **solo las fuentes con `enabled: true`** en el config. Comandos exactos en `references/SOURCE_QUERIES.md`. Cada fuente que falle → degradá y anotá menor confianza (no inventes).

1. **Sesiones de agentes** (`sources.agent_sessions`): transcripts modificados en la ventana. Capturá objetivo + resultado verificado + proyecto + PR/issue enlazado + próximo paso pendiente. **Nunca** copies prompts privados al reporte.
2. **Git local** (`sources.git`): commits del usuario en la ventana en todos los repos bajo `roots`. Incluí todas las ramas (`--all`).
3. **GitHub** (`sources.github`): eventos del usuario (`gh api users/<login>/events`) y **estado real** de las PRs tocadas (¿mergeada?, ¿a qué rama base?, ¿esperando review de quién?).
4. **Issue tracker** (`sources.issue_tracker`): consultas de solo lectura de issues actualizados/resueltos en la ventana + issues activos asignados para el plan de hoy. Leé issues referenciados por sesiones/PRs aunque haya cambiado el assignee. No infieras "hecho" por una fecha de resolución vieja en un issue solo editado ayer.
5. **Mensajería** (`sources.messaging`): tus **propios mensajes** en los canales configurados durante la ventana — decisiones, avisos, acuerdos, bloqueos que planteaste. Es evidencia de trabajo y coordinación. No cites mensajes de terceros salvo para dar contexto mínimo.
6. **Mail** (`sources.mail`): correos que **enviaste** en la ventana (`only_sent_by_me`) — envíos, coordinación, decisiones comunicadas. Nunca vuelques contenido sensible al canal.
7. **Calendario** (`sources.calendar`): eventos de **hoy** para detectar bloqueos de agenda. Los eventos personales no van al daily, pero se avisan en la nota privada.

### 3. Cruce de compromisos

Para cada compromiso abierto del Paso 1, buscá evidencia (commit, PR, issue movido de estado, sesión, mensaje, mail). Clasificá:

- **done** — hay evidencia → va en Yesterday.
- **carried** — sin evidencia y sigue vigente → repetir en Today y avisar al usuario ("esto lo prometiste el X y no hay rastro").
- **dropped** — ya no aplica → confirmarlo con el usuario.

### 4. Reconciliar y redactar

Armá una tabla privada de evidencia con una fila por resultado y columnas por fuente (sesiones / git / github / tracker / mensajería / mail). Preferí resultados corroborados por más de una fuente; omití duplicados, intención vaga, actividad personal e inferencia sin respaldo.

Redactá con `references/REPORT_TEMPLATE.md`:
- Secciones `yesterday` y `today` (títulos según `output.headings`), bullets `- ` de una línea, en el idioma de `output.language`.
- `yesterday`: resultados verificados del día hábil anterior.
- `today`: trabajo ya hecho hoy + planes concretos derivados de sesiones sin cerrar, PRs activas, issues del tracker y compromisos arrastrados.
- `@Nombre` **solo si necesitás algo de esa persona** (review, merge coordinado, decisión). Avisos informativos van sin mención.

Presentá el borrador **+ una nota privada** para el usuario con: compromisos incumplidos detectados, issues/tareas vencidas del tracker, y bloqueos de calendario.

### 5. Validar

Verificá que cada bullet sea conciso, en primera persona, no duplicado, respaldado y libre de secretos. Confirmá que se consideró el trabajo de ramas de PR y que el tracker quedó en solo lectura.

### 6. Entregar

Según `delivery`:

- Corridas agendadas: auto-envían **solo si** `scheduled_run_auto_send: true`.
- Corridas manuales: requieren confirmación salvo que el usuario haya pedido explícitamente enviar (`manual_run_requires_confirmation`).
- Resolvé el destino exacto (`destination_name`) antes de escribir.
- Usá `content_format`. Para Teams HTML, mandá por el campo HTML del conector con tags semánticos, no Markdown crudo.
- Enviá solo el standup; los diagnósticos de fuentes quedan locales.
- Si la entrega falla, preservá el borrador y reportá el bloqueo sin declarar éxito.

### 7. Persistir (al aprobar el usuario)

```bash
scripts/standup_db.sh save <fecha> <archivo_md> ["notas"]
scripts/standup_db.sh add-commitment <fecha> "<cada bullet de Today>"
scripts/standup_db.sh resolve <id> done|carried|dropped ["evidencia"]   # compromisos previos
```

Guardá el `.md` temporal en el scratchpad de la sesión, no en el repo.

### 8. Cierre

Devolvé el standup final, los conteos de sesiones/commits/PRs/issues/mensajes inspeccionados, el estado de entrega, los compromisos arrastrados y cualquier fuente no disponible que haya reducido la confianza. Si el runtime tiene memoria persistente (p. ej. engram), guardá un resumen de sesión.
