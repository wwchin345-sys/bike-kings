"""
STEP 3 — refuse to publish something broken.

This runs before every commit. If it raises, the workflow stops and the live
site keeps yesterday's good data instead of getting today's bad data.

Add your own checks as you learn what "wrong" looks like for your dataset.
"""
import json
import sys

import pandas as pd

from common import DATA, load_config


def validate():
    cfg = load_config()
    path = DATA / "site_data.csv"

    if not path.exists():
        raise SystemExit("FAIL: data/site_data.csv does not exist")

    df = pd.read_csv(path)
    problems = []

    if df.empty:
        problems.append("the dataset is empty")

    for col in (cfg["label_column"], cfg["value_column"]):
        if col not in df.columns:
            problems.append(f"missing required column: {col}")

    if cfg["label_column"] in df.columns and df[cfg["label_column"]].isna().any():
        problems.append("some rows have no label")

    # The derived columns the page is built from. If transform.py stops
    # producing one, the table quietly loses a column instead of failing.
    for col in ("lane_miles_added", "crashes_per_10k_before",
                "crashes_per_10k_after", "crash_rate_change_pct"):
        if col not in df.columns:
            problems.append(f"missing derived column: {col}")

    # The bar chart scales each row against the largest value and cannot draw
    # a negative bar, so a sign flip upstream has to stop the run.
    value_col = cfg["value_column"]
    if value_col in df.columns:
        values = pd.to_numeric(df[value_col], errors="coerce")
        if values.isna().any():
            problems.append(f"{value_col} has values that are not numbers")
        elif (values < 0).any():
            problems.append(
                f"{value_col} has negative values — the chart cannot draw them, "
                "and a traffic decline below zero means traffic went up"
            )
        elif values.max() > 90:
            problems.append(
                f"{value_col} tops out at {values.max()}% — a drop that large "
                "is a unit error, not a real change in traffic"
            )

    # A crash rate of zero means the division in transform.py lost its
    # denominator; publishing it would read as "nobody crashed here".
    for col in ("crashes_per_10k_before", "crashes_per_10k_after"):
        if col in df.columns:
            rates = pd.to_numeric(df[col], errors="coerce")
            if (rates <= 0).any() or rates.isna().any():
                problems.append(f"{col} has values that are zero, missing, or negative")

    # Guard against a broken source silently gutting the site.
    meta_path = DATA / "meta.json"
    if meta_path.exists():
        previous = json.loads(meta_path.read_text(encoding="utf-8")).get("rows")
        if previous and len(df) < previous * 0.5:
            problems.append(
                f"row count fell from {previous} to {len(df)} — "
                "that looks like a broken source, not real change"
            )

    if problems:
        print("VALIDATION FAILED:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        raise SystemExit(1)

    print(f"validation passed: {len(df)} rows")
    return df


if __name__ == "__main__":
    validate()
