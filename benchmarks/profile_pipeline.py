from __future__ import annotations

import cProfile
import json
import pstats
import time
from pathlib import Path

from dashboard_data import generate_demo_bundle


OUTPUT_DIR = Path("benchmarks/results")
PROFILE_PATH = OUTPUT_DIR / "pipeline.prof"
SUMMARY_PATH = OUTPUT_DIR / "pipeline_summary.json"
STATS_PATH = OUTPUT_DIR / "pipeline_stats.txt"


def run_profile() -> dict:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    profiler = cProfile.Profile()
    start = time.perf_counter()
    profiler.enable()
    bundle = generate_demo_bundle(num_orders=2500, seed=42, num_quality_incidents=150)
    profiler.disable()
    duration = time.perf_counter() - start

    profiler.dump_stats(str(PROFILE_PATH))

    stats = pstats.Stats(profiler)
    stats.sort_stats("cumulative")
    with STATS_PATH.open("w", encoding="utf-8") as handle:
        stats.stream = handle
        stats.print_stats(40)

    summary = {
        "duration_seconds": duration,
        "total_spend": bundle["insights"]["total_spend"],
        "total_savings": bundle["insights"]["total_savings"],
        "forecast_rows": len(bundle["analytics"]["demand_forecast"]),
        "anomaly_rows": int(bundle["analytics"]["purchase_order_anomalies"]["is_anomaly"].sum()),
    }
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


if __name__ == "__main__":
    summary = run_profile()
    print(json.dumps(summary, indent=2))