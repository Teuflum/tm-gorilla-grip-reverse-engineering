"""Print position-aligned recovery metrics for the FL-last ice jump."""

import csv
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
paths = sorted((ROOT / "outputs").glob("automated_jump3_left_*.csv"))
paths.extend(sorted((ROOT / "outputs").glob("automated_last_fl_*.csv")))
paths.append(sorted((ROOT / "outputs").glob("automated_baseline_right_*.csv"))[-1])

for path in paths:
    with path.open(newline="", encoding="utf-8-sig") as source:
        rows = list(csv.DictReader(source))
    run = max(int(row["run"]) for row in rows)
    rows = [row for row in rows if int(row["run"]) == run]
    region = [row for row in rows if 870 < float(row["px"]) < 915 and 590 < float(row["pz"]) < 610]
    if not region:
        print(path.stem, "jump3 landing missed")
        continue
    first_ground = next((row for row in region if row["ground"] == "1" and int(row["time_ms"]) > 10300), None)
    if first_ground is None:
        print(path.stem, "no landing")
        continue
    def speed(row):
        return 3.6 * math.sqrt(sum(float(row[k]) ** 2 for k in ("vx", "vy", "vz")))
    measures = {x: min(region, key=lambda row: abs(float(row["px"]) - x)) for x in (910, 905, 900, 895, 890, 880)}
    print(path.stem, "land", first_ground["time_ms"], first_ground["px"],
          round(speed(first_ground), 2),
          "speeds", {x: (round(speed(row), 2), row["time_ms"]) for x, row in measures.items()})
