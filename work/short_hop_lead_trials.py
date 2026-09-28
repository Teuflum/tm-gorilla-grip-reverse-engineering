"""Early-countersteer trials on two short hops (13.3 s and 20.3 s takeoff).

The map is the one Teuflum had loaded on 28 September 2026 (UID in MAP_UID);
the baseline input is outputs/TICK_short_hops_baseline.txt. Each variant holds
full right and switches to full left at one tick, so the stored direction
flips 50 ms later; `lead` is how long before takeoff that should happen.
Only that hop's steering changes; every other action is the baseline's.

Reuses the TICK plumbing of countersteer_lead_trials.py (Analysis automation
collection, restores the active collection afterwards). Each run's TICK
telemetry and Trainer log lines are saved under outputs/short_hop_lead and
summarized from the Trainer snapshots, so "Log trainer events" and "Log every
tire-force change" must be on.

The game runs at SLOW only inside the hop windows. Keep the game window in
the foreground: each restart sends keys to it.

Usage:
  py -3 short_hop_lead_trials.py --pid <PID> run base
  py -3 short_hop_lead_trials.py --pid <PID> run a 0 10 20 30 50 100 150 200 300 400 0
  py -3 short_hop_lead_trials.py --pid <PID> run b 610 450 500 550 650 700 750 800 610
  py -3 short_hop_lead_trials.py --pid <PID> run f 0 10 20 30 50 100 150 200 300 400 500 600 0
  py -3 short_hop_lead_trials.py summary a|b|f|base
  py -3 short_hop_lead_trials.py resummarize
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
import threading
import time
import uuid
from pathlib import Path

import countersteer_lead_trials as trials


sys.stdout.reconfigure(encoding="utf-8")
trials.MAP_UID = "pBoO2N5xKZRTuOGcVBRuoOCbhM3"
trials.RECORD_FROM, trials.RECORD_TO = 11000, 21600
trials.OUT = trials.ROOT / "outputs/short_hop_lead"
BASELINE = trials.ROOT / "outputs/TICK_short_hops_baseline.txt"
ORDER = {"seed": 0, "accel": 1, "brake": 2, "flags": 3, "steer": 4}
SLOW = 0.2  # game speed inside the hop windows, for a Trainer snapshot on every tick
# Mode flips 50 ms after a full-right to full-left step (0.2 per tick; measured on hop A).
FLIP_DELAY_MS = 50

# hop: (baseline takeoff race ms, baseline steer actions replaced by the step,
#       window of Trainer snapshots that belong to this hop)
HOPS = {
    "a": (13300, (12900, 13200), (12400, 14400)),
    "b": (20320, (19600, 19720), (19300, 21500)),
    # Grounded-only reversal: no jump. The car slides on flat ice (y 18.05) from
    # 16.4 s until the ramp foot near 19.9 s. At 19.10 s its speed (199 km/h) and
    # slip size (30 degrees) match hop A's switch, so that tick stands in for the
    # takeoff and FLAT_AIRTIME_MS later for the front touchdown. Unlike on hop A,
    # the slide is still closing there (it changes side near 19.35 s). The baseline
    # reversal at 19.66 s is replaced by the step, so the car keeps full left.
    "f": (19100, (19600, 19720), (18300, 20000)),
}
FLAT_AIRTIME_MS = 110  # hop A's airtime, so force is compared at the same age


def base_entries() -> dict[tuple[int, str], int]:
    entries = {}
    for line in BASELINE.read_text(encoding="utf-8").splitlines():
        if line.strip():
            ms, action, value = line.split()
            entries[(int(ms), action)] = {"left": -127, "right": 127}.get(value) or int(value)
    return entries


def script(entries: dict[tuple[int, str], int]) -> str:
    rows = sorted(entries.items(), key=lambda item: (item[0][0], ORDER[item[0][1]]))
    return "".join(f"{ms} {action} {value}\n" for (ms, action), value in rows)


def variant(hop: str, lead_ms: int) -> str:
    """Baseline with this hop's reversal replaced by one full-left step."""
    takeoff, (first, last), _ = HOPS[hop]
    entries = {key: value for key, value in base_entries().items()
               if not (key[1] == "steer" and first <= key[0] <= last)}
    entries[(takeoff - FLIP_DELAY_MS - lead_ms, "steer")] = -127
    return script(entries)


