"""
Procurement Spend Intelligence Dashboard — single-page tabbed view.

Uses the shared dashboard_ui helpers for data loading, filtering, and
metrics so that filtering logic lives in exactly one place.
"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from dashboard_data import export_powerbi_pack, upload_schema_reference
from dashboard_ui import (
    PALETTE,
    build_filtered_context,
    configure_page,
    ensure_dashboard_bundle,
    format_currency,
    metric_strip,
    powerbi_pack_download,
)


configure_page("Procurement Spend Intelligence")

st.title("Procurement Spend Intelligence Dashboard")
st.caption(
    "Streamlit Cloud-ready procurement dashboard with realistic demo generation, "
    "company-data uploads, and one-click Power BI export pack generation."
)

with st.expander("Open dedicated pages", expanded=True):
    nav_col1, nav_col2, nav_col3 = st.columns(3)
    nav_col1.page_link("pages/01_Executive_Overview.py", label="Executive Overview")
    nav_col1.page_link("pages/02_Supplier_Performance.py", label="Supplier Performance")
    nav_col2.page_link("pages/03_Savings_Opportunities.py", label="Savings Opportunities")
    nav_col2.page_link("pages/04_Risk_and_Uncertainty.py", label="Risk & Uncertainty")
    nav_col3.page_link("pages/05_Data_Hub.py", label="Data Hub")

# ── shared sidebar: data source + filters ──────────────────────────────
bundle = ensure_dashboard_bundle()
context = build_filtered_context(bundle)

analytics = context["analytics"]
insights = context["insights"]
metadata = context["metadata"]
raw = context["raw"]

# ── top-level metric strip ──────────────────────────────────────────────
metric_strip(context)

# ── tabbed content ──────────────────────────────────────────────────────
summary_tab, supplier_tab, savings_tab, risk_tab, hub_tab = st.tabs(
    ["Executive overview", "Supplier performance", "Savings", "Risk & uncertainty", "Data hub"]
)

with summary_tab:
    left, right = st.columns([1.2, 1.0])
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
        st.subheader("KPI snapshot")
        summary_df = analytics["procurement_insights_summary"].copy()
        summary_df["formatted_value"] = summary_df.apply(
            lambda row: format_currency(row["value"], row["unit"])
            if row["unit"] in {"NGN", "USD"}
            else f"{row['value']:.2f}%",
            axis=1,
        )
        st.dataframe(summary_df[["metric", "formatted_value"]], use_container_width=True, hide_index=True)

    st.subheader("Monthly trend")
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
    scenario_fig = px.bar(
        analytics["savings_scenarios"],
        x="scenario",
        y="total_savings_ngn",
        text="savings_pct_of_spend",
        color="scenario",
        color_discrete_sequence=PALETTE,
    )
    scenario_fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    st.plotly_chart(scenario_fig, use_container_width=True)

with supplier_tab:
    top_left, top_right = st.columns([1.05, 0.95])
    with top_left:
        st.subheader("Supplier scorecard")
        st.dataframe(
            context["filtered_suppliers"].sort_values("total_spend_ngn", ascending=False),
            use_container_width=True,
            hide_index=True,
        )
    with top_right:
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

    st.subheader("Supplier mix by performance grade")
    grade_fig = px.histogram(
        context["filtered_suppliers"],
        x="performance_grade",
        color="category",
        barmode="group",
        color_discrete_sequence=PALETTE,
    )
    st.plotly_chart(grade_fig, use_container_width=True)

with savings_tab:
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

with risk_tab:
    left, right = st.columns([1.1, 0.9])
    with left:
        st.subheader("Maverick and supplier-risk exposure")
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
        risk_fig.update_layout(xaxis_title="Spend (NGN)", yaxis_title="Risk level")
        st.plotly_chart(risk_fig, use_container_width=True)
    with right:
        st.subheader("FX and uncertainty envelope")
        st.metric("USD exposure", format_currency(float(insights.get("usd_spend", 0.0)), "USD"))
        st.metric("FX volatility", f"{float(insights.get('fx_volatility', 0.0)):.2f}%")
        st.metric("Monte Carlo P05", format_currency(float(insights.get("total_savings_p05_ngn", 0.0))))
        st.metric("Monte Carlo P95", format_currency(float(insights.get("total_savings_p95_ngn", 0.0))))

    st.subheader("Monte Carlo bounds")
    st.dataframe(analytics["monte_carlo_uncertainty_bounds"], use_container_width=True, hide_index=True)

with hub_tab:
    st.subheader("Upload-readiness and export hub")
    hub_left, hub_right = st.columns([1.0, 1.0])
    with hub_left:
        st.markdown("**Data quality report**")
        st.json(metadata.get("quality_report", {}))
        if metadata.get("rename_maps"):
            with st.expander("Detected column mappings"):
                st.json(metadata["rename_maps"])
    with hub_right:
        st.markdown("**Expected upload schemas**")
        schema_df = upload_schema_reference()
        st.dataframe(schema_df, use_container_width=True, hide_index=True)

    powerbi_pack_download(bundle)

    st.download_button(
        "Download schema reference CSV",
        data=schema_df.to_csv(index=False),
        file_name="upload_schema_reference.csv",
        mime="text/csv",
        use_container_width=True,
    )

    with st.expander("Preview normalized raw tables"):
        selected_table = st.selectbox("Table", list(raw.keys()))
        st.dataframe(raw[selected_table].head(200), use_container_width=True, hide_index=True)

st.markdown("---")
st.caption(
    "Deploy on Streamlit Cloud with `streamlit_app.py` as the entry point. "
    "Use the Power BI deployment pack to seed a PBIX model or scheduled Fabric refresh pipeline."
)
