"""Pause an automated TICK replay on a chosen tick and scan physics memory read-only."""

from __future__ import annotations

import argparse
import ctypes as C
import json
import time
import uuid

from auto_trials import COMMAND, MAP_UID, STATE, activate_collection, load_variant
from scan_live_vehicle import PROCESS_QUERY_INFORMATION, PROCESS_VM_READ, kernel, scan
from tick_client import TickClient
from tick_events import TickEvents


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("variant")
    parser.add_argument("pause_tick", type=int, help="Race time in ms")
    parser.add_argument("pid", type=int)
    parser.add_argument("--steer", type=float, default=1.0)
    parser.add_argument("--gas", type=float, default=1.0)
    parser.add_argument("--brake", type=float, default=0.0)
    args = parser.parse_args()
    state = json.loads(STATE.read_text(encoding="utf-8"))
    client = TickClient()
    if client.get("runtime/status")["currentMapUid"] != MAP_UID:
        raise RuntimeError("Target map is not loaded")
    original_speed = client.get("runtime/game-speed")["requestedGameSpeed"]
    previous_collection = activate_collection(client, state["collection_id"])
    stream = None
    try:
        client.request("PUT", "runtime/game-speed", {"requestedGameSpeed": 1})
        revision = load_variant(client, state, args.variant)
        stream = TickEvents(client)
        command_id = uuid.uuid4().hex[:12]
        temp = COMMAND.with_suffix(".tmp")
        temp.write_text(command_id, encoding="utf-8")
        temp.replace(COMMAND)
        print(f"loaded {revision}; restart command {command_id}", flush=True)
        saw_restart = False
        deadline = time.monotonic() + 45
        while time.monotonic() < deadline:
            event = stream.read_event()
            runtime = event.get("runtimeEvent") or {}
            if runtime.get("eventType") != "vehicle-state":
                continue
            vehicle = runtime["payload"]
            tick = vehicle.get("raceTick")
            if tick is None:
                continue
            if tick < 1000:
                saw_restart = True
            if saw_restart and tick >= args.pause_tick:
                client.request("PUT", "runtime/game-speed", {"requestedGameSpeed": 0})
                print(f"paused after event raceTick={tick}, inputs={vehicle.get('inputs')}", flush=True)
                break
        else:
            raise TimeoutError("Replay did not reach requested race tick")
        handle = kernel.OpenProcess(PROCESS_VM_READ | PROCESS_QUERY_INFORMATION, False, args.pid)
        if not handle:
            raise OSError(C.get_last_error(), "OpenProcess failed")
        try:
            matches = scan(handle, args.steer, args.gas, args.brake)
            print("physics candidates:", [hex(x) for x in matches], flush=True)
        finally:
            kernel.CloseHandle(handle)
    finally:
        if stream is not None:
            stream.close()
        client.request("PUT", "runtime/game-speed", {"requestedGameSpeed": original_speed})
        activate_collection(client, previous_collection)
        print("restored TICK game speed and input collection", flush=True)


if __name__ == "__main__":
    main()
