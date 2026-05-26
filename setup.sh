#!/bin/bash
# Setup Claude Code dotfiles on a new machine.
#
# Two usage modes:
#   1. Clone-anywhere + symlink:
#        git clone <repo-url> ~/dotfiles/claude-dotfiles
#        cd ~/dotfiles/claude-dotfiles && ./setup.sh
#
#   2. Use as ~/.claude directly (skip this script):
#        mv ~/.claude ~/.claude.bak  # if it exists
#        git clone <repo-url> ~/.claude

set -e

DOTFILES_DIR="$(cd "$(dirname "$0")" && pwd)"
CLAUDE_DIR="$HOME/.claude"

# Refuse to run if invoked from inside ~/.claude itself — that means the
# repo IS the live config, no symlinking needed.
if [ "$DOTFILES_DIR" = "$CLAUDE_DIR" ]; then
    echo "This repo is checked out as ~/.claude itself — no symlinking needed."
    echo "Skipping to plugin install."
else
    echo "Setting up Claude Code dotfiles..."
    echo "  Source: $DOTFILES_DIR"
    echo "  Target: $CLAUDE_DIR"

    mkdir -p "$CLAUDE_DIR"

    # Items to symlink into ~/.claude/
    for item in settings.json CLAUDE.md skills commands hooks agents; do
        source="$DOTFILES_DIR/$item"
        target="$CLAUDE_DIR/$item"

        if [ ! -e "$source" ]; then
            echo "  Skipping (not in repo): $item"
            continue
        fi

        if [ -L "$target" ]; then
            echo "  Removing existing symlink: $target"
            rm "$target"
        elif [ -e "$target" ]; then
            echo "  Backing up existing $target -> $target.bak"
            mv "$target" "$target.bak"
        fi

        ln -s "$source" "$target"
        echo "  Linked: $target -> $source"
    done

    # Ensure hook scripts are executable.
    chmod +x "$DOTFILES_DIR"/hooks/*.sh 2>/dev/null || true
fi

# Install plugins listed in settings.json -> enabledPlugins.
echo ""
echo "Installing plugins..."
PLUGINS=(
    "code-review@claude-plugins-official"
    "ralph-loop@claude-plugins-official"
    "hookify@claude-plugins-official"
    "explanatory-output-style@claude-plugins-official"
    "code-simplifier@claude-plugins-official"
    "superpowers@claude-plugins-official"
    "pr-review-toolkit@claude-plugins-official"
    "frontend-design@claude-plugins-official"
    "learning-output-style@claude-plugins-official"
)

if command -v claude &> /dev/null; then
    for plugin in "${PLUGINS[@]}"; do
        echo "  Installing: $plugin"
        claude plugins install "$plugin" 2>/dev/null || echo "    (skipped or already installed)"
    done
else
    echo "  Claude CLI not found. Install it first, then re-run this script."
    echo "  Or install plugins manually:"
    for plugin in "${PLUGINS[@]}"; do
        echo "    claude plugins install $plugin"
    done
fi

# Optional: enable the JIRA-close hook by setting these in your shell rc.
echo ""
echo "Optional (only if you use the JIRA-close-on-worktree-remove hook):"
echo "  Add to ~/.bashrc / ~/.zshrc:"
echo "    export JIRA_TICKET_PREFIX=\"XXX\"     # your project's ticket prefix"
echo "    export JIRA_CLOUD_ID=\"<uuid>\"        # via atlassian MCP"
echo "    export JIRA_DONE_TRANSITION_ID=31    # defaults to 31"

echo ""
echo "Done! Restart Claude Code to pick up changes."
