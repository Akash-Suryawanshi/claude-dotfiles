#!/bin/bash
# Hook: PostToolUse on ExitWorktree.
# When a worktree whose name matches the configured JIRA ticket prefix is removed
# (action=remove), nudge the active Claude session to transition the matching
# ticket to Done. The hook itself doesn't call JIRA — Claude has atlassian MCP
# access and runs the transition based on additionalContext.
#
# Configure via shell rc (export these before starting Claude Code):
#   export JIRA_TICKET_PREFIX="MLT"                              # required to fire
#   export JIRA_CLOUD_ID="00000000-0000-0000-0000-000000000000"  # required to fire
#   export JIRA_DONE_TRANSITION_ID="31"                          # optional (default 31)
# Look up cloudId via mcp__atlassian__getAccessibleAtlassianResources.

set -e

input="$(cat)"

# Only fire on action=remove (i.e., the user actually deleted the worktree+branch).
action="$(printf '%s' "$input" | jq -r '.tool_input.action // empty')"
[ "$action" = "remove" ] || exit 0

# Extract the worktree directory name from the tool response. The success
# message embeds the path: "Exited and removed worktree at .../.claude/worktrees/<name>."
name="$(printf '%s' "$input" | jq -r '.tool_response | tostring' \
  | grep -oE '\.claude/worktrees/[a-zA-Z0-9_-]+' \
  | head -1 \
  | sed 's|.*/||')"
[ -n "$name" ] || exit 0

# Normalize and match against the configured ticket prefix. Without
# JIRA_TICKET_PREFIX set the hook is a no-op.
prefix="${JIRA_TICKET_PREFIX:-}"
[ -n "$prefix" ] || exit 0
ticket="$(printf '%s' "$name" | tr '[:lower:]' '[:upper:]')"
printf '%s' "$ticket" | grep -qE "^${prefix}-[0-9]+$" || exit 0

CLOUD_ID="${JIRA_CLOUD_ID:-}"
DONE_ID="${JIRA_DONE_TRANSITION_ID:-31}"
[ -n "$CLOUD_ID" ] || exit 0

# Emit additionalContext for Claude. systemMessage shows in the UI; the model
# reads additionalContext to know what to do next.
jq -n \
  --arg t "$ticket" \
  --arg cloud "$CLOUD_ID" \
  --arg done "$DONE_ID" '
{
  "systemMessage": ($t + " worktree removed — closing JIRA ticket"),
  "hookSpecificOutput": {
    "hookEventName": "PostToolUse",
    "additionalContext": (
      "Worktree for " + $t + " was just removed (branch+wt deletion = task complete per project convention). " +
      "Transition " + $t + " to Done via mcp__atlassian__transitionJiraIssue with " +
      "cloudId=" + $cloud + ", issueIdOrKey=" + $t + ", transition={\"id\":\"" + $done + "\"}. " +
      "Optional sanity check: run `gh pr list --state merged --head " + $t + "` first to confirm a merged PR exists; " +
      "if none exists, surface that and skip the transition."
    )
  }
}'
