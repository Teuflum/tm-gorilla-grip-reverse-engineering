# What an early countersteer costs before a jump

Measured on 28 September 2026 on `ANGULAR _ MOMENTUM.Map.Gbx`, Stadium car, with TICK replaying the TAS input and the Gorilla Grip Trainer's exact physics reads active (its build-signature check passed). The question: if the slide-direction switch commits earlier than the last possible tick before takeoff, how much speed does that cost? The Trainer grades this lead time (S+ 0 ms, S ≤ 10, A ≤ 30, B ≤ 60, C ≤ 110, D ≤ 250 ms).

Two jumps were tested. The first ice jump (takeoff 5.27 s) leaves the ground in a deep slide, 111–126° off the direction of travel. The third (takeoff 11.31 s) leaves almost straight, at 5–12°. The same lead cost 10 to 60 times more speed on the deep-slide jump.

In both jumps every run landed with full tire force (`2.0`): the flights last 0.8–1.3 s, so the mode age is past the 800 ms cutoff at touchdown however late the switch is. An early switch has no force benefit on these jumps, so any difference is its cost. The Trainer's own log reported the lead of every run.

Speed and position come from TICK's live telemetry (about every 35 ms at 1× game speed, interpolated). Positions are projected onto the path of the lead-0 run, so "behind" means distance along the same line. "Behind in the air" is taken at a moment when every variant is still airborne and converted to time at the reference car's speed then; it is the cost carried out of the takeoff, before the landing changes anything.

## First ice jump, 5.27 s: deep slide, landing angle matched

The TAS switches with a short right pulse (`104`, `54`, `-126`, `0` from 5200 ms), a lead of 20 ms. For a clean series the variants hold full left, then `steer 104` from 50 ms before the intended commit until the takeoff tick; the smoothed steering crosses +0.1 five ticks after the input. The lead-0 run is the reference. The air and landing inputs from 5620 ms are the TAS's own.

**Matching the landing angle.** Air steering here acts like a switch rather than a dial: `+2` and `+127` between takeoff and 5620 ms gave the same landing (150° slip), and every negative value gave about 178°. A left pulse of `-127` held for 10–50 ms after takeoff was the fine control. Each lead got the shortest pulse that brought its landing slip (measured by the Trainer at first contact) back to the reference's 158°. The lead-0 reference was repeated; both runs landed at 158° and differ by 0.09 km/h at takeoff.

| Lead (ms) | Trainer grade | Air input after takeoff | Landing slip | Takeoff speed (km/h) | Lost at takeoff (km/h) | Behind in the air | Lands short |
|---:|:---:|---|---:|---:|---:|---:|---:|
| 0 | S+ | none | 158° | 188.51 | 0 | 0 | 0 |
| 10 | S | none | 159° | 187.73 | 0.78 | 0.21 m (4 ms) | 0.2 m |
| 20 | A | none | 158° | 186.68 | 1.83 | 0.44 m (8 ms) | 1.1 m |
| 30 | A | none | 158° | 185.59 | 2.92 | 0.70 m (13 ms) | 1.9 m |
| 50 | B | none | 158° | 183.37 | 5.14 | 1.25 m (23 ms) | 3.1 m |
| 70 | C | none | 157° | 180.58 | 7.93 | 1.92 m (35 ms) | 4.3 m |
| 100 | C | left for 10 ms | 158° | 176.58 | 11.93 | 2.96 m (54 ms) | 6.5 m |
| 160 | D | left for 30 ms | 159° | 169.44 | 19.07 | 4.80 m (87 ms) | 9.5 m |
| 220 | D | left for 50 ms | 158° | 161.92 | 26.59 | 6.84 m (124 ms) | 13.5 m |

"Behind in the air" is at race time 6.07 s (reference speed 55.6 m/s). The 150 and 200 ms inputs measured as 160 and 220 ms leads because the slower car reached the lip 10–20 ms later.

**The loss is roughly linear and large.** Each millisecond of lead costs about 0.1 km/h at takeoff and about half a millisecond of time by touchdown. Even the S band costs 0.8 km/h. The countersteer brakes a car that is sliding sideways: the multiplier has just been reset to `1.0` and the tires now push against the slide. The slower car also makes a shorter jump and lands up to 13.5 m short of the reference touchdown point and 5.7 m off its line.

**After touchdown the speeds converge, the lost time does not come back on its own.** Landing at 158° with full force sheds speed quickly: one second after each run's own touchdown, all variants were between 160 and 165 km/h. Because the shorter jumps land somewhere else, positions after touchdown cannot be compared on the same line, so this measurement stops at the in-air deficit.

## Third ice jump, 11.31 s: almost straight takeoff

