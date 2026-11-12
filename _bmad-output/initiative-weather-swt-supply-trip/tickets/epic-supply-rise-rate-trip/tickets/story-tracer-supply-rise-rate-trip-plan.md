<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent
**Problem:** Weather-curve demand SWT (CAP-8) has no supply rise-rate protection; `boiler_water` is still an ignored leftover key, and there is no latch that forces SWT `0` when supply rises too fast.

**Approach:** Commission top-level `boiler_water` / `r_max` (default 2) / `hold` (default 900); listen on supply; under Plant∧Demand compute `r_obs` (°C/min) from two successive valid samples; if `r_obs > r_max` latch and write SWT `0`; while latched `_run_demand` commands `0` (no weather curve, equal-float skip); hold via AppDaemon `run_in` from **first** latch moment (re-trip does not restart the timer); clear latch + cancel hold + wipe samples on hold expiry / idle write-`0` / plant-off; hold expiry under still-gated demand re-runs `_run_demand` with the weather curve. Zone rising-edge clear is entry 2; house accept-check is entry 3.

## Boundaries & Constraints
**Always:**
- Require non-empty `boiler_water` entity id (mirror Outdoor). `r_max` / `hold` optional with defaults `2` / `900`; after coerce each must be `math.isfinite` and `> 0` or `ConfigError`. Keys are top-level — not under `weather_feedforward`. Yaml key names stay `r_max` / `hold` (epic-locked); internal local may stay `r_obs`.
- `boiler_water` leaves `ignored_keys`; leftover `pid` / `base_water_temp` stay ignored.
- Supply `listen_state` → dedicated `supply_event` (not `control_event`): only under Plant on ∧ Heating Demand, read supply; unreadable/non-finite → WARN, no trip, no auto-clear of an existing latch, do not advance the sample pair; first valid sample stores `(T, t)`; second yields `r_obs = (T2−T1) / (dt_s/60)`; if `dt_s ≤ 0` → WARN, replace sample with latest, no trip; while latched, valid samples still advance the pair; if `r_obs > r_max` and not latched → set RAM latch, `run_in(hold)` clear callback, write SWT `0` via `_write_setpoint`; if `r_obs > r_max` and already latched → do not restart `run_in` / do not replace the hold callback; may `_write_setpoint(0)` (equal-float skip). Trip/rate logs name supply rise with °C/min (not a bare `r_obs=` alone).
- While latched, `_run_demand` skips FF/`quantize_command` and commands `0` (equal-float skip). CAP-8 shared prelude→writer otherwise unchanged.
- Clear (`_clear_trip_state`): latch false, cancel hold timer if any, wipe supply sample history. Call from `_go_idle` (idle write-`0`, including outdoor-miss / no-zones / no-demand / non-finite `u_ff`), `_hands_off` (plant-off), and hold expiry callback. Clear is idempotent if the hold callback fires after cancel (no second demand write from a stale callback alone). Hold expiry then: if `_gate_prelude()` returns demand, call `_run_demand` (weather curve again). Outdoor-miss (or any `_go_idle`) while latched clears trip + cancels hold — same as other idle write-`0` paths.
- Latch is RAM-only (reload clears). Critical Zone must not drive the trip (diagnostics/log only as today).
- Stay inside AppDaemon `ha_smart_hvac` writing existing `plant_setpoint`. Example commissions `boiler_water` / `r_max` / `hold` with house-shaped placeholder for supply **and** comments that `r_max` is °C/min and `hold` is latch duration in seconds (not a setpoint).

**Never:**
- Zone rising-edge latch clear (entry 2); house `apps/apps.yaml` entity-id edits (entry 3 HITL).
- CAP-7 / `ff_auto_correct` / `ff_auto_correct_state.json`; persist latch to JSON.
- Change Exclusive Session, Heating Demand definition, weather-curve formula, or CAP-8 shared writer contract (trip only gates it).
- Drive trip or SWT from Critical Zone; rewrite AGENTS/CONTEXT/ADR/`knowledge/` (epic 3).
- Restart `run_in` / slide `hold` on re-trip while already latched; rename epic yaml keys (`r_max` / `hold`) in this story.

