"""08 — FMCG Audit & Recommendation Ledger.

Admin-focused audit page for browsing persistent recommendation history,
reviewing ledger statistics, exporting the JSONL ledger, and compacting the
event file when needed.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pandas as pd
import plotly.express as px
import streamlit as st

from dashboard_ui import (
    configure_page,
    fmcg_recommendation_stats,
    fmcg_user_has_permission,
    get_fmcg_event_log,
    page_header,
    recommendation_history_df,
    require_fmcg_dashboard_access,
)
from procurement_spend_analysis.fmcg.access_control import Permission


configure_page("Audit & Recommendations", icon="🧾")
principal = require_fmcg_dashboard_access(
    Permission.VIEW_AUDIT_LOG,
    key_prefix="fmcg_audit",
)

page_header(
    "FMCG Audit & Recommendation Ledger",
    "Persistent recommendation history, approval trail, and ledger operations for admin users.",
)

stats = fmcg_recommendation_stats()
integrity_report = get_fmcg_event_log().integrity_report(limit=20)
metric_cols = st.columns(5, gap="small")
metric_cols[0].metric("Total events", f"{stats['total_events']}")
metric_cols[1].metric("Root recommendations", f"{stats['root_recommendations']}")
metric_cols[2].metric("Decision events", f"{stats['decision_events']}")
metric_cols[3].metric("Pending", f"{stats['action_counts'].get('pending', 0)}")
metric_cols[4].metric("Integrity", "Verified" if stats.get("integrity_verified") else "Broken")

if stats.get("integrity_verified"):
    st.success("Ledger integrity verified. The recommendation chain head matches the recorded event history.")
else:
    st.error("Ledger integrity check failed. Review the stored recommendation history before trusting audit outputs.")

st.caption(f"Ledger file: {stats['file_path'] or 'in-memory only'}")
if stats.get("archive_path"):
    st.caption(f"Archive file: {stats['archive_path']}")
if stats.get("chain_head"):
    st.caption(f"Current chain head: {stats['chain_head'][:16]}...")

st.markdown("##### Chain integrity inspector")
inspector_cols = st.columns([0.2, 0.2, 0.2, 0.4], gap="small")
inspector_cols[0].metric("Checked links", f"{integrity_report['checked_events']}")
inspector_cols[1].metric("Broken links", f"{integrity_report['broken_links']}")
inspector_cols[2].metric("Chain head", integrity_report["chain_head"][:12] if integrity_report.get("chain_head") else "N/A")
inspector_cols[3].caption(
    "Recent ledger links with recorded and expected hashes. Any mismatch indicates tampering or corruption in persisted history."
)

if integrity_report["rows"]:
    chain_df = pd.DataFrame(integrity_report["rows"])
    chain_df["status"] = chain_df["link_ok"].map({True: "ok", False: "broken"})
    chain_df["recorded_prev_hash"] = chain_df["recorded_prev_hash"].fillna("").str[:12]
    chain_df["expected_prev_hash"] = chain_df["expected_prev_hash"].fillna("").str[:12]
    chain_df["recorded_entry_hash"] = chain_df["recorded_entry_hash"].fillna("").str[:12]
    chain_df["expected_entry_hash"] = chain_df["expected_entry_hash"].fillna("").str[:12]
    st.dataframe(
        chain_df[[
            "sequence",
            "event_id",
            "action_taken",
            "recommendation_type",
            "status",
            "recorded_prev_hash",
            "expected_prev_hash",
            "recorded_entry_hash",
            "expected_entry_hash",
        ]],
        use_container_width=True,
        hide_index=True,
        height=260,
    )
else:
    st.info("No chain entries available for integrity inspection yet.")

left, right = st.columns([0.7, 0.3], gap="large")
with left:
    st.markdown("##### Recommendation type volume")
    type_df = pd.DataFrame(
        [
            {"recommendation_type": key, "events": value}
            for key, value in stats["recommendation_types"].items()
        ]
    )
    if type_df.empty:
        st.info("No recommendation events recorded yet.")
    else:
        st.dataframe(type_df.sort_values("events", ascending=False), use_container_width=True, hide_index=True)

with right:
    st.markdown("##### Action mix")
    action_df = pd.DataFrame(
        [
            {"action": key, "events": value}
            for key, value in stats["action_counts"].items()
        ]
    )
    st.dataframe(action_df, use_container_width=True, hide_index=True)

st.divider()

history = recommendation_history_df()
if not history.empty:
    summary_left, summary_right = st.columns(2, gap="large")
    with summary_left:
        st.markdown("##### Daily ledger volume")
        history["event_day"] = pd.to_datetime(history["timestamp"], errors="coerce").dt.date
        daily = history.groupby("event_day", as_index=False).size().rename(columns={"size": "events"})
        daily_fig = px.bar(daily, x="event_day", y="events")
        st.plotly_chart(daily_fig, use_container_width=True, config={"displayModeBar": False})
    with summary_right:
        st.markdown("##### Approval latency")
        root_df = history[history["related_event_id"].isna()][["event_id", "timestamp"]].rename(
            columns={"event_id": "root_event_id", "timestamp": "root_timestamp"}
        )
        decisions = history[history["related_event_id"].notna()][["related_event_id", "action_timestamp", "action_taken"]]
        latency = decisions.merge(root_df, left_on="related_event_id", right_on="root_event_id", how="left")
        if latency.empty:
            st.info("No resolved recommendations yet.")
        else:
            latency["latency_hours"] = (
                pd.to_datetime(latency["action_timestamp"], errors="coerce")
                - pd.to_datetime(latency["root_timestamp"], errors="coerce")
            ).dt.total_seconds() / 3600
            st.metric("Average approval latency", f"{latency['latency_hours'].mean():.2f} hrs")
            latency_fig = px.box(latency, x="action_taken", y="latency_hours")
            st.plotly_chart(latency_fig, use_container_width=True, config={"displayModeBar": False})

if history.empty:
    st.info("No recommendation history available yet.")
else:
    filter_col1, filter_col2 = st.columns(2, gap="large")
    with filter_col1:
        recommendation_types = ["All"] + sorted(history["recommendation_type"].dropna().unique().tolist())
        selected_type = st.selectbox("Recommendation type", options=recommendation_types, key="audit_type_filter")
    with filter_col2:
        actions = ["All"] + sorted(history["action_taken"].dropna().unique().tolist())
        selected_action = st.selectbox("Action status", options=actions, key="audit_action_filter")

    filtered = history.copy()
    if selected_type != "All":
        filtered = filtered[filtered["recommendation_type"] == selected_type]
    if selected_action != "All":
        filtered = filtered[filtered["action_taken"] == selected_action]

    st.markdown("##### Ledger history")
    st.dataframe(
        filtered[[
            "event_id",
            "recommendation_type",
            "action_taken",
            "model_id",
            "confidence_score",
            "approver_id",
            "timestamp",
        ]],
        use_container_width=True,
        hide_index=True,
        height=320,
    )

    selected_event_id = st.selectbox(
        "Inspect event history",
        options=filtered["event_id"].tolist(),
        key="audit_history_selector",
    )
    event_history = get_fmcg_event_log().history(selected_event_id)
    if event_history:
        st.markdown("##### Selected event timeline")
        st.json([event.model_dump() for event in event_history], expanded=False)

st.divider()

ops_left, ops_right = st.columns([0.55, 0.45], gap="large")
with ops_left:
    st.markdown("##### Export ledger")
    st.download_button(
        "Download JSONL ledger",
        data=get_fmcg_event_log().to_jsonl(),
        file_name="fmcg_recommendation_events.jsonl",
        mime="application/x-ndjson",
        use_container_width=True,
    )
    archive_data = get_fmcg_event_log().archive_jsonl()
    if archive_data:
        st.download_button(
            "Download archive JSONL",
            data=archive_data,
            file_name="fmcg_recommendation_events.archive.jsonl",
            mime="application/x-ndjson",
            use_container_width=True,
        )

with ops_right:
    st.markdown("##### Ledger maintenance")
    if fmcg_user_has_permission(principal, Permission.VIEW_AUDIT_LOG):
        if st.button("Compact persisted ledger", use_container_width=True, key="compact_fmcg_ledger"):
            retained = get_fmcg_event_log().compact()
            st.success(f"Ledger compacted. Retained {retained} events.")
        archive_days = st.number_input(
            "Archive resolved threads older than days",
            min_value=1,
            max_value=3650,
            value=30,
            step=1,
            key="archive_fmcg_days",
        )
        if st.button("Archive resolved history", use_container_width=True, key="archive_fmcg_ledger"):
            cutoff = (datetime.now(timezone.utc) - timedelta(days=int(archive_days))).isoformat()
            result = get_fmcg_event_log().archive_before(cutoff)
            st.success(
                f"Archived {result['archived_events']} events across {result['archived_threads']} threads."
            )
            st.rerun()