"""
STEP 4 — render the site from the data.

Reads templates/index.html, fills it in, and writes site/. The site folder is
generated output: edit the template, not the result.
"""
import json
import shutil

import pandas as pd
from jinja2 import Template

import charts
from common import DATA, SITE, TEMPLATES, load_config


def build():
    cfg = load_config()
    df = pd.read_csv(DATA / "site_data.csv")
    meta = json.loads((DATA / "meta.json").read_text(encoding="utf-8"))

    rows = df.to_dict(orient="records")
    values = df[cfg["value_column"]].tolist()

    # Sorted by the highest after-rate so the dumbbell reads as a ranking
    # rather than inheriting the bar chart's order.
    by_rate = df.sort_values("crashes_per_10k_after", ascending=False)

    html = Template((TEMPLATES / "index.html").read_text(encoding="utf-8")).render(
        cfg=cfg,
        meta=meta,
        rows=rows,
        columns=list(df.columns),
        label_col=cfg["label_column"],
        value_col=cfg["value_column"],
        max_value=max(values) if values else 1,
        data_json=json.dumps(rows),
        stats=charts.headline_stats(df),
        scatter=charts.scatter(df, "lane_miles_added",
                               "traffic_decline_pct", cfg["label_column"]),
        dumbbell=charts.dumbbell(by_rate, "crashes_per_10k_before",
                                 "crashes_per_10k_after", cfg["label_column"]),
        corr=round(df["lane_miles_added"].corr(df["traffic_decline_pct"]), 2),
    )

    SITE.mkdir(exist_ok=True)
    (SITE / "index.html").write_text(html, encoding="utf-8")

    # The raw data, downloadable from the site.
    shutil.copy(DATA / "site_data.csv", SITE / "data.csv")

    for asset in ("favicon.svg", "preview.png"):
        src = TEMPLATES / asset
        if src.exists():
            shutil.copy(src, SITE / asset)

    print(f"built site/index.html from {len(rows)} rows")


if __name__ == "__main__":
    build()
