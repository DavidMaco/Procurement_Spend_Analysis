# Power BI Deployment Guide

This project now ships with a Streamlit-first ingestion layer and a Power BI export pack
so the same procurement model can support:

1. realistic synthetic demo data for portfolio use
2. normalized external company data for stakeholder demos
3. repeatable Power BI desktop and service deployment

## Recommended deployment pattern

### Option A — Streamlit-first data intake

Use the Streamlit app to:

- generate a fresh realistic demo dataset
- upload company CSV extracts and normalize them into the canonical schema
- download a ready-to-use Power BI deployment pack

The deployment pack contains:

- curated analytics CSV exports
- normalized raw CSVs
- DAX starter measures
- theme JSON
- field mapping reference
- data-quality report
- `.pbit` starter specification
- page-by-page build sheet

### Option B — Local export pack generation

Run the export script locally if you want a Power BI package without launching Streamlit:

```bash
python powerbi/export_powerbi_pack.py --mode demo --output procurement_powerbi_pack.zip
```

Generate a fresh synthetic dataset first:

```bash
python powerbi/export_powerbi_pack.py --mode generate --num-orders 5000 --seed 7 --output procurement_powerbi_pack.zip
```

Build from a folder of external company CSVs:

```bash
python powerbi/export_powerbi_pack.py --mode folder --input-dir ./company_extracts --output procurement_powerbi_pack.zip
```

## Power BI Desktop steps

1. Unzip the deployment pack.
2. Load all files from the `exports/` folder.
3. Use `powerbi/powerbi_theme.json` as the report theme.
4. Create relationships using shared business keys only:
   - `category`
   - `supplier_id`
   - `material_name` where stable
5. Add measures from [powerbi/DAX_MEASURES.md](DAX_MEASURES.md).
6. Publish the report to Power BI Service.

Use these authoring assets while building:

- [POWERBI_PBIT_STARTER_SPEC.json](POWERBI_PBIT_STARTER_SPEC.json)
- [POWERBI_PAGE_BUILD_SHEET.md](POWERBI_PAGE_BUILD_SHEET.md)

## Recommended model

### Fact-style tables

- `monthly_spend_by_category`
- `price_variance_top20`
- `supplier_optimization_recommendations`
- `constrained_supplier_recommendations`
- `savings_scenarios`

### Dimension-like tables

- `category_spend`
- `supplier_performance`
- `procurement_insights_summary`

## Power BI Service refresh guidance

### For demo mode

- Store the zipped export pack or extracted CSVs in OneDrive or SharePoint.
- Configure scheduled refresh daily or weekly.

### For external company data

- Land raw CSVs in SharePoint, Azure Blob, or Fabric Lakehouse.
- Normalize them first through Streamlit or the local export script.
- Point Power BI refresh to the normalized `exports/` folder, not directly to inconsistent upstream source files.

## Governance guidance

- Keep uploaded company data in a separate workspace from the public portfolio demo.
- Treat `normalized_raw/` as controlled intermediate data.
- Publish only `exports/` tables to wider BI audiences.
- Use the bundled `data_quality_report.json` before publishing to detect missing keys or duplicates.

## Suggested report pages

1. Executive overview
2. Supplier performance
3. Savings opportunities
4. Risk and uncertainty
5. Data quality and ingestion readiness