## I/O & Edge-Case Matrix
| Scenario | Input / State | Expected Output / Behavior | Error Handling |
| --- | --- | --- | --- |
| Happy trip | Plant∧Demand; two valid supply samples; `r_obs > r_max` | Latch; SWT `0`; hold `run_in` started; FF not applied while latched | No error |
| Latched demand tick/event | Latch set; prelude demand | `_run_demand` writes `0` (equal-float skip); no `u_ff` command | No error |
| Re-trip while latched | Latch set; another valid pair with `r_obs > r_max` | Sample pair advances; no new `run_in`; hold deadline unchanged; optional write `0` (equal-float) | No error |
| Hold expiry still demand | Latch; hold elapses (captured `run_in` callback); still Plant∧Demand | Clear trip state; `_run_demand` weather curve again | No error |
| Hold expiry idle/plant-off | Latch; hold elapses; gates closed | Clear only; no FF write | No error |
| Orphan hold callback | Clear already ran (`cancel_timer`); callback still invoked | Idempotent clear; no extra demand write from stale callback alone | No error |
| Outdoor-miss while latched | Latch set; Outdoor unavailable under plant-on | `_go_idle`: clear trip + cancel hold + write `0` | WARN Outdoor entity id |
| Idle / plant-off clear | Latched or sampled; idle write-`0` or plant-off | Clear latch + samples + cancel hold; idle writes `0`; plant-off no write | No error |
| Bad supply | Unreadable / non-finite under Plant∧Demand | WARN; no trip; existing latch stays | WARN entity id |
| `dt_s ≤ 0` | Two samples same/back timestamp | WARN; keep latest sample; no trip | WARN |
| CZ only | Multiple demand zones | Trip from supply only; CZ log-only on FF success path | No error |
| Parse defaults | Omit `r_max`/`hold`; valid `boiler_water` | `r_max=2`, `hold=900` | — |
| Parse reject | Missing/empty `boiler_water`; non-finite or `≤0` `r_max`/`hold` | `ConfigError` | ConfigError |
| Example yaml | Parse `apps.yaml.example` | Has `boiler_water`/`r_max`/`hold` with unit/meaning comments; not ignored | — |

</frozen-after-approval>

## Code Map
Continuity from 1.1 plan: CAP-8 `_gate_prelude` → `_run_demand`; Outdoor listener; vacuous idle/plant-off clear now gains trip-state clear (ADR vacuous-clear). Historical CAP-7 `r_obs` was zone-air °C/h — do not revive (`a305049`); name reuse for supply °C/min is ok if logs carry units.

1. `apps/ha_smart_hvac/models.py` — add `boiler_water: str`, `r_max: float = 2.0`, `hold: float = 900.0` on `HvacConfig`.
2. `apps/ha_smart_hvac/config.py` — `_KNOWN_KEYS` += those three; require non-empty `boiler_water` str; `_number` defaults 2/900 with finite and `> 0`; stop treating `boiler_water` as ignored leftover.
3. `apps/ha_smart_hvac/hvac_app.py` — RAM: latch, last supply sample, hold timer handle; `listen_state(supply_event, boiler_water)`; `supply_event` trip logic (Always, including no `run_in` restart while latched + sample advance); gate `_run_demand` when latched → write `0`; `_clear_trip_state` from `_go_idle` / `_hands_off` / hold callback (idempotent); hold callback cancel+clear then optional `_run_demand`; trip/rate logs include °C/min; reuse `_write_setpoint` / `_read_float` / `has_heating_demand` / `_read_zones`. Do not change FF formula or prelude order beyond clear hooks.
4. `apps.yaml.example` — top-level `boiler_water: sensor.YOUR_BOILER_WATER_TEMPERATURE` (or house-shaped comment), `r_max: 2` (°C/min comment), `hold: 900` (latch seconds comment, not setpoint).
5. Tests — `test_config.py`: example parse includes trip keys; stop expecting `boiler_water` in `ignored_keys`; defaults + reject cases. `test_hvac_app.py`: fixtures add `boiler_water`; listener registration; trip latch→0; latched FF gated; re-trip does not restart `run_in`; hold expiry via captured `run_in` callback restore; orphan callback after clear idempotent; outdoor-miss while latched clears; idle/plant-off clear; bad supply WARN no trip/no clear; CZ does not trip. Mock `run_in` / `cancel_timer`.

