from __future__ import annotations

from dataclasses import dataclass
import logging

import numpy as np
import pandas as pd
from scipy.optimize import Bounds, LinearConstraint, milp


RISK_ORDER = {"Low": 0.0, "Medium": 0.5, "High": 1.0}
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class OptimizationResult:
    recommendations: pd.DataFrame
    summary: dict[str, float]


def _normalize(series: pd.Series, inverse: bool = False) -> pd.Series:
    values = series.astype(float)
    min_val = values.min()
    max_val = values.max()
    if max_val == min_val:
        base = pd.Series(np.ones(len(values)), index=values.index)
    else:
        base = (values - min_val) / (max_val - min_val)
    return 1 - base if inverse else base


def _objective_costs(frame: pd.DataFrame, weights: dict[str, float]) -> pd.Series:
    quality_column = "quality_cost_ngn" if "quality_cost_ngn" in frame.columns else "total_quality_cost_ngn"
    cost_component = _normalize(frame["avg_unit_cost_ngn"], inverse=False)
    delivery_component = _normalize(frame["on_time_delivery_pct"], inverse=True)
    quality_component = _normalize(frame[quality_column], inverse=False)
    risk_component = frame["risk_level"].map(RISK_ORDER).fillna(1.0)
    return (
        weights["unit_cost"] * cost_component
        + weights["delivery"] * delivery_component
        + weights["quality"] * quality_component
        + weights["risk"] * risk_component
    )


def _build_optimized_frame(
    frame: pd.DataFrame,
    shares: np.ndarray,
    selected: np.ndarray,
    category_spend: float,
    category_quantity: float,
) -> pd.DataFrame:
    optimized = frame.copy()
    optimized["recommended_share"] = shares
    optimized["selected"] = selected
    optimized = optimized[optimized["recommended_share"] > 1e-6].copy()
    optimized["projected_quantity"] = optimized["recommended_share"] * category_quantity
    optimized["projected_spend_ngn"] = optimized["projected_quantity"] * optimized["avg_unit_cost_ngn"]
    optimized["historical_category_spend_ngn"] = category_spend
    return optimized


def _fallback_category_mix(
    frame: pd.DataFrame,
    category_spend: float,
    category_quantity: float,
    min_selected_suppliers: int,
) -> pd.DataFrame:
    fallback_count = min(max(1, min_selected_suppliers), len(frame))
    selected = np.zeros(len(frame), dtype=bool)
    selected[:fallback_count] = True
    shares = np.zeros(len(frame), dtype=float)

    if fallback_count == 1:
        shares[0] = 1.0
    else:
        costs = frame.iloc[:fallback_count]["avg_unit_cost_ngn"].astype(float).to_numpy()
        safe_costs = np.where(costs > 0, costs, 1.0)
        weights = 1.0 / safe_costs
        shares[:fallback_count] = weights / weights.sum()

    return _build_optimized_frame(frame, shares, selected, category_spend, category_quantity)


def _solve_category_mix(
    frame: pd.DataFrame,
    category_spend: float,
    category_quantity: float,
    max_suppliers: int,
    min_supplier_share: float,
    max_single_supplier_share: float,
    min_selected_suppliers: int = 1,
) -> pd.DataFrame:
    n = len(frame)
    if n == 0:
        raise ValueError("Category optimization requires at least one supplier.")
    if min_selected_suppliers > max_suppliers:
        raise ValueError("Minimum selected suppliers cannot exceed max suppliers.")
    if min_selected_suppliers > n:
        raise ValueError("Not enough suppliers remain to satisfy minimum selection.")
    if max_single_supplier_share * n < 1.0 - 1e-9:
        raise ValueError("Supplier share cap makes the category infeasible.")
    if min_supplier_share * min_selected_suppliers > 1.0 + 1e-9:
        raise ValueError("Minimum supplier share makes the category infeasible.")

    shares_offset = 0
    select_offset = n
    num_vars = 2 * n

    c = np.concatenate([frame["avg_unit_cost_ngn"].to_numpy(dtype=float), np.full(n, 0.001)])
    integrality = np.concatenate([np.zeros(n, dtype=int), np.ones(n, dtype=int)])
    lower = np.concatenate([np.zeros(n), np.zeros(n)])
    upper = np.concatenate([np.full(n, max_single_supplier_share), np.ones(n)])
    bounds = Bounds(lower, upper)

    constraints = []

    sum_row = np.zeros(num_vars)
    sum_row[:n] = 1.0
    constraints.append(LinearConstraint(sum_row, lb=1.0, ub=1.0))

    select_row = np.zeros(num_vars)
    select_row[select_offset:] = 1.0
    constraints.append(LinearConstraint(select_row, lb=float(min_selected_suppliers), ub=float(max_suppliers)))

    for i in range(n):
        row_upper = np.zeros(num_vars)
        row_upper[i] = 1.0
        row_upper[select_offset + i] = -max_single_supplier_share
        constraints.append(LinearConstraint(row_upper, lb=-np.inf, ub=0.0))

        row_lower = np.zeros(num_vars)
        row_lower[i] = -1.0
        row_lower[select_offset + i] = min_supplier_share
        constraints.append(LinearConstraint(row_lower, lb=-np.inf, ub=0.0))

    result = milp(c=c, constraints=constraints, integrality=integrality, bounds=bounds)
    if not result.success or result.x is None:
        raise ValueError(f"MILP optimization failed: {result.message}")

    shares = result.x[shares_offset:shares_offset + n]
    selected = result.x[select_offset:select_offset + n] > 0.5
    return _build_optimized_frame(frame, shares, selected, category_spend, category_quantity)


