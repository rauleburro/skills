# Runtime portability

This skill uses the open Agent Skills directory convention and capability-based instructions.

| Capability | Possible implementations |
|---|---|
| session history | runtime API, MCP server, authorized JSONL logs |
| GitHub | GitHub MCP, REST/GraphQL, `gh` |
| Jira | Atlassian MCP, Jira REST API |
| messaging | Teams/Slack MCP, provider API, approved webhook |
| scheduling | runtime automation, cron, systemd timer, CI schedule |

Install in Codex or Claude through a compatible skills CLI or copy the directory into the runtime's skills folder. Open-source agents can load `SKILL.md` directly when they do not implement automatic skill discovery.

Credentials must come from a secret store or environment. Keep organization names, tenant IDs, recipients, channel IDs, and account identifiers in an untracked local configuration.

Gracefully degrade when a source is unavailable and report reduced confidence locally. Never pretend a delivery succeeded.

