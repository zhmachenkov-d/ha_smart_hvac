---
title: '1.1 Tracer: fixed-gain PID SWT law'
type: 'feature'
ticket: '1'
created: '2026-11-07'
status: 'built'
baseline_revision: 'dcedf7d8d56ebf19bcaead7e5b7f8ffa335473e7'
route: 'full'
route_source: 'auto'
risk: 'high'
review: 'quick'
review_source: 'pinned'
lenses_ran: ['quick']
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Demand SWT still follows weather feedforward (`clamp(u_ff)`), so zone comfort is driven by outdoor/FF/CAP-7 rather than fixed-gain multi-zone PID.

**Approach:** On Plant Management + Heating Demand, command `round_0.1(clamp(base_water_temp + u_pid))` from weighted demand-zone averages over **successfully read** demand-zone snapshots (`e = Tset_w − Tair_w`, `u_pid = Kp·e + Ki·∫e`, Kd = 0); per demand zone `Tair` = `zone_temp`, `Tset` = max setpoint among that zone's heating thermostats (same eligibility as Critical Zone); outdoor is not a demand gate and is not registered as a control listener; anti-windup = integral clamps **plus** freeze `∫ += e·dt` on tick when the pre-clamp command is outside `[setpoint_min, setpoint_max]` and `e` has the same sign as the saturation; idle writes 0 and clears integral + last→`None` (clear even if write fails) while plant-entity equal-float skip remains; plant-off clears without write; also skip when rounded equals last commanded; Critical Zone stays log-only (Floor fields on demand success INFO). Interim: demand writes still on tick **and** event, but integral advances only on `control_tick`; leave FF/CAP-7 modules and weather/outdoor **parse/yaml** until entry 3 (no R4 / no full R5–R6 claim).

## Boundaries & Constraints

**Always:**
- SWT clamp uses only `setpoint_min` / `setpoint_max`.
- Heating Demand = any zone with thermostat `hvac_action == "heating"` (unchanged), evaluated only on successfully built zone snapshots (invalid air/setpoint reads skipped with WARNING — status quo `_read_zones`).
- PID averages only over demand zones **in that snapshot set**; per demand zone `Tair` = `zone_temp`, `Tset` = max heating-thermostat setpoint; per-zone yaml `weight` omit → 1.0 then normalize.
- Defaults: `base_water_temp=40`, `kp=1.0`, `ki=0.1`, `integral_min=-50`, `integral_max=50`, `control_interval` omit → 300 — epic C4 **starting commission** values, not house-proven.
- Anti-windup: after a tick integral step (when not frozen), clamp ∫ to `[integral_min, integral_max]`; **Decision:** on `control_tick`, if `raw = base_water_temp + u_pid` is `> setpoint_max` and `e > 0`, or `raw < setpoint_min` and `e < 0`, do **not** apply `∫ += e·dt` (saturation freeze); otherwise advance then clamp ∫.
- Clear inventory: ephemeral integral + last commanded SWT; no new persisted PID JSON.
- AppDaemon `ha_smart_hvac` writing existing plant entity only.
- Decision: Outdoor is not a demand-gate input; missing outdoor does not idle; do **not** register Outdoor as a control listener (Plant Management, zone air, thermostat `hvac_action` / setpoint only). Weather/outdoor parse and FF package files may remain until entry 3.
- Decision: On idle/fail clear paths, clear integral + last commanded to `None` even when write `0` fails; keep plant-entity equal-float skip in `_write_setpoint` as a second throttle so repeat idle `0` does not spam the plant.
- Decision: This story / epic-1 runtime Done does **not** require CONTEXT/ADR green; HITL «do not commission live Exclusive Session until epic 2 docs/ADR closed» is an operator note, not an AC.
- Decision: Demand success INFO Floor MUST include `e`, `u_pid`, rounded `command`, and Critical Zone id/name when selected; prose free (no outdoor/u_ff).

