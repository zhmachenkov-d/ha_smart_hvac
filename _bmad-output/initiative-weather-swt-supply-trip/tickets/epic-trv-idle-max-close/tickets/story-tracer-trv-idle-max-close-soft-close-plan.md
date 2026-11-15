---
title: 'Tracer: TRV idle max-close soft-close'
type: 'feature'
ticket: '1'
created: '2026-11-15'
status: 'built'
baseline_revision: '9c7bc3697a9fa155bea1ee7c60bd1ef26a17d201'
route: 'full'
route_source: 'auto'
risk: 'high'
review: 'thorough'
review_source: 'auto'
lenses_ran: ['blind-hunter', 'edge-case-hunter', 'verification-gap', 'intent-alignment']
review_loop_iteration: 0
context:
  - '{project-root}/CONTEXT.md'
  - '{project-root}/AGENTS.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent
**Problem:** Commissioned Sonoff TRVs have no AppDaemon idle max-close, so residual valve flow still cycles the boiler even when weather-curve SWT is correct.

**Approach:** Add yaml `valve_closure_floor` (default 80) and per-TRV closure+accuracy wiring; Plant on writes only `valve_closure_degree` as idle max-close **limit** (floor or 100 with overshoot hysteresis); Plant off writes 100 on all commissioned Sonoff TRVs; never `valve_opening_degree`. Example yaml only — house ids are story 4.2.

## Boundaries & Constraints
**Always:**
- Write only `valve_closure_degree` via a shared equal-float number helper (not `_write_setpoint`); closure = idle max-close **limit**, including under Heating Demand.
- Plant on: unlatched overshoot → 100; else floor when `T_zone ≤ setpoint` or unlatched non-overshoot; latched stays 100 until `T_zone ≤ setpoint`. Runs with or without Heating Demand / Outdoor.
- Every `control_tick` / `control_event` (and init first tick) runs `_apply_trv_law()` **before** water `_gate_prelude`; TRV reads come from commissioned config, not prelude snapshots. `T_zone` = zone yaml `temperature`; overshoot/clear setpoint = that mapping's climate `temperature` attribute.
- Plant off: `_apply_trv_law` writes 100 on every commissioned Sonoff TRV; `_hands_off` stays no-SWT + clear trip.
- `ThermostatConfig(climate, valve_closure=None, accuracy=None)`; plain string → climate-only; mapping needs both TRV fields as non-empty entity-id strings; commissioned iff both set. Call sites use `.climate`.
- Latch keyed by `valve_closure` entity id; set/clear only after helper True. Critical Zone never drives TRV or SWT.

**Never:**
- Write `valve_opening_degree`; infer TRV by name; reuse `_write_setpoint` for TRV; treat closure as position or skip floor under demand.
- Change weather-curve SWT, supply-trip, Exclusive Session, or Heating Demand; edit house `apps.yaml` (4.2) or ADR/`knowledge/` (epic 6).
- Hook TRV to Critical Zone, `supply_event`, or flame; use zone max/CZ/climate current/TRV local temp; apply TRV only after prelude success.

**Decisions:**
- Yaml: `thermostats[]` is climate string or `{climate, valve_closure, accuracy}`; top-level `valve_closure_floor` optional default 80 on `HvacConfig` + `_KNOWN_KEYS`.
- Scope cut: accuracy-only re-apply, prelude-isolation edge ACs, and expanded goldens → deferred-work (not this tracer).

## I/O & Edge-Case Matrix
| Scenario | Input / State | Expected Output / Behavior | Error Handling |
| --- | --- | --- | --- |
| At/below setpoint | Plant on; `T_zone ≤ setpoint` | Write floor; clear latch only if helper True | Skip unreadable: no latch mutate |
| Overshoot | Plant on; `T_zone > setpoint + accuracy` | Write 100; latch only if helper True | Skip unreadable: no latch mutate |
| Dead-band after overshoot | Latched; `setpoint < T ≤ setpoint+accuracy` | Keep 100 | No error expected |
| Clear | Latched; `T_zone ≤ setpoint` | Write floor; clear latch only if helper True | Skip unreadable: latch stays |
| Plant off | Plant not `on` | Write 100 all commissioned; no SWT `set_value` | Skip unreadable closure |
| Generic thermostat | Plain-string climate only | No TRV write | No error expected |
| Equal float | Number already equals command | Skip `set_value` | No error expected |

</frozen-after-approval>

