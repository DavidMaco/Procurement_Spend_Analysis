"""FastAPI router exposing FMCG OS Milestone-1 endpoints."""

from __future__ import annotations

import io
from dataclasses import asdict
from typing import Annotated, Any

import pandas as pd
from fastapi import APIRouter, Depends, File, Header, HTTPException, UploadFile
from pydantic import BaseModel

from procurement_spend_analysis.config import get_settings
from procurement_spend_analysis.fmcg.access_control import (
    Permission,
    build_scoped_access_control,
)
from procurement_spend_analysis.fmcg.event_log import EventLog, RecommendationEvent
from procurement_spend_analysis.fmcg.features import default_feature_store
from procurement_spend_analysis.fmcg.kpi_catalog import default_kpi_catalog
from procurement_spend_analysis.fmcg.metrics import default_metrics_layer
from procurement_spend_analysis.fmcg.models import validate_fmcg_dataframe
from procurement_spend_analysis.fmcg.pilot import (
    PilotCohort,
    PilotImpactReport,
    evaluate_pilot_impact,
    select_pilot_cohort,
)
from procurement_spend_analysis.fmcg.reconciliation import (
    ReconciliationSuite,
    default_reconciliation_suite,
)
from procurement_spend_analysis.fmcg.variance_alerts import default_variance_engine

router = APIRouter(prefix="/fmcg", tags=["fmcg"])

_settings = get_settings()
_MAX_BYTES = _settings.max_upload_file_size_mb * 1024 * 1024
_MAX_ROWS = _settings.max_upload_rows_per_file
_EVENT_LOG = EventLog(_settings.fmcg_event_log_path, _settings.fmcg_event_archive_path)


class RecommendationCreateRequest(BaseModel):
    model_id: str
    model_version: str
    input_snapshot_ref: str
    recommendation_type: str
    recommendation_payload: dict[str, Any]
    confidence_score: float


class RecommendationDecisionRequest(BaseModel):
    approver_id: str


class RecommendationArchiveRequest(BaseModel):
    before_timestamp: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _read_upload(file: UploadFile) -> pd.DataFrame:
    """Read an uploaded CSV into a DataFrame with safety limits."""
    content = await file.read()
    if len(content) > _MAX_BYTES:
        raise HTTPException(status_code=413, detail="File exceeds maximum upload size")

    # Detect separator (tab vs comma)
    head = content[:2048].decode("utf-8", errors="replace")
    sep = "\t" if "\t" in head else ","

    df = pd.read_csv(io.BytesIO(content), sep=sep)
    df.columns = [c.strip() for c in df.columns]

    if len(df) > _MAX_ROWS:
        raise HTTPException(
            status_code=413, detail=f"File exceeds {_MAX_ROWS} row limit"
        )
    return df


def require_permission(permission: Permission):
    async def _dependency(
        x_user_id: Annotated[str | None, Header(alias="X-User-Id")] = None,
        x_roles: Annotated[str | None, Header(alias="X-Roles")] = None,
    ) -> str:
        if not x_user_id or not x_roles:
            raise HTTPException(
                status_code=401,
                detail="Missing X-User-Id or X-Roles header",
            )

        role_names = [role.strip() for role in x_roles.split(",") if role.strip()]
        try:
            access = build_scoped_access_control(x_user_id, role_names)
            access.require_permission(x_user_id, permission)
        except KeyError as exc:
            raise HTTPException(status_code=401, detail="Unauthorized") from exc
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail="Permission denied") from exc
        return x_user_id

    return _dependency


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/validate")
async def validate_upload(
    file: UploadFile = File(...),
    _: Annotated[str, Depends(require_permission(Permission.UPLOAD_DATA))] = "",
) -> dict[str, Any]:
    """Validate an FMCG CSV against the Pandera schema and reconciliation suite."""
    df = await _read_upload(file)

    # Schema validation
    schema_errors: list[dict[str, str]] = []
    try:
        validate_fmcg_dataframe(df)
    except Exception as exc:
        schema_errors = [{"error": str(exc)}]

    # Reconciliation
    suite = default_reconciliation_suite()
    try:
        reports = suite.run(df)
        recon_summary = ReconciliationSuite.summary(reports)
    except Exception as exc:
        recon_summary = {"error": str(exc)}

    return {
        "rows": len(df),
        "columns": list(df.columns),
        "schema_valid": len(schema_errors) == 0,
        "schema_errors": schema_errors,
        "reconciliation": recon_summary,
    }


