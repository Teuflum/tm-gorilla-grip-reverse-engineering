"""Compare short_hop_lead_trials.py runs of one hop against its latest switch.

For each lead the newest run whose input still matches variant() is used.
Positions are projected onto the reference path; "ahead" at a race time is the
arc-length difference, also given in ms at the reference speed there. The
race times are fixed, so every run has had the same inputs up to that moment.

The reference is lead 0, the latest switch (on hop A it lands on the takeoff
tick itself and the Trainer grades it S+), except on hop B: there any switch much
later than Teuflum's own (nominal 610) sends the car off the ramp, so that run is
the reference.

Usage: py -3 analyze_short_hop_lead.py a|b|f
"""

from __future__ import annotations

import json
import math
import re
import sys

from analyze_countersteer_lead import Path3, interpolate, load
from short_hop_lead_trials import HOPS, trials, variant


sys.stdout.reconfigure(encoding="utf-8")
OUT = trials.OUT
# Race times compared, all after the reference run's front touchdown (or stand-in).
REFERENCE = {"a": 0, "b": 610, "f": 0}
COMPARE_AT = {
    "a": (13600, 13800, 14100, 14500, 15000),
    "b": (20600, 20800, 21000, 21500),
    "f": (19400, 19600, 19800, 20000, 20300),
}


def monotonic_projection(path: Path3, rows: list[dict]) -> list[tuple]:
    """(race ms, speed, arc length, distance off the line), projected in time order."""
    out, last = [], None
    for row in rows:
        p = (row["x"], row["y"], row["z"])
        best = (math.inf, math.nan)
        for i, (a, b) in enumerate(zip(path.points, path.points[1:])):
            if last is not None and not (last - 10 <= path.arc[i] <= last + 15):
                continue
            d = [bj - aj for aj, bj in zip(a, b)]
            length2 = sum(c * c for c in d) or 1e-9
            t = max(0.0, min(1.0, sum((pj - aj) * dj for pj, aj, dj in zip(p, a, d)) / length2))
            off = math.dist([aj + t * dj for aj, dj in zip(a, d)], p)
            if off < best[0]:
                best = (off, path.arc[i] + t * math.sqrt(length2))
        if not math.isnan(best[1]):
            last = best[1]
        out.append((row["race_ms"], row["speed_kmh"], best[1], best[0]))
    return out


def lead_of(name: str) -> int:
    return int(re.match(r"[abf]_lead([-+]\d+)$", name)[1])


def main() -> None:
    hop = sys.argv[1]
    runs = [json.loads(line) for line in (OUT / "summaries.jsonl").read_text(encoding="utf-8").splitlines()]
    runs = [r for r in runs if r["hop"] == hop and r["variant"].startswith(f"{hop}_lead")
            and r["script"] == variant(hop, lead_of(r["variant"])) and not r["override"]]
    best: dict[int, dict] = {}
    for r in runs:  # newest run per nominal lead
        best[lead_of(r["variant"])] = r
    zero = [r for r in runs if lead_of(r["variant"]) == REFERENCE[hop]]
    reference = zero[0]
    csv_of = lambda r: OUT / f"{r['variant']}_{r['run']}.csv"
    path = Path3(load(csv_of(reference)))
    ref = monotonic_projection(path, load(csv_of(reference)))
    rows = []
    for nominal in sorted(best, key=lambda n: (n < 0, n)):
        r = best[nominal]
        track = monotonic_projection(path, load(csv_of(r)))
        row = {"nominal": nominal, "lead_ms": r.get("lead_ms"), "grade": r.get("grade", "-"),
               "switch_to_front_ms": r.get("switch_to_front_ms"), "airtime_ms": r.get("airtime_ms"),
               "landing_slip_deg": r.get("landing_slip_deg"), "force_takeoff": r.get("force_takeoff")}
        for dt in (0, 100, 200, 300, 400):
            row[f"force+{dt}"] = r.get(f"force_front+{dt}")
        full = r.get("full_force_ms")
        row["full_after_front_ms"] = None if full is None or "front_touch_ms" not in r else full - r["front_touch_ms"]
        row["speed_takeoff_kmh"] = r.get("speed_takeoff_kmh")
        row["lost_at_takeoff_kmh"] = round(reference["speed_takeoff_kmh"] - r["speed_takeoff_kmh"], 2) \
            if "speed_takeoff_kmh" in r else None
        for t in COMPARE_AT[hop]:
            ahead = interpolate(track, t, 2) - interpolate(ref, t, 2)
            row[f"ahead@{t}_m"] = round(ahead, 2)
            row[f"ahead@{t}_ms"] = round(1000 * ahead / (interpolate(ref, t, 1) / 3.6))
            row[f"speed@{t}"] = round(interpolate(track, t, 1), 1)
            row[f"off@{t}_m"] = round(interpolate(track, t, 3), 1)
        row["runs"] = sum(1 for x in runs if lead_of(x["variant"]) == nominal)
        rows.append(row)
    if len(zero) > 1:
        again = monotonic_projection(path, load(csv_of(zero[-1])))
        t = COMPARE_AT[hop][-1]
        print(f"reference repeat: takeoff speed {zero[-1].get('speed_takeoff_kmh')} vs {reference.get('speed_takeoff_kmh')}, "
              f"position at {t} differs by {interpolate(again, t, 2) - interpolate(ref, t, 2):.3f} m")
    (OUT / f"summary_{hop}.json").write_text(json.dumps(rows, indent=1), encoding="utf-8")
    keys = list(rows[0])
    print("\t".join(keys))
    for row in rows:
        print("\t".join(str(row[k]) for k in keys))


if __name__ == "__main__":
    main()
