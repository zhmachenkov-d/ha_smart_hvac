---
title: 'Tracer: replace supply trip with flame short-on'
type: 'feature'
ticket: '1'
created: '2026-11-16'
status: built
baseline_revision: 'b9352a3cc9cd3fd3b887560a729da12a970cdffb'
route: 'full'
route_source: 'auto'
risk: 'high'
review: 'thorough'
review_source: 'auto'
review_loop_iteration: 0
lenses_ran: ['blind-hunter', 'edge-case-hunter', 'verification-gap', 'intent-alignment']
context:
  - '{project-root}/CONTEXT.md'
  - '{project-root}/AGENTS.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent
**Problem:** Supply rise-rate trip is the wrong plant anti-cycle after TRV soft-close; flame short-on must gate weather-curve demand instead.

**Approach:** Remove supply trip end-to-end; add yaml `flame_on` / `ch_active` / `flame_on_min_s` (default 300) / `flame_trip_hold_s` (default 900); short True→False flame under Plant∧Demand∧`ch_active`∧¬latch latches SWT `0` after successful write; clear on hold / zone rising-edge / plant-off / successful idle write-0; ADV8 hold-expiry = `_apply_trv_law` then Outdoor prelude + demand. Example yaml only — house ids are epic entry id=2.

## Boundaries & Constraints
**Always:**
- Delete `supply_event`, `_supply_sample`, `_plant_and_heating_demand`, and `boiler_water` / `r_max` / `hold` from App, config, example, tests.
- `_flame_observe_gate` = Plant on ∧ `_read_zones` + `has_heating_demand` ∧ `ch_active == "on"` ∧ ¬latch — never Outdoor / `_gate_prelude`. Same gate for arm and falling-edge latch attempt.
- Arm only on strict rising (`old` explicitly not-on ∧ `new == "on"`) under open gate; duration via `_monotonic()`; falling edge trips only if gate still open and duration &lt; `flame_on_min_s`; latch only after `_write_setpoint(0)` True + tokenized `run_in` hold. Every falling-edge eval clears `_flame_on_since`.
- Listen `flame_on` and `ch_active`. Ungated / `ch_active` off / unreadable → wipe `since` (no trip). Binary active = `"on"`.
- While latched: `_run_demand` keeps SWT 0 (no curve, no CZ select/log); TRV law still on tick/event; flame/`ch_active` handlers never write SWT (wipe `since` only). No latched observer re-assert (unlike former supply).
- Clears: ADV8 hold expiry (TRV → prelude → demand); zone False→True in `_gate_prelude`; `_hands_off` clear without SWT write; `_go_idle` disarm always, clear latch iff idle write-0 succeeds (Decision C, including while latched). Any clear/disarm/ungated/falling → `since = None`.
- Required: `flame_on`, `ch_active`. Optional: `flame_on_min_s` float &gt;0 (300); `flame_trip_hold_s` fractional-truncate int ≥1 (900). Latch RAM-only. House `apps.yaml` is entry id=2 only.

**Never:** Restore supply trip; edit house yaml / ADR / knowledge / AGENTS / CONTEXT; collapse `ch_active` into plant; hardcode flame ids; freeze TRV while latched; latch on write-fail or closed gate at fall; arm on already-on / `None`→`"on"`; restart hold while latched.

**Decisions:**
- Flame-named RAM/helpers; delete `_plant_and_heating_demand`. Expanded U1/S1 goldens, E1 example comments, named supply-port suite, dedicated V1 truncate AC, and meta house-verify AC → deferred-work (token split).
- Example: `YOUR_*` flame placeholders; drop trip keys; keep TRV / weather_ff.

## I/O & Edge-Case Matrix
| Scenario | Input / State | Expected / Behavior | Error Handling |
| --- | --- | --- | --- |
| Short flame | Gate open rise+fall; duration &lt; min | SWT 0; latch; hold; clear since | Write False → no latch; clear since |
| Long flame | Gate open; duration ≥ min | No latch; wipe since | — |
| Fall gate closed | Armed; demand/`ch_active` lost before fall | Wipe since; no latch | No SWT |
| No Outdoor | Demand+plant+ch; outdoor unread | Observe/trip still allowed | — |
| Latched demand | Latch; tick/event | SWT 0 only; TRV runs; no CZ select/log | Write fail keeps latch |
| Hold expiry | Token match | Clear; TRV then prelude; curve if open | Orphan → no-op |
| Rising-edge | Zone False→True while latched | Clear then curve | Empty prior seeds |
| Plant off | Plant not on | Clear latch/hold/since; no SWT | — |
| Idle Decision C | No demand / bad outdoor / empty zones | Disarm; clear latch iff write-0 True | Write-fail keeps latch |
| Gate / CH off | Plant off / no demand / ch off / latched arm | Wipe since; no new latch | CH listen wipes now |
| Example | Parse example | Flame keys; no trip keys | Missing flame → ConfigError |

</frozen-after-approval>

