# Walkthrough: Story 5.1 — Tracer: replace supply trip with flame short-on
Target: [PR #151](https://github.com/zhmachenkov-d/ha_smart_hvac/pull/151) · branch `feat/5-1-flame-short-on` · `e2d9884`+

**Current block:** Wrap-up (done — merged PR #151; story marked done)

## Blocks
- [x] **Intent** — done (Formal review 5 patch; Test 352 + ruff)
- [x] **Broad strokes** — done (Demo transcript)
- [x] **Slice: config/models — flame fields, drop supply trip** — done (Test 20 config)
- [x] **Slice: hvac_app — remove supply path; flame observe/latch/clear** — done (Test 27+; Formal review 5 patch)
- [x] **Slice: `_run_demand` latch gate + ADV8 hold-expiry** — done (Test 15; Formal review 6 patch)
- [x] **Slice: example yaml + tests flame matrix** — done (Test 20+39)
- [x] **Periphery** — done
- [x] **Wrap-up** — done (merged PR #151; story marked done)

---

### Intent
Source: frozen Intent from plan [story-tracer-replace-supply-trip-with-flame-short-on-plan.md](../tickets/epic-replace-supply-trip-with-flame/tickets/story-tracer-replace-supply-trip-with-flame-short-on-plan.md) (Problem + Approach).

**Problem:** Supply rise-rate trip is the wrong plant anti-cycle after TRV soft-close; flame short-on must gate weather-curve demand instead.

**Approach:** Remove supply trip end-to-end; add yaml `flame_on` / `ch_active` / `flame_on_min_s` (default 300) / `flame_trip_hold_s` (default 900); short True→False flame under Plant∧Demand∧`ch_active`∧¬latch latches SWT `0` after successful write; clear on hold / zone rising-edge / plant-off / successful idle write-0; ADV8 hold-expiry = `_apply_trv_law` then Outdoor prelude + demand. Example yaml only — house ids are epic entry id=2.

Review notes: Formal review — 5 patch applied (ch_active wipe+tests, since-None fall, closed-gate arm, ADV8 TRV assert, `_flame_trip_app` kwargs); 15 rejected; Test — 352 pytest + ruff clean.

---

### Broad strokes
Supply rise-rate trip is gone; flame short-on observes binary `flame_on` under Plant∧Demand∧`ch_active`, latches SWT 0 on short True→False, and ADV8 clears via TRV then Outdoor prelude.

1. [hvac_app.py](../../../apps/ha_smart_hvac/hvac_app.py) (`_flame_observe_gate` / `flame_event` ~L133) — Outdoor-free observe; arm `"off"→"on"`; short `"on"→"off"` latches after write-0
2. [hvac_app.py](../../../apps/ha_smart_hvac/hvac_app.py) (`_run_demand` / `_flame_trip_hold_expired` ~L160) — latched demand keeps 0; hold expiry ADV8 = TRV → prelude → curve
3. [config.py](../../../apps/ha_smart_hvac/config.py) / [models.py](../../../apps/ha_smart_hvac/models.py) (`flame_on` / `ch_active` ~L221) — required entities; min/hold defaults; trip keys dropped
4. [apps.yaml.example](../../../apps.yaml.example) (~L14) — `YOUR_*` flame placeholders; no `boiler_water` / `r_max` / supply hold
5. [test_hvac_app.py](../../../tests/test_hvac_app.py) (flame matrix ~L1077+) — latch/clear/TRV-while-latched/ADV8 goldens

Review notes: Demo — [demo-broad-strokes-transcript.md](demo-broad-strokes-transcript.md) (observe latch + ADV8 + config/example + 27 matrix); accepted after Demo + commit/push.

---

### Slice: config/models — flame fields, drop supply trip
`HvacConfig` commissions required `flame_on` / `ch_active` plus optional min/hold (defaults 300 / 900, hold fractional-truncate ≥1). Supply-trip fields are absent from the model and `_KNOWN_KEYS`; leftover `boiler_water` / `r_max` / `hold` land in `ignored_keys`.

1. [models.py](../../../apps/ha_smart_hvac/models.py) (`HvacConfig` ~L78) — `flame_on`, `ch_active`, `flame_on_min_s`, `flame_trip_hold_s`; no boiler_water/r_max/hold
2. [config.py](../../../apps/ha_smart_hvac/config.py) (`_KNOWN_KEYS` ~L32) — flame keys known; trip keys unknown → ignored
3. [config.py](../../../apps/ha_smart_hvac/config.py) (`parse_config` ~L221) — require entities; validate min >0; hold truncate int ≥1
4. [test_config.py](../../../tests/test_config.py) (~L126+) — defaults, missing/empty reject, truncate, legacy ignore

Review notes: Test — 20 focused config (flame/legacy/example) + ruff clean; accepted.

---

### Slice: hvac_app — remove supply path; flame observe/latch/clear
`supply_event` / `_supply_sample` / `_plant_and_heating_demand` are gone. Flame listens arm only on `"off"→"on"` under Outdoor-free observe gate; short `"on"→"off"` writes SWT 0 and latches only after success; `ch_active_event` wipes `since` when CH leaves on or the gate is closed.

1. [hvac_app.py](../../../apps/ha_smart_hvac/hvac_app.py) (`initialize` ~L48) — listen `flame_on` / `ch_active`; RAM latch fields
2. [hvac_app.py](../../../apps/ha_smart_hvac/hvac_app.py) (`_flame_observe_gate` ~L133) — Plant∧Demand∧CH∧¬latch; no Outdoor
3. [hvac_app.py](../../../apps/ha_smart_hvac/hvac_app.py) (`flame_event` ~L172) — strict binary arm/fall; latch after write-0 + `run_in` hold
4. [hvac_app.py](../../../apps/ha_smart_hvac/hvac_app.py) (`ch_active_event` ~L225) — wipe on `new != "on"` or closed gate
5. [test_hvac_app.py](../../../tests/test_hvac_app.py) (~L1080+) — short/long/write-fail/edges/CH bounce goldens

Review notes: Test — 27 flame/CH observe-latch goldens + ruff clean; Formal review — 5 patch applied (latch after run_in; non-default min/hold; orphan assert; armed-since wipe; e2e latch→expiry); 9 rejected; accepted.

---

### Slice: `_run_demand` latch gate + ADV8 hold-expiry
While flame-latched, `_run_demand` keeps SWT 0 (no curve, no CZ). Hold expiry clears, runs `_apply_trv_law`, then Outdoor prelude + demand (ADV8). Other clears: zone rising-edge under prelude, plant-off via `_hands_off`, Decision C idle write-0.

1. [hvac_app.py](../../../apps/ha_smart_hvac/hvac_app.py) (`_run_demand` ~L263) — latched branch writes 0 only
2. [hvac_app.py](../../../apps/ha_smart_hvac/hvac_app.py) (`_flame_trip_hold_expired` ~L160) — ADV8 TRV → prelude → demand
3. [hvac_app.py](../../../apps/ha_smart_hvac/hvac_app.py) (`_gate_prelude` ~L104) — rising-edge clear when latched
4. [hvac_app.py](../../../apps/ha_smart_hvac/hvac_app.py) (`_hands_off` / `_go_idle` ~L302) — plant-off clear; Decision C idle
5. [test_hvac_app.py](../../../tests/test_hvac_app.py) (~L1374+) — latched demand, ADV8, rising-edge, TRV-while-latched

Review notes: Test — 15 latched/ADV8/rising-edge/TRV-while-latched + ruff clean; Formal review — 6 patch applied (latched retention/write-fail; closed-gate disarm asserts; TRV control_event; ADV8 valve write; CH-off keep latch; Decision C token); 9 rejected; accepted.

---

### Slice: example yaml + tests flame matrix
Example commissions `YOUR_*` flame placeholders and drops supply-trip keys. Config/app tests lock parse defaults, legacy ignore, and the flame short-on matrix (arm/fall/latch/clear/ADV8/TRV-while-latched).

1. [apps.yaml.example](../../../apps.yaml.example) (~L14) — `flame_on` / `ch_active` / min/hold; no `boiler_water` / `r_max` / supply hold
2. [test_config.py](../../../tests/test_config.py) (`test_parse_apps_yaml_example` ~L70) — flame keys present; trip keys absent
3. [test_config.py](../../../tests/test_config.py) (~L126+) — defaults, reject missing/empty, truncate, legacy ignore
4. [test_hvac_app.py](../../../tests/test_hvac_app.py) (~L1080+) — flame matrix + review goldens

Review notes: Test — 20 config + 39 flame-matrix pytest; example has flame keys / no trip keys; ruff apps+tests clean; accepted.

---

### Periphery
Planning/process residue beside the App swap — not live water law.

1. [deferred-work.md](../deferred-work.md) (token-split 5.1) — parked U1/S1/E1/V1 goldens and meta ACs
2. [story-tracer-…-plan.md](../tickets/epic-replace-supply-trip-with-flame/tickets/story-tracer-replace-supply-trip-with-flame-short-on-plan.md) — Code Review appendices from this walkthrough
3. [party-mode … .memlog.md](../../party-mode/memories/installed/.memlog.md) — party planning notes for epic 5
4. [walkthrough-story-5-1-flame-short-on/](.) — this review narrative, log, demo transcript

Review notes: accepted.

---

### Wrap-up
Merged [PR #151](https://github.com/zhmachenkov-d/ha_smart_hvac/pull/151); story 5.1 plan `status: done`. House flame commission is entry 5.2.

Review notes: User confirmed merge + mark done (1+2).
