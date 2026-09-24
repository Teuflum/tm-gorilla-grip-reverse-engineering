# Trackmania ice “gorilla grip”: measured mechanism

Investigated 24 September 2026 on the user's `ANGULAR _ MOMENTUM.Map.Gbx` and `AngularMomentumTAS.Replay.Gbx`. The local `Trackmania.exe` analyzed here has SHA-256 `3FC7D8CDA542BEDA131C44306B123F4004D07D7E22F512B46B762AFC29F6EDDA`. This conclusion is specific to that physics build and the tested ice transitions.

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
