"""Probe the one-tick sign and magnitude boundary while RR alone touches."""

from pathlib import Path


root = Path(__file__).resolve().parent.parent / "outputs"
source = root / "TICK_right_through_1131.txt"
original = source.read_text(encoding="utf-8").splitlines()
order = {"accel": 0, "brake": 1, "steer": 2, "seed": 3, "flags": 4}
for tick, steer_values in ((1128, (-4, -5)),
                           (1130, (-13, -12, -8, -7, -6, -5, -4, -1, 1, 12, 13))):
    for steer in steer_values:
        entries = {(int(ms), action): int(value)
                   for ms, action, value in (line.split() for line in original)}
        entries[(tick * 10, "steer")] = steer
        entries[((tick + 1) * 10, "steer")] = 78
        rows = sorted(entries.items(), key=lambda item: (item[0][0], order[item[0][1]]))
        name = f"rr_gap_{'left' if steer < 0 else 'right'}_{abs(steer)}_{tick}"
        (root / f"TICK_{name}.txt").write_text(
            "\n".join(f"{ms} {action} {value}" for (ms, action), value in rows) + "\n",
            encoding="utf-8",
        )
        print(name)
