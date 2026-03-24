---
applyTo: "src/**"
---

# Python Application Standards — Procurement Spend SaaS

Standards for the Python analytics package (`src/procurement_spend_analysis/`).

## Module Conventions

- `from __future__ import annotations` at the top of every module
- Pydantic models or dataclasses for all structured config and output types
- All config via settings object; no bare `os.environ` in business logic
- Structured logging: `logger = logging.getLogger(__name__)`; no f-string log messages

## Data Processing Standards

- Validate input DataFrames before processing (check shape, required columns)
- Handle empty DataFrames explicitly — no silent failures on empty input
- Use parameterized queries for all database interactions (no f-string SQL)
- Return typed structures, not raw dicts, from public functions

## Error Handling

```python
# CORRECT
try:
    result = process_data(df)
except Exception as exc:
    logger.warning("Processing failed", extra={"error": str(exc)})
    raise RuntimeError("Data processing failed. Check input data.") from exc
```

## Secret Management

```python
# CORRECT
db_url = os.environ.get("DATABASE_URL")
if not db_url:
    raise RuntimeError("DATABASE_URL must be set")

# WRONG
db_url = os.environ.get("DATABASE_URL", "sqlite:///procurement.db")  # FORBIDDEN
```

## Test Requirements

- Every data transformation has at least one test with data and one with an empty input
- Run: `pytest tests/ -q --cov=src/procurement_spend_analysis`
