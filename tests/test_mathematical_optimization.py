import pandas as pd
from hypothesis import given, strategies as st

from procurement_spend_analysis.optimization import optimize_supplier_mix


@given(
    cost_a=st.floats(min_value=10, max_value=1000, allow_nan=False, allow_infinity=False),
    cost_b=st.floats(min_value=10, max_value=1000, allow_nan=False, allow_infinity=False),
    cost_c=st.floats(min_value=10, max_value=1000, allow_nan=False, allow_infinity=False),
    otd_a=st.floats(min_value=60, max_value=100, allow_nan=False, allow_infinity=False),
    otd_b=st.floats(min_value=60, max_value=100, allow_nan=False, allow_infinity=False),
    otd_c=st.floats(min_value=60, max_value=100, allow_nan=False, allow_infinity=False),
)
def test_mip_supplier_mix_preserves_share_constraints(cost_a, cost_b, cost_c, otd_a, otd_b, otd_c):
    supplier_metrics = pd.DataFrame(
        {
            "category": ["Packaging", "Packaging", "Packaging"],
            "supplier_id": ["SUP1", "SUP2", "SUP3"],
            "supplier_name": ["A", "B", "C"],
            "total_quantity": [100, 120, 90],
            "total_spend_ngn": [100000, 130000, 95000],
            "avg_unit_cost_ngn": [cost_a, cost_b, cost_c],
            "on_time_delivery_pct": [otd_a, otd_b, otd_c],
            "quality_cost_ngn": [500.0, 900.0, 700.0],
            "risk_level": ["Low", "Medium", "High"],
        }
    )
    category_history = pd.DataFrame(
        {
            "category": ["Packaging"],
            "category_quantity": [500.0],
            "category_spend_ngn": [600000.0],
            "category_avg_unit_cost": [1200.0],
        }
    )

    result = optimize_supplier_mix(
        supplier_metrics=supplier_metrics,
        category_history=category_history,
        max_suppliers_per_category=3,
        min_supplier_share=0.15,
        max_single_supplier_share=0.8,
    )

    shares = result.recommendations["recommended_share"]
    assert not shares.empty
    assert abs(shares.sum() - 1.0) < 1e-6
    assert (shares <= 0.8 + 1e-9).all()
    assert (shares >= 0.15 - 1e-9).all()
