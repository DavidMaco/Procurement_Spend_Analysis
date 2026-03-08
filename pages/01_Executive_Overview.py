from __future__ import annotations

import plotly.express as px
import streamlit as st

from dashboard_ui import PALETTE, configure_page, ensure_dashboard_bundle, build_filtered_context, metric_strip, powerbi_pack_download, format_currency


configure_page("Executive Overview")

bundle = ensure_dashboard_bundle()
context = build_filtered_context(bundle)
analytics = context["analytics"]
insights = context["insights"]

st.title("Executive Overview")
st.caption("High-level spend, savings, and scenario trends for procurement leadership reviews.")
metric_strip(context)

left, right = st.columns([1.15, 0.85])
with left:
    st.subheader("Spend by category")
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
    st.plotly_chart(fig, use_container_width=True)
with right:
    st.subheader("Core KPI snapshot")
    summary_df = analytics["procurement_insights_summary"].copy()
    summary_df["formatted_value"] = summary_df.apply(
        lambda row: format_currency(row["value"], row["unit"]) if row["unit"] in {"NGN", "USD"} else f"{row['value']:.2f}%",
        axis=1,
    )
    st.dataframe(summary_df[["metric", "formatted_value"]], use_container_width=True, hide_index=True)

st.subheader("Monthly spend trend")
trend_fig = px.line(
    context["filtered_monthly"],
    x="month",
    y="total_spend_ngn",
    color="category",
    markers=True,
    color_discrete_sequence=PALETTE,
)
trend_fig.update_layout(yaxis_title="Spend (NGN)", xaxis_title="Month")
st.plotly_chart(trend_fig, use_container_width=True)

st.subheader("Scenario outlook")
scenario_df = analytics["savings_scenarios"].copy()
scenario_fig = px.bar(
    scenario_df,
    x="scenario",
    y="total_savings_ngn",
    text="savings_pct_of_spend",
    color="scenario",
    color_discrete_sequence=PALETTE,
)
scenario_fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
st.plotly_chart(scenario_fig, use_container_width=True)

col1, col2 = st.columns(2)
col1.metric("Total savings potential", format_currency(float(insights.get("total_savings", 0.0))))
col2.metric("Savings percentage", f"{float(insights.get('savings_percentage', 0.0)):.2f}%")

powerbi_pack_download(bundle)
