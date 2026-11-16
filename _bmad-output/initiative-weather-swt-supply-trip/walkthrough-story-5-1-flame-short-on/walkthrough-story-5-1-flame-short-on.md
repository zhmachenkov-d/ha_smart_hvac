# Walkthrough: Story 5.1 — Tracer: replace supply trip with flame short-on
Target: [PR #151](https://github.com/zhmachenkov-d/ha_smart_hvac/pull/151) · branch `feat/5-1-flame-short-on` · `918debc`

**Current block:** Broad strokes (in progress)

## Blocks
- [x] **Intent** — done (Formal review 5 patch; Test 352 + ruff)
- [ ] **Broad strokes** — in progress
- [ ] **Slice: config/models — flame fields, drop supply trip** — unvisited
- [ ] **Slice: hvac_app — remove supply path; flame observe/latch/clear** — unvisited
- [ ] **Slice: `_run_demand` latch gate + ADV8 hold-expiry** — unvisited
- [ ] **Slice: example yaml + tests flame matrix** — unvisited
- [ ] **Periphery** — unvisited

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

Review notes: Demo — [demo-broad-strokes-transcript.md](demo-broad-strokes-transcript.md) (observe latch + ADV8 + config/example + 27 matrix).

---

### Slice: config/models — flame fields, drop supply trip
*Unvisited — not yet reviewed.*

Review notes: *(none — block unvisited)*

---

### Slice: hvac_app — remove supply path; flame observe/latch/clear
*Unvisited — not yet reviewed.*

Review notes: *(none — block unvisited)*

---

### Slice: `_run_demand` latch gate + ADV8 hold-expiry
*Unvisited — not yet reviewed.*

Review notes: *(none — block unvisited)*

---

### Slice: example yaml + tests flame matrix
*Unvisited — not yet reviewed.*

Review notes: *(none — block unvisited)*

---

### Periphery
*Unvisited — not yet reviewed.*

Review notes: *(none — block unvisited)*