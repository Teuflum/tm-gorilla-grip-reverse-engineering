"""Sample a known vehicle physics object through one slowed takeoff, read-only."""

from __future__ import annotations

import argparse
import ctypes as C
import json
import struct
import threading
import time
import uuid

from auto_trials import COMMAND, MAP_UID, STATE, activate_collection, load_variant
from scan_live_vehicle import PROCESS_QUERY_INFORMATION, PROCESS_VM_READ, kernel, read
from tick_client import TickClient
from tick_events import TickEvents


RECORD = struct.Struct("<dI")
BYTES = 0x1D00


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("variant")
    parser.add_argument("pid", type=int)
    parser.add_argument("pointer", type=lambda value: int(value, 0))
    parser.add_argument("--start-tick", type=int, default=11150)
    parser.add_argument("--end-tick", type=int, default=11380)
    parser.add_argument("--expected-steer", type=float, default=-1.0)
    parser.add_argument("--slow-speed", type=float, default=0.01)
    parser.add_argument("--tag", default="takeoff")
    args = parser.parse_args()
    state = json.loads(STATE.read_text(encoding="utf-8"))
    client = TickClient()
    if client.get("runtime/status")["currentMapUid"] != MAP_UID:
        raise RuntimeError("Target map is not loaded")
    original_speed = client.get("runtime/game-speed")["requestedGameSpeed"]
    previous_collection = activate_collection(client, state["collection_id"])
    stream = None
    handle = None
    stop = threading.Event()
    live = {"tick": None, "started": False, "inputs": None, "error": None}
    try:
        client.request("PUT", "runtime/game-speed", {"requestedGameSpeed": 1})
        revision = load_variant(client, state, args.variant)
        stream = TickEvents(client)

        def listen():
            try:
                while not stop.is_set():
                    event = stream.read_event()
                    runtime = event.get("runtimeEvent") or {}
                    if runtime.get("eventType") == "vehicle-state":
                        vehicle = runtime["payload"]
                        tick = vehicle.get("raceTick")
                        if tick is not None:
                            live["tick"] = tick
                            live["inputs"] = vehicle.get("inputs")
                            if tick < 500:
                                live["started"] = True
            except Exception as exc:
                live["error"] = repr(exc)

        thread = threading.Thread(target=listen, daemon=True)
        thread.start()
        command_id = uuid.uuid4().hex[:12]
        temp = COMMAND.with_suffix(".tmp")
        temp.write_text(command_id, encoding="utf-8")
        temp.replace(COMMAND)
        print(f"loaded {revision}; restart command {command_id}", flush=True)
        deadline = time.monotonic() + 45
        while time.monotonic() < deadline:
            if live["error"]:
                raise RuntimeError(live["error"])
            if live["started"] and live["tick"] is not None and live["tick"] >= args.start_tick:
                break
            time.sleep(0.02)
        else:
            raise TimeoutError(f"Replay did not reach {args.start_tick} ms")
        handle = kernel.OpenProcess(PROCESS_VM_READ | PROCESS_QUERY_INFORMATION, False, args.pid)
        if not handle:
            raise OSError(C.get_last_error(), "OpenProcess failed")
        sample = read(handle, args.pointer, BYTES)
        if len(sample) != BYTES:
            raise RuntimeError("Known vehicle pointer became unreadable")
        gas, brake, steer = struct.unpack_from("<fff", sample, 0x98)
        wheel_count = struct.unpack_from("<I", sample, 0x380)[0]
        if wheel_count != 4 or abs(steer - args.expected_steer) > 0.01 or abs(gas - 1) > 0.01:
            raise RuntimeError(f"Known vehicle pointer is stale: steer={steer}, gas={gas}, wheels={wheel_count}")
        client.request("PUT", "runtime/game-speed", {"requestedGameSpeed": args.slow_speed})
        print(f"slowed at TICK raceTick={live['tick']}, memory steer={steer}", flush=True)
        path = STATE.parent / f"memory_{args.tag}_{args.variant}.bin"
        count = 0
        first_air = None
        last_contact = None
        deadline = time.monotonic() + 50
        with path.open("wb") as output:
            while time.monotonic() < deadline:
                tick = live["tick"]
                if live["error"]:
                    raise RuntimeError(live["error"])
                if tick is not None and tick > args.end_tick:
                    break
                data = read(handle, args.pointer, BYTES)
                if len(data) != BYTES:
                    raise RuntimeError("Vehicle pointer became unreadable during takeoff")
                output.write(RECORD.pack(time.monotonic(), tick or 0))
                output.write(data)
                count += 1
                contacts = [struct.unpack_from("<I", data, 0x17b4 + 0xB8 * i)[0] for i in range(4)]
                if any(value != 0 for value in contacts):
                    last_contact = (tick, contacts)
                elif first_air is None and last_contact is not None:
                    first_air = (tick, contacts)
                time.sleep(0.05)
            else:
                raise TimeoutError(f"Slowed takeoff stalled at tick={live['tick']}")
        print(f"saved {count} snapshots to {path}; last contact={last_contact}; first air={first_air}", flush=True)
    finally:
        stop.set()
        if stream is not None:
            stream.close()
        if handle:
            kernel.CloseHandle(handle)
        client.request("PUT", "runtime/game-speed", {"requestedGameSpeed": original_speed})
        activate_collection(client, previous_collection)
        print("restored TICK game speed and input collection", flush=True)


if __name__ == "__main__":
    main()
