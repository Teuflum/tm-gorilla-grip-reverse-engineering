"""Early-countersteer trials on the first ice jump (takeoff near 5.26 s).

Reuses the TICK plumbing of countersteer_lead_trials.py with a record window
around this jump. Each run is summarized straight away from TICK telemetry
and the Gorilla Grip Trainer log lines, so a search can tune the air steering
until the landing slip angle matches the lead-0 run.

Usage: py -3 jump1_lead_trials.py --pid <PID> baseline
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path

import countersteer_lead_trials as trials
from tick_client import TickClient


sys.stdout.reconfigure(encoding="utf-8")
trials.RECORD_FROM, trials.RECORD_TO = 4000, 9000
trials.OUT = trials.ROOT / "outputs/jump1_lead"
BASE = [tuple(line.split()) for line in trials.BASELINE.read_text(encoding="utf-8").splitlines()]
ORDER = {"seed": 0, "accel": 1, "brake": 2, "flags": 3, "steer": 4}


def script(changes: dict[tuple[int, str], int | None]) -> str:
    """Baseline with (ms, action) -> value replaced, added, or removed (None)."""
    entries = {(int(ms), action): int(value) for ms, action, value in BASE}
    for key, value in changes.items():
        if value is None:
            entries.pop(key, None)
        else:
            entries[key] = value
    rows = sorted(entries.items(), key=lambda item: (item[0][0], ORDER[item[0][1]]))
    return "".join(f"{ms} {action} {value}\n" for (ms, action), value in rows)


TAKEOFF_MS = 5270
AIR_UNTIL_MS = 5620  # first baseline air-steer change after takeoff


def variant(lead_ms: int, air_steer: int = 0, air_ms: int = 0) -> str:
    """Full left, then steer 104 from 50 ms before the commit until takeoff.

    The smoothed steering crosses +0.1 five ticks after the input, so the mode
    commits lead_ms before the 5270 ms takeoff tick. From takeoff the baseline
    air inputs play, except that air_steer replaces its neutral 5280-5620 ms
    stretch; that is the knob that matches the landing angle. The takeoff tick
    itself still reads 104, or a lead-0 switch would never cross +0.1.
    """
    start = TAKEOFF_MS - 50 - lead_ms
    changes = {(5200, "steer"): None, (5250, "steer"): None, (5260, "steer"): None,
               (5270, "steer"): None, (start, "steer"): 104, (TAKEOFF_MS + 10, "steer"): air_steer}
    if air_ms:
        # Air steering acts like a switch, not a dial: hold it only air_ms, then neutral.
        changes[(TAKEOFF_MS + 10 + air_ms, "steer")] = 0
    return script(changes)


def summarize(csv_path: Path) -> dict:
    import csv
    with csv_path.open(encoding="utf-8") as handle:
        rows = [{k: float(v) for k, v in row.items()} for row in csv.DictReader(handle)]
    log = csv_path.with_suffix(".log").read_text(encoding="utf-8")
    result: dict = {}
    verdict = re.search(r"verdict at \d+ms: (\S+) \|.*?\| force ([\d.]+) \|.*?takeoff (5\d{3})ms \| "
                        r"landing (\d+)ms \| lead (-?\d+)ms", log)
    if verdict:
        result.update(grade=verdict[1], force=float(verdict[2]), takeoff_ms=int(verdict[3]),
                      landing_ms=int(verdict[4]), lead_ms=int(verdict[5]))
    snaps = [(int(t), bits, float(steer), int(slip), int(speed)) for t, steer, bits, speed, slip in re.findall(
        r"snapshot at (\d+)ms: exact true, mode \d, steer ([-\d.]+), contacts (\d{4}).*?speed (\d+), slip (\d+)", log)]
    if "landing_ms" in result:
        landing = result["landing_ms"]
        touch = [s for s in snaps if landing - 30 <= s[0] <= landing + 60 and s[1] != "0000"]
        result["landing_slip_deg"] = touch[0][3] if touch else None
    def at(ms: float, key: str) -> float:
        for a, b in zip(rows, rows[1:]):
            if a["race_ms"] <= ms <= b["race_ms"]:
                return a[key] + (ms - a["race_ms"]) / (b["race_ms"] - a["race_ms"]) * (b[key] - a[key])
        return math.nan
    if "takeoff_ms" in result:
        result["speed_takeoff_kmh"] = round(at(result["takeoff_ms"], "speed_kmh"), 2)
        result["yaw_takeoff_deg"] = round(at(result["takeoff_ms"], "yaw_deg"), 2)
        result["speed_landing_kmh"] = round(at(result["landing_ms"], "speed_kmh"), 2)
        result["yaw_landing_deg"] = round(at(result["landing_ms"], "yaw_deg"), 2)
        for dt in (200, 500, 1000):
            result[f"speed_land+{dt}"] = round(at(result["landing_ms"] + dt, "speed_kmh"), 2)
    return result


def match(session: "Session", lead: int, target: int, tries: int = 6) -> dict:
    """Secant search on the air steer until the landing slip is within 1 degree."""
    tried: dict[int, int] = {}

    def slip(air: int) -> int:
        if air not in tried:
            tried[air] = session.run(f"lead{lead:03d}_air{air:+04d}", variant(lead, air))["landing_slip_deg"]
        return tried[air]

    a, b = 0, 64 if slip(0) > target else -64
    for _ in range(tries):
        fa, fb = slip(a) - target, slip(b) - target
        best = min(tried, key=lambda k: abs(tried[k] - target))
        if abs(tried[best] - target) <= 1:
            break
        nxt = b if fa == fb else round(b - fb * (b - a) / (fb - fa))
        nxt = max(-127, min(127, nxt))
        if nxt in tried:
            nxt = max(-127, min(127, nxt + (1 if fb > 0 else -1)))
            if nxt in tried:
                break
        a, b = b, nxt
    best = min(tried, key=lambda k: abs(tried[k] - target))
    print(f"lead {lead}: best air steer {best} -> slip {tried[best]} (target {target}); tried {tried}", flush=True)
    return {"lead": lead, "air": best, "slip": tried[best]}


class Session:
    def __init__(self, pid: int) -> None:
        self.client = TickClient()
        if self.client.get("runtime/status")["currentMapUid"] != trials.MAP_UID:
            raise SystemExit("ANGULAR MOMENTUM is not loaded")
        self.pid = pid
        self.live = trials.Recorder(self.client)
        state = json.loads(trials.STATE.read_text())
        self.previous = trials.activate(self.client, state["collection_id"])

    def run(self, name: str, text: str) -> dict:
        result = trials.run(self.client, self.live, self.pid, name, text)
        path = trials.OUT / f"{name}_{result['run']}.csv"
        summary = {"variant": name, "run": result["run"], **summarize(path)}
        print("  " + json.dumps(summary), flush=True)
        with (trials.OUT / "summaries.jsonl").open("a", encoding="utf-8") as handle:
            handle.write(json.dumps({**summary, "script": text}) + "\n")
        return summary

    def close(self) -> None:
        self.live.close()
        trials.activate(self.client, self.previous)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pid", type=int, required=True)
    parser.add_argument("what", choices=("baseline", "probe", "match"))
    parser.add_argument("pairs", nargs="*", help="lead:air_steer pairs for probe; leads for match")
    parser.add_argument("--target", type=int, help="landing slip to match (default: lead 0, air 0)")
    args = parser.parse_args()
    session = Session(args.pid)
    try:
        if args.what == "baseline":
            session.run("base", script({}))
        if args.what == "probe":
            for pair in args.pairs:
                lead, air, *hold = (int(v) for v in pair.split(":"))
                hold_ms = hold[0] if hold else 0
                name = f"lead{lead:03d}_air{air:+04d}" + (f"_for{hold_ms:03d}" if hold_ms else "")
                session.run(name, variant(lead, air, hold_ms))
        if args.what == "match":
            target = args.target
            if target is None:
                target = session.run("lead000_air+000", variant(0, 0))["landing_slip_deg"]
            print(f"target landing slip {target} deg", flush=True)
            for lead in (int(v) for v in args.pairs):
                match(session, lead, target)
    finally:
        session.close()


if __name__ == "__main__":
    main()
