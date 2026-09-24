# Trackmania ice “gorilla grip”: measured mechanism

Investigated 24 September 2026 on the user's `ANGULAR _ MOMENTUM.Map.Gbx` and `AngularMomentumTAS.Replay.Gbx`. The local `Trackmania.exe` analyzed here has SHA-256 `3FC7D8CDA542BEDA131C44306B123F4004D07D7E22F512B46B762AFC29F6EDDA`. This conclusion is specific to that physics build and the tested ice transitions.

## The simple version

Imagine the game keeps two things for your car: a note saying **“sliding left” or “sliding right,”** and a short recovery timer. When you steer far enough in a new direction while **any wheel is still touching the ground**, the game changes the note and restarts the timer. During the first part of that timer, the tire-force boost is low. That is the short period where the ice slide feels slow to gain speed.

The game looks at steering that has been smoothed over several physics updates. A tiny tap may not change the note immediately. In the tested build, the smoothed steering must pass **10% left or right**. It does not matter which wheel is touching; the **last wheel to lift is your deadline** before a jump.

| Situation | What happens |
|---|---|
| Start or reverse a slide while staying on the ice | If this changes the stored direction, the recovery timer runs **while you are driving**. You can feel the slow start, then the stronger slide. |
| Set the new direction just before a jump | The direction changes before takeoff. The timer keeps running **during the flight**, so the stronger force can be ready when you land. |
| Wait until landing to set the new direction | The timer starts **on landing**. You feel the brief weak period after touchdown. |

Steering either way in mid-air can change where the car points, but it cannot rewrite this note while no wheel touches. You still need the intended steering for the landing. **Yes: this mechanism also operates without an air transition.** The code contains no requirement to jump. Our controlled speed comparisons specifically tested jumps, so this report does not claim that every slow-feeling grounded slide is caused only by this timer; speed, angle, and surface contact can affect the result too.

If the note already says the direction you want, this particular direction change does not restart the timer.

### How many ticks for a full steering reversal?

The deciding value is an **internal smoothed steering number**, not the raw button/TICK input or the visible front-wheel angle. In these ice-contact runs, it changed by about `0.2` per **10 ms physics update** when we switched from full left (`-1`) toward full right (`+1`):

`-1 → -0.8 → -0.6 → -0.4 → -0.2 → 0 → +0.2 → … → +1`

The **sixth affected update** reaches `+0.2`, which is the first value above the required `+0.1`; if a wheel still touches then, the car stores right mode. That is roughly **50–60 ms after the raw input change**, depending on whether the input arrives just before or just after a physics update. It takes **ten affected updates**, roughly **90–100 ms**, for this internal number to reach full right. Full right to full left is symmetric.

For the small-input test, raw `+12/127 ≈ 0.0945` can never carry the smoothed value past `+0.1`, however long it is held. Raw `+13/127 ≈ 0.1024` can cross it once the smoothed value has caught up.

This explains the apparent few-tick wait before the game *recognizes* the new slide direction. A **second, longer delay** starts only when that stored direction changes: the tire-force multiplier stays low for about **400 ms** before recovering. On the measured delayed landing near 12.58 s, it reached its recovered value by about 13.17 s, roughly **0.6 s after touchdown**. A jump can hide much of this second delay by letting the timer run in the air. The `0.2` steering step is measured for these ice conditions and can differ with the physics conditions; the six- and ten-update estimates are not universal constants.

## The deciding rule

The physics code keeps a **car-level directional slide mode**. For these tests, mode `1` is left and mode `2` is right. On a physics update where at least **one of the four wheels has a ground-contact flag**, it reads **smoothed steering**, not the raw TICK input:

| Smoothed steering in the contact-eligible update | New mode |
|---|---:|
| Less than `-0.1` | `1` (left) |
| Between `-0.1` and `+0.1`, including the endpoints | Keep the previous mode initially; clear to neutral only after its 300-unit timer |
| Greater than `+0.1` | `2` (right) |

The code also checks two special vehicle-status flags. They were clear in all of these runs. The contact check loops over all four wheels and returns as soon as **any** contact flag is nonzero. There is no fixed front, rear, left, or right wheel that owns this mode. The **last wheel still touching the surface supplies the final opportunity** to commit the intended direction before airtime.

On the supplied 11.26–12.58 s transition, that last wheel is **rear-right** (internal wheel index 2). On the independent 9.41–10.38 s transition, it is **front-left** (internal index 0). The same threshold rule predicts both. An after-update snapshot can already show all four flags clear even though the mode changed in that update; use the code's contact check and the immediately preceding contact snapshot to interpret that boundary, rather than the displayed race timestamp alone.

While all wheels are airborne, smoothed steering still follows air inputs, but this contact-gated mode does not update. Thus steering either way during the spin can leave the previously committed mode intact. To get the intended rightward response on landing, the car must arrive with right mode already stored and rightward landing input. If it arrives carrying left mode, the first eligible landing update changes it to right and starts the recovery delay.