**Never:**
- Drive SWT from max Zone Error / Critical Zone.
- Remove outdoor/FF/CAP-7 package files (entry 3) or claim tick-only demand writes / event clear-only for demand (full R5/R6 — entry 2).
- RLS, Kd ≠ 0, ADR/CONTEXT/AGENTS edits (epic 2 / other stories).
- Change Exclusive Session or Heating Demand definition.
- Gate demand on outdoor availability.
- Treat CONTEXT/ADR updates or live Exclusive Session HITL as Acceptance Criteria for this tracer.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Demand happy (tick) | Plant on, ≥1 heating zone, valid air/setpoints, `control_tick`, unsaturated | Write `round(clamp(base + u_pid), 1)`; advance integral by `e·dt` then clamp to `[integral_min, integral_max]` | — |
| Demand event (interim) | Same demand valid, `control_event` | May write `round(clamp(base + u_pid), 1)`; integral **unchanged** | — |
| SWT sat. freeze (tick) | `raw = base+u_pid` outside `[min,max]` and `e` same sign as sat. | Write clamped/rounded command; **do not** apply `∫ += e·dt` | — |
| Weighted averages | Two demand zones, weights 1 and 3; multi-thermostat zone uses max heating setpoint as `Tset` | `Tair_w`/`Tset_w` use normalized weights; `e` from those | — |
| Partial zones (A1) | Some zones invalid air/setpoint; ≥1 valid demand snapshot | Skip invalid with WARNING; demand + PID average only over successful snapshots | WARNING per skip |
| Equal rounded skip | Rounded command == last commanded SWT | No `number/set_value` | — |
| Plant equal-float skip | Plant entity already equals value to write | No `number/set_value` (second throttle) | — |
| Idle | Plant on, no heating demand | Write `0` (best-effort); clear integral + last→`None` even if write fails | — |
| Idle write fail | Plant on, no demand, plant entity unavailable | No successful write; still clear integral + last→`None` | Log warning |
| Plant off | Plant switch ≠ on | No SWT write; clear integral + last commanded | Log warning |
| Outdoor missing | Plant on, outdoor unavailable, demand otherwise valid | Demand PID path still runs (no outdoor gate) | — |
| Outdoor not listened | App initialized | Outdoor entity is **not** among control listeners | — |
| No valid zones | Plant on, all zone reads fail (empty snapshots) | Write `0`; clear integral + last commanded | Log warning |
| Critical Zone | Max zone-error zone selected for log | Same SWT as without that selection; Floor log includes zone id/name | — |
| Demand success log | Demand path wrote (or would log success) | INFO includes Floor MUST: `e`, `u_pid`, `command`, Critical Zone when selected | — |
| Zero weight sum | All demand-zone weights ≤ 0 | Idle path: write `0` + clear | Log warning |

</frozen-after-approval>

## Code Map

