"""Print force-multiplier and steering-mode changes in the tarmac capture."""

import struct

from analyze_phy_memory import rows


previous = None
changes = []
samples = list(rows("baseline_right", tag="tarmac"))
for _, _, tick, raw_steer, contacts, _, smoothed, blob in samples:
    multiplier = struct.unpack_from("<f", blob, 0x14DC)[0]
    mode = blob[0x14E5]
    timestamp = struct.unpack_from("<I", blob, 0x14D8)[0]
    ice_factor = struct.unpack_from("<f", blob, 0x1C44)[0]
    value = (round(multiplier, 6), round(smoothed, 6), mode,
             timestamp, round(ice_factor, 6), contacts)
    if value != previous:
        changes.append((tick, raw_steer, *value))
        previous = value

print("snapshots", len(samples), "changes", len(changes))
for row in changes:
    print(row)
