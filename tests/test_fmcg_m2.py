"""Tests for Milestone 2 — Variance Alerts, Event Log, Access Control."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd
import pytest

# ---------------------------------------------------------------------------
# Variance Alerts
# ---------------------------------------------------------------------------
from procurement_spend_analysis.fmcg.variance_alerts import (
    Alert,
    AlertCategory,
    AlertSeverity,
    VarianceAlertEngine,
    VarianceRule,
    default_variance_engine,
)


class TestVarianceAlerts:
    """Unit tests for the variance alerting engine."""

    @pytest.fixture()
    def baseline_df(self) -> pd.DataFrame:
        rng = np.random.default_rng(1)
        return pd.DataFrame(
            {
                "net_sales": rng.uniform(100, 500, 50),
                "discount_pct": rng.uniform(0.05, 0.15, 50),
                "purchase_cost": rng.uniform(50, 200, 50),
                "lead_time_days": rng.uniform(5, 10, 50),
                "category": ["Beverages"] * 25 + ["Snacks"] * 25,
                "supplier_id": [f"S{i % 5:02d}" for i in range(50)],
            }
        )

    @pytest.fixture()
    def current_df(self, baseline_df: pd.DataFrame) -> pd.DataFrame:
        """Shift values so some rules should fire."""
        df = baseline_df.copy()
        df["net_sales"] *= 0.5  # -50% → should fire
        df["purchase_cost"] *= 1.3  # +30% → should fire
        return df

    def test_engine_registers_rules(self) -> None:
        engine = VarianceAlertEngine()
        assert engine.list_rules() == []
        engine.add_rule(
            VarianceRule(
                name="test",
                metric_column="net_sales",
                category=AlertCategory.COMMERCIAL,
                threshold_pct=5.0,
            )
        )
        assert len(engine.list_rules()) == 1

    def test_no_alerts_when_within_threshold(self, baseline_df: pd.DataFrame) -> None:
        engine = VarianceAlertEngine()
        engine.add_rule(
            VarianceRule(
                name="tight",
                metric_column="net_sales",
                category=AlertCategory.COMMERCIAL,
                threshold_pct=99.0,  # huge threshold — nothing should fire
            )
        )
        alerts = engine.evaluate(baseline_df, baseline_df)
        assert alerts == []

    def test_alert_fires_on_large_variance(
        self, baseline_df: pd.DataFrame, current_df: pd.DataFrame
    ) -> None:
        engine = VarianceAlertEngine()
        engine.add_rule(
            VarianceRule(
                name="net_drop",
                metric_column="net_sales",
                category=AlertCategory.COMMERCIAL,
                threshold_pct=10.0,
                severity=AlertSeverity.CRITICAL,
                aggregation="sum",
            )
        )
        alerts = engine.evaluate(baseline_df, current_df)
        assert len(alerts) == 1
        assert alerts[0].rule_name == "net_drop"
        assert alerts[0].severity == "critical"
        assert alerts[0].variance_pct < 0  # decrease

    def test_grouped_alert(
        self, baseline_df: pd.DataFrame, current_df: pd.DataFrame
    ) -> None:
        engine = VarianceAlertEngine()
        engine.add_rule(
            VarianceRule(
                name="cost_by_supplier",
                metric_column="purchase_cost",
                category=AlertCategory.PROCUREMENT,
                threshold_pct=5.0,
                group_by=["supplier_id"],
            )
        )
        alerts = engine.evaluate(baseline_df, current_df)
        assert len(alerts) > 0
        for a in alerts:
            assert a.group_key is not None
            assert "supplier_id" in a.group_key

    def test_default_engine_has_rules(self) -> None:
        engine = default_variance_engine()
        assert len(engine.list_rules()) >= 4

    def test_derived_metric_rule_uses_canonical_leakage(self) -> None:
        engine = default_variance_engine()
        baseline = pd.DataFrame(
            {
                "gross_sales": [100.0, 100.0],
                "net_sales": [95.0, 95.0],
                "category": ["Beverages", "Beverages"],
                "supplier_id": ["S01", "S01"],
                "purchase_cost": [10.0, 10.0],
                "lead_time_days": [5.0, 5.0],
            }
        )
        current = baseline.copy()
        current["net_sales"] = [70.0, 70.0]
        alerts = engine.evaluate(baseline, current)
        assert any(a.rule_name == "gross_to_net_leakage_spike" for a in alerts)

    def test_zero_baseline_no_crash(self) -> None:
        engine = VarianceAlertEngine()
        engine.add_rule(
            VarianceRule(
                name="zero",
                metric_column="val",
                category=AlertCategory.COMMERCIAL,
                threshold_pct=5.0,
            )
        )
        base = pd.DataFrame({"val": [0.0, 0.0]})
        curr = pd.DataFrame({"val": [10.0, 20.0]})
        alerts = engine.evaluate(base, curr)
        assert alerts == []  # zero baseline → skipped


# ---------------------------------------------------------------------------
# Event Log
# ---------------------------------------------------------------------------
from procurement_spend_analysis.fmcg.event_log import (
    ActionTaken,
    EventLog,
    RecommendationEvent,
)


class TestEventLog:
    """Unit tests for the recommendation event log."""

    @pytest.fixture()
    def log(self) -> EventLog:
        return EventLog()

    @pytest.fixture()
    def sample_event(self) -> RecommendationEvent:
        return RecommendationEvent(
            model_id="promo_v1",
            model_version="1.0.0",
            input_snapshot_ref="s3://bucket/snap_001.parquet",
            recommendation_type="promo_depth",
            recommendation_payload={"sku": "SKU-001", "suggested_discount": 0.15},
            confidence_score=0.87,
        )

    def test_record_and_get(self, log: EventLog, sample_event: RecommendationEvent) -> None:
        eid = log.record(sample_event)
        assert log.count() == 1
        retrieved = log.get(eid)
        assert retrieved is not None
        assert retrieved.model_id == "promo_v1"

    def test_get_missing_returns_none(self, log: EventLog) -> None:
        assert log.get("nonexistent") is None

    def test_query_by_type(self, log: EventLog) -> None:
        for rt in ["promo_depth", "supplier_switch", "promo_depth"]:
            log.record(
                RecommendationEvent(
                    model_id="m",
                    model_version="1",
                    input_snapshot_ref="ref",
                    recommendation_type=rt,
                    recommendation_payload={},
                    confidence_score=0.5,
                )
            )
        results = log.query(recommendation_type="promo_depth")
        assert len(results) == 2

    def test_approve_and_reject(self, log: EventLog, sample_event: RecommendationEvent) -> None:
        eid = log.record(sample_event)
        updated = log.approve(eid, "user-42")
        assert updated.action_taken == ActionTaken.APPROVED
        assert updated.approver_id == "user-42"
        assert updated.action_timestamp is not None
        assert updated.related_event_id == eid

    def test_approval_is_appended_not_overwritten(
        self, log: EventLog, sample_event: RecommendationEvent
    ) -> None:
        eid = log.record(sample_event)
        approved = log.approve(eid, "user-42")
        history = log.history(eid)
        assert len(history) == 2
        assert history[0].event_id == eid
        assert history[0].action_taken == ActionTaken.PENDING
        assert history[1].event_id == approved.event_id
        assert history[1].related_event_id == eid

    def test_double_transition_raises(
        self, log: EventLog, sample_event: RecommendationEvent
    ) -> None:
        eid = log.record(sample_event)
        log.approve(eid, "user-42")
        with pytest.raises(ValueError, match="already resolved"):
            log.reject(eid, "user-99")

    def test_transition_missing_raises(self, log: EventLog) -> None:
        with pytest.raises(KeyError):
            log.approve("no-such-id", "usr")

    def test_event_immutability(self, sample_event: RecommendationEvent) -> None:
        with pytest.raises(Exception):
            sample_event.model_id = "hacked"  # type: ignore[misc]

    def test_all_events_insertion_order(self, log: EventLog) -> None:
        ids: list[str] = []
        for i in range(5):
            ev = RecommendationEvent(
                model_id=f"m{i}",
                model_version="1",
                input_snapshot_ref="r",
                recommendation_type="t",
                recommendation_payload={},
                confidence_score=0.1 * i,
            )
            ids.append(log.record(ev))
        all_ev = log.all_events()
        assert [e.event_id for e in all_ev] == ids

    def test_event_log_persists_to_jsonl(self, tmp_path) -> None:
        log_path = tmp_path / "events.jsonl"
        first = EventLog(log_path)
        event = RecommendationEvent(
            model_id="promo_v1",
            model_version="1.0.0",
            input_snapshot_ref="snapshot://001",
            recommendation_type="promo_depth",
            recommendation_payload={"sku": "SKU-001"},
            confidence_score=0.88,
        )
        first.record(event)

        second = EventLog(log_path)
        assert second.count() == 1
        assert second.get(event.event_id) is not None

        decision = second.approve(event.event_id, "approver-1")
        third = EventLog(log_path)
        assert third.count() == 2
        assert len(third.history(event.event_id)) == 2
        assert third.get(decision.event_id) is not None

    def test_event_log_stats_and_compaction(self, tmp_path) -> None:
        log_path = tmp_path / "events.jsonl"
        log = EventLog(log_path)
        event = RecommendationEvent(
            model_id="procurement-hub",
            model_version="2.0.0",
            input_snapshot_ref="snapshot://stats",
            recommendation_type="supplier_negotiation",
            recommendation_payload={"supplier_id": "S001"},
            confidence_score=0.77,
        )
        log.record(event)
        log.approve(event.event_id, "approver-2")

        stats = log.stats()
        assert stats["total_events"] == 2
        assert stats["root_recommendations"] == 1
        assert stats["decision_events"] == 1
        assert stats["action_counts"]["approved"] == 1
        assert stats["recommendation_types"]["supplier_negotiation"] == 2

        retained = log.compact()
        assert retained == 2
        assert log_path.exists()
        assert len(log_path.read_text(encoding="utf-8").splitlines()) == 2

    def test_event_log_archives_resolved_threads(self, tmp_path) -> None:
        log_path = tmp_path / "events.jsonl"
        archive_path = tmp_path / "events.archive.jsonl"
        log = EventLog(log_path, archive_path)

        root = RecommendationEvent(
            event_id="root-1",
            timestamp=(datetime.now(timezone.utc) - timedelta(days=90)).isoformat(),
            model_id="procurement-hub",
            model_version="2.0.0",
            input_snapshot_ref="snapshot://archive",
            recommendation_type="supplier_negotiation",
            recommendation_payload={"supplier_id": "S001"},
            confidence_score=0.81,
        )
        log.record(root)
        log.approve(root.event_id, "approver-9")

        pending = RecommendationEvent(
            event_id="root-2",
            timestamp=datetime.now(timezone.utc).isoformat(),
            model_id="commercial-command-centre",
            model_version="2.0.0",
            input_snapshot_ref="snapshot://pending",
            recommendation_type="promo_depth",
            recommendation_payload={"category": "Beverages"},
            confidence_score=0.74,
        )
        log.record(pending)

        cutoff = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        result = log.archive_before(cutoff)
        assert result["archived_threads"] == 1
        assert result["archived_events"] == 2
        assert result["retained_events"] == 1
        assert archive_path.exists()
        assert len(archive_path.read_text(encoding="utf-8").splitlines()) == 2
        assert log.get("root-1") is None
        assert log.get("root-2") is not None


# ---------------------------------------------------------------------------
# Access Control
# ---------------------------------------------------------------------------
from procurement_spend_analysis.fmcg.access_control import (
    AccessControlService,
    Permission,
    Role,
    User,
)


class TestAccessControl:
    """Unit tests for the RBAC access-control service."""

    @pytest.fixture()
    def svc(self) -> AccessControlService:
        return AccessControlService()

    def test_default_roles_loaded(self, svc: AccessControlService) -> None:
        roles = svc.list_roles()
        names = {r.name for r in roles}
        assert {"viewer", "analyst", "approver", "admin"} <= names

    def test_add_and_get_user(self, svc: AccessControlService) -> None:
        svc.add_user(User(user_id="u1", display_name="Alice"))
        assert svc.get_user("u1").display_name == "Alice"

    def test_get_missing_user_raises(self, svc: AccessControlService) -> None:
        with pytest.raises(KeyError, match="User"):
            svc.get_user("nobody")

    def test_assign_role(self, svc: AccessControlService) -> None:
        svc.add_user(User(user_id="u1", display_name="Alice"))
        updated = svc.assign_role("u1", "analyst")
        assert "analyst" in updated.roles

    def test_assign_unknown_role_raises(self, svc: AccessControlService) -> None:
        svc.add_user(User(user_id="u1", display_name="Alice"))
        with pytest.raises(KeyError, match="Role"):
            svc.assign_role("u1", "superadmin")

    def test_check_permission_positive(self, svc: AccessControlService) -> None:
        svc.add_user(User(user_id="u1", display_name="Alice"))
        svc.assign_role("u1", "viewer")
        assert svc.check_permission("u1", Permission.VIEW_COMMERCIAL_DASHBOARD)

    def test_check_permission_negative(self, svc: AccessControlService) -> None:
        svc.add_user(User(user_id="u1", display_name="Alice"))
        svc.assign_role("u1", "viewer")
        assert not svc.check_permission("u1", Permission.MANAGE_USERS)

    def test_require_permission_raises(self, svc: AccessControlService) -> None:
        svc.add_user(User(user_id="u1", display_name="Alice"))
        svc.assign_role("u1", "viewer")
        with pytest.raises(PermissionError, match="lacks permission"):
            svc.require_permission("u1", Permission.APPROVE_RECOMMENDATION)

    def test_admin_has_all_permissions(self, svc: AccessControlService) -> None:
        svc.add_user(User(user_id="a1", display_name="Admin"))
        svc.assign_role("a1", "admin")
        perms = svc.get_user_permissions("a1")
        assert perms == frozenset(Permission)

    def test_add_custom_role(self, svc: AccessControlService) -> None:
        custom = Role(
            name="finance",
            permissions=frozenset({Permission.VIEW_KPI_CATALOG, Permission.VIEW_EVENT_LOG}),
        )
        svc.add_role(custom)
        assert svc.get_role("finance").name == "finance"

    def test_duplicate_role_assignment_is_idempotent(
        self, svc: AccessControlService
    ) -> None:
        svc.add_user(User(user_id="u1", display_name="Alice"))
        svc.assign_role("u1", "viewer")
        svc.assign_role("u1", "viewer")
        assert svc.get_user("u1").roles.count("viewer") == 1
