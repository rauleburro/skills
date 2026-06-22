---
name: jira-task-workflow
description: >
  Workflow completo para implementar tareas individuales de Jira: obtiene el ticket, analiza el código
  y la documentación existente, genera diagramas de arquitectura ASCII, discute la implementación con
  el usuario en un ping-pong interactivo, entra en modo planning, implementa, y verifica cobertura de
  tests al 80% mínimo. Usa este skill cuando el usuario mencione un ID de Jira (ej. "TS-6", "PROJ-45"),
  pida implementar una tarea/ticket/issue, o quiera planificar una implementación basada en un ticket.
  También aplica cuando el usuario diga "trabaja en", "implementa", "tarea", "ticket" seguido de un
  identificador tipo "XXX-NNN". NO usar para épicas completas con múltiples historias — para eso usar
  epic-plan-executor.
---

# Jira Task Workflow

Guía el proceso completo de implementación de una tarea individual de Jira, desde el análisis hasta el código con tests. El valor está en no saltar al código antes de entender el problema — cada fase construye sobre la anterior.

## Flujo general

```
1. Obtener ticket  →  2. Analizar código/docs  →  3. Diagrama arquitectura
                                                           |
                                                           v
4. Ping-pong con usuario  →  5. Modo Planning  →  6. Setup rama + worktree
                                                           |
                                                           v
                                                   7. Implementar + Tests
```

---

## Fase 1: Obtener el ticket de Jira

Cuando el usuario pase un ID de Jira (formato `PROYECTO-NUMERO`):

### Obtención del ticket
Usar herramientas MCP de Jira si están disponibles (`mcp__atlassian__jira_get_issue`). Si no hay MCP, usar la API REST como fallback:

```bash
curl -s -u "$JIRA_USER_EMAIL:$JIRA_API_TOKEN" \
  -H "Content-Type: application/json" \
  "$JIRA_BASE_URL/rest/api/3/issue/PROYECTO-123" | python3 -m json.tool
```

### Qué extraer del ticket
- **Título** y **descripción completa**
- **Tipo** (bug, feature, improvement, task)
- **Prioridad** y **story points** si existen
- **Criterios de aceptación** (suelen estar en la descripción)
- **Subtareas** vinculadas
- **Comentarios** relevantes (pueden tener contexto adicional)

Presenta un resumen estructurado al usuario para confirmar que entendiste la tarea correctamente.

---

## Fase 2: Analizar código fuente y documentación

### Documentación existente
Busca documentación en el proyecto (`docs/`, `Docs/`, o la carpeta que use el proyecto). Lee documentos relacionados con el área que toca la tarea: arquitectura, decisiones previas, specs, guías.

### Código fuente
Usa el agente Explore para análisis profundo del código relacionado:
- Modelos/tipos involucrados y sus relaciones
- Componentes, páginas, o API routes afectados
- Tests existentes en el área
- Middleware, hooks, o código auxiliar relevante
- Dependencias entre módulos

El objetivo es entender el estado actual antes de proponer cambios. No propongas nada todavía — primero entiende.

---

## Fase 3: Diagrama de arquitectura actual (ASCII)

Genera un diagrama ASCII de la arquitectura del área afectada. El diagrama es un apoyo visual — el texto descriptivo es donde está el valor real.

```
+------------------+       +------------------+       +------------------+
|                  |       |                  |       |                  |
|    Componente A  +------>+   Componente B   +------>+   Componente C   |
|                  |       |                  |       |                  |
+------------------+       +--------+---------+       +------------------+
                                    |
                                    v
                           +------------------+
                           |                  |
                           |   Componente D   |
                           |                  |
                           +------------------+
```

### Contenido obligatorio junto al diagrama
- **Descripción de cada componente**: Qué hace, qué archivos lo componen, qué modelos usa
- **Flujo de datos**: Cómo se mueven los datos entre componentes
- **Puntos de integración**: APIs externas, servicios, base de datos
- **Estado actual vs. lo que pide la tarea**: Qué existe y qué falta

---

## Fase 4: Ping-pong con el usuario

Esta es la fase más importante. Aquí se toman las decisiones de diseño.

### Cómo funciona
1. Presenta tu análisis: qué entendiste del ticket, qué encontraste en el código, y tu propuesta de implementación
2. El usuario responde con feedback, preguntas, correcciones, o aprobación
3. Itera hasta alinearse en:
   - **Qué** se va a implementar exactamente
   - **Cómo** se va a implementar (enfoque técnico)
   - **Qué NO** se va a implementar (límites del alcance)
   - **Qué riesgos** existen y cómo mitigarlos

### Reglas del ping-pong
- Sé directo: "propongo X porque Y", no "podríamos considerar tal vez..."
- Máximo 2-3 opciones con pros/contras claros y tu recomendación
- Cuando el usuario decida, confirma y avanza. No re-preguntes lo mismo
- Si la tarea es más grande de lo estimado, dilo y propón cómo dividirla

---

## Fase 5: Modo Planning

Una vez alineados, entra en modo planning (`EnterPlanMode`) para crear el plan de implementación.

### Estructura del plan

