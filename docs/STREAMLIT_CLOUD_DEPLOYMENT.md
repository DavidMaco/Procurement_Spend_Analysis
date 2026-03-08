# Streamlit Cloud Deployment Guide

This project is configured for direct deployment to Streamlit Community Cloud.

## Deployment target

- Entry point: `streamlit_app.py`
- Python runtime: `runtime.txt` (`python-3.11`)
- App theme and server defaults: `.streamlit/config.toml`

## Why this deploys well

- No database service is required for demo mode.
- Bundled CSV data is committed to the repository.
- Fresh synthetic data can be generated at runtime.
- Company CSV uploads are normalized in-app.
- Power BI deployment packs are generated directly from the app.

## Required files for deployment

- `requirements.txt`
- `runtime.txt`
- `.streamlit/config.toml`
- `streamlit_app.py`
- `pages/`

## Streamlit Cloud setup

1. Push the repository to GitHub.
2. In Streamlit Community Cloud, create a new app.
3. Select the repository and branch.
4. Set the main file path to `streamlit_app.py`.
5. Deploy.

## Recommended app settings

- Keep file uploads enabled.
- No secrets are required for demo mode.
- If using private company demos, deploy from a private repo or protected branch.

## Operational notes

- Uploads are session-scoped and not persisted.
- Generated datasets are reproducible through the seed control.
- Exported Power BI packs should be stored outside the app if long-term retention is needed.

## Troubleshooting

### App boots but charts are empty

Use the bundled demo source first to confirm the deployment is healthy.

### Upload normalization fails

Download the template pack from the sidebar and align column names or aliases.

### Slow startup

First render may take longer while dependencies install. Subsequent loads should be faster.
