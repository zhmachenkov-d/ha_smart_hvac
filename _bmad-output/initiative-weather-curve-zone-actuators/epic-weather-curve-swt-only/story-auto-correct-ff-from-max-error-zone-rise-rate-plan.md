---
title: 'Auto-correct FF from max-error zone rise rate'
type: 'feature'
ticket: '5'
created: '2026-10-19'
status: built
baseline_revision: 'd3c099bbd92be0daf4ec94cdec6bd1e6c75dbd15'
route: 'full'
route_source: 'auto'
review: 'quick'
review_source: 'pinned'
lenses_ran: ['quick']
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/initiative-weather-curve-zone-actuators/epic-weather-curve-swt-only/spike-ff-rise-rate-auto-correct-rule-decision.md'
  - '{project-root}/docs/adr/0004-weather-curve-swt.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** CAP-7 is documented (spike decision + ADR 0004) but not live — FF params stay at yaml commission and never adapt from the max-error demand zone’s air rise rate.

**Approach:** Implement the accepted spike contract so under Heating Demand the app selects that zone for rise-rate only, adapts `base`/`slope` (not `comfort_ref`), persists via B1 JSON only when params actually changed **and** SWT write succeeds, and keeps SWT as `clamp(u_ff)` with updated params — no air→SWT tracking.

## Boundaries & Constraints

**Always:**
- Encode `spike-ff-rise-rate-auto-correct-rule-decision.md` verbatim (Signal W15/1A+1B, Law I1/CS-base/N2+G25, Guards N-both+2B/2C/3A, Persistence B1). Do not invent thresholds, formulas, or persist shapes.
- Demand SWT stays `clamp(weather_feedforward)` from **current** in-memory params; selection feeds FF params only.
- Plant-on idle **or no demand** → write `0` + clear ephemeral; plant-off → no write + clear ephemeral; neither clears/rewrites `ff_auto_correct_state.json`.
- Yaml nest `weather_feedforward.auto_correct` (E2): `outdoor_gate_delta_k`, `r_expected_c_per_h`, `near_setpoint_eps_k`, `e_sat_c_per_h` (defaults 12 / 0.25 / 0.3 / 0.25); missing nest → defaults. Other scalars = code constants.
- Load: yaml FF → overlay `base`/`slope` from JSON if valid and in bounds; `comfort_ref` always yaml.
- CAP-5 keepers stay green: CAP-5(e) remains single-tick air≠additive (no adapt fixture); CAP-7 adapt≠additive covered separately.

