# Power BI Page Build Sheet

Use this as the page-by-page implementation checklist when converting the deployment pack into a `.pbix` or `.pbit`.

## Page 1 — Executive Overview

### Visuals

- 4 KPI cards: Total Spend, Total Savings Potential, Savings %, Maverick Spend
- Clustered bar: Spend by Category
- Line chart: Monthly Spend by Category
- Clustered bar: Savings Scenarios

### Slicers

- Category
- Month

### Notes

- Use `procurement_insights_summary` for cards.
- Use `category_spend` and `monthly_spend_by_category` for category and trend visuals.

## Page 2 — Supplier Performance

### Visuals

- Matrix: Supplier scorecard
- Scatter: On-time Delivery % vs Total Quality Cost
- Column chart: Performance Grade by Category
- Bar chart: Top Suppliers by Spend

### Slicers

- Category
- Country
- Performance Grade

### Notes

- Use conditional formatting on performance grades.
- Highlight suppliers with low OTD and high quality cost.

## Page 3 — Savings Opportunities

### Visuals

- Horizontal bar: Top Price Variance Opportunities
- Table: Optimization Recommendations
- Table: Constrained Sourcing Plan
- Cards: Optimization Savings and Constrained Savings

### Slicers

- Category
- Supplier
- Material

### Notes

- Sort price-variance bars by `potential_savings_ngn` descending.
- Keep the top 15 materials visible on default view.

## Page 4 — Risk & Uncertainty

### Visuals

- Bar chart: Maverick Spend by Risk Level
- KPI cards: USD Spend, FX Volatility, Monte Carlo P05, P50, P95
- Table: Monte Carlo Uncertainty Bounds

### Slicers

- Category
- Risk Level

### Notes

- Color-code risk levels red/amber/green.
- Use the Monte Carlo table as an executive appendix visual.

## Page 5 — Data Quality & Refresh Notes

### Visuals

- Table: Data-quality diagnostics imported from JSON or manual table
- Card: Data source label
- Text boxes: Refresh steps, assumptions, upload policy

### Notes

- This page is especially useful for company-data demos.
- Include notes on alias normalization and missing-field defaults.

## Final QA checklist

- Apply `powerbi_theme.json`
- Import DAX from `DAX_MEASURES.md`
- Validate category relationships
- Validate currency and percentage formatting
- Save final template as `Procurement_Spend_Intelligence_Template.pbit`
