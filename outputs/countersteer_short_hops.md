# Early countersteer on short hops

Measured on 28 September 2026 on a map Teuflum had loaded (UID `pBoO2N5xKZRTuOGcVBRuoOCbhM3`), Stadium car, on the same `Trackmania.exe` as the [mechanism report](gorilla_grip_mechanism.md) (SHA-256 `3FC7D8CD…6EDDA`). TICK replayed Teuflum's TAS input with one change per run, and the Gorilla Grip Trainer 0.3.0 logged its exact physics reads. This note fills the gap left by the [long-jump measurement](countersteer_lead_cost.md): there every flight was long enough for full tire force on landing, so an early switch could only cost. On a hop shorter than the force timer, an earlier switch also brings the grip back sooner. The question is which effect wins.

**Short answer.** On both hops an earlier switch beat the latest one. On the 13.3 s hop every lead from 10 to 200 ms was faster than a switch on the takeoff tick; the best was about 150 ms, and no break-even appeared before the car's line ran into a hole (from 290 ms). On the 20.3 s hop a switch at takeoff is not playable (the car leaves the ramp at 110 km/h); earlier than Teuflum's own lead (610 ms, 600 ms in the replay) was faster up to 730 ms, and the gain was gone again at 790 ms, so the break-even against 600 ms lies near 790 ms (about 930 ms from switch to front touchdown). The flat-ground reversal shows why: switching costs speed while the slide is still closing, and holding the old direction at full force costs speed once the slide has changed side. Where that side change lies decides whether an earlier switch pays, more than the length of the flight does.

## Method

Each variant holds full right and steps to full left (`steer -127`) on one tick; the stored direction flips 50 ms later (smoothed steering moves 0.2 per tick). "Lead" is takeoff tick minus the flip tick, read from the Trainer's snapshots (`modeAt`, contact bits) and equal to the Trainer's own lead where it graded the jump. Every other input is Teuflum's. The game ran at 0.2× only inside each hop's window, so the Trainer logged a snapshot on nearly every 10 ms tick; physics ticks are unchanged by game speed. Force values are the Trainer's tire-force multiplier (`vehicle+0x14dc`) at the tick named.

Positions come from TICK telemetry, projected onto the reference run's path. "Ahead" is the distance along that path at a fixed race time, also given in milliseconds at the reference speed; fixed race times mean every run had played the same inputs up to that moment. Runs that drift more than a few metres off the reference line are only compared up to where they stay close; the tables give the distance off the line. Repeated reference runs matched to 0.003 m.

**The landing angle was not matched.** Air steering needs tens of milliseconds to do anything, and these flights last 110–160 ms. The landing slip is listed instead. On the 13.3 s hop it moved from 63° to 55° over the valid leads; on the 20.3 s hop from 126° to 80°.

## Why the 20.3 s hop was not rated

Teuflum's switch there flips the stored direction at 19.71 s. The car stays on the ground up the ramp and takes off at 20.32 s, a lead of 610 ms. The Trainer publishes a timing preview only for leads up to `S_DMaxLeadMs` (250 ms, the D limit), so this takeoff got no preview and no cue. The landing then kept the same direction with the force at 1.99, which resolves silently (`landing resolved without verdict … force 2.000`). The jump passed every eligibility filter; only the lead was outside the graded range. It was measured like the other hop. The Trainer's grading is unchanged.

## Hop A, 13.3 s takeoff: 110 ms flight

The car leaves flat ice over a small drop (0.25 m) at 194–200 km/h and touches down with the front wheels 110 ms later. Teuflum's own switch had a lead of 190 ms. The reference is lead 0: the direction flips on the takeoff tick itself (Trainer grade S+).

