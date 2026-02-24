"""
Monte Carlo simulation for procurement savings uncertainty quantification.
Propagates uncertainty in savings drivers to generate confidence intervals.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def run_monte_carlo_analysis(
    base_insights: dict,
    num_simulations: int = 10000,
    random_seed: int = 42,
    uncertainty_params: dict | None = None,
) -> dict:
    """
    Run Monte Carlo simulation on savings estimates.

    Uncertainty params (std dev as % of base):
    - price_standardization_sigma: volatility in price variance realization
    - performance_improvement_sigma: volatility in supplier replacement benefit
    - consolidation_sigma: volatility in consolidation savings
    - total_spend_sigma: volatility in procured volume/pricing
    """

    if uncertainty_params is None:
        uncertainty_params = {
            "price_standardization_sigma": 0.15,
            "performance_improvement_sigma": 0.20,
            "consolidation_sigma": 0.25,
            "total_spend_sigma": 0.05,
        }

    np.random.seed(random_seed)

    total_spend_base = float(base_insights.get("total_spend", 0.0))
    price_base = float(base_insights.get("price_standardization_savings", 0.0))
    perf_base = float(base_insights.get("performance_improvement_savings", 0.0))
    cons_base = float(base_insights.get("consolidation_savings", 0.0))

    price_sigma = price_base * float(uncertainty_params.get("price_standardization_sigma", 0.15))
    perf_sigma = perf_base * float(uncertainty_params.get("performance_improvement_sigma", 0.20))
    cons_sigma = cons_base * float(uncertainty_params.get("consolidation_sigma", 0.25))
    spend_sigma = total_spend_base * float(uncertainty_params.get("total_spend_sigma", 0.05))

    draws = {
        "price": np.maximum(0.0, np.random.normal(price_base, price_sigma, num_simulations)),
        "perf": np.maximum(0.0, np.random.normal(perf_base, perf_sigma, num_simulations)),
        "cons": np.maximum(0.0, np.random.normal(cons_base, cons_sigma, num_simulations)),
        "spend": np.maximum(total_spend_base * 0.5, np.random.normal(total_spend_base, spend_sigma, num_simulations)),
    }

    total_savings_draws = draws["price"] + draws["perf"] + draws["cons"]
    savings_pct_draws = (total_savings_draws / draws["spend"]) * 100.0

    results = {
        "total_savings_mean_ngn": float(np.mean(total_savings_draws)),
        "total_savings_median_ngn": float(np.median(total_savings_draws)),
        "total_savings_std_ngn": float(np.std(total_savings_draws)),
        "total_savings_p05_ngn": float(np.percentile(total_savings_draws, 5)),
        "total_savings_p25_ngn": float(np.percentile(total_savings_draws, 25)),
        "total_savings_p75_ngn": float(np.percentile(total_savings_draws, 75)),
        "total_savings_p95_ngn": float(np.percentile(total_savings_draws, 95)),
        "savings_pct_mean": float(np.mean(savings_pct_draws)),
        "savings_pct_median": float(np.median(savings_pct_draws)),
        "savings_pct_p05": float(np.percentile(savings_pct_draws, 5)),
        "savings_pct_p95": float(np.percentile(savings_pct_draws, 95)),
    }

    return results


def monte_carlo_to_dataframe(mc_results: dict) -> pd.DataFrame:
    """Convert Monte Carlo results dict to a display-ready DataFrame."""

    rows = [
        ("Mean", mc_results.get("total_savings_mean_ngn"), mc_results.get("savings_pct_mean")),
        ("Median", mc_results.get("total_savings_median_ngn"), mc_results.get("savings_pct_median")),
        ("Std Dev", mc_results.get("total_savings_std_ngn"), None),
        ("5% Percentile", mc_results.get("total_savings_p05_ngn"), mc_results.get("savings_pct_p05")),
        ("25% Percentile", mc_results.get("total_savings_p25_ngn"), None),
        ("75% Percentile", mc_results.get("total_savings_p75_ngn"), None),
        ("95% Percentile", mc_results.get("total_savings_p95_ngn"), mc_results.get("savings_pct_p95")),
    ]

    df = pd.DataFrame(rows, columns=["Statistic", "Total Savings (NGN)", "Savings % of Spend"])
    df["Total Savings (NGN)"] = df["Total Savings (NGN)"].apply(lambda x: f"{x:,.0f}" if x is not None else "—")
    df["Savings % of Spend"] = df["Savings % of Spend"].apply(lambda x: f"{x:.2f}%" if x is not None else "—")

    return df
