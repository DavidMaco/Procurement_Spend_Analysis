---
applyTo: "**"
---

# Security Standards — Procurement Spend SaaS

Non-negotiable security requirements. Violations fail the CI `standards-governance` scan.

## Secret Management

```python
# ALWAYS — fail loudly at startup
secret = os.environ.get("MY_SECRET")
if not secret:
    raise RuntimeError("MY_SECRET environment variable must be set")

# NEVER — hardcoded fallback
secret = os.environ.get("MY_SECRET", "dev-default")  # FORBIDDEN
```

- Minimum 32-character entropy for signing secrets
- Rotate secrets via environment; never in source code
- No `.env` files committed; add to `.gitignore`

## HTTP Error Handling

```python
# CORRECT — opaque error to caller, details logged internally
except Exception as exc:
    logger.warning("Operation failed", extra={"error": str(exc)})
    raise HTTPException(status_code=400, detail="Operation failed. Check your input.") from exc

# WRONG — leaks internal implementation details
raise HTTPException(status_code=400, detail=str(exc))  # FORBIDDEN
```

## CORS

```python
# CORRECT — explicit allowlist
allow_origins=settings.allow_origins
allow_credentials=False

# WRONG
allow_origins=["*"]     # FORBIDDEN
allow_credentials=True  # FORBIDDEN
```

## Dependency Security

- Run `pip-audit -r requirements.txt` in CI; fail on HIGH/CRITICAL CVEs
- Pin direct dependencies

## CI Enforcement

The `standards-governance` job runs a security pattern scan that will **fail the build** on:

1. `os.environ.get(VAR, "secret-fallback")` patterns
2. `raise HTTPException(..., detail=str(exc))` patterns
3. `allow_origins=["*"]` patterns
