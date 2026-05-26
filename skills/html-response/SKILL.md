---
name: html-response
description: Use for every substantive response in this session — instead of replying in terminal markdown, compose the response as a single HTML file in the Quiet Luxury aesthetic, serve it on a local HTTP server, and return only the URL. Apply when the user asks a question, requests work, reports results, or any time a "normal" reply would otherwise be more than ~3 lines of terminal markdown. Skip only for trivial acknowledgements ("ok", "done") and when actively running tool chains where the next step depends on terminal output streaming back.
---

# html-response

Every response becomes an **HTML page on a local HTTP server**, not terminal markdown. Akash is a mix of ML engineer, mathematician, coder, and artist; he reads a lot of Claude output and the terminal collapses everything into a linear stream. HTML buys side-by-side panels, real tables, syntax highlighting, KaTeX math, mermaid diagrams, and typographic hierarchy. **The page is the response medium, not a side artifact.**

## Workflow per turn

```
1. Compose the response as HTML content blocks (see catalog below).
2. Copy ~/.claude/skills/html-response/template.html
   to ~/.claude/skills/html-response/state/responses/
   r-<UTC-ISO>.html, replacing the 4 marker comments.
3. Run ~/.claude/skills/html-response/ensure_server.sh   (idempotent)
4. Output ONLY the URL in the terminal (one line, optionally with a ≤10-word
   gist). The page IS the response.
```

