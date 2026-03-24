# Plan -> Execute -> Verify

**Skill domain:** Structured change execution for any layer of the Procurement Spend SaaS.

## When to Use

Use whenever a task involves more than a single-line edit:

- Adding or modifying API endpoints
- Changing authentication or middleware
- Streamlit dashboard feature work
- Database schema changes
- CI/CD pipeline modifications

## Protocol

### Step 1 — Plan

```text
Files to change: [list]
Tests to run: [list of commands]
Risk of regression: [low | medium | high]
Sub-tasks: [numbered list]
```

Register sub-tasks in the todo list tool; mark `in-progress` before starting each.

### Step 2 — Execute

- Change one concern at a time
- Read files before editing them
- Apply security standards throughout
- Do not add code outside the stated scope

### Step 3 — Verify

| Layer | Commands |
|---|---|
| Python | `ruff check . && pytest tests -q` |
| Streamlit | launch app and verify no import errors |

Then run `get_errors` on every modified file.

### Step 4 — Complete

Mark each todo complete immediately after it is verified.

## Discipline Constraints

- Never mark a step complete if errors remain
- One pull request = one logical concern
