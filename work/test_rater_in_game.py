"""Controlled in-game regression checks for Gorilla Grip Rater.

Requires Trackmania on ANGULAR ↻ MOMENTUM, TICK, GorillaGripLogger, and the
installed GorillaGripRater. Runs the existing automated variants; it does not
modify game memory. The logs and generated CSVs remain local.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
LOG = Path.home() / "OpenplanetNext/Openplanet.log"


def trial_log(variant: str, region: str = "target") -> str:
    offset = LOG.stat().st_size
    args = [sys.executable, str(ROOT / "work/auto_trials.py")]
    if region != "target":
        args.extend(["--region", region])
    args.append(variant)
    completed = subprocess.run(
        args,
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=180,
    )
    if completed.returncode:
        raise AssertionError(f"TICK {variant} failed:\n{completed.stdout}\n{completed.stderr}")
    with LOG.open("rb") as handle:
        handle.seek(offset)
        return handle.read().decode("utf-8", "replace")


def verdict_at(log: str, start_ms: int, end_ms: int) -> tuple[int, str, float]:
    pattern = re.compile(
        r"Gorilla Grip Rater verdict at (\d+)ms.*?: ([A-Z]+)( ~)? \|.*?landing force ([0-9.]+) \| exact (true|false)"
    )
    for match in pattern.finditer(log):
        t = int(match.group(1))
        if start_ms <= t <= end_ms:
            assert match.group(3) is None, f"Provisional verdict at {t}ms: {match.group(0)}"
            assert match.group(5) == "true", f"Inexact verdict at {t}ms: {match.group(0)}"
            return t, match.group(2), float(match.group(4))
    raise AssertionError(f"No rater verdict between {start_ms} and {end_ms} ms")


def first_draw_at(log: str, start_ms: int, end_ms: int) -> int:
    pattern = re.compile(r"Gorilla Grip Rater first popup draw at (\d+)ms")
    for match in pattern.finditer(log):
        t = int(match.group(1))
        if start_ms <= t <= end_ms:
            return t
    raise AssertionError(f"No first popup draw between {start_ms} and {end_ms} ms")


def make_post_contact_reversal() -> None:
    """Keep the baseline jump, then reverse steering just after its first contact."""
    source = (ROOT / "outputs/TICK_baseline_right.txt").read_text(encoding="utf-8")
    needle = "6250 accel 1"
    assert source.count(needle) == 1
    source = source.replace(needle, "6200 steer -127\n" + needle + "\n6300 steer 127")
    (ROOT / "outputs/TICK_reverse_after_first_landing.txt").write_text(source, encoding="utf-8")


def main() -> None:
    baseline = trial_log("baseline_right")
    landing = re.search(r"Gorilla Grip Rater landing (6\d\d\d)ms", baseline)
    assert landing is not None, "First icy landing not observed"
    landing_t = int(landing.group(1))
    verdict_t, grade, force = verdict_at(baseline, 6150, 6350)
    draw_t = first_draw_at(baseline, 6150, 6350)
    assert grade == "S", f"First icy landing should rate S, got {grade} at {verdict_t}ms"
    assert force >= 1.95, f"First icy landing's checked force should recover, got {force}x"
    assert 0 <= verdict_t - landing_t <= 120, (landing_t, verdict_t)
    assert 0 <= draw_t - landing_t <= 120, (landing_t, draw_t)
    print(f"baseline: landing {landing_t}ms, S at {verdict_t}ms, first draw {draw_t}ms")

    delayed = trial_log("right_12_from_1126_through_1131")
    verdict_t, grade, force = verdict_at(delayed, 12550, 12750)
    assert grade == "E", f"Wrong pre-takeoff direction should rate E, got {grade}"
    assert force <= 1.1, f"Wrong-direction landing should reset force, got {force}x"
    print(f"wrong-direction: E at {verdict_t}ms, force {force}x")

    make_post_contact_reversal()
    reversed_after_contact = trial_log("reverse_after_first_landing", "jump2")
    landing = re.search(r"Gorilla Grip Rater landing (6\d\d\d)ms, air .*? steer ([0-9.eE+-]+)", reversed_after_contact)
    assert landing is not None, "First landing in reversal variant not observed"
    assert float(landing.group(2)) > 0.1, f"Touchdown steering was not right: {landing.group(0)}"
    verdict_t, grade, force = verdict_at(reversed_after_contact, 6150, 6350)
    assert grade != "E", (
        f"Touchdown was right-steered, so a later reversal must not become a wrong-direction E; "
        f"got {grade} at {verdict_t}ms"
    )
    print(f"post-contact reversal: {grade} at {verdict_t}ms, force {force}x")


if __name__ == "__main__":
    main()
