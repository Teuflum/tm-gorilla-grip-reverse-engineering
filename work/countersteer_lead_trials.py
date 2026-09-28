"""Replay the 11.31 s ice jump with the pre-takeoff countersteer moved earlier.

The baseline TICK input switches from full left to +78 at 11260 ms, which
commits right mode on the last contact tick before the 11.31 s takeoff. Each
variant moves only that action earlier by the given number of milliseconds.
TICK telemetry (position, velocity) is recorded around the jump, and the
Gorilla Grip Trainer's debug log lines (lead, takeoff, landing) are copied from
Openplanet.log for the same run. Needs the ANGULAR MOMENTUM map loaded, TICK
running, and Trainer event logging on.

Usage: py -3 countersteer_lead_trials.py --pid <Trackmania PID> [--leads 0 20 50]
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
import time
import uuid
from pathlib import Path

from tick_client import TickClient, encoded
from tick_restart import Live, restart


sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "work/tick_automation_state.json"
BASELINE = ROOT / "outputs/TICK_baseline_right.txt"
OUT = ROOT / "outputs/countersteer_lead"
LOG = Path.home() / "OpenplanetNext/Openplanet.log"
MAP_UID = "xsBIINZa10KzKOtrSt_oxEAnHX5"
SWITCH_LINE = "11260 steer 78"
RECORD_FROM, RECORD_TO = 10500, 16500


def variant_text(shift_ms: int) -> str:
    lines = BASELINE.read_text(encoding="utf-8").splitlines()
    lines[lines.index(SWITCH_LINE)] = f"{11260 - shift_ms} steer 78"
    return "\n".join(lines) + "\n"


class Recorder(Live):
    """Live that also keeps every vehicle-state event inside the record window."""

    def __init__(self, client: TickClient) -> None:
        self.samples: list[dict] = []
        super().__init__(client)

    def listen(self) -> None:
        try:
            while not self.stop.is_set():
                event = self.stream.read_event().get("runtimeEvent") or {}
                if event.get("eventType") != "vehicle-state":
                    continue
                payload = event["payload"]
                tick = payload.get("raceTick")
                if tick is None:
                    continue
                if 0 <= tick < 200:
                    self.restarted = True
                    self.samples = []
                p = payload.get("position") or {}
                self.position = (p.get("x", math.nan), p.get("y", math.nan), p.get("z", math.nan))
                self.sim = payload.get("simulationTick", -1)
                self.tick = tick
                if self.restarted and RECORD_FROM <= tick <= RECORD_TO:
                    v = payload.get("linearVelocity") or {}
                    ypr = payload.get("pitchYawRollDegrees") or {}
                    self.samples.append({
                        "race_ms": tick, "sim": self.sim,
                        "x": p.get("x"), "y": p.get("y"), "z": p.get("z"),
                        "vx": v.get("x"), "vy": v.get("y"), "vz": v.get("z"),
                        "speed_kmh": 3.6 * payload.get("speedMetersPerSecond", math.nan),
                        "yaw_deg": ypr.get("y"),
                        "steer": (payload.get("inputs") or {}).get("steer"),
                    })
        except Exception as exc:
            self.error = repr(exc)


def activate(client: TickClient, collection_id: str) -> str:
    settings = client.get("settings")
    previous = settings["activeInputCollectionId"]
    if previous != collection_id:
        client.patch("settings", {"expectedRevision": settings["revision"],
                                  "activeInputCollectionId": collection_id})
    return previous


def load(client: TickClient, collection_id: str, text: str) -> str:
    collection = client.get(f"input-collections/{encoded(collection_id)}")
    result = client.post(
        f"input-collections/{encoded(collection_id)}/revisions?"
        f"expectedBaseRevisionId={encoded(collection['currentRevisionId'])}&origin=ui",
        text, raw=True)
    revision_id = result["revision"]["id"]
    collection = client.get(f"input-collections/{encoded(collection_id)}")
    client.post(f"input-revisions/{revision_id}/load?expectedCollectionRevision={collection['node']['revision']}")
    deadline = time.monotonic() + 10
    while client.get("runtime/status")["loadedInputRevisionId"] != revision_id:
        if time.monotonic() > deadline:
            raise TimeoutError("TICK did not load the variant")
        time.sleep(0.2)
    return revision_id


def run(client: TickClient, live: Recorder, pid: int, name: str, text: str) -> dict:
    revision_id = load(client, json.loads(STATE.read_text())["collection_id"], text)
    offset = LOG.stat().st_size
    restart(pid, client, live)
    live.wait(lambda: live.tick >= RECORD_TO, 60, f"{name} to reach {RECORD_TO} ms")
    status = client.get("runtime/status")
    samples = list(live.samples)
    with LOG.open("rb") as handle:
        handle.seek(offset)
        log = [line for line in handle.read().decode("utf-8", "replace").splitlines()
               if "[GorillaGripTrainer]" in line and "Gorilla Grip Trainer" in line]
    run_id = uuid.uuid4().hex[:8]
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{name}_{run_id}.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(samples[0]))
        writer.writeheader()
        writer.writerows(samples)
    (OUT / f"{name}_{run_id}.log").write_text("\n".join(log) + "\n", encoding="utf-8")
    result = {"variant": name, "run": run_id, "revision_id": revision_id, "samples": len(samples),
              "override": status["userInputOverrideActive"], "effective": status["inputExecutionEffective"],
              "leads": [line.split("lead ")[-1] for line in log if " preview at " in line]}
    print(json.dumps(result), flush=True)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pid", type=int, required=True)
    parser.add_argument("--leads", type=int, nargs="+", default=[0, 20, 50, 100, 200])
    parser.add_argument("--repeat", type=int, default=1)
    args = parser.parse_args()
    client = TickClient()
    if client.get("runtime/status")["currentMapUid"] != MAP_UID:
        raise SystemExit("ANGULAR MOMENTUM is not loaded")
    state = json.loads(STATE.read_text())
    live = Recorder(client)
    previous = activate(client, state["collection_id"])
    results = []
    try:
        for _ in range(args.repeat):
            for shift in args.leads:
                results.append(run(client, live, args.pid, f"shift_{shift:03d}", variant_text(shift)))
    finally:
        live.close()
        activate(client, previous)
        with (OUT / "runs.jsonl").open("a", encoding="utf-8") as handle:
            for result in results:
                handle.write(json.dumps(result) + "\n")


if __name__ == "__main__":
    main()
