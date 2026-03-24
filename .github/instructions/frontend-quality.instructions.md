---
applyTo: "{app.py,streamlit_app.py,pages/**}"
---

# Frontend Quality — Procurement Spend SaaS

Standards for the Streamlit dashboard.

## Streamlit Standards

- One `st.set_page_config()` per app entry point only
- Use `@st.cache_data` for data-loading functions (not `@st.cache`)
- No secrets in source; use `st.secrets` or env vars
- All DataFrame operations must handle empty frames gracefully
- Page files in `pages/` must be independently runnable

## Layout and UX

- Each page must have a clear title via `st.title()` or `st.header()`
- Loading states must use `st.spinner()` for operations over 1 second
- Error messages must be user-friendly, not raw stack traces

## Security

- No API keys or secrets in source code
- No hardcoded URLs to production systems
- Never commit `.env` files

## Shared Rules

- No hardcoded URLs — use constants or config
- No commented-out code in committed files
- Accessibility: add `alt` text to all images
