from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from dashboard_ui import (
    PALETTE,
    build_filtered_context,
    configure_page,
    ensure_dashboard_bundle,
    format_currency,
    metric_strip,
    page_header,
    render_chart,
)


configure_page("Risk and Uncertainty")

bundle = ensure_dashboard_bundle()
context = build_filtered_context(bundle)
insights = context["insights"]

page_header(
    "Risk and Uncertainty",
    "Maverick spend, supplier-risk exposure, FX sensitivity, and Monte Carlo savings envelope.",
)
metric_strip(context)
st.divider()

# ── maverick chart + risk KPI cards ─────────────────────────────────────
left, right = st.columns([0.6, 0.4], gap="large")
with left:
    st.markdown("##### Maverick and supplier-risk exposure")
    risk_breakdown = (
        context["filtered_maverick"]
        .groupby("risk_level", as_index=False)["total_amount_ngn"]
        .sum()
        .sort_values("total_amount_ngn")
        if not context["filtered_maverick"].empty
        else pd.DataFrame({"risk_level": [], "total_amount_ngn": []})
    )
    risk_fig = px.bar(
        risk_breakdown,
        x="total_amount_ngn",
        y="risk_level",
        orientation="h",
        color="risk_level",
        color_discrete_sequence=PALETTE,
    )
    risk_fig.update_layout(xaxis_title="Spend (NGN)", yaxis_title="Risk level", showlegend=False)
    render_chart(risk_fig, height=300)

with right:
    st.markdown("##### Risk & FX KPIs")
    r1, r2 = st.columns(2)
    r1.metric("USD exposure",   format_currency(float(insights.get("usd_spend", 0.0)), "USD"))
    r2.metric("FX volatility",  f"{float(insights.get('fx_volatility', 0.0)):.2f}%")
    st.metric("Monte Carlo P05",    format_currency(float(insights.get("total_savings_p05_ngn", 0.0))))
    st.metric("Monte Carlo median", format_currency(float(insights.get("total_savings_median_ngn", 0.0))))
    st.metric("Monte Carlo P95",    format_currency(float(insights.get("total_savings_p95_ngn", 0.0))))

st.divider()

# ── Monte Carlo bounds table ──────────────────────────────────────────────
st.markdown("##### Monte Carlo savings bounds")
st.dataframe(
    context["analytics"]["monte_carlo_uncertainty_bounds"],
    use_container_width=True,
    hide_index=True,
)
