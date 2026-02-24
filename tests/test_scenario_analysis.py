import pytest

from scenario_analysis import run_sensitivity_analysis


def test_sensitivity_outputs_totals_and_pct():
    insights = {
        "total_spend": 1_000_000.0,
        "price_standardization_savings": 100_000.0,
        "performance_improvement_savings": 200_000.0,
        "consolidation_savings": 50_000.0,
    }

    scenarios = {
        "Conservative": {
            "price_standardization": 0.8,
            "performance_improvement": 0.8,
            "consolidation": 0.8,
        },
        "Base": {
            "price_standardization": 1.0,
            "performance_improvement": 1.0,
            "consolidation": 1.0,
        },
    }

    df = run_sensitivity_analysis(insights=insights, scenario_factors=scenarios)

    assert set(df["scenario"].tolist()) == {"Conservative", "Base"}

    base = df[df["scenario"] == "Base"].iloc[0]
    assert base["total_savings_ngn"] == pytest.approx(350_000.0)
    assert base["savings_pct_of_spend"] == pytest.approx(35.0)
