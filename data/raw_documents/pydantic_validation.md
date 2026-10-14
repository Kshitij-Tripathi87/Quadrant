# Pydantic v2: Data Validation and Settings Management

Pydantic is the most widely used data validation library for Python. Rewritten in Rust for version 2, Pydantic delivers up to 20x performance improvements while enforcing strict type safety.

## 1. Defining Models with `BaseModel`
Models are classes inheriting from `pydantic.BaseModel`. Attributes are typed using standard Python type annotations:

```python
from datetime import datetime
from pydantic import BaseModel, Field

class User(BaseModel):
    id: int
    name: str = Field(..., min_length=2, max_length=50)
    email: str
    is_active: bool = True
    signup_ts: datetime | None = None
```

When instantiating `User`, Pydantic parses and coerces types where unambiguous (e.g. string integers `"123"` to `123`) and raises a `ValidationError` with structured JSON errors if validation fails.

## 2. Field Customization with `Field()`
The `Field` function provides metadata and validation rules:
- `default`: Default value if field is omitted.
- `default_factory`: Callable returning default values (e.g. `list`, `datetime.utcnow`).
- Numeric constraints: `gt`, `ge`, `lt`, `le`, `multiple_of`.
- String constraints: `min_length`, `max_length`, `pattern` (regex).
- OpenAPI metadata: `description`, `title`, `examples`.

## 3. Custom Validators in Pydantic v2
Pydantic v2 introduces `@field_validator` and `@model_validator`:

```python
from pydantic import BaseModel, field_validator, model_validator

class Payment(BaseModel):
    amount: float
    currency: str
    card_number: str

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        allowed = {"USD", "EUR", "GBP", "INR"}
        v_upper = v.upper()
        if v_upper not in allowed:
            raise ValueError(f"Currency must be one of {allowed}")
        return v_upper

    @model_validator(mode="after")
    def check_min_amount(self) -> "Payment":
        if self.currency == "USD" and self.amount < 1.0:
            raise ValueError("USD transactions must be at least $1.00")
        return self
```

## 4. Settings Management with `pydantic-settings`
Configuration settings loaded from environment variables or `.env` files are defined via `BaseSettings`:

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class AppSettings(BaseSettings):
    app_name: str = "My RAG System"
    port: int = 8000
    debug: bool = False
    openai_api_key: str

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = AppSettings()
```
Environment variables automatically populate the configuration with type validation.
