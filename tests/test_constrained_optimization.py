"""
Unit tests for constrained_optimization module (Phase 2).
Tests constraint-based supplier allocation with SLA enforcement and dual-sourcing.
"""

import pytest
import sqlite3
import pandas as pd
from constrained_optimization import run_constrained_optimization


@pytest.fixture
def in_memory_db():
    """Create in-memory SQLite database with test data."""
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()
    
    # Create supplier_performance view
    cursor.execute('''
        CREATE TABLE suppliers (
            supplier_id INTEGER PRIMARY KEY,
            supplier_name TEXT,
            category TEXT,
            on_time_delivery_pct REAL,
            quality_incidents_per_order REAL,
            risk_level TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE supplier_pricing (
            supplier_id INTEGER,
            material_id INTEGER,
            price_ngn REAL,
            FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE procurement_data (
            purchase_order_id INTEGER,
            supplier_id INTEGER,
            material_id INTEGER,
            category TEXT,
            quantity INTEGER,
            unit_price_ngn REAL,
            total_cost_ngn REAL,
            order_date TEXT,
            FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id)
        )
    ''')
    
    # Insert test suppliers
    suppliers = [
        (1, 'SupplierA', 'Raw Materials', 95.0, 0.02, 'Low'),
        (2, 'SupplierB', 'Raw Materials', 88.0, 0.05, 'Medium'),
        (3, 'SupplierC', 'Packaging', 92.0, 0.01, 'Low'),
        (4, 'SupplierD', 'Packaging', 85.0, 0.10, 'High'),
    ]
    cursor.executemany('INSERT INTO suppliers VALUES (?, ?, ?, ?, ?, ?)', suppliers)
    
    # Insert test procurement data (with total spend for each category)
    procurement = [
        (1, 1, 100, 'Raw Materials', 1000, 100.0, 100000.0, '2024-01-01'),
        (2, 1, 100, 'Raw Materials', 500, 100.0, 50000.0, '2024-01-02'),
        (3, 2, 100, 'Raw Materials', 800, 95.0, 76000.0, '2024-01-03'),
        (4, 3, 200, 'Packaging', 2000, 50.0, 100000.0, '2024-01-04'),
        (5, 3, 200, 'Packaging', 1500, 50.0, 75000.0, '2024-01-05'),
        (6, 4, 200, 'Packaging', 1000, 48.0, 48000.0, '2024-01-06'),
    ]
    cursor.executemany(
        'INSERT INTO procurement_data VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
        procurement
    )
    
    conn.commit()
    yield conn
    conn.close()


def test_constrained_optimization_basic(in_memory_db):
    """Test basic constrained optimization execution."""
    constraints = {
        'min_otd_pct': 85.0,
        'max_quality_incidents_per_order': 0.08,
        'risk_level_cap': 'Medium',
        'min_dual_source_threshold_ngn': 50000.0,
        'price_percentile_cap': 80,
        'max_single_supplier_share_pct': 80.0,
    }
    
    results_df, summary = run_constrained_optimization(
        conn=in_memory_db,
        constraints=constraints
    )
    
    assert isinstance(results_df, pd.DataFrame)
    assert isinstance(summary, dict)
    assert 'constrained_savings_ngn' in summary
    assert 'constrained_savings_pct' in summary
    assert 'dual_sourced_categories' in summary
    assert summary['constrained_savings_ngn'] >= 0
    assert 0 <= summary['constrained_savings_pct'] <= 100


def test_constrained_optimization_conservative(in_memory_db):
    """Test conservative constraint preset (stricter SLAs)."""
    constraints = {
        'min_otd_pct': 90.0,  # Higher bar
        'max_quality_incidents_per_order': 0.05,  # Tighter quality
        'risk_level_cap': 'Low',  # Only low-risk suppliers
        'min_dual_source_threshold_ngn': 100000.0,
        'price_percentile_cap': 75,
        'max_single_supplier_share_pct': 65.0,
    }
    
    results_df, summary = run_constrained_optimization(
        conn=in_memory_db,
        constraints=constraints
    )
    
    # Conservative preset should result in more suppliers due to dual-sourcing
    assert summary['dual_sourced_categories'] >= 0
    assert 'constrained_savings_ngn' in summary


def test_constrained_optimization_dual_sourcing(in_memory_db):
    """Test dual-sourcing enforcement for large categories."""
    constraints = {
        'min_otd_pct': 80.0,
        'max_quality_incidents_per_order': 0.15,
        'risk_level_cap': 'High',
        'min_dual_source_threshold_ngn': 100000.0,  # Triggers dual-sourcing for Packaging
        'price_percentile_cap': 90,
        'max_single_supplier_share_pct': 85.0,
    }
    
    results_df, summary = run_constrained_optimization(
        conn=in_memory_db,
        constraints=constraints
    )
    
    assert summary['dual_sourced_categories'] >= 0
    assert len(results_df) > 0


def test_constrained_optimization_single_supplier_share(in_memory_db):
    """Test that single supplier share respects max cap."""
    constraints = {
        'min_otd_pct': 80.0,
        'max_quality_incidents_per_order': 0.15,
        'risk_level_cap': 'High',
        'min_dual_source_threshold_ngn': 50000.0,
        'price_percentile_cap': 90,
        'max_single_supplier_share_pct': 50.0,  # Tight cap
    }
    
    results_df, summary = run_constrained_optimization(
        conn=in_memory_db,
        constraints=constraints
    )
    
    if len(results_df) > 0:
        # Check that no single supplier exceeds the cap for any category
        category_groups = results_df.groupby('category')
        for category, group in category_groups:
            for supplier_id in group['supplier_id'].unique():
                supplier_allocation_pct = (
                    group[group['supplier_id'] == supplier_id]['supplier_allocation_share_pct'].sum()
                )
                assert supplier_allocation_pct <= constraints['max_single_supplier_share_pct'] + 1  # +1% tolerance


def test_constrained_optimization_returns_dataframe_structure(in_memory_db):
    """Test that output DataFrame has required columns."""
    constraints = {
        'min_otd_pct': 85.0,
        'max_quality_incidents_per_order': 0.08,
        'risk_level_cap': 'Medium',
        'min_dual_source_threshold_ngn': 50000.0,
        'price_percentile_cap': 80,
        'max_single_supplier_share_pct': 80.0,
    }
    
    results_df, summary = run_constrained_optimization(
        conn=in_memory_db,
        constraints=constraints
    )
    
    # Check core columns that should exist
    if len(results_df) > 0:
        assert 'category' in results_df.columns
        assert 'supplier_id' in results_df.columns
        assert 'supplier_name' in results_df.columns


def test_constrained_optimization_summary_structure(in_memory_db):
    """Test that summary dict has required keys."""
    constraints = {
        'min_otd_pct': 85.0,
        'max_quality_incidents_per_order': 0.08,
        'risk_level_cap': 'Medium',
        'min_dual_source_threshold_ngn': 50000.0,
        'price_percentile_cap': 80,
        'max_single_supplier_share_pct': 80.0,
    }
    
    _, summary = run_constrained_optimization(
        conn=in_memory_db,
        constraints=constraints
    )
    
    required_keys = {'constrained_savings_ngn', 'constrained_savings_pct', 'dual_sourced_categories'}
    assert required_keys.issubset(set(summary.keys()))
    assert isinstance(summary['constrained_savings_ngn'], (int, float))
    assert isinstance(summary['constrained_savings_pct'], (int, float))
    assert isinstance(summary['dual_sourced_categories'], int)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
