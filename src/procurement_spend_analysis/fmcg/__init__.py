"""FMCG Revenue and Procurement OS — M1 + M2 package."""

from __future__ import annotations

# M1 — Foundation
from .features import FeatureStore, default_feature_store
from .kpi_catalog import KPICatalog, default_kpi_catalog
from .metrics import SemanticMetricsLayer, default_metrics_layer
from .models import (
    FMCGSalesRecord,
    FMCGSalesSchema,
    SKUEntity,
    StoreEntity,
    SupplierEntity,
    load_fmcg_csv,
    validate_fmcg_dataframe,
)
from .pilot import PilotCohort, PilotConfig, select_pilot_cohort
from .reconciliation import ReconciliationSuite, default_reconciliation_suite

# M2 — Baseline apps
from .access_control import (
    AccessControlService,
    Permission,
    Role,
    User,
    build_scoped_access_control,
)
from .event_log import ActionTaken, EventLog, RecommendationEvent
from .variance_alerts import (
    Alert,
    AlertCategory,
    AlertSeverity,
    VarianceAlertEngine,
    VarianceRule,
    default_variance_engine,
)

__all__ = [
    # M1
    "FMCGSalesSchema",
    "FMCGSalesRecord",
    "StoreEntity",
    "SKUEntity",
    "SupplierEntity",
    "validate_fmcg_dataframe",
    "load_fmcg_csv",
    "SemanticMetricsLayer",
    "default_metrics_layer",
    "FeatureStore",
    "default_feature_store",
    "ReconciliationSuite",
    "default_reconciliation_suite",
    "KPICatalog",
    "default_kpi_catalog",
    "PilotConfig",
    "PilotCohort",
    "select_pilot_cohort",
    # M2 — Variance alerts
    "VarianceAlertEngine",
    "VarianceRule",
    "Alert",
    "AlertCategory",
    "AlertSeverity",
    "default_variance_engine",
    # M2 — Event log
    "EventLog",
    "RecommendationEvent",
    "ActionTaken",
    # M2 — Access control
    "AccessControlService",
    "Permission",
    "Role",
    "User",
    "build_scoped_access_control",
]
