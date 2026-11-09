---
title: 'Tracer: initialize first tick and demand-edge SWT write'
type: 'feature'
ticket: '1'
created: '2026-11-09'
status: 'built'
baseline_revision: '3e56f8dc761cac18489587c70fcb80aac75a23f5'
route: 'full'
route_source: 'auto'
risk: 'high'
review: 'thorough'
review_source: 'auto'
lenses_ran: ['blind-hunter', 'edge-case-hunter', 'verification-gap', 'intent-alignment']
review_loop_iteration: 0
context:
  - /workspaces/ha-smart-hvac/AGENTS.md
  - /workspaces/ha-smart-hvac/docs/adr/0005-fixed-pid-swt.md
  - /workspaces/ha-smart-hvac/docs/adr/0006-optional-rls-adaptive-pid.md
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** After App reload or entry into gated Heating Demand the plant can wait up to a full `control_interval` before the first demand SWT command; mid-demand events correctly stay quiet, but there is no rising-edge write and `initialize` never runs a tick.

**Approach:** Run one full `control_tick` at the end of successful `initialize`. On rising-edge into gated demand (Plant on ∧ Heating Demand) from `control_event`, write demand SWT with current gains without advancing ∫ and without stepping RLS; keep mid-demand zone/setpoint events as no-ops and leave idle / plant-off / fail clears unchanged.

## Boundaries & Constraints

**Always:**
- Gated demand = Plant Management on **and** Heating Demand (D28), including plant-on while zones already demand.
- Full initialize tick may write + advance ∫ (+ RLS per ADR 0006 when adaptive).
- Demand-edge write uses current gains only; no ∫ advance; no RLS step (D29); no `_maybe_persist_rls` on edge; do not reset `control_interval` (D30).
- Sticky `_gated_demand`: True only after a successful **demand-path** write in `_run_demand` / `_run_demand_edge` (`_write_setpoint` True, incl. equal-float). Idle `0` via `_go_idle` never sets latch; `_go_idle`, prelude `None`, and R7-skip leave/set latch False so a later event can retry the edge.
- Keep `run_every(..., "now", interval)` — AppDaemon `"now"` already means first periodic fire at now+interval; lag is fixed by the explicit initialize tick, not by changing start.
- Weights-unusable on the edge path: write `0` + clear ∫ (same fail as tick); latch False.
- Clamp via existing `setpoint_min` / `setpoint_max` only; stay inside `ha_smart_hvac`.

**Never:**
- Docs (`AGENTS.md`, ADR 0005/0006, `CONTEXT.md`, `knowledge/`) — story 4.2.
- Change PID law form, Heating Demand definition, Exclusive Session, or RLS JSON / latch semantics beyond forbidding RLS step (and persist) on edge.
- Replace `run_every` start `"now"` with a numeric start delay (invalid/fragile vs AD API; `"now"` is not immediate).
- Write or advance ∫ on mid-demand zone air / setpoint events.
- Debounce listeners or merge tick/event into one public entrypoint.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Init under gated demand | `initialize` with plant on + heating | One full tick: demand SWT write + ∫ advance; RLS steps only if adaptive priors allow; `run_every` still start `"now"` | Config error: no schedule, no tick |
| Init not gated | plant off or idle | First tick takes existing prelude clear / hands-off; ∫ cleared as today | — |
| Idle → gated demand event | was not gated; prelude returns zones | Demand SWT write; ∫ unchanged; RLS step count unchanged; `last_u` updated on write True; no persist; latch True on write True | Weights-unusable → write 0 + clear ∫; latch False |
| Plant-off → on with demand | was not gated; zones already heating | Same edge write (no ∫ / no RLS step / no persist) | — |
| Mid-demand zone/setpoint event | latch already True | No write; ∫ unchanged; no RLS step | — |
| Idle / plant-off / no-zones event | gate fail | Existing clear / hands-off; latch gated=false | — |
| Edge plant unreadable | rising edge; plant NaN/unavailable | Skip write; ∫ unchanged; `last_u` unchanged; **latch stays False** (retry on later event) | Same as tick R7 skip |
| Tick weights-unusable while previously gated | latch was True; demand zones but weight sum unusable | Write `0` + clear ∫ via `_go_idle`; **latch False** (idle write must not latch) | Same as edge weights-unusable |
| Periodic tick after edge | next `control_tick` | Full demand path (∫ + optional RLS + persist); timer not restarted by edge | — |

</frozen-after-approval>

## Code Map

