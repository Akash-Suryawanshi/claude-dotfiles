# Clean Code Rules — Full Reference (Robert C. Martin, Chapter 17, Python-adapted)

## Comments (C1-C5)
- **C1:** No metadata in comments — use Git for author, date, changelog
- **C2:** Delete obsolete comments immediately — stale comments mislead
- **C3:** No redundant comments — don't restate what the code says
- **C4:** Write comments well if you must — proper grammar, concise
- **C5:** Never commit commented-out code — Git has history

## Environment (E1-E2)
- **E1:** One command to build: `pip install -e ".[dev]"`
- **E2:** One command to test: `pytest`

## Functions (F1-F4)
- **F1:** Maximum 3 arguments. Group more into a `@dataclass`
- **F2:** No output arguments — return values instead
- **F3:** No boolean flag arguments — split into two named functions
- **F4:** Delete dead functions immediately

## General (G1-G36)
- **G1:** One language per file
- **G2:** Implement the obvious expected behavior
- **G3:** Handle all boundary conditions
- **G4:** Don't override safeties (linters, type checks)
- **G5:** DRY — no duplication of any kind
- **G6:** Code at consistent abstraction levels within a function
- **G7:** Base classes must not know about their children
- **G8:** Minimize the public interface
- **G9:** Delete dead code — if it's not called, remove it
- **G10:** Declare variables close to their usage
- **G11:** Be consistent — same pattern for same situation
- **G12:** Remove clutter — unused variables, empty constructors
- **G13:** No artificial coupling — don't group unrelated things
- **G14:** No feature envy — methods should use their own class's data
- **G15:** No selector arguments (use polymorphism instead)
- **G16:** No obscured intent — don't write clever one-liners
- **G17:** Place code where a reader would expect to find it
- **G18:** Prefer instance methods over static when state is involved
- **G19:** Use explanatory variables for complex sub-expressions
- **G20:** Function names must say exactly what the function does
- **G21:** Understand the algorithm before you claim it works
- **G22:** Make logical dependencies physical (import/call, don't assume)
- **G23:** Prefer polymorphism to if/else or switch chains
- **G24:** Follow PEP 8 conventions
- **G25:** Named constants, not magic numbers or strings
- **G26:** Be precise — don't return `list` when you mean the first match
- **G27:** Structure over convention (enforce with code, not comments)
- **G28:** Encapsulate conditionals into named functions
- **G29:** Avoid negative conditionals (`if is_valid` not `if not is_invalid`)
- **G30:** Functions do one thing
- **G31:** Make temporal coupling explicit (return values that feed next step)
- **G32:** Don't be arbitrary — have a reason for every structural choice
- **G33:** Encapsulate boundary conditions (`end = start + length` once, not repeated)
- **G34:** One abstraction level per function
- **G35:** Keep configurable data (URLs, limits, timeouts) at high levels
- **G36:** Law of Demeter — only call methods on: self, parameters, objects you created, direct attributes

## Python-Specific (P1-P3)
- **P1:** No wildcard imports (`from x import *`) — always explicit per PEP 8
- **P2:** Use `Enum` classes, not magic string/int constants
- **P3:** Type hints on all public interfaces

## Names (N1-N7)
- **N1:** Choose descriptive, unambiguous names
- **N2:** Names at the right abstraction level
- **N3:** Use standard nomenclature (`is_`, `has_`, `can_` for booleans)
- **N4:** Unambiguous — `elapsed_time_in_days` not `d`
- **N5:** Name length proportional to scope (loop `i` fine, module `user_count`)
- **N6:** No encodings or prefixes (no Hungarian notation)
- **N7:** Names describe side effects (`create_or_return_user` not `get_user` if it creates)

## Tests (T1-T9)
- **T1:** Test everything that could break
- **T2:** Use coverage tools
- **T3:** Don't skip trivial tests — they document behavior
- **T4:** An ignored/skipped test is a question about ambiguity
- **T5:** Test boundary conditions exhaustively
- **T6:** Exhaustively test near known bugs
- **T7:** Look for patterns in test failures
- **T8:** Coverage patterns can point you to bugs
- **T9:** Tests must be fast (target < 100ms each)

## Quick Anti-Patterns Table

| Don't | Do | Rule |
|-------|-----|------|
| Comment every line | Delete obvious comments | C3 |
| `from x import *` | Explicit imports | P1 |
| Magic number `86400` | `SECONDS_PER_DAY = 86400` | G25 |
| `process(data, True)` | `process_verbose(data)` | F3 |
| `obj.a.b.c.value` | `obj.get_value()` | G36 |
| 100+ line function | Split by responsibility | G30 |
| Deep nesting | Guard clauses, early returns | G28/G29 |
| Commented-out code | Delete it | C5 |
| Dead functions | Delete them | F4/G9 |
| `if not is_invalid` | `if is_valid` | G29 |
| Helper for one-liner | Inline the code | KISS |
| 5+ function arguments | Group into `@dataclass` | F1 |
