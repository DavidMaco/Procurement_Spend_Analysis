"""Pilot cohort selection and impact measurement for the FMCG OS A/B-test framework."""

from __future__ import annotations

from typing import Literal, Optional

import pandas as pd
from pydantic import BaseModel


class PilotConfig(BaseModel):
    """Tunable parameters for pilot cohort selection."""

    countries: int = 1
    min_categories: int = 2
    max_categories: int = 3
    min_rows_per_category: int = 10_000
    min_completeness_pct: float = 0.95


class PilotCohort(BaseModel):
    """Selected pilot cohort ready for A/B experimentation."""

    country: str
    categories: list[str]
    control_stores: list[str]
    treatment_stores: list[str]
    row_count: int
    date_range: tuple[str, str]


class PilotArmSummary(BaseModel):
    """Normalized outcome summary for one arm in one pilot period."""

    arm: Literal["control", "treatment"]
    period: Literal["pre", "post"]
    row_count: int
    store_count: int
    active_days: int
    start_date: str
    end_date: str
    gross_sales: float
    net_sales: float
    units_sold: int
    purchase_cost_total: float
    contribution_margin: float
    gross_to_net_leakage_pct: float
    net_sales_per_store_day: float
    units_sold_per_store_day: float
    contribution_margin_per_store_day: float
    purchase_cost_per_unit: float


class PilotMetricImpact(BaseModel):
    """Difference-in-differences result for a single pilot KPI."""

    metric: str
    direction: Literal["higher_is_better", "lower_is_better"]
    control_pre: float
    control_post: float
    treatment_pre: float
    treatment_post: float
    control_change: float
    treatment_change: float
    control_change_pct: float | None
    treatment_change_pct: float | None
    incremental_lift: float
    incremental_lift_pct: float | None
    favorable_movement: bool


class PilotImpactReport(BaseModel):
    """Evaluation of pilot outcomes across control and treatment arms."""

    cohort: PilotCohort
    intervention_start_date: str
    pre_period: tuple[str, str]
    post_period: tuple[str, str]
    arm_summaries: list[PilotArmSummary]
    metric_impacts: list[PilotMetricImpact]
    primary_metric: str
    primary_incremental_lift: float
    primary_incremental_lift_pct: float | None


def profile_data_completeness(df: pd.DataFrame) -> pd.DataFrame:
    """Return per-country completeness statistics.

    Completeness is defined as 1 − (fraction of NaN cells) for each country
    partition.
    """
    countries = df.groupby("country").apply(
        lambda g: pd.Series(
            {
                "row_count": len(g),
                "completeness": 1.0 - g.isna().sum().sum() / (len(g) * len(g.columns)),
                "n_stores": g["store_id"].nunique(),
                "n_categories": g["category"].nunique(),
                "date_min": str(g["date"].min()),
                "date_max": str(g["date"].max()),
            }
        ),
        include_groups=False,
    )
    return countries.reset_index()


def select_pilot_cohort(
    df: pd.DataFrame,
    config: Optional[PilotConfig] = None,
) -> PilotCohort:
    """Deterministically pick the best country + categories for a pilot.

    Steps
    -----
    1.  Profile data completeness per country.
    2.  Pick the country with highest completeness (ties broken by volume).
    3.  Within that country, pick the top-N categories by row count that
        satisfy the min-rows threshold.
    4.  Split stores 50 / 50 into control vs. treatment (seed = 42).
    """
    if config is None:
        config = PilotConfig()

    profile = profile_data_completeness(df)
    # Filter to countries meeting completeness threshold
    eligible = profile[profile["completeness"] >= config.min_completeness_pct]
    if eligible.empty:
        # Fall back to all countries sorted by completeness
        eligible = profile.sort_values("completeness", ascending=False)

    # Best country: highest completeness then row_count
    best = eligible.sort_values(
        ["completeness", "row_count"], ascending=[False, False]
    ).iloc[0]
    country: str = best["country"]

    # Categories within the chosen country
    country_df = df[df["country"] == country]
    cat_counts = country_df.groupby("category").size().sort_values(ascending=False)
    # Relax min_rows_per_category if the dataset is small (e.g. test fixtures)
    qualifying = cat_counts[cat_counts >= config.min_rows_per_category]
    if len(qualifying) < config.min_categories:
        qualifying = cat_counts  # take whatever is available
    selected_cats = qualifying.head(config.max_categories).index.tolist()

    # Slice to selected categories
    pilot_df = country_df[country_df["category"].isin(selected_cats)]

    # 50/50 store split (deterministic)
    stores = sorted(pilot_df["store_id"].unique())
    mid = len(stores) // 2 or 1
    control_stores = stores[:mid]
    treatment_stores = stores[mid:]

    date_min = str(pilot_df["date"].min())
    date_max = str(pilot_df["date"].max())

    return PilotCohort(
        country=country,
        categories=selected_cats,
        control_stores=list(control_stores),
        treatment_stores=list(treatment_stores),
        row_count=len(pilot_df),
        date_range=(date_min, date_max),
    )