- `apps/ha_smart_hvac/hvac_app.py` — `initialize` (~43–78): keep `run_every(..., "now", interval)`; after listeners + schedule, call one explicit `control_tick({})`. Seed `_gated_demand = False` with other ephemeral state. Config-error early return: no schedule, no tick (existing). `_gate_prelude` (~204–222) / `control_tick` (~224–228) / `control_event` (~230–240): replace bare `_gate_prelude()` with `zones = self._gate_prelude()`; on `None` set latch False and return; on zones + latch False call thin `_run_demand_edge(zones) -> bool` (no ∫ assign / no `_maybe_rls_step` / no `_maybe_persist_rls`); latch True only when that returns True. Tick keeps `_run_demand` (~332–369); latch True only on demand-path `_write_setpoint` True (never on `_go_idle` idle `0`). Set latch False in `_go_idle`, on prelude `None`, and on R7-skip. Reuse `_gains_for_demand`, `evaluate_demand`, `_write_setpoint`, `_log_demand_success`. Do not change Exclusive Session, Heating Demand via `hvac_action`, or RLS load/persist helpers beyond skipping them on edge.
- `apps/ha_smart_hvac/pid.py` — `evaluate_demand` (~83–106): pure; command uses pre-step ∫; caller owns apply (tick assigns after write True). Edge may call and **must not** assign returned ∫. Update docstring (today wrongly says every call advances ∫ / events must never call). No API split / no `advance_integral` flag. Do not change PI math or saturation freeze.
- `apps/ha_smart_hvac/rls.py` — do not call from edge; tick `_maybe_rls_step` / `_maybe_persist_rls` unchanged.
- `tests/test_hvac_app.py` — `_tick_app` (~78–124) must seed `_gated_demand=True` so existing mid-demand no-ops stay no-ops (`test_demand_event_no_write_*`, `test_tick_then_demand_event_leaves_integral`, `test_adaptive_control_event_no_rls_no_write`). Extend `_init_app` (~171–183) with Hass stubs (`get_state` / `call_service`; default **plant-off** so prelude hands-off, ∫=0, no write) and audit every `_init_app().initialize()` caller for gated overrides. Keep/strengthen `test_initialize_schedules_control_tick` to assert full `run_every(control_tick, "now", interval)`. Add **new** rising-edge tests with latch False (idle→edge, plant-on-with-demand); plus init demand tick, mid-demand no-op, edge/tick weights-unusable → latch False, edge no-RLS / ∫ frozen / no persist, edge R7-skip latch False. Keep idle/plant-off/no-zones event clears.

## Tasks & Acceptance

**Execution:**
- [x] `apps/ha_smart_hvac/hvac_app.py` — Add sticky `_gated_demand`; initialize keeps `run_every(..., "now", interval)` then runs one `control_tick`; add `_run_demand_edge` sibling; `control_event` uses `zones = self._gate_prelude()` then rising-edge via sibling when latch False; weights-unusable / `_go_idle` / prelude None / R7 → latch False; latch True only on demand-path write success (never idle `0`).
- [x] `apps/ha_smart_hvac/pid.py` — Adjust `evaluate_demand` docstring so edge reuse is explicit without changing the PI math (no new flag).
- [x] `tests/test_hvac_app.py` — Seed `_tick_app` latch True for mid-demand; `_init_app` default plant-off Hass stubs + audit init callers; new rising-edge tests (latch False); lock I/O matrix (init tick, edge write, mid-demand no-op, clears, weights-unusable latch False, no RLS/persist on edge, R7-skip latch False, `run_every(control_tick, "now", interval)`).

**Acceptance Criteria:**
- Given plant on + Heating Demand at initialize, when `initialize` completes, then one demand SWT write occurred, ∫ advanced once when plant readable, and `run_every` is still armed with start `"now"` and the configured interval.
- Given transition into gated demand via `control_event`, when the rising edge is processed and the plant write succeeds, then demand SWT is written (or equal-float skipped), ∫ is unchanged, RLS is not stepped, `last_u` matches the command, RLS JSON is not persisted by the edge, and `_gated_demand` is True.
- Given already gated demand (`_gated_demand` True), when a zone air or setpoint `control_event` fires, then no demand write and ∫ unchanged.
- Given weights-unusable on that rising edge or on a demand tick, when the fail path runs, then plant gets `0`, ∫ is cleared, and latch is False (idle write must not latch).
- Given edge plant unreadable (R7), when the edge path runs, then no write, ∫ and `last_u` unchanged, and latch stays False so a later event may retry.
- Given idle or plant-off events, when gates fail, then existing clear / hands-off behavior still holds and latch is False.

## Implementation Notes

## Plan Change Log

