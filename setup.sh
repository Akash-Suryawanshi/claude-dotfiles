#!/bin/bash
# Setup Claude Code dotfiles on a new machine
# Usage: git clone <repo-url> && cd claude-dotfiles && ./setup.sh

set -e

DOTFILES_DIR="$(cd "$(dirname "$0")" && pwd)"
CLAUDE_DIR="$HOME/.claude"

echo "Setting up Claude Code dotfiles..."
echo "  Source: $DOTFILES_DIR"
echo "  Target: $CLAUDE_DIR"

mkdir -p "$CLAUDE_DIR"

# Symlink settings, skills, and commands
for item in settings.json skills commands; do
    target="$CLAUDE_DIR/$item"
    source="$DOTFILES_DIR/$item"

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

# Install plugins
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

echo ""
echo "Done! Restart Claude Code to pick up changes."