## Tasks & Acceptance
**Execution:**
- [ ] `models.py` + `config.py` — trip fields; required `boiler_water`; defaults/finite/`>0` for `r_max`/`hold`.
- [ ] `hvac_app.py` — supply listener, `r_obs`, latch/hold (no restart while latched), gate `_run_demand`, clear on idle/plant-off/hold expiry (+ re-run demand); unit-bearing trip logs.
- [ ] `apps.yaml.example` — commission `boiler_water` / `r_max` / `hold` with °C/min and latch-seconds comments.
- [ ] `tests/test_config.py` + `tests/test_hvac_app.py` — Behavior matrix rows (incl. re-trip, outdoor-miss while latched, orphan callback); flip legacy-ignore assertions for `boiler_water`.

**Acceptance Criteria:**
- Given Plant on + Heating Demand and two valid supply samples with `r_obs > r_max`, when the second sample arrives, then latch is set and plant SWT is commanded `0`.
- Given latch set under demand, when tick/event runs `_run_demand`, then SWT stays/commands `0` and weather curve is not applied.
- Given latch set, when another supply pair has `r_obs > r_max`, then `run_in` is not restarted and the hold deadline is unchanged.
- Given latch set, when hold expires while still gated (test fires captured `run_in` callback), then latch/samples clear and demand SWT follows weather curve again.
- Given latch or samples, when idle write-`0` or plant-off runs, then latch and samples clear (and hold cancelled).
- Given latch set, when Outdoor is unavailable under plant-on, then `_go_idle` clears trip state and cancels hold (write `0`).
- Given clear already ran, when a stale hold callback fires, then clear is idempotent and does not alone re-enter demand write.
- Given unreadable/non-finite supply under demand, when supply event fires, then WARN only — no new trip and no auto-clear of an existing latch.
- Given `apps.yaml.example` / parse fixtures, when parsed, then `boiler_water`/`r_max`/`hold` are accepted (not ignored) with defaults 2/900 and example comments document °C/min and latch seconds.

## Design Notes
- Hold uses AD `run_in` + `cancel_timer` (no existing timer pattern beyond `run_every`); wall-clock-only on tick would delay clear up to `control_interval`. Hold clock starts at first latch; sliding restart on noisy supply would extend SWT `0` indefinitely (party C1).
- Supply is trip observation, not an FF control input — dedicated handler avoids refreshing the curve on every supply change.
- Idle paths that call `_go_idle` (outdoor-miss, no zones, no demand, non-finite `u_ff`) clear trip state because they are idle write-`0` — including while latched (party A1); trip therefore lives only while the demand-path gates stay open.
- Yaml keeps epic names `r_max` / `hold`; operator truth is in example comments + log units (party B1), not a key rename.

## Verification
**Commands:**
- `uv run pytest` — expected: all pass (matrix + negatives).
- `uv run ruff check apps/ha_smart_hvac tests` — expected: clean.

**Manual checks (if no CLI):**
- Exclusive Session: under Plant∧Demand, sudden supply rise > `r_max` → SWT `0`; after `hold` (or idle/plant-off) latch clears and curve returns when gated.

## Implementation Notes
## Plan Change Log
- 2026-11-12 party (A1/B1/C1): outdoor-miss while latched → matrix+AC clear; example comments + unit-bearing logs (yaml/`r_obs` names kept); re-trip does not restart `run_in`; orphan callback idempotent; sample pair still advances while latched.
## Review Triage Log
