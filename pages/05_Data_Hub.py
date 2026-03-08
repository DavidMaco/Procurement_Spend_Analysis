from __future__ import annotations

import streamlit as st

from dashboard_ui import (
    build_filtered_context,
    configure_page,
    ensure_dashboard_bundle,
    powerbi_pack_download,
    schema_reference_table,
)


configure_page("Data Hub")

bundle = ensure_dashboard_bundle()
context = build_filtered_context(bundle)
metadata = context["metadata"]
raw = context["raw"]

st.title("Data Hub")
st.caption("Upload readiness, normalized raw tables, schema reference, and Power BI handoff downloads.")

left, right = st.columns([1.0, 1.0])
with left:
    st.subheader("Data quality report")
    st.json(metadata.get("quality_report", {}))
    if metadata.get("rename_maps"):
        with st.expander("Detected column mappings"):
            st.json(metadata["rename_maps"])
with right:
    st.subheader("Expected upload schemas")
    schema_df = schema_reference_table()
    st.dataframe(schema_df, use_container_width=True, hide_index=True)
    st.download_button(
        "Download schema reference CSV",
        data=schema_df.to_csv(index=False),
        file_name="upload_schema_reference.csv",
        mime="text/csv",
        use_container_width=True,
    )

st.subheader("Power BI handoff")
powerbi_pack_download(bundle)

with st.expander("Preview normalized raw tables"):
    selected_table = st.selectbox("Table", list(raw.keys()))
    st.dataframe(raw[selected_table].head(200), use_container_width=True, hide_index=True)
