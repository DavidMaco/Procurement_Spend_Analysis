---
applyTo: "{dashboard_ui.py,streamlit_app.py,pages/**}"
description: "Streamlit interface standards for quality, accessibility, and resilient analytical storytelling in Procurement Spend Analysis."
---

# Frontend Quality Standard

## Design Direction

- Start from a clear analytical narrative for each page.
- Keep one dominant purpose per section.
- Avoid interchangeable, generic dashboard layouts.

## UX and Accessibility

- Keep labels, controls, and chart context easy to understand.
- Ensure readable hierarchy and acceptable contrast.
- Avoid horizontal overflow in common desktop and laptop viewports.

## Resilience and Safety

- Every page and data-dependent section must fail gracefully.
- Do not let one unhandled exception blank the entire experience.
- Validate upload inputs for type and size before processing.
- Encode user-controlled content before rendering it.

## Code Quality

- Keep Streamlit logic maintainable and scoped.
- Reuse existing page and utility patterns where practical.
- If any TypeScript or AI-generated client code is introduced, strict typing is mandatory.

## Verification

- Verify changed pages render correctly.
- Validate affected filters, uploads, and key chart states.
- Confirm graceful fallback behavior on recoverable errors.
