# AGENTS.md — Procurement Spend SaaS

Operational guide for AI agents and automated systems working on this repository.

## Repository Layout

```text
src/
  procurement_spend_analysis/   Python analytics package
tests/                           pytest test suite
docs/                            Project documentation
app.py                           Streamlit dashboard entry point
Dockerfile                       Production container
```

## Mandatory Workflow

### Before any code change

1. Read the relevant instruction file from `.github/instructions/`
2. Identify the verification gate for the layer being changed
3. Plan using the `plan-execute-verify` skill

### After any code change

1. Run the verification gate for the changed layer (see below)
2. Run `get_errors` on all modified files
3. Fix all errors before reporting done

## Verification Gates

### Python Analytics Package

```bash
ruff check src/ tests/
ruff format --check src/ tests/
pytest tests/ -q --cov=src/procurement_spend_analysis
```

### Pipeline Smoke Test

```bash
python generate_data.py
python create_db.py
python analyze_procurement.py
```

## Security Rules (blocking)

- No `os.environ.get("VAR", "fallback")` for secrets — raise `RuntimeError`
- No database credentials hardcoded
- No API keys in source code
- All sensitive config via environment variables

## CI / Standards Governance

The `standards-governance` job in `.github/workflows/python-app.yml` enforces:

- All 12 standards baseline files present
- Markdown lint on all standards artifacts
- Security pattern scan (hardcoded fallback secrets, raw exception exposure, CORS wildcards)

## Skills Available

| Skill | Path |
|---|---|
| Plan -> Execute -> Verify | `.github/skills/plan-execute-verify/SKILL.md` |
| Standards Review | `.github/skills/standards-review/SKILL.md` |
