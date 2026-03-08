from __future__ import annotations

import plotly.express as px
import streamlit as st

from dashboard_ui import PALETTE, build_filtered_context, configure_page, ensure_dashboard_bundle, metric_strip


configure_page("Savings Opportunities")

bundle = ensure_dashboard_bundle()
context = build_filtered_context(bundle)

st.title("Savings Opportunities")
st.caption("Price standardization, optimized sourcing, and constrained allocation opportunities.")
metric_strip(context)

left, right = st.columns(2)
with left:
    st.subheader("Top price-variance opportunities")
    variance_fig = px.bar(
        context["filtered_price_variance"].head(15),
        x="potential_savings_ngn",
        y="material_name",
        orientation="h",
        color="category",
        color_discrete_sequence=PALETTE,
    )
    variance_fig.update_layout(yaxis_title="", xaxis_title="Potential savings (NGN)")
    st.plotly_chart(variance_fig, use_container_width=True)
with right:
    st.subheader("Optimization recommendations")
    st.dataframe(
        context["filtered_optimization"].sort_values(["category", "composite_score"], ascending=[True, False]),
        use_container_width=True,
        hide_index=True,
    )

st.subheader("Constrained sourcing plan")
st.dataframe(
    context["filtered_constrained"].sort_values(["category", "projected_spend_ngn"], ascending=[True, False]),
    use_container_width=True,
    hide_index=True,
)

st.subheader("Scenario savings table")
st.dataframe(context["analytics"]["savings_scenarios"], use_container_width=True, hide_index=True)
