# Gorilla Grip Rater design

## Purpose

Create an original Openplanet plugin that makes successful icy-tire airtime transitions satisfying to practice. It displays the normalized internal steering value that the physics code compares with ±0.1 when a verified exact read is available, then grades each eligible landing and tracks a combo. It must distinguish exact telemetry from any estimate.

## Player experience

- A compact neon arcade HUD shows internal steering, the ±10% direction gate, stored left/right mode, tire icing, contact/air phase, and force recovery status.
- On takeoff with sufficiently icy tires, it freezes the last grounded mode and starts an airtime meter. A long spin can add a style bonus, but style does not override an incorrect grip verdict.
- On landing it waits about 80 ms for the grounded physics update, then shows an S–E grade with a plain reason: no direction stored before takeoff, opposite direction stored, insufficient force recovery, no landing steering, or a successful pre-set direction.
- Successful transitions build a combo and score. A miss breaks it. A run reset clears the active combo but retains a visible previous-run summary.
- Settings control HUD position/scale, minimum icing and airtime, grade thresholds, and whether the HUD hides with the game UI.

## Measurement rules

- The exact source is the active physics vehicle's normalized smoothed steering at `vehicle+0x1430` on the tested build. The mode at `+0x14e5` and force multiplier at `+0x14dc` are read as corroborating fields. Raw input and VehicleState wheel angles are not substitutes.
- Read-only memory access requires a validated path to the current vehicle object on each map load/restart. Reject stale pointers using multiple independent fields and stop showing exact values if validation fails. Do not write game memory.
- The rater may use a visibly labeled estimate while the exact source is unavailable. A grade that claims an exact mode/force verdict requires verified exact telemetry; otherwise label it provisional or defer it.
- A candidate requires icy tires before airtime and a minimum airborne duration. Any wheel contact is the grounded boundary. The stored direction must match steering captured at visible contact (with up to 30 ms to catch the first grounded physics tick); a later steering change cannot change that landing direction. The force reading at least 80 ms after visible contact determines the grade. Icing, airtime, and steering thresholds are configurable filters, not claims of universal slide requirements.
- Account for display-frame sampling: show the actual source freshness, avoid claiming the precise last contact tick from VehicleState alone, and validate against the controlled TICK traces.

## Implementation constraints

- Use Openplanet's VehicleState for visible tire/position data and its NanoVG/UI APIs for presentation. Keep the source original; WiggleRater is a visual/interaction reference, not copied code.
- Include a deterministic, testable grading state machine outside the game where practical. Verify the plugin compiles and loads in the installed Openplanet environment.
- Push only original source, documentation, and tests. Do not push Trackmania, maps/replays, memory dumps, third-party plugins, or full telemetry CSVs.
