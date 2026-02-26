# Phase 3 - Power BI Handoff Pack

This handoff defines a recruiter-ready Power BI implementation for the Procurement Spend Analysis portfolio.

## Scope

Phase 3 covers:

1. Dashboard information architecture
2. Data model mapping from prepared CSV exports
3. Measure catalog and KPI definitions
4. Screenshot delivery checklist for portfolio publishing

## Input Files (Already Produced by Pipeline)

Use these files from the repository root:

- `procurement_insights_summary.csv`
- `category_spend.csv`
- `supplier_performance.csv`
- `price_variance_top20.csv`
- `monthly_spend_by_category.csv`
- `savings_scenarios.csv`
- `supplier_optimization_recommendations.csv`
- `constrained_supplier_recommendations.csv`
- `monte_carlo_uncertainty_bounds.csv`

## Dashboard Pages

## 1) Executive Overview

Visuals:
- KPI cards: Total Spend, Total Savings Potential, Savings %, Maverick Spend
- Category spend bar chart
- Monthly trend line chart
- Scenario comparison table (Conservative/Base/Aggressive)

Filters:
- Category
- Month/Year

## 2) Supplier Performance

Visuals:
- Supplier score table (spend, OTD %, quality incidents, risk)
- OTD vs quality incidents scatter
- Top underperformers bar chart

Filters:
- Supplier
- Category
- Risk level

## 3) Savings Opportunities

Visuals:
- Top materials by overpayment %
- Potential savings by material
- Optimization recommendations table
- Constrained optimization summary card

Filters:
- Category
- Material

## 4) Risk & Uncertainty

Visuals:
- Maverick spend breakdown
- FX exposure/volatility KPI cards
- Monte Carlo percentile table (P05, Median, P95)
- Confidence interval card

Filters:
- Category
- Supplier risk level

## KPI Definitions

- Total Spend: Sum of spend baseline in insights summary
- Total Savings Potential: Sum of identified opportunities
- Savings %: `Total Savings Potential / Total Spend`
- Constrained Savings %: constrained scenario savings percentage
- Monte Carlo P05/P95: downside/upside savings envelope from uncertainty simulation

## Build Steps

1. Load all listed CSV files with UTF-8 encoding.
2. Set numeric data types explicitly for amount and percent fields.
3. Create relationships only where keys are stable (category, supplier_id).
4. Build measures from `DAX_MEASURES.md`.
5. Apply consistent formatting:
   - Currency: NGN with thousands separator
   - Percentage: one or two decimals
6. Export screenshots to `docs/screenshots` using required names.

## Deliverables Checklist

- [ ] Power BI file (`.pbix`) built locally
- [ ] Four dashboard screenshots exported
- [ ] Screenshots copied into `docs/screenshots`
- [ ] README screenshot references verified
- [ ] Phase 3 walkthrough captured in portfolio notes
