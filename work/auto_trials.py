"""Run TICK grip variants with no copy/paste or manual CSV saving.

Requires GorillaGripLogger 0.5.1 loaded in Openplanet.  This script uses the
local TICK API, then asks the logger to restart the race and save telemetry.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import shutil
import sys
import time
import uuid
from pathlib import Path

from tick_client import TickClient, encoded


sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "work/tick_automation_state.json"
OUTPUT = ROOT / "outputs"
STORAGE = Path.home() / "OpenplanetNext/PluginStorage/GorillaGripLogger"
COMMAND = STORAGE / "automation_command.txt"
STATUS = STORAGE / "automation_status.txt"
MAP_UID = "xsBIINZa10KzKOtrSt_oxEAnHX5"


def wait_for(predicate, seconds: float, description: str):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        result = predicate()
        if result:
            return result
        time.sleep(0.2)
    raise TimeoutError(f"Timed out waiting for {description}")


def activate_collection(client: TickClient, collection_id: str) -> str:
    """Select the collection the native TICK runtime will actually execute."""
    settings = client.get("settings")
    previous = settings["activeInputCollectionId"]
    if previous != collection_id:
        client.patch("settings", {
            "expectedRevision": settings["revision"],
            "activeInputCollectionId": collection_id,
        })
    return previous


def load_variant(client: TickClient, state: dict, name: str) -> str:
    collection_id = state["collection_id"]
    collection = client.get(f"input-collections/{collection_id}")
    if name == "baseline_right":
        revision_id = state["baseline_revision_id"]
    else:
        source = (OUTPUT / f"TICK_{name}.txt").read_text(encoding="utf-8")
        current_id = collection["currentRevisionId"]
        result = client.post(
            f"input-collections/{encoded(collection_id)}/revisions?"
            f"expectedBaseRevisionId={encoded(current_id)}&origin=ui",
            source,
            raw=True,
        )
        revision_id = result["revision"]["id"]
        print(f"  Created revision {result['revision']['revisionNumber']} ({result['revision']['actionCount']} actions)", flush=True)
        collection = client.get(f"input-collections/{collection_id}")
    client.post(
        f"input-revisions/{revision_id}/load?expectedCollectionRevision={collection['node']['revision']}"
    )
    wait_for(
        lambda: client.get("runtime/status")["loadedInputRevisionId"] == revision_id,
        10,
        f"TICK to load {name}",
    )
    return revision_id


def summarize(path: Path) -> dict:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        all_rows = list(csv.DictReader(handle))
    run_number = max(int(row["run"]) for row in all_rows)
    rows = [row for row in all_rows if int(row["run"]) == run_number]
    takeoff = [
        row for row in rows
        if 860 < float(row["px"]) < 868 and 570 < float(row["pz"]) < 590
    ]
    if not takeoff:
        raise ValueError("Target takeoff region absent from latest logger run")
    landing = [
        row for row in rows
        if 780 < float(row["px"]) < 800 and 530 < float(row["pz"]) < 560
    ]
    if not landing:
        raise ValueError("Target landing region absent from logger CSV")
    at_782 = min(landing, key=lambda row: abs(float(row["px"]) - 782))
    ground = next((row for row in landing if row["ground"] == "1"), None)
    if ground is None:
        raise ValueError("No ground-contact sample at target landing")
    speed = lambda row: 3.6 * math.sqrt(sum(float(row[a]) ** 2 for a in ("vx", "vy", "vz")))
    heading = math.degrees(math.atan2(float(ground["dirx"]), float(ground["dirz"])))
    speed_782 = speed(at_782)
    return {
        "samples": len(rows),
        "touchdown_x": round(float(ground["px"]), 3),
        "touchdown_speed_kmh": round(speed(ground), 3),
        "touchdown_heading_deg": round(heading, 3),
        "speed_at_x782_kmh": round(speed_782, 3),
        "classification": "instant" if speed_782 > 229.5 else "delayed",
    }


def summarize_jump2(path: Path) -> dict:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        all_rows = list(csv.DictReader(handle))
    run_number = max(int(row["run"]) for row in all_rows)
    rows = [row for row in all_rows if int(row["run"]) == run_number]
    landing = [
        row for row in rows
        if 6150 <= int(row["time_ms"]) <= 6300
        and 940 < float(row["px"]) < 951
        and 720 < float(row["pz"]) < 730
    ]
    if not landing:
        raise ValueError("FR-last ice landing absent from logger CSV")
    ground = next((row for row in landing if row["ground"] == "1"), None)
    if ground is None:
        raise ValueError("No ground-contact sample at FR-last ice landing")
    at_949 = min(landing, key=lambda row: abs(float(row["px"]) - 949))
    speed = lambda row: 3.6 * math.sqrt(sum(float(row[a]) ** 2 for a in ("vx", "vy", "vz")))
    return {
        "samples": len(rows),
        "touchdown_x": round(float(ground["px"]), 3),
        "touchdown_speed_kmh": round(speed(ground), 3),
        "speed_at_x949_kmh": round(speed(at_949), 3),
    }


def run_variant(client: TickClient, state: dict, name: str, summarize_func=summarize) -> dict:
    print(f"Running {name}", flush=True)
    revision_id = load_variant(client, state, name)
    for attempt in range(1, 4):
        command_id = uuid.uuid4().hex[:12]
        temp = COMMAND.with_suffix(".tmp")
        temp.write_text(command_id, encoding="utf-8")
        temp.replace(COMMAND)
        print(f"  Loaded {revision_id}; sent restart command {command_id} (attempt {attempt})", flush=True)

        def finished():
            if not STATUS.exists():
                return None
            line = STATUS.read_text(encoding="utf-8").strip()
            if not line.startswith(command_id + " "):
                return None
            if " error:" in line:
                raise RuntimeError(f"Openplanet automation: {line}")
            return line if " complete " in line else None

        wait_for(finished, 65, f"Openplanet trial {name}")
        path = STORAGE / f"gorilla_grip_auto_{command_id}.csv"
        if not path.exists():
            raise RuntimeError(f"Completion reported but CSV not found: {path}")
        output = OUTPUT / f"automated_{name}_{command_id}.csv"
        shutil.copy2(path, output)
        try:
            measurement = summarize_func(output)
        except ValueError as exc:
            print(f"  Invalid trajectory: {exc}; CSV preserved at {output}", flush=True)
            if attempt == 3:
                raise
            continue
        result = {"variant": name, "command_id": command_id, "revision_id": revision_id,
                  "csv": str(output), **measurement}
        print("  " + json.dumps(result, ensure_ascii=False), flush=True)
        return result
    raise AssertionError("Unreachable")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--region", choices=("target", "jump2"), default="target")
    parser.add_argument("variants", nargs="+", help="Names of outputs/TICK_<name>.txt variants")
    args = parser.parse_args()
    state = json.loads(STATE.read_text(encoding="utf-8"))
    client = TickClient()
    if client.get("runtime/status")["currentMapUid"] != MAP_UID:
        raise RuntimeError("Target map is not loaded")
    results = []
    summarize_func = summarize if args.region == "target" else summarize_jump2
    previous_collection_id = activate_collection(client, state["collection_id"])
    try:
        for name in args.variants:
            results.append(run_variant(client, state, name, summarize_func))
    finally:
        activate_collection(client, previous_collection_id)
        path = OUTPUT / "automated_trial_results.json"
        existing = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
        existing.extend(results)
        path.write_text(json.dumps(existing, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