SNAPSHOT = re.compile(r"snapshot at (\d+)ms: exact true, mode (\d), steer ([-\d.]+), contacts (\d{4}), "
                      r"modeAt (\d+), clock (\d+), .*?force ([\d.]+), gate (\d).*?speed (\d+), slip (\d+)")


def snapshots(log: str) -> list[dict]:
    keys = ("race", "mode", "steer", "contacts", "modeAt", "clock", "force", "gate", "speed", "slip")
    out = []
    for match in SNAPSHOT.finditer(log):
        row = dict(zip(keys, match.groups()))
        for k in ("race", "mode", "modeAt", "clock", "gate", "speed", "slip"):
            row[k] = int(row[k])
        row["steer"], row["force"] = float(row["steer"]), float(row["force"])
        out.append(row)
    return out


def load_rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as handle:
        return [{k: float(v) for k, v in row.items() if v not in ("", None)} for row in csv.DictReader(handle)]


def at(rows: list[dict], ms: float, key: str) -> float:
    for a, b in zip(rows, rows[1:]):
        if a["race_ms"] <= ms <= b["race_ms"] and b["race_ms"] > a["race_ms"]:
            return a[key] + (ms - a["race_ms"]) / (b["race_ms"] - a["race_ms"]) * (b[key] - a[key])
    return math.nan


def hop_facts(log: str, hop: str) -> dict:
    """Switch, takeoff, touchdown and force from the Trainer snapshots of one hop.

    Times are physics-clock ticks turned into race ms with the run's clock
    offset (snapshot race times are frame times, 0-10 ms after the tick). On the
    flat case takeoff and touchdown are the fixed stand-in ticks.
    """
    window = HOPS[hop][2]
    snaps = [s for s in snapshots(log) if window[0] <= s["race"] <= window[1]]
    offset = math.ceil(max(s["clock"] - s["race"] for s in snaps) / 10) * 10
    race = lambda clock: clock - offset
    facts: dict = {}
    # The reversal of interest: the first right (2) -> left (1) flip in the window.
    for prev, cur in zip(snaps, snaps[1:]):
        if prev["mode"] == 2 and cur["mode"] == 1:
            facts["switch_ms"] = race(cur["modeAt"])
            break
    if "switch_ms" not in facts:
        return facts
    switch_clock = cur["modeAt"]

    def at_clock(clock: int) -> dict:
        """The snapshot in force at a tick: snapshots print only when something changes."""
        known = [s for s in snaps if s["clock"] <= clock]
        return known[-1] if known else {"force": math.nan, "slip": None}

    if hop == "f":
        takeoff_clock = HOPS[hop][0] + offset
        facts["takeoff_ms"] = HOPS[hop][0]
        front_clock = takeoff_clock + FLAT_AIRTIME_MS
        facts["first_touch_ms"] = race(front_clock)
    else:
        # Takeoff: the tick of the first all-air snapshot after the switch (the Trainer's takeoff tick).
        grounded_before = [s for s in snaps if s["clock"] >= prev["clock"]]
        for prev, s in zip(grounded_before, grounded_before[1:]):
            if s["contacts"] == "0000" and prev["contacts"] != "0000":
                facts["takeoff_ms"] = race(s["clock"])
                facts["takeoff_frame_gap_ms"] = s["clock"] - prev["clock"]
                takeoff_clock = s["clock"]
                break
        else:
            return facts
        for s in snaps:
            if s["clock"] > takeoff_clock and s["contacts"] != "0000":
                facts["first_touch_ms"] = race(s["clock"])
                break
        front = next((s for s in snaps if s["clock"] > takeoff_clock and "1" in s["contacts"][:2]), None)
        if front is None:
            return facts
        front_clock = front["clock"]
    facts["front_touch_ms"] = race(front_clock)
    facts["lead_ms"] = facts["takeoff_ms"] - facts["switch_ms"]
    facts["switch_to_front_ms"] = facts["front_touch_ms"] - facts["switch_ms"]
    facts["airtime_ms"] = facts["front_touch_ms"] - facts["takeoff_ms"]
    facts["landing_slip_deg"] = at_clock(front_clock)["slip"]
    facts["force_takeoff"] = at_clock(takeoff_clock - 10)["force"]
    for dt in (0, 100, 200, 300, 400):
        facts[f"force_front+{dt}"] = at_clock(front_clock + dt)["force"]
    # First tick after the switch with the force back at 2.0 (it can be before touchdown).
    full = next((s for s in snaps if s["clock"] > switch_clock and s["force"] >= 1.999), None)
    facts["full_force_ms"] = race(full["clock"]) if full else None
    return facts


