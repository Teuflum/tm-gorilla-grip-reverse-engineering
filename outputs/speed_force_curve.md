# How speed limits the recovered tire force

Read on 28 September 2026 from the saved decompile of `FUN_14084f720` (`14084f98a.c`), its disassembly, and a read-only memory read of the Stadium car's model with the car spawned on `ANGULAR _ MOMENTUM.Map.Gbx`, on the same executable build as the [mechanism report](gorilla_grip_mechanism.md). The question: the report measured a recovered target of `1 + s^1.5` (`s` the steering amount without its sign) (2.0 at full steering) in high-speed samples and noted a speed-related model curve. What is that curve, and what does it take as input?

## The formula

When the backwards-motion state `vehicle+0x1600` is clear, the target of the tire-force multiplier at `vehicle+0x14dc` is:

```
target = 1 + curve(x) × s^1.5
```

- **`s`** is the smoothed steering amount without its sign, from 0 to 1; left and right count the same.

- **`curve`** is the model curve at `model+0xFA0`. On the Stadium car it has two points, `(10, 0)` and `(30, 1)`, is linear between them and clamped outside. The live car's model pointer (`vehicle+0x88`) leads to this curve.
- **`x`** is the car's velocity component along the lateral axis of the steered front wheel, as an absolute value, in m/s. The car-local velocity is the vector the caller `FUN_140851f00` also copies to `vehicle+0x1424..0x142c`. The code takes the dot product with the wheel's lateral axis, applies an absolute-value mask, and passes the result to the curve with no `× 3.6`. Other curve calls in the same function do multiply by 3.6, so this one is in m/s.
- **The steered wheel angle** is `model+0xDA8` (45° on the Stadium car) × smoothed steering × a surface factor. The surface factor is the icing curve described in the report (`model+0xCF0` on ice-family materials, `model+0xD40` otherwise). On settled ice it is `1`, so full steering turns the wheel lateral axis 45°. Just after landing, when average icing has not fully returned, it is slightly less (about 43°).

With `v` the car's horizontal speed and `α` the angle between the steered front wheels and the direction of travel, `x = v × sin α`, with `α` between 0° and 180°. So the curve starts at 36 km/h of `x` and saturates at 108 km/h of `x`:

```
target at full steering = 1 + clamp((x − 36 km/h) / 72 km/h, 0, 1)
```

**Check.** Across the 215 steady samples in the 13 saved vehicle snapshots (mode age above 820 ms, a front wheel touching), this formula reproduces `vehicle+0x14dc` within `0.0001`, including the partial-steering values `1.089`, `1.253`, `1.465` and `1.716`. Plain speed, the forward component, and the car's own sideways component all fail. Those samples all have `x` above 30 m/s, so they confirm the input and the saturated value; the 10–30 m/s ramp comes from the model read. The Trainer's Openplanet log of 27 September agrees in shape: at full steering, grounded and long after the switch, the multiplier averages about 1.1–1.2 at 40–60 km/h, 1.35 at 80 km/h and reaches 2.0 from about 140–160 km/h. The log has no yaw rate or slide side, so it cannot give `α` exactly.

## What the car gets at full steering

`α` is the angle between where the steered front wheels point and where the car is going. Driving straight with full lock, or sliding at 90° with full lock, gives `α = 45°`.

| α | 50 km/h | 75 km/h | 100 km/h | 125 km/h | 150 km/h | 200 km/h |
|---:|---:|---:|---:|---:|---:|---:|
| 0° | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| 15° | 1.00 | 1.00 | 1.00 | 1.00 | 1.04 | 1.22 |
| 30° | 1.00 | 1.02 | 1.19 | 1.37 | 1.54 | 1.89 |
| 45° | 1.00 | 1.24 | 1.48 | 1.73 | 1.97 | 2.00 |
| 60° | 1.10 | 1.40 | 1.70 | 2.00 | 2.00 | 2.00 |
| 90° | 1.19 | 1.54 | 1.89 | 2.00 | 2.00 | 2.00 |

The boost starts where `v × sin α` passes 36 km/h and is full at 108 km/h:

| α | Boost starts | Full boost |
|---:|---:|---:|
| 90° | 36 km/h | 108 km/h |
| 45° | 51 km/h | 153 km/h |
| 30° | 72 km/h | 216 km/h |
| 15° | 139 km/h | 417 km/h |

## What this means

- **Slow landings get little or nothing.** The same well-timed switch that gives 2.0 at high speed gives 1.0 below about 51 km/h in a straight run or a 90° slide, and only about 1.25 at 75 km/h. The recovery timer and the stored direction work the same at any speed; only the size of the reward shrinks.
- **The wheel angle to the travel direction matters as much as speed.** When the steered wheels point where the car is going, `x` is near zero and there is no boost, however fast the car is. When they point across the travel direction, the boost is full from 108 km/h.
- **The report's 2.0 was a saturated value.** Every earlier sample had `x` above 30 m/s, which is why `1 + s^1.5` fitted them exactly. The graphs' `targetMultiplier` uses the same saturated form.