Filename pattern: `r-YYYY-MM-DDTHH-MM-SS.html` (UTC, colons replaced with dashes so it's filesystem-safe and lexically sortable). Get it via bash: `date -u +"r-%Y-%m-%dT%H-%M-%S.html"`.

## Trigger rules — when to use this skill

| Situation | Use html-response? |
|---|---|
| Question, explanation, code review, plan, status report | **Yes** |
| Tool result that needs Akash to read it (diffs, logs, screenshots) | **Yes** |
| Verification report after running work | **Yes** |
| Multi-turn tool chain where the next call depends on the output you just produced | No (stay in terminal so the chain can read it) |
| Trivial ack ("done", "ok", "got it") | No |
| Plan-mode `ExitPlanMode` content | No (that flows through the plan file, not the response surface) |

When in doubt, prefer HTML. The cost of an extra page is low; the benefit of one consolidated visual surface per turn is high.

## Template substitution

`template.html` has exactly four marker comments to replace:

| Marker | What goes there |
|---|---|
| `<!--TITLE-->` | Short page title, 2–8 words. Goes in the browser tab AND as the big italic gold H1. Example: "HAB-19 · hero ring flipped". |
| `<!--EYEBROW-->` | Tiny mono uppercase label above the title. Sets context. Example: `HAB-19 · STATUS · 4 COMMITS · PR #14`. Two or three pipe-separated chips work well. |
| `<!--TIMESTAMP-->` | Human-readable time in the footer. Use IST since Akash is there. Example: `2026-05-14 · 16:34 IST`. |
| `<!--CONTENT-->` | The actual response body, as HTML blocks. Use the component catalog. |

Do not touch any CSS, fonts, script tags, or layout. The template is locked.

## Component catalog

Use these semantic classes — they're styled by the template.

### Prose

```html
<div class="r-prose">
  <p>The hero ring on Today now fills from each habit's <em>strength fraction</em> instead of today's completion %. The center number drops from 73 → 67, matching the mean of <code>strengthFraction</code> over the five mock habits.</p>
</div>
```

`<em>` renders as italic Cormorant Garamond gold — use for emphasis sparingly, like a callout in prose. `<code>` renders as a small gold-tinted chip. `<strong>` is plain bright ink, not gold.

### Section heading

```html
<h2 class="r-h2">Design decision <span class="r-h2-accent">— locked</span></h2>
<h3 class="r-h3">option matrix</h3>
```

H2 is Inter 600; the accent span is italic Cormorant gold (use for the right-half of the title). H3 is a small mono eyebrow — use it as a sub-section label, not a heading proper.

### Insight (matches your "★ Insight" pattern)

```html
<div class="r-insight">
  <span class="r-insight-title">insight</span>
  <ul>
    <li>Mock strength values sum to 0.672 → center reads 67. The arithmetic alone validates the wire flip.</li>
    <li>HAB-10's chassis was always metric-agnostic — segments are L1–L7 labels, not progress encoding.</li>
  </ul>
</div>
```

The `★` glyph is added by CSS. Use 2–3 bullets max, dense and specific.

### Callout (info/warn/danger/success)

```html
<div class="r-callout info">
  <div class="r-callout-title">heads up</div>
  Font files at <code>HabitTracker/App/Resources/Fonts/CormorantGaramond-*.ttf</code> are HTML, not TTF. Pre-existing — SwiftUI falls back to system serif silently.
</div>
```

Change `info` → `warn`, `danger`, `success` to shift the left-border color.

### Table

```html
<table class="r-table">
  <thead>
    <tr><th>concern</th><th>before</th><th>after</th></tr>
  </thead>
  <tbody>
    <tr><td>Center number</td><td>73</td><td><strong>67</strong></td></tr>
    <tr><td>Per-ring fill source</td><td><code>todayFraction</code></td><td><code>strengthFraction</code></td></tr>
  </tbody>
</table>
```

`<strong>` inside a cell renders as gold — use to mark the value that changed or the recommended answer.

### Side-by-side panels

```html
<div class="r-grid-2">
  <div class="r-card">
    <div class="r-card-eyebrow">option A · linear</div>
    <p class="r-prose">Each habit's strength fraction maps directly to its ring band's fill. 7 segments stay as L1–L7 milestone labels. <strong>Recommended.</strong></p>
  </div>
  <div class="r-card">
    <div class="r-card-eyebrow">option B · banded</div>
    <p class="r-prose">Segments fill as the user crosses level thresholds. Fights the equal-slot geometry — rejected.</p>
  </div>
</div>
```

Use `r-grid-3` for three columns. Both collapse to single column on narrow screens.

### Big-number stat

```html
<div class="r-grid-3">
  <div class="r-stat"><div class="r-stat-value">67</div><div class="r-stat-label">after · strength %</div></div>
  <div class="r-stat"><div class="r-stat-value">73</div><div class="r-stat-label">before · today %</div></div>
  <div class="r-stat"><div class="r-stat-value">4</div><div class="r-stat-label">commits shipped</div></div>
</div>
```

### Code block (auto-highlighted)

```html
<pre><code class="language-swift">let meters = rows.map { row in
    HabitMeterRing.HabitMeter(
        id: row.id,
        chipColor: row.chipColor,
        strength: row.strengthFraction
    )
}</code></pre>
```

highlight.js auto-detects the language. The `language-<lang>` class hint is optional but speeds detection. Languages supported: swift, python, javascript, typescript, bash, html, css, json, yaml, go, rust, sql, etc.

### Math (KaTeX, $ delimiters)

```html
<p class="r-prose">The mean strength is
$\\bar{s} = \\frac{1}{N}\\sum_{i=1}^{N} s_i = \\frac{0.92 + 0.78 + 0.64 + 0.88 + 0.14}{5} = 0.672$,
which rounds to 67.</p>

<p class="r-prose">Display math is also supported:</p>
$$\\nabla_\\theta \\mathcal{L}(\\theta) = \\mathbb{E}_{x \\sim p_{\\text{data}}}\\left[\\nabla_\\theta \\log p_\\theta(x)\\right]$$
```

Inline math uses `$...$`; display math uses `$$...$$` or `\[...\]`. Use real math notation — never unicode approximations like `∇` or `∑` when KaTeX can render the real glyph. (HTML escapes: in your written .html file the backslashes do NOT need escaping — write `$\nabla$` literally.)

### Mermaid diagram

```html
<div class="r-mermaid">
  <pre class="mermaid">
flowchart LR
    A[strengthFraction] --> B[HabitMeter.strength]
    B --> C[HabitMeterRing arc]
    C --> D{0..1 fill}
    D -->|0.92| E[outer ring · Meditate]
    D -->|0.14| F[inner ring · No sugar]
  </pre>
</div>
```

Mermaid auto-initializes on page load. Use for architecture diagrams, flow, sequence, state, gantt, class.

### Collapsible (long traces, diffs)

```html
<details class="r-collapsible">
  <summary>full sim log · 47 lines</summary>
  <div class="r-collapsible-body">
    <pre><code>2026-05-11 23:33:52.451 ...</code></pre>
  </div>
</details>
```

Use for anything verbose Akash might want to skip on first read but verify on demand.

## Composition principles

1. **Density is a feature.** Long flowing prose belongs in books, not Claude responses. Compress with tables, stat cards, callouts, and side-by-side panels. A single page with 8 well-shaped blocks beats 40 paragraphs of markdown.
2. **Hierarchy maps to scanability.** The title says "what." The lede paragraph (one `r-prose` block right after the rule) says "in one sentence, what changed." Sections via `r-h2` for the major beats. `r-h3` only for narrow sub-labels.
3. **Math, code, and notation stay precise.** Akash is a mathematician — never paraphrase a formula into prose if KaTeX can render it. Never replace a code identifier with a description. Use the real names.
4. **Visual restraint.** The locked aesthetic is Quiet Luxury — gold accents are a *spice*, not the meal. If everything is highlighted, nothing is. Default to plain ink; reserve gold for the title, italic accents, and value-emphasis in tables.
5. **One page = one turn = one URL.** Each response is its own self-contained page. Don't link backward across pages mid-response. The `/index` route handles history.

## Step-by-step example

User asks: "summarize the HAB-19 work and what's left."

```bash
# 1. Build the response file. Use the Write tool, not heredoc-via-bash,
# so the content is auditable in the transcript.
TS=$(date -u +"r-%Y-%m-%dT%H-%M-%S.html")
DEST="$HOME/.claude/skills/html-response/state/responses/$TS"
# (then call Write with file_path=$DEST and content=<full HTML>)

# 2. Ensure server.
~/.claude/skills/html-response/ensure_server.sh
# → prints http://127.0.0.1:4747/

# 3. Output (terminal): just the URL + 8-word gist.
# Example: "HAB-19 shipped, PR #14 open → http://127.0.0.1:4747/"
```

## Fallback when the skill is unavailable

If you're in a session where this SKILL.md is NOT loaded (the tool list won't show it), you can't use this skill — fall back to terminal markdown and flag the gap once at the top of the first response so Akash can decide whether to install/enable.

## Files in this skill

| File | Purpose |
|---|---|
| `SKILL.md` | This file. Loaded into Claude's context when the skill is invoked. |
| `template.html` | Locked canonical template. Read it, copy it, fill four markers, write the copy. |
| `serve.py` | Stdlib HTTP server on port 4747. Routes `/`, `/version`, `/index`, `/r-*.html`. |
| `ensure_server.sh` | Idempotent starter. Safe to call every turn. Prints the URL on success. |
| `state/responses/` | Where response HTMLs live. Created at runtime. |
| `state/server.pid`, `state/server.log` | Runtime — PID + access log. |

## What if the page looks wrong?

- **No styles at all** → CDN blocked or offline. Page still readable, just monochrome. Note the gap in terminal output; suggest Akash check his network or set up local copies of KaTeX/highlight.js if it's persistent.
- **Math renders as raw `$..$`** → KaTeX auto-render didn't fire. Check that the `$` delimiters are paired and not inside `<code>` (which is excluded by default).
- **mermaid block stays as text** → likely a syntax error in the diagram. Open browser devtools console to see the parser error.
- **Server won't start** → another process on port 4747. `lsof -nP -iTCP:4747 -sTCP:LISTEN` will name the culprit.
