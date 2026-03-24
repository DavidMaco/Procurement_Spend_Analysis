# Operational Build Guide

This file is operational-only. Keep status and progress in planning artifacts, not here.

## Build and Run

### Environment

- Create virtual environment: `python -m venv .venv`
- Activate (Windows): `.venv\\Scripts\\activate`
- Install dependencies: `pip install -e ".[dev]"`

### Core Workflows

- Run data pipeline: `python generate_data.py && python create_db.py && python analyze_procurement.py`
- Run API: `uvicorn procurement_spend_analysis.api.app:app --reload`
- Run Streamlit app: `streamlit run streamlit_app.py`

## Validation Gates

Run applicable gates before completion:

- Lint: `ruff check src/ tests/`
- Format check: `ruff format --check src/ tests/`
- Tests: `pytest tests/ -q`

Additional gates by changed surface:

- Pipeline or analytics changes: run the pipeline smoke path and verify generated artifacts.
- API changes: validate success and failure behavior for changed routes.
- Streamlit changes: verify the affected page, filters, and upload flows.

## Logging and Security

- Include correlation context in API logs where feasible.
- Redact tokens, secrets, credentials, and session identifiers.
- Do not log raw sensitive payload content.
- Use the repository security rubric for API, auth, database, upload, and public endpoint changes.

## Codebase Patterns

- Keep analytical logic in existing domain modules.
- Preserve the current flow: data generation, storage, analytics, reporting, API, presentation.
- Prefer extending existing modules over introducing parallel duplicates.
