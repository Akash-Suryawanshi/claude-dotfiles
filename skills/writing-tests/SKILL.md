---
name: writing-tests
description: Use when writing, reviewing, adding, or trimming tests in any project. Enforces a necessity-first testing philosophy — every test must declare WHY it exists (Regression / Critical contract / Acceptance criterion / Non-obvious correctness). Cuts redundant operator-coverage and happy-path-only tests. Triggers on phrases like "add a test", "write tests for", "test coverage", "improve coverage", "trim tests", "do I need this test", "test this fix", "regression test".
---

# Writing Tests — Necessity-First Philosophy

Default to writing fewer tests. Tests carry maintenance cost: re-read on every change, mock churn on refactor, false-positive failures when behavior intentionally shifts. The cheapest test is the one you didn't write.

## The Rule

Only write a test if at least one of the four categories applies — **and the test's docstring MUST name which.**

| # | Category | When it applies | Docstring opener |
|---|---|---|---|
| 1 | **Regression** | Pins a specific bug fix. Removing the test could let the bug return unnoticed. | `"REGRESSION (<bug-id> from <PR/ticket>): …"` |
| 2 | **Critical contract** | Load-bearing invariant not enforced elsewhere. Boundary tests (AST scans, type checks) are the canonical example — they catch a regression class no functional test can. | `"Critical: …"` |
| 3 | **Acceptance criterion** | A ticket explicitly lists the behavior. The test is the literal contract with the requestor. | `"AC<N> representative: …"` |
| 4 | **Non-obvious correctness** | Subtle semantic a future reader would not derive from the code alone. (Dedup, off-by-one, "off-corpus clip counts as false_positive", "$gte only on ordered enums".) | `"Non-obvious correctness: …"` |

If you cannot honestly write one of these openers for the test, **the test isn't necessary — delete it.**

## What to cut

- **Redundant operator coverage.** One happy `$eq` + one happy `$in` + one happy `$gte` + one error path is enough. Not 14 variations on the matcher.
- **Happy-path-only tests** when an adjacent error test covers the same code path. The error test exercises the success branch on its way to the failure.
- **Tests that exercise the same lines as another test** with a different fixture shape. Collapse to one.
- **Smoke "the import works"** — collection failure already catches that.
- **Per-fixture tests** when the goldens differ only in fixture data, not code path. Keep one representative; collapse the rest.

## How to trim existing tests

When reviewing an existing test file:

1. For each test, ask: "Which of the four categories does it fit?" If none — delete.
2. Group remaining tests by code path. Within each group, keep one + delete duplicates that vary only in input shape.
3. Add a docstring opener (table above) to every kept test. If the opener is forced or vague — that's a signal the test is on the cut list.

Target: cut 50%+ on first pass without losing meaningful coverage. The bug-detection power of the suite usually doesn't degrade — surviving tests carry the load that mattered.

## Bug-fix discipline

When fixing a bug:
- **Write the regression test in the same commit as the fix.** Without it, the next refactor will reintroduce the bug.
- Name the bug in the docstring: `"REGRESSION (C2 from PR #22 review): ..."`. A reviewer should be able to grep for the bug ID and find the guard.

## Boundary tests beat functional tests for invariants

When an invariant takes the form "no module in X may import Y" or "every X must satisfy Y":

```python
import pathlib, re
REPO = pathlib.Path(__file__).resolve().parents[2]

def test_no_agent_module_imports_eval():
    """Critical: invariant #2 — agent never reads ground truth, so no
    file in agent/ may import from eval/. AST scan catches the
    regression class no functional test can."""
    pat = re.compile(r"^\s*(from\s+eval\b|import\s+eval\b)", re.M)
    offenders = [str(p.relative_to(REPO))
                 for p in (REPO / "agent").rglob("*.py")
                 if pat.search(p.read_text())]
    assert not offenders, f"agent/ must not import eval/: {offenders}"
```

One test, zero behavioral mocks, eternal vigilance. This pattern is irreplaceable.

## Test docstring examples (copy this style)

```python
def test_evaluate_query_dedupes_clip_ids(gte_corpus):
    """Non-obvious correctness: multi-window agent responses for the
    same clip must collapse to one before computing MRR / `returned`.
    Without dedup, MRR would over-count when the agent returned the
    same clip in multiple window-positions."""
    ...

def test_semantic_judge_does_not_cache_unparseable_response(tmp_path):
    """REGRESSION (C2 from PR #22 review): unparseable Gemini responses
    (safety refusals, hedges) must NOT poison the cache — they were
    silently coerced to no_match + persisted, conflating real semantic
    disagreement with parser misses. Counter must increment on retry."""
    ...

def test_cli_emits_jsonl_and_markdown(tmp_path):
    """AC3 ("CLI emits per-query JSONL + aggregate Markdown"): the only
    test that exercises eval.cli end-to-end. Pins argparse wiring +
    output shape. Without this, AC3 has no automated verification."""
    ...

def test_only_eval_graph_imports_langgraph():
    """Critical: invariant #4 generalized — only eval/graph.py imports
    langgraph. AST scan; catches the regression no functional test can."""
    ...
```

## What you do NOT need to test

- Trivial getters / setters / constructors with no logic.
- Format-only output (e.g. exact Markdown punctuation) — too brittle, low signal.
- Third-party library behavior (Python stdlib, langgraph, requests) — trust the upstream tests.
- "Plumbing-only" pass-throughs that have no branching.
- Code paths that fail at import (collection catches it).

## Anti-patterns to refuse

- **"Test for coverage's sake"** — a test that exercises lines without asserting meaningful behavior. Coverage % is a lagging indicator; tests should encode requirements.
- **Tests with `assert True` or no assertions** — delete on sight.
- **Mock-heavy tests where the mocks are the entire test** — you're testing the mock framework, not your code.
- **Tests that duplicate the implementation** — e.g. asserting on the exact format string passed to a logger. Brittle; refactor-fragile.

## When user asks "should I add tests?"

Ask back, before writing any:
1. Is this a bug fix? → yes, regression test in same commit.
2. Is this a new invariant or boundary? → AST/type-scan test.
3. Does a ticket name this as AC? → write the AC test.
4. Is the behavior non-obvious from the code? → write the correctness test.
5. None of the above? → don't write a test. Document the intent in a comment or commit message instead.

## When user asks "the test suite is too big"

Sweep with the four-category lens. Expect to cut 40–60% on first pass. Each surviving test gets a category-opener docstring as you go. Reference suites I've trimmed under this rule:

- An eval-runner suite trimmed under this rule: 68 → 26 tests (–60%), all green afterward.
