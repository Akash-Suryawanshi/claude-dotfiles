# Production Coding Examples

Concrete bad-to-good transformations for each principle.

## 1. SRP: God Class -> Focused Classes

```python
# BAD: One class does validation, persistence, email, reporting
class UserManager:
    def create_user(self, email, password, name):
        # validates email...
        # saves to database...
        # sends welcome email...
        # logs creation...

# GOOD: Each class has one job, orchestrator delegates
class EmailValidator:
    @staticmethod
    def validate(email: str) -> bool:
        return bool(re.match(r"[^@]+@[^@]+\.[^@]+", email))

class UserRepository:
    def save(self, email: str, password: str, name: str) -> int: ...

class EmailService:
    def send_welcome_email(self, email: str, name: str): ...

class UserService:
    def __init__(self, repository: UserRepository,
                 email_service: EmailService):
        self.repository = repository
        self.email_service = email_service

    def create_user(self, email: str, password: str, name: str) -> int:
        if not EmailValidator.validate(email):
            raise ValueError("Invalid email")
        user_id = self.repository.save(email, password, name)
        self.email_service.send_welcome_email(email, name)
        return user_id
```

## 2. Encapsulation: Public Fields -> Controlled Access

```python
# BAD: Direct state mutation, no validation
class BankAccount:
    def __init__(self, owner, balance):
        self.balance = balance       # Anyone can set to -500
        self.transactions = []       # Anyone can corrupt

# GOOD: Private state, validation in methods, return copies
class BankAccount:
    def __init__(self, owner: str, initial_balance: float = 0):
        self._owner = owner
        self._balance = initial_balance
        self._transactions: list[Transaction] = []

    def deposit(self, amount: float) -> float:
        if amount <= 0:
            raise ValueError("Deposit amount must be positive")
        self._balance += amount
        return self._balance

    def withdraw(self, amount: float) -> float:
        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive")
        if amount > self._balance:
            raise ValueError("Insufficient funds")
        self._balance -= amount
        return self._balance

    def get_balance(self) -> float:
        return self._balance

    def get_statement(self) -> list[str]:
        return [str(t) for t in self._transactions]  # Copy, not original
```

## 3. Loose Coupling: Hard-coded -> Injected Dependencies

```python
# BAD: OrderProcessor creates its own EmailSender — can't swap or test
class OrderProcessor:
    def __init__(self):
        self.email_sender = EmailSender()  # Tight coupling

# GOOD: Depend on abstract interface, inject concrete implementation
from abc import ABC, abstractmethod

class Notifier(ABC):
    @abstractmethod
    def send(self, recipient: str, subject: str, message: str): ...

class EmailNotifier(Notifier):
    def send(self, recipient, subject, message):
        print(f"[EMAIL] {recipient}: {subject}")

class SMSNotifier(Notifier):
    def send(self, recipient, subject, message):
        print(f"[SMS] {recipient}: {message}")

class OrderProcessor:
    def __init__(self, notifier: Notifier):  # Injected
        self.notifier = notifier

    def process_order(self, order_id: int, contact: str):
        # ... business logic ...
        self.notifier.send(contact, f"Order {order_id}", "Confirmed")
```

## 4. Extensibility: if/else Chain -> Strategy Pattern

```python
# BAD: Must edit generate_report() to add every new format
class ReportGenerator:
    def generate_report(self, data, format_type):
        if format_type == "text": ...
        elif format_type == "csv": ...
        elif format_type == "html": ...
        # Want JSON? Edit this method. Want Markdown? Edit again.

# GOOD: New format = new class, existing code untouched
class ReportFormatter(ABC):
    @abstractmethod
    def format(self, data: list[dict]) -> str: ...

class CSVFormatter(ReportFormatter):
    def format(self, data):
        headers = data[0].keys()
        return ",".join(headers) + "\n" + "\n".join(
            ",".join(str(item[h]) for h in headers) for item in data
        )

class JSONFormatter(ReportFormatter):  # Added without touching existing code
    def format(self, data):
        import json
        return json.dumps(data, indent=2)

class ReportGenerator:
    def __init__(self, formatter: ReportFormatter):
        self.formatter = formatter

    def generate(self, data: list[dict]) -> str:
        return self.formatter.format(data)
```

## 5. Portability: Hard-coded Paths -> Config-driven

