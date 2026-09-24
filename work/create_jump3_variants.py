"""Generate one-variable steer-start tests for the earlier FL-last ice jump."""

from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
base = []
for line in (ROOT / "outputs/TICK_baseline_right.txt").read_text(encoding="utf-8").splitlines():
    ms, action, value = line.split()
    base.append((int(ms), action, int(value)))

for start_tick in (940, 942, 943, 944, 945, 946, 947, 948):
    entries = [event for event in base if event != (9410, "steer", -123)]
    entries.append((start_tick * 10, "steer", -123))
    entries.sort(key=lambda row: (row[0], {"accel": 0, "brake": 1, "steer": 2, "seed": 3, "flags": 4}[row[1]]))
    assert len(entries) == len(base)
    assert len({(ms, action) for ms, action, _ in entries}) == len(entries)
    name = f"jump3_left_from_{start_tick}"
    (ROOT / f"outputs/TICK_{name}.txt").write_text(
        "\n".join(f"{ms} {action} {value}" for ms, action, value in entries) + "\n",
        encoding="utf-8",
    )
    print(name)

for strength in (12, 13, 20):
    entries = [event for event in base if event != (9410, "steer", -123)]
    entries.extend(((9410, "steer", -strength), (9470, "steer", -123)))
    entries.sort(key=lambda row: (row[0], {"accel": 0, "brake": 1, "steer": 2, "seed": 3, "flags": 4}[row[1]]))
    assert len({(ms, action) for ms, action, _ in entries}) == len(entries)
    name = f"jump3_left_{strength}_from_941_through_946"
    (ROOT / f"outputs/TICK_{name}.txt").write_text(
        "\n".join(f"{ms} {action} {value}" for ms, action, value in entries) + "\n",
        encoding="utf-8",
    )
    print(name)
