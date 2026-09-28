"""Compare jump1_lead_trials.py runs with the landing angle matched.

For each lead the run whose landing slip came closest to the lead-0 reference
is used. Distances are measured along the reference path. "Behind in the air"
is taken at LAST_AIR_MS, when every variant is still airborne, so it is the
cost carried out of the takeoff. Points after touchdown are not compared by
position: earlier switches make the jump shorter and land metres away from
the reference line.

Usage: py -3 analyze_jump1_lead.py [reference run id]
"""

from __future__ import annotations

import json
import math
import re
import sys

from analyze_countersteer_lead import Path3, interpolate, load
from jump1_lead_trials import trials, variant


sys.stdout.reconfigure(encoding="utf-8")
OUT = trials.OUT
LAST_AIR_MS = 6070


def script_of(name: str) -> str:
    """Rebuild a run's input from its name, to drop runs made by older variant code."""
    lead, air, hold = re.match(r"lead(\d+)_air([-+]\d+)(?:_for(\d+))?$", name).groups()
    return variant(int(lead), int(air), int(hold or 0))


def monotonic_projection(path: Path3, rows: list[dict]) -> list[tuple]:
    """(race ms, speed, arc length, distance off the line), projected in time order.

    Only segments near the previous arc length are searched: the spin brings the
    car back near earlier parts of the path, where a plain nearest point jumps.
    """
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


def main() -> None:
    runs = [json.loads(line) for line in (OUT / "summaries.jsonl").read_text(encoding="utf-8").splitlines()]
    runs = [r for r in runs if r["variant"].startswith("lead") and "landing_slip_deg" in r
            and r["script"] == script_of(r["variant"]) and r["lead_ms"] >= 0]
    reference = next(r for r in runs if r["run"] == sys.argv[1]) if sys.argv[1:] else \
        next(r for r in runs if r["variant"] == "lead000_air+000")
    target = reference["landing_slip_deg"]
    best: dict[str, dict] = {"lead000": reference}
    for r in runs:
        key = r["variant"][:7]
        if key not in best or abs(r["landing_slip_deg"] - target) < abs(best[key]["landing_slip_deg"] - target):
            best[key] = r

    def csv_of(r: dict):
        return OUT / f"{r['variant']}_{r['run']}.csv"

    path = Path3(load(csv_of(reference)))
    ref_track = monotonic_projection(path, load(csv_of(reference)))
    ref_air_s = interpolate(ref_track, LAST_AIR_MS, 2)
    ref_air_speed = interpolate(ref_track, LAST_AIR_MS, 1) / 3.6
    ref_landing_s = interpolate(ref_track, reference["landing_ms"], 2)
    rows = []
    for key in sorted(best):
        r = best[key]
        t = monotonic_projection(path, load(csv_of(r)))
        behind = ref_air_s - interpolate(t, LAST_AIR_MS, 2)
        rows.append({
            "lead_ms": r["lead_ms"], "grade": r["grade"], "air_input": r["variant"][8:],
            "landing_slip_deg": r["landing_slip_deg"], "force": r["force"],
            "takeoff_ms": r["takeoff_ms"], "landing_ms": r["landing_ms"],
            "speed_takeoff_kmh": r["speed_takeoff_kmh"],
            "takeoff_speed_lost_kmh": round(reference["speed_takeoff_kmh"] - r["speed_takeoff_kmh"], 2),
            "behind_in_air_m": round(behind, 2),
            "behind_in_air_ms": round(1000 * behind / ref_air_speed),
            "landing_short_m": round(ref_landing_s - interpolate(t, r["landing_ms"], 2), 1),
            "landing_off_line_m": round(interpolate(t, r["landing_ms"], 3), 1),
            "speed_landing_kmh": r["speed_landing_kmh"],
            "speed_land+500": r["speed_land+500"], "speed_land+1000": r["speed_land+1000"],
        })
    (OUT / "summary.json").write_text(json.dumps(rows, indent=1), encoding="utf-8")
    keys = list(rows[0])
    print("\t".join(keys))
    for row in rows:
        print("\t".join(str(row[k]) for k in keys))


if __name__ == "__main__":
    main()
