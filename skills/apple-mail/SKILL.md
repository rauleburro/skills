---
name: apple-mail
description: Send, read, search, reply to, archive, and delete emails through Apple Mail on macOS. Use this skill whenever the user wants to interact with their Mail.app inbox — composing or sending a message (with or without attachments), checking unread mail, finding a specific thread, replying to a sender, cleaning up an inbox, or scripting any email operation locally. Triggers on Mac-specific email tasks like "send Ruben that doc", "what's unread from my boss", "reply to the last invoice", "archive everything from no-reply", "find that flight confirmation", or "draft a message with this PDF attached". Supports file attachments. Requires explicit user confirmation before sending, replying, or deleting.
allowed-tools: Bash, Read, AskUserQuestion
---

# Apple Mail Skill (AiMA fork)

This skill provides commands to interact with Apple Mail on macOS via AppleScript.

It is a user-managed fork of the upstream `rbouschery/marketplace@apple-mail` skill. Differences from the upstream version:

1. **Attachment support** in `send-email.sh`, `create-draft.sh`, and `create-reply-draft.sh` (extra final argument: comma-separated absolute paths). Scripts validate that each file exists before composing the message.
2. **Mandatory confirmation flow** before any outbound or destructive operation (see below). The agent must confirm with the user before invoking scripts that send mail or mutate the mailbox in ways that are hard to reverse.

---

## MANDATORY: confirm before sending or deleting

Sending an email or deleting one from the mailbox is a real-world, externally-visible, hard-to-reverse action. **Before invoking any of the following scripts, you MUST use `AskUserQuestion` (or a plain question in chat if the harness lacks that tool) to confirm with the user, and wait for explicit approval:**

- `send-email.sh` — sends a new message
- `send-draft.sh` — sends the front-most draft (which may already be composed)
- `create-reply-draft.sh` — composes a reply that the user could then send
- `delete-email.sh` — removes a message from the mailbox

The confirmation MUST surface every relevant field, even when the user originally provided them — they may have changed their mind, mistyped, or expect you to derive defaults:

- **From (sender account)** — which configured Mail account will send. If unspecified, list available accounts with `list-accounts.sh` and ask which to use.
- **To** — comma-separated list as it will be sent.
- **Cc / Bcc** — if any.
- **Subject** — exact text.
- **Body** — full text the user will see, not a paraphrase.
- **Attachments** — list of absolute paths (confirm they're the right files; check existence with `ls -la` if uncertain).

For `delete-email.sh`, surface the message id, subject, sender, and target mailbox before confirming.

Only after explicit approval do you invoke the script. If the user requests changes, update the draft locally and re-confirm.

Reading, searching, archiving, marking read/unread, listing, and creating drafts (which stay open for the user to inspect) do NOT require this confirmation — they are read-only or non-destructive operations whose results the user can review before any final commit.

### Suggested confirmation prompt for outbound mail

```
About to send this email — confirm before I proceed:

  From:        <sender>
  To:          <to>
  Cc:          <cc>
  Subject:     <subject>
  Attachments: <path1>, <path2>

  Body:
  ---
  <full body>
  ---
```

Then ask: "Send as-is, edit, or cancel?"

---

## Available Scripts

All scripts are in the `./scripts/` directory (relative to this SKILL.md). Execute them via bash.

### Account & Mailbox Management (read-only)

| Script | Purpose | Arguments |
|--------|---------|-----------|
| `list-accounts.sh` | List all email accounts | none |
| `list-mailboxes.sh` | List mailboxes/folders | `[account]` (optional) |
| `get-unread-count.sh` | Get unread email count | `[account] [mailbox]` (optional) |

### Reading Emails (read-only)

| Script | Purpose | Arguments |
|--------|---------|-----------|
| `get-emails.sh` | Get recent emails | `[account] [mailbox] [limit] [include_content] [unread_only]` |
| `get-email-by-id.sh` | Get specific email by ID | `<id> [account] [mailbox] [include_content]` |
| `search-emails.sh` | Search emails | `<query> [account] [mailbox] [limit]` |

### Sending & Composing

| Script | Purpose | Arguments | Confirm? |
|--------|---------|-----------|----------|
| `send-email.sh` | Send an email | `<to> <subject> <body> [cc] [bcc] [from] [attachments]` | **YES** |
| `send-draft.sh` | Send front-most draft | none | **YES** |
| `create-reply-draft.sh` | Create reply to email | `<message_id> <body> [reply_all] [account] [mailbox] [attachments]` | **YES** |
| `create-draft.sh` | Create a draft email (stays open for review) | `<subject> <body> [to] [cc] [bcc] [from] [attachments]` | optional |

`[attachments]` is a comma-separated list of absolute file paths. Each script verifies the files exist before composing the message; if any path is missing the script aborts with `ERROR:Attachment not found: <path>`.

### Email Management

| Script | Purpose | Arguments | Confirm? |
|--------|---------|-----------|----------|
| `delete-email.sh` | Delete an email | `<message_id> [account] [mailbox]` | **YES** |
| `archive-email.sh` | Archive an email | `<message_id> [account] [mailbox] [archive_mailbox]` | optional |
| `mark-read.sh` | Mark email as read | `<message_id> [account] [mailbox]` | no |
| `mark-unread.sh` | Mark email as unread | `<message_id> [account] [mailbox]` | no |

---

## Output Format

Scripts use delimiters for structured output:
- `<<>>` separates fields within a record
- `|||` separates multiple records
- `ERROR:` prefix indicates an error message

### Email Record Format

```
id<<>>subject<<>>sender<<>>to<<>>cc<<>>bcc<<>>dateSent<<>>isRead<<>>content|||
```

---

## Usage Examples

### List accounts
```bash
./scripts/list-accounts.sh
```

### Get recent emails from INBOX
```bash
./scripts/get-emails.sh "" "INBOX" 10 false false
```

### Search emails
```bash
./scripts/search-emails.sh "meeting notes" "" "" 20
```

### Send an email (only after user confirmation!)
```bash
./scripts/send-email.sh "recipient@example.com" "Subject" "Body text"
```

### Send with CC, BCC, sender, and attachments
```bash
./scripts/send-email.sh \
  "to@example.com" \
  "Subject" \
  "Body" \
  "cc@example.com" \
  "bcc@example.com" \
  "me@example.com" \
  "/path/to/report.pdf,/path/to/diagram.png"
```

### Create a draft with attachment
```bash
./scripts/create-draft.sh \
  "Draft Subject" \
  "Draft body" \
  "recipient@example.com" \
  "" "" "" \
  "/path/to/notes.md"
```

### Reply to an email with an attachment (confirmation required)
```bash
./scripts/create-reply-draft.sh 12345 "Thanks for your message!" false "iCloud" "INBOX" "/path/to/answer.pdf"
```

---

## Parsing Output

When receiving email records, parse them like this:

1. Split by `|||` to get individual records
2. Split each record by `<<>>` to get fields
3. Fields are: id, subject, sender, to, cc, bcc, dateSent, isRead, content

---

## Notes

- Scripts require macOS with Apple Mail configured.
- Apple Mail must have at least one account set up.
- First run may trigger macOS permission prompts for automation.
- Empty optional arguments should be passed as empty strings `""`.
- For scripts that take arrays (multiple recipients or attachments), pass comma-separated values.
- Attachment paths must be absolute, and the files must exist before invoking the script.

---

## Reference

For advanced AppleScript patterns and customization, see `./reference/applescript-patterns.md`.