- `apps/ha_smart_hvac/hvac_app.py` — `_gate_prelude`, `control_tick`, `control_event`, `_write_setpoint`: replace FF/CAP-7 demand command with PID law; drop outdoor from gate **and** from control listeners; advance integral only on `control_tick` (event may still write demand command); clear PID integral + last→`None` on idle/plant-off/fail; last-commanded skip plus keep plant-entity equal-float skip.
- `apps/ha_smart_hvac/models.py` / `config.py` — add `base_water_temp`, PID gains/clamps, zone `weight`; `control_interval` default **300**; keep weather/outdoor parse required until entry 3.
- `apps/ha_smart_hvac/pid.py` **(new)** — weighted demand averages, `e`, fixed PI step (`dt = control_interval`), saturation freeze + integral clamps, `round(clamp(base + u_pid), 1)`.
- `apps/ha_smart_hvac/coordinator.py` — reuse `has_heating_demand`; keep `select_max_error_demand_zone` for diagnostics/logging only (no SWT input).
- `apps/ha_smart_hvac/ff_auto_correct.py`, `feedforward.py` — leave files; stop calling them from the demand write path in this story.
- `apps.yaml.example` — commission `base_water_temp`, `pid` nest, zone `weight`, `control_interval: 300` with «starting defaults, not house-proven»; weather/outdoor keys may remain until entry 3 with «not a PID demand gate» comment.
- `tests/test_hvac_app.py` — rewrite demand/idle/plant-off/skip/critical-zone assertions for PID law; lock tick vs event integral; sat. freeze; partial-zone skip; outdoor missing still demands; outdoor not in listeners; demand INFO Floor fields; drop CAP-7 adapt expectations from the demand path.
- `tests/test_pid.py` **(new)** + `tests/test_config.py` — unit law + freeze + parse defaults; keep `test_coordinator.py` / `test_plant_management.py` with light tweaks.
- Do **not** change: Exclusive Session scripts; ADR/CONTEXT/AGENTS; delete FF modules (entry 3); force event clear-only / tick-only demand write (entry 2).

## Tasks & Acceptance

**Execution:**
- [ ] `apps/ha_smart_hvac/pid.py` -- add fixed-gain PI + weighted averages + sat. freeze + round/clamp helper -- isolates R1 math from AppDaemon
- [ ] `apps/ha_smart_hvac/models.py` + `config.py` -- parse `base_water_temp`, `pid` nest, zone `weight`, default `control_interval` 300 -- commissioning surface
- [ ] `apps/ha_smart_hvac/hvac_app.py` -- wire PID demand path, clear inventory, round/last-commanded skip; stop outdoor listener; Floor demand INFO; stop FfAutoCorrector for SWT; integral only on tick -- runtime tracer
- [ ] `apps.yaml.example` -- base/PID/weights/interval 300 + starting-defaults comment; weather/outdoor non-gating until entry 3 -- commission template
- [ ] `tests/test_pid.py` + `tests/test_hvac_app.py` + `tests/test_config.py` -- lock I/O matrix and ACs -- prove verify clause

**Acceptance Criteria:**
- Given Plant Management on and Heating Demand with valid weighted zone readings and unsaturated command, when `control_tick` runs, then SWT written is `round(clamp(base_water_temp + u_pid), 1)` where per-zone `Tset` is the max heating-thermostat setpoint and `Tair` is `zone_temp`, the integral advances by `e·dt` (then clamped), and Critical Zone selection does not change that SWT value.
- Given Plant Management on and Heating Demand, when `control_tick` runs with `raw = base+u_pid` outside `[setpoint_min, setpoint_max]` and `e` the same sign as that saturation, then the clamped/rounded SWT may be written and the integral does **not** advance via `e·dt`.
- Given Plant Management on and Heating Demand with valid weighted zone readings, when `control_event` runs, then SWT may be written as `round(clamp(base_water_temp + u_pid), 1)` and the integral does **not** advance.
- Given some configured zones fail air/setpoint reads and at least one valid demand snapshot remains, when the control path runs, then invalid zones are skipped (WARNING) and demand/PID use only successful snapshots.
- Given Plant Management on and no Heating Demand, when the control path runs, then SWT write `0` is attempted and integral + last commanded are cleared to `None` even if that write fails.
- Given Plant Management off, when the control path runs, then no SWT write occurs and integral + last commanded are cleared.
- Given the rounded command equals last commanded SWT, when the control path would write, then `number/set_value` is not called.
- Given the plant entity state already equals the value about to be written, when `_write_setpoint` runs, then `number/set_value` is not called (plant equal-float throttle).
- Given Plant Management on, Heating Demand otherwise valid, and outdoor unavailable, when the control path runs, then the demand PID path still runs (outdoor is not a gate).
- Given the App is initialized, when listeners are registered, then Outdoor Temperature is not among them.
- Given a demand success log line, when emitted, then it includes Floor MUST fields `e`, `u_pid`, `command`, and Critical Zone id/name when selected (prose free; no outdoor/u_ff as drivers).
- Given `apps.yaml.example` / omitted keys, when config is parsed, then base/PID/weights/interval 300 defaults apply and max Zone Error is not an SWT driver.

