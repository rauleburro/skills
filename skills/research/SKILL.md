---
name: research
description: >
  Conduct focused technical research on a problem before implementation. Use when the user
  asks to investigate, research, deep-dive, or understand a technical issue (bugs, platform quirks,
  integration problems). Produces a concise consolidated report plus optional detail docs.
---

# Research Skill

Investigate a technical problem efficiently and persist what you learn so the team never
re-investigates the same topic twice.

## 1. Scope the topic

Extract from the user's message (ask only if genuinely unclear):

- **Topic slug**: kebab-case folder name, e.g. `bluetooth-audio-routing`
- **Stack**: platform/language/framework
- **Symptom**: observed vs expected behavior
- **Known**: hypotheses already tried

## 2. Prepare the workspace

Run `scripts/init-research.sh {topic-slug}` to create the docs folder.

## 3. Launch 3 default agents in parallel

Each agent gets a one-line angle plus the shared context. Read `reference/agent-prompts.md`
when you need the exact prompt wording.

1. **Codebase analysis** (Explore agent) — find relevant code, gaps, file:line references.
2. **Root-cause theory** (web agent) — why it happens at the OS/framework/protocol level.
3. **Solutions & validation** (web agent) — native APIs, libraries, community-confirmed fixes.

Spawn the optional 4th/5th agent **only** if the user explicitly asks for library comparison
or cross-platform API deep-dive.

## 4. Synthesize

Create exactly these two files:

- `docs/{topic}/NOTAS.md` — raw findings, snippets, URLs, quick observations.
- `docs/{topic}/RESEARCH_CONSOLIDADO.md` — structured master doc.

Use `reference/consolidated-template.md` only when you need the full template.
Optional detail files (`03_android_api.md`, `04_librerias.md`, etc.) are created only when
findings justify them.

## 5. Finalize

Run `scripts/finalize-research.sh {topic-slug}` to validate the master doc exists and append
an iteration row. Then report to the user:

1. Root cause (with file:line if applicable)
2. Top 3 non-obvious findings
3. Files created
4. Suggested next step

Keep the chat report concise; the detail lives in the docs.