This is the jump used in the [mechanism report](gorilla_grip_mechanism.md) (rear-right wheel last, landing near 12.58 s). The TAS holds full left and switches to `steer 78` at 11260 ms, committing right mode on the takeoff tick (lead 0 ms). Each variant moves only that action earlier; all other inputs stay the same. The lead-0 run was repeated at the start and end; the two runs agree within 0.01 km/h and 0.01 m.

| Lead (ms) | Trainer grade | Takeoff speed (km/h) | Lost at takeoff (km/h) | Behind in the air | Landing slip (air inputs not matched) |
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

"Behind in the air" is at race time 12.56 s (66.4 m/s).

**The loss grows faster than the lead but stays small.** Doubling the lead from 50 to 100 ms roughly quadruples the takeoff speed loss; up to 30 ms it is within a few hundredths of a km/h. With the car already pointing almost where it travels, the countersteer has little slide to kill.

**Here the early switch changed the landing angle a lot.** The countersteer on the ground took yaw rotation out of the car, and with unchanged air inputs the landing slip fell from 108° to 71°. After touchdown this dominated the speed: 30 m after touchdown the lead-200 run was going 232.7 km/h against 221.1 km/h, although it got there 27 ms later. The angle was not matched on this jump, so its post-landing speeds say nothing about switch timing. On the 5.27 s jump the same effect was small (158° to 155° at lead 220 before matching).

## What this means for the grade limits

Cost at each grade boundary, interpolated from the tables (the D value extrapolated from the longest measured lead):

| Boundary | Deep slide, 5.27 s: speed / time | Straight, 11.31 s: speed |
|---|---:|---:|
| S (10 ms) | 0.8 km/h / 4 ms | 0.01 km/h |
| A (30 ms) | 2.9 km/h / 13 ms | 0.05 km/h |
| B (60 ms) | ~6.5 km/h / ~29 ms | ~0.3 km/h |
| C (110 ms) | ~13 km/h / ~60 ms | ~1.0 km/h |
| D (250 ms) | ~30 km/h / ~140 ms | ~4 km/h |

**The data supports keeping the limits as they are.** On both jumps the cost rises steadily through S, A, B, C and D, so the grades rank switches by what they cost. How much each grade costs depends on how deep the slide is at takeoff, which a lead-only grade cannot see: from a deep slide every 10 ms is worth about 1 km/h and 5 ms, so even the tight S and A bands matter; from an almost straight takeoff nothing below 30 ms is measurable. Both jumps support Teuflum's rule that a later switch is better when the flight is long enough for full force: every lead reached full force on landing, and every millisecond of lead only cost speed.

## Conclusion for play

On maps built for the current ice physics, where jumps give enough airtime, **countersteer as late as possible, but early enough that the grip is back when the front wheels land.** Once the switch plus the flight reach about 800 ms before a front wheel touches, every extra millisecond of lead only costs speed; both jumps here measured that. On a short hop an earlier switch helps only until the grip is fully back at touchdown, and any lead beyond that is lost; this part comes from the code and the landing traces. A lead series on two short hops is in [Early countersteer on short hops](countersteer_short_hops.md): there an earlier switch beat the latest one on both hops, and the latest sensible switch was bounded by where the slide changes side. Countersteering early on purpose to slow down and land sooner, for example to make a turn right after a short jump on a map not built for this physics, is a line choice that trades speed for position; it does not contradict the rule.

## Limits of this measurement

- Two jumps on one map. The takeoff slip angle looks like the main factor; other jumps can fall anywhere between the two.
- On a short jump (under ~800 ms from switch to touchdown) an earlier switch buys tire force on landing; neither jump can show that trade-off. [Early countersteer on short hops](countersteer_short_hops.md) measures it on two hops and a grounded reversal.
- The landing angle was matched through the slip at first contact only. Yaw rate and the exact touchdown spot still differ between leads.
- The takeoff speed and the in-air deficit are the clean numbers. After touchdown, the 11.31 s results are confounded by the unmatched landing angle, and the 5.27 s runs land in different places.

## Reproducing

Both scripts replay variants in the Analysis automation collection, never the user's collection, and restore the active collection afterwards. They need the map loaded, TICK running, and Trainer event logging on. Telemetry and Trainer log lines are saved as local data (not tracked).

- 5.27 s jump: `work/jump1_lead_trials.py --pid <PID> probe 0:0 10:0 20:0 30:0 50:0 70:0 100:-127:10 150:-127:30 200:-127:50` (arguments are lead, air steer and, optionally, how long the air steer is held). `match <leads>` searches a constant air steer; that does not converge here because air steering acts like a switch. `work/analyze_jump1_lead.py` prints the table.
- 11.31 s jump: `work/countersteer_lead_trials.py --pid <PID> --leads 0 10 20 30 50 70 100 150 200 0`, then `work/analyze_countersteer_lead.py`.