@router.get("/metrics")
def list_metrics(
    _: Annotated[str, Depends(require_permission(Permission.VIEW_KPI_CATALOG))] = "",
) -> list[dict[str, Any]]:
    """Return the list of registered semantic metrics."""
    layer = default_metrics_layer()
    return [
        {
            "name": m.name,
            "grain": m.grain,
            "dimensions": m.dimensions,
            "description": m.description,
        }
        for m in layer.list_metrics()
    ]


@router.get("/kpis")
def list_kpis(
    _: Annotated[str, Depends(require_permission(Permission.VIEW_KPI_CATALOG))] = "",
) -> list[dict[str, Any]]:
    """Return the full KPI catalog as JSON."""
    catalog = default_kpi_catalog()
    return [
        {
            "id": k.id,
            "name": k.name,
            "formula": k.formula_str,
            "category": k.category,
            "owner": k.owner,
            "cadence": k.cadence,
            "description": k.description,
        }
        for k in catalog.list_all()
    ]


@router.post("/pilot")
async def run_pilot_selection(
    file: UploadFile = File(...),
    _: Annotated[str, Depends(require_permission(Permission.UPLOAD_DATA))] = "",
) -> dict[str, Any]:
    """Upload an FMCG CSV and run pilot cohort selection."""
    df = await _read_upload(file)
    try:
        validate_fmcg_dataframe(df)
    except Exception as exc:
        raise HTTPException(
            status_code=422, detail=f"Schema validation failed: {exc}"
        ) from exc

    cohort: PilotCohort = select_pilot_cohort(df)
    return cohort.model_dump()


@router.post("/pilot/evaluate")
async def evaluate_pilot_selection(
    file: UploadFile = File(...),
    intervention_date: str | None = None,
    _: Annotated[str, Depends(require_permission(Permission.UPLOAD_DATA))] = "",
) -> dict[str, Any]:
    """Upload an FMCG CSV and evaluate pilot performance with a control baseline."""
    df = await _read_upload(file)
    try:
        df = validate_fmcg_dataframe(df)
        report: PilotImpactReport = evaluate_pilot_impact(
            df,
            intervention_date=intervention_date,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=422, detail=f"Schema validation failed: {exc}"
        ) from exc

    return report.model_dump()


@router.get("/features")
def list_features(
    _: Annotated[str, Depends(require_permission(Permission.VIEW_KPI_CATALOG))] = "",
) -> list[dict[str, Any]]:
    """Return the list of registered demand-driver features."""
    store = default_feature_store()
    return [
        {
            "name": f.name,
            "source_columns": f.source_columns,
            "description": f.description,
        }
        for f in store.list_features()
    ]


@router.get("/alerts/rules")
def list_alert_rules(
    _: Annotated[str, Depends(require_permission(Permission.VIEW_ALERTS))] = "",
) -> list[dict[str, Any]]:
    """Return the configured variance-alert rules."""
    engine = default_variance_engine()
    return [
        {
            "name": rule.name,
            "metric_column": rule.metric_column,
            "category": rule.category.value,
            "threshold_pct": rule.threshold_pct,
            "severity": rule.severity.value,
            "aggregation": rule.aggregation,
            "group_by": rule.group_by,
            "description": rule.description,
        }
        for rule in engine.list_rules()
    ]


@router.post("/alerts/evaluate")
async def evaluate_alerts(
    baseline_file: UploadFile = File(...),
    current_file: UploadFile = File(...),
    _: Annotated[str, Depends(require_permission(Permission.VIEW_ALERTS))] = "",
) -> dict[str, Any]:
    """Evaluate default variance rules against baseline and current FMCG uploads."""
    baseline_df = validate_fmcg_dataframe(await _read_upload(baseline_file))
    current_df = validate_fmcg_dataframe(await _read_upload(current_file))

    engine = default_variance_engine()
    alerts = engine.evaluate(baseline_df, current_df)
    return {
        "rule_count": len(engine.list_rules()),
        "alert_count": len(alerts),
        "alerts": [asdict(alert) for alert in alerts],
    }


