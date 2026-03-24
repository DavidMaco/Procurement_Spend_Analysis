# Procurement Spend Analysis Copilot Instructions

These are repository-level engineering standards for this repository.

## Execution Model

- Use plan-first execution for non-trivial work, especially cross-file changes, architectural choices, or requests with 3 or more implementation steps.
- Re-plan when assumptions break.
- Use focused subagents for read-only discovery and comparison work.

## Verification Requirements

Never mark work complete without evidence.

- Run lint and format checks on changed Python surfaces.
- Run relevant pytest suites for changed behavior.
- For data-model or pipeline changes, run the pipeline smoke path.
- For API changes, verify both success and failure behavior.
- For Streamlit changes, verify changed pages and upload flows behave correctly.

## Scope and Change Hygiene

- Keep changes minimal and targeted.
- Fix root causes, not symptoms.
- Do not broaden to unrelated failures without explicit request.

## Standards Priority

1. Repository contracts and architecture docs in `docs/`
2. Instructions in `.github/instructions/`
3. Skills in `.github/skills/`
4. Existing local module conventions

## API and Security Defaults

- Keep response and error shapes stable.
- Include request correlation IDs in logs and responses where feasible.
- Redact sensitive fields in logs and diagnostics.
- Apply rate limiting to public and write endpoints.
- Use parameterised queries and validated input only.
- Auth tokens in browser contexts belong in `httpOnly` cookies, never `localStorage`.
- Verify webhook signatures before trusting event payloads.
- Admin routes must enforce role checks.
- Validate required environment variables at startup and fail loudly when missing.
- Apply the security rubric in `.github/instructions/security.instructions.md` for API, auth, database, upload, or public endpoint changes.

## Frontend Quality Defaults

- Keep a clear analytical narrative per page.
- Avoid generic dashboard output.
- Preserve accessibility, readable hierarchy, and fallback behavior.
- Add graceful error handling for page and section failures.
- If any TypeScript or AI-generated client code is introduced, strict typing is mandatory.

## Documentation and Commit Defaults

- Write in natural language. No em dashes. No generic boilerplate.
- README files follow the PVIS structured narrative pattern.
- Commit messages use `type(scope): summary` and each commit should contain one logical change.
