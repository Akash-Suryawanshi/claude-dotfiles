---
name: update-docs
description: Use when the user invokes /update_docs or asks to fold a conversation's outputs into the repo's docs. Triggers also on phrases like "update the docs from this conversation", "what should land in the docs", or after a design/scoping session that produced locked decisions. Decides what's agent-actionable, routes to the right file, and protects CLAUDE.md from context-window bloat.
---

# update-docs

## Overview

Fold a conversation's outputs into the repo's docs only when the content is **all three**:

1. **Necessary** — a future agent would re-derive a wrong conclusion or repeat work without it.
2. **Non-redundant** — not already covered in Jira, code, another doc section, or memory.
3. **Concise** — fits in the smallest unit that conveys it (one line, one sentence, one subsection — never a paragraph where a sentence suffices, never a section where a sentence suffices).

If any of the three fails, the content stays in Jira, memory, or the transcript.

**Iron rule for CLAUDE.md**: it loads into every conversation. One line max per update. Substantive content goes to a domain doc; CLAUDE.md only points.

## Decision: does this belong in the docs at all?

For each candidate from the conversation, run this in order. First "no" wins:

1. **Agent-actionable?** Would a future agent re-derive a wrong conclusion or repeat work without this? If no → skip.
2. **Already documented?** In Jira, code, an existing doc section, or memory? If yes → skip (optionally cross-reference).
3. **One-conversation ephemera?** Status snapshots, conversation summaries, debugging logs? → skip.
4. **User preference, not project knowledge?** (Output format, communication style.) → goes to `~/.claude/projects/.../memory/feedback_*.md`, not docs.

Only if all four checks pass does it land in a doc.

## Routing

| Content | Lands in | Form |
|---|---|---|
| Architecture, scope, sampling strategy, eval protocol | Domain doc (`docs/*.md`) | Section / subsection |
| Project invariant that overrides agent defaults | CLAUDE.md | One line; pointer to domain doc if details exist |
| User preference / collaboration style | `memory/feedback_*.md` | Memory file |
| External system pointer (dashboard, Jira project, channel) | `memory/reference_*.md` | Memory file |
| Ticket-specific output (clip IDs, scripts, schedules) | Jira ticket | Cross-reference from the doc |

## CLAUDE.md guards

- **One line per update. Never a paragraph.** Pointer line format: `**<topic>**: <one-sentence claim>. See [doc](path) §N.`
- If it can't compress to one line → it belongs in a domain doc; CLAUDE.md gets the pointer or nothing.
- Never duplicate prose between CLAUDE.md and a domain doc.
- Before editing CLAUDE.md, ask: "Useful in *every* future conversation, or just some?" Only "every" earns a line.

## Workflow

1. **Read current state** of every doc you might touch. The user may have edited since you last saw it.
2. **List candidates** from the conversation. Score each with the 4-step decision out loud (1 line each).
3. **Group skips and adds separately.** Skips are valuable — reporting them proves the line was drawn correctly, not that you forgot the candidate.
4. **Apply minimum-surface-area edits.** Add a section or one sentence; prefer that over rewriting paragraphs.
5. **Never rewrite user-authored prose or tables.** If your update contradicts what's there, add a footnote or adjacent note. The user's cells are the user's call.
6. **Report the diff structurally**: what sections were touched, what was skipped, why.

## Common mistakes

| Mistake | Fix |
|---|---|
| Mirroring a Jira ticket's description into the doc | Cross-reference; never duplicate |
| Adding "context" paragraphs to CLAUDE.md | Move to domain doc; CLAUDE.md gets a pointer line or nothing |
| Bulk-rewriting a table/matrix to match new framing | Update the legend or add a footnote; cells are the user's call |
| Treating user preferences as project knowledge | Memory file, not doc |
| Creating a new doc when an existing §N would fit | Use the existing doc |
| Recording the conversation as a summary | Only locked decisions land; summaries don't |

## Red flags — STOP and re-triage

- "I'll add this to CLAUDE.md so the agent doesn't miss it" → first ask if it belongs in a domain doc
- "A short paragraph in CLAUDE.md will help" → max one line, or move to a doc
- "Let me rewrite this section to match the new framing" → user wrote it; add a note instead
- "This is a nice summary of what we decided" → summaries don't land; only the decision does
- "I'll add it everywhere it could be relevant" → pick one home, cross-reference from others

## Quick reference

```
candidate ──┬─ agent-actionable?       no ─► skip
            ├─ already documented?    yes ─► skip (or x-ref)
            ├─ one-shot ephemera?     yes ─► skip
            ├─ user preference?       yes ─► memory/feedback_*.md
            └─ route by type:
                 arch / strategy / protocol  →  docs/*.md
                 project invariant            →  CLAUDE.md (1 line + pointer)
                 external reference           →  memory/reference_*.md
                 ticket output                →  Jira ticket
```
