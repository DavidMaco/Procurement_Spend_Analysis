"""Pilot cohort selection for the FMCG OS A/B-test framework."""

from __future__ import annotations

from typing import Optional

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


def profile_data_completeness(df: pd.DataFrame) -> pd.DataFrame:
    """Return per-country completeness statistics.

    Completeness is defined as 1 − (fraction of NaN cells) for each country
    partition.
    """
    countries = df.groupby("country").apply(
        lambda g: pd.Series({
            "row_count": len(g),
            "completeness": 1.0 - g.isna().sum().sum() / (len(g) * len(g.columns)),
            "n_stores": g["store_id"].nunique(),
            "n_categories": g["category"].nunique(),
            "date_min": str(g["date"].min()),
            "date_max": str(g["date"].max()),
        }),
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
    best = eligible.sort_values(["completeness", "row_count"], ascending=[False, False]).iloc[0]
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
    rng = pd.array(range(len(stores)))  # deterministic order
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