```python
# BAD: Windows-only, hard-coded user, string path concatenation
class DataProcessor:
    def __init__(self):
        self.input_dir = "C:\\Users\\John\\Documents\\data"
        self.db_host = "localhost"

    def process_file(self, filename):
        path = self.input_dir + "\\" + filename  # Platform-specific

# GOOD: pathlib, env vars, works everywhere
from pathlib import Path
import os

class Config:
    def __init__(self):
        self.input_dir = Path(os.getenv("INPUT_DIR", "./data"))
        self.output_dir = Path(os.getenv("OUTPUT_DIR", "./output"))
        self.db_host = os.getenv("DB_HOST", "localhost")

class DataProcessor:
    def __init__(self, config: Config | None = None):
        self.config = config or Config()

    def process_file(self, filename: str) -> Path:
        input_path = self.config.input_dir / filename  # Cross-platform
        output_path = self.config.output_dir / (Path(filename).stem + ".csv")
        return output_path
```

## 6. Defensibility: Silent Failures -> Fail-fast

```python
# BAD: No validation, stores CVV, debug ON, swallows exceptions
class PaymentProcessor:
    def __init__(self):
        self.debug_mode = True    # Unsafe default
        self.timeout = None       # Hangs forever

    def process_payment(self, amount, account_number, cvv=None):
        if self.debug_mode:
            print(f"DEBUG: CVV: {cvv}")  # Leaks secrets
        try:
            result = self._charge(amount, account_number)
        except Exception:
            return None  # Silent failure

# GOOD: Validate immediately, safe defaults, never log secrets
class PaymentProcessor:
    def __init__(self, debug_mode: bool = False, timeout: int = 30):
        self.debug_mode = debug_mode
        self.timeout = timeout

    def process_payment(self, amount, account_number: str, cvv: str) -> PaymentResult:
        validated_amount = PaymentValidator.validate_amount(amount)  # Fails fast
        validated_account = PaymentValidator.validate_account(account_number)

        if self.debug_mode:
            print(f"DEBUG: Processing from ****-****-****-{validated_account[-4:]}")
            # CVV never logged

        try:
            self._charge(validated_amount, validated_account, cvv)
        except Exception as e:
            raise PaymentError(f"Payment failed: {e}") from e  # Propagate, don't swallow

        return PaymentResult(
            amount=validated_amount,
            masked_account=f"****-****-****-{validated_account[-4:]}",
            status="SUCCESS"
        )
```

## 7. Testability: Side Effects Mixed In -> Pure Functions

```python
# BAD: Calculation, printing, and file I/O all mixed
def calculate_and_report(expr):
    # parsing + math + side effects in one blob
    result = eval(expr)
    print(f"Result: {result}")
    with open("log.txt", "a") as f:
        f.write(f"{expr} = {result}\n")
    return result

# GOOD: Pure calculation separated from I/O
class Operations:
    @staticmethod
    def add(a: float, b: float) -> float:  # Pure: testable without mocks
        return a + b

    @staticmethod
    def divide(a: float, b: float) -> float:
        if b == 0:
            raise ValueError("Division by zero")
        return a / b

class Calculator:
    def calculate(self, expr: str) -> float:
        a, op, b = OperationParser.parse(expr)  # Parse separately
        return Operations.get_operation(op)(a, b)  # Pure computation
```

## 8. Simplicity: Over-engineered -> Direct

```python
# BAD: Factory + enum + ABC + 3 classes for string case conversion
class StringCase(Enum):
    UPPER = "upper"
    LOWER = "lower"

class StringTransformerInterface(ABC):
    @abstractmethod
    def transform(self, text: str) -> str: ...

class UpperCaseTransformer(StringTransformerInterface):
    def transform(self, text): return text.upper()

class TransformerFactory:
    @staticmethod
    def create(case_type: StringCase): ...

# GOOD: Simple function
def change_case(text: str, case_type: str) -> str:
    cases = {"upper": str.upper, "lower": str.lower, "title": str.title}
    if case_type not in cases:
        raise ValueError(f"Unknown case type: {case_type}")
    return cases[case_type](text)

# BAD: Three nearly identical methods (DRY violation)
def greet_morning(name): return f"Hello, {name}! Good morning!"
def greet_afternoon(name): return f"Hello, {name}! Good afternoon!"
def greet_evening(name): return f"Hello, {name}! Good evening!"

# GOOD: One parameterized function
def greet(name: str, time_of_day: str = "day") -> str:
    if not name:
        name = "Guest"
    if len(name) > 20:
        name = name[:20] + "..."
    return f"Hello, {name}! Good {time_of_day}!"
```
