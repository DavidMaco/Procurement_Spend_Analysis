"""
Procurement Spend Intelligence — executive landing page.

Clean single-page overview with KPIs, spend-by-category, and monthly
trend.  Use the sidebar navigation links to open the five dedicated
detail pages (supplier performance, savings, risk, data hub).
"""

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
    render_chart,
)


configure_page("Procurement Spend Intelligence")

page_header(
    "Procurement Spend Intelligence",
    "Real-time visibility across supplier performance, savings opportunities, and procurement risk.",
)

# ── data + sidebar filters ────────────────────────────────────────────────
bundle = ensure_dashboard_bundle()
context = build_filtered_context(bundle)
analytics = context["analytics"]
insights = context["insights"]

# ── KPI strip ─────────────────────────────────────────────────────────────
metric_strip(context)

# ── page navigation ───────────────────────────────────────────────────────
st.divider()
nc1, nc2, nc3, nc4, nc5 = st.columns(5, gap="small")
nc1.page_link("pages/01_Executive_Overview.py",    label="📊 Executive")
nc2.page_link("pages/02_Supplier_Performance.py",  label="🏭 Suppliers")
nc3.page_link("pages/03_Savings_Opportunities.py", label="💰 Savings")
nc4.page_link("pages/04_Risk_and_Uncertainty.py",  label="⚠️ Risk")
nc5.page_link("pages/05_Data_Hub.py",              label="📂 Data Hub")

st.divider()

# ── spend by category + KPI summary ──────────────────────────────────────
left, right = st.columns([1.2, 0.8], gap="large")
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
    st.markdown("##### KPI summary")
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

# ── monthly spend trend ───────────────────────────────────────────────────
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
st.caption(
    "Streamlit Cloud · source selector in the sidebar · "
    "Power BI deployment pack available on the **Data Hub** page."
)
