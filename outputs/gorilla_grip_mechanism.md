# Trackmania ice “gorilla grip”: measured mechanism

Investigated 24 September 2026 on the user's `ANGULAR _ MOMENTUM.Map.Gbx` and `AngularMomentumTAS.Replay.Gbx`, with a later check of `IOTW - Flix.Map.Gbx` and its ghost. The local `Trackmania.exe` analyzed here has SHA-256 `3FC7D8CDA542BEDA131C44306B123F4004D07D7E22F512B46B762AFC29F6EDDA`. This conclusion is specific to that physics build and the tested transitions.

## The simple version

Imagine the game keeps two things for your car: a note saying **“sliding left” or “sliding right,”** and a short recovery timer. Once the tires are icy enough for this physics branch to run, steering far enough in a new direction while **any wheel is still touching the ground** changes the note and restarts the timer. During the first part of that timer, the tire-force boost is low. That is the short period where the ice slide feels slow to gain speed.

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

For the small-input test, raw `+12/127 ≈ 0.0945` can never carry the smoothed value past `+0.1`, however long it is held. Raw `+13/127 ≈ 0.1024` can cross it once the smoothed value has caught up.

This explains the apparent few-tick wait before the game *recognizes* the new slide direction. A **second, longer delay** starts only when that stored direction changes: the tire-force multiplier stays low for about **400 ms** before recovering. On the measured delayed landing near 12.58 s, it reached its recovered value by about 13.17 s, roughly **0.6 s after touchdown**. A jump can hide much of this second delay by letting the timer run in the air. The `0.2` steering change per update was measured for these ice conditions and can differ with the physics conditions; the six- and ten-update estimates are not universal constants.

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

The direction-update code checks whether **any wheel contacts a surface**, not whether that wheel contacts ice. Another guard makes the tire-force branch inactive when its car-level icing-related factor is effectively zero. The caller derives that factor from `vehicle+0x1c44`, the model's `0.8` ice coefficient, and one of two model curves. A wheel reporting material `74` (RoadIce), `21` (Snow), or `3` selects one curve; other materials, including `77` (Plastic), select a different curve:

| Normalized car-level icing value | Curve for materials 74/21/3 | Other-material curve |
|---:|---:|---:|
| `0` | `0` | `0` |
| `0.8` | About `0.9625` | `0.3` |
| `1.0` | `1.0` | `1.0` |

Both curves at `0.8` exceed the branch's `0.00001` guard. **Thus the code supports setting or retaining the direction while on plastic if the tires remain icy enough**, then carrying that mode into the jump and landing on ice. The same alternate curve can apply on other non-ice materials if icy tires persist, but those particular surfaces were not separately tested. Surface material still matters because it chooses the curve and affects other tire forces; this is not a rule based on tire icing alone. These curve outputs are **not** the `1.0–2.0` multiplier and do not by themselves give the total tire-force ratio between surfaces.

We also measured the clean-tire tarmac start of ANGULAR ↻ MOMENTUM. During the full-right, wheel-contact interval around 2.37–2.88 s, the car-level ice coefficient field was `1.0` (no accumulated ice), the stored directional mode stayed `0`, and this multiplier stayed at its **baseline `1.0`**. At first ice contact near 2.93 s, the field began falling below `1.0` and right mode appeared. The `2.0` observed later on iced full steering is therefore **not a universal tarmac default**. These values are for this internal multiplier, not a ratio of the total grip of asphalt, plastic, and ice.

The supplied IOTW - Flix ghost confirms plastic sections with tires still heavily iced: the four visible wheel-icing readings were about `0.79–1.00` on plastic. Its recorded airtime near **35.95 s** is not a clean plastic-takeoff proof: the 50 ms ghost samples show a plastic-to-ice transition around 35.85–35.90 s and all wheels reporting RoadIce just before the airborne sample. A controlled last-contact-on-plastic run would be needed to verify that particular map claim in game. The code-path result above does not rely on that ghost's takeoff classification.

## Why the grip feels delayed

When the mode switches into a left or right direction, the code writes a timestamp and resets the tire-force multiplier at vehicle offset `0x14dc` to `1.0`. That multiplier directly appears in the tire-force calculation inside the four-wheel loop. In these full-steering ice runs its recovered target is `2.0`; with smaller steering, the target itself is lower, as the neutral trial above demonstrates. The vehicle model's delay parameter at `model+0x1194` is `400`; the code holds the multiplier at `1.0` until that interval expires, then raises it toward the target. It also limits the recovery window to twice that delay. In the measured delayed landing, it remained at `1.0` through roughly race time 12.95 s, rose from about 1.05 to 2.0 between 12.97 and 13.17 s, and was 2.0 thereafter. The fast variant had already recovered to `2.0` before landing.

