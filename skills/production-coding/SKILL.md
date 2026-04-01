---
name: production-coding
description: Use when writing, reviewing, or refactoring Python code to enforce production-quality design and clean code practices. Triggers on code smells like god classes, public mutable state, tight coupling, hard-coded paths, silent failures, copy-pasted logic, over-engineered abstractions, bad naming, excessive comments, long functions, magic numbers, deep nesting, or Law of Demeter violations. Also use when the user asks for "production-ready", "clean code", "refactor", or "code quality" improvements.
---

# Production Python Coding

Write Python code that is cohesive, encapsulated, loosely coupled, extensible, portable, defensive, maintainable, and simple — following both design principles and Robert C. Martin's Clean Code rules.

## Quick Decision Tree

```
Is my class doing more than one thing?
 Yes -> Split it (SRP/G30)

Can clients modify internal state directly?
 Yes -> Make it private, expose methods (Encapsulation/G8)

Am I creating dependencies inside my class?
 Yes -> Inject them via constructor (Loose Coupling)

Do I need to edit existing code to add features?
 Yes -> Use strategy/plugin pattern (Extensibility/G23)

Do I have hard-coded paths or platform assumptions?
 Yes -> Use pathlib and env vars (Portability/G35)

Am I accepting input without validation?
 Yes -> Validate and fail-fast (Defensibility/G3)

Would this be hard to test?
 Yes -> Separate logic from I/O, use pure functions (Testability)

Am I adding abstractions "just in case"?
 Yes -> Remove them (YAGNI/KISS)

Am I repeating this logic elsewhere?
 Yes -> Extract it (DRY/G5)

Does my function have more than 3 parameters?
 Yes -> Group into a dataclass (F1)

Am I chaining dots? (obj.a.b.c.value)
 Yes -> Wrap in a method (Law of Demeter/G36)

Are there magic numbers or strings?
 Yes -> Extract to named constants (G25)
```

## Code Smells -> Solutions

| Smell | Rule | Fix |
|-------|------|-----|
| God class doing everything | SRP/G30 | Split into focused classes |
| Public fields everywhere | Encapsulation/G8 | Private fields + methods |
| Hard-coded dependencies | Loose Coupling | Dependency injection |
| Giant if/else for types | G23 | Strategy pattern / polymorphism |
| Hard-coded paths | Portability/G35 | Config + pathlib |
| Silent failures (bare except) | Defensibility | Fail-fast with exceptions |
| 100+ line function | G30/G34 | Break into smaller functions |
| Copy-pasted code | DRY/G5 | Extract to function |
| Unused "future" code | YAGNI/G9 | Delete it |
| Factory for a one-liner | KISS | Simple function |
| Magic numbers (`86400`) | G25 | `SECONDS_PER_DAY = 86400` |
| `obj.a.b.c.value` | G36 | `obj.get_value()` |
| `process(data, True)` | F3 | `process_verbose(data)` |
| Deep nesting (3+ levels) | G28/G29 | Guard clauses, early returns |
| Commented-out code | C5 | Delete it (Git has history) |
| `from x import *` | P1 | Explicit imports |

---

## Part 1: Design Principles

### 1. Cohesion & SRP
One class, one reason to change. Split validation, persistence, notification, and reporting into separate classes. Orchestrator classes delegate, not implement.

**Test:** "Can I describe this class in one sentence without 'and'?"

### 2. Encapsulation & Abstraction
Private attributes (`self._field`), controlled access via methods. Return copies of internal collections. Validate in setters/methods, not in callers.

**Test:** "If I change the internal representation, will client code break?"

### 3. Loose Coupling & Modularity
Depend on `ABC` abstractions, not concrete classes. Inject dependencies via `__init__`. Components should be swappable and testable with mocks.

**Test:** "Can I test this without instantiating half the system?"

### 4. Reusability & Extensibility (Open/Closed)
Use strategy pattern and ABC for variation. New behavior = new class implementing the interface, not editing existing if/else chains. Prefer composition over inheritance.

**Test:** "Can I add new functionality without editing existing code?"

### 5. Portability
`pathlib.Path` for all paths (never string concatenation). `os.getenv()` with sensible defaults for config. No platform-specific assumptions.

**Test:** "Will this work on Linux, Windows, and Mac?"

### 6. Defensibility
- **Fail-fast:** Validate input immediately, raise specific exceptions
- **Safe defaults:** `debug_mode=False`, `timeout=30`, never `None` for timeouts
- **Least privilege:** Mask sensitive data (`****-****-****-1234`), never store/log secrets
- **No silent failures:** Never swallow exceptions with bare `except: pass`

**Test:** "What's the worst that could happen with bad input?"

### 7. Maintainability & Testability
Pure functions where possible (same input = same output, no side effects). Separate business logic from I/O. Use `@dataclass` for data structures. Dependency injection enables test isolation.

**Test:** "Can I write a unit test without mocking 5 things?"

