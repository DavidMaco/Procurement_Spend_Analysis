from __future__ import annotations

import streamlit as st

from dashboard_ui import (
    build_filtered_context,
    configure_page,
    ensure_dashboard_bundle,
    page_header,
    powerbi_pack_download,
    schema_reference_table,
)


configure_page("Data Hub")

bundle = ensure_dashboard_bundle()
context = build_filtered_context(bundle)
metadata = context["metadata"]
raw = context["raw"]

page_header(
    "Data Hub",
    "Upload readiness diagnostics, schema reference, and Power BI export handoff.",
)

# ── quality report + schema reference ───────────────────────────────────
left, right = st.columns(2, gap="large")
with left:
    st.markdown("##### Data quality report")
    st.json(metadata.get("quality_report", {}), expanded=False)
    if metadata.get("rename_maps"):
        with st.expander("Detected column mappings"):
            st.json(metadata["rename_maps"], expanded=False)

with right:
    st.markdown("##### Upload schema reference")
    schema_df = schema_reference_table()
    st.dataframe(schema_df, use_container_width=True, hide_index=True)
    st.download_button(
        "⬇️  Download schema reference CSV",
        data=schema_df.to_csv(index=False),
        file_name="upload_schema_reference.csv",
        mime="text/csv",
        use_container_width=True,
    )

st.divider()

# ── Power BI export ─────────────────────────────────────────────────────────────
st.markdown("##### Power BI deployment pack")
powerbi_pack_download(bundle)

st.divider()

# ── raw table preview ────────────────────────────────────────────────────────
with st.expander("Preview normalized raw tables", expanded=False):
    selected_table = st.selectbox("Table", list(raw.keys()))
    st.dataframe(raw[selected_table].head(200), use_container_width=True, hide_index=True)