Not measured here: what a smaller target costs in speed after a slow landing. The [plastic flick below](#plastic-sections) measures the 10–30 m/s part of the curve with the car's exact velocity.

## Plastic sections

Measured on 30 September 2026 on a map Teuflum had loaded (UID `9VT6qODgbTLrvPCtBCL0QregkMc`), Stadium car, same `Trackmania.exe` (SHA-256 `3FC7D8CD…6EDDA`). TICK replayed Teuflum's input: full left steering from 5.21 s to 8.91 s with gas held, and no brake between 6.94 s and 9.26 s. The [Gorilla Grip Logger](GorillaGripLogger/Main.as) recorded every display frame and the Gorilla Grip Trainer 0.3.0 logged every change of `vehicle+0x14dc` on the same replay. The run is deterministic: four earlier replays logged the same force values at the same race times.

**What happens.** The slide crosses a plastic flick. The stored direction stays left and the backwards-motion state stays clear, yet the multiplier drops from 2.0 to 1.0 on a single frame at 8.28 s, stays there for about 150 ms and climbs back to 2.0 by 8.58 s. The climb (about +0.07 per tick, a little less each tick) is not the recovery ramp (+0.025 per touching front wheel per tick), and the mode is 3.2 s old, far past the 800 ms at which the ramp ends.

**Why.** The target's `x` depends on the steered wheel angle, and that angle's surface factor is chosen by material: the ice-family curve while any wheel is on Ice, Snow or RoadIce, the other-material curve while all four are elsewhere. With `slip` the angle of the travel direction from the car's nose and `θ` the steered wheel angle, both measured to the same side, `x = v × |sin(slip − θ)|`.

| Race ms | Wheels (FL/FR/RL/RR) | Average icing | Slip | Wheel angle `θ` | Predicted target | Logged |
|---|---|---:|---:|---:|---:|---:|
| 7502 | RoadIce ×4 | 100% | 104° | 45° | 2.00 | 2.000 |
| 7734 | first wheels on Plastic | 100% | 101° | 45° | 2.00 | 2.000 |
| 8096 | Plastic ×4 | 89% | 81° | 24.7° | 2.00 | 2.000 |
| 8277 | Plastic ×4 | 84% | 55° | 18.1° | 2.00 | 2.000 |
| **8282** | **FL on RoadIce** | 84% | 54.5° | **43.6°** | **1.03** | **1.013** |
| 8300–8410 | RoadIce reaches all four | 83–89% | 52° → 36° | 44° | 1.00 | 1.000 |
| 8445 | RoadIce ×4 | 91% | 31° | 44.2° | 1.13 | 1.129 |
| 8514 | RoadIce ×4 | 95% | 22° | 44.6° | 1.60 | 1.605 |
| 8585 | RoadIce ×4 | 99% | 12° | 44.9° | 2.00 | 2.000 |

1. **On the plastic** (7.73–8.28 s) the plastic's grip swings the car round quickly: slip falls from 101° to 55°, where it had changed by only about 3° in the 0.2 s before on RoadIce. At the same time the tires lose icing, and the other-material curve (80% icing → 0.3) shrinks the wheel angle from 45° to 18°. The wheels stay more than 32° across the travel direction, so the target stays at 2.0. With the ice curve the wheels would have stayed near 44°, and the target would have started falling at about 8.15 s.
2. **Back on RoadIce.** The front-left wheel's first RoadIce frame switches the surface factor to the ice curve, and the wheel angle jumps from 18° to 43.6° in one tick. At 54° of slip the wheels now point about 10° from the direction of travel, `x` falls to about 10 m/s, and the multiplier, being above the new target, is clamped straight down to it.
3. **The dip.** Slip keeps falling and passes through the wheel angle: the wheels point exactly where the car is going. Until slip falls below about 33°, `x` stays under 10 m/s and the target stays at 1.0.
4. **The climb.** As slip falls from 31° to 12°, `x` rises from about 12 to 31 m/s along the curve's ramp, and the target climbs from 1.13 to 2.0. That is the 10–30 m/s section of `model+0xFA0` measured with the car's own velocity.

**Check.** Over the 502 frames from 5.83 to 8.75 s, the target with the material-selected surface factor matches the logged force within `0.033`. Using the ice curve on every frame misses by up to `0.931`. The remaining error comes from the Logger's display frames (about 6 ms apart) falling between the 10 ms physics ticks, and from the visible icing standing in for the per-wheel coefficient. [Graph 8](https://teuflum.github.io/tm-ice-physics-reverse-engineering/#plastic) plots both angles and all three force lines over the replay; `work/analyze_plastic_flick.py` recomputes the table from the Logger CSV and the Openplanet log.

**What it means for play.** Crossing plastic mid-slide can hide the loss until the tires are back on ice: the plastic curve keeps the target high while the car rotates, and the first ice contact reveals where the wheels point. If the car leaves the plastic with its slip near the full-lock wheel angle (about 45°), the multiplier falls to 1.0 until the car turns further. This is geometry, not the timer: no direction change and no wait are involved. We tested only this full-lock replay. We did not measure how partial steering or a different exit angle changes the dip, or whether it costs time.
