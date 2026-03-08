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


configure_page("Savings Opportunities")

bundle = ensure_dashboard_bundle()
context = build_filtered_context(bundle)

page_header(
    "Savings Opportunities",
    "Price standardization, optimized sourcing, and constrained supplier allocation.",
)
metric_strip(context)
st.divider()

# ── price variance chart + optimization table ─────────────────────────────
left, right = st.columns([0.55, 0.45], gap="large")
with left:
    st.markdown("##### Top price-variance opportunities")
    variance_fig = px.bar(
        context["filtered_price_variance"].head(15),
        x="potential_savings_ngn",
        y="material_name",
        orientation="h",
        color="category",
        color_discrete_sequence=PALETTE,
    )
    variance_fig.update_layout(yaxis_title="", xaxis_title="Potential savings (NGN)")
    apply_chart_theme(variance_fig, height=400)
    st.plotly_chart(variance_fig, use_container_width=True)

with right:
    st.markdown("##### Optimization recommendations")
    st.dataframe(
        context["filtered_optimization"].sort_values(
            ["category", "composite_score"], ascending=[True, False]
        ),
        use_container_width=True,
        hide_index=True,
        height=400,
    )

st.divider()

# ── constrained plan + scenario summary ──────────────────────────────────
left2, right2 = st.columns([0.55, 0.45], gap="large")
with left2:
    st.markdown("##### Constrained sourcing plan")
    st.dataframe(
        context["filtered_constrained"].sort_values(
            ["category", "projected_spend_ngn"], ascending=[True, False]
        ),
        use_container_width=True,
        hide_index=True,
    )

with right2:
    st.markdown("##### Scenario savings summary")
    st.dataframe(
        context["analytics"]["savings_scenarios"],
        use_container_width=True,
        hide_index=True,
    )
