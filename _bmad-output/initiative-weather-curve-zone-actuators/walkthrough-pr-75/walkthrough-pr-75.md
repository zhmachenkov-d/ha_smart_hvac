# Walkthrough: PR #75 — Event-driven SWT gate re-evaluation

Target: [PR #75](https://github.com/zhmachenkov-d/ha_smart_hvac/pull/75) (`feat/2-1-event-driven-swt-gate` → `main`).

Story plan: [story-tracer-event-driven-swt-gate-re-evaluation-plan.md](../epic-immediate-swt-reactivity/story-tracer-event-driven-swt-gate-re-evaluation-plan.md).

Current block: **Wrap-up** (done — review finished)

## Blocks

- [x] **1. Intent** — done
- [x] **2. Broad strokes** — done
- [x] **3. R8 listeners** — done
- [x] **4. Shared gate prelude** — done
- [x] **5. Dual entrypoints** — done
- [x] **6. R8 test matrix** — done
- [x] **7. Periphery** — done

---

### 1. Intent

Source: frozen Intent in [story-tracer-event-driven-swt-gate-re-evaluation-plan.md](../epic-immediate-swt-reactivity/story-tracer-event-driven-swt-gate-re-evaluation-plan.md) (lines 21–25).

**Problem:** Plant Management, thermostat `hvac_action` / setpoint, zone air, and Outdoor Temperature only affect Set Water Temperature on the next periodic `control_interval`, so R1…R3 gate writes can lag those inputs.

**Approach:** Register AppDaemon `listen_state` on the R8 trigger set. Dual entrypoints share a gate prelude: `control_event` re-applies R1…R3 and on demand writes via `clamp_uff` only; `control_tick` keeps the full path including `process_demand` / R7.

---

### 2. Broad strokes

R8 wires `listen_state` → `control_event`; both event and tick share `_gate_prelude` for R1…R3; demand forks by entry (event = `clamp_uff`, tick = `process_demand`).

1. [hvac_app.py — `_register_cap8_listeners`](../../../apps/ha_smart_hvac/hvac_app.py#L45-L58) — plant / outdoor / zone air / climate `hvac_action` + `temperature`.
2. [hvac_app.py — `_gate_prelude`](../../../apps/ha_smart_hvac/hvac_app.py#L60-L90) — shared plant-off / outdoor / zones / idle; returns `(zones, outdoor)` only on demand.
3. [hvac_app.py — `control_event`](../../../apps/ha_smart_hvac/hvac_app.py#L110-L130) — event demand writes `clamp_uff` only (no R7).
4. [hvac_app.py — `control_tick`](../../../apps/ha_smart_hvac/hvac_app.py#L92-L108) — periodic demand still `process_demand` + optional FF persist.
5. [test_hvac_app.py — R8 tests](../../../tests/test_hvac_app.py#L662-L924) — listener registration + matrix locks (stub-only).

---

### 3. R8 listeners

`initialize` registers R8 `listen_state` callbacks to `control_event`, then still schedules `run_every(control_tick)`. Climate uses `attribute=` for `hvac_action` and setpoint `temperature`; plant, outdoor, and zone air listen on entity state.

- [initialize](../../../apps/ha_smart_hvac/hvac_app.py#L37-L43)
- [_register_cap8_listeners](../../../apps/ha_smart_hvac/hvac_app.py#L45-L58)
- [test_cap8_initialize_registers_listeners](../../../tests/test_hvac_app.py#L671-L712)

---

### 4. Shared gate prelude

One prelude owns R1…R3 side effects: plant-off clears ephemeral and hands off (no write); missing outdoor / no valid zones clear ephemeral and write `0`; idle clears ephemeral and writes `0`. On Heating Demand it returns `(zones, outdoor)` and leaves the demand fork to the caller.

- [_gate_prelude](../../../apps/ha_smart_hvac/hvac_app.py#L60-L90)

---

### 5. Dual entrypoints

No `advance_cap7` flag. After a non-`None` prelude: `control_event` writes `corrector.clamp_uff(outdoor)` and never calls `process_demand` / persist; `control_tick` runs `process_demand` and may persist when `params_changed and write_ok`. Listen-state callback args are ignored; state is re-read in the prelude. Write throttle remains `_write_setpoint` float equality skip.

- [control_event](../../../apps/ha_smart_hvac/hvac_app.py#L110-L130)
- [control_tick](../../../apps/ha_smart_hvac/hvac_app.py#L92-L108)
- [_write_setpoint](../../../apps/ha_smart_hvac/hvac_app.py#L253-L269)

---

### 6. R8 test matrix

Hass stubs invoke `_fire_control_event` / `control_tick` directly — no timer race. Locks: demand clamp without `process_demand`, outdoor flip, plant-off, idle, outdoor missing, no zones, R7 ephemeral unchanged on event, seed→event→tick, equality skip, listeners + `run_every`.

- [_fire_control_event](../../../tests/test_hvac_app.py#L662-L664)
- R8 tests from [test_cap8_initialize_registers_listeners](../../../tests/test_hvac_app.py#L671) through the equality-skip case (~L924)

---

### 7. Periphery

- [epic-immediate-swt-reactivity.md](../epic-immediate-swt-reactivity/epic-immediate-swt-reactivity.md) — R8 wording + tracer decisions note
- [story-tracer-event-driven-swt-gate-re-evaluation-plan.md](../epic-immediate-swt-reactivity/story-tracer-event-driven-swt-gate-re-evaluation-plan.md) — frozen plan (status built)
- [tickets.toml](../epic-immediate-swt-reactivity/tickets.toml) — story 1 `verify` reworded (stub-honest: event callback / no process_demand)
- ADR/docs deferred to story 2.2 (out of this PR)
