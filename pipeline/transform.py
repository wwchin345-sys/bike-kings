"""
STEP 2 — turn raw data into exactly what the site needs.

This is the file you will spend the most time in. Cleaning, filtering,
joining, and computing go here. It must produce two things:

  data/site_data.csv   the published dataset, one row per thing shown
  data/meta.json       row count, update date, and provenance for the footer
"""
from datetime import datetime, timezone

import pandas as pd

from common import DATA, load_config, write_json
from fetch import RAW


def transform():
    cfg = load_config()
    df = pd.read_csv(RAW)

    # --- your work goes here -------------------------------------------
    before, after = "car_trips_daily_before", "car_trips_daily_after"
    required = ["label", before, after, "crashes_before", "crashes_after",
                "lane_miles_added"]
    df = df.dropna(subset=required)
    df = df[df[before] > 0]

    # How much car traffic fell, as a share of the before figure. Positive
    # means traffic went down.
    df["traffic_decline_pct"] = ((df[before] - df[after]) / df[before] * 100).round(1)

    # Crashes per 10,000 daily car trips. This is the number that matters:
    # fewer cars means fewer crashes mechanically, even if nothing got safer,
    # so the raw crash count on its own would flatter the result.
    df["crashes_per_10k_before"] = (df["crashes_before"] / (df[before] / 10_000)).round(1)
    df["crashes_per_10k_after"] = (df["crashes_after"] / (df[after] / 10_000)).round(1)
    df["crash_rate_change_pct"] = (
        (df["crashes_per_10k_after"] - df["crashes_per_10k_before"])
        / df["crashes_per_10k_before"] * 100
    ).round(1)

    df = df[["label", "lane_miles_added", "traffic_decline_pct",
             "crashes_per_10k_before", "crashes_per_10k_after",
             "crash_rate_change_pct"]]
    df = df.sort_values(cfg["value_column"], ascending=False)
    # -------------------------------------------------------------------

    out = DATA / "site_data.csv"
    df.to_csv(out, index=False)

    write_json(DATA / "meta.json", {
        "rows": int(len(df)),
        "updated": datetime.now(timezone.utc).strftime("%B %d, %Y"),
        "updated_iso": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source_name": cfg["source_name"],
        "source_url": cfg["source_url"],
    })

    print(f"wrote {len(df)} rows to data/site_data.csv")
    return df


if __name__ == "__main__":
    transform()