- 2026-11-09 — Party pressure-test locks: **B** sticky `_gated_demand` (True only on `_write_setpoint` True; R7-skip retries); **A** edge `last_u` mirrors tick on write True, no `_maybe_persist_rls` on edge; **N** keep `run_every` start `"now"` + explicit init `control_tick` (AD `"now"` = now+interval; drop numeric start delay); **S** thin `_run_demand_edge` sibling (not `edge=` flag). Frozen Always/Never/matrix, Code Map, Tasks, AC, Design Notes aligned.
- 2026-11-09 — Plan review: latch True only on demand-path success (not `_go_idle` idle `0`); matrix row tick weights-unusable → latch False; `_init_app` default plant-off + audit init callers; `control_event` captures prelude zones; new rising-edge tests with latch False; assert full `run_every(..., "now", interval)`.

## Review Triage Log

- false — BH: latch clear only in tick/event callers of prelude — only `control_tick`/`control_event` call `_gate_prelude` and both set latch False on None; speculative future caller is not a present defect.
- false — BH: `_run_demand` / `_run_demand_edge` pipeline duplication — intentional thin sibling (plan lock S); not a defect.
- medium → defer — BH: AGENTS.md / CONTEXT.md still say tick-only demand SWT — real after this change; Intent Never + story 4.2 owns docs; fix edits agent-context.
- medium → patch — BH: no init-under-demand + plant-unreadable (R7) test — latch must stay False so post-init events can edge-retry; uncovered sticky-open path.
- medium → patch — BH: no tick R7-fail then later `control_event` edge-retry test — party lock B sticky-open; `test_demand_fail_write_aborts` omits latch/follow-up event.
- low → reject — BH: `test_rising_edge_plant_on_with_demand_writes` does not drive plant-mgmt transition — production path covered by latch False + plant on; docstring overclaim only.
- low → reject — BH: `test_tick_after_edge_advances_integral` omits tick write assert — ∫ advance is the contract under test; everyday risk low.
- low → reject — BH: init plant-on + idle not gated uncovered — plant-off init + event-idle latch clears cover the not-gated / clear behaviors for everyday use.
- low → reject — BH: `_gated_demand` lacks field comment — cosmetic naming note.
- false — BH: edge calls `evaluate_demand` which returns stepped ∫ — pure helper by design; docstring updated; edge must not assign (already true).
- low → reject — BH: duplicated `_init_app` / `_init_gated_get_state` entity matrix — hygiene only.
- false — BH: plan Tasks unchecked / triage empty / memlog draft — fix would edit this plan artifact; rejected.
- medium → patch — VG: `test_plant_off_no_write_clears` never asserts `_gated_demand` False — tick plant-off uses `_hands_off` (not `_go_idle`); deleting the tick None unlatch leaves latch True and skips later edge; sibling event test already asserts.
- medium → patch — VG: rising-edge never checks adapted/current gains via `_gains_for_demand` — replacing with yaml `kp`/`ki` still passes all edge tests; first edge command can disagree with adapted tick path.
- false — IA: R4 “clears unchanged” vs latch clears on idle/plant-off — Approach means plant/∫ clear semantics; latch bookkeeping is required for sticky rising-edge (R2).

## Design Notes

**Gated latch (sticky / B):** Persist `_gated_demand` across tick/event. Prelude `None` → False. Prelude zones + latch was False + `control_event` → run `_run_demand_edge`; latch True **only** if it returns True (demand-path write succeeded, incl. equal-float). `_go_idle` (idle `0`, incl. weights-unusable) must set latch False — never treat idle `_write_setpoint(0)` as gated success. R7-skip → latch stays False (later events retry edge; may WARN while plant is down). Tick: full `_run_demand`; latch True only on demand-path write success (same sticky gate). Do not infer edge only from `entity`/`old`/`new` (listeners still re-read Hass); latch is what makes plant-on-while-already-demand an edge.

**Edge write (A + S):** Thin `_run_demand_edge(zones) -> bool` — same command path pieces as tick (`_gains_for_demand`, `evaluate_demand`, `_write_setpoint`) but no `_maybe_rls_step`, do not assign `self._integral`, and do **not** call `_maybe_persist_rls`. On write True (incl. equal-float), set `_rls.last_u` to the command (RAM prior for the next tick) and return True; never update `last_u` on idle `0`. Leave `_run_demand` tick path unchanged for RLS / ∫ / persist.

**Initialize vs `run_every` (N):** After `run_every(self.control_tick, "now", control_interval)`, call explicit `control_tick({})`. Do **not** replace `"now"` with a numeric start: AppDaemon documents `"now"` as first trigger at now+interval (not immediate); `"immediate"` would fire ASAP. Numeric `start` is outside the documented str|time|datetime|None types. Explicit init tick removes the comfort lag; `"now"` already prevents a back-to-back scheduled double-step with that explicit tick.

## Verification

**Commands:**
- `uv run pytest` -- expected: all tests pass
- `uv run ruff check apps/ha_smart_hvac tests` -- expected: clean
