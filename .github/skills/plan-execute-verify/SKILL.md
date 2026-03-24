# Plan -> Execute -> Verify

**Skill domain:** Structured change execution for any layer of this repository.

## When to Use

Use this skill whenever a task involves more than a single-line edit:

- Adding or modifying pipeline stages or data transformations
- Changing database schema or output formats
- Frontend Streamlit feature work
- CI/CD pipeline modifications

## Protocol

### Step 1 — Plan

Write an explicit plan before editing any file:

```
Files to change: [list]
Tests to run: [list of commands]
Risk of regression: [low | medium | high]
Sub-tasks: [numbered list]
```

Register sub-tasks in the todo list tool; mark `in-progress` before starting each.

### Step 2 — Execute

- Change one concern at a time
- Read files before editing them
- Apply security standards (`security.instructions.md`) throughout
- Do not add code outside the stated scope

### Step 3 — Verify

Run all gates relevant to changed layers:

| Layer | Commands |
|---|---|
| `src/` | `ruff check src/ tests/ && pytest tests/ -q` |
| Streamlit | `ruff check app.py` |
| Pipeline | `python generate_data.py && python analyze_procurement.py` |

Then run `get_errors` on every modified file.

### Step 4 — Complete

Mark each todo complete immediately after it is verified. Do not batch completions.
Report only when the entire task is clean.

## Discipline Constraints

- Never mark a step complete if errors remain
- Never skip verification to save time
- One pull request = one logical concern
