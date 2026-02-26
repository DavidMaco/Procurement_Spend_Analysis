import pandas as pd

from monte_carlo import monte_carlo_to_dataframe, run_monte_carlo_analysis


def sample_insights():
    return {
        "total_spend": 310_000_000_000.0,
        "price_standardization_savings": 18_000_000_000.0,
        "performance_improvement_savings": 120_000_000_000.0,
        "consolidation_savings": 10_000_000_000.0,
    }


def test_monte_carlo_analysis_execution():
    mc_results = run_monte_carlo_analysis(
        base_insights=sample_insights(),
        num_simulations=200,
        random_seed=42,
    )

    assert isinstance(mc_results, dict)
    assert "total_savings_mean_ngn" in mc_results
    assert "savings_pct_mean" in mc_results


def test_monte_carlo_percentile_structure():
    mc_results = run_monte_carlo_analysis(
        base_insights=sample_insights(),
        num_simulations=1000,
        random_seed=42,
    )

    required_keys = {
        "total_savings_mean_ngn",
        "total_savings_median_ngn",
        "total_savings_std_ngn",
        "total_savings_p05_ngn",
        "total_savings_p25_ngn",
        "total_savings_p75_ngn",
        "total_savings_p95_ngn",
    }
    assert required_keys.issubset(set(mc_results.keys()))

    assert mc_results["total_savings_p05_ngn"] <= mc_results["total_savings_p25_ngn"]
    assert mc_results["total_savings_p25_ngn"] <= mc_results["total_savings_median_ngn"]
    assert mc_results["total_savings_median_ngn"] <= mc_results["total_savings_p75_ngn"]
    assert mc_results["total_savings_p75_ngn"] <= mc_results["total_savings_p95_ngn"]


def test_monte_carlo_consistency_with_seed():
    mc_results1 = run_monte_carlo_analysis(
        base_insights=sample_insights(),
        num_simulations=500,
        random_seed=42,
    )

    mc_results2 = run_monte_carlo_analysis(
        base_insights=sample_insights(),
        num_simulations=500,
        random_seed=42,
    )

    assert mc_results1["total_savings_mean_ngn"] == mc_results2["total_savings_mean_ngn"]
    assert mc_results1["total_savings_median_ngn"] == mc_results2["total_savings_median_ngn"]


def test_monte_carlo_variance_with_different_seed():
    mc_results1 = run_monte_carlo_analysis(
        base_insights=sample_insights(),
        num_simulations=500,
        random_seed=42,
    )

    mc_results2 = run_monte_carlo_analysis(
        base_insights=sample_insights(),
        num_simulations=500,
        random_seed=999,
    )

    assert mc_results1["total_savings_mean_ngn"] != mc_results2["total_savings_mean_ngn"]


def test_monte_carlo_to_dataframe_basic():
    mc_results = run_monte_carlo_analysis(
        base_insights=sample_insights(),
        num_simulations=100,
        random_seed=42,
    )

    mc_df = monte_carlo_to_dataframe(mc_results)

    assert isinstance(mc_df, pd.DataFrame)
    assert len(mc_df) > 0
    assert {"Statistic", "Total Savings (NGN)", "Savings % of Spend"}.issubset(set(mc_df.columns))


def test_monte_carlo_to_dataframe_structure():
    mc_results = run_monte_carlo_analysis(
        base_insights=sample_insights(),
        num_simulations=100,
        random_seed=42,
    )

    mc_df = monte_carlo_to_dataframe(mc_results)
    stats = set(mc_df["Statistic"].tolist())
    assert {"Mean", "Median", "Std Dev", "5% Percentile", "95% Percentile"}.issubset(stats)


def test_monte_carlo_result_keys():
    mc_results = run_monte_carlo_analysis(
        base_insights=sample_insights(),
        num_simulations=100,
        random_seed=42,
    )

    required_keys = {
        "total_savings_mean_ngn",
        "total_savings_median_ngn",
        "total_savings_std_ngn",
        "total_savings_p05_ngn",
        "total_savings_p95_ngn",
        "savings_pct_mean",
        "savings_pct_median",
        "savings_pct_p05",
        "savings_pct_p95",
    }
    assert required_keys.issubset(set(mc_results.keys()))
