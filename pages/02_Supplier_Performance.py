from __future__ import annotations

import plotly.express as px
import streamlit as st

from dashboard_ui import (
    PALETTE,
    apply_chart_theme,
    build_filtered_context,
    configure_page,
    ensure_dashboard_bundle,
    metric_strip,
    page_header,
)


configure_page("Supplier Performance")

bundle = ensure_dashboard_bundle()
context = build_filtered_context(bundle)

page_header(
    "Supplier Performance",
    "Operational performance, quality cost, and grade distribution across your supply base.",
)
metric_strip(context)
st.divider()

# ── scorecard + OTD scatter ───────────────────────────────────────────────
left, right = st.columns([1.1, 0.9], gap="large")
with left:
    st.markdown("##### Supplier scorecard")
    st.dataframe(
        context["filtered_suppliers"].sort_values("total_spend_ngn", ascending=False),
        use_container_width=True,
        hide_index=True,
        height=360,
    )
with right:
    st.markdown("##### OTD vs quality cost")
    scatter = px.scatter(
        context["filtered_suppliers"],
        x="on_time_delivery_pct",
        y="total_quality_cost",
        size="total_spend_ngn",
        color="performance_grade",
        hover_name="supplier_name",
        color_discrete_sequence=PALETTE,
    )
    scatter.update_layout(xaxis_title="On-time delivery %", yaxis_title="Quality cost (NGN)")
    apply_chart_theme(scatter, height=360)
    st.plotly_chart(scatter, use_container_width=True)

st.divider()

# ── grade mix + top suppliers by spend ───────────────────────────────────
bottom_left, bottom_right = st.columns(2, gap="large")
with bottom_left:
    st.markdown("##### Performance-grade distribution")
    grade_fig = px.histogram(
        context["filtered_suppliers"],
        x="performance_grade",
        color="category",
        barmode="group",
        color_discrete_sequence=PALETTE,
    )
    grade_fig.update_layout(xaxis_title="Grade", yaxis_title="Supplier count")
    apply_chart_theme(grade_fig, height=300)
    st.plotly_chart(grade_fig, use_container_width=True)

with bottom_right:
    st.markdown("##### Top 15 suppliers by spend")
    top_spend = context["filtered_suppliers"].nlargest(15, "total_spend_ngn")
    bar_fig = px.bar(
        top_spend,
        x="total_spend_ngn",
        y="supplier_name",
        orientation="h",
        color="category",
        color_discrete_sequence=PALETTE,
    )
    bar_fig.update_layout(yaxis_title="", xaxis_title="Spend (NGN)")
    apply_chart_theme(bar_fig, height=300)
    st.plotly_chart(bar_fig, use_container_width=True)
