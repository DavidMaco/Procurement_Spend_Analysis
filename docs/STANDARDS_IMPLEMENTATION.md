# Standards Implementation

## Repository

- `Procurement_Spend_Analysis`

## Implemented Standards Files

- `.github/copilot-instructions.md`
- `.github/instructions/api-ops.instructions.md`
- `.github/instructions/frontend-quality.instructions.md`
- `.github/instructions/execution-workflow.instructions.md`
- `.github/instructions/security.instructions.md`
- `.github/instructions/documentation.instructions.md`
- `AGENTS.md`

## Standards Profile

1. Execution: plan-first for non-trivial engineering changes
2. Verification: mandatory evidence and relevant gate checks before completion
3. API operations: stable contracts, structured errors, correlation context, redaction, pagination
4. Security review: checklist-based review for API, auth, database, upload, and public endpoint changes
5. UI quality: purposeful analytical storytelling and resilient Streamlit interaction design
6. Documentation and commits: PVIS-style README structure, natural language only, no em dashes, one logical change per commit
7. Scope control: minimal-impact, root-cause-first implementation discipline

## Required Verification Gates

- `ruff check src/ tests/`
- `ruff format --check src/ tests/`
- `pytest tests/ -q`

Additional checks by changed surface:

- pipeline or analytics changes: run the data pipeline smoke path and verify generated artifacts
- API behavior changes: validate success and failure paths
- Streamlit changes: validate affected pages, upload flows, and fallback behavior

## Enforcement Order

1. Repository architecture and contract documentation
2. `.github/instructions/*.instructions.md`
3. `.github/skills/**/SKILL.md`
4. Existing local module conventions