## Code Map
- `models.py` / `config.py` — `ThermostatConfig`; floor on `HvacConfig`+`_KNOWN_KEYS`; string|map; reject partial/non-string TRV fields.
- `hvac_app.py` — `.climate` listeners/`_read_zones`; `_apply_trv_law` before prelude; TRV helper; latch by `valve_closure` id; `_hands_off` no-SWT.
- `coordinator.py` / `feedforward.py` — do not change.
- `apps.yaml.example` — floor + mapping TRV + plain-string neighbor.
- `tests/test_config.py` / `test_hvac_app.py` — floor default/override; partial→`ConfigError`; hysteresis; plant-off by entity_id; never opening.

## Tasks & Acceptance
**Execution:**
- [ ] `models.py` + `config.py` — `ThermostatConfig` + floor + string|map validate.
- [ ] `hvac_app.py` — `.climate` call sites; `_apply_trv_law` before prelude; helper + latch; plant-on/off writes.
- [ ] `apps.yaml.example` — floor + mapping + plain-string placeholder.
- [ ] `tests/test_config.py` + `tests/test_hvac_app.py` — matrix above; assert writes by `entity_id`.

**Acceptance Criteria:**
- Given Plant on and a commissioned TRV, when `T_zone > setpoint + accuracy`, then closure 100 and latch (by `valve_closure` id) only after helper True; when later `T_zone ≤ setpoint`, then floor and clear only after helper True — independent of Heating Demand.
- Given Plant off, when tick/event runs, then every commissioned closure entity is 100 and `plant_setpoint` gets no `set_value`.
- Given only plain-string thermostats, when app runs, then no TRV closure `set_value` calls.
- Given any run, when inspecting services, then no `valve_opening_degree` write; TRV writes never go through `_write_setpoint`.
- Given `apps.yaml.example`, when parsed, then floor and per-TRV closure/accuracy keys are present with a plain-string thermostat.
- Given yaml that omits `valve_closure_floor`, when parsed, then floor is 80; given `85`, floor is 85 and key not in `ignored_keys`.
- Given a thermostat mapping missing/empty/non-string TRV fields, when parsed, then `ConfigError`.

