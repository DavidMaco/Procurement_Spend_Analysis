---
name: plan-execute-verify
description: Use for non-trivial engineering tasks requiring plan-first execution, explicit verification gates, and minimal-scope delivery. Trigger when a request involves architectural choices, cross-file changes, uncertain requirements, or 3 or more implementation steps.
---

# Plan Execute Verify

## Purpose

Provide a deterministic workflow for medium and large engineering tasks:

1. Define a plan and acceptance checks
2. Implement in scoped increments
3. Verify with evidence before completion

## Protocol

### Step 1: Plan

- Write a short, checkable plan.
- Include acceptance criteria and required verification gates.
- Identify risk points and fallback strategy.

### Step 2: Execute

- Implement the smallest viable increments.
- Use focused subagents for discovery or comparison work when useful.
- Re-plan immediately if assumptions fail.

### Step 3: Verify

- Run required checks for changed surfaces.
- Validate success and failure behavior for changed flows.
- Record concise evidence.

### Step 4: Finalize

- Summarize what changed and why.
- Confirm no unresolved mandatory gate remains.

## Rules

- Do not declare completion without verification evidence.
- Prefer root-cause fixes over symptom-only patches.
- Keep blast radius minimal and explicit.