## Implementation Notes

## Plan Change Log

- 2026-11-07 party: Fork 1 **A** — interim AC/matrix: demand `control_event` may write rounded PID command; integral advances only on `control_tick` (not full R5/R6).
- 2026-11-07 party: Fork 2 **C** — drop Outdoor from control listeners in this story; weather/outdoor parse + FF package files may remain until entry 3; outdoor still not a demand gate.
- 2026-11-07 party: Fork 3 **A** — Boundaries + Design Notes: epic-1 runtime Done does not require CONTEXT/ADR green; live Exclusive Session until epic 2 = operator HITL note, not AC.
- 2026-11-07 party: **A1** — partial zones = status quo skip invalid snapshots + WARNING; demand/PID only over successful reads.
- 2026-11-07 party: **B1** — keep C4 numeric defaults; example/Design Notes mark starting commission, not house-proven.
- 2026-11-07 party: **C2** — saturation freeze: no `∫ += e·dt` on tick when raw outside SWT clamp and `e` same sign; still clamp ∫ when stepping.
- 2026-11-07 party: **D1** — demand success INFO Floor MUST `e`, `u_pid`, `command`, Critical Zone id/name; prose free; yaml comments for defaults + outdoor non-gate.
- 2026-11-07 review: **Tset** — per demand zone `Tair` = `zone_temp`, `Tset` = max heating-thermostat setpoint (same eligibility as Critical Zone) before zone-weight normalize.
- 2026-11-07 review: idle/fail clear integral + last→`None` even when write `0` fails; AC for plant equal-float skip.

## Review Triage Log

| finding | verdict | evidence | route |
|---------|---------|----------|-------|
| `apps.yaml.example` Ops line still says delete `ff_auto_correct_state.json` to restore yaml commission, but HvacApp no longer loads/saves that file | low | Confirmed: Ops comment remains at `apps.yaml.example` L29; `hvac_app.py` has no `_load_ff_overlay`/`_persist_ff_state`/`app_dir` usage. Stale ops guidance only — no runtime SWT impact. | patch |

## Design Notes

- **Interim event path (not full R5/R6):** Keep demand writes on both `control_tick` and `control_event` with the PID command; advance integral only on `control_tick` (mirrors CAP-8: event = command without CAP-7). Event may update SWT more often than the 300s tick; ∫ does not follow every event. Entry 2 removes demand writes from events (tick-only demand write + event clear-only).
- **Outdoor listener vs package:** This story stops registering Outdoor as a control listener. Entry 2 keeps it off and owns tick-only demand write. Entry 3 deletes outdoor/FF/CAP-7 from package + commissioning yaml. Until then, example keys may remain with an explicit non-gating note.
- **Done vs docs:** Automated verify (pytest/ruff) is enough for this tracer Done. Do not edit ADR/CONTEXT/AGENTS here (epic 2). Operator HITL between epic 1 and 2: do not commission live Exclusive Session until docs/ADR closed — not an AC.
- **Per-zone Tset/Tair:** Demand zone contributes `Tair = zone_temp` and `Tset = max(setpoint)` over thermostats with `hvac_action == "heating"` (same set as `zone_error` / Critical Zone). Then weight-normalize those scalars across demand zones → `Tair_w` / `Tset_w` → `e`.
- **Partial zones (A1):** Keep `_read_zones` behavior — zone missing air temp or all thermostats skipped entirely; Heating Demand and PID see only successful snapshots. Empty snapshots → idle. No incomplete-demand idle policy.
- **Clear vs write:** Idle/plant-off/fail always clear integral + last→`None`. Idle/no-zones still attempt write `0`; clear does not wait on write success.
- **Defaults (B1):** `40 / 1.0 / 0.1 / ±50 / 300` are epic C4 starting commission numbers; example yaml comments must say they are not house-proven; retune under operator HITL after epic 2 docs, not in this story.
- **Saturation freeze (C2):** On tick only, compute `u_pid` from current ∫, then `raw = base + u_pid`. If `(raw > setpoint_max and e > 0) or (raw < setpoint_min and e < 0)`, skip `∫ += e·dt`; still write `round(clamp(raw), 1)`. When not frozen, `∫ += e·dt` then clamp to `[integral_min, integral_max]`. Event path never advances ∫.
- **Yaml shape:** top-level `base_water_temp`; nest `pid: {kp, ki, integral_min, integral_max}`; optional per-zone `weight`.
- **Reuse:** `clamp` from `ff_auto_correct` or a tiny shared helper — prefer importing existing `clamp` to avoid duplicate math until entry 3 deletes FF.
- **Logging (D1):** Demand success INFO Floor MUST: `e`, `u_pid`, rounded `command`, Critical Zone id/name when selected. Prose free. Do not log outdoor/u_ff as if they drove SWT. Critical Zone still does not feed the command.
- **Skip layers:** (1) rounded == last commanded; (2) plant entity float equality in `_write_setpoint`. Idle clears last to `None` so the next demand write is not suppressed by a stale last; layer 2 still throttles repeat idle `0`.

