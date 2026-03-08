from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

from dashboard_data import (
    UploadValidationError,
    build_bundle_from_upload_bytes,
    export_powerbi_pack,
    export_upload_template_pack,
    generate_demo_bundle,
    load_demo_bundle,
    prepare_dashboard_context,
    upload_schema_reference,
)


PALETTE = ["#0F766E", "#2563EB", "#D97706", "#DC2626", "#7C3AED"]
DEFAULT_PAGE_ICON = "📦"


def configure_page(title: str, icon: str = DEFAULT_PAGE_ICON) -> None:
    st.set_page_config(
        page_title=title,
        page_icon=icon,
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(
        """
        <style>
        /* metric tiles */
        [data-testid="metric-container"] {
            background: var(--secondary-background-color);
            border: 1px solid #E2E8F0;
            border-radius: 10px;
            padding: 1rem 1.25rem 0.75rem;
        }
        /* thinner horizontal rules */
        hr { border: none; border-top: 1px solid #E2E8F0; margin: 0.25rem 0 1rem; }
        /* tighten default heading margins */
        h2 { margin-bottom: 0 !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def page_header(title: str, subtitle: str = "") -> None:
    """Render a consistent styled page title and optional subtitle, then a divider."""
    st.markdown(f"## {title}")
    if subtitle:
        st.markdown(
            f'<p style="color:#64748B;font-size:0.95rem;margin-top:-0.4rem">{subtitle}</p>',
            unsafe_allow_html=True,
        )
    st.divider()


def apply_chart_theme(fig, height: int = 380) -> None:
    """Apply a clean, minimal Plotly layout theme to *fig* in-place."""
    fig.update_layout(
        height=height,
        margin=dict(l=0, r=0, t=36, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", size=12, color="#0F172A"),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor="rgba(0,0,0,0)",
        ),
        hoverlabel=dict(bgcolor="#0F172A", font_color="#F8FAFC", bordercolor="#0F172A"),
    )
    fig.update_xaxes(gridcolor="#E2E8F0", gridwidth=1, zeroline=False, linecolor="#E2E8F0")
    fig.update_yaxes(gridcolor="#E2E8F0", gridwidth=1, zeroline=False, linecolor="#E2E8F0")


def render_chart(fig, height: int = 380) -> None:
    """Apply theme to *fig* and render it with the Plotly modebar hidden."""
    apply_chart_theme(fig, height=height)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def format_currency(value: float, currency: str = "NGN") -> str:
    symbol = "$" if currency == "USD" else "₦"
    return f"{symbol}{value:,.0f}"


def format_currency_abbr(value: float, currency: str = "NGN") -> str:
    """Return a compact currency string with B/M/K suffix for metric cards."""
    symbol = "$" if currency == "USD" else "₦"
    abs_val = abs(value)
    if abs_val >= 1_000_000_000:
        return f"{symbol}{value / 1_000_000_000:.1f}B"
    if abs_val >= 1_000_000:
        return f"{symbol}{value / 1_000_000:.1f}M"
    if abs_val >= 1_000:
        return f"{symbol}{value / 1_000:.1f}K"
    return f"{symbol}{value:,.0f}"


@st.cache_data(show_spinner=False)
def cached_demo_bundle() -> dict:
    return load_demo_bundle()


@st.cache_data(show_spinner=True)
def cached_generated_bundle(num_orders: int, seed: int, num_quality_incidents: int) -> dict:
    return generate_demo_bundle(
        num_orders=num_orders,
        seed=seed,
        num_quality_incidents=num_quality_incidents,
    )


def _build_bundle_from_uploads(uploaded_files) -> dict:
    payload = {file.name: file.getvalue() for file in uploaded_files}
    return build_bundle_from_upload_bytes(payload)


def ensure_dashboard_bundle() -> dict:
    with st.sidebar:
        st.header("Data source")
        source_mode = st.radio(
            "Choose source",
            ["Bundled demo", "Generate fresh demo", "Upload company data"],
            help="Use the included sample data, generate a realistic synthetic dataset, or upload company CSV extracts.",
            key="dashboard_source_mode",
        )
        st.download_button(
            "Download company upload templates",
            data=export_upload_template_pack(),
            file_name="company_upload_templates.zip",
            mime="application/zip",
            use_container_width=True,
        )

        bundle = None
        upload_error = None

        if source_mode == "Bundled demo":
            bundle = cached_demo_bundle()
            st.success("Using bundled demo dataset.")
        elif source_mode == "Generate fresh demo":
            num_orders = st.slider("Purchase orders", min_value=500, max_value=10000, value=2500, step=250, key="gen_orders")
            num_quality_incidents = st.slider(
                "Quality incidents",
                min_value=25,
                max_value=1000,
                value=150,
                step=25,
                key="gen_incidents",
            )
            seed = st.number_input("Random seed", min_value=1, max_value=999999, value=42, step=1, key="gen_seed")
            if st.button("Generate dataset", use_container_width=True, key="gen_button"):
                bundle = cached_generated_bundle(num_orders, seed, num_quality_incidents)
                st.session_state["dashboard_bundle"] = bundle
            else:
                bundle = st.session_state.get("dashboard_bundle") or cached_generated_bundle(num_orders, seed, num_quality_incidents)
        else:
            st.caption("Upload supplier, material, PO, and optional quality CSV files. Alias columns are auto-mapped.")
            uploaded_files = st.file_uploader(
                "Upload CSV files",
                type=["csv"],
                accept_multiple_files=True,
                help="Examples: vendor master, item master, PO lines, quality incidents.",
                key="company_csv_upload",
            )
            if uploaded_files:
                try:
                    bundle = _build_bundle_from_uploads(uploaded_files)
                    st.session_state["dashboard_bundle"] = bundle
                    st.success("Company data normalized successfully.")
                except UploadValidationError as exc:
                    upload_error = str(exc)
                except Exception as exc:  # pragma: no cover
                    upload_error = f"Unexpected upload error: {exc}"
            else:
                bundle = st.session_state.get("dashboard_bundle")
                st.info("Upload at least supplier, material, and purchase order CSVs.")

        if upload_error:
            st.error(upload_error)
            st.stop()

    if bundle is None:
        st.stop()

    st.session_state["dashboard_bundle"] = bundle
    return bundle


def build_filtered_context(bundle: dict) -> dict:
    purchase_orders = bundle["raw"]["purchase_orders"].copy()
    purchase_orders["po_date"] = pd.to_datetime(purchase_orders["po_date"], errors="coerce")
    min_date = purchase_orders["po_date"].min()
    max_date = purchase_orders["po_date"].max()
    all_categories = sorted([category for category in purchase_orders["category"].dropna().unique().tolist()])

    with st.sidebar:
        st.divider()
        st.subheader("Filters")
        selected_categories = st.multiselect(
            "Categories",
            all_categories,
            default=st.session_state.get("selected_categories", all_categories),
            key="selected_categories",
        )
        if min_date is not None and max_date is not None:
            default_range = st.session_state.get("selected_date_range", (min_date.date(), max_date.date()))
            date_range = st.date_input("Date range", value=default_range, key="selected_date_range")
        else:
            date_range = (date.today(), date.today())
        st.caption(f"Source: {bundle['metadata'].get('source_label', 'Unknown')}")

    start_date = None
    end_date = None
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range

    return prepare_dashboard_context(bundle, selected_categories=selected_categories, start_date=start_date, end_date=end_date)


def metric_strip(context: dict) -> None:
    metrics = context["metrics"]
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total spend", format_currency_abbr(metrics["filtered_total_spend"]))
    col2.metric("Suppliers", f"{metrics['filtered_supplier_count']:,}")
    col3.metric("Savings opportunity", format_currency_abbr(metrics["filtered_savings"]))
    col4.metric("Maverick spend", format_currency_abbr(metrics["filtered_maverick_spend"]))


def powerbi_pack_download(bundle: dict) -> None:
    st.download_button(
        "Download Power BI deployment pack",
        data=export_powerbi_pack(bundle),
        file_name="procurement_powerbi_pack.zip",
        mime="application/zip",
        use_container_width=True,
    )


def schema_reference_table():
    return upload_schema_reference()
