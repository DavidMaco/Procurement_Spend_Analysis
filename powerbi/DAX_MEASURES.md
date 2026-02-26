# DAX Measures Starter Pack

Use these measures in the Power BI model for consistent KPI reporting.

## Core Financial Measures

```DAX
Total Spend NGN =
SUM('procurement_insights_summary'[value])
```

```DAX
Total Savings NGN =
CALCULATE(
    SUM('procurement_insights_summary'[value]),
    'procurement_insights_summary'[metric] = "total_savings"
)
```

```DAX
Savings Percent =
DIVIDE([Total Savings NGN], [Total Spend NGN], 0)
```

## Scenario Measures

```DAX
Scenario Savings NGN =
SUM('savings_scenarios'[total_savings_ngn])
```

```DAX
Scenario Savings Percent =
AVERAGE('savings_scenarios'[savings_pct_of_spend])
```

## Constraint and Risk Measures

```DAX
Constrained Savings NGN =
CALCULATE(
    MAX('procurement_insights_summary'[value]),
    'procurement_insights_summary'[metric] = "constrained_savings_ngn"
)
```

```DAX
Constrained Savings Percent =
CALCULATE(
    MAX('procurement_insights_summary'[value]),
    'procurement_insights_summary'[metric] = "constrained_savings_pct"
)
```

```DAX
Maverick Spend NGN =
CALCULATE(
    MAX('procurement_insights_summary'[value]),
    'procurement_insights_summary'[metric] = "maverick_spend"
)
```

## Monte Carlo Measures

```DAX
MC P05 Savings NGN =
CALCULATE(
    MAX('procurement_insights_summary'[value]),
    'procurement_insights_summary'[metric] = "total_savings_p05_ngn"
)
```

```DAX
MC Median Savings NGN =
CALCULATE(
    MAX('procurement_insights_summary'[value]),
    'procurement_insights_summary'[metric] = "total_savings_median_ngn"
)
```

```DAX
MC P95 Savings NGN =
CALCULATE(
    MAX('procurement_insights_summary'[value]),
    'procurement_insights_summary'[metric] = "total_savings_p95_ngn"
)
```

```DAX
MC Confidence Interval Width NGN =
[MC P95 Savings NGN] - [MC P05 Savings NGN]
```

## Formatting Guidance

- Format NGN measures as currency with no decimal places.
- Format percentage measures as `%` with 1–2 decimal places.
- Use conditional color for risk metrics (green/amber/red) via Power BI theme defaults.
