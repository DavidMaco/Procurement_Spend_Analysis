"""
Scenario and sensitivity analysis for procurement savings estimates.
"""

from __future__ import annotations

from typing import Dict

import pandas as pd


def run_sensitivity_analysis(insights: Dict[str, float], scenario_factors: Dict[str, Dict[str, float]]) -> pd.DataFrame:
    """Apply scenario multipliers to key savings components and return a scenario table."""

    base_price = float(insights.get("price_standardization_savings", 0.0))
    base_perf = float(insights.get("performance_improvement_savings", 0.0))
    base_cons = float(insights.get("consolidation_savings", 0.0))
    total_spend = float(insights.get("total_spend", 0.0))

    rows = []

    for scenario_name, factors in scenario_factors.items():
        price = base_price * float(factors.get("price_standardization", 1.0))
        perf = base_perf * float(factors.get("performance_improvement", 1.0))
        cons = base_cons * float(factors.get("consolidation", 1.0))
        total = price + perf + cons
        pct = (total / total_spend * 100) if total_spend > 0 else 0.0

        rows.append(
            {
                "scenario": scenario_name,
                "price_standardization_savings_ngn": round(price, 2),
                "performance_improvement_savings_ngn": round(perf, 2),
                "consolidation_savings_ngn": round(cons, 2),
                "total_savings_ngn": round(total, 2),
                "savings_pct_of_spend": round(pct, 4),
            }
        )

    return pd.DataFrame(rows).sort_values("total_savings_ngn")
