# claude-dotfiles

Portable Claude Code config — hooks, skills, slash commands, and user-scope CLAUDE.md.
Drop this in `~/.claude/` (or symlink via `setup.sh`) and your Claude Code setup
travels with you.

## What's in here

```
.
├── settings.json          Claude Code user settings (model, plugins, hooks)
├── CLAUDE.md              user-scope global guidance (test discipline, commit format)
├── hooks/                 hook scripts wired by settings.json
│   ├── html-response-format-reminder.json
│   └── jira-close-on-worktree-remove.sh
├── skills/                user-scope skills (override plugin skills on name collision)
│   ├── ml-code-architect/
│   ├── production-coding/
│   ├── update-docs/
│   └── writing-tests/
├── commands/              user-scope slash commands
│   ├── fix-github-issue.md
│   └── prev-commits.md
├── agents/                user-scope subagent definitions (drop .md files here)
└── setup.sh               bootstrap script for a fresh machine
```

What's deliberately **not** tracked: `.credentials.json` (OAuth token),
`projects/` (per-project memory + chat history), `plugins/` (reproduced from
`settings.json:enabledPlugins`), and all ephemeral runtime state.
See `.gitignore` for the deny-by-default whitelist.

## Install on a new machine

```bash
git clone https://github.com/Akash-Suryawanshi/claude-dotfiles.git ~/dotfiles/claude-dotfiles
cd ~/dotfiles/claude-dotfiles
./setup.sh
```

`setup.sh` will:

1. Symlink `settings.json`, `CLAUDE.md`, `skills/`, `commands/`, `hooks/`, `agents/`
   into `~/.claude/`, backing up any existing entries to `*.bak`.
2. Install the plugins listed in `settings.json:enabledPlugins`
   (idempotent — skips if already installed).

Alternative: clone directly as `~/.claude` (skips the symlink step):

```bash
mv ~/.claude ~/.claude.bak    # if you already have one
git clone https://github.com/Akash-Suryawanshi/claude-dotfiles.git ~/.claude
```

Either way, you'll need to log into Claude Code on each machine —
the OAuth token regenerates and lives at `~/.claude/.credentials.json` (gitignored).

## Optional: enable the JIRA-close hook

`hooks/jira-close-on-worktree-remove.sh` fires when an `MLT-XXX`-style worktree is
removed and asks Claude to mark the matching JIRA ticket Done via the
`atlassian` MCP. It's a no-op until you set:

```bash
# ~/.bashrc or ~/.zshrc
export JIRA_TICKET_PREFIX="XXX"                 # e.g. MLT, ENG, INFRA
export JIRA_CLOUD_ID="00000000-0000-0000-0000-000000000000"
export JIRA_DONE_TRANSITION_ID=31               # optional (default 31)
```

Look up `JIRA_CLOUD_ID` via `mcp__atlassian__getAccessibleAtlassianResources`.

## Updating

This repo IS the source of truth. Edit files in place, commit, push.

```bash
cd ~/.claude   # or wherever you cloned it
git add <files>
git commit -m "..."
git push
```

On other machines: `git -C ~/.claude pull`.
