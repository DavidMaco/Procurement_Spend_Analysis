---
applyTo: "**"
---

# Documentation Standards — Procurement Spend SaaS

## When to Write Documentation

Write or update documentation when:

- Adding a new pipeline stage or data transformation
- Changing database schema or output file formats
- Modifying environment variable requirements
- Adding a new Streamlit page or chart

Do **not** add docstrings or comments to code you did not change.

## Docstring Format (Python)

```python
def calculate_savings(df: pd.DataFrame, baseline: float) -> pd.DataFrame:
    """Calculate cost savings against baseline spend.

    Args:
        df: Spend data with columns [supplier, amount, category].
        baseline: Total baseline spend for comparison.

    Returns:
        DataFrame with savings_absolute and savings_pct columns added.

    Raises:
        ValueError: If df is empty or baseline is zero.
    """
```

## README Updates

Every `README.md` must include:

1. One-sentence product description
2. Local development prerequisites and quickstart commands
3. Environment variable list with type, required/optional, and description
4. Link to full documentation

## Changelog

Add a headline entry to `CHANGELOG.md` for every breaking change, new feature,
and security fix. Format: `## [YYYY-MM-DD] — description`.

## Standards Docs Location

Implementation status lives in `docs/`:

- `STANDARDS_IMPLEMENTATION.md` — which standards are active
- `SKILLS_IMPLEMENTATION.md` — which skills are available
- `ROLLOUT_IMPLEMENTATION.md` — rollout history and next steps