@router.post("/events/recommendations")
def record_recommendation(
    payload: RecommendationCreateRequest,
    _: Annotated[str, Depends(require_permission(Permission.VIEW_EVENT_LOG))] = "",
) -> dict[str, Any]:
    """Append a new recommendation event to the immutable event log."""
    event = RecommendationEvent(**payload.model_dump())
    _EVENT_LOG.record(event)
    return event.model_dump()


@router.get("/events")
def list_recommendation_events(
    recommendation_type: str | None = None,
    model_id: str | None = None,
    _: Annotated[str, Depends(require_permission(Permission.VIEW_EVENT_LOG))] = "",
) -> list[dict[str, Any]]:
    """List recorded recommendation events, newest first."""
    return [
        event.model_dump()
        for event in _EVENT_LOG.query(
            recommendation_type=recommendation_type,
            model_id=model_id,
        )
    ]


@router.get("/events/stats")
def get_recommendation_event_stats(
    _: Annotated[str, Depends(require_permission(Permission.VIEW_AUDIT_LOG))] = "",
) -> dict[str, Any]:
    """Return operational statistics for the recommendation ledger."""
    return _EVENT_LOG.stats()


@router.get("/events/integrity")
def get_recommendation_event_integrity(
    limit: int = 25,
    _: Annotated[str, Depends(require_permission(Permission.VIEW_AUDIT_LOG))] = "",
) -> dict[str, Any]:
    """Return a recent chain-inspection report for the recommendation ledger."""
    if limit < 0:
        raise HTTPException(
            status_code=422, detail="limit must be greater than or equal to zero"
        )
    return _EVENT_LOG.integrity_report(limit=limit)


@router.post("/events/compact")
def compact_recommendation_event_log(
    _: Annotated[str, Depends(require_permission(Permission.VIEW_AUDIT_LOG))] = "",
) -> dict[str, int]:
    """Rewrite the persisted recommendation ledger in compact JSONL form."""
    return {"retained_events": _EVENT_LOG.compact()}


@router.post("/events/archive")
def archive_recommendation_event_log(
    payload: RecommendationArchiveRequest,
    _: Annotated[str, Depends(require_permission(Permission.VIEW_AUDIT_LOG))] = "",
) -> dict[str, int]:
    """Move resolved recommendation threads older than the cutoff into the archive ledger."""
    return _EVENT_LOG.archive_before(payload.before_timestamp)


@router.get("/events/{event_id}/history")
def get_recommendation_history(
    event_id: str,
    _: Annotated[str, Depends(require_permission(Permission.VIEW_EVENT_LOG))] = "",
) -> list[dict[str, Any]]:
    """Return the original recommendation and any approval/rejection history."""
    history = _EVENT_LOG.history(event_id)
    if not history:
        raise HTTPException(status_code=404, detail=f"Event {event_id} not found")
    return [event.model_dump() for event in history]


@router.post("/events/{event_id}/approve")
def approve_recommendation(
    event_id: str,
    payload: RecommendationDecisionRequest,
    _: Annotated[
        str, Depends(require_permission(Permission.APPROVE_RECOMMENDATION))
    ] = "",
) -> dict[str, Any]:
    """Append an approval decision event for a recommendation."""
    try:
        event = _EVENT_LOG.approve(event_id, payload.approver_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Recommendation not found") from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=409, detail="Recommendation already decided"
        ) from exc
    return event.model_dump()


@router.post("/events/{event_id}/reject")
def reject_recommendation(
    event_id: str,
    payload: RecommendationDecisionRequest,
    _: Annotated[
        str, Depends(require_permission(Permission.REJECT_RECOMMENDATION))
    ] = "",
) -> dict[str, Any]:
    """Append a rejection decision event for a recommendation."""
    try:
        event = _EVENT_LOG.reject(event_id, payload.approver_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Recommendation not found") from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=409, detail="Recommendation already decided"
        ) from exc
    return event.model_dump()
