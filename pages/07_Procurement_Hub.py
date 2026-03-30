"""07 — FMCG Procurement Hub.

Cost-reduction dashboard for the procurement team.  Surfaces purchase-cost
variance by supplier, lead-time reliability, and negotiated-savings
realisation metrics from the FMCG OS.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from dashboard_ui import (
    PALETTE,
    configure_page,
    evaluate_fmcg_alerts,
    fmcg_user_has_permission,
    log_fmcg_recommendation,
    page_header,
    recommendation_history_df,
    render_chart,
    resolve_fmcg_recommendation,
    require_fmcg_dashboard_access,
)
from procurement_spend_analysis.fmcg.access_control import Permission
from procurement_spend_analysis.fmcg.event_log import ActionTaken


configure_page("Procurement Hub", icon="🔗")
principal = require_fmcg_dashboard_access(
    Permission.VIEW_PROCUREMENT_DASHBOARD,
    key_prefix="fmcg_procurement",
)

page_header(
    "FMCG Procurement Hub",
    "Purchase-cost optimisation, supplier lead-time reliability, and variance alerts.",
)

# ---------------------------------------------------------------------------
# Session-state initialisation — demo data
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def _demo_procurement() -> pd.DataFrame:
    rng = np.random.default_rng(99)
    n = 500
    dates = pd.date_range("2024-01-01", periods=180, freq="D")
    suppliers = [f"SUP-{i:03d}" for i in range(1, 21)]
    categories = ["Beverages", "Snacks", "Personal Care", "Dairy", "Bakery"]
    rows: list[dict] = []
    for _ in range(n):
        sup = rng.choice(suppliers)
        cat = rng.choice(categories)
        units = int(rng.integers(10, 500))
        unit_cost = rng.uniform(80, 2000)
        lead = int(rng.integers(2, 30))
        contracted = lead * rng.uniform(0.7, 1.0)
        rows.append(
            {
                "date": rng.choice(dates),
                "supplier_id": sup,
                "category": cat,
                "units_ordered": units,
                "purchase_cost": round(unit_cost * units, 2),
                "unit_cost": round(unit_cost, 2),
                "lead_time_days": lead,
                "contracted_lead_time": round(contracted, 1),
                "on_time": lead <= contracted + 1,
                "negotiated_cost": round(unit_cost * rng.uniform(0.85, 1.05), 2),
            }
        )
    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"])
    df["savings"] = (df["unit_cost"] - df["negotiated_cost"]) * df["units_ordered"]
    return df


df = _demo_procurement()

# ---------------------------------------------------------------------------
# KPI strip
# ---------------------------------------------------------------------------

total_cost = df["purchase_cost"].sum()
avg_lead = df["lead_time_days"].mean()
otd = df["on_time"].mean() * 100
realised_savings = df["savings"].sum()

baseline_df = df.copy()
baseline_df["purchase_cost"] = baseline_df["purchase_cost"] * 0.92
baseline_df["lead_time_days"] = (baseline_df["lead_time_days"] * 0.85).round(0)
procurement_alerts = evaluate_fmcg_alerts(
    baseline_df,
    df,
    category="procurement",
)

cols = st.columns(4, gap="small")
cols[0].metric("Total purchase cost", f"₦{total_cost:,.0f}")
cols[1].metric("Avg lead time", f"{avg_lead:.1f} days")
cols[2].metric("On-time delivery", f"{otd:.1f}%")
cols[3].metric("Negotiated savings", f"₦{realised_savings:,.0f}")

st.divider()

# ---------------------------------------------------------------------------
# Alerting and recommendations
# ---------------------------------------------------------------------------

alert_col, rec_col = st.columns([0.95, 1.05], gap="large")
with alert_col:
    st.markdown("##### Procurement alerts")
    if procurement_alerts.empty:
        st.info("No procurement alerts are firing against the current baseline.")
    else:
        st.metric("Active alerts", f"{len(procurement_alerts)}")
        st.dataframe(
            procurement_alerts[["rule_name", "severity", "metric_column", "variance_pct", "message"]],
            width="stretch",
            hide_index=True,
            height=260,
        )

with rec_col:
    st.markdown("##### Recommendation workflow")
    supplier_candidates = (
        df.groupby("supplier_id")
        .agg(
            total_cost=("purchase_cost", "sum"),
            avg_unit_cost=("unit_cost", "mean"),
            avg_lead_time=("lead_time_days", "mean"),
        )
        .sort_values(["avg_unit_cost", "avg_lead_time"], ascending=[False, False])
        .reset_index()
    )
    selected_idx = st.selectbox(
        "Focus supplier",
        options=supplier_candidates.index,
        format_func=lambda idx: f"{supplier_candidates.loc[idx, 'supplier_id']} (avg unit cost ₦{supplier_candidates.loc[idx, 'avg_unit_cost']:.0f})",
        key="procurement_recommendation_candidate",
    )
    selected = supplier_candidates.loc[selected_idx]
    suggested_target = max(float(selected["avg_unit_cost"]) * 0.94, 0.0)
    st.caption(
        f"Suggested action: negotiate {selected['supplier_id']} toward ₦{suggested_target:,.0f} average unit cost and tighten lead time commitments."
    )
    if st.button("Log procurement recommendation", key="log_procurement_recommendation"):
        event = log_fmcg_recommendation(
            principal=principal,
            model_id="procurement-hub",
            model_version="m2",
            input_snapshot_ref="dashboard://procurement-hub",
            recommendation_type="supplier_negotiation",
            recommendation_payload={
                "supplier_id": selected["supplier_id"],
                "current_avg_unit_cost": round(float(selected["avg_unit_cost"]), 2),
                "current_avg_lead_time": round(float(selected["avg_lead_time"]), 2),
                "suggested_target_unit_cost": round(suggested_target, 2),
            },
            confidence_score=0.79,
        )
        st.success(f"Recommendation logged: {event.event_id}")

history = recommendation_history_df("supplier_negotiation")
if not history.empty:
    st.markdown("##### Procurement recommendation history")
    st.dataframe(
        history[["event_id", "action_taken", "approver_id", "confidence_score", "recommendation_payload"]],
        width="stretch",
        hide_index=True,
        height=220,
    )
    if fmcg_user_has_permission(principal, Permission.APPROVE_RECOMMENDATION):
        pending = history[history["action_taken"] == ActionTaken.PENDING.value]
        if not pending.empty:
            pending_ids = pending["event_id"].tolist()
            selected_event_id = st.selectbox(
                "Pending procurement recommendation",
                options=pending_ids,
                key="procurement_pending_event",
            )
            approve_col, reject_col = st.columns(2)
            if approve_col.button("Approve", key="procurement_approve"):
                resolve_fmcg_recommendation(
                    principal=principal,
                    event_id=selected_event_id,
                    action=ActionTaken.APPROVED,
                )
                st.rerun()
            if reject_col.button("Reject", key="procurement_reject"):
                resolve_fmcg_recommendation(
                    principal=principal,
                    event_id=selected_event_id,
                    action=ActionTaken.REJECTED,
                )
                st.rerun()

st.divider()

# ---------------------------------------------------------------------------
# Spend by supplier (top 15) + category breakdown
# ---------------------------------------------------------------------------

left, right = st.columns([1.2, 0.8], gap="large")
with left:
    st.markdown("##### Top 15 suppliers by spend")
    sup_spend = df.groupby("supplier_id")["purchase_cost"].sum().nlargest(15).reset_index()
    fig_sup = px.bar(
        sup_spend,
        x="purchase_cost",
        y="supplier_id",
        orientation="h",
        color_discrete_sequence=PALETTE,
    )
    fig_sup.update_layout(yaxis_title="", xaxis_title="₦ Purchase cost")
    render_chart(fig_sup, height=380)

with right:
    st.markdown("##### Spend by category")
    cat_spend = df.groupby("category")["purchase_cost"].sum().reset_index()
    fig_cat = px.pie(
        cat_spend,
        values="purchase_cost",
        names="category",
        color_discrete_sequence=PALETTE,
        hole=0.45,
    )
    render_chart(fig_cat, height=380)

st.divider()

# ---------------------------------------------------------------------------
# Lead-time distribution & OTD by supplier
# ---------------------------------------------------------------------------

st.markdown("##### Supplier lead-time reliability")
sup_lead = (
    df.groupby("supplier_id")
    .agg(
        avg_lead=("lead_time_days", "mean"),
        otd_pct=("on_time", "mean"),
        total_cost=("purchase_cost", "sum"),
    )
    .reset_index()
)
sup_lead["otd_pct"] = (sup_lead["otd_pct"] * 100).round(1)

c1, c2 = st.columns(2, gap="large")
with c1:
    scatter = px.scatter(
        sup_lead,
        x="avg_lead",
        y="otd_pct",
        size="total_cost",
        hover_name="supplier_id",
        color_discrete_sequence=PALETTE,
    )
    scatter.update_layout(xaxis_title="Avg lead time (days)", yaxis_title="On-time %")
    render_chart(scatter, height=320)

with c2:
    hist = px.histogram(
        df,
        x="lead_time_days",
        nbins=20,
        color_discrete_sequence=PALETTE,
    )
    hist.update_layout(xaxis_title="Lead time (days)", yaxis_title="# orders")
    render_chart(hist, height=320)

st.divider()

# ---------------------------------------------------------------------------
# Cost trend (weekly)
# ---------------------------------------------------------------------------

st.markdown("##### Weekly purchase-cost trend")
weekly = df.groupby([pd.Grouper(key="date", freq="W"), "category"])["purchase_cost"].sum().reset_index()
trend_fig = px.area(
    weekly,
    x="date",
    y="purchase_cost",
    color="category",
    color_discrete_sequence=PALETTE,
)
trend_fig.update_layout(xaxis_title="", yaxis_title="₦ Purchase cost")
render_chart(trend_fig, height=340)