def _optimize_categories(
    supplier_metrics: pd.DataFrame,
    category_history: pd.DataFrame,
    weights: dict[str, float],
    max_suppliers_per_category: int,
    min_supplier_share: float,
    max_single_supplier_share: float,
    category_options: dict[str, dict[str, float | int]] | None = None,
    allow_fallback: bool = False,
) -> OptimizationResult:
    recommendations = []
    historical_spend = float(category_history["category_spend_ngn"].sum())

    for category, frame in supplier_metrics.groupby("category"):
        category_row = category_history[category_history["category"] == category].iloc[0]
        scoped = frame.copy()
        scoped["composite_penalty"] = _objective_costs(scoped, weights)
        scoped = scoped.sort_values(["composite_penalty", "avg_unit_cost_ngn"], ascending=[True, True]).reset_index(drop=True)

        options = (category_options or {}).get(category, {})
        resolved_max_suppliers = int(options.get("max_suppliers", max_suppliers_per_category))
        resolved_min_supplier_share = float(options.get("min_supplier_share", min_supplier_share))
        resolved_max_single_supplier_share = float(options.get("max_single_supplier_share", max_single_supplier_share))
        resolved_min_selected_suppliers = int(options.get("min_selected_suppliers", 1))

        try:
            optimized = _solve_category_mix(
                frame=scoped,
                category_spend=float(category_row["category_spend_ngn"]),
                category_quantity=float(category_row["category_quantity"]),
                max_suppliers=resolved_max_suppliers,
                min_supplier_share=resolved_min_supplier_share,
                max_single_supplier_share=resolved_max_single_supplier_share,
                min_selected_suppliers=resolved_min_selected_suppliers,
            )
        except ValueError as exc:
            if not allow_fallback:
                raise
            logger.warning("Falling back to deterministic supplier allocation for category %s: %s", category, exc)
            optimized = _fallback_category_mix(
                frame=scoped,
                category_spend=float(category_row["category_spend_ngn"]),
                category_quantity=float(category_row["category_quantity"]),
                min_selected_suppliers=resolved_min_selected_suppliers,
            )

        recommendations.append(optimized)

    recommendations_df = pd.concat(recommendations, ignore_index=True) if recommendations else pd.DataFrame()
    optimized_spend = float(recommendations_df["projected_spend_ngn"].sum()) if not recommendations_df.empty else historical_spend
    savings = max(0.0, historical_spend - optimized_spend)
    savings_pct = (savings / historical_spend * 100.0) if historical_spend else 0.0

    return OptimizationResult(
        recommendations_df,
        {
            "historical_spend_ngn": historical_spend,
            "optimized_spend_ngn": optimized_spend,
            "optimization_savings_ngn": savings,
            "optimization_savings_pct": savings_pct,
        },
    )


