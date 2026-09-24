"""Summarize the 100 ms grounded neutral-steer experiment."""

import struct
import sys

from analyze_phy_memory import rows


previous = None
variant = sys.argv[1] if len(sys.argv) > 1 else "neutral_100ms_ice"
for _, _, tick, raw, contacts, _, smoothed, blob in rows(
        variant, tag="neutral"):
    mode = blob[0x14E5]
    multiplier = struct.unpack_from("<f", blob, 0x14DC)[0]
    neutral_start = struct.unpack_from("<I", blob, 0x14E0)[0]
    mode_change = struct.unpack_from("<I", blob, 0x14D8)[0]
    values = (round(raw, 4), round(smoothed, 4), mode,
              round(multiplier, 5), neutral_start, mode_change, contacts)
    if values != previous:
        print(tick, *values)
        previous = values
