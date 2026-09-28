# What an early countersteer costs before a jump

Measured on 28 September 2026 on `ANGULAR _ MOMENTUM.Map.Gbx`, Stadium car, with TICK replaying the TAS input and the Gorilla Grip Trainer's exact physics reads active (its build-signature check passed). The question: if the slide-direction switch commits earlier than the last possible tick before takeoff, how much speed does that cost? The Trainer grades this lead time (S+ 0 ms, S ≤ 10, A ≤ 30, B ≤ 60, C ≤ 110, D ≤ 250 ms).

## Setup

The jump is the 11.31 s takeoff used in the [mechanism report](gorilla_grip_mechanism.md) (rear-right wheel last, landing near 12.58 s). The TAS holds full left and switches to `steer 78` at 11260 ms; the smoothed steering crosses +0.1 on the takeoff tick, so the baseline commits right mode at 11310 ms with a **lead of 0 ms**. Each variant moves only that one action earlier by 10, 20, 30, 50, 70, 100, 150 or 200 ms. Everything else, including the air and landing inputs, stays the same.

The Trainer's own log reported a lead equal to the shift in every run, and every landing had full tire force (`2.0`): with 1.26–1.28 s of flight, the mode age is past the 800 ms cutoff at touchdown however late the switch is. On this jump the early switch has no force benefit at all, so any difference is the cost of the switch.

Speed and position come from TICK's live telemetry (about every 35 ms at 1× game speed, interpolated). Positions are projected onto the path of the lead-0 run, so "behind" means distance along the same line. The lead-0 run was repeated at the start and end; the two runs agree within 0.01 km/h and 0.01 m.

## Results

| Lead (ms) | Trainer grade | Takeoff speed (km/h) | Lost at takeoff (km/h) | Behind just before touchdown | Landing slip angle |
|---:|:---:|---:|---:|---:|---:|
| 0 | S+ | 220.79 | 0 | 0 | 108° |
| 10 | S | 220.78 | 0.01 | 0.01 m (0.2 ms) | 106° |
| 20 | A | 220.77 | 0.02 | 0.03 m (0.5 ms) | 104° |
| 30 | A | 220.74 | 0.05 | 0.04 m (0.6 ms) | 102° |
| 50 | B | 220.58 | 0.21 | 0.10 m (1.5 ms) | 99° |
| 70 | C | 220.39 | 0.40 | 0.20 m (3.0 ms) | 95° |
| 100 | C | 219.99 | 0.80 | 0.34 m (5.1 ms) | 89° |
| 150 | D | 219.14 | 1.65 | 0.71 m (10.7 ms) | 80° |
| 200 | D | 218.15 | 2.64 | 1.15 m (17.3 ms) | 71° |

"Behind just before touchdown" is measured at race time 12.56 s, when every variant is still in the air, and converted to time at the car's speed then (66.4 m/s). It is the cost carried out of the takeoff, before the landing changes anything.

**The loss grows faster than the lead.** Doubling the lead from 50 to 100 ms roughly quadruples the takeoff speed loss (0.21 → 0.80 km/h); 200 ms costs 2.64 km/h, 1.2% of the car's speed. Up to 30 ms the cost is within a few hundredths of a km/h. On the ground, the countersteer steers the car against its slide while the tire-force multiplier has just been reset to `1.0`, and the car's velocity also turns by up to 1.8° (lead 200), so the car lands up to 2.7 m off the lead-0 line.

**The early switch also changes the landing angle.** The countersteer on the ground takes yaw rotation out of the car before takeoff. With the same air inputs, the car lands at 108° slip for lead 0 and 71° for lead 200, about 0.18° less per millisecond of lead. After touchdown this dominates the speed: the early variants scrubbed less speed in the landing slide, and 30 m after touchdown the lead-200 run was going 232.7 km/h against 221.1 km/h for lead 0, although it reached that point 27 ms later. Further on, the paths drift 3–9 m apart under the fixed replay inputs and the comparison stops being meaningful. A player would steer the spin differently to land at the angle they want, so this landing-angle difference is a side effect of keeping the TAS inputs fixed, not a benefit of switching early.

## What this means for the grade limits

The takeoff speed loss at each grade boundary, interpolated from the table, is roughly:

| Boundary | Lost at takeoff |
|---|---:|
| S (10 ms) | 0.01 km/h |
| A (30 ms) | 0.05 km/h |
| B (60 ms) | ~0.3 km/h |
| C (110 ms) | ~1.0 km/h |
| D (250 ms) | ~4 km/h (extrapolated; 200 ms measured 2.6) |

Each grade step costs about three to six times the one before, so the current limits already follow the shape of the measured cost. **The data supports keeping them as they are.** S+, S and A are separated by timing precision rather than by speed: nothing below 30 ms is measurable in speed on this jump. The data also supports Teuflum's rule that a later switch is better when the jump is long enough: here every lead reached full force on landing, and every millisecond of lead only cost speed before takeoff.

## Limits of this measurement

- One jump, one map, one takeoff state. This car took off almost straight (5–12° slip), so the countersteer had little slide left to kill; a takeoff from a deep slide may lose more per millisecond.
- On a short jump (under ~800 ms from switch to touchdown) an earlier switch buys tire force on landing; this jump cannot show that trade-off.
- The post-landing speed is confounded by the landing angle under fixed inputs, as described above. The takeoff speed and the in-air deficit are the clean numbers.

## Reproducing

`work/countersteer_lead_trials.py --pid <Trackmania PID> --leads 0 10 20 30 50 70 100 150 200 0` replays the variants in the Analysis automation collection (never the user's collection) and restores the active collection afterwards. It needs the map loaded, TICK running, and Trainer event logging on. `work/analyze_countersteer_lead.py` prints the table above from the saved telemetry and Trainer log lines in `outputs/countersteer_lead/` (local data, not tracked).
