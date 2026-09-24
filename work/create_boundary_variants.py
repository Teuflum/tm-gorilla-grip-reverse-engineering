"""Generate steering reversals on and just after the final contact tick."""

from pathlib import Path


root = Path(__file__).resolve().parent.parent / "outputs"


def write_variant(source_name, name, changes):
    source = root / f"TICK_{source_name}.txt"
    entries = {(int(ms), action): int(value)
               for ms, action, value in (line.split() for line in source.read_text().splitlines())}
    for tick, value in changes.items():
        entries[(tick * 10, "steer")] = value
    order = {"accel": 0, "brake": 1, "steer": 2, "seed": 3, "flags": 4}
    rows = sorted(entries.items(), key=lambda item: (item[0][0], order[item[0][1]]))
    (root / f"TICK_{name}.txt").write_text(
        "\n".join(f"{ms} {action} {value}" for (ms, action), value in rows) + "\n",
        encoding="utf-8",
    )
    print(name)


write_variant("right_through_1131", "last_rr_left_1131_air", {1131: -127})
write_variant("right_through_1131", "last_rr_neutral_1131_air", {1131: 0})
write_variant("jump3_left_13_from_941_through_946", "last_fl_right_945_ground", {945: 127, 946: -13})
write_variant("jump3_left_13_from_941_through_946", "last_fl_neutral_945_ground", {945: 0, 946: -13})
write_variant("jump3_left_13_from_941_through_946", "last_fl_right_946_air", {946: 127})