## Implementation Notes
## Plan Change Log
- 2026-11-15 token split → deferred-work (accuracy re-apply; prelude-isolation ACs; expanded goldens); kept review locks (`ThermostatConfig`, latch id, entity asserts).
## Review Triage Log
| lens | finding | verdict | route | evidence |
| --- | --- | --- | --- | --- |
| blind-hunter | tickets.toml must-fix vs deferred-work disagree | false | reject | Intent Decisions explicitly cut those ACs to deferred-work; notes drift is planning hygiene, not a code defect in this change. |
| blind-hunter | no Outdoor-fail / failed-prelude TRV write test | false | reject | Frozen Intent Decisions defer prelude-isolation edge ACs; Always still requires before-prelude TRV, but that proof is intentionally out of this tracer. |
| blind-hunter | no multi-TRV / mixed-list closure assertion | false | reject | Intent Decisions defer expanded multi-TRV / mixed goldens. |
| blind-hunter | no cold-start overshoot golden | false | reject | Intent Decisions defer expanded cold-start goldens. |
| blind-hunter | plant-off leaves overshoot latch uncleared | false | reject | Verified `hvac_app.py` plant-off path writes 100 then continue; on plant return, dead-band keep-100 / clear at T≤setpoint still matches Always hysteresis — clearing on plant-off is not required by Intent. |
| blind-hunter | accuracy entity never listen_state’d | false | reject | Intent Decisions / deferred-work exclude accuracy-only re-apply from this tracer; Approach wiring is config+read (intent-alignment reading B). |
| blind-hunter | valve_closure_floor unbounded finite float | medium | patch | Verified `config.py` `_number` only; no 0–100 check. Out-of-range floor would be written to TRV. |
| blind-hunter | `_write_number` docstring says confirmed without readback | low | reject | Same post-`call_service` True pattern as plant `_write_setpoint`; cosmetic docstring, no distinct bad outcome. |
| blind-hunter | missing unreadable zone/setpoint/failed-write latch twins | low | reject | Zone/setpoint share the same pre-write `continue` already covered by accuracy-unavailable test; closure-False latch case is the separate verification-gap finding below. |
| blind-hunter | opening-degree test only greps source | low | reject | Runtime service asserts already filter by `entity_id` / spy `_write_number` vs `_write_setpoint`; grep is redundant belt. |
| blind-hunter | no test that supply_event / trip-hold skip TRV law | low | reject | Code paths never call `_apply_trv_law` from supply/trip; everyday miss unlikely; Intent Never already recorded. |
| blind-hunter | plan Execution still unchecked / memlog draft | false | reject | Fix would be editing this plan/process state, which triage forbids as a finding fix. |
| blind-hunter | thermostat mapping silently ignores unknown keys | low | reject | With required TRV fields present, extra keys do not change commissioned behavior; everyday harm unlikely. |
| blind-hunter | example yaml omits “limit not position” comment | low | reject | Cosmetic operator docs; Intent already locks the semantics in Always/Never. |
| edge-case-hunter | floor outside 0..100 | medium | patch | Same root as unbounded floor — verified no range guard at parse. |
| edge-case-hunter | negative accuracy widens overshoot | low | reject | Sonoff accuracy entity negative is not an everyday case; reject per low+unlikely. |
| edge-case-hunter | whitespace-only TRV entity id commissions | medium | defer | Pre-existing `_entity_id` accepts non-empty whitespace for all entity fields; not introduced uniquely by TRV logic. |
| edge-case-hunter | duplicate valve_closure ids share latch | low | reject | Unlikely commissioning; no other entity uniqueness checks in parse either. |
| edge-case-hunter | accuracy state change alone skips law | false | reject | Same as accuracy listen defer — Intent excludes it. |
| edge-case-hunter | setpoint+accuracy overflows to inf | low | reject | Extreme float pair not everyday; reject. |
| edge-case-hunter | plant-off skip when closure unreadable | false | reject | Matches matrix Error Handling “Skip unreadable closure”; not a defect. |
| verification-gap | latch set/clear ignores `_write_number` False (unreadable closure) | medium | patch | Pre-verified gap: code gates latch on helper True, but no test uses `closure` unavailable; removing guards would still pass suite. |
| verification-gap | equal-float True clear-latch path untested | medium | patch | Pre-verified gap: clear with closure already at floor returns True without set_value and must discard latch; untested. |
| verification-gap | commissioned TRV initialize never asserts `.climate` listeners | medium | patch | Pre-verified gap: listeners use `thermo.climate`; no initialize assert with mapping thermostats. |
| intent-alignment | descriptive readings only | false | reject | Auditor reports reading B implemented; no actionable defect claim. |
## Design Notes
Before-prelude `_apply_trv_law` stays (deferred ACs only postpone extra proofs). Golden: T≤sp→80; overshoot→100 latch; dead-band keep; clear→80; plant off→100 all.

## Verification
**Commands:**
- `uv run pytest` -- expected: pass
- `uv run ruff check apps/ha_smart_hvac tests` -- expected: clean

## Code Review

### 2026-11-15 (walkthrough Formal review — Config slice)
**Code review complete.** 0 `decision-needed`, 2 `patch`, 1 `defer`, 9 rejected.

- [x] [Review][Patch] Missing ConfigError tests for non-mapping thermostat items and bad climate with TRV keys [tests/test_config.py:527 / apps/ha_smart_hvac/config.py:128]
- [x] [Review][Patch] Inclusive valve_closure_floor bounds 0 and 100 not acceptance-tested [tests/test_config.py:499 / apps/ha_smart_hvac/config.py:259]
- [x] [Review][Defer] Whitespace-only entity ids pass `_entity_id` [apps/ha_smart_hvac/config.py:_entity_id] — deferred: pre-existing helper; already in deferred-work for this plan

Rejected: R1/R10 unknown mapping keys (low — required keys still enforced); R2 house-calibration lag (false — epic 6); R3 dual default 80 (low hygiene); R6/R11 empty commissioned (false — parse rejects empty); R7 example absent from scoped diff (false — scope artifact); R8 label wording (low cosmetic); R15 intent descriptive only (false — R1 aligned).

### 2026-11-15 (walkthrough Formal review — `_apply_trv_law` slice)
**Code review complete.** 0 `decision-needed`, 2 `patch`, 0 `defer`, 11 rejected.

- [x] [Review][Patch] Latched hysteresis incorrectly gated on accuracy readability [apps/ha_smart_hvac/hvac_app.py:401]
- [x] [Review][Patch] Missing boundary and unreadable-input TRV tests [tests/test_hvac_app.py]

Rejected: R3 silent skip log (low); R4 use .commissioned (low); R6 mixed-list (deferred/false for tracer); R7 docstring (low); R8 latch logs (low); R9 plant-off latch clear (false); R11 opening service shape (low); R13 negative accuracy (low, prior reject); R17 intent descriptive (false).