### 8. Simplicity (KISS, DRY, YAGNI)
- **KISS:** If a simple function works, don't create a class hierarchy with factories
- **DRY:** Parameterize instead of duplicating (one `greet(name, time_of_day)` not three methods)
- **YAGNI:** No placeholder methods, no "future feature" stubs. Add when needed.

**Test:** "Am I making this more complex than it needs to be?"

---

## Part 2: Clean Code Rules (Robert C. Martin, adapted for Python)

### Comments (C1-C5)
- **C1:** No metadata in comments (author, date) — use Git
- **C2:** Delete obsolete comments immediately
- **C3:** No redundant comments (`x = x + 1  # increment x`)
- **C4:** If you must comment, write it well
- **C5:** Never commit commented-out code — Git has history

### Functions (F1-F4)
- **F1:** Maximum 3 arguments. More? Group into a `@dataclass`
- **F2:** No output arguments — return values instead
- **F3:** No boolean flag arguments — split into two functions (`process_verbose`, `process_quiet`)
- **F4:** Delete dead functions immediately

### Naming (N1-N7)
- **N1:** Descriptive names (`user_count` not `n`)
- **N2:** Right abstraction level (interface names shouldn't reveal implementation)
- **N3:** Use standard nomenclature (`is_`, `has_`, `can_` for booleans)
- **N4:** Unambiguous names (`elapsed_time_in_days` not `d`)
- **N5:** Name length matches scope (loop `i` is fine; module-level needs full name)
- **N7:** Names describe side effects (`create_or_return_user` not `get_user` if it creates)

### General (key rules)
- **G5:** DRY — no duplication
- **G8:** Minimize public interface
- **G9:** Delete dead code
- **G10:** Declare variables close to usage
- **G19:** Use explanatory variables for complex expressions
- **G23:** Polymorphism over if/else chains
- **G24:** Follow PEP 8 conventions
- **G25:** Named constants, not magic numbers
- **G28:** Encapsulate conditionals (`is_eligible()` not `age > 18 and status == 'active'`)
- **G29:** Avoid negative conditionals (`if is_valid` not `if not is_invalid`)
- **G30:** Functions do one thing
- **G34:** One abstraction level per function
- **G35:** Config values at high levels, not buried in logic
- **G36:** Law of Demeter — talk to friends, not strangers (`obj.get_value()` not `obj.a.b.c.value`)

### Python-Specific (P1-P3)
- **P1:** No wildcard imports (`from x import *`) — always explicit
- **P2:** Use `Enum`, not magic string/int constants
- **P3:** Type hints on all public interfaces

### Tests (T1-T9)
- **T1:** Test everything that could break
- **T5:** Test boundary conditions exhaustively
- **T6:** Test exhaustively near known bugs
- **T9:** Tests must be fast (< 100ms each)

For the full 66-rule reference, see [clean-code-rules.md](clean-code-rules.md).

---

## Python Idioms for Production Code

```python
# Paths: always pathlib
from pathlib import Path
path = Path("data") / "file.txt"          # Not "data" + "/" + "file.txt"

# Type hints: always for public interfaces
def process(data: list[str]) -> dict[str, int]: ...

# Interfaces: ABC
from abc import ABC, abstractmethod
class Notifier(ABC):
    @abstractmethod
    def send(self, message: str) -> None: ...

# Data: dataclasses or frozen dataclasses for immutability
from dataclasses import dataclass
@dataclass(frozen=True)
class PaymentResult:
    transaction_id: str
    amount: Decimal
    status: str

# Resources: context managers
with open("file.txt") as f:              # Not f = open(); ... f.close()
    data = f.read()

# Config: env vars with defaults
db_host = os.getenv("DB_HOST", "localhost")

# Validation: custom exceptions, not generic ones
class ValidationError(Exception): ...
if amount <= 0:
    raise ValidationError(f"Amount must be positive, got: {amount}")

# Money: Decimal, not float
from decimal import Decimal
price = Decimal("19.99")                 # Not 19.99

# Constants: Enum, not magic strings
from enum import Enum
class Status(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"

# Conditionals: encapsulate complex checks
def is_eligible(user) -> bool:            # Not inline: age > 18 and status == ...
    return user.age >= 18 and user.status == Status.ACTIVE

# Guard clauses: avoid deep nesting
def process(data):
    if not data:
        return None                       # Early return, not nested else
    if not data.is_valid():
        raise ValidationError("Invalid")
    return transform(data)                # Main logic at top level
```

## Applying During Code Review

When reviewing, cite rule numbers (e.g., "G5 violation: duplicated logic", "F1: too many arguments").
When fixing, report what was applied (e.g., "Fixed: extracted magic number to `SECONDS_PER_DAY` (G25)").

For bad-vs-good transformation examples, see [examples.md](examples.md).
For the full 66-rule Clean Code reference, see [clean-code-rules.md](clean-code-rules.md).
