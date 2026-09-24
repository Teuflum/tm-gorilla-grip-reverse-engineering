"""Insert grounded neutral-steer intervals into the existing TICK replay."""

from pathlib import Path


source = Path("outputs/TICK_baseline_right.txt")
baseline = [line for line in source.read_text(encoding="utf-8").splitlines() if line.strip()]
for duration, return_tick in ((100, 4800), (400, 5100)):
    target = Path(f"outputs/TICK_neutral_{duration}ms_ice.txt")
    actions = baseline + ["4700 steer 0", f"{return_tick} steer -127"]
    actions.sort(key=lambda line: int(line.split()[0]))
    target.write_text("\n".join(actions) + "\n", encoding="utf-8")
    print(target, len(actions), "actions")
