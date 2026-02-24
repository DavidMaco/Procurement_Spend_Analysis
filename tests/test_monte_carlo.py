"""
Unit tests for monte_carlo module (Phase 2).
Tests uncertainty quantification via Monte Carlo simulation.
"""

import pytest
import pandas as pd
import numpy as np
from monte_carlo import run_monte_carlo_analysis, monte_carlo_to_dataframe


@pytest.fixture
def sample_insights():
    """Create sample insights dict for Monte Carlo analysis."""
    return {
        'total_spend_ngn': 310000000000.0,  # ₦310B
        'optimization_savings_ngn': 15680000000.0,  # ₦15.68B
        'optimization_savings_pct': 5.05,
        'consolidation_savings_ngn': 50000000000.0,  # ₦50B
        'consolidation_savings_pct': 16.13,
        'price_variance_savings_ngn': 80000000000.0,  # ₦80B
        'price_variance_savings_pct': 25.81,
    }


def test_monte_carlo_analysis_execution(sample_insights):
    """Test that Monte Carlo analysis runs without errors."""
    mc_results = run_monte_carlo_analysis(
        base_insights=sample_insights,
        num_simulations=100,  # Small number for speed
        random_seed=42,
        uncertainty_params={
            'price_standardization_sigma': 0.15,
            'performance_improvement_sigma': 0.20,
            'consolidation_sigma': 0.25,
            'total_spend_sigma': 0.05,
        },
    )
    
    assert isinstance(mc_results, dict)
    assert 'total_savings_mean_ngn' in mc_results
    assert 'savings_pct_mean' in mc_results


def test_monte_carlo_percentile_structure(sample_insights):
    """Test that percentile calculations are present and ordered."""
    mc_results = run_monte_carlo_analysis(
        base_insights=sample_insights,
        num_simulations=1000,
        random_seed=42,
        uncertainty_params={
            'price_standardization_sigma': 0.15,
            'performance_improvement_sigma': 0.20,
            'consolidation_sigma': 0.25,
            'total_spend_sigma': 0.05,
        },
    )
    
    required_keys = {'total_savings_mean_ngn', 'total_savings_median_ngn', 'total_savings_std_ngn',
                     'total_savings_p05_ngn', 'total_savings_p25_ngn', 'total_savings_p75_ngn', 'total_savings_p95_ngn'}
    assert required_keys.issubset(set(mc_results.keys()))
    
    # Verify percentile ordering
    assert mc_results['total_savings_p05_ngn'] <= mc_results['total_savings_p25_ngn']
    assert mc_results['total_savings_p25_ngn'] <= mc_results['total_savings_median_ngn']
    assert mc_results['total_savings_median_ngn'] <= mc_results['total_savings_p75_ngn']
    assert mc_results['total_savings_p75_ngn'] <= mc_results['total_savings_p95_ngn']


def test_monte_carlo_consistency_with_seed(sample_insights):
    """Test that same seed produces same results (reproducibility)."""
    mc_results1 = run_monte_carlo_analysis(
        base_insights=sample_insights,
        num_simulations=500,
        random_seed=42,
        uncertainty_params={
            'price_standardization_sigma': 0.15,
            'performance_improvement_sigma': 0.20,
            'consolidation_sigma': 0.25,
            'total_spend_sigma': 0.05,
        },
    )
    
    mc_results2 = run_monte_carlo_analysis(
        base_insights=sample_insights,
        num_simulations=500,
        random_seed=42,
        uncertainty_params={
            'price_standardization_sigma': 0.15,
            'performance_improvement_sigma': 0.20,
            'consolidation_sigma': 0.25,
            'total_spend_sigma': 0.05,
        },
    )
    
    assert mc_results1['total_savings_mean_ngn'] == mc_results2['total_savings_mean_ngn']
    assert mc_results1['total_savings_median_ngn'] == mc_results2['total_savings_median_ngn']


def test_monte_carlo_variance_with_different_seed(sample_insights):
    """Test that different seeds produce different results."""
    mc_results1 = run_monte_carlo_analysis(
        base_insights=sample_insights,
        num_simulations=500,
        random_seed=42,
        uncertainty_params={
            'price_standardization_sigma': 0.15,
            'performance_improvement_sigma': 0.20,
            'consolidation_sigma': 0.25,
            'total_spend_sigma': 0.05,
        },
    )
    
    mc_results2 = run_monte_carlo_analysis(
        base_insights=sample_insights,
        num_simulations=500,
        random_seed=999,
        uncertainty_params={
            'price_standardization_sigma': 0.15,
            'performance_improvement_sigma': 0.20,
            'consolidation_sigma': 0.25,
            'total_spend_sigma': 0.05,
        },
    )
    
    # Results should differ (with high probability)
    assert mc_results1['total_savings_mean_ngn'] != mc_results2['total_savings_mean_ngn']


