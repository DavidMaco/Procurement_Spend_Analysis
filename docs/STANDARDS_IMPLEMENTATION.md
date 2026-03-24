# Procurement Spend SaaS Standards Implementation

## Scope

This document defines implemented standards for this repository and how they are enforced.

## Implemented Standards

### 1. Execution Workflow Standard

Implemented via:

- `.github/copilot-instructions.md`
- `.github/instructions/execution-workflow.instructions.md`
- `.github/skills/plan-execute-verify/SKILL.md`

Key rules:

- Plan-first for non-trivial tasks
- Mandatory verification evidence before completion
- Immediate re-plan when assumptions fail

### 2. Python Application Standard

Implemented via:

- `.github/instructions/api-ops.instructions.md`
- `AGENTS.md`

Key rules:

- Parameterized queries for all database interactions
- Empty DataFrame handling in all data processing functions
- Typed return structures from public functions

### 3. Frontend Quality Standard

Implemented via:

- `.github/instructions/frontend-quality.instructions.md`
- `.github/copilot-instructions.md`

Key rules:

- `@st.cache_data` for all data loading
- User-friendly error messages only
- No secrets in Streamlit source files

### 4. Security Review Standard

Implemented via:

- `.github/instructions/security.instructions.md`
- `.github/skills/standards-review/SKILL.md`

Key rules:

- No hardcoded fallback secrets
- No raw exception exposure
- No CORS wildcards
- CI-enforced pattern scan

### 5. Documentation and Commit Standard

Implemented via:

- `.github/instructions/documentation.instructions.md`

Key rules:

- No generic boilerplate in docstrings
- Conventional commits, one logical change per commit
- README follows quickstart + env var table pattern
