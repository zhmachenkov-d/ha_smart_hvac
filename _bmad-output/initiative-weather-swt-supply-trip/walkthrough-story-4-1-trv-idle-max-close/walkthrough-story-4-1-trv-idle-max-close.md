# Walkthrough: Story 4.1 — TRV idle max-close soft-close
Target: [PR #146](https://github.com/zhmachenkov-d/ha_smart_hvac/pull/146) · branch `feat/4-1-trv-idle-max-close` · `784fc71`

**Current block:** Wrap-up (in progress — commit+push done; merge deferred)

## Blocks
- [x] **Intent** — done (Test: 305 pytest; ruff clean)
- [x] **Broad strokes** — done (Test: 30 focused TRV/config)
- [x] **Slice: Config + ThermostatConfig** — done (Formal review patches + 21 config tests)
- [x] **Slice: `_apply_trv_law` before prelude** — done (Formal review patches; 321 pytest)
- [x] **Slice: Example yaml** — done (Test: example parse + 10 config)
- [x] **Periphery** — done (Test: 9/9; 321 pytest)
- [ ] **Wrap-up**

---

### Intent
Source: frozen Intent from plan [story-tracer-trv-idle-max-close-soft-close-plan.md](../tickets/epic-trv-idle-max-close/tickets/story-tracer-trv-idle-max-close-soft-close-plan.md) (Problem + Approach).

**Problem:** Commissioned Sonoff TRVs have no AppDaemon idle max-close, so residual valve flow still cycles the boiler even when weather-curve SWT is correct.

**Approach:** Add yaml `valve_closure_floor` (default 80) and per-TRV closure+accuracy wiring; Plant on writes only `valve_closure_degree` as idle max-close **limit** (floor or 100 with overshoot hysteresis); Plant off writes 100 on all commissioned Sonoff TRVs; never `valve_opening_degree`. Example yaml only — house ids are story 4.2.

Review notes: Test — 305 pytest; ruff clean.

---

### Broad strokes
Yaml commissions Sonoff closure+accuracy and floor; every tick/event applies idle max-close before water prelude; plant-off forces closure 100.

1. [models.py](../../../apps/ha_smart_hvac/models.py) (`ThermostatConfig`, `HvacConfig.valve_closure_floor`) — climate plus optional TRV wiring; floor default 80
2. [config.py](../../../apps/ha_smart_hvac/config.py) (`_parse_thermostat`, floor 0–100) — string|map parse; reject partial TRV fields; range-check floor
3. [hvac_app.py](../../../apps/ha_smart_hvac/hvac_app.py) (`control_tick` / `control_event` → `_apply_trv_law`) — TRV law before `_gate_prelude`; shared `_write_number`
4. [apps.yaml.example](../../../apps.yaml.example) — floor + mapping TRV + plain-string neighbor
5. [tests/test_hvac_app.py](../../../tests/test_hvac_app.py) (TRV matrix ~1740+) — hysteresis / plant-off / never opening

Review notes: Test — 30 focused TRV/config pytest passed (filter trv|valve_closure|…).

---

### Slice: Config + ThermostatConfig
Commissioning shape: climate string stays climate-only; mapping needs both TRV entity ids; floor defaults to 80 and must be 0–100.

1. [models.py](../../../apps/ha_smart_hvac/models.py) — `ThermostatConfig` + `commissioned`; `HvacConfig.valve_closure_floor` default 80
2. [config.py](../../../apps/ha_smart_hvac/config.py) `_parse_thermostat` — string|map; require both keys; `_entity_id` on each
3. [config.py](../../../apps/ha_smart_hvac/config.py) floor parse — default + `0..100` `ConfigError`
4. [test_config.py](../../../tests/test_config.py) — override, out-of-range, mapping commissioned, partial/invalid reject

Review notes: Formal review — 2 patch applied (reject-matrix + floor 0/100 accept); 1 defer whitespace; 9 rejected. Test: 21 focused config.

---

### Slice: `_apply_trv_law` before prelude
Every `control_tick` / `control_event` applies idle max-close before water `_gate_prelude`. Plant off writes 100 on commissioned closures (no SWT via this path). Plant on: overshoot→100+latch; clear at T≤setpoint→floor; dead-band keeps 100. Writes go through `_write_number`, never `_write_setpoint`.

1. [hvac_app.py](../../../apps/ha_smart_hvac/hvac_app.py) `control_tick` / `control_event` — `_apply_trv_law()` before prelude
2. [hvac_app.py](../../../apps/ha_smart_hvac/hvac_app.py) `_apply_trv_law` — plant-on hysteresis / plant-off 100; latch by `valve_closure` id
3. [hvac_app.py](../../../apps/ha_smart_hvac/hvac_app.py) `_write_number` — equal-float number helper
4. [hvac_app.py](../../../apps/ha_smart_hvac/hvac_app.py) `_register_control_listeners` — listens on `thermo.climate` attrs
5. [test_hvac_app.py](../../../tests/test_hvac_app.py) — TRV matrix (~1740+)

Review notes: Formal review — 2 patch applied (latched accuracy gate + boundary/unreadable/init/event tests); 11 rejected. Test: 24 focused TRV.

---

### Slice: Example yaml
Example commissions floor + one Sonoff mapping + plain-string neighbor; house ids stay story 4.2.

1. [apps.yaml.example](../../../apps.yaml.example) — `valve_closure_floor: 80`; mapping TRV; generic string thermostat
2. [test_config.py](../../../tests/test_config.py) `test_parse_apps_yaml_example` — parses example; asserts floor + commissioned + plain-string

Review notes: Test — test_parse_apps_yaml_example + related valve_closure config tests passed.

### Periphery
Review notes: Test — 9/9 periphery checks; 321 pytest; ruff clean.

Outside the three code slices:
1. [deferred-work.md](../deferred-work.md) — accuracy re-apply, prelude-isolation ACs, expanded goldens, whitespace `_entity_id`
2. [story-tracer-trv-idle-max-close-soft-close-plan.md](../tickets/epic-trv-idle-max-close/tickets/story-tracer-trv-idle-max-close-soft-close-plan.md) — frozen Intent + Code Review findings/patches
3. [tickets.toml](../tickets/epic-trv-idle-max-close/tickets/tickets.toml) — epic 4 entry 1 tracer / entry 2 HITL split
4. Local dirty from this review — walkthrough folder; uncommitted `hvac_app`/tests/plan patches from Formal review

### Wrap-up
Review complete for [PR #146](https://github.com/zhmachenkov-d/ha_smart_hvac/pull/146) (story 4.1).

Follow-through so far: **commit + push** `b4d7603` (Formal review patches + walkthrough). **Merge deferred** — say if you want `gh pr merge`. House yaml remains story 4.2.
