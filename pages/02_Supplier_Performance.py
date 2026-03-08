from __future__ import annotations

import plotly.express as px
import streamlit as st

from dashboard_ui import PALETTE, build_filtered_context, configure_page, ensure_dashboard_bundle, metric_strip


configure_page("Supplier Performance")

bundle = ensure_dashboard_bundle()
context = build_filtered_context(bundle)

st.title("Supplier Performance")
st.caption("Operational performance, quality cost, and grade distribution across suppliers.")
metric_strip(context)

left, right = st.columns([1.05, 0.95])
with left:
    st.subheader("Supplier scorecard")
    st.dataframe(
        context["filtered_suppliers"].sort_values("total_spend_ngn", ascending=False),
        use_container_width=True,
        hide_index=True,
    )
with right:
    st.subheader("OTD vs quality cost")
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
    st.plotly_chart(scatter, use_container_width=True)

bottom_left, bottom_right = st.columns(2)
with bottom_left:
    st.subheader("Performance-grade mix")
    grade_fig = px.histogram(
        context["filtered_suppliers"],
        x="performance_grade",
        color="category",
        barmode="group",
        color_discrete_sequence=PALETTE,
    )
    st.plotly_chart(grade_fig, use_container_width=True)
with bottom_right:
    st.subheader("Top suppliers by spend")
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
    st.plotly_chart(bar_fig, use_container_width=True)
