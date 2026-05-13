#!/bin/bash
# Send an email (supports attachments)
# Usage: ./send-email.sh <to> <subject> <body> [cc] [bcc] [from] [attachments]
# For multiple recipients, pass comma-separated: "a@example.com,b@example.com"
# For multiple attachments, pass comma-separated absolute paths: "/path/one.pdf,/path/two.md"
# Output: Success or error message

TO="${1:-}"
SUBJECT="${2:-}"
BODY="${3:-}"
CC="${4:-}"
BCC="${5:-}"
FROM="${6:-}"
ATTACHMENTS="${7:-}"

if [ -z "$TO" ]; then
    echo "ERROR:Recipient (to) is required"
    exit 1
fi

if [ -z "$SUBJECT" ]; then
    echo "ERROR:Subject is required"
    exit 1
fi

if [ -z "$BODY" ]; then
    echo "ERROR:Body is required"
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

# Escape special characters for AppleScript
escape_for_applescript() {
    echo "$1" | sed 's/\\/\\\\/g' | sed 's/"/\\"/g' | tr '\n' '\r' | sed 's/\r/\\n/g'
}

ESCAPED_SUBJECT=$(escape_for_applescript "$SUBJECT")
ESCAPED_BODY=$(escape_for_applescript "$BODY")

# Build recipient commands
build_recipients() {
    local TYPE="$1"
    local ADDRESSES="$2"
    local RESULT=""

    IFS=',' read -ra ADDR_ARRAY <<< "$ADDRESSES"
    for addr in "${ADDR_ARRAY[@]}"; do
        addr=$(echo "$addr" | xargs)  # trim whitespace
        if [ -n "$addr" ]; then
            RESULT="$RESULT
        make new $TYPE recipient at end of $TYPE recipients with properties {address:\"$addr\"}"
        fi
    done
    echo "$RESULT"
}

# Build attachment commands. Files are attached after the last paragraph of the body.
build_attachments() {
    local PATHS="$1"
    local RESULT=""

    IFS=',' read -ra PATH_ARRAY <<< "$PATHS"
    for p in "${PATH_ARRAY[@]}"; do
        p=$(echo "$p" | xargs)
        if [ -n "$p" ]; then
            RESULT="$RESULT
        make new attachment with properties {file name:(POSIX file \"$p\")} at after last paragraph"
        fi
    done
    echo "$RESULT"
}

TO_RECIPIENTS=$(build_recipients "to" "$TO")
CC_RECIPIENTS=""
BCC_RECIPIENTS=""
ATTACHMENT_CMDS=""
FROM_PART=""
DELAY_FOR_ATTACH=""

if [ -n "$CC" ]; then
    CC_RECIPIENTS=$(build_recipients "cc" "$CC")
fi

if [ -n "$BCC" ]; then
    BCC_RECIPIENTS=$(build_recipients "bcc" "$BCC")
fi

if [ -n "$FROM" ]; then
    FROM_PART=", sender:\"$FROM\""
fi

if [ -n "$ATTACHMENTS" ]; then
    ATTACHMENT_CMDS=$(build_attachments "$ATTACHMENTS")
    # Allow Mail to load attachments fully before sending
    DELAY_FOR_ATTACH="delay 1"
fi

osascript <<EOF
tell application "Mail"
    set newMessage to make new outgoing message with properties {subject:"$ESCAPED_SUBJECT", content:"$ESCAPED_BODY"$FROM_PART}
    tell newMessage
        $TO_RECIPIENTS
        $CC_RECIPIENTS
        $BCC_RECIPIENTS
        $ATTACHMENT_CMDS
        $DELAY_FOR_ATTACH
    end tell
    send newMessage
    return "Message sent successfully"
end tell
EOF