def _prepare_pilot_frame(df: pd.DataFrame, cohort: PilotCohort) -> pd.DataFrame:
    scoped = df[
        (df["country"] == cohort.country)
        & (df["category"].isin(cohort.categories))
        & (
            df["store_id"].isin(cohort.control_stores)
            | df["store_id"].isin(cohort.treatment_stores)
        )
    ].copy()
    if scoped.empty:
        raise ValueError("Pilot cohort does not match any rows in the dataset")

    scoped["date"] = pd.to_datetime(scoped["date"], errors="coerce")
    if scoped["date"].isna().any():
        raise ValueError("Pilot evaluation requires parseable date values")

    scoped["arm"] = scoped["store_id"].map(
        lambda store_id: (
            "control"
            if store_id in cohort.control_stores
            else "treatment"
            if store_id in cohort.treatment_stores
            else "excluded"
        )
    )
    scoped = scoped[scoped["arm"] != "excluded"].copy()
    scoped["purchase_cost_total"] = scoped["purchase_cost"] * scoped["units_sold"]
    scoped["contribution_margin"] = scoped["net_sales"] - scoped["purchase_cost_total"]
    gross = scoped["gross_sales"].replace(0, float("nan"))
    scoped["gross_to_net_leakage_pct"] = (
        (scoped["gross_sales"] - scoped["net_sales"]) / gross
    ) * 100
    return scoped