| Time relative to a mode change | Tire-force multiplier in these runs | Meaning for the slide |
|---|---:|---|
| At the change | Reset to `1.0` | The timer starts; the stronger tire-force contribution is unavailable. |
| First ~400 ms | Remains near `1.0` | The car still has tire forces and can gain or lose speed, but this contribution is lower. |
| After ~400 ms | Starts rising | The stronger slide response begins returning. |
| About ~600 ms in the measured landing | Reached `2.0` | This contribution had fully recovered for that run. |

These numbers describe a **multiplier on a tire-force calculation**, not a multiplier on the car's speed or a promise of forward acceleration. In the target pair, both variants touched down near 241.5 km/h; at x≈782 the delayed run was 227.323 km/h and the pre-set run was 230.944–230.958 km/h. The recovered multiplier therefore corresponded to **less speed lost after landing** on this trajectory. On another trajectory, the same force difference can feel like stronger slide acceleration.

For a grounded slide begun by switching raw input from full left to full right in these ice conditions, the mode switch is estimated ~50–60 ms after input. Adding the timer gives an estimated **~450–460 ms from input until this force contribution starts recovering**, and **~650–660 ms until full recovery** if it follows the measured landing ramp. Those input-to-force figures are a projection from the code and the jump measurements; we have not measured a separate ground-only reversal to confirm its exact speed response.

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

## Code trail and exact fields

| Address / field | Observation |
|---|---|
| `FUN_140841500`, called from `FUN_140851f00` | Updates smoothed steer `vehicle+0x1430` from raw steer `vehicle+0xa0` using a rate limit. |
| `FUN_14084f720` at `0x14084f851` | Loads smoothed steer from `vehicle+0x1430`. |
| `FUN_140843150` at `0x140843150`, called at `0x14084f8d8` | Returns true if any of four contact flags at `vehicle+0x17b4+0xb8*i` is nonzero. |
| `FUN_14084f720` at `0x14084f900`–`0x14084f936` | Compares smoothed steer with float constants `-0.10000000149` and `+0.10000000149`; writes mode `1` or `2` at `vehicle+0x14e5`. |
| Neutral branch in `FUN_14084f720` | Starts/checks the neutral timestamp at `vehicle+0x14e0` against `model+0x1198 = 300`, and clears mode after the neutral timeout. |
| `FUN_14084f720` at `0x14084f967`–`0x14084f988` | On mode change, writes timestamp `vehicle+0x14d8` and resets `vehicle+0x14dc` to `1.0`. |
| `FUN_140851f00` calling `FUN_140850e10` | Uses material IDs `74`, `21`, and `3` to choose the model curve at `model+0xcf0`; other materials use `model+0xd40`. Their output enters `FUN_14084f720` as its nonzero activation/force factor. |
| `FUN_14084f720`, later tire-force loop | Recovers `vehicle+0x14dc` using model delay `400`; its target depends on smoothed-steering magnitude through a power of `1.5` and a speed-related model curve, then it multiplies a tire-force vector. |

The decompiler sometimes omits call arguments. The x64 disassembly shows `lea rcx, [rdi+0x1280]` before the contact call; `FUN_140843150` accesses `param_1+0x534`, giving `vehicle+0x17b4`. The mode code is additionally guarded by `FUN_14083dbd0`, which checks two status bits at `vehicle+0x176c` and `vehicle+0x1370`; both were zero in the paired snapshots. The other reset path tests `vehicle+0x128c & 0x20000`; that bit was also zero here.

Relevant local decompilations are `work/ghidra_decompiled/14084f98a.c` (function `FUN_14084f720`), `work/ghidra_decompiled/140843150.c`, `work/ghidra_decompiled/140841500.c`, `work/ghidra_decompiled/14083dbd0.c`, `work/ghidra_decompiled/140850e10.c`, and `work/ghidra_decompiled/140851f00.c`. Raw memory captures are `work/memory_takeoff_*.bin`, `work/memory_landing_*.bin`, `work/memory_tarmac_baseline_right.bin`, and `work/memory_neutral_*.bin`. Reproducible input files are `outputs/TICK_*.txt`, frame logs are `outputs/automated_*.csv`, and summarized jump trials are in `outputs/automated_trial_results.json`.

## Practical input rule

For a rightward ice slide after a jump, begin steering right early enough that **smoothed steering becomes strictly greater than `+0.1` while any wheel still contacts the surface**; for a leftward slide use strictly less than `-0.1`. The needed lead time depends on the starting smoothed steer, how quickly that internal value follows input, and when the final wheel lifts. Once the correct mode is committed, airborne steering can vary, provided the smoothed steering does not trigger the opposite mode when contact resumes. The shorter the airtime after the mode switch, the more of the multiplier recovery may still remain at touchdown.
