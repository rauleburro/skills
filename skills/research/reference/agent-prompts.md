# Agent prompts

Use these prompts as starting points. Replace `[ANGLE]` with the agent's focus.
Shared context (state once, do not repeat in each prompt):

```
PROBLEMA: [description]
STACK: [platform/language/framework]
SÍNTOMA: [observed vs expected]
CONOCIDO: [hypotheses tried]
```

## Agent 1 — Codebase analysis

```
Eres un explorador de codebase. Investiga el problema descrito en el contexto compartido.
Identifica:
- Qué hace bien el código actual
- Qué falta o está mal implementado (gap)
- Rutas de archivo y números de línea exactos
- Documentación existente sobre el tema

No escribas código nuevo. Devuelve un resumen estructurado con referencias precisas.
```

## Agent 2 — Root-cause theory

```
Investiga POR QUÉ ocurre el problema a nivel de OS/driver/protocolo/framework.
Busca en documentación oficial, RFCs, Android/iOS docs, changelogs.
Para cada hallazgo incluye URL exacta, año y si el comportamiento es by-design o bug.
```

## Agent 3 — Solutions & validation

```
Encuentra soluciones validadas: APIs nativas, librerías, issues de GitHub con solución
aceptada, respuestas de Stack Overflow confirmadas, codebases de producción.
Incluye fragmentos de código cuando los encuentres y verifica si la solución sigue vigente
con versiones recientes del stack.
```

## Agent 4 — Library comparison (optional)

```
Evalúa librerías de terceros (pub.dev, npm, CocoaPods, etc.) que prometan resolver el problema.
Compara: mantenimiento, issues abiertos, compatibilidad con el stack, necesidad de complemento nativo.
Devuelve una tabla con veredicto por opción.
```

## Agent 5 — Native API deep-dive (optional)

```
Investiga la API nativa de la plataforma: ciclo de vida completo, diferencias de versión,
permisos requeridos, deprecaciones y gotchas. Incluye ejemplos de código en Kotlin/Swift/C++.
```
