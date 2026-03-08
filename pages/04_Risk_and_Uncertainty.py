from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from dashboard_ui import PALETTE, build_filtered_context, configure_page, ensure_dashboard_bundle, format_currency, metric_strip


configure_page("Risk and Uncertainty")

bundle = ensure_dashboard_bundle()
context = build_filtered_context(bundle)
insights = context["insights"]

st.title("Risk and Uncertainty")
st.caption("Maverick spend, supplier-risk exposure, FX sensitivity, and Monte Carlo savings envelope.")
metric_strip(context)

left, right = st.columns([1.1, 0.9])
with left:
    st.subheader("Maverick and supplier-risk exposure")
    risk_breakdown = (
        context["filtered_maverick"].groupby("risk_level", as_index=False)["total_amount_ngn"].sum().sort_values("total_amount_ngn")
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
    risk_fig.update_layout(xaxis_title="Spend (NGN)", yaxis_title="Risk level")
    st.plotly_chart(risk_fig, use_container_width=True)
with right:
    st.subheader("Risk KPI cards")
    st.metric("USD exposure", format_currency(float(insights.get("usd_spend", 0.0)), "USD"))
    st.metric("FX volatility", f"{float(insights.get('fx_volatility', 0.0)):.2f}%")
    st.metric("Monte Carlo P05", format_currency(float(insights.get("total_savings_p05_ngn", 0.0))))
    st.metric("Monte Carlo median", format_currency(float(insights.get("total_savings_median_ngn", 0.0))))
    st.metric("Monte Carlo P95", format_currency(float(insights.get("total_savings_p95_ngn", 0.0))))

st.subheader("Monte Carlo bounds")
st.dataframe(context["analytics"]["monte_carlo_uncertainty_bounds"], use_container_width=True, hide_index=True)
