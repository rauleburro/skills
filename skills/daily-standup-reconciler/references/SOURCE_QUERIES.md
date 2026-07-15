# Source query patterns

Adapt these examples to the available connector.

## GitHub

```text
org:ORGANIZATION author:LOGIN author-date:YYYY-MM-DD..YYYY-MM-DD
org:ORGANIZATION author:LOGIN updated:YYYY-MM-DD..YYYY-MM-DD
```

Fetch relevant PR branch commits because default-branch commit search may omit unmerged work.

## Jira

```jql
assignee = currentUser() AND updated >= "YYYY-MM-DD" AND updated < "YYYY-MM-DD" ORDER BY updated DESC
```

```jql
assignee = currentUser() AND resolved >= "YYYY-MM-DD" AND resolved < "YYYY-MM-DD" ORDER BY resolved DESC
```

```jql
assignee = currentUser() AND statusCategory != Done ORDER BY priority DESC, updated DESC
```

When appropriate, narrow planning to active-sprint parent issues. Keep all queries read-only.

