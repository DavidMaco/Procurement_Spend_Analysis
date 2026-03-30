"""06 — FMCG Commercial Command Centre.

Revenue-growth dashboard for the commercial team.  Shows promo ROI,
gross-to-net leakage, net-sales trend, and variance alerts for the
commercial KPI domain.
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
    format_currency_abbr,
    log_fmcg_recommendation,
    page_header,
    recommendation_history_df,
    render_chart,
    resolve_fmcg_recommendation,
    require_fmcg_dashboard_access,
)
from procurement_spend_analysis.fmcg.access_control import Permission
from procurement_spend_analysis.fmcg.event_log import ActionTaken
from procurement_spend_analysis.fmcg.pilot import evaluate_pilot_impact


configure_page("Commercial Command Centre", icon="💹")
principal = require_fmcg_dashboard_access(
    Permission.VIEW_COMMERCIAL_DASHBOARD,
    key_prefix="fmcg_commercial",
)

page_header(
    "FMCG Commercial Command Centre",
    "Revenue growth, promo effectiveness, and gross-to-net leakage — powered by the FMCG OS.",
)

# ---------------------------------------------------------------------------
# Session-state initialisation — demo data
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def _demo_sales() -> pd.DataFrame:
    """Generate a small synthetic FMCG sales slice for the dashboard demo."""
    rng = np.random.default_rng(42)
    n = 600
    dates = pd.date_range("2024-01-01", periods=180, freq="D")
    categories = ["Beverages", "Snacks", "Personal Care", "Dairy", "Bakery"]
    stores = [f"S{i:03d}" for i in range(1, 16)]
    rows: list[dict] = []
    for _ in range(n):
        cat = rng.choice(categories)
        list_price = rng.uniform(200, 5000)
        disc_pct = rng.uniform(0, 0.35)
        units = int(rng.integers(1, 200))
        purchase_cost = list_price * rng.uniform(0.4, 0.75)
        rows.append(
            {
                "date": rng.choice(dates),
                "store_id": rng.choice(stores),
                "category": cat,
                "list_price": round(list_price, 2),
                "discount_pct": round(disc_pct, 4),
                "units_sold": units,
                "net_sales": round(list_price * (1 - disc_pct) * units, 2),
                "gross_sales": round(list_price * units, 2),
                "purchase_cost": round(purchase_cost * units, 2),
                "is_promo": bool(rng.random() < 0.3),
            }
        )
    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"])
    return df


@st.cache_data(show_spinner=False)
def _demo_pilot_sales() -> pd.DataFrame:
    """Return a canonical pilot dataset with a clear commercial intervention uplift."""
    rows: list[dict[str, object]] = []
    dates = pd.date_range("2024-03-25", periods=8, freq="D")
    stores = ["STORE001", "STORE002", "STORE003", "STORE004"]
    for date_value in dates:
        for store in stores:
            is_treatment = store in {"STORE003", "STORE004"}
            post_period = date_value >= pd.Timestamp("2024-03-29")
            discount_pct = 0.18
            purchase_cost = 62.0
            units_sold = 36
            if is_treatment and post_period:
                discount_pct = 0.12
                purchase_cost = 58.0
                units_sold = 43

            gross_sales = float(units_sold * 120.0)
            net_sales = gross_sales * (1 - discount_pct)
            purchase_cost_total = purchase_cost * units_sold
            margin_pct = (net_sales - purchase_cost_total) / net_sales if net_sales else 0.0
            rows.append(
                {
                    "date": date_value.strftime("%Y-%m-%d"),
                    "year": date_value.year,
                    "month": date_value.month,
                    "day": date_value.day,
                    "weekofyear": int(date_value.isocalendar().week),
                    "weekday": date_value.weekday(),
                    "is_weekend": int(date_value.weekday() >= 5),
                    "is_holiday": 0,
                    "temperature": 27.0,
                    "rain_mm": 0.0,
                    "store_id": store,
                    "country": "Nigeria",
                    "city": "Lagos",
                    "channel": "Hypermarket",
                    "latitude": 6.5244,
                    "longitude": 3.3792,
                    "sku_id": "SKU-PER-001",
                    "sku_name": "Premium Body Wash",
                    "category": "Personal Care",
                    "subcategory": "Body Wash",
                    "brand": "Northstar",
                    "units_sold": units_sold,
                    "list_price": 120.0,
                    "discount_pct": discount_pct,
                    "promo_flag": 1,
                    "gross_sales": gross_sales,
                    "net_sales": net_sales,
                    "stock_on_hand": 200,
                    "stock_out_flag": 0,
                    "lead_time_days": 4,
                    "supplier_id": "SUP-001",
                    "purchase_cost": purchase_cost,
                    "margin_pct": round(margin_pct, 3),
                }
            )
    return pd.DataFrame(rows)


df = _demo_sales()

# ---------------------------------------------------------------------------
# KPI strip
# ---------------------------------------------------------------------------

total_gross = df["gross_sales"].sum()
total_net = df["net_sales"].sum()
leakage_pct = (1 - total_net / total_gross) * 100 if total_gross else 0
promo_rows = df[df["is_promo"]]
promo_roi = (
    (promo_rows["net_sales"].sum() - promo_rows["purchase_cost"].sum())
    / promo_rows["purchase_cost"].sum()
    * 100
    if promo_rows["purchase_cost"].sum() > 0
    else 0
)

cols = st.columns(4, gap="small")
cols[0].metric("Gross sales", f"₦{total_gross:,.0f}")
cols[1].metric("Net sales", f"₦{total_net:,.0f}")
cols[2].metric("Gross-to-net leakage", f"{leakage_pct:.1f}%")
cols[3].metric("Promo ROI", f"{promo_roi:.1f}%")

st.divider()

# ---------------------------------------------------------------------------
# Net-sales trend by category
# ---------------------------------------------------------------------------

left, right = st.columns([1.4, 0.6], gap="large")
with left:
    st.markdown("##### Net-sales trend (daily)")
    trend = df.groupby([pd.Grouper(key="date", freq="W"), "category"])["net_sales"].sum().reset_index()
    fig_trend = px.area(
        trend,
        x="date",
        y="net_sales",
        color="category",
        color_discrete_sequence=PALETTE,
    )
    fig_trend.update_layout(xaxis_title="", yaxis_title="₦ Net sales")
    render_chart(fig_trend, height=340)

with right:
    st.markdown("##### Category mix")
    cat_mix = df.groupby("category")["net_sales"].sum().reset_index()
    fig_pie = px.pie(
        cat_mix,
        values="net_sales",
        names="category",
        color_discrete_sequence=PALETTE,
        hole=0.45,
    )
    render_chart(fig_pie, height=340)

st.divider()

# ---------------------------------------------------------------------------
# Discount depth & leakage by category
# ---------------------------------------------------------------------------

st.markdown("##### Discount depth & leakage by category")
cat_leakage = (
    df.groupby("category")
    .agg(gross=("gross_sales", "sum"), net=("net_sales", "sum"), avg_disc=("discount_pct", "mean"))
    .reset_index()
)
cat_leakage["leakage_pct"] = (1 - cat_leakage["net"] / cat_leakage["gross"]) * 100

baseline_df = df.copy()
baseline_df["discount_pct"] = (baseline_df["discount_pct"] * 0.7).clip(0, 1)
baseline_df["net_sales"] = baseline_df["gross_sales"] * (1 - baseline_df["discount_pct"])
commercial_alerts = evaluate_fmcg_alerts(
    baseline_df,
    df,
    category="commercial",
)

c1, c2 = st.columns(2, gap="large")
with c1:
    bar_fig = px.bar(
        cat_leakage,
        x="category",
        y="leakage_pct",
        text="leakage_pct",
        color="category",
        color_discrete_sequence=PALETTE,
    )
    bar_fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    bar_fig.update_layout(showlegend=False, yaxis_title="Leakage %", xaxis_title="")
    render_chart(bar_fig, height=300)

with c2:
    disc_fig = px.bar(
        cat_leakage,
        x="category",
        y="avg_disc",
        text="avg_disc",
        color="category",
        color_discrete_sequence=PALETTE,
    )
    disc_fig.update_traces(texttemplate="%{text:.1%}", textposition="outside")
    disc_fig.update_layout(showlegend=False, yaxis_title="Avg discount %", xaxis_title="")
    render_chart(disc_fig, height=300)

st.divider()

# ---------------------------------------------------------------------------
# Alerting and recommendations
# ---------------------------------------------------------------------------

left_panel, right_panel = st.columns([0.9, 1.1], gap="large")
with left_panel:
    st.markdown("##### Commercial alerts")
    if commercial_alerts.empty:
        st.info("No commercial alerts are firing against the current baseline.")
    else:
        st.metric("Active alerts", f"{len(commercial_alerts)}")
        st.dataframe(
            commercial_alerts[["rule_name", "severity", "metric_column", "variance_pct", "message"]],
            use_container_width=True,
            hide_index=True,
            height=260,
        )

with right_panel:
    st.markdown("##### Recommendation workflow")
    recommendation_candidates = cat_leakage.sort_values("leakage_pct", ascending=False).reset_index(drop=True)
    selected_idx = st.selectbox(
        "Focus category",
        options=recommendation_candidates.index,
        format_func=lambda idx: f"{recommendation_candidates.loc[idx, 'category']} ({recommendation_candidates.loc[idx, 'leakage_pct']:.1f}% leakage)",
        key="commercial_recommendation_candidate",
    )
    selected = recommendation_candidates.loc[selected_idx]
    suggested_discount = max(float(selected["avg_disc"]) - 0.03, 0.0)
    st.caption(
        f"Suggested action: reduce average discount in {selected['category']} to {suggested_discount:.1%} and re-test promo elasticity."
    )
    if st.button("Log commercial recommendation", key="log_commercial_recommendation"):
        event = log_fmcg_recommendation(
            principal=principal,
            model_id="commercial-command-centre",
            model_version="m2",
            input_snapshot_ref="dashboard://commercial-command-centre",
            recommendation_type="promo_depth",
            recommendation_payload={
                "category": selected["category"],
                "current_leakage_pct": round(float(selected["leakage_pct"]), 2),
                "current_discount_pct": round(float(selected["avg_disc"]), 4),
                "suggested_discount_pct": round(suggested_discount, 4),
            },
            confidence_score=0.82,
        )
        st.success(f"Recommendation logged: {event.event_id}")

history = recommendation_history_df("promo_depth")
if not history.empty:
    st.markdown("##### Commercial recommendation history")
    st.dataframe(
        history[["event_id", "action_taken", "approver_id", "confidence_score", "recommendation_payload"]],
        use_container_width=True,
        hide_index=True,
        height=220,
    )
    if fmcg_user_has_permission(principal, Permission.APPROVE_RECOMMENDATION):
        pending = history[history["action_taken"] == ActionTaken.PENDING.value]
        if not pending.empty:
            pending_ids = pending["event_id"].tolist()
            selected_event_id = st.selectbox(
                "Pending commercial recommendation",
                options=pending_ids,
                key="commercial_pending_event",
            )
            approve_col, reject_col = st.columns(2)
            if approve_col.button("Approve", key="commercial_approve"):
                resolve_fmcg_recommendation(
                    principal=principal,
                    event_id=selected_event_id,
                    action=ActionTaken.APPROVED,
                )
                st.rerun()
            if reject_col.button("Reject", key="commercial_reject"):
                resolve_fmcg_recommendation(
                    principal=principal,
                    event_id=selected_event_id,
                    action=ActionTaken.REJECTED,
                )
                st.rerun()

st.divider()

# ---------------------------------------------------------------------------
# Pilot impact scorecard
# ---------------------------------------------------------------------------

st.markdown("##### Pilot impact scorecard")
pilot_report = evaluate_pilot_impact(
    _demo_pilot_sales(),
    intervention_date="2024-03-29",
)
pilot_impacts = pd.DataFrame(
    [impact.model_dump() for impact in pilot_report.metric_impacts]
)
pilot_summary = {summary.metric: summary for summary in pilot_report.metric_impacts}
pilot_cols = st.columns(4, gap="small")
pilot_cols[0].metric(
    "Incremental net sales / store-day",
    f"₦{pilot_report.primary_incremental_lift:,.0f}",
    None
    if pilot_report.primary_incremental_lift_pct is None
    else f"{pilot_report.primary_incremental_lift_pct:.1f}% vs treatment pre",
)
pilot_cols[1].metric(
    "Margin lift / store-day",
    f"₦{pilot_summary['contribution_margin_per_store_day'].incremental_lift:,.0f}",
)
pilot_cols[2].metric(
    "Purchase-cost movement / unit",
    f"₦{pilot_summary['purchase_cost_per_unit'].incremental_lift:,.2f}",
)
pilot_cols[3].metric(
    "Leakage movement",
    f"{pilot_summary['gross_to_net_leakage_pct'].incremental_lift:.1f} pts",
)

pilot_chart = px.bar(
    pilot_impacts,
    x="metric",
    y="incremental_lift",
    color="favorable_movement",
    color_discrete_map={True: PALETTE[0], False: PALETTE[3]},
    text="incremental_lift",
)
pilot_chart.update_traces(texttemplate="%{text:.2f}", textposition="outside")
pilot_chart.update_layout(
    showlegend=False,
    xaxis_title="",
    yaxis_title="Incremental lift",
)

pilot_left, pilot_right = st.columns([1.15, 0.85], gap="large")
with pilot_left:
    render_chart(pilot_chart, height=320)

with pilot_right:
    st.caption(
        "Difference-in-differences readout for a promo-depth intervention. Positive values are good for revenue and margin metrics; negative values are good for leakage and purchase cost."
    )
    st.dataframe(
        pilot_impacts[
            [
                "metric",
                "control_change",
                "treatment_change",
                "incremental_lift",
                "favorable_movement",
            ]
        ],
        use_container_width=True,
        hide_index=True,
        height=260,
    )
    st.caption(
        f"Treatment stores: {', '.join(pilot_report.cohort.treatment_stores)}. Control stores: {', '.join(pilot_report.cohort.control_stores)}."
    )
    post_net_sales = next(
        summary.net_sales
        for summary in pilot_report.arm_summaries
        if summary.arm == "treatment" and summary.period == "post"
    )
    st.caption(
        f"Post-period treatment net sales: {format_currency_abbr(post_net_sales)} across {pilot_report.post_period[0]} to {pilot_report.post_period[1]}."
    )

st.divider()

# ---------------------------------------------------------------------------
# Top stores by net sales
# ---------------------------------------------------------------------------

st.markdown("##### Top stores by net sales")
store_sales = df.groupby("store_id")["net_sales"].sum().nlargest(15).reset_index()
store_fig = px.bar(
    store_sales,
    x="net_sales",
    y="store_id",
    orientation="h",
    color_discrete_sequence=PALETTE,
)
store_fig.update_layout(yaxis_title="", xaxis_title="₦ Net sales")
render_chart(store_fig, height=360)
