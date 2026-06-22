---
name: epic-plan-executor
description: >
  Ejecuta planes de implementación multi-historia (épicas) de Jira de forma estructurada por fases.
  Coordina trabajo secuencial y paralelo, gestiona transiciones de Jira automáticamente,
  crea branches por historia, mergea al final, y valida con lint/test/build.
  Usa este skill cuando el usuario quiera ejecutar un plan con múltiples historias de Jira,
  implementar una épica completa, o coordinar varias tareas de setup/implementación en fases.
  También aplica cuando el usuario diga "implementa este plan", "ejecuta la épica",
  "haz el setup del proyecto", o presente una tabla de historias de Jira para ejecutar.
---

# Epic Plan Executor

Ejecuta planes de implementación estructurados en fases, donde cada fase contiene una o más historias de Jira. El valor está en la coordinación: secuenciar lo que debe ir en orden, paralelizar lo que puede ir en paralelo, y mantener Jira sincronizado con el progreso real.

## Cuándo usar este skill

- El usuario presenta un plan con fases y múltiples historias de Jira
- Hay una épica con historias que deben ejecutarse en orden específico
- Se necesita setup inicial de proyecto (pero el patrón aplica a cualquier épica)

## Entrada esperada

El plan del usuario debe incluir (o tú debes preguntar por):

1. **Historias de Jira** con sus keys (ej. TS-6, TS-7)
2. **Fases** con orden de ejecución y dependencias
3. **IDs de transición** de Jira (ej. 31 = En curso, 41 = Listo)
4. **Archivos protegidos** que no se deben modificar
5. **Criterios de validación** para la fase final

## Flujo de ejecución

```
Fase 0: Preparación (git init, commit inicial)
    |
Fase N (secuencial): Trabajo fundacional que otros necesitan
    |
Fase N+1 (paralelo): Historias independientes en branches separados
    |
Fase merge: Integrar branches, resolver conflictos
    |
Fase estructura: Crear código que depende de todo lo anterior
    |
Fase tests: Cobertura completa
    |
Fase validación: lint + test + build + docker
```

## Reglas de ejecución

### Git
- Cada historia trabaja en su propio branch: `feature/<KEY>-<slug>`
- Branches parten desde `main` para minimizar conflictos
- Formato de commit: `type(scope): description [KEY]`
- Nunca hacer commit con tests fallando o lint errors

### Jira
- Mover la historia a "En curso" AL EMPEZAR el trabajo
- Mover a "Listo" SOLO cuando el trabajo está commiteado
- Usar las herramientas MCP de Jira (`mcp__atlassian__jira_transition_issue`)

### Archivos protegidos
- Nunca modificar archivos que el plan marque como protegidos
- Típicos: README.md, CHANGELOG.md, VERSION, LICENSE, AGENTS.md, docs/

### Paralelización
- Intentar usar agentes en worktrees aislados (`isolation: "worktree"`) para trabajo paralelo
- Si worktrees no están disponibles (sin remote, etc.), ejecutar secuencialmente en branches separados
- Cada agente paralelo recibe instrucciones completas y autónomas

## Fases en detalle

### Fase 0: Preparación
Siempre ejecutar directamente (no delegar):
1. Verificar/inicializar git
2. Commit inicial con archivos existentes
3. Verificar que el directorio está limpio

### Fases secuenciales
Para trabajo que es prerequisito de otros:
1. Mover Jira a "En curso"
2. Crear branch desde main
3. Ejecutar el trabajo
4. Verificar que compila/funciona
5. Commit con mensaje convencional
6. Mover Jira a "Listo"

### Fases paralelas
Para historias independientes:
1. Intentar lanzar agentes con `isolation: "worktree"` y `mode: "bypassPermissions"`
2. Si worktrees fallan, ejecutar secuencialmente:
   - `git checkout main && git checkout -b feature/<KEY>-<slug>`
   - Ejecutar trabajo
   - Commit
   - Repetir para siguiente historia
3. Cada agente/iteración maneja su propia transición de Jira

### Fase de merge
Integrar todas las branches de la fase paralela:
```
git checkout main
git merge feature/<branch-1> --no-edit
git merge feature/<branch-2> --no-edit  # resolver conflictos si hay
git merge feature/<branch-3> --no-edit
git branch -d feature/<branch-1> feature/<branch-2> feature/<branch-3>
```

Para conflictos en package-lock.json (muy común):
1. Aceptar una versión
2. Ejecutar `npm install` para regenerar
3. Completar el merge commit

### Fase de validación
Ejecutar TODOS los checks antes de declarar victoria:
```bash
npm run lint          # 0 errores
npm run test          # todos pasan, coverage >= objetivo
npm run build         # exitoso
docker compose up -d  # servicios levantan
docker compose down   # limpieza
```

## Gestión de errores

- **Build falla**: Leer el error, corregir, nuevo commit (no amend)
- **Lint falla**: Corregir en nuevo commit separado `fix(lint): ...`
- **Tests fallan**: Corregir tests o código, nuevo commit
- **Merge conflicto**: Resolver manualmente, priorizar la versión que tiene más cambios
- **Worktrees no disponibles**: Caer a ejecución secuencial sin pedir al usuario

## Ejemplo de output al usuario

Al finalizar, presentar un resumen tipo:

```
| Fase | Resultado |
|------|-----------|
| Fase 0 | Git init, commit inicial |
| Fase 1 (TS-6) | Next.js + TypeScript + Tailwind |
| Fase 2 (TS-7) | Docker + Docker Compose |
| ...  | ... |
| Validación | lint ✓, test ✓, build ✓, docker ✓ |

Jira: TS-6, TS-7, TS-8, TS-9 todas en estado Finalizada.
```
