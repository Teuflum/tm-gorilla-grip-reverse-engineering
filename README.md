# Trackmania gorilla grip research

This repository contains the [mechanism report](outputs/gorilla_grip_mechanism.md) and the original scripts used to investigate instant ice-slide grip in the current Trackmania physics build. The report identifies a car-level slide-direction state, a strict ±0.1 threshold on smoothed steering, and an any-wheel contact condition. It includes the measured input and landing-speed pairs, the relevant function addresses, and the limits of the conclusion.

## Included

- `outputs/GorillaGripLogger/`: an Openplanet logger for visible vehicle and wheel telemetry. It requires the Openplanet **VehicleState** dependency.
- `work/tick_client.py`, `work/tick_events.py`, `work/setup_tick_automation.py`, and `work/auto_trials.py`: local TICK API access and automated replay variants.
- `work/scan_live_vehicle.py`, `work/capture_live_phy.py`, `work/capture_takeoff_memory.py`, and `work/analyze_phy_memory.py`: read-only vehicle-memory capture and analysis. The capture tools use Windows `ReadProcessMemory`; they never write to game memory.
- `work/create_*variants.py` and `work/analyze_jump3_trials.py`: controlled steering variants and landing-speed comparison.
- `work/scan_float_code_refs.py` and `work/ghidra_scripts/`: scripts used to locate and inspect the physics branch in a locally obtained game binary.

## Reproducing a local experiment

These are research scripts for the specific map and replay used in the report, rather than a packaged Openplanet release. You need your own legally obtained Trackmania installation, the map/replay, TICK, Openplanet, and VehicleState. Ghidra is needed only for the code-inspection scripts. `scan_float_code_refs.py` uses Python packages `pefile` and `capstone`.

1. Install `outputs/GorillaGripLogger` as an Openplanet script and ensure VehicleState is available.
2. Supply your own TICK baseline as `outputs/TICK_baseline_right.txt`, review the map UID and collection settings in `work/setup_tick_automation.py`, and run that setup script once. It writes `work/tick_automation_state.json` locally.
3. Generate variants with the relevant `work/create_*variants.py` script, then run `work/auto_trials.py <variant-names>`. The TICK client reads its key from TICK's local runtime configuration at execution time. No key is stored in this repository.
4. For a physics-memory check, first locate the current vehicle object with `work/capture_live_phy.py`; then use that process ID and object address with `work/capture_takeoff_memory.py`. The address changes when the game restarts. Analyze the captured file with `work/analyze_phy_memory.py`.

The scripts have case-specific coordinates, action times, and internal addresses. Verify those before using them with a different map or game build. The report's cited raw inputs, logs, memory snapshots, and decompilations remain in the original local workspace. They are deliberately not redistributed here, along with `Trackmania.exe`, the map, the replay, downloaded tools, and third-party source trees.
