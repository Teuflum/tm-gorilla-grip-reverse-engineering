# Early countersteer on short hops

Measured on 28 September 2026 on a map Teuflum had loaded (UID `pBoO2N5xKZRTuOGcVBRuoOCbhM3`), Stadium car, on the same `Trackmania.exe` as the [mechanism report](gorilla_grip_mechanism.md) (SHA-256 `3FC7D8CD…6EDDA`). TICK replayed Teuflum's TAS input with one steering change per run, and the Gorilla Grip Trainer 0.3.0 logged its exact physics reads. The aim was the case the [long-jump measurement](countersteer_lead_cost.md) could not test: a hop shorter than the force timer, where an earlier switch also brings the grip back sooner.

**The sweep does not answer whether an earlier switch pays on a short hop.** An earlier switch also lands the car less sideways: the landing slip fell from 63° to 55° on the 13.3 s hop and from 114° to 94° on the 20.3 s hop. A car that lands less angled can ice-slide longer and gains speed from that alone, so any speed difference after touchdown mixes the switch timing with the landing angle. The flights (110–160 ms) are too short to correct the angle with air steering, and the earlier-switch runs leave the track shortly after landing. After-touchdown results are therefore not reported. Three findings do not depend on the landing.

## Method

Each variant holds full right and steps to full left (`steer -127`) on one tick; the stored direction flips 50 ms later (smoothed steering moves 0.2 per tick). "Lead" is the takeoff tick minus the flip tick, read from the Trainer's snapshots (`modeAt`, contact bits); where the Trainer graded the jump, its own lead matches. Every other input is Teuflum's. The game ran at 0.2× only inside each hop's window, so the Trainer logged a snapshot on nearly every 10 ms tick; game speed does not change the physics ticks. Force is the Trainer's tire-force multiplier (`vehicle+0x14dc`), speed and slip come from TICK telemetry. Repeated reference runs matched to 0.01 km/h.

## 1. Why the 20.3 s hop was not rated

Teuflum's switch there flips the stored direction at 19.71 s. The car stays on the ground up a ramp and takes off at 20.32 s, a lead of 610 ms. The Trainer publishes a timing preview only for leads up to `S_DMaxLeadMs` (250 ms, the D limit), so this takeoff got no preview and no cue. The landing then kept the same direction with the force at 1.99, which resolves silently (`landing resolved without verdict … force 2.000`). The jump passed every eligibility filter; only the lead was outside the graded range. The Trainer's grading is unchanged.

## 2. Grip after a switch: about 600 ms on the ground, paused in the air

The same step was placed on flat ice (height constant to 0.05 m) at 18.5–19.1 s, with no jump nearby. With both front wheels down, the force holds at 1.0 for 400 ms after the flip, then climbs `+0.05` per tick to 2.0 in about 200 ms. **On the ground the grip is back about 600 ms after a switch.** The 800 ms figure in the code is the cutoff for setting the target directly; it only matters when front-wheel contact is missing during the ramp.

| Time since the flip | 110 ms | 310 ms | 510 ms | 610 ms |
|---|---:|---:|---:|---:|
| Flat ice, lead 0 | 1.0 | 1.0 | 1.6 | 2.0 |
| 13.3 s hop, lead 0 (flight 0–110 ms after the flip) | 1.0 | 1.0 | 1.6 | 2.0 |

A flight that ends inside the 400 ms hold changes nothing: on the 13.3 s hop the force followed the grounded values tick for tick for leads 0–100 ms, and within 0.03 at 150 ms. Every lead that stayed on the track (0–200 ms, 110–310 ms from flip to front touchdown) landed at 1.0.

A flight during the ramp pauses it, because only touching front wheels update the force. On the 20.3 s hop the force at front touchdown equalled the force at takeoff:

| Lead (ms) | Flip to front touchdown (ms) | Force at takeoff | Force at front touchdown |
|---:|---:|---:|---:|
| 480 | 640 | 1.33 | 1.34 |
| 520 | 680 | 1.53 | 1.55 |
| 560 | 720 | 1.73 | 1.75 |
| 600 | 770 | 1.95 | 1.99 |
| 640 | 800 | 2.0 | 2.0 |

