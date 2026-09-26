# Trackmania ice “gorilla grip”: measured mechanism

Investigated 24 September 2026 on the user's `ANGULAR _ MOMENTUM.Map.Gbx` and `AngularMomentumTAS.Replay.Gbx`. The local `Trackmania.exe` analyzed here has SHA-256 `3FC7D8CDA542BEDA131C44306B123F4004D07D7E22F512B46B762AFC29F6EDDA`. This conclusion is specific to that physics build and the tested transitions.

For a visual explanation, open [the interactive graphs](../graphs/interactive.html) from a local copy of this repository. The [static icing graph](../graphs/static/icing-force-mix.svg) can be viewed directly on GitHub.

## The simple version

Imagine the game keeps two things for your car: a note saying **“sliding left” or “sliding right,”** and a short recovery timer. Once the tires are icy enough for this physics branch to run, steering far enough in a new direction while **any wheel is still touching the ground** changes the note and restarts the timer. During the first part of that timer, the tire-force boost is low. That is the short period where the ice slide feels slow to gain speed.

The game also remembers **how icy each tire is**. Ice contact adds icing; other ground and airtime can let it fade. Wetness can hold the icing at a minimum level, even on plastic. The game averages the four tires' icing to decide how much of this icy tire-force calculation to use. The current surface still changes that calculation, so icing and surface both matter.

The game looks at steering that has been smoothed over several physics updates. A tiny tap may not change the note immediately. In the tested build, the smoothed steering must pass **10% left or right**. It does not matter which wheel is touching; the **last wheel to lift is your deadline** before a jump.

| Situation | What happens |
|---|---|
| Start or reverse a slide while staying on the ice | If this changes the stored direction, the recovery timer runs **while you are driving**. You can feel the slow start, then the stronger slide. |
| Set the new direction just before a jump | The direction changes before takeoff. The timer keeps running **during the flight**, so the stronger force can be ready when you land. |
| Wait until landing to set the new direction | The timer starts **on landing**. You feel the brief weak period after touchdown. |

Steering either way in mid-air can change where the car points, but it cannot rewrite this note while no wheel touches. You still need the intended steering for the landing. **Yes: this mechanism also operates without an air transition.** The code contains no requirement to jump. Our controlled speed comparisons specifically tested jumps, so this report does not claim that every slow-feeling grounded slide is caused only by this timer; speed, angle, and surface contact can affect the result too.

If the note already says the direction you want, steering farther in that same direction does not restart the timer. Briefly letting the steering return toward center can preserve the note too, although the multiplier itself falls while steering is near center; see the neutral-steering experiment below.

For an instant rightward response after a jump, the note must already say **right** before takeoff, and it must still say right when the tires meet the ice. “Right” here means the **steering direction used for the landing**, not the direction the car is pointing or moving. Raw right input at the last possible moment may still leave the internal smoothed value pointing left, which can change the note again at touchdown. The note also needs to have been set early enough for its recovery timer to finish; crossing 10% immediately before a very short jump does not guarantee full force on landing.

### How quickly does the game steering catch up with your input?

The deciding value is an **internal smoothed steering number**, not the raw button/TICK input or the visible front-wheel angle. The game limits how much this number can change on each physics update. Programmers call that limit the *slew rate*: here it just means **the internal steering takes several updates to catch up with your input**. In these ice-contact runs, it moved by about `0.2` per **10 ms physics update** when we switched from full left (`-1`) toward full right (`+1`):

`-1 → -0.8 → -0.6 → -0.4 → -0.2 → 0 → +0.2 → … → +1`

The **sixth affected update** reaches `+0.2`, which is the first value above the required `+0.1`; if a wheel still touches then, the car stores right mode. That is roughly **50–60 ms after the raw input change**, depending on whether the input arrives just before or just after a physics update. It takes **ten affected updates**, roughly **90–100 ms**, for this internal number to reach full right. Full right to full left is symmetric.

