---
applyTo: "**"
description: "Security review rubric for Procurement Spend Analysis code that exposes an API, web frontend, database, authentication flow, or public endpoint."
---

# Security Standard

Apply only the items relevant to the artifact under review. Mark non-applicable items as N/A rather than PASS.

## Verdict Rules

- Any CRITICAL item triggered: risk CRITICAL, verdict FAIL regardless of score.
- Any HIGH item triggered: risk HIGH, verdict FAIL if more than one triggered.
- Score starts at 10. Deduct: CRITICAL -3, HIGH -2, MEDIUM -1, LOW -0.5.

## API and Backend

### Rate Limiting (HIGH)

- Public or submit-key endpoints must enforce per-IP request limits.

### Input Sanitisation (CRITICAL)

- Validate, sanitise, or parameterise all user input before using it in queries, shell commands, file paths, or rendered output.
- Use parameterised queries only.

### Admin Route Protection (CRITICAL)

- Privileged routes must verify role or tier, not authentication alone.

### Webhook Signature Verification (HIGH)

- Webhook endpoints must verify provider signatures before trusting payloads.

### CORS Policy (MEDIUM)

- Wildcard CORS is only acceptable when all endpoints are key-protected and no cookie-based auth exists.

### Health Endpoint Information Leakage (LOW)

- Health endpoints must return only `{"status": "ok"}`.

### Error Response Leakage (MEDIUM)

- Do not return stack traces, internal identifiers, or raw exception details to clients.

## Authentication and Sessions

### Token Storage (CRITICAL)

- Tokens must never be stored in `localStorage` or `sessionStorage`.

### Session Expiry (HIGH)

- Sessions and tokens must have finite lifetimes.

### Password Reset Link Expiry (HIGH)

- Reset tokens must expire within 15 to 60 minutes.

### Hardcoded Credentials (CRITICAL)

- API keys, secrets, and passwords must never appear in source or build artifacts.

### Environment Variable Validation at Startup (MEDIUM)

- Validate required environment variables at process start and fail loudly on missing config.

## Database

### Database Indexing (MEDIUM)

- Index fields used in WHERE, ORDER BY, and JOIN clauses.

### Pagination on Queries (HIGH)

- List endpoints must paginate.

### Database Connection Pooling (MEDIUM)

- Use a connection pool sized for expected concurrency.

### Backup Strategy (HIGH)

- Production databases need automated backups and tested restore procedures.

## Frontend

### XSS and Output Encoding (CRITICAL)

- Encode user-controlled content before rendering it.

### Error Boundaries (MEDIUM)

- UI surfaces must degrade gracefully and show fallback output on failure.

### Type Safety on AI-Generated Code (MEDIUM)

- If a TypeScript client surface exists, strict typing is mandatory and AI-generated code must be reviewed for unsafe types.

## Infrastructure

### Image Upload Handling (MEDIUM)

- Uploaded files must not be served directly from the application server.
- Use object storage or equivalent external storage and validate file type and size server-side.

### Email Sent Synchronously (MEDIUM)

- Emails must be dispatched through background work, not inline in request handlers.

### Logging in Production (HIGH)

- Production environments must emit structured logs with enough context to diagnose failures.

### Health Check Endpoint (LOW)

- Services must expose a health endpoint for monitoring and return only `{"status": "ok"}` to unauthenticated callers.