| Lead (ms) | Trainer grade | Switch to front touchdown (ms) | Landing slip | Force at touchdown / +200 / +400 ms | Force 2.0 after touchdown (ms) | Takeoff speed (km/h) | Faster at takeoff (km/h) | Ahead at 13.8 s | Ahead at 14.1 s | Speed at 14.1 s (km/h) | Off the line at 14.1 s |
|---:|:---:|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 0 | S+ | 110 | 63° | 1.0 / 1.0 / 1.6 | 480 | 193.89 | 0 | 0 | 0 | 195.3 | 0 |
| 10 | S | 120 | 63° | 1.0 / 1.0 / 1.65 | 470 | 194.10 | 0.21 | 0.04 m (1 ms) | 0.10 m (2 ms) | 196.2 | 0.0 m |
| 20 | A | 130 | 62° | 1.0 / 1.0 / 1.7 | 460 | 194.30 | 0.41 | 0.08 m (2 ms) | 0.20 m (4 ms) | 196.9 | 0.1 m |
| 30 | A | 140 | 62° | 1.0 / 1.0 / 1.75 | 450 | 194.53 | 0.64 | 0.11 m (2 ms) | 0.28 m (5 ms) | 198.2 | 0.2 m |
| 50 | B | 160 | 62° | 1.0 / 1.0 / 1.85 | 430 | 195.03 | 1.14 | 0.19 m (4 ms) | 0.49 m (9 ms) | 199.8 | 0.4 m |
| 100 | C | 210 | 61° | 1.0 / 1.1 / 2.0 | 380 | 196.26 | 2.37 | 0.45 m (9 ms) | 1.14 m (21 ms) | 205.0 | 0.8 m |
| 150 | D | 260 | 58° | 1.0 / 1.33 / 2.0 | 400 | 197.10 | 3.21 | 0.70 m (13 ms) | 1.81 m (33 ms) | 213.4 | 1.5 m |
| 200 | D | 310 | 55° | 1.0 / 1.4 / 1.76 | 610 | 197.68 | 3.79 | 0.69 m (13 ms) | 1.62 m (30 ms) | 215.6 | 2.9 m |
| 290 | none | 410 | 47° | 1.0 / 1.0 / 1.62 | — | 198.69 | 4.80 | falls into a hole after the drop | | | |
| 400 | none | 510 | 30° | 1.01 / 1.0 / 1.0 | — | 199.83 | 5.94 | falls into a hole after the drop | | | |

**Every lead reached the front touchdown with the force still at 1.0.** Switch to touchdown was 110–310 ms, inside the 400 ms hold. An earlier switch also put the car on a different line, and from about 290 ms that line ended in a hole in the track (Teuflum confirmed the crashes). The playable range here stops before the grip could be back on landing.

**The earlier switch still won, from two sources.**

1. *Before takeoff.* The slide changed side near 12.79 s (telemetry slip −7° at 12.70 s, +10° at 12.88 s) and then opened towards the new side: +28° at 13.06 s, +53° at 13.30 s. Holding full right at force 2.0 through that phase cost the lead-0 run 5.3 km/h between 13.06 s and takeoff; the lead-200 run, at force 1.0 and countersteering from 13.10 s, lost 1.6 km/h. That is the takeoff-speed column.
2. *After touchdown.* An earlier switch starts the force ramp earlier. At 13.54 s, with the force still near 1.0 in both runs, lead 200 was 3.4 km/h faster than lead 0; at 13.84 s, after its force had come back, it was 15.1 km/h faster. That gap made up most of the distance gained by 14.1 s.

**The flight did not change the force timer.** With switch to touchdown under 400 ms, the force stays 1.0 through the flight anyway and ramps from 400 ms after the switch once both front wheels are down. The grounded runs below have the same force at the same age for leads 0–150 (identical up to 100 ms, within 0.03 at 150 ms) (1.0, 1.0, then 1.1–1.85 at +400 ms). Lead 200's slower rise is the target rising with the slide, not the timer: the force tracked a target that climbed from 1.56 to 2.0 over 13.68–14.04 s, consistent with the target's dependence on the front wheels' lateral velocity in the [speed-force curve](speed_force_curve.md).

The best measured lead was about 150 ms. Lead 200 gained more at takeoff but touched down with less slip, its force target came back more slowly, and it was 0.2 m behind lead 150 at 14.1 s.

## Hop B, 20.3 s takeoff: 160 ms flight up a ramp

The car slides over flat ice, meets the foot of an uphill ramp near 19.9 s, and hops off a bump in it at 20.30–20.35 s, landing on the front wheels 140–170 ms later. Leads of 0 and 10 ms mean holding full right up the ramp: the car took off at 109–113 km/h and went off the track. The reference replays Teuflum's own switch: the step flips the direction on the same tick (19.71 s) as Teuflum's input, and the car leaves 10 ms sooner, so it measures 600 ms against the original 610.