(Lead 600 is Teuflum's switch replayed as a single step: the flip is on the same tick, and the car leaves 10 ms sooner than with the original input.)

## 3. Speed before takeoff depends on which way the slide is moving

Before takeoff the landing plays no part, so takeoff speed compares the switch timing cleanly. It went opposite ways on the two slides measured.

**Slide opening (13.3 s hop).** The slide changed side near 12.79 s (telemetry slip −7° at 12.70 s, +10° at 12.88 s) and then opened towards the new side: +28° at 13.06 s, +53° at 13.30 s. Holding full right at force 2.0 through that phase cost the lead-0 run 5.3 km/h between 13.06 s and takeoff; the lead-200 run, at force 1.0 and countersteering from 13.10 s, lost 1.6 km/h. The reference is lead 0, a flip on the takeoff tick itself (Trainer grade S+).

| Lead (ms) | Trainer grade | Takeoff speed (km/h) | Faster than lead 0 (km/h) |
|---:|:---:|---:|---:|
| 0 | S+ | 193.89 | 0 |
| 10 | S | 194.10 | 0.21 |
| 20 | A | 194.30 | 0.41 |
| 30 | A | 194.53 | 0.64 |
| 50 | B | 195.03 | 1.14 |
| 100 | C | 196.26 | 2.37 |
| 150 | D | 197.10 | 3.21 |
| 200 | D | 197.68 | 3.79 |

**Slide closing (flat ice).** At 19.10 s the car was at 199 km/h and 30° of slip, and the full right at force 2.0 was straightening it: slip −41° at 19.0 s, −13° at 19.3 s, with speed flat (199.4 to 199.2 km/h from 19.0 to 19.1 s). An earlier switch stopped the straightening. Lead 200 kept 36–46° of slip at force 1.0.

| Lead before 19.10 s (ms) | Speed at 19.10 s (km/h) | Lost against lead 0 (km/h) |
|---:|---:|---:|
| 0 | 199.18 | 0 |
| 10 | 199.12 | 0.06 |
| 30 | 198.77 | 0.41 |
| 50 | 198.30 | 0.88 |
| 100 | 196.48 | 2.70 |
| 200 | 193.45 | 5.73 |
| 300 | 190.20 | 8.98 |
| 400 | 184.83 | 14.35 |
| 600 | 162.78 | 36.40 |

The 20.3 s hop shows the same opening-slide effect on the ground before its takeoff. That slide changed side near 19.35 s. Teuflum's lead 600 was 7.6 km/h faster than lead 480 at 19.86 s, when lead 480 had just switched after 160 ms more of full right at force 2.0, with the slip opening from +42° to +60°.

So a switch before the slide changes side costs speed on the ground, as on the long jumps. After the side change, the old direction at full force costs speed instead.

## What this sweep could not show

- **Whether an earlier switch pays overall on a short hop.** Settling that needs matched landing angles and a track that lets the earlier line continue. Here the 13.3 s hop's line ends in a hole from a 290 ms lead, and the 20.3 s hop sends the car off the ramp when switching at takeoff, and the car hits something shortly after landing from a 730 ms lead.
- Two hops and one grounded stretch on one map.

## Reproducing

`work/short_hop_lead_trials.py` replays the variants in the Analysis automation collection, never Teuflum's, slows the game only inside the hop windows, and restores the active collection, loaded revision and game speed afterwards. It needs this map loaded, TICK running, the game window in the foreground (each restart sends keys to it), and Trainer event logging plus "Log every tire-force change" on. Telemetry and log lines stay local (not tracked). `outputs/TICK_short_hops_baseline.txt` is the input that was replayed.

```
py -3 work/short_hop_lead_trials.py --pid <PID> run a 0 10 20 30 50 100 150 200 0
py -3 work/short_hop_lead_trials.py --pid <PID> run b 610 450 500 550 650 610
py -3 work/short_hop_lead_trials.py --pid <PID> run f 0 10 30 50 100 200 300 400 600 0
py -3 work/short_hop_lead_trials.py summary a
```

`work/analyze_short_hop_lead.py a|b|f` also prints positions after touchdown along the reference path; those are the landing-confounded numbers left out here.
