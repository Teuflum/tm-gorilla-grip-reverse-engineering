"""Insert a one-tick steer gap into the successful six-tick pulse."""

from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
source = []
for line in (ROOT / "outputs/TICK_right_through_1131.txt").read_text(encoding="utf-8").splitlines():
    ms, action, value = line.split()
    source.append((int(ms), action, int(value)))

for gap_tick in (1127, 1128, 1129, 1130):
    for label, value in (("neutral", 0), ("left", -127)):
        entries = source + [
            (gap_tick * 10, "steer", value),
            ((gap_tick + 1) * 10, "steer", 78),
        ]
        entries.sort(key=lambda row: (row[0], {"accel": 0, "brake": 1, "steer": 2, "seed": 3, "flags": 4}[row[1]]))
        assert len({(ms, action) for ms, action, _ in entries}) == len(entries)
        name = f"gap_{label}_{gap_tick}"
        (ROOT / f"outputs/TICK_{name}.txt").write_text(
            "\n".join(f"{ms} {action} {value}" for ms, action, value in entries) + "\n",
            encoding="utf-8",
        )
        print(name)
