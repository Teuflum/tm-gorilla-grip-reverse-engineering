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

With `v` the car's horizontal speed and `α` the angle between the steered front wheels and the direction of travel, `x = v × |sin α|`. So the curve starts at 36 km/h of `x` and saturates at 108 km/h of `x`:

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

Not measured here: a speed-only run on the ramp itself (`x` between 10 and 30 m/s) with the car's exact velocity, and what a smaller target costs in speed after a slow landing.