def optimize_supplier_mix(
    supplier_metrics: pd.DataFrame,
    category_history: pd.DataFrame,
    max_suppliers_per_category: int = 3,
    min_supplier_share: float = 0.15,
    max_single_supplier_share: float = 0.8,
    score_weights: dict[str, float] | None = None,
) -> OptimizationResult:
    if supplier_metrics.empty:
        return OptimizationResult(pd.DataFrame(), {
            "historical_spend_ngn": 0.0,
            "optimized_spend_ngn": 0.0,
            "optimization_savings_ngn": 0.0,
            "optimization_savings_pct": 0.0,
        })

    weights = score_weights or {
        "unit_cost": 0.45,
        "delivery": 0.30,
        "quality": 0.15,
        "risk": 0.10,
    }
    return _optimize_categories(
        supplier_metrics=supplier_metrics,
        category_history=category_history,
        weights=weights,
        max_suppliers_per_category=max_suppliers_per_category,
        min_supplier_share=min_supplier_share,
        max_single_supplier_share=max_single_supplier_share,
    )


def optimize_supplier_mix_with_constraints(
    supplier_metrics: pd.DataFrame,
    category_history: pd.DataFrame,
    constraints: dict,
) -> OptimizationResult:
    if supplier_metrics.empty:
        return OptimizationResult(pd.DataFrame(), {
            "constrained_spend_ngn": 0.0,
            "constrained_savings_ngn": 0.0,
            "constrained_savings_pct": 0.0,
            "dual_sourced_categories": 0,
        })

    risk_level_order = {"Low": 0, "Medium": 1, "High": 2}
    max_risk_numeric = risk_level_order.get(constraints.get("max_risk_level", "High"), 2)
    eligible = supplier_metrics.copy()
    eligible["risk_numeric"] = eligible["risk_level"].map(risk_level_order).fillna(3)
    eligible = eligible[
        (eligible["on_time_delivery_pct"] >= float(constraints.get("min_on_time_delivery_pct", 0)))
        & (eligible["quality_incident_count"] <= float(constraints.get("max_quality_incidents_per_order", float("inf"))))
        & (eligible["risk_numeric"] <= max_risk_numeric)
    ].copy()
    if eligible.empty:
        eligible = supplier_metrics.copy()

    weights = {
        "unit_cost": 0.45,
        "delivery": 0.30,
        "quality": 0.15,
        "risk": 0.10,
    }
    dual_source_threshold = float(constraints.get("min_dual_source_threshold", 0))
    max_single_supplier_share = float(constraints.get("max_single_supplier_share", 0.8))
    min_supplier_share = min(max_single_supplier_share / 2, 0.35)
    scoped_frames = []
    category_options: dict[str, dict[str, float | int]] = {}

    for category, frame in supplier_metrics.groupby("category"):
        eligible_frame = eligible[eligible["category"] == category].copy()
        eligible_count = len(eligible_frame)
        scoped = eligible_frame if eligible_count else frame.copy()
        if eligible_count == 0:
            logger.warning("No suppliers met constrained eligibility for category %s; using original candidate set.", category)

        category_row = category_history[category_history["category"] == category].iloc[0]
        category_spend = float(category_row["category_spend_ngn"])
        dual_source_required = eligible_count >= 2 and category_spend >= dual_source_threshold
        category_options[category] = {
            "max_suppliers": min(2, len(scoped)),
            "min_selected_suppliers": 2 if dual_source_required else 1,
            "min_supplier_share": min_supplier_share,
            "max_single_supplier_share": 1.0 if len(scoped) == 1 else max_single_supplier_share,
        }
        scoped_frames.append(scoped)

    scoped_metrics = pd.concat(scoped_frames, ignore_index=True) if scoped_frames else eligible
    result = _optimize_categories(
        supplier_metrics=scoped_metrics,
        category_history=category_history,
        weights=weights,
        max_suppliers_per_category=2,
        min_supplier_share=min_supplier_share,
        max_single_supplier_share=max_single_supplier_share,
        category_options=category_options,
        allow_fallback=True,
    )
    recommendations = result.recommendations.copy()
    recommendations["constrained_share"] = recommendations["recommended_share"]
    recommendations["dual_sourced"] = recommendations.groupby("category")["supplier_id"].transform("nunique").gt(1).astype(int)
    constrained_summary = {
        "constrained_spend_ngn": result.summary["optimized_spend_ngn"],
        "constrained_savings_ngn": result.summary["optimization_savings_ngn"],
        "constrained_savings_pct": result.summary["optimization_savings_pct"],
        "dual_sourced_categories": int(recommendations.groupby("category")["supplier_id"].nunique().gt(1).sum()) if not recommendations.empty else 0,
    }
    return OptimizationResult(recommendations, constrained_summary)
