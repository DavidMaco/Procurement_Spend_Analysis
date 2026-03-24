---
applyTo: "**"
description: "Plan-execute-verify workflow rules for non-trivial changes in Procurement Spend Analysis."
---

# Execution Workflow Standard

## Plan First

Use plan-first flow when work includes any of:

- 3 or more meaningful steps
- architectural decisions
- cross-file or cross-module changes
- uncertain requirements

Include acceptance criteria and verification gates in the plan.

## Execute Autonomously

- Proceed without unnecessary hand-holding once requirements are clear.
- Use focused subagents for discovery and comparison work.
- Re-plan immediately when assumptions change.

## Verify Before Done

- Never mark complete without evidence.
- Run applicable checks and summarize verification outcomes.
- Compare before and after behavior when behavior changes matter.

## Scope Discipline

- Keep changes narrow.
- Do not broaden into unrelated failures unless explicitly requested.
