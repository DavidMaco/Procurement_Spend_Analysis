# Procurement Spend SaaS — Copilot Instructions

Python procurement spend analytics pipeline with Streamlit dashboard.
AWS ECS production deployment via Docker. Python 3.13, src-layout package.

## Verification Gates

### Python Package

```bash
ruff check src/ tests/
ruff format --check src/ tests/
pytest tests/ -q --cov=src/procurement_spend_analysis --cov-fail-under=80
```

### Pipeline Smoke Test

```bash
python generate_data.py && python create_db.py && python analyze_procurement.py
```

## Security Standards (non-negotiable)

- **Never** add `os.environ.get("VAR", "fallback-secret")` — raise `RuntimeError` if missing
- **Never** expose `str(exc)` in HTTP response bodies
- No secrets in source code; environment variables only
- No hardcoded database credentials

## Code Standards

### Python

- `from __future__ import annotations` on every module
- Pydantic models or dataclasses for structured config
- Logger via `logging.getLogger(__name__)`; no f-string interpolation in log calls
- DataFrames must handle empty frames gracefully

### Streamlit

- `@st.cache_data` for all data-loading functions
- `st.set_page_config()` in main entry point only
- No secrets in source; use `st.secrets` or env vars

## Instruction Files

| Scope | File |
|---|---|
| Python Application | `.github/instructions/api-ops.instructions.md` |
| Streamlit | `.github/instructions/frontend-quality.instructions.md` |
| Security | `.github/instructions/security.instructions.md` |
| Documentation | `.github/instructions/documentation.instructions.md` |
| Workflow | `.github/instructions/execution-workflow.instructions.md` |