**Can an Openplanet steering display show this number?** Yes. The prototype Rater used during this research showed it on the tested build; the separate [Gorilla Grip Trainer](https://github.com/Teuflum/Gorilla-Grip-Trainer) project will carry that feature forward. The normal `VehicleState::ViewingPlayerState()` exposes `InputSteer` and per-wheel `FLSteerAngle`/`FRSteerAngle`, but neither is the physics field `vehicle+0x1430` used by the ±0.1 comparison. `InputSteer` is the input; the wheel-angle fields describe the actual front-wheel angles in the visual state. In the controlled `+13/127` reversal, a physics snapshot showed smoothed steering `+0.102362` near tick 11300, while the logger's display-frame CSV for the same input variant still showed front-left/front-right angles around `+0.642`/`+0.665` near 11.30 s. These are separate runs and clocks, but the code paths and different values show why `FLSteerAngle > 0.1` is **not** the gorilla-grip condition. The prototype reached the current physics car through the active `CSmPlayer` at offset `0x1118`, validated the pointer against the current visual car, and read the internal field directly. It labeled any fallback as **ESTIMATE**.

For the small-input test, raw `+12/127 ≈ 0.0945` can never carry the smoothed value past `+0.1`, however long it is held. Raw `+13/127 ≈ 0.1024` can cross it once the smoothed value has caught up.

This explains the apparent few-tick wait before the game *recognizes* the new slide direction. A **second, longer delay** starts only when that stored direction changes: the tire-force multiplier stays low for about **400 ms** before recovering. On the measured delayed landing near 12.58 s, it reached its recovered value by about 13.17 s, roughly **0.6 s after touchdown**, with the car on the ground the whole time. A jump can hide this second delay by letting the timer run in the air, but the multiplier itself does not ramp in the air: the full value is guaranteed on landing only once the mode age has passed the code's **800 ms** cutoff. Inside the 400–800 ms window it climbs after contact by `0.0125` per touching wheel per 10 ms physics tick (200 ms from `1.0` to `2.0` with all four wheels down), and only while the force gate at `vehicle+0x1600` is clear. The `0.2` steering change per update was measured for these ice conditions and can differ with the physics conditions; the six- and ten-update estimates are not universal constants.

## The deciding rule

The physics code keeps a **car-level directional slide mode**. For these tests, mode `1` is left and mode `2` is right. On a physics update where at least **one of the four wheels has a ground-contact flag**, it reads **smoothed steering**, not the raw TICK input:

| Smoothed steering in the contact-eligible update | New mode |
|---|---:|
| Less than `-0.1` | `1` (left) |
| Between `-0.1` and `+0.1`, including the endpoints | Keep the previous mode initially; clear to neutral when the 300 ms timeout is checked during wheel contact |
| Greater than `+0.1` | `2` (right) |

The code also checks two special vehicle-status flags. They were clear in all of these runs. The contact check loops over all four wheels and returns as soon as **any** contact flag is nonzero. There is no fixed front, rear, left, or right wheel that owns this mode. The **last wheel still touching the surface supplies the final opportunity** to commit the intended direction before airtime.

On the supplied 11.26–12.58 s transition, that last wheel is **rear-right** (internal wheel index 2). On the independent 9.41–10.38 s transition, it is **front-left** (internal index 0). The same threshold rule predicts both. An after-update snapshot can already show all four flags clear even though the mode changed in that update; use the code's contact check and the immediately preceding contact snapshot to interpret that boundary, rather than the displayed race timestamp alone.

While all wheels are airborne, smoothed steering still follows air inputs, but this contact-gated mode does not update. Thus steering either way during the spin can leave the previously committed mode intact. To get the intended rightward response on landing, the car must arrive with right mode already stored and smoothed steering that will not switch it back to left when contact resumes. If it arrives carrying left mode, the first eligible landing update with sufficiently rightward smoothed steering changes it to right and starts the recovery delay.

### What happens between −10% and +10%?

**There is no automatic new direction at zero steering.** When the smoothed steering enters this band on a contact-eligible update, the car keeps its previous left or right mode and records the start of a neutral interval. If it already had neutral mode, it stays neutral. The code clears a retained direction when a later contact-eligible update finds that about **300 ms** has elapsed since that start. Returning past the 10% threshold in the *same* direction before that cutoff cancels the neutral interval without changing mode or restarting the 400 ms force-recovery timer. Crossing the threshold in the *opposite* direction changes mode immediately and restarts that timer.

The neutral check does not execute with all wheels airborne or when this tire-icing branch is inactive. The old mode therefore survives flight; the clock used for the neutral timeout still advances. If the car lands after a long flight while its smoothed steering is **still neutral**, the first eligible landing update can clear the old mode. If landing steering is already beyond the same-direction threshold, that update keeps the intended mode.

We tested this on grounded ice by changing only the steering near race time 4.70 s. In the **100 ms neutral-input trial**, left mode stayed `1`, its original mode-change timestamp stayed unchanged, and the multiplier fell `2.0 → 1.0 → 2.0` as internal steering moved `−1 → 0 → −1`. The `2.0` multiplier returned as soon as full steering returned, with no new 400 ms wait. In the **400 ms neutral-input trial**, internal steering became neutral near 4.73 s; mode cleared to `0` near 5.03 s. When steering became left again near 5.09 s, mode returned to `1`, a new mode-change timestamp was stored, and the multiplier remained `1.0` through the sampled 5.20 s endpoint.

The **10% threshold controls the stored direction, not the amount of current force**. In these high-speed ice samples, the multiplier's recovered target followed `1 + |smoothed steering|^1.5`: at internal steering magnitudes `1.0`, `0.8`, `0.6`, `0.4`, `0.2`, and `0`, the measured values were `2.0`, `1.71554`, `1.46476`, `1.25298`, `1.08944`, and `1.0`. The model also has a speed-related curve, so this compact formula describes these particular high-speed samples. Holding just over 10% steering in the same direction preserves the mode but **does not keep the multiplier at 2.0**. Holding full steering in the same direction lets this contribution stay recovered; it does not guarantee endless slide acceleration or speed, which also depend on the rest of the vehicle dynamics.

### Ice surface, icy tires, plastic, and tarmac

The direction-update code checks whether **any wheel contacts a surface**, not whether that wheel contacts ice. We traced its icing input back through the game code. In the ordinary status used by our tests, each wheel's coefficient is `1 − 0.2 × that wheel's icing` (`1.0` for a clean tire, `0.8` for a fully icy tire). The game averages the four coefficients into `vehicle+0x1c44`, then computes `(1 − that average) / (1 − 0.8)`. Algebraically, the result is **the average icing of the four wheels**. Across all `607` snapshots in the clean-tarmac and target-takeoff captures, the stored car coefficient matched the average of the four stored wheel coefficients within `0.000001`. This is why the car can use an icy force response even when the current ground is plastic: it still carries icing state from its wheels.

**What does the curve mean?** Think of this part of the code as having an ordinary tire-force calculation and an ice-specific tire-force calculation. It scales down one ordinary contribution by `1 − curve output` and passes the curve output into the icy contribution. The curve changes **how much of these tire-force contributions is used at the current icing level**. It does **not** say how quickly tires gain or lose ice, how much speed the car gains, or the total grip of the surface.

The wheel-material entries select which curve to use: if **any** entry is material `3` (**Ice**), `21` (**Snow**), or `74` (**RoadIce**), the code uses the ice-family curve. Otherwise it uses the other-material curve, which includes `77` (**Plastic**) and `16` (**Asphalt**). These are values in this game build; a mixed-material transition can select the ice-family curve. For the *same icing input*, the outputs are:

| Average icing across four wheels in the tested status | Ice / Snow / RoadIce: ice-force share | Plastic / Asphalt / other: ice-force share |
|---:|---:|---:|
| `0%` | `0%` | `0%` |
| `5%` | `60%` | `1.875%` |
| `20%` | `85%` | `7.5%` |
| `80%` | `96.25%` | `30%` |
| `100%` | `100%` | `100%` |

For example, **80% icing does not mean 96% total grip on ice**. It means the ice-specific contribution in this calculation has a weight of about `0.9625` on an ice-family surface. On plastic at the same icing input its weight is `0.3`. The ordinary contribution gets the complementary weight in this part of the calculation; other surface-specific forces still exist.

The icy contribution is enabled when its curve output is at least about `0.00001`. Both curves become nonzero immediately above zero icing. In the tested status, this guard is reached at roughly `0.000083%` **average wheel icing** with the ice-family curve, or `0.0027%` with the other-material curve. Those tiny values are numerical switches for this force branch, **not practical slide thresholds**. This code does **not** contain a meaningful fixed icy-tire percentage at which an ice slide abruptly becomes possible. Tire force changes progressively as icing rises. A visibly sustainable slide also depends on speed, steering, slip angle, and the other forces; we have not measured a universal minimum percentage for that outcome.

**What happens to icing on plastic?** At driving speed above the model's `5` speed threshold, the per-wheel update switches to an icing-growth state while the wheel contacts Ice or RoadIce. On other surfaces such as Plastic, it switches to a decay state. The model's icing-growth time is `1,650 ms`; decay from full to zero would take about `3,300 ms` while the wheel remains grounded, or `6,000 ms` in the air, if no lower limit intervenes. Those are state-update rates, **not** the force-recovery timer that causes the delayed slide response. Snow can also select the icing-growth state when a separate model flag is enabled.

The important exception is **wetness**. The car's wetness value at `vehicle+0x13a4` is passed to each wheel update. When a wheel leaves the icing-growth state, the code uses the smaller of its current icing and wetness as a **minimum icing level** during decay. If both are `100%`, icing remains at `100%` even while the wheel touches plastic; if wetness later drops, that minimum can drop too. Thus the code supports your wet-plastic explanation **as long as wetness stays high**. Plastic itself still selects a different force curve and does not inherently freeze the icing timer. We have not measured a clean plastic-takeoff run yet, so this is a code-path prediction rather than a measured outcome on a specific map.

At full icing, the ice-family and other-material curves both output `1.0`, so the icy-force path and stored-direction logic can run on plastic before a jump. Ice is more than a source of icing: its material ID also selects the ice-family force curve, and other surface-specific forces still matter. That is why “only the icy-tire percentage matters” is too broad, even though **tire icing is the state that carries the effect onto plastic**.

We also measured the clean-tire tarmac start of ANGULAR ↻ MOMENTUM. During the full-right, wheel-contact interval around 2.37–2.88 s, the car-level ice coefficient field was `1.0` (no accumulated ice), the stored directional mode stayed `0`, and this multiplier stayed at its **baseline `1.0`**. At first ice contact near 2.93 s, the field began falling below `1.0` and right mode appeared. The `2.0` observed later on iced full steering is therefore **not a universal tarmac default**. These values are for this internal multiplier, not a ratio of the total grip of asphalt, plastic, and ice.

## Why the grip feels delayed

When the mode switches into a left or right direction, the code writes a timestamp and resets the tire-force multiplier at vehicle offset `0x14dc` to `1.0`. That multiplier directly appears in the tire-force calculation inside the four-wheel loop. In these full-steering ice runs its recovered target is `2.0`; with smaller steering, the target itself is lower, as the neutral trial above demonstrates. The vehicle model's delay parameter at `model+0x1194` is `400`. Each time the tire-force code runs, it compares the mode age with that delay:

| Mode age when the tire-force code runs | What the code does to `vehicle+0x14dc` |
|---|---|
| Below 400 ms | Leaves it unchanged (`1.0` after a mode change). |
| 400–800 ms | Adds **one step** toward the target: the step length passed in milliseconds divided by 400, capped at the target. Measured: `+0.0125` per touching wheel per 10 ms tick. |
| Above 800 ms | Sets it to the target directly. |
| Any age, multiplier already at or above the target | Sets it to the target, so a falling target pulls the multiplier down at once. |

Two inputs to that rule change the result. First, the target is not always the recovered value: when the gate at `vehicle+0x1600` (`plVar2[0x2c0]` in the decompile) is nonzero, the code skips the steering/speed target and uses the base value, which pins the multiplier at `1.0`. Second, the target itself moves with steering and speed, and a multiplier above it is clamped straight down to it.

The ramp is therefore **per update, not a function of elapsed time alone**. The multiplier only moves when this code runs, which requires tire-force calculation on a contacting wheel. It does not catch up for time that passed without such updates.

In the measured delayed landing, the mode changed at touchdown near 12.58 s and the car stayed on the ground. The multiplier remained at `1.0` through roughly race time 12.95 s, rose from about 1.05 to 2.0 between 12.97 and 13.17 s, and was 2.0 thereafter. That is full recovery at roughly **600 ms mode age**, about 200 ms into the 400–800 ms window, because grounded updates kept adding steps. The fast variant had already recovered to `2.0` before landing.

| Time relative to a mode change | Tire-force multiplier in these runs | Meaning for the slide |
|---|---:|---|
| At the change | Reset to `1.0` | The timer starts; the stronger tire-force contribution is unavailable. |
| First ~400 ms | Remains at `1.0` | The car still has tire forces and can gain or lose speed, but this contribution is lower. |
| 400–800 ms | Rises `0.0125` per touching wheel per tick while the gate is clear | Four wheels: `1.0` → `2.0` in 200 ms (the measured landing reached `2.0` near ~600 ms). Airborne: no updates, so no rise. |
| After 800 ms | Target on the next update | Guaranteed full value as soon as the tire-force code runs again. |

**The ~600 ms figure is a measured grounded result, not the game's limit.** The code's hard cutoff is 800 ms (twice the delay). The ramp speed depends on how many wheels touch: the traced landing below rose `+0.025` per 10 ms tick on two wheels and `+0.05` on four, i.e. `0.0125` per touching wheel per tick. A full four-wheel ramp therefore takes 200 ms, which matches the ~200 ms measured here. Why the per-wheel step is `0.0125` (half of `10 ms / 400`) has not been resolved in the code.

**Consequence for jumps.** If the stored mode changes before takeoff and the car lands while mode age is between 400 and 800 ms, the multiplier generally has not ramped in the air. It is still near `1.0` at contact (or whatever value it reached during pre-takeoff contact) and must ramp after touchdown, reaching the target within the grounded ramp time or at 800 ms mode age, whichever comes first. A landing **after** 800 ms mode age gets the full target on its first contact update, matching the observed instant `1.00x → 2.00x` change below. A landing at 600 ms mode age can therefore start with **less than `2.0`**, as the traced landing below shows.

### Traced landing inside the 400–800 ms window

Measured on 26 September 2026 on *XPIce26 – Trialthon ft thounej* with a TICK input run, on the same executable build as above (the Trainer's build-signature check passed). The Trainer read `vehicle+0x14dc`, `+0x14d8`, `+0x1600`, and the contact flags once per display frame, with the game slowed to 0.1× around the jump so every 10 ms physics tick was sampled. Mode age is game clock minus `vehicle+0x14d8`. The stored mode changed to right at race time 27.90 s; the input released gas at 27.97 s and pressed it again at 28.52 s.

| Mode age (ms) | Contacts (FL FR RL RR) | Gate `+0x1600` | Multiplier |
|---:|---|---:|---:|
| 0–400 | airborne from 50 ms | 0 | `1.000` |
| 410 | `1000` (first touch) | 1 | `1.013` |
| 420–610 | one to four wheels | 1 | `1.000` |
| 620 | `1110` | 0 | `1.025` |
| 630–760 | `0110` | 0 | `1.075` → `1.400`, `+0.025` per tick |
| 770–800 | `1110`, then `1111` | 0 | `1.438`, `1.488`, `1.538`, `1.588` |
| 810 | `1111` | 0 | `2.000` |

Three things follow. The landing started well below `2.0` and ramped on the ground, confirming the in-window case described above. The gate held the multiplier at `1.0` for the first ~210 ms of contact and cleared on the tick the gas input returned (mode age 620), so the ramp only began then. And the final `1.588` → `2.000` jump is the 800 ms cutoff taking over from the ramp. The gate's coincidence with the gas input is a measured correlation; the code that writes `vehicle+0x1600` has not been identified.

The same trace also shows the clamp to a falling target. Gas was released again at 28.95 s with the gate clear, four wheels down, and full right steering. From 29.00 s the multiplier fell from `2.000` to `1.000` in about 190 ms, by `0.025` and then gradually larger steps up to `0.062` per tick. That is the target dropping (it depends on a speed-related curve), with the multiplier clamped to it, not a timed reversal of the ramp.

These numbers describe a **multiplier on a tire-force calculation**, not a multiplier on the car's speed or a promise of forward acceleration. In the target pair, both variants touched down near 241.5 km/h; at x≈782 the delayed run was 227.323 km/h and the pre-set run was 230.944–230.958 km/h. The recovered multiplier therefore corresponded to **less speed lost after landing** on this trajectory. On another trajectory, the same force difference can feel like stronger slide acceleration.

For a grounded slide begun by switching raw input from full left to full right in these ice conditions, the mode switch is estimated ~50–60 ms after input. Adding the timer gives an estimated **~450–460 ms from input until this force contribution starts recovering**, and **~650–660 ms until full recovery** if it follows the measured grounded landing ramp (at most ~850–860 ms, the 800 ms code cutoff plus the switch delay). Those input-to-force figures are a projection from the code and the jump measurements; we have not measured a separate ground-only reversal to confirm its exact speed response.

Changing mode before takeoff resets the multiplier early enough for the long airborne interval to consume the delay. Air steering cannot reset that mode while no wheel touches. Changing mode at touchdown resets the multiplier there instead, producing the observed brief loss of slide acceleration.

This `1.0` to `2.0` value is the multiplier observed in these runs. It should not be read as a universal coefficient of ice friction on every map or build.

## Controlled evidence

All pairs start from the same full TICK replay; only the named pre-jump steering action changes. TICK steering integers are divided by 127 in the physical input field. The Openplanet logger saved the run traces automatically. Live vehicle snapshots were read with `ReadProcessMemory`; no game code or memory was modified.

| Jump and last wheel | Pre-jump intervention | Smoothed steering at first all-air snapshot | Stored mode at that snapshot | Landing result |
|---|---|---:|---:|---|
| 11.31 s, RR | `+12` at ticks 1126–1131 | `+0.094488` | Left `1` | Delayed; 227.323 km/h at x≈782, twice |
| 11.31 s, RR | `+13` at ticks 1126–1131 | `+0.102362` | Right `2` | Instant; 230.944–230.958 km/h at x≈782, twice |
| 9.46 s, FL | `-12` at ticks 941–946 | `-0.094488` | Right `2` | Delayed; 203.36 km/h at x≈900 |
| 9.46 s, FL | `-13` at ticks 941–946 | `-0.102362` | Left `1` | Instant; 208.95 km/h at x≈900 |

The 9.46 s pair touched down at x≈912.0 and 208.5 km/h in both variants. This controls for the landing trajectory when comparing the later recovery speeds. The rightward pair's touchdown speed was also close (241.60 versus 241.45 km/h).

The smoothed steering does not jump directly from full left to the raw right input. On the 11.31 s jump it advanced approximately `-1, -0.8, -0.6, -0.4, -0.2, 0, +0.094488/+0.102362` over successive physics updates. The mirrored leftward jump advanced `+1, +0.8, +0.6, +0.4, +0.2, 0, -0.094488/-0.102362`. The measured `0.2` change per update applies to these contact conditions; it is not a universal input-duration constant. It explains why five full-right input ticks can still fail: the smoothed value has not crossed `+0.1` in a contact-eligible update.

A separate late-gap pair confirms that **crossing the threshold after the contact window is too late**. With a `+78` pulse, replacing the tick-1130 input by `-4` preserved instant grip and mode `2`; replacing it by `-5` produced delayed grip and left mode `1`. Both reached a smoothed value above `+0.1` in the first all-air snapshot (`+0.168504` and `+0.160630`). The latter did not commit right mode, showing why merely inspecting steering after takeoff is insufficient. The exact sub-update contact timing of this one-unit gap is not resolved by 50 ms wall-time sampling; the any-contact code path supplies the rule.

The landing-memory pair gives the causal link. The `+12` run had mode `2` but multiplier `1.0` near touchdown and only later recovered to `2.0`. The `+13` run had mode `2` and multiplier `2.0` throughout its sampled landing.

**Live HUD timing.** Openplanet's first display frame marked as grounded can precede the physics update that applies the contact-dependent mode and force changes. In a fresh +13/+12 TICK pair, the first grounded display sample showed `1.0` in the instant +13 run and about `1.81` in the delayed +12 run; these transient values would reverse a naive rating. Roughly 30–40 ms later, the +13 run showed mode `2` and multiplier `2.0`, and the +12 run had switched from mode `1` to `2` with multiplier `1.0`. On the earlier 6.19 s landing, the multiplier was still `1.0` at 6.212 s but had reached `2.0` by 6.265 s. The rater therefore freezes the pre-takeoff mode, captures landing steering at visible contact (with up to 30 ms for the first grounded physics tick), and grades the force sample at least 80 ms after first visible contact. A later steering reversal can reduce the force grade but cannot rewrite the captured landing direction. Its `S` and `E` verdicts matched the controlled instant and delayed runs. The HUD still samples at display-frame resolution, so it does not identify the exact last-wheel physics tick.

**Why the air display used to say `1.00x`.** The multiplier at `vehicle+0x14dc` is a stored value, and the wheel-force loop refreshes it when it calculates tire force. With no wheel force in the air, this value can stay at `1.00x` even though the stored direction is correct and the recovery timer has elapsed. At the first ice landing above, it changed to `2.00x` on contact without a visible post-landing ramp; that landing came after the 800 ms cutoff, where the code sets the target directly. A landing inside the 400–800 ms window instead ramps after contact (see *Traced landing inside the 400–800 ms window*). The prototype Rater displayed **FORCE ON CONTACT** while airborne and checked the updated multiplier after landing. This value is a multiplier inside the tire-force calculation, not a speed or acceleration reading.

## Code trail and exact fields

| Address / field | Observation |
|---|---|
| `FUN_140841500`, called from `FUN_140851f00` | Updates smoothed steer `vehicle+0x1430` from raw steer `vehicle+0xa0` using a rate limit. |
| `FUN_14084f720` at `0x14084f851` | Loads smoothed steer from `vehicle+0x1430`. |
| `FUN_140843150` at `0x140843150`, called at `0x14084f8d8` | Returns true if any of four contact flags at `vehicle+0x17b4+0xb8*i` is nonzero. |
| `FUN_14084f720` at `0x14084f900`–`0x14084f936` | Compares smoothed steer with float constants `-0.10000000149` and `+0.10000000149`; writes mode `1` or `2` at `vehicle+0x14e5`. |
| Neutral branch in `FUN_14084f720` | Starts/checks the neutral timestamp at `vehicle+0x14e0` against `model+0x1198 = 300`, and clears mode after the neutral timeout. |
| `FUN_14084f720` at `0x14084f967`–`0x14084f988` | On mode change, writes timestamp `vehicle+0x14d8` and resets `vehicle+0x14dc` to `1.0`. |
| `FUN_140851f00` calling `FUN_140850e10` | If any wheel-material entry is `74` (RoadIce), `21` (Snow), or `3` (Ice), it chooses the model curve at `model+0xcf0`; otherwise it uses `model+0xd40`. The caller scales one force contribution by `1 − curve output` and passes the output to `FUN_14084f720` for the icy-force contribution. Material names were checked against GBX.NET's material enum; the numeric choices come from the game code. |
| `FUN_1408426e0`, `FUN_140842310`, and `FUN_14083b200` | Pass car wetness and a model speed gate into each wheel's timed icing update, then turn icing into a tire coefficient. Ice/RoadIce contact starts accumulation; plastic contact starts decay. Wetness at `vehicle+0x13a4` can set a minimum icing level during decay. Model timings at `model+0xcdc/+0xce0/+0xce4` are `1,650/3,300/6,000 ms` for growth, grounded decay, and airborne decay. |
| `FUN_140869a40` and `FUN_1408465e0` | Increase and decrease `vehicle+0x13a4` under wetting and drying conditions, supporting its identification as the wetness state passed into the wheel icing update. |
| `FUN_140842500`, called from `FUN_1408426a0` | Writes the four per-wheel coefficients to `vehicle+0x1c2c..0x1c38` and their average to `vehicle+0x1c44`. The main force caller normalizes that average with model coefficient `0.8`, yielding average wheel icing in the tested status. |
| `FUN_14084f720`, later tire-force loop | Recovers `vehicle+0x14dc` using model delay `400`: unchanged below the delay, `+ step_ms / delay` per call up to twice the delay, then the target directly (caller `140851f00` passes the step in ms via constant `1000`); a multiplier at or above the target is set to the target. When `vehicle+0x1600` (`plVar2[0x2c0]`) is nonzero, the steering/speed target is skipped and the base value is used. Otherwise the target depends on smoothed-steering magnitude through a power of `1.5` and a speed-related model curve, then it multiplies a tire-force vector. |

The decompiler sometimes omits call arguments. The x64 disassembly shows `lea rcx, [rdi+0x1280]` before the contact call; `FUN_140843150` accesses `param_1+0x534`, giving `vehicle+0x17b4`. The mode code is additionally guarded by `FUN_14083dbd0`, which checks two status bits at `vehicle+0x176c` and `vehicle+0x1370`; both were zero in the paired snapshots. The other reset path tests `vehicle+0x128c & 0x20000`; that bit was also zero here.

Relevant local decompilations are `work/ghidra_decompiled/14084f98a.c` (function `FUN_14084f720`), `work/ghidra_decompiled/140843150.c`, `work/ghidra_decompiled/140841500.c`, `work/ghidra_decompiled/14083dbd0.c`, `work/ghidra_decompiled/140850e10.c`, `work/ghidra_decompiled/140851f00.c`, `work/ghidra_decompiled/14084237c.c` (`FUN_140842310`), `work/ghidra_decompiled/14083b200.c`, and `work/ghidra_decompiled/140842500.c`. Raw memory captures are `work/memory_takeoff_*.bin`, `work/memory_landing_*.bin`, `work/memory_tarmac_baseline_right.bin`, and `work/memory_neutral_*.bin`. Reproducible input files are `outputs/TICK_*.txt`, frame logs are `outputs/automated_*.csv`, and summarized jump trials are in `outputs/automated_trial_results.json`.

## Practical input rule

For a rightward ice slide after a jump, begin steering right early enough that **smoothed steering becomes strictly greater than `+0.1` while any wheel still contacts the surface**; for a leftward slide use strictly less than `-0.1`. The needed lead time depends on the starting smoothed steer, how quickly that internal value follows input, and when the final wheel lifts. Once the correct mode is committed, airborne steering can vary, provided the smoothed steering does not trigger the opposite mode when contact resumes. The shorter the airtime after the mode switch, the more of the multiplier recovery may still remain at touchdown.