## Code Map
- `models.py` / `config.py` — drop trip fields; add flame entities + min/hold defaults/validation.
- `hvac_app.py` — remove supply path; `_flame_observe_gate` + `flame_event`/`ch_active` listen; latch/hold/clears; `_run_demand` flame gate; ADV8 hold-expired; TRV before prelude on tick/event.
- `coordinator.py` / `feedforward.py` — do not change.
- `apps.yaml.example` — flame `YOUR_*`; drop trip block.
- `tests/test_config.py` / `test_hvac_app.py` — flame matrix ACs; remove trip keys/fixtures.

## Tasks & Acceptance
**Execution:**
- [ ] `models.py` + `config.py` — flame fields/defaults/validation; drop trip keys.
- [ ] `hvac_app.py` — remove supply trip; flame observe/latch/clear + ADV8; gate `_run_demand`.
- [ ] `apps.yaml.example` — flame placeholders; no trip keys.
- [ ] `tests/test_config.py` + `tests/test_hvac_app.py` — core matrix; CZ/TRV-while-latched; ADV8 TRV-before-prelude; pytest+ruff clean.

**Acceptance Criteria:**
- Given App/config/example/tests, when searched, then no `supply_event` / `boiler_water` / `r_max` / supply `hold` / `r_obs` / `_plant_and_heating_demand` remain.
- Given gate open at rise and fall, when duration &lt; `flame_on_min_s` and write-0 succeeds, then latch + SWT 0; when write-0 fails, then no latch and `since` cleared.
- Given `since` set, when demand or `ch_active` drops before True→False, then fall wipes `since` and does not latch.
- Given Plant∧Demand∧`ch_active`∧¬latch with Outdoor unavailable, when short True→False, then flame may still latch (observe never uses Outdoor).
- Given flame-latched demand, when tick/event runs, then SWT stays 0, TRV soft-close still applies, and no `select_max_error_demand_zone` / `critical_zone=` logging.
- Given latch, when hold expires with matching token, then clear, `_apply_trv_law` before Outdoor prelude, and curve demand when prelude opens.
- Given latch, when zone Heating Demand rises False→True, or Plant turns off, then latch clears (plant-off without SWT write); idle write-0 fail keeps latch; idle write-0 success clears it.
- Given `ch_active` turns off while `since` set, when its listener runs, then `since` wipes without latching.
- Given `apps.yaml.example`, when parsed, then `flame_on` / `ch_active` present and trip keys absent; missing flame entities → `ConfigError`.

## Implementation Notes
## Plan Change Log
- 2026-11-16 party + plan-review locks retained in Always (observe no Outdoor; gate-at-fall; A/W1/S1/C2/H1/V1/O1/Y1/D1; ADV8 ≠ old expiry).
- 2026-11-16 token split → deferred-work (expanded U1/S1 goldens; E1 comments; named supply-port suite; dedicated V1/example-comment AC; latched-handler + house-verify meta ACs); regenerated narrowed plan.
## Review Triage Log
| lens | finding | verdict | route | evidence |
| --- | --- | --- | --- | --- |
| plan-review | observe gate / fall-gate / CZ / ADV8 | medium | patch | carried retained in narrowed Always+ACs |
| token-scope | plan &gt;1600 tokens | — | split | carried deferred-work entries appended |
| blind-hunter | unavailable/unknown→on arms; on→unavailable can latch | high | patch | Verified: `flame_event` uses `old != "on"` / `new != "on"`; Always requires unreadable→wipe no trip and Intent True→False (binary off) |
| blind-hunter | AGENTS/CONTEXT/ADR still describe supply trip | false | — | Intent Approach is App/config/example swap + example-only; docs owned elsewhere (epic 6); stale text is not a defect of this Intent reading |
| blind-hunter | example lost per-key comments / header omits flame | false | — | E1 comments deferred in frozen Decisions/token split; parse AC still requires flame keys |
| blind-hunter | no golden for duration == flame_on_min_s | medium | patch | Verified: long-on uses 301 only; `>=` boundary unpinned |
| blind-hunter | missing closed-gate arm / already-on goldens | low | — | Reject: expanded U1/S1 goldens deferred; fall-after-gate-loss already covered |
| blind-hunter | tests still embed boiler_water/hold for ignore fixtures | false | — | Intentional legacy-ignore asserts; production surfaces clean |
| blind-hunter | empty Implementation Notes / plan status noise | false | — | Status now in-review; notes cosmetic |
| blind-hunter | latch run_in without canceling prior handle | false | — | Latched observe gate closed; disarm cancels before any re-arm; token invalidates orphans |
| blind-hunter | ADR/decision docs still name supply_event | false | — | Same as AGENTS/docs; epic 6 owns ADR |
| edge-case-hunter | unavailable/unknown→on arms short-on timer | high | patch | Same root as blind-hunter arm predicate |
| edge-case-hunter | on→unavailable/None can latch SWT 0 | high | patch | Same root as loose fall predicate vs Always unreadable wipe |
| edge-case-hunter | claim True→False vs any new!="on" | high | patch | Same root; Intent True→False means binary off |
| verification-gap | U1 unavailable→on arm not pinned | high | patch | Pre-verified gap; current predicate already arms; extend none-to-on tests |
| verification-gap | unreadable flame fall can trip; no test | high | patch | Pre-verified gap; add wipe/no-latch AC |
| verification-gap | exact flame_on_min_s equality untested | medium | patch | Pre-verified; add duration==min no-latch case |
| verification-gap | ch_active open while flame already on no-arm unpinned | low | patch | Code never arms from CH; small pin test; strengthens S1 |
| verification-gap | Other: arm/fall predicates contradict Always | high | patch | Same binary-edge root cause |
| intent-alignment | R3 engineering port vs R4 living-docs | false | — | Diff correctly implements R3; R4 not required by Intent Approach |