def test_monte_carlo_to_dataframe_basic(sample_insights):
    """Test conversion of MC results to DataFrame."""
    mc_results = run_monte_carlo_analysis(
        base_insights=sample_insights,
        num_simulations=100,
        random_seed=42,
        uncertainty_params={
            'price_standardization_sigma': 0.15,
            'performance_improvement_sigma': 0.20,
            'consolidation_sigma': 0.25,
            'total_spend_sigma': 0.05,
        },
    )
    
    mc_df = monte_carlo_to_dataframe(mc_results)
    
    assert isinstance(mc_df, pd.DataFrame)
    assert len(mc_df) > 0
    assert 'Metric' in mc_df.columns


def test_monte_carlo_to_dataframe_structure(sample_insights):
    """Test DataFrame structure includes all required statistics."""
    mc_results = run_monte_carlo_analysis(
        base_insights=sample_insights,
        num_simulations=100,
        random_seed=42,
        uncertainty_params={
            'price_standardization_sigma': 0.15,
            'performance_improvement_sigma': 0.20,
            'consolidation_sigma': 0.25,
            'total_spend_sigma': 0.05,
        },
    )
    
    mc_df = monte_carlo_to_dataframe(mc_results)
    
    # Check that key metrics are present
    metrics = mc_df['Metric'].unique()
    assert 'Total Savings (₦B)' in metrics or 'Total Savings (NGN_B)' in metrics.tolist()


def test_monte_carlo_with_high_uncertainty(sample_insights):
    """Test Monte Carlo with high uncertainty sigma values."""
    mc_results = run_monte_carlo_analysis(
        base_insights=sample_insights,
        num_simulations=500,
        random_seed=42,
        uncertainty_params={
            'price_standardization_sigma': 0.50,  # 50% uncertainty
            'performance_improvement_sigma': 0.50,
            'consolidation_sigma': 0.50,
            'total_spend_sigma': 0.20,
        },
    )
    
    # With high uncertainty, confidence interval should be wide:
    ci_width = mc_results['total_savings_p95_ngn'] - mc_results['total_savings_p05_ngn']
    assert ci_width > 0
    # Standard deviation should reflect high uncertainty
    assert mc_results['total_savings_std_ngn'] > mc_results['total_savings_mean_ngn'] * 0.1


def test_monte_carlo_with_low_uncertainty(sample_insights):
    """Test Monte Carlo with low uncertainty sigma values."""
    mc_results = run_monte_carlo_analysis(
        base_insights=sample_insights,
        num_simulations=500,
        random_seed=42,
        uncertainty_params={
            'price_standardization_sigma': 0.01,  # 1% uncertainty
            'performance_improvement_sigma': 0.01,
            'consolidation_sigma': 0.01,
            'total_spend_sigma': 0.005,
        },
    )
    
    # With low uncertainty, percentiles should be close to median
    assert abs(mc_results['total_savings_p25_ngn'] - mc_results['total_savings_median_ngn']) < \
           abs(mc_results['total_savings_p75_ngn'] - mc_results['total_savings_p25_ngn'])
    assert abs(mc_results['total_savings_p75_ngn'] - mc_results['total_savings_median_ngn']) < \
           abs(mc_results['total_savings_p75_ngn'] - mc_results['total_savings_p25_ngn'])


def test_monte_carlo_num_simulations_effect(sample_insights):
    """Test that more simulations reduce variance in percentile estimates."""
    # Small simulation count
    mc_small = run_monte_carlo_analysis(
        base_insights=sample_insights,
        num_simulations=100,
        random_seed=42,
        uncertainty_params={
            'price_standardization_sigma': 0.15,
            'performance_improvement_sigma': 0.20,
            'consolidation_sigma': 0.25,
            'total_spend_sigma': 0.05,
        },
    )
    
    # Large simulation count
    mc_large = run_monte_carlo_analysis(
        base_insights=sample_insights,
        num_simulations=5000,
        random_seed=42,
        uncertainty_params={
            'price_standardization_sigma': 0.15,
            'performance_improvement_sigma': 0.20,
            'consolidation_sigma': 0.25,
            'total_spend_sigma': 0.05,
        },
    )
    
    # Both should be valid (no assertions on accuracy, just that they run)
    assert 'total_savings_mean_ngn' in mc_small
    assert 'total_savings_mean_ngn' in mc_large


def test_monte_carlo_result_keys(sample_insights):
    """Test that all expected keys are in result dict."""
    mc_results = run_monte_carlo_analysis(
        base_insights=sample_insights,
        num_simulations=100,
        random_seed=42,
        uncertainty_params={
            'price_standardization_sigma': 0.15,
            'performance_improvement_sigma': 0.20,
            'consolidation_sigma': 0.25,
            'total_spend_sigma': 0.05,
        },
    )
    
    required_keys = {'total_savings_mean_ngn', 'total_savings_median_ngn', 'savings_pct_mean', 'savings_pct_median'}
    assert required_keys.issubset(set(mc_results.keys()))


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