def _resolve_intervention_start(
    scoped_df: pd.DataFrame,
    intervention_date: str | None,
) -> pd.Timestamp:
    unique_dates = sorted(scoped_df["date"].dropna().unique())
    if len(unique_dates) < 2:
        raise ValueError("Pilot evaluation requires at least two distinct dates")

    if intervention_date is None:
        return pd.Timestamp(unique_dates[len(unique_dates) // 2])

    parsed = pd.Timestamp(intervention_date)
    if pd.isna(parsed):
        raise ValueError("intervention_date must be a valid date")
    return parsed


def _summarize_arm_period(
    scoped_df: pd.DataFrame,
    *,
    arm: Literal["control", "treatment"],
    period: Literal["pre", "post"],
) -> PilotArmSummary:
    frame = scoped_df[
        (scoped_df["arm"] == arm) & (scoped_df["period"] == period)
    ].copy()
    if frame.empty:
        raise ValueError(f"Pilot evaluation requires non-empty {arm} {period} data")

    row_count = len(frame)
    store_count = int(frame["store_id"].nunique())
    active_days = int(frame["date"].dt.normalize().nunique())
    store_days = max(store_count * active_days, 1)
    gross_sales = float(frame["gross_sales"].sum())
    net_sales = float(frame["net_sales"].sum())
    units_sold = int(frame["units_sold"].sum())
    purchase_cost_total = float(frame["purchase_cost_total"].sum())
    contribution_margin = float(frame["contribution_margin"].sum())
    leakage_pct = (
        ((gross_sales - net_sales) / gross_sales * 100) if gross_sales else 0.0
    )
    purchase_cost_per_unit = purchase_cost_total / units_sold if units_sold else 0.0

    return PilotArmSummary(
        arm=arm,
        period=period,
        row_count=row_count,
        store_count=store_count,
        active_days=active_days,
        start_date=frame["date"].min().date().isoformat(),
        end_date=frame["date"].max().date().isoformat(),
        gross_sales=gross_sales,
        net_sales=net_sales,
        units_sold=units_sold,
        purchase_cost_total=purchase_cost_total,
        contribution_margin=contribution_margin,
        gross_to_net_leakage_pct=leakage_pct,
        net_sales_per_store_day=net_sales / store_days,
        units_sold_per_store_day=units_sold / store_days,
        contribution_margin_per_store_day=contribution_margin / store_days,
        purchase_cost_per_unit=purchase_cost_per_unit,
    )


def _pct_change(post_value: float, pre_value: float) -> float | None:
    if pre_value == 0:
        return None
    return ((post_value - pre_value) / abs(pre_value)) * 100


def _build_metric_impact(
    metric: str,
    direction: Literal["higher_is_better", "lower_is_better"],
    control_pre: float,
    control_post: float,
    treatment_pre: float,
    treatment_post: float,
) -> PilotMetricImpact:
    control_change = control_post - control_pre
    treatment_change = treatment_post - treatment_pre
    incremental_lift = treatment_change - control_change
    incremental_lift_pct = None
    if treatment_pre != 0:
        incremental_lift_pct = (incremental_lift / abs(treatment_pre)) * 100

    favorable_movement = (
        incremental_lift > 0
        if direction == "higher_is_better"
        else incremental_lift < 0
    )
    return PilotMetricImpact(
        metric=metric,
        direction=direction,
        control_pre=control_pre,
        control_post=control_post,
        treatment_pre=treatment_pre,
        treatment_post=treatment_post,
        control_change=control_change,
        treatment_change=treatment_change,
        control_change_pct=_pct_change(control_post, control_pre),
        treatment_change_pct=_pct_change(treatment_post, treatment_pre),
        incremental_lift=incremental_lift,
        incremental_lift_pct=incremental_lift_pct,
        favorable_movement=favorable_movement,
    )


def evaluate_pilot_impact(
    df: pd.DataFrame,
    cohort: PilotCohort | None = None,
    *,
    intervention_date: str | None = None,
) -> PilotImpactReport:
    """Measure pre/post pilot impact using a control-versus-treatment design."""
    if cohort is None:
        cohort = select_pilot_cohort(df)

    scoped = _prepare_pilot_frame(df, cohort)
    intervention_start = _resolve_intervention_start(scoped, intervention_date)
    scoped["period"] = scoped["date"].map(
        lambda value: "pre" if value < intervention_start else "post"
    )

    if "pre" not in set(scoped["period"]) or "post" not in set(scoped["period"]):
        raise ValueError("Pilot evaluation requires both pre and post periods")

    summaries = [
        _summarize_arm_period(scoped, arm="control", period="pre"),
        _summarize_arm_period(scoped, arm="control", period="post"),
        _summarize_arm_period(scoped, arm="treatment", period="pre"),
        _summarize_arm_period(scoped, arm="treatment", period="post"),
    ]
    summary_map = {(summary.arm, summary.period): summary for summary in summaries}

    metric_impacts = [
        _build_metric_impact(
            "net_sales_per_store_day",
            "higher_is_better",
            summary_map[("control", "pre")].net_sales_per_store_day,
            summary_map[("control", "post")].net_sales_per_store_day,
            summary_map[("treatment", "pre")].net_sales_per_store_day,
            summary_map[("treatment", "post")].net_sales_per_store_day,
        ),
        _build_metric_impact(
            "contribution_margin_per_store_day",
            "higher_is_better",
            summary_map[("control", "pre")].contribution_margin_per_store_day,
            summary_map[("control", "post")].contribution_margin_per_store_day,
            summary_map[("treatment", "pre")].contribution_margin_per_store_day,
            summary_map[("treatment", "post")].contribution_margin_per_store_day,
        ),
        _build_metric_impact(
            "purchase_cost_per_unit",
            "lower_is_better",
            summary_map[("control", "pre")].purchase_cost_per_unit,
            summary_map[("control", "post")].purchase_cost_per_unit,
            summary_map[("treatment", "pre")].purchase_cost_per_unit,
            summary_map[("treatment", "post")].purchase_cost_per_unit,
        ),
        _build_metric_impact(
            "gross_to_net_leakage_pct",
            "lower_is_better",
            summary_map[("control", "pre")].gross_to_net_leakage_pct,
            summary_map[("control", "post")].gross_to_net_leakage_pct,
            summary_map[("treatment", "pre")].gross_to_net_leakage_pct,
            summary_map[("treatment", "post")].gross_to_net_leakage_pct,
        ),
    ]
    primary_metric = next(
        impact
        for impact in metric_impacts
        if impact.metric == "net_sales_per_store_day"
    )

    pre_dates = scoped.loc[scoped["period"] == "pre", "date"]
    post_dates = scoped.loc[scoped["period"] == "post", "date"]
    return PilotImpactReport(
        cohort=cohort,
        intervention_start_date=intervention_start.date().isoformat(),
        pre_period=(
            pre_dates.min().date().isoformat(),
            pre_dates.max().date().isoformat(),
        ),
        post_period=(
            post_dates.min().date().isoformat(),
            post_dates.max().date().isoformat(),
        ),
        arm_summaries=summaries,
        metric_impacts=metric_impacts,
        primary_metric=primary_metric.metric,
        primary_incremental_lift=primary_metric.incremental_lift,
        primary_incremental_lift_pct=primary_metric.incremental_lift_pct,
    )
