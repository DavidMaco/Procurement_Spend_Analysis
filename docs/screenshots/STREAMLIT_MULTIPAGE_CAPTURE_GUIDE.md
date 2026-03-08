# Streamlit Multipage Capture Guide

Use this guide when capturing polished screenshots from the Streamlit app for portfolio use.

## Recommended screenshot set

### Required recruiter-facing set

1. `01-executive-dashboard.png`
2. `02-supplier-performance.png`
3. `03-savings-opportunities.png`
4. `04-risk-analysis.png`

### Optional extended set

1. `05-data-hub.png`

## Page-to-file mapping

- `01-executive-dashboard.png` → `Executive Overview`
- `02-supplier-performance.png` → `Supplier Performance`
- `03-savings-opportunities.png` → `Savings Opportunities`
- `04-risk-analysis.png` → `Risk & Uncertainty`
- `05-data-hub.png` → `Data Hub`

## Capture standards

- Resolution: 1920x1080 minimum
- Browser zoom: 100%
- Theme: use the default light theme from `.streamlit/config.toml`
- Filters: keep all categories selected unless the screenshot is telling a tighter story
- File format: PNG

## Recommended capture flow

1. Launch the app with bundled demo data.
2. Open each dedicated page from the multipage sidebar.
3. Wait for plots to finish rendering.
4. Ensure tables show meaningful top rows before capture.
5. Export each screenshot with the exact file name.

## Page-specific notes

### Executive Overview

Include:

- KPI strip
- spend by category chart
- monthly spend trend
- scenario outlook

### Supplier Performance

Include:

- supplier scorecard table
- OTD vs quality scatter
- performance grade chart

### Savings Opportunities

Include:

- top price variance chart
- optimization recommendation table
- constrained sourcing plan

### Risk & Uncertainty

Include:

- risk exposure bar chart
- FX and Monte Carlo KPI cards
- Monte Carlo bounds table

### Data Hub

Include:

- data-quality report
- expected upload schemas
- Power BI download section

## Redaction guidance

If using company data:

- hide supplier names if required
- remove internal buyer names
- remove confidential plant or site names
- prefer category-level views for public screenshots
