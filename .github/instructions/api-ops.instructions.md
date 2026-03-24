---
applyTo: "src/procurement_spend_analysis/**"
description: "Backend API standards for contracts, security, logging, and verification in Procurement Spend Analysis."
---

# API Operations Standard

## Contract Rules

- Keep response and error contracts structured and stable.
- Paginate list responses. Never expose unbounded public result sets.
- Keep auth and privilege semantics explicit.

## Observability Rules

- Include request IDs or equivalent correlation fields in logs and responses where feasible.
- Log route, status, and error classification.
- Do not log secrets or unbounded payloads.

## Safety Rules

- Validate and sanitise all user input before use in queries, file paths, or downstream processing.
- Use parameterised queries only.
- Never return stack traces, internal file paths, or raw exception text to clients.

## Security Rules

- Apply rate limiting to public and write endpoints.
- Privileged routes must enforce role checks, not authentication alone.
- Webhook endpoints must verify provider signatures before trusting payloads.
- Wildcard CORS is not acceptable with cookie or session auth.
- Health endpoints must return only `{"status": "ok"}`.
- Validate environment variables at startup.
- Use connection pooling and review indexing for queried fields.

## Verification Rules

- Run relevant backend tests before completion.
- Validate success and failure paths for changed endpoints.
- Do not close work without evidence.