**Never:**
- Air→SWT tracking / `u_track`; adapt `comfort_ref`; new HA entities; resurrect LADRC/ωc; invent law beyond the decision note; commit house entity IDs / touch gitignored `apps/apps.yaml`.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Happy adapt | Demand, same CZ, W15 full, steady≥15, \|error\|≥ε, \|e_r\|>δ, not W-skip, D-cmd ok | Nudge active knob; SWT post-nudge `clamp(u_ff)`; JSON iff params **changed and** write ok (2C) | No error expected |
| Incomplete W15 / near-ε / in-band δ / W-skip slope | Freeze path | No param mutate; append (1A) still runs on non-flush demand; I1 `previous` advances (3C); SWT prior params | No JSON |
| Warm outdoor, I1 on base (G1#6) | `(comfort_ref − T_out) ≤ 0`, I1 selects base, slow rise | Base nudge allowed; W-skip does not freeze base | No error expected |
| Zone switch / 4A absent / M2 non-finite / empty | Flush path | Flush window + clear_steady + clear ephemeral; no adapt | No JSON |
| Plant-off | PM off | No SWT write; clear ephemeral; JSON untouched | Log only |
| Plant-on idle / outdoor unavailable / no demand | Idle write `0` (outdoor/empty/no-demand); flush ephemeral on **all** these branches | JSON untouched | Warn as today |
| D-cmd at max/min | Raise@max or lower@min | No mutate; SWT prior; no JSON; relieving ok | No error expected |
| Bounds no-op (3A) | Δ then clamp leaves params equal | **No JSON**; SWT may still write unchanged command | No error expected |
| SWT write fail | Plant unreadable / write false | Keep in-memory nudge; **no** JSON; no rollback | Warn as today |
| Restart valid JSON | File in bounds | Yaml + overlay; ephemeral empty; first I1 evaluate = CS-base fill then hysteresis **same tick** (may select slope immediately) | No rewrite until next commit |
| Restart missing/corrupt/OOB JSON | Bad/absent file | Yaml only; warn; no rewrite until next commit | Warn |

</frozen-after-approval>

## Code Map

- `apps/ha_smart_hvac/coordinator.py` — Pure `select_max_error_demand_zone(zones, previous_name: str | None) -> ZoneSnapshot | None` (T-hold while previous still in max-error tie set among demand zones; else max `zone_error`, lex `name` on ties). Keep `has_heating_demand`.
- `apps/ha_smart_hvac/models.py` — Add frozen `AutoCorrectConfig` (E2 knobs) on commission config; keep frozen `WeatherFeedforwardConfig` for yaml. **Do not** mutate commission dataclasses.
- `apps/ha_smart_hvac/config.py` — Parse optional `weather_feedforward.auto_correct` nest → defaults when missing.
- **Create** `apps/ha_smart_hvac/ff_auto_correct.py` — Ephemeral state + rise-rate window, I1/CS-base, N2+G25, N-both guards, B1 load/save `ff_auto_correct_state.json` under `app_dir`. Pure logic (no `Hass`); unit-testable.
- `apps/ha_smart_hvac/hvac_app.py` — Own mutable runtime `base`/`slope` (yaml/`comfort_ref` from config). `initialize`: load YAML+JSON overlay into runtime + empty ephemeral. `control_tick` flush/clear ephemeral on: plant-off (`_hands_off` today logs only — wire clear), outdoor-unavailable, empty snapshots, **no-demand**, idle. Demand: select(previous) → **append W15 before freeze early-returns** → steady → I1 → Δ → D-cmd on **pre-nudge** `clamp(u_ff)` → if allowed apply runtime mutate → SWT post-nudge → JSON only if params changed **and** write ok. Reuse `_write_setpoint` for 2C.
- `apps/ha_smart_hvac/feedforward.py` — Keep law; each call builds a throwaway `WeatherFeedforwardConfig(runtime_base, runtime_slope, yaml_comfort_ref)` (or equivalent) — never mutate stored commission config.
- `apps.yaml.example` — Document optional `auto_correct` nest; comment: omit nest = E2 defaults (auto-correct always on); ops delete `ff_auto_correct_state.json` to restore yaml commission.
- `tests/test_coordinator.py` — Selector + T-hold / lex / demand-pool only.
- `tests/test_ff_auto_correct.py` — Pure: W15/1A append-on-freeze, I1/CS-base+hysteresis same-tick, N2+G25 / G1#1–6 signs, guards, B1 load/corrupt/OOB, bounds no-op.
- `tests/test_hvac_app.py` — Hass: plant-off/idle/no-demand flush (JSON untouched), 2C write-fail, D-cmd, demand SWT = clamp(runtime); keep CAP-5 a–e **unchanged** (CAP-5(e) single-tick no-adapt); separate CAP-7 tick test that adapt≠additive air term.
- `tests/test_config.py` — Missing nest → defaults; valid nest overrides.
- Out of scope: ADR/CONTEXT/AGENTS (1.3 done), house `apps/apps.yaml`, `knowledge/`.

## Tasks & Acceptance

**Execution:**
- [ ] `apps/ha_smart_hvac/models.py` + `config.py` — E2 `AutoCorrectConfig` nest + defaults -- commission surface
- [ ] `apps/ha_smart_hvac/coordinator.py` — `select_max_error_demand_zone(zones, previous_name)` T-hold/lex -- CAP-7 signal
- [ ] `apps/ha_smart_hvac/ff_auto_correct.py` — Window/I1/nudge/guards/B1 JSON (pure) -- decision law
- [ ] `apps/ha_smart_hvac/hvac_app.py` + `feedforward.py` — Runtime base/slope + throwaway FF config; plant-off/no-demand flush; append-before-freeze; 2C -- runtime
- [ ] `apps.yaml.example` — `auto_correct` nest + omit=defaults / delete-JSON restore comment -- ops
- [ ] `tests/test_ff_auto_correct.py` — Pure matrix/G1 (incl. G1#6) + B1 load/corrupt -- law
- [ ] `tests/test_hvac_app.py` + `test_coordinator.py` + `test_config.py` — Flush/2C/D-cmd/CAP-7 tick; CAP-5 keepers untouched; selector; nest parse -- green

**Acceptance Criteria:**
- Given sustained demand with full W15 and guards open, when ticks run, then FF `base`/`slope` move with rise-rate and SWT equals `clamp(u_ff)` from post-nudge params (no additive air term).
- Given CAP-5(e) multi-zone setup on a **single tick** with no adapt window, when max-error zone air changes without changing outdoor/runtime FF, then SWT is unchanged — never `u_ff + f(air)`.
- Given a CAP-7 adapt tick, when params nudge from rise-rate, then SWT still equals `clamp(u_ff)` from post-nudge params only (air not an additive term).
- Given plant-off, idle, or no-demand, when tick runs, then ephemeral cleared and `ff_auto_correct_state.json` neither deleted nor rewritten.
- Given D-cmd block, bounds no-op, or SWT write fail, when adapt would otherwise nudge, then JSON is not written (2C/3A); on bounds no-op SWT may still write the unchanged command.
- Given restart with valid JSON, when app initializes then first I1 evaluate runs, then `base`/`slope` overlay yaml, ephemeral starts empty, and CS-base fill then hysteresis run **same tick** (slope allowed immediately when `d ≥ gate+hyst`).
- Given missing `auto_correct` nest, when `parse_config` runs, then E2 defaults apply.
- Given warm outdoor with I1 on base and slow rise, when adapt runs, then base may nudge (G1#6); with I1 on slope, adapt skips.
- Given the suite, when `uv run pytest` and ruff check/format run, then they pass.

## Implementation Notes

## Plan Change Log

- 2026-10-19 plan review patch-all: runtime base/slope + throwaway FF config; CS-base→hysteresis same-tick on restart; 3A SWT-ok/JSON-no in Design Notes; no-demand flush explicit; CAP-5(e) vs CAP-7 ACs split; G1#6 matrix/AC; JSON = changed∧write-ok; selector signature; pure vs Hass test split.

## Review Triage Log

| finding | verdict | route | evidence |
|---------|---------|-------|----------|
| `_load_ff_overlay` silent on missing JSON | medium | patch | Spike Load §3 + matrix: missing → yaml only **and warn**. Code warns only when `path.exists()`; absent file returns None with no WARNING. Verified in `hvac_app.py`. |
| `e_sat_c_per_h: 0` → ZeroDivisionError on adapt | medium | patch | `_parse_auto_correct` accepts `0.0`; `process_demand` divides by `e_sat` after W15/I1 advance. Repro with `AutoCorrectConfig(e_sat_c_per_h=0)`. |
| OOB yaml `base`/`slope` reverse-snap on first clamp | low | reject | Real if commission is OOB, but everyday yaml (`apps.yaml.example` 25/1.2) is in bounds; fix needs clamp-vs-reject design beyond a direct patch. |
| party-mode `.memlog.md` in diff | false | reject | Pre-existing dirty tree from party mode; not CAP-7 runtime; not introduced as part of story Code Map. |

## Design Notes

Same-tick demand order: select(previous) → **append W15 before freeze early-returns** → steady → I1 (CS-base then hysteresis same tick) → if not frozen compute Δ → D-cmd vs **pre-nudge** `clamp(u_ff)` → if blocked: no mutate, SWT prior, no JSON → if allowed: apply post-bounds mutate when params **changed**; **always** write SWT from current (post-nudge or unchanged) `clamp(u_ff)`; JSON **only** when params changed **and** write succeeded (3A: SWT ok, no JSON). Flush paths skip append.

Runtime pattern: mutable `base`/`slope` on app/corrector state; commission `WeatherFeedforwardConfig` stays frozen; FF calls use throwaway config with yaml `comfort_ref`.

## Verification

**Commands:**
- `uv run pytest` -- expected: pass
- `uv run ruff check apps/ha_smart_hvac tests` && `uv run ruff format --check apps/ha_smart_hvac tests` -- expected: clean