def trainer_verdict(log: str, window: tuple[int, int]) -> dict:
    for grade, takeoff, lead in re.findall(r"verdict at \d+ms: (\S+) \|.*?takeoff (\d+)ms \| landing \d+ms \| "
                                           r"lead (-?\d+)ms", log):
        if window[0] <= int(takeoff) <= window[1]:
            return {"grade": grade, "trainer_takeoff_ms": int(takeoff), "trainer_lead_ms": int(lead)}
    return {}


def summarize(csv_path: Path, hop: str) -> dict:
    log = csv_path.with_suffix(".log").read_text(encoding="utf-8")
    result = {**hop_facts(log, hop), **trainer_verdict(log, HOPS[hop][2])}
    rows = load_rows(csv_path)
    if "takeoff_ms" in result:
        result["speed_takeoff_kmh"] = round(at(rows, result["takeoff_ms"], "speed_kmh"), 2)
    if "front_touch_ms" in result:
        result["speed_front_touch_kmh"] = round(at(rows, result["front_touch_ms"], "speed_kmh"), 2)
    return result


class Session:
    def __init__(self, pid: int) -> None:
        self.client = trials.TickClient()
        if self.client.get("runtime/status")["currentMapUid"] not in (trials.MAP_UID, None):
            raise SystemExit("the short-hop map is not loaded")
        self.pid = pid
        self.speed = self.client.get("runtime/game-speed")["requestedGameSpeed"]
        self.live = trials.Recorder(self.client)
        state = json.loads(trials.STATE.read_text())
        self.previous = trials.activate(self.client, state["collection_id"])

    def slow_near_hops(self, hops: tuple[str, ...]) -> None:
        """Watch the race clock and run the game at SLOW only inside the hop windows.

        Physics is tick-based, so this changes nothing but how many frames (and
        so Trainer snapshots) land on each tick.
        """
        windows = [HOPS[hop][2] for hop in hops]
        slow = False
        while not self.stop_slow.is_set():
            tick = self.live.tick
            inside = self.live.restarted and any(a <= tick <= b for a, b in windows)
            if inside != slow:
                self.client.request("PUT", "runtime/game-speed", {"requestedGameSpeed": SLOW if inside else 1})
                slow = inside
            time.sleep(0.002)
        if slow:
            self.client.request("PUT", "runtime/game-speed", {"requestedGameSpeed": 1})

    def replay(self, name: str, hops: tuple[str, ...], text: str) -> dict:
        """trials.run, but slowed inside the hop windows and waiting for the log.

        Openplanet writes its log file with a delay of several seconds when the
        Trainer logs every tire-force change, so the lines are read only once a
        snapshot of this attempt has reached the end of the last hop window.
        """
        revision_id = trials.load(self.client, json.loads(trials.STATE.read_text())["collection_id"], text)
        offset = trials.LOG.stat().st_size
        self.stop_slow = threading.Event()
        watcher = threading.Thread(target=self.slow_near_hops, args=(hops,), daemon=True)
        watcher.start()
        try:
            trials.restart(self.pid, self.client, self.live)
            self.live.wait(lambda: self.live.tick >= trials.RECORD_TO, 120, f"{name} to reach {trials.RECORD_TO} ms")
        finally:
            self.stop_slow.set()
            watcher.join()
        status = self.client.get("runtime/status")
        samples = list(self.live.samples)
        until = max(HOPS[hop][2][1] for hop in hops)
        deadline = time.monotonic() + 60
        while True:
            with trials.LOG.open("rb") as handle:
                handle.seek(offset)
                lines = [line for line in handle.read().decode("utf-8", "replace").splitlines()
                         if "[GorillaGripTrainer]" in line and "Gorilla Grip Trainer" in line]
            races = [(i, int(m[1])) for i, m in enumerate(re.search(r"snapshot at (\d+)ms", l) for l in lines) if m]
            # The previous attempt's last lines can land after the offset: start where race time drops.
            drops = [b[0] for a, b in zip(races, races[1:]) if b[1] < a[1]]
            start = drops[-1] if drops else 0
            if any(i >= start and r >= until for i, r in races):
                lines = lines[start:]
                break
            if time.monotonic() > deadline:
                raise TimeoutError(f"{name}: Trainer log never reached {until} ms")
            time.sleep(1)
        run_id = uuid.uuid4().hex[:8]
        trials.OUT.mkdir(parents=True, exist_ok=True)
        path = trials.OUT / f"{name}_{run_id}.csv"
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(samples[0]))
            writer.writeheader()
            writer.writerows(samples)
        path.with_suffix(".log").write_text("\n".join(lines) + "\n", encoding="utf-8")
        result = {"variant": name, "run": run_id, "revision_id": revision_id, "samples": len(samples),
                  "override": status["userInputOverrideActive"], "effective": status["inputExecutionEffective"]}
        print(json.dumps(result), flush=True)
        return result

    def run(self, name: str, hops: tuple[str, ...], text: str) -> None:
        result = self.replay(name, hops, text)
        path = trials.OUT / f"{name}_{result['run']}.csv"
        for hop in hops:
            summary = {"variant": name, "hop": hop, "run": result["run"], "override": result["override"],
                       **summarize(path, hop)}
            print("  " + json.dumps(summary), flush=True)
            with (trials.OUT / "summaries.jsonl").open("a", encoding="utf-8") as handle:
                handle.write(json.dumps({**summary, "script": text}) + "\n")

    def close(self) -> None:
        self.live.close()
        self.client.request("PUT", "runtime/game-speed", {"requestedGameSpeed": self.speed})
        trials.activate(self.client, self.previous)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--pid", type=int)
    parser.add_argument("what", choices=("run", "summary", "resummarize"))
    parser.add_argument("hop", nargs="?", choices=("a", "b", "f", "base"))
    parser.add_argument("leads", type=int, nargs="*")
    args = parser.parse_args()
    if args.what == "resummarize":
        # Recompute every saved run from its telemetry and log after a parser change.
        path = trials.OUT / "summaries.jsonl"
        old = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
        new = []
        for r in old:
            keep = {k: r[k] for k in ("variant", "hop", "run", "override")}
            csv_path = trials.OUT / f"{r['variant']}_{r['run']}.csv"
            new.append({**keep, **summarize(csv_path, r["hop"]), "script": r["script"]})
        path.write_text("".join(json.dumps(r) + "\n" for r in new), encoding="utf-8")
        print(f"resummarized {len(new)} runs")
        return
    if args.what == "summary":
        for line in (trials.OUT / "summaries.jsonl").read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            if args.hop == "base" or r["hop"] == args.hop:
                r.pop("script")
                print(json.dumps(r))
        return
    # Record only as far as the compared race times need.
    trials.RECORD_TO = 15500 if args.hop == "a" else 21600
    session = Session(args.pid)
    try:
        if args.hop == "base":
            session.run("base", ("a", "b"), BASELINE.read_text(encoding="utf-8"))
        else:
            for lead in args.leads:
                session.run(f"{args.hop}_lead{lead:+04d}", (args.hop,), variant(args.hop, lead))
    finally:
        session.close()


if __name__ == "__main__":
    main()
