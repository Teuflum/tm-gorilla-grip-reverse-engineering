"""Predict the tire-force target frame by frame across a plastic section and
compare it with the force the Gorilla Grip Trainer logged on the same replay.

Inputs: a Gorilla Grip Logger CSV (outputs/GorillaGripLogger) and the
Openplanet.log of the same replay with the Trainer's Debug -> "Log trainer
events" and "Log every tire-force change" on. The Trainer logs a snapshot on
every force change, so the last logged force before a frame is its force.

The target is 1 + curve_FA0(x) * s^1.5 (outputs/speed_force_curve.md), with x
the car-local speed across the steered front wheels. The wheel angle is
45 deg * s * a surface factor: the ice-family icing curve (model+0xCF0) when
any wheel is on Ice, Snow or RoadIce, otherwise the other-material curve
(model+0xD40). The script prints both that prediction and one that always
uses the ice curve, and the largest error of each against the logged force.
The curve points match graphs/model.js.

Usage:
  py -3 analyze_plastic_flick.py --csv gorilla_grip_left.csv --csv-run 1
      --log-from 17:14:20 --log-to 17:19:16 --from 7500 --to 8750 [--step 5] [--js]

--js prints the sampled rows as the graphs' PlasticFlickData array instead.
"""

from __future__ import annotations

import argparse
import csv
import math
import re
import sys
from pathlib import Path

ICE_POINTS = [(0, 0), (0.05, 0.6), (0.2, 0.85), (1, 1)]      # model+0xCF0
OTHER_POINTS = [(0, 0), (0.8, 0.3), (0.95, 0.7), (1, 1)]     # model+0xD40
ICE_FAMILY = {3, 21, 74}                                      # Ice, Snow, RoadIce
FULL_LOCK_DEG = 45.0                                          # model+0xDA8
SNAPSHOT = re.compile(r"\[(\d\d:\d\d:\d\d)\.\d+\] \[GorillaGripTrainer\]  Gorilla Grip Trainer "
                      r"snapshot at (-?\d+)ms: .*?, force ([0-9.]+),")


def curve(points: list[tuple[float, float]], x: float) -> float:
    if x <= points[0][0]:
        return points[0][1]
    for (a, fa), (b, fb) in zip(points, points[1:]):
        if x <= b:
            return fa + (fb - fa) * (x - a) / (b - a)
    return points[-1][1]


def target(sideways_ms: float, steer: float) -> float:
    """1 + curve_FA0 (Stadium: (10, 0) to (30, 1) m/s) * s^1.5."""
    return 1 + min(max((sideways_ms - 10) / 20, 0), 1) * abs(steer) ** 1.5


def logged_forces(log: Path, start: str, end: str) -> list[tuple[int, float]]:
    out = []
    for line in log.read_text(encoding="utf-8", errors="replace").splitlines():
        m = SNAPSHOT.search(line)
        if m and start <= m[1] <= end:
            out.append((int(m[2]), float(m[3])))
    return out


def frames(csv_path: Path, run: str, t0: float, t1: float):
    for r in csv.DictReader(csv_path.open(encoding="utf-8")):
        t = float(r["time_ms"])
        if r["run"] != run or not t0 <= t <= t1:
            continue
        v = [float(r[k]) for k in ("vx", "vy", "vz")]
        d = [float(r[k]) for k in ("dirx", "diry", "dirz")]
        u = [float(r[k]) for k in ("upx", "upy", "upz")]
        side = [u[1] * d[2] - u[2] * d[1], u[2] * d[0] - u[0] * d[2], u[0] * d[1] - u[1] * d[0]]
        lateral = sum(a * b for a, b in zip(v, side))
        forward = sum(a * b for a, b in zip(v, d))
        materials = [int(r[k]) for k in ("fl_mat", "fr_mat", "rl_mat", "rr_mat")]
        yield {
            "t": t,
            "speed": math.hypot(lateral, forward),  # m/s in the car's ground plane
            "slip": math.degrees(math.atan2(lateral, forward)),
            "icing": sum(float(r[k]) for k in ("fl_ice", "fr_ice", "rl_ice", "rr_ice")) / 4,
            "ice_family": any(m in ICE_FAMILY for m in materials),
            "materials": materials,
            "steer": float(r["steer"]),
        }


def predict(f: dict, by_material: bool) -> tuple[float, float]:
    """(wheel angle in degrees, target) for a frame."""
    points = ICE_POINTS if f["ice_family"] or not by_material else OTHER_POINTS
    angle = FULL_LOCK_DEG * curve(points, f["icing"]) * -f["steer"]
    sideways = f["speed"] * abs(math.sin(math.radians(f["slip"] - angle)))
    return angle, target(sideways, f["steer"])


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--csv", type=Path, required=True)
    p.add_argument("--csv-run", default="1", help="the CSV's run column for this replay")
    p.add_argument("--log", type=Path, default=Path.home() / "OpenplanetNext" / "Openplanet.log")
    p.add_argument("--log-from", required=True, help="wall time HH:MM:SS of the replay's first log line")
    p.add_argument("--log-to", required=True, help="wall time HH:MM:SS of its last log line")
    p.add_argument("--from", dest="t0", type=float, default=7500)
    p.add_argument("--to", dest="t1", type=float, default=8750)
    p.add_argument("--step", type=int, default=1, help="print every Nth frame")
    p.add_argument("--js", action="store_true")
    a = p.parse_args()

    forces = logged_forces(a.log, a.log_from, a.log_to)
    if not forces:
        sys.exit("no Trainer force snapshots in that wall-time range")
    rows = list(frames(a.csv, a.csv_run, a.t0, a.t1))
    worst = {True: 0.0, False: 0.0}
    printed = []
    for i, f in enumerate(rows):
        before = [force for t, force in forces if t <= f["t"]]
        f["force"] = before[-1] if before else None
        f["angle"], f["target"] = predict(f, True)
        f["target_ice"] = predict(f, False)[1]
        if f["force"] is not None:
            worst[True] = max(worst[True], abs(f["target"] - f["force"]))
            worst[False] = max(worst[False], abs(f["target_ice"] - f["force"]))
        if i % a.step == 0:
            printed.append(f)

    if a.js:
        print("  // [race ms, speed km/h, slip deg, average icing, any wheel on ice-family, logged force]")
        for f in printed:
            print(f"  [{f['t']:.0f}, {f['speed'] * 3.6:.1f}, {f['slip']:.1f}, {f['icing']:.3f}, "
                  f"{int(f['ice_family'])}, {f['force']}],")
        return
    print(" race ms  materials     icing  slip°  wheel°  target  ice-curve  logged")
    for f in printed:
        print(f"{f['t']:8.0f}  {'/'.join(map(str, f['materials'])):12} {f['icing'] * 100:5.0f}%"
              f" {f['slip']:6.1f}  {f['angle']:6.1f}  {f['target']:6.3f}  {f['target_ice']:9.3f}  {f['force']}")
    print(f"{len(rows)} frames. Largest |prediction - logged force|: surface factor by material "
          f"{worst[True]:.3f}, ice curve always {worst[False]:.3f}")


if __name__ == "__main__":
    main()