| Lead (ms) | Switch to front touchdown (ms) | Landing slip | Force at takeoff | Force at touchdown / +100 / +200 ms | Takeoff speed (km/h) | Against lead 600 (km/h) | Ahead at 20.8 s | Ahead at 21.0 s | Speed at 21.0 s (km/h) | Off the line at 21.0 s |
|---:|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|
| 480 | 640 | 126° | 1.33 | 1.34 / 1.73 / 2.0 | 175.80 | −13.99 | −2.71 m (−56 ms) | −3.35 m (−73 ms) | 142.1 | 3.4 m |
| 520 | 680 | 123° | 1.53 | 1.55 / 1.94 / 2.0 | 179.87 | −9.92 | −1.86 m (−38 ms) | −2.25 m (−49 ms) | 148.6 | 2.6 m |
| 560 | 720 | 120° | 1.73 | 1.75 / 2.0 / 2.0 | 184.04 | −5.75 | −1.05 m (−22 ms) | −1.28 m (−28 ms) | 154.2 | 1.7 m |
| 600 | 770 | 114° | 1.95 | 1.99 / 2.0 / 2.0 | 189.79 | 0 | 0 | 0 | 164.3 | 0 |
| 640 | 800 | 110° | 2.0 | 2.0 / 2.0 / 2.0 | 193.28 | +3.49 | +0.51 m (+11 ms) | +0.48 m (+10 ms) | 170.3 | 1.8 m |
| 680 | 850 | 104° | 2.0 | 2.0 / 2.0 / 2.0 | 198.31 | +8.52 | +1.11 m (+23 ms) | +1.12 m (+25 ms) | 179.8 | 3.8 m |
| 730 | 890 | 94° | 2.0 | 2.0 / 2.0 / 2.0 | 202.28 | +12.49 | +1.45 m (+30 ms) | +1.33 m (+29 ms) | 189.0 | 6.6 m |
| 790 | 930 | 80° | 1.68 | 1.68 / 2.0 / 2.0 | 196.72 | +6.93 | −0.07 m (−1 ms) | −0.91 m (−20 ms) | 189.4 | 9.7 m |

The 730 and 790 runs hit something near 21.2–21.4 s (speed −40 km/h, force back to 1.0), and all runs from 680 on drift several metres off the reference line, so the comparison stops at 21.0 s.

**Here the force timer is visible.** The flight pauses the ramp (no front-wheel contact), so the force at touchdown equals the force at takeoff, and that depends on how long the car was on the ground after the 400 ms hold. From lead 640 (800 ms switch to touchdown) the force was back to 2.0 before takeoff.

**Both sources again.** Against lead 480, Teuflum's lead 600 was 7.6 km/h faster at 19.86 s, when lead 480 had just switched. The gap came from 160 ms of full right at force 2.0 while the slide opened from +42° to +60°. From 19.86 s to 20.10 s both runs were at force 1.0 and the gap stayed at 8 km/h. It grew to 14 km/h by takeoff while lead 600's force came back (1.0 to 1.95) and lead 480's stayed at 1.0. Against lead 600, lead 680 gained 2 km/h before 20.02 s and 6.5 km/h over the next 280 ms up the ramp, while its force was already back.

**Too early turns it around again.** This slide changed side near 19.35 s (telemetry slip −4° at 19.32 s, +4° at 19.38 s). Lead 790 flips at 19.52 s, when the new slide is only about +20° wide. Its force target stayed lower (1.68 at takeoff), it landed at 80° slip on a different line, and by 21.0 s it was behind lead 600.

## Grounded-only reversal: the same step on flat ice

The same full-right to full-left step, placed on flat ice (height constant to 0.05 m) from 18.5 to 19.1 s, with no jump in the compared window. 19.10 s stands in for the takeoff: speed 199 km/h and a 30° slip, like hop A's switch. Unlike on hop A, the slide there was still closing: telemetry slip −77° at 18.3 s, −41° at 19.0 s, −13° at 19.3 s. Lead 0 (the flip at 19.10 s) is the reference.

| Lead (ms) | Speed at 19.10 s (km/h) | Lost (km/h) | Force at +110 / +310 / +510 ms | Ahead at 19.6 s | Ahead at 19.8 s | Speed at 19.8 s (km/h) | Off the line at 19.8 s |
|---:|---:|---:|---|---:|---:|---:|---:|
| 0 | 199.18 | 0 | 1.0 / 1.0 / 1.6 | 0 | 0 | 205.3 | 0 |
| 10 | 199.12 | 0.06 | 1.0 / 1.0 / 1.65 | −0.03 m (−1 ms) | −0.03 m (0 ms) | 205.5 | 0.2 m |
| 20 | 198.97 | 0.21 | 1.0 / 1.0 / 1.7 | −0.07 m (−1 ms) | −0.06 m (−1 ms) | 206.0 | 0.3 m |
| 30 | 198.77 | 0.41 | 1.0 / 1.0 / 1.75 | −0.12 m (−2 ms) | −0.09 m (−2 ms) | 206.3 | 0.5 m |
| 50 | 198.30 | 0.88 | 1.0 / 1.0 / 1.85 | −0.20 m (−4 ms) | −0.19 m (−3 ms) | 206.2 | 0.8 m |
| 100 | 196.48 | 2.70 | 1.0 / 1.1 / 2.0 | −0.59 m (−10 ms) | −0.80 m (−14 ms) | 201.2 | 1.7 m |
| 150 | 194.61 | 4.57 | 1.0 / 1.35 / 2.0 | −1.19 m (−21 ms) | −1.88 m (−33 ms) | 191.4 | 2.6 m |
| 200 | 193.45 | 5.73 | 1.0 / 1.6 / 2.0 | −1.80 m (−32 ms) | −3.07 m (−54 ms) | 180.0 | 3.3 m |
| 300 | 190.20 | 8.98 | 1.1 / 2.0 / 2.0 | −3.30 m (−59 ms) | −5.89 m (−103 ms) | 154.5 | 3.5 m |
| 400 | 184.83 | 14.35 | 1.6 / 2.0 / 1.94 | −5.76 m (−102 ms) | −9.97 m (−175 ms) | 116.9 | 2.7 m |
| 500 | 175.26 | 23.92 | 2.0 / 2.0 / 1.66 | −8.27 m (−147 ms) | −13.09 m (−230 ms) | 105.7 | 2.6 m |
| 600 | 162.78 | 36.40 | 1.16 / 1.0 / 1.0 | −11.73 m (−209 ms) | −17.84 m (−313 ms) | 85.1 | 0.4 m |

