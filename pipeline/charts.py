"""
Chart geometry for the page. Part of STEP 4 — this computes coordinates only.

The SVG markup itself lives in templates/index.html, so the page stays editable
where you would expect to edit it. Everything here is arithmetic: scales, ticks,
and pixel positions.

Colours are not chosen here either. The template reads them from CSS custom
properties so light and dark mode each get their own validated step.
"""


def _nice_ceiling(value):
    """Round a maximum up to a clean axis top: 1, 2, 2.5 or 5 x a power of ten."""
    if value <= 0:
        return 1.0
    power = 10 ** (len(str(int(value))) - 1)
    for step in (1, 1.2, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10):
        top = step * power
        if top >= value:
            return float(top)
    return float(10 * power)


def _ticks(top, count=4):
    return [round(top * i / count, 2) for i in range(count + 1)]


def _fmt(n):
    return f"{n:g}"


def scatter(df, x_col, y_col, label_col, width=640, height=360):
    """Lane miles against traffic decline — does more lane mean less traffic?"""
    pad_l, pad_r, pad_t, pad_b = 54, 18, 18, 46
    plot_w = width - pad_l - pad_r
    plot_h = height - pad_t - pad_b

    x_top = _nice_ceiling(df[x_col].max())
    y_top = _nice_ceiling(df[y_col].max())

    def px(v):
        return round(pad_l + (v / x_top) * plot_w, 1)

    def py(v):
        return round(pad_t + plot_h - (v / y_top) * plot_h, 1)

    # Label only the two extremes. A label on all 18 is noise.
    hi = df[y_col].idxmax()
    lo = df[y_col].idxmin()

    points = []
    for i, row in df.iterrows():
        x, y = px(row[x_col]), py(row[y_col])
        points.append({
            "x": x,
            "y": y,
            "name": row[label_col],
            "label": row[label_col] if i in (hi, lo) else None,
            # Keep an end label from running off the right edge.
            "anchor": "end" if x > pad_l + plot_w * 0.72 else "start",
            "dx": -10 if x > pad_l + plot_w * 0.72 else 10,
            "title": (f"{row[label_col]}: {_fmt(row[x_col])} lane miles added, "
                      f"car traffic down {_fmt(row[y_col])}%"),
        })

    return {
        "width": width, "height": height,
        "plot": {"x": pad_l, "y": pad_t, "w": plot_w, "h": plot_h},
        "points": points,
        "x_ticks": [{"v": _fmt(t), "px": px(t)} for t in _ticks(x_top)],
        "y_ticks": [{"v": _fmt(t), "py": py(t)} for t in _ticks(y_top)],
        "baseline_y": py(0),
    }


def dumbbell(df, before_col, after_col, label_col, width=640, row_h=22):
    """Crash rate before against after — the comparison that carries the finding."""
    label_w, pad_r, pad_t, pad_b = 118, 56, 36, 10
    rows_n = len(df)
    height = pad_t + rows_n * row_h + pad_b
    plot_w = width - label_w - pad_r

    top = _nice_ceiling(max(df[before_col].max(), df[after_col].max()))

    def px(v):
        return round(label_w + (v / top) * plot_w, 1)

    rows = []
    for n, (_, row) in enumerate(df.iterrows()):
        y = pad_t + n * row_h + row_h / 2
        before, after = row[before_col], row[after_col]
        change = after - before
        rows.append({
            "y": round(y, 1),
            "name": row[label_col],
            "x_before": px(before),
            "x_after": px(after),
            "after_is_higher": after > before,
            # "+0.0" reads as a rise that is not there.
            "delta": "0.0" if round(change, 1) == 0 else f"{change:+.1f}",
            "title": (f"{row[label_col]}: {_fmt(before)} crashes per 10,000 daily "
                      f"car trips before, {_fmt(after)} after ({change:+.1f})"),
        })

    return {
        "width": width, "height": height, "row_h": row_h,
        "plot": {"x": label_w, "y": pad_t, "w": plot_w,
                 "h": rows_n * row_h},
        "rows": rows,
        "x_ticks": [{"v": _fmt(t), "px": px(t)} for t in _ticks(top)],
        "value_x": width - pad_r + 10,
    }


def headline_stats(df):
    """The three numbers the page is actually about."""
    decline = df["traffic_decline_pct"]
    change = df["crash_rate_change_pct"]
    fell = int((change < 0).sum())
    return [
        {"label": "Average fall in car traffic",
         "value": f"{decline.mean():.1f}%",
         "note": f"across {len(df)} cities, from {decline.min():.1f}% to "
                 f"{decline.max():.1f}%"},
        {"label": "Average change in crashes per car",
         "value": f"{change.mean():+.1f}%",
         "note": "crashes per 10,000 daily car trips, before against after"},
        {"label": "Cities where the crash rate fell",
         "value": f"{fell} of {len(df)}",
         "note": "close to the half you would expect from chance alone"},
    ]
