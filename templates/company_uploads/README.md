# Company Upload Templates

Use these starter CSV files when preparing company data for the Streamlit dashboard.

## Required files

- `suppliers_template.csv`
- `materials_template.csv`
- `purchase_orders_template.csv`

## Optional file

- `quality_incidents_template.csv`

## Notes

- Column aliases are supported, but matching the canonical template names reduces cleanup.
- Dates should be formatted as `YYYY-MM-DD`.
- `total_amount_ngn` can be left blank if `quantity * unit_price_ngn` should be derived.
- `total_amount_usd` is optional for NGN transactions.
- Boolean supplier approval values can be `TRUE/FALSE`, `Yes/No`, or `1/0`.
