# Gorilla Grip Rater Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and install an original Gorilla Grip Rater Openplanet plugin with verified live steering telemetry and arcade-style transition grading.

**Architecture:** A read-only telemetry layer supplies exact physics fields when a current-vehicle pointer is validated; VehicleState supplies visible wheel/contact context. A small transition state machine produces one verdict per eligible flight. An original NanoVG HUD renders the steering gate, airtime, verdict, combo, and settings.

**Tech Stack:** Python 3.11 for read-only validation tools and tests; Openplanet AngelScript, VehicleState, and NanoVG for the plugin.

**Spec:** [Gorilla Grip Rater design](../specs/2026-09-24-gorilla-grip-rater.md)

## Global Constraints

- Tested game build SHA-256: `3FC7D8CDA542BEDA131C44306B123F4004D07D7E22F512B46B762AFC29F6EDDA`.
- No writes to Trackmania process memory.
- Never present an inferred steering value as an exact physics read.
- Do not distribute game binaries, the downloaded map/replay, raw memory dumps, third-party plugin code, or telemetry CSVs.

## Review Focus

- Stale vehicle pointer after restart: exact telemetry must disappear rather than read unrelated memory.
- Display-frame misses of first/last contact: verdict must avoid pretending to know an unobserved tick.
- Ambiguous landing steering: no false MISS or success before intent is clear.
- Short hop/low icing: configurable eligibility filters should suppress spam.
- Game build change: disable build-specific exact reads.

## Task 1: Validate an exact read path

- [x] Trace the active physics vehicle pointer from live memory. Openplanet `CSmPlayer+0x1118` points to the physics car on the tested build.
- [x] Recheck the pointer across automated map restarts and compare smoothed steer, mode, and multiplier with controlled TICK trials. A full process restart was not needed for these trials.
- [x] Implement build and active-car validation; show EXACT PHYSICS or ESTIMATE on the HUD.
- [x] Document the access path and failure behavior.

## Task 2: Define and test the rating model

- [x] Exercise success, missed direction, unready multiplier, short hop, combo gain/break, and run reset in the in-game state machine using the established TICK replays and Openplanet verdict logs.
- [x] Implement the transition state machine. It waits 30 ms after visible contact to avoid sampling the pre-update force value.
- [x] Compare +13 and +12 controlled variants against speed and direct physics measurements.

## Task 3: Build the Openplanet plugin

- [x] Create `outputs/GorillaGripRater/info.toml` and original AngelScript source.
- [x] Wire verified telemetry and VehicleState to the state machine; show exact or estimated source prominently.
- [x] Draw an arcade HUD with steering gate, stored mode, airtime, verdict animation, combo score, and previous-run summary.
- [x] Add settings for layout and grading filters.

## Task 4: Install, verify, and publish

- [x] Install in `C:\Users\Tobi\OpenplanetNext\Plugins\GorillaGripRater` and verify Openplanet loads it without script errors.
- [x] Compare at least one successful and one failed controlled transition in game with recorded physics fields.
- [ ] Run tests, audit staged files, update README/report, then commit and push to the specified GitHub remote.
