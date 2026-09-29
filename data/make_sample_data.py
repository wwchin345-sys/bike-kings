import random, statistics

cities = ["Portland","Minneapolis","Denver","Austin","Seattle","Boston","Pittsburgh",
          "Columbus","Sacramento","Nashville","Raleigh","Tucson","Milwaukee","Omaha",
          "Albuquerque","Fresno","Louisville","Oklahoma City"]

def corr(a, b):
    ma, mb = statistics.mean(a), statistics.mean(b)
    num = sum((x-ma)*(y-mb) for x, y in zip(a, b))
    den = (sum((x-ma)**2 for x in a) * sum((y-mb)**2 for y in b)) ** 0.5
    return num / den if den else 0.0

def build(seed):
    rnd = random.Random(seed)
    rows = []
    for c in cities:
        lanes = round(rnd.uniform(1.5, 24.0), 1)
        before = rnd.randrange(38_000, 210_000, 500)
        decline = min(max(0.0038 * lanes + rnd.uniform(-0.012, 0.030), 0.015), 0.16)
        after = int(round(before * (1 - decline) / 100.0) * 100)
        rate_before = rnd.uniform(9.0, 26.0) / 10_000
        # Crash RATE is flat: the after-rate is the before-rate nudged either
        # way, centred on no change and independent of how much lane went in.
        rate_after = rate_before * rnd.uniform(0.94, 1.06)
        rows.append((c, lanes, before, after,
                     max(6, round(before * rate_before)),
                     max(6, round(after * rate_after))))
    lanes_col = [r[1] for r in rows]
    change = [((r[5]/(r[3]/10_000)) - (r[4]/(r[2]/10_000))) / (r[4]/(r[2]/10_000)) * 100
              for r in rows]
    return rows, statistics.mean(change), corr(lanes_col, change), sum(1 for x in change if x < 0)

# Pick a seed where the crash rate is genuinely flat and unrelated to lane miles.
for seed in range(1, 6000):
    rows, mean_chg, r, fell = build(seed)
    if abs(mean_chg) < 0.25 and abs(r) < 0.08 and 7 <= fell <= 11:
        break

rows.sort(key=lambda x: -x[1])
head = "label,lane_miles_added,car_trips_daily_before,car_trips_daily_after,crashes_before,crashes_after"
open("data/source.csv", "w", newline="\n", encoding="utf-8").write(
    "\n".join([head] + [",".join(str(x) for x in r) for r in rows]) + "\n")
print(f"seed={seed}  mean crash-rate change {mean_chg:+.2f}%  "
      f"corr(lanes, change)={r:+.2f}  fell in {fell}/18")
