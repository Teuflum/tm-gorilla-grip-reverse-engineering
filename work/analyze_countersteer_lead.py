"""Summarize countersteer_lead_trials.py runs: speed and time after the 11.31 s jump.

Reads outputs/countersteer_lead/*.csv (TICK telemetry) and the matching .log
(Gorilla Grip Trainer lines). Positions are projected onto the path of the
first lead-0 run, so "time to reach a point" means the same place on the track
for every variant even when the takeoff heading differs. Prints one row per run
and writes summary.json next to the inputs.
"""

from __future__ import annotations

import csv
import json
import math
import re
import sys
from pathlib import Path


sys.stdout.reconfigure(encoding="utf-8")
OUT = Path(__file__).resolve().parent.parent / "outputs/countersteer_lead"
# Distances along the reference path, measured from its touchdown point.
AFTER_TOUCHDOWN_M = (10, 30, 60)
# Every variant is still airborne here, so its progress deficit is the cost
# carried out of the takeoff, before the landing angle changes the slide.
LAST_AIR_MS = 12560


def trainer_facts(log: str) -> dict:
    verdicts = re.findall(r"verdict at \d+ms: (\S+) \|.*?\| force ([\d.]+) \|.*?"
                          r"takeoff (\d+)ms \| landing (\d+)ms \| lead (-?\d+)ms", log)
    jump = next((v for v in verdicts if 11200 <= int(v[2]) <= 11400), None)
    if jump is None:
        return {}
    grade, force, takeoff, landing, lead = jump
    return {"grade": grade, "force": float(force), "takeoff_ms": int(takeoff),
            "landing_ms": int(landing), "lead_ms": int(lead)}


def load(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as handle:
        return [{k: float(v) for k, v in row.items()} for row in csv.DictReader(handle)]


def interpolate(points: list[tuple], ms: float, index: int) -> float:
    for a, b in zip(points, points[1:]):
        if a[0] <= ms <= b[0]:
            return a[index] + (ms - a[0]) / (b[0] - a[0]) * (b[index] - a[index])
    return math.nan


class Path3:
    """Polyline of the reference run, for arc length and distance off the line."""

    def __init__(self, rows: list[dict]) -> None:
        self.points = [(r["x"], r["y"], r["z"]) for r in rows]
        self.arc = [0.0]
        for a, b in zip(self.points, self.points[1:]):
            self.arc.append(self.arc[-1] + math.dist(a, b))

    def project(self, p: tuple) -> tuple[float, float]:
        best = (math.inf, math.nan)
        for i, (a, b) in enumerate(zip(self.points, self.points[1:])):
            d = [bj - aj for aj, bj in zip(a, b)]
            length2 = sum(c * c for c in d)
            t = max(0.0, min(1.0, sum((pj - aj) * dj for pj, aj, dj in zip(p, a, d)) / length2))
            q = [aj + t * dj for aj, dj in zip(a, d)]
            off = math.dist(q, p)
            if off < best[0]:
                best = (off, self.arc[i] + t * math.sqrt(length2))
        return best


def summarize(path: Path, reference: Path3, reference_landing_s: float) -> dict:
    rows = load(path)
    facts = trainer_facts(path.with_suffix(".log").read_text(encoding="utf-8"))
    result = {"variant": path.stem.rsplit("_", 1)[0], "run": path.stem.rsplit("_", 1)[1], **facts}
    if not facts:
        return result
    # (race ms, speed, velocity heading, arc length, distance off the reference line)
    track = [(r["race_ms"], r["speed_kmh"], math.degrees(math.atan2(r["vx"], r["vz"])),
              *reversed(reference.project((r["x"], r["y"], r["z"])))) for r in rows]
    takeoff, landing = facts["takeoff_ms"], facts["landing_ms"]
    result["speed_takeoff_kmh"] = round(interpolate(track, takeoff, 1), 2)
    result["heading_takeoff_deg"] = round(interpolate(track, takeoff, 2), 2)
    result["speed_landing_kmh"] = round(interpolate(track, landing, 1), 2)
    result["off_line_landing_m"] = round(interpolate(track, landing, 4), 2)
    result["arc_last_air_m"] = interpolate(track, LAST_AIR_MS, 3)
    slips = re.findall(r"snapshot at (\d+)ms: .*?contacts (\d{4}).*?slip (\d+)",
                       path.with_suffix(".log").read_text(encoding="utf-8"))
    first_touch = next((s for s in slips if landing - 30 <= int(s[0]) <= landing + 60 and s[1] != "0000"), None)
    result["landing_slip_deg"] = int(first_touch[2]) if first_touch else None
    for metres in AFTER_TOUCHDOWN_M:
        target = reference_landing_s + metres
        for a, b in zip(track, track[1:]):
            if a[0] >= takeoff and a[3] <= target < b[3]:
                f = (target - a[3]) / (b[3] - a[3])
                result[f"t_{metres}m"] = round(a[0] + f * (b[0] - a[0]), 1)
                result[f"v_{metres}m"] = round(a[1] + f * (b[1] - a[1]), 2)
                result[f"off_{metres}m"] = round(a[4] + f * (b[4] - a[4]), 2)
                break
    return result


def main() -> None:
    paths = sorted(OUT.glob("shift_*.csv"), key=lambda p: p.stat().st_mtime)
    reference_path = next(p for p in paths if p.stem.startswith("shift_000"))
    reference = Path3(load(reference_path))
    landing = trainer_facts(reference_path.with_suffix(".log").read_text(encoding="utf-8"))["landing_ms"]
    rows = load(reference_path)
    reference_landing_s = interpolate(
        [(r["race_ms"], reference.project((r["x"], r["y"], r["z"]))[1]) for r in rows], landing, 1)
    results = [summarize(p, reference, reference_landing_s) for p in paths]
    results.sort(key=lambda r: (r.get("lead_ms", 999), r["run"]))
    zero = next(r for r in results if r.get("lead_ms") == 0)
    for r in results:
        for metres in AFTER_TOUCHDOWN_M:
            if f"t_{metres}m" in r:
                r[f"lost_{metres}m_ms"] = round(r[f"t_{metres}m"] - zero[f"t_{metres}m"], 1)
        r["takeoff_speed_lost_kmh"] = round(zero["speed_takeoff_kmh"] - r["speed_takeoff_kmh"], 2)
    for r in results:
        r["behind_last_air_m"] = round(zero["arc_last_air_m"] - r["arc_last_air_m"], 2)
    for r in results:
        r["arc_last_air_m"] = round(r["arc_last_air_m"], 2)
    (OUT / "summary.json").write_text(json.dumps(results, indent=1), encoding="utf-8")
    keys = ["lead_ms", "grade", "force", "speed_takeoff_kmh", "takeoff_speed_lost_kmh",
            "behind_last_air_m", "landing_slip_deg", "off_line_landing_m"] + \
           [f"{k}_{m}m{s}" for m in AFTER_TOUCHDOWN_M for k, s in (("lost", "_ms"), ("v", ""), ("off", ""))]
    print("\t".join(keys))
    for r in results:
        print("\t".join(str(r.get(k, "")) for k in keys))


if __name__ == "__main__":
    main()
