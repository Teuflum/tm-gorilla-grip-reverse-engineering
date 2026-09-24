"""Generate focused takeoff steering interventions from the immutable baseline."""

from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
base = []
for line in (ROOT / "outputs/TICK_baseline_right.txt").read_text(encoding="utf-8").splitlines():
    ms, action, value = line.split()
    base.append((int(ms) // 10, action, int(value)))


def variant(name, *, start, release, strength=78, release_value=-127):
    entries = [a for a in base if a != (1126, "steer", 78)]
    entries += [(start, "steer", strength), (release, "steer", release_value)]
    entries.sort(key=lambda row: (row[0], {"accel": 0, "brake": 1, "steer": 2, "seed": 3, "flags": 4}[row[1]]))
    if len({(tick, action) for tick, action, _ in entries}) != len(entries):
        raise ValueError(f"Duplicate action at same tick in {name}")
    output = ROOT / f"outputs/TICK_{name}.txt"
    output.write_text("\n".join(f"{tick * 10} {action} {value}" for tick, action, value in entries) + "\n", encoding="utf-8")
    print(name, [(tick, action, value) for tick, action, value in entries if 1123 <= tick <= 1133])


variant("right_from_1125_through_1129", start=1125, release=1130)
variant("right_78_then_neutral_at_1131", start=1126, release=1131, release_value=0)
variant("right_10_from_1126_through_1131", start=1126, release=1132, strength=10)
variant("right_1_from_1126_through_1131", start=1126, release=1132, strength=1)
for amount in (20, 30, 40, 44):
    variant(f"right_{amount}_from_1126_through_1131", start=1126, release=1132, strength=amount)
variant("right_127_from_1126_through_1130", start=1126, release=1131, strength=127)
for amount in (11, 12, 13, 14, 15, 16, 18, 19):
    variant(f"right_{amount}_from_1126_through_1131", start=1126, release=1132, strength=amount)
variant("right_12_from_1125_through_1130", start=1125, release=1131, strength=12)
variant("right_13_from_1125_through_1130", start=1125, release=1131, strength=13)
variant("right_from_1124_through_1129", start=1124, release=1130, strength=78)
variant("right_from_1123_through_1128", start=1123, release=1129, strength=78)
