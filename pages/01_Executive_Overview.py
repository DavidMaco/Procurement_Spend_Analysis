from __future__ import annotations

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
    powerbi_pack_download,
    render_chart,
)


configure_page("Executive Overview")

bundle = ensure_dashboard_bundle()
context = build_filtered_context(bundle)
analytics = context["analytics"]
insights = context["insights"]

page_header(
    "Executive Overview",
    "High-level spend, savings potential, and scenario trends for procurement leadership.",
)
metric_strip(context)
st.divider()

# ── spend by category + KPI table ────────────────────────────────────────
left, right = st.columns([1.4, 0.6], gap="large")
with left:
    st.markdown("##### Spend by category")
    fig = px.bar(
        context["filtered_category_spend"],
        x="category",
        y="total_spend_ngn",
        text="pct_of_total",
        color="category",
        color_discrete_sequence=PALETTE,
    )
    fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig.update_layout(showlegend=False, yaxis_title="Spend (NGN)", xaxis_title="")
    render_chart(fig, height=340)

with right:
    st.markdown("##### Core KPIs")
    summary_df = analytics["procurement_insights_summary"].copy()
    summary_df["Value"] = summary_df.apply(
        lambda row: format_currency(row["value"], row["unit"])
        if row["unit"] in {"NGN", "USD"}
        else f"{row['value']:.2f}%",
        axis=1,
    )
    st.dataframe(
        summary_df[["metric", "Value"]],
        use_container_width=True,
        hide_index=True,
        height=340,
    )

st.divider()

# ── monthly trend ─────────────────────────────────────────────────────────
st.markdown("##### Monthly spend trend")
trend_fig = px.line(
    context["filtered_monthly"],
    x="month",
    y="total_spend_ngn",
    color="category",
    markers=True,
    color_discrete_sequence=PALETTE,
)
trend_fig.update_layout(yaxis_title="Spend (NGN)", xaxis_title="")
render_chart(trend_fig, height=300)

st.divider()

# ── scenario outlook ──────────────────────────────────────────────────────
st.markdown("##### Scenario savings outlook")
scenario_fig = px.bar(
    analytics["savings_scenarios"],
    x="scenario",
    y="total_savings_ngn",
    text="savings_pct_of_spend",
    color="scenario",
    color_discrete_sequence=PALETTE,
)
scenario_fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
scenario_fig.update_layout(showlegend=False, yaxis_title="Savings (NGN)", xaxis_title="")
render_chart(scenario_fig, height=280)

m1, m2 = st.columns(2)
m1.metric("Total savings potential", format_currency(float(insights.get("total_savings", 0.0))))
m2.metric("Savings percentage", f"{float(insights.get('savings_percentage', 0.0)):.2f}%")

st.divider()
powerbi_pack_download(bundle)
