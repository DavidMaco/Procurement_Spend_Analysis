from benchmarks.profile_pipeline import run_profile


def test_profile_pipeline_returns_summary():
    summary = run_profile()
    assert summary["duration_seconds"] > 0
    assert summary["total_spend"] > 0
    assert summary["total_savings"] >= 0