Here every millisecond of lead cost speed, as on the long jumps, and the cost grew faster than the lead. The full right held at force 2.0 was straightening the car without losing speed (199.4 to 199.2 km/h from 19.0 to 19.1 s while the slip closed from 41° to 30°). An earlier switch stopped the straightening: lead 200 kept 36–46° of slip at force 1.0 and lost 5.7 km/h by 19.10 s. The force columns match hop A's for leads 0–150, which is the timer running identically with and without a 110 ms flight.

**Grounded, the force is back about 600 ms after a switch, not 800 ms.** With both front wheels down it holds at 1.0 for 400 ms and then climbs `+0.05` per tick (both fronts) to 2.0 in about 200 ms. The 800 ms figure is the code's cutoff for setting the target directly; it only matters when front-wheel contact is missing during the ramp window, as in a flight.

## What this means for the play rule

The long-jump rule, **countersteer as late as possible, but early enough that the grip is back when the front wheels land**, holds on these hops with one addition: *as late as possible* has a floor where the slide changes side. Before that point the old direction at full force is holding the car's speed, and switching costs (grounded runs, long jumps). After it, the old direction at full force scrubs speed as the car rotates into the new slide, and an earlier switch both ends that and starts the force timer sooner.

- **Hop A.** The slide changed side about 510 ms before takeoff, but the line allows a lead between 200 and 290 ms at most. Within that range, earlier was always faster, by about 30 ms at 14.1 s for the best leads (150–200 ms). The latest switch (lead 0) was the slowest playable choice.
- **Hop B.** The slide changed side about 970 ms before takeoff. Faster runs came with leads up to 730 ms, 230 ms after that side change and with the grip back before takeoff; switching 170 ms after it (lead 790) already lost again. Teuflum's own lead was 30 ms slower than the best one by 21.0 s, and the latest playable leads were slower still.

A switch "just early enough" for full force at the front touchdown (lead 640 here) is not yet the best on a hop that takes off from a ramp: the grip also helps on the ground before the takeoff.

## Limits of this measurement

- Two hops on one map and one grounded stretch. On both hops the earlier switch also changed the line: from about 290 ms on hop A and 730 ms on hop B the car no longer made it through. How much lead a hop allows depends on the track around it.
- The landing angle was not matched; the flights were too short for air steering to correct it.
- The grounded reference is a different slide phase (still closing) from hop A's (opening); it separates the cost of countersteering from the timer by showing both phases, not by repeating hop A without a jump.
- Positions after touchdown are compared along the reference path; runs drift up to 3 m (hop A at 14.1 s) and up to 7 m (hop B at 21.0 s) off it.

## Reproducing

`work/short_hop_lead_trials.py` replays the variants in the Analysis automation collection, never Teuflum's, slows the game only inside the hop windows, and restores the active collection, loaded revision and game speed afterwards. It needs this map loaded, TICK running, the game window in the foreground (each restart sends keys to it), and Trainer event logging plus "Log every tire-force change" on. Telemetry and log lines stay local (not tracked). `outputs/TICK_short_hops_baseline.txt` is the input that was replayed.

```
py -3 work/short_hop_lead_trials.py --pid <PID> run a 0 10 20 30 50 100 150 200 300 400 0
py -3 work/short_hop_lead_trials.py --pid <PID> run b 610 450 500 550 650 700 750 800 610
py -3 work/short_hop_lead_trials.py --pid <PID> run f 0 10 20 30 50 100 150 200 300 400 500 600 0
py -3 work/analyze_short_hop_lead.py a
```

The analysis prints one row per lead (`a`, `b`, or `f` for flat ground) and writes `summary_<hop>.json` next to the runs.