1. **Resumen de la tarea** (1-2 oraciones)
2. **Decisiones tomadas** en el ping-pong
3. **Iteraciones** (si la tarea es compleja)
4. **Pasos de implementación** por iteración:
   - Archivos a crear/modificar
   - Modelos/migraciones si aplica
   - Componentes/páginas/API routes
   - Lógica de negocio
5. **Tests requeridos** (ver Fase 6)

### Archivo de iteración

Crear en `docs/<area-tarea>/iteraciones/` (o la carpeta de docs del proyecto):

```markdown
# Iteración NN - <Descripción>

**Ticket**: PROYECTO-XXX
**Fecha**: YYYY-MM-DD
**Estado**: En progreso | Completada

## Objetivo
Qué se busca lograr en esta iteración.

## Decisiones tomadas
- Decisión 1: razón
- Decisión 2: razón

## Cambios realizados
- [ ] Archivo 1: descripción del cambio
- [ ] Archivo 2: descripción del cambio

## Tests
- [ ] Test 1: qué verifica
- [ ] Test 2: qué verifica

## Notas para la siguiente iteración
Qué queda pendiente o qué tener en cuenta.
```

---

## Fase 6: Setup — Rama, worktree y estado Jira

Antes de escribir código, preparar el entorno de trabajo aislado.

### 1. Crear rama desde main
```bash
git checkout main && git pull
git checkout -b feature/<KEY>-<slug>   # ej. feature/IRB-365-restrict-payment-filter
```

### 2. Crear worktree (si se trabaja con agentes en paralelo)
Si se va a usar un agente con `isolation: "worktree"`, el worktree se crea automáticamente. Si se trabaja directamente, la rama creada en el paso anterior es suficiente.

### 3. Mover la tarea a "En curso" en Jira
Usar MCP de Jira para transicionar el ticket al estado "En curso" / "In Progress":
```
mcp__atlassian__jira_transition_issue(issue_key, transition_name="En curso")
```
Esto señaliza al equipo que alguien está trabajando activamente en la tarea.

---

## Fase 7: Implementación + Tests

### Git workflow
- Rama ya creada en Fase 6: `feature/<KEY>-<slug>`
- Commits con formato: `type(scope): description [KEY]`
- No hacer commit con tests fallando o lint errors

### Tests — parte obligatoria, no opcional

**Cobertura mínima**: 80% del código nuevo/modificado (idealmente mayor)

#### Qué cubrir
- **Modelos/tipos**: Creación, validaciones, métodos custom
- **API routes/Server actions**: Respuestas HTTP, validación de input, errores
- **Componentes**: Renderizado, props, interacciones de usuario
- **Edge cases**: Datos vacíos, límites, errores esperados

#### Ejecución de tests
Detectar automáticamente el stack del proyecto y usar los comandos correctos:

```bash
# Next.js / React (Jest)
npm run test -- --coverage

# Django / Python
docker compose exec web python manage.py test <app>
docker compose exec web coverage run --source='<app>' manage.py test <app>

# Otros — usar lo que tenga configurado el proyecto
```

Si la cobertura está por debajo del 80%, identificar qué falta y agregarlo.

### Validación pre-commit
Antes de hacer commit, ejecutar:
```bash
npm run lint    # o el linter del proyecto
npm run test    # todos deben pasar
npm run build   # debe compilar
```

### Al finalizar — Mover a "Code Review" en Jira
Una vez que el código está commiteado, los tests pasan y la validación es exitosa, transicionar el ticket a "Code Review":
```
mcp__atlassian__jira_transition_issue(issue_key, transition_name="Code Review")
```
Esto indica al equipo que la tarea está lista para ser revisada.

---

## Documentación

### Qué documentar
Genera documentación en la carpeta de docs del proyecto cuando la tarea introduce:
- Arquitectura nueva o cambios significativos
- Decisiones de diseño no obvias
- Configuración necesaria
- Flujos de datos complejos

### Convención
Seguir el estilo de la documentación existente. La documentación debe ser útil para alguien que no participó en las decisiones.

---

## Resumen visual

```
  USUARIO PASA ID JIRA
          |
          v
  +--[1. Obtener ticket]--+
  |  - Descripción         |
  |  - Criterios           |
  +----------+-------------+
             |
             v
  +--[2. Analizar código]--+
  |  - Docs existentes      |
  |  - Código fuente        |
  |  - Tests existentes     |
  +----------+--------------+
             |
             v
  +--[3. Diagrama ASCII]---+
  |  - Arquitectura actual  |
  |  - Texto descriptivo    |
  +----------+--------------+
             |
             v
  +--[4. Ping-pong]--------+
  |  - Propuesta            |
  |  - Feedback             |  <--- Loop hasta alineamiento
  |  - Decisiones           |
  +----------+--------------+
             |
             v
  +--[5. Planning]---------+
  |  - Plan de implementación|
  |  - Iteraciones          |
  +----------+--------------+
             |
             v
  +--[6. Setup]-------------+
  |  - Rama desde main       |
  |  - Worktree si aplica    |
  |  - Jira → "En curso"    |
  +----------+--------------+
             |
             v
  +--[7. Implementar]------+
  |  - Código + Tests       |
  |  - 80% coverage mínimo  |
  |  - lint + build OK      |
  |  - Jira → "Code Review" |
  +-------------------------+
```
