---
applyTo: "**"
---

# Execution Workflow — Procurement Spend SaaS

The required work pattern for every task in this repository.

## Phase 1 — Understand

1. Read the relevant instruction file for the layer being changed
2. Read the files you will modify — understand context before making changes
3. Identify the correct verification gate

## Phase 2 — Plan

Write a step-by-step plan before touching any code:

- What files change?
- What tests cover those files?
- What could break?

For multi-step tasks, use the todo list tool to track progress.

## Phase 3 — Implement

- Make the smallest change that satisfies the requirement
- Do not refactor, add docstrings, or improve unrelated code
- Apply security standards from `security.instructions.md` throughout
- Never use placeholder secrets or hardcoded credentials

## Phase 4 — Verify

| Layer | Gate |
|---|---|
| `src/` | `ruff check src/ tests/ && pytest tests/ -q` |
| Streamlit | `ruff check app.py` |
| Pipeline | `python generate_data.py && python analyze_procurement.py` |

## Phase 5 — Validate

- Run `get_errors` on every modified file
- Fix all errors; do not mark a task complete with open errors

## Discipline Rules

- One concern per commit
- Do not add features not in the task scope
- Do not skip any phase to save time