## Design Notes
Dual-gate observe stays Outdoor-free. Latched SWT only via `_run_demand`. ADV8 adds TRV before prelude. Entry id=2 owns house yaml.
## Verification
**Commands:**
- `uv run pytest` -- expected: pass
- `uv run ruff check apps/ha_smart_hvac tests` -- expected: clean

## Code Review

### 2026-11-16
**Code review complete.** 0 decision-needed, 5 patch, 0 defer, 15 rejected.

- [x] [Review][Patch] ch_active_event re-reads gate and can miss a CH-off wipe (race + missing open-gate preserve test) [apps/ha_smart_hvac/hvac_app.py:225]
- [x] [Review][Patch] Open-gate flame fall with since None is untested [apps/ha_smart_hvac/hvac_app.py:190]
- [x] [Review][Patch] Closed-gate off→on arm wipe branch unpinned [apps/ha_smart_hvac/hvac_app.py:183]
- [x] [Review][Patch] Closed-gate hold expiry does not assert ADV8 TRV still runs [tests/test_hvac_app.py:1294]
- [x] [Review][Patch] _flame_trip_app silently drops ch_active/flame_on kwargs [tests/test_hvac_app.py:1060]

Rejected: R1 Always arm wording vs code (frozen Always; Never+code correct); R2/R18 stale triage predicates (process noise); R3 status/checkbox drift (cosmetic); R4 AC vs legacy-ignore fixtures (intentional); R5 E1 example comments (deferred); R6 V1 900.9 golden (deferred); R9 non-positive duration (monotonic unreachable); R11 init warn only boiler_water (parse already covers); R12 True→False vs on/off (E1/Intent); R13 AGENTS/ADR supply trip (Never/epic 6); R15 Outdoor idle wipes since (Always requires disarm); R19 R-C vs R-D (aligned); R20 docs/house out of scope (intentional).

### 2026-11-16 (hvac observe/latch slice)
**Code review complete.** 0 decision-needed, 5 patch, 0 defer, 9 rejected.

- [x] [Review][Patch] Latch assigned before run_in completes [apps/ha_smart_hvac/hvac_app.py:198]
- [x] [Review][Patch] App tests never commission non-default flame_on_min_s / flame_trip_hold_s [tests/test_hvac_app.py]
- [x] [Review][Patch] Orphan-after-clear hold callback does not pin latch/handle unchanged [tests/test_hvac_app.py:1412]
- [x] [Review][Patch] Armed (unlatched) since wipe via plant-off/idle untested [tests/test_hvac_app.py]
- [x] [Review][Patch] No single e2e flame latch to hold expiry to curve golden [tests/test_hvac_app.py]

Rejected: R2 cancel-before-rearm (gate closed while latched); R3 non-positive duration (monotonic); R4 no mid-burn re-arm (Never); R5 no latched re-assert (Always); R6 Decision C disarm (Always+tested); R10 silent suppressions (noise); R13 ADV8 vs R2 (Always); R14 config outside slice diff (same PR elsewhere).

### 2026-11-16 (_run_demand / ADV8 slice)
**Code review complete.** 0 decision-needed, 6 patch, 0 defer, 9 rejected.

- [x] [Review][Patch] Latched _run_demand tests omit latch-retention and write-fail cases [tests/test_hvac_app.py:1374]
- [x] [Review][Patch] Closed-gate hold expiry omits disarm handle/token asserts [tests/test_hvac_app.py:1411]
- [x] [Review][Patch] TRV soft-close while flame-latched untested on control_event [tests/test_hvac_app.py:2009]
- [x] [Review][Patch] ADV8 hold-expiry TRV not proven by valve write [apps/ha_smart_hvac/hvac_app.py:160]
- [x] [Review][Patch] CH-off while latched leave-latch behavior untested [tests/test_hvac_app.py]
- [x] [Review][Patch] Decision C idle write-fail omits hold-token advance assert [tests/test_hvac_app.py:1544]

Rejected: R2 ADV8 then idle Decision C (clear-first by Always); R5 restore-demand after idle-fail (low); R8 ADV8 clear-before-idle (design); R9 u_ff log (cosmetic); R11 docs epic 6; R12 duration<=0 (monotonic); R13 CH-off ADV8 curve (demand never needs CH); R15 title-slice framing (not defect).
