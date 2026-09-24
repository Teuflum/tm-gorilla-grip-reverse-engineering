"""Summarize raw vehicle physics snapshots around the target takeoff."""

from __future__ import annotations

import struct
from pathlib import Path

from capture_takeoff_memory import RECORD


ROOT = Path(__file__).resolve().parent


def rows(variant, tag="takeoff"):
    data = (ROOT / f"memory_{tag}_{variant}.bin").read_bytes()
    size = next((value for value in (0x1D00, 0x1B00)
                 if len(data) % (RECORD.size + value) == 0), None)
    if size is None:
        raise ValueError(f"Unknown snapshot size in {variant}")
    stride = RECORD.size + size
    assert len(data) % stride == 0
    for i in range(len(data) // stride):
        item = data[i * stride:(i + 1) * stride]
        wall, race_tick = RECORD.unpack_from(item)
        blob = item[RECORD.size:]
        steer = struct.unpack_from("<f", blob, 0xA0)[0]
        contacts = tuple(struct.unpack_from("<I", blob, 0x17B4 + 0xB8 * w)[0] for w in range(4))
        contact_time = tuple(struct.unpack_from("<Q", blob, 0x17B8 + 0xB8 * w)[0] for w in range(4))
        smoothed = struct.unpack_from("<f", blob, 0x1430)[0]
        yield i, wall, race_tick, steer, contacts, contact_time, smoothed, blob


if __name__ == "__main__":
    for variant in ("right_12_from_1126_through_1131", "right_13_from_1126_through_1131"):
        print("\n", variant)
        previous = None
        for i, wall, tick, steer, contacts, times, smoothed, blob in rows(variant):
            key = (steer, contacts, times)
            if key != previous:
                print(f"{i:3} eventTick={tick:5} steer={steer:+.7f} contacts={contacts} "
                      f"times={times} smooth={smoothed:+.6f}")
                previous = key
