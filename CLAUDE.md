# CLAUDE.md — Home Directory

Global guidance for Claude Code across all projects.

## Auto-Maintain Project CLAUDE.md Files

**Rule**: When you discover something that would have saved time if known earlier → add it to the project's CLAUDE.md immediately.

### Update Triggers
- Non-obvious architecture requiring multiple files to understand
- Configuration relationships and override hierarchies
- Deployment/scaling details (GPU needs, ECR patterns, CI/CD)
- Critical implementation details (correction factors, async patterns)
- Gotchas and working solutions

### Don't Add
- Info in single file / obvious from README
- Generic best practices / file listings

### Format
```markdown
## Knowledge Updates

### [YYYY-MM-DD] - Title
**Finding**: Discovery with file:line refs (2-3 sentences)
**Impact**: Why it matters
```

## Git Commit Format (ticket-based projects)

For projects that link commits to a ticket tracker, use:

```
<branch_name>:- <commit message>
```

Where `<branch_name>` matches the ticket ID (e.g. branch named after the JIRA/Linear/GitHub-issue ID).

**Example:**
```bash
# For branch TICKET-27
git commit -m "TICKET-27:- Add thread-safe progress tracking"
```

**Helper:**
```bash
BRANCH_NAME=$(git rev-parse --abbrev-ref HEAD)
git commit -m "${BRANCH_NAME}:- Your commit message here"
```

This convention ensures commits are automatically linked to tickets for tracking.

## Writing tests — always invoke the `writing-tests` skill

Before adding, reviewing, or trimming any test in any project, invoke the user-scope `writing-tests` skill (located at `~/.claude/skills/writing-tests/SKILL.md`). The skill enforces a necessity-first discipline: every test must declare WHY it exists (Regression / Critical contract / Acceptance criterion / Non-obvious correctness) via its docstring, and tests that don't fit one of the four categories should be deleted rather than written.

**This is a mandatory invocation, not a suggestion.** Test code without category-tagged docstrings is technical debt — the skill exists to prevent it from accumulating.

Triggers (any of these in user request → invoke the skill first):
- "add a test for …", "write tests", "test coverage", "improve coverage"
- "trim tests", "tests are too many", "review the tests"
- "regression test for this fix", "make sure this doesn't break again"
- Any bug fix (regression test goes in the same commit as the fix)
- Any PR review that touches test files