## Why the grip feels delayed

Every directional-mode change writes a timestamp and resets the tire-force multiplier at vehicle offset `0x14dc` to `1.0`. That multiplier directly appears in the tire-force calculation inside the four-wheel loop. In these ice runs its recovered value is `2.0`. The vehicle model's delay parameter at `model+0x1194` is `400`; the code holds the multiplier at `1.0` until that interval expires, then raises it toward the target. It also limits the recovery window to twice that delay. In the measured delayed landing, it remained at `1.0` through roughly race time 12.95 s, rose from about 1.05 to 2.0 between 12.97 and 13.17 s, and was 2.0 thereafter. The fast variant had already recovered to `2.0` before landing.

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

The smoothed steering does not jump directly from full left to the raw right input. On the 11.31 s jump it advanced approximately `-1, -0.8, -0.6, -0.4, -0.2, 0, +0.094488/+0.102362` over successive physics updates. The mirrored leftward jump advanced `+1, +0.8, +0.6, +0.4, +0.2, 0, -0.094488/-0.102362`. The measured `0.2` per update is the slew rate in these contact conditions, not a universal input-duration constant. It explains why five full-right input ticks can still fail: the smoothed value has not crossed `+0.1` in a contact-eligible update.

A separate late-gap pair confirms that **crossing the threshold after the contact window is too late**. With a `+78` pulse, replacing the tick-1130 input by `-4` preserved instant grip and mode `2`; replacing it by `-5` produced delayed grip and left mode `1`. Both reached a smoothed value above `+0.1` in the first all-air snapshot (`+0.168504` and `+0.160630`). The latter did not commit right mode, showing why merely inspecting steering after takeoff is insufficient. The exact sub-update contact timing of this one-unit gap is not resolved by 50 ms wall-time sampling; the any-contact code path supplies the rule.

The landing-memory pair gives the causal link. The `+12` run had mode `2` but multiplier `1.0` near touchdown and only later recovered to `2.0`. The `+13` run had mode `2` and multiplier `2.0` throughout its sampled landing.

## Code trail and exact fields

| Address / field | Observation |
|---|---|
| `FUN_140841500`, called from `FUN_140851f00` | Updates smoothed steer `vehicle+0x1430` from raw steer `vehicle+0xa0` using a rate limit. |
| `FUN_14084f720` at `0x14084f851` | Loads smoothed steer from `vehicle+0x1430`. |
| `FUN_140843150` at `0x140843150`, called at `0x14084f8d8` | Returns true if any of four contact flags at `vehicle+0x17b4+0xb8*i` is nonzero. |
| `FUN_14084f720` at `0x14084f900`–`0x14084f936` | Compares smoothed steer with float constants `-0.10000000149` and `+0.10000000149`; writes mode `1` or `2` at `vehicle+0x14e5`. |
| `FUN_14084f720` at `0x14084f967`–`0x14084f988` | On mode change, writes timestamp `vehicle+0x14d8` and resets `vehicle+0x14dc` to `1.0`. |
| `FUN_14084f720`, later tire-force loop | Recovers `vehicle+0x14dc` using model delay `400`, then multiplies the tire-force vector by it. |

The decompiler sometimes omits call arguments. The x64 disassembly shows `lea rcx, [rdi+0x1280]` before the contact call; `FUN_140843150` accesses `param_1+0x534`, giving `vehicle+0x17b4`. The mode code is additionally guarded by `FUN_14083dbd0`, which checks two status bits at `vehicle+0x176c` and `vehicle+0x1370`; both were zero in the paired snapshots. The other reset path tests `vehicle+0x128c & 0x20000`; that bit was also zero here.

Relevant local decompilations are `work/ghidra_decompiled/14084f98a.c` (function `FUN_14084f720`), `work/ghidra_decompiled/140843150.c`, `work/ghidra_decompiled/140841500.c`, and `work/ghidra_decompiled/14083dbd0.c`. Raw memory captures are `work/memory_takeoff_*.bin` and `work/memory_landing_*.bin`. Reproducible input files are `outputs/TICK_*.txt`, frame logs are `outputs/automated_*.csv`, and summarized trials are in `outputs/automated_trial_results.json`.

## Practical input rule

For a rightward ice slide after a jump, begin steering right early enough that **smoothed steering becomes strictly greater than `+0.1` while any wheel still contacts the surface**; for a leftward slide use strictly less than `-0.1`. The needed lead time depends on the starting smoothed steer, its slew rate, and when the final wheel lifts. Once the correct mode is committed, airborne steering can vary, provided the intended steering is restored for landing. The shorter the airtime after the mode switch, the more of the multiplier recovery may still remain at touchdown.