## Verification

**Commands:**
- `uv run pytest` -- expected: all tests green
- `uv run ruff check apps tests` -- expected: clean

## Code Review

### 2026-11-07
**Code review complete.** 0 `decision-needed`, 8 `patch`, 1 `defer`, 10 rejected. (F1+F5 resolved → A → patch)

- [x] [Review][Patch] Demand-path integral advances only after successful write (decision A) [apps/ha_smart_hvac/hvac_app.py:120] — equal-rounded skip still advances ∫
- [x] [Review][Patch] Demand write-fail test pins ∫ unchanged and `_last_commanded is None` (decision A) [tests/test_hvac_app.py:481]
- [x] [Review][Patch] Non-finite zone readings can permanently NaN-poison PI state [apps/ha_smart_hvac/hvac_app.py:194]
- [x] [Review][Patch] Zone weight and PID integral bounds lack commission guards [apps/ha_smart_hvac/config.py:41]
- [x] [Review][Patch] Equal-rounded skip test does not assert tick integral advance [tests/test_hvac_app.py:410]
- [x] [Review][Patch] Happy-path tick ∫ assert is clamp-rail and misses control_interval→dt [tests/test_hvac_app.py:198]
- [x] [Review][Patch] select_max_error_demand_zone still documented as CAP-7 FF selector [apps/ha_smart_hvac/coordinator.py:19]
- [x] [Review][Patch] App-level partial-zone coverage omits thermostat-skip trigger [tests/test_hvac_app.py:341]
- [x] [Review][Defer] Plan Tasks checkboxes still open despite status built [story-tracer-fixed-gain-pid-swt-law-plan.md] — deferred: fix edits the plan/ticket artifact, not runtime code

#### Rejected
- R1 false — 0.0 is the correct cleared integral; AC “to None” over-applies the last-commanded arrow.
- R4 low — rarely visible; fix is plan-log edit with no runtime effect.
- R5 low — fix would edit plan intent/AC section.
- R7 false — name is the zone id in this model.
- R9 false — no reachable FfAutoCorrector call path remains to lock.
- R11 low — cosmetic docstring; rename adds little vs entry-3 CAP cleanup.
- R12 low — memlog/helper noise; cleaning adds churn without fixing SWT.
- R15 false — intentional two-layer skip per plan.
- R22 false — name fulfills Floor identity.
- R23 false — descriptive Rs vs Verify surface split; implementation matches interim Verify.
