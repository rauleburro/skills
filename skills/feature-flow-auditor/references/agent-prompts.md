# Feature Flow Auditor subagent prompts

Use these prompts as templates. Replace `[ROOT]`, `[FEATURE]`, and optional technology hints.

## Model/Data Explorer

```text
In [ROOT], analyze only the data/domain layer for [FEATURE]. Do not edit files. Find models/entities/tables/schemas, relationships, state fields, audit/log tables, managers/signals/hooks, and business invariants. Deliver: (1) absolute file map, (2) entities and relationships, (3) state fields and semantic meaning, (4) functions/methods that mutate state, (5) risks/gotchas. Use exact class/function names.
```

## Entrypoints Explorer

```text
In [ROOT], analyze entrypoints for [FEATURE]. Do not edit files. Find routes/URLs/controllers/views/forms/templates/static JS/admin/API endpoints that users or systems call. Trace the user/system flow from first entrypoint through validation and persistence. Include management UI and API differences. Deliver absolute paths and involved classes/functions.
```

## Integration Explorer

```text
In [ROOT], analyze external integrations for [FEATURE]. Do not edit files. Find clients, SDKs, HTTP calls, middleware services, settings/env variables, payload builders, response parsers, credentials, certs, webhooks, retries, timeouts, and error handling. Deliver a textual pipeline, endpoint list, payload shapes, success/failure behavior, and risks.
```

## Operations Explorer

```text
In [ROOT], analyze operational automation for [FEATURE]. Do not edit files. Find cron/management commands/tasks/queues/batch jobs/deployment config/logging/monitoring. Explain how pending work is selected, retried, marked failed, and recovered. Specifically check whether batch processing groups multiple items or creates one batch per item. Deliver flow, state transitions, and operational risks.
```

## Critical Auditor

```text
In [ROOT], act as an independent critical auditor for [FEATURE]. Do not edit files. Do not repeat the happy path. Challenge the design and prior analysis. Look for omissions, contradictions, security risks, secrets, unsafe endpoints, side effects on GET, idempotency/concurrency gaps, retry/timeout gaps, state ambiguity, one-item batching, duplicate legacy paths, hardcoded placeholders, PII/logging concerns, and testability problems. Return improvements ordered from most urgent/important to least, with quick wins vs larger refactors and absolute path references.
```
