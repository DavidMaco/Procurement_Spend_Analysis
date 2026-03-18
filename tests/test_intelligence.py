"""Tests for AI/ML intelligence engines (intelligence.py)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from procurement_spend_analysis.intelligence import (
    AnomalyMethod,
    DemandForecastEngine,
    InsightGenerator,
    SavingsOpportunityFinder,
    SpendAnomalyDetector,
    SupplierRiskEngine,
)


# ── Fixtures ──────────────────────────────────────────────────────────────

def _make_po_df(n: int = 200) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    dates = pd.date_range("2023-01-01", periods=n, freq="D")
    categories = rng.choice(["Raw Materials", "Packaging", "Logistics", "Services"], n)
    suppliers = [f"SUP-{i:03d}" for i in rng.integers(1, 20, n)]
    return pd.DataFrame({
        "order_date": dates[:n],
        "category": categories,
        "supplier_id": suppliers,
        "unit_price": rng.normal(100, 30, n).clip(10),
        "quantity": rng.integers(10, 500, n),
        "total_amount": rng.normal(5000, 2000, n).clip(100),
    })


def _make_suppliers_df(n: int = 20) -> pd.DataFrame:
    return pd.DataFrame({
        "supplier_id": [f"SUP-{i:03d}" for i in range(1, n + 1)],
        "supplier_name": [f"Supplier {i}" for i in range(1, n + 1)],
        "country": ["Nigeria"] * 10 + ["Ghana"] * 5 + ["UK"] * 5,
        "years_active": list(range(1, n + 1)),
        "credit_rating": ["A"] * 5 + ["B"] * 10 + ["C"] * 5,
    })


def _make_quality_df(n: int = 30) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    return pd.DataFrame({
        "supplier_id": [f"SUP-{i:03d}" for i in rng.integers(1, 20, n)],
        "incident_type": rng.choice(["defect", "delay", "contamination"], n),
        "severity": rng.choice(["low", "medium", "high"], n),
    })


# ── Anomaly Detection ────────────────────────────────────────────────────

class TestSpendAnomalyDetector:
    def test_detect_returns_list(self):
        detector = SpendAnomalyDetector()
        df = _make_po_df(200)
        anomalies = detector.detect(df)
        assert isinstance(anomalies, list)

    def test_detect_zscore_method(self):
        detector = SpendAnomalyDetector(zscore_threshold=2.0)
        df = _make_po_df(200)
        anomalies = detector.detect(df, method=AnomalyMethod.ZSCORE)
        # Should find some anomalies with a low threshold
        assert isinstance(anomalies, list)

    def test_detect_combined_deduplicates(self):
        detector = SpendAnomalyDetector()
        df = _make_po_df(300)
        anomalies = detector.detect(df, method=AnomalyMethod.COMBINED)
        ids = [a.anomaly_id for a in anomalies]
        assert len(ids) == len(set(ids))  # no duplicates

    def test_anomaly_fields(self):
        detector = SpendAnomalyDetector()
        df = _make_po_df(300)
        anomalies = detector.detect(df)
        if anomalies:
            a = anomalies[0]
            assert hasattr(a, "anomaly_score")
            assert hasattr(a, "severity")
            assert hasattr(a, "explanation")
            assert a.severity in ("low", "medium", "high", "critical")


# ── Demand Forecasting ───────────────────────────────────────────────────

class TestDemandForecastEngine:
    def test_forecast_returns_results(self):
        engine = DemandForecastEngine(forecast_periods=3)
        df = _make_po_df(200)
        results = engine.forecast(df, date_col="order_date", value_col="unit_price", group_col="category")
        assert isinstance(results, list)

    def test_forecast_bounds(self):
        engine = DemandForecastEngine(forecast_periods=3)
        df = _make_po_df(200)
        results = engine.forecast(df, date_col="order_date", value_col="unit_price", group_col="category")
        for r in results:
            assert r.lower_bound <= r.point_forecast <= r.upper_bound


# ── Supplier Risk ────────────────────────────────────────────────────────

class TestSupplierRiskEngine:
    def test_assess_returns_scores(self):
        engine = SupplierRiskEngine()
        scores = engine.assess(_make_suppliers_df(), _make_po_df(), _make_quality_df())
        assert isinstance(scores, list)
        assert len(scores) > 0

    def test_risk_grade_valid(self):
        engine = SupplierRiskEngine()
        scores = engine.assess(_make_suppliers_df(), _make_po_df(), _make_quality_df())
        valid_grades = {"A", "B", "C", "D", "E"}
        for s in scores:
            assert s.risk_grade in valid_grades

    def test_overall_score_range(self):
        engine = SupplierRiskEngine()
        scores = engine.assess(_make_suppliers_df(), _make_po_df(), _make_quality_df())
        for s in scores:
            assert 0 <= s.overall_score <= 100


# ── Insight Generator ────────────────────────────────────────────────────

class TestInsightGenerator:
    def test_generate_returns_insights(self):
        gen = InsightGenerator()
        context = {
            "insights": {
                "total_spend_ngn": 5_000_000,
                "price_standardization_savings_ngn": 200_000,
                "on_time_delivery_pct": 85.0,
                "quality_incident_count": 12,
            },
            "analytics": {
                "category_spend": pd.DataFrame({"category": ["A", "B"], "total_spend": [3000, 2000]}),
                "price_variance_top20": pd.DataFrame({"material": ["M1"], "variance_pct": [25.0]}),
            },
            "forecasts": [],
        }
        insights = gen.generate(context)
        assert isinstance(insights, list)
        assert len(insights) > 0

    def test_insight_fields(self):
        gen = InsightGenerator()
        context = {
            "insights": {"total_spend_ngn": 1_000_000, "price_standardization_savings_ngn": 50_000, "on_time_delivery_pct": 90, "quality_incident_count": 5},
            "analytics": {"category_spend": pd.DataFrame(), "price_variance_top20": pd.DataFrame()},
            "forecasts": [],
        }
        insights = gen.generate(context)
        if insights:
            i = insights[0]
            assert hasattr(i, "headline")
            assert hasattr(i, "body")
            assert hasattr(i, "priority")


# ── Savings Opportunities ────────────────────────────────────────────────

class TestSavingsOpportunityFinder:
    def test_find_returns_opportunities(self):
        finder = SavingsOpportunityFinder()
        opps = finder.find(_make_po_df(300), _make_suppliers_df())
        assert isinstance(opps, list)

    def test_opportunity_fields(self):
        finder = SavingsOpportunityFinder()
        opps = finder.find(_make_po_df(300), _make_suppliers_df())
        if opps:
            o = opps[0]
            assert hasattr(o, "estimated_savings")
            assert hasattr(o, "confidence")
            assert 0 <= o.confidence <= 1
