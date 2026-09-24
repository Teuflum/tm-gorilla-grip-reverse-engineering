"""Test whether extra grounded steering time rescues sub-0.1 input."""

from pathlib import Path


root = Path(__file__).resolve().parent.parent / "outputs"
source = root / "TICK_right_through_1131.txt"
original = {(int(ms), action): int(value)
            for ms, action, value in (line.split() for line in source.read_text().splitlines())}
order = {"accel": 0, "brake": 1, "steer": 2, "seed": 3, "flags": 4}
for start, value in ((1124, 12), (1124, 13), (1123, 12)):
    entries = original.copy()
    entries.pop((11260, "steer"))
    entries[(start * 10, "steer")] = value
    entries[(11310, "steer")] = -127
    rows = sorted(entries.items(), key=lambda item: (item[0][0], order[item[0][1]]))
    name = f"right_{value}_from_{start}_through_1130"
    (root / f"TICK_{name}.txt").write_text(
        "\n".join(f"{ms} {action} {amount}" for (ms, action), amount in rows) + "\n",
        encoding="utf-8",
    )
    print(name)
