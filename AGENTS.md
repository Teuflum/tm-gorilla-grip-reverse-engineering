# Analysis repository guide

This repository owns the reverse engineering report, research scripts, and
graphs. The main explanation is `outputs/gorilla_grip_mechanism.md`; start
there and distinguish measured behavior, code observations, and hypotheses.
State the tested game build when making physics claims. See `README.md` for
the workflow and dependencies.

- Run `node --test graphs/model.test.js` for the offline graph/model checks.
  If a model value changes, update the report, interactive graph, static
  exports, and checks together.
- `work/` and `outputs/` contain both selected tracked files and ignored
  local data. Use `git ls-files` and review individual additions; do not
  force-add whole directories.
- The map and replay live one folder above this repository. Several scripts
  reference their current absolute paths.
- The local `Trackmania.exe`, Ghidra tools/projects, memory captures, TICK
  telemetry, and other generated files are research inputs, not publishable
  repository content. Keep TICK keys and runtime configuration local.
- TICK scripts and memory capture operate on a live game session. Run them
  only for a requested experiment, after checking the current map/input
  revision; preserve and restore user settings and selections. The memory
  capture scripts are read-only.
