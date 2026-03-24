---
name: standards-review
description: Use when reviewing proposed or completed changes for compliance with repository standards, quality gates, API contracts, security rules, UI quality rules, and documentation requirements. Trigger for audits, pre-merge checks, and post-change compliance validation.
---

# Standards Review

## Objective

Evaluate changes against repository standards and produce actionable findings.

## Review Dimensions

1. Execution workflow compliance
2. Verification evidence quality
3. API contract and operations standards
4. Security checklist, applying only items relevant to the artifact under review
5. Frontend quality and usability standards
6. Documentation and commit message standards
7. Scope control and maintainability

## Output Format

### Standards Review Report

- Status: pass or fail
- Security verdict: CRITICAL / HIGH / MEDIUM / LOW / N/A
- Findings by severity: critical, high, medium, low
- Evidence references: file paths and behavioral proof notes
- Required fixes
- Advisory improvements

## Rules

- Findings must be concrete and testable.
- Any CRITICAL security item is an automatic FAIL regardless of other scores.
- Do not approve work missing mandatory verification evidence.
- Prefer behavior and contract correctness over style-only comments.
- Mark security items as N/A when they do not apply to the artifact's actual technology stack or exposure surface.
