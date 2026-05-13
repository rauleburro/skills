#!/bin/bash
# Create a draft reply to an existing email (supports attachments)
# Usage: ./create-reply-draft.sh <message_id> <body> [reply_all] [account] [mailbox] [attachments]
# For multiple attachments, pass comma-separated absolute paths: "/path/one.pdf,/path/two.md"
# Output: Success or error message

MESSAGE_ID="${1:-}"
BODY="${2:-}"
REPLY_ALL="${3:-false}"
ACCOUNT="${4:-}"
MAILBOX="${5:-INBOX}"
ATTACHMENTS="${6:-}"

if [ -z "$MESSAGE_ID" ]; then
    echo "ERROR:Message ID is required"
    exit 1
fi

if [ -z "$BODY" ]; then
    echo "ERROR:Reply body is required"
    exit 1
fi

# Validate attachments exist before invoking AppleScript
if [ -n "$ATTACHMENTS" ]; then
    IFS=',' read -ra ATTACH_ARRAY <<< "$ATTACHMENTS"
    for path in "${ATTACH_ARRAY[@]}"; do
        path=$(echo "$path" | xargs)
        if [ -n "$path" ] && [ ! -f "$path" ]; then
            echo "ERROR:Attachment not found: $path"
            exit 1
        fi
    done
fi

# Build the account/mailbox part
if [ -n "$ACCOUNT" ]; then
    ACCOUNT_PART="mailbox \"$MAILBOX\" of account \"$ACCOUNT\""
else
    ACCOUNT_PART="mailbox \"$MAILBOX\""
fi

# Build reply command
if [ "$REPLY_ALL" = "true" ]; then
    REPLY_COMMAND="reply theMessage with opening window and reply to all"
else
    REPLY_COMMAND="reply theMessage with opening window"
fi

# Escape the body for AppleScript - handle quotes and newlines
ESCAPED_BODY=$(echo "$BODY" | sed 's/\\/\\\\/g' | sed 's/"/\\"/g' | tr '\n' '\r' | sed 's/\r/" \& return \& "/g')

# Build attachment block (AppleScript). Each line becomes part of the tell replyMessage body.
ATTACHMENT_BLOCK=""
if [ -n "$ATTACHMENTS" ]; then
    IFS=',' read -ra PATH_ARRAY <<< "$ATTACHMENTS"
    for p in "${PATH_ARRAY[@]}"; do
        p=$(echo "$p" | xargs)
        if [ -n "$p" ]; then
            ATTACHMENT_BLOCK="$ATTACHMENT_BLOCK
            tell replyMessage to make new attachment with properties {file name:(POSIX file \"$p\")} at after last paragraph"
        fi
    done
fi

osascript -e "
tell application \"Mail\"
    try
        set theMailbox to $ACCOUNT_PART
        set theMessage to (first message of theMailbox whose id is $MESSAGE_ID)

        set replyMessage to $REPLY_COMMAND

        -- Set the reply body content (the quoted original will appear below in the compose window)
        set content of replyMessage to \"$ESCAPED_BODY\"
        $ATTACHMENT_BLOCK

        return \"Draft reply created successfully\"
    on error errMsg
        return \"ERROR:\" & errMsg
    end try
end tell
"
