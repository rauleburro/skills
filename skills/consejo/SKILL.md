---
name: consejo
description: Put one question to a council of 5 independent counsellors — 3 clean-context Claude (Opus) agents with different stances (advocate, adversary, pragmatist) and 2 Codex counsellors in adversarial mode — and follow the majority vote. Falls back to the 3 Claude counsellors when Codex is not installed, not logged in, or out of usage. Use when the user says "consejo", "el consejo", "lanza el consejo", "pregunta al consejo", "ask the council", or when you or a sub-agent face a design or scope doubt with real options that you cannot settle alone and would otherwise guess.
argument-hint: "<question> [options: A / B / ...] [context: files, facts]"
---

# El consejo

Five counsellors answer the same question on the same facts, each on their own, and the majority decides. The point is independent judgement: no counsellor sees another's answer, and none of them acts.

## 1. Build the brief

Write one brief file (in the scratchpad or a temp dir) with:

- **Question**, in one sentence.
- **Options**, as a short list with exact labels (`tabs` / `espacios`). If the question is open, write the 2–4 real options first; a vote needs options.
- **Context**: the facts that decide it, the files to read (absolute paths), constraints, and what is already decided. Same facts for everyone; do not lean toward an option in the wording.
- **Language**: answer in the caller's language (Spanish or English).

## 2. Check Codex

The helper lives in this skill's directory (`~/.claude/skills/consejo` or `~/.agents/skills/consejo` when installed globally):

```bash
H=~/.claude/skills/consejo/scripts/codex-counsellor.sh   # adjust to where the skill is installed
$H check
```

Exit 0: run 5 counsellors. Exit 2 (not installed, not logged in): run the 3 Claude counsellors only, and say so in the verdict.

## 3. Run all counsellors in parallel

Send everything in **one message**: three Agent calls and two background Bash calls.

**Claude counsellors** — Agent tool, `model: "opus"`, a fresh agent each (never a fork), read-only (`subagent_type: "Explore"` or `"Plan"` when available, otherwise `general-purpose`). Prompt = the brief + the stance + the rules + the output contract:

| Counsellor | Stance |
|---|---|
| `claude-advocate` | Make the strongest honest case for the option you find best; steelman it. |
| `claude-adversary` | Attack every option, the obvious one first; vote for the one that survives. |
| `claude-pragmatist` | Weigh cost, risk, reversibility and time; pick what a senior engineer would ship today. |

**Codex counsellors** — the helper runs `codex exec` read-only (`-s read-only`, `gpt-6.1-sol`, effort `xhigh`; override with `CONSEJO_CODEX_MODEL` / `CONSEJO_CODEX_EFFORT`). Use `run_in_background: true` and a timeout of 600000:

```bash
$H run adversary <brief> <dir>/codex-adversary.md <repo-dir>
$H run premortem <brief> <dir>/codex-premortem.md <repo-dir>
```

Exit 0: the answer is in the out file. Exit 2 (usage limit, auth): drop that counsellor and note "Codex unavailable". Exit 1: note the failure; do not retry more than once.

**Rules every counsellor gets, verbatim:**

> You are read-only: read files and run read-only commands only; never edit, create, commit, push, comment or take any action beyond answering. Argue independently from the facts given. End with exactly:
> `VOTE: <option exactly as listed>`
> `CONFIDENCE: <0.0-1.0>`
> `RATIONALE: <one paragraph>`

## 4. Tally

Read the last `VOTE:` line of each answer. A vote outside the listed options, or a missing one, is an abstention.

- **Majority wins**: the option with more votes than any other (3 of 5, 2 of 3, or a plurality when votes split three ways with a clear leader).
- **Empate** (tie for first place, e.g. 2–2 when a counsellor failed): no decision. Return `empate` and escalate: the caller decides with the dissent in view, or asks the human. A sub-agent always escalates to its caller.
- Fewer than 3 valid votes: no quorum; escalate the same way.

Do not override the majority with your own opinion. If you think the council missed a fact, say so under the verdict and let the caller rerun it with that fact in the brief.

## 5. Verdict

Reply with this block (in the caller's language):

```text
CONSEJO — <question>
Counsellors: <5 | 3 (Codex unavailable: reason)>
- claude-advocate    <vote> (<confidence>)
- claude-adversary   <vote> (<confidence>)
- claude-pragmatist  <vote> (<confidence>)
- codex-adversary    <vote> (<confidence>)
- codex-premortem    <vote> (<confidence>)
Decision: <option> (<n>-<m>)  |  empate → escalate to <caller / human>
Dissent: <one or two lines: the strongest argument of the minority>
```

The caller records one line where the decision applies (the PR description or the goal document), e.g. `Consejo (4-1): espacios — YAML forbids tabs for indentation.`

## Rules

- Counsellors never edit, commit, push, comment, or open issues; the skill never asks them to act. Acting on the decision is the caller's job, under its own rules.
- Same brief, same facts for all. No counsellor sees another's answer.
- One council per question. Do not rerun until the result you want comes out; rerun only when the brief was missing a fact, and say so.
- On a Codex host (no Agent tool with `model`), the 3 Claude counsellors become 3 clean-context sub-agents with the same stances; if none can be spawned, report that the council cannot run.
