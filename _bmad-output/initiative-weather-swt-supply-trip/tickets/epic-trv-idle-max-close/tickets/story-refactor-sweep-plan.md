---
title: 'Refactor sweep'
type: 'chore'
ticket: '3'
created: '2026-11-16'
status: built
baseline_revision: '165eb56e849dc42cbeef665fa81491a0c8d8c4a0'
route: 'full'
route_source: 'auto'
risk: 'medium'
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
**Problem:** Epic 4 deferred notes still call out open TRV soft-close leftovers from 4.1: no accuracy-entity listener, missing prelude-isolation and expanded multi-TRV goldens, and `_entity_id` accepting whitespace-only ids.

**Approach:** Close those four deferred items only — listen accuracy → `control_event`, add the named ACs, strip entity ids at parse, then prune this epic’s deferred-work bullets. No flame/SWT/house-yaml scope; leave epic-3 deferred bullets alone.

## Boundaries & Constraints
**Always:**
- Scope = epic-trv entry `id=3` deferred findings A–D from `deferred-work.md` (accuracy listen; Outdoor-fail / empty-zone prelude / sibling-zone-T TRV ACs; multi-TRV / mixed-list / cold-start goldens; `_entity_id` → `raw.strip()` then non-empty, return stripped).
- Keep `_apply_trv_law` before `_gate_prelude` on tick/event; never on `supply_event`.
- App still never writes `valve_opening_degree`; Critical Zone never drives TRV or SWT.
- After settlement, prune only this epic’s TRV deferred bullets (incl. the 2026-11-15 whitespace code-review repeat); leave epic-3 AGENTS/CONTEXT/ADR and CAP-8 bullets on purpose (they point at dropped epic-3 entry 4 / docs hygiene — not this story).
- `uv run pytest` and `uv run ruff check apps/ha_smart_hvac tests` clean.

**Never:**
- New product laws beyond A–D (no closure listen, no flame trip, no CAP-7, no house `apps/apps.yaml` edits).
- Edit frozen Intent of 4.1/4.2 plans; rewrite AGENTS/CONTEXT/ADR/`knowledge/`; Exclusive Session.
- Touch epic-3 deferred bullets or dropped epic-3 entry-4 plan.
- Idle-overshoot “if still thin” extras — covered by 4.1 `independent_of_heating_demand` + core overshoot.
- Separate Plant-off + accuracy AC — plant-off law covered by 4.1; accuracy AC stays Plant-on only.

## I/O & Edge-Case Matrix
| Scenario | Input / State | Expected Output / Behavior | Error Handling |
| --- | --- | --- | --- |
| Accuracy change | Plant on; accuracy entity state changes | Same `control_event` → `_apply_trv_law` re-applies floor/100 (no TRV-only handler) | Unlatched + unreadable accuracy: skip overshoot (as today); latched clear/hold already locked by 4.1 `test_trv_latched_accuracy_unavailable_*` |
| Outdoor prelude fail + TRV | Outdoor unavailable; Plant on; commissioned TRV | TRV law ran before failed prelude; SWT idle as today | No TRV rollback on prelude fail |
| Empty-zone prelude + TRV | Zone reads empty → prelude `_go_idle`; commissioned TRV | TRV law ran before failed prelude; SWT idle as today | No TRV rollback on prelude fail |
| Sibling T unreadable + TRV | Sibling zone T bad; this TRV’s own reads OK | This TRV still writes per own reads (own-reads isolation, not “prelude None”) | Per-TRV skip when this TRV’s inputs unreadable |
| Multi-TRV / mixed | ≥2 commissioned + plain string | Independent latches; plain never gets closure write | Per-TRV skip on unreadable inputs |
| Cold-start overshoot | Initialize with T > sp+acc | First tick writes 100 and latches | Write-fail: no latch |
| Whitespace-only entity id | `"   "` in any `_entity_id` field | `ConfigError` (strip → empty) | Same for climate/closure/accuracy/plant/etc. |
| Padded entity id | `"  climate.x  "` (or any entity field) | Parse OK; stored id is stripped (`climate.x`) | Non-str still `ConfigError` |

</frozen-after-approval>

## Code Map
- `apps/ha_smart_hvac/hvac_app.py` — `_register_control_listeners` (~L59–72): today plant/outdoor/zone T + climate `hvac_action`/`temperature` only; **add** `listen_state(control_event, thermo.accuracy)` when `thermo.accuracy` set (same `control_event`, not a TRV-only callback). `_apply_trv_law` (~L387–422) + call sites `control_tick`/`control_event` (~L229–247) before prelude — reuse; do not call from `supply_event`. `_trv_overshoot_latched` set keyed by `closure_id`.
- `apps/ha_smart_hvac/config.py` — `_entity_id` (~L118–121): `strip()` then reject empty; **return stripped**; used by all entity fields (not TRV-only). Floor/TRV parse already OK.
- `apps/ha_smart_hvac/models.py` — `ThermostatConfig.accuracy` / `valve_closure`; `commissioned` unused by runtime — **do not** refactor unless a deferred note requires it (none does).
- `tests/test_hvac_app.py` — extend TRV suite (~L1740+); update `test_initialize_trv_mapping_listens_on_climate_attrs`: keep climate attr asserts; **add** entity-level assert listen on each commissioned `accuracy`; **assert no** listen on `valve_closure` (entity or attribute). Do not rely on “invert” — today’s test only filters attribute listens, so accuracy entity listen would not fail it.
- `tests/test_config.py` — whitespace-only `_entity_id` reject; padded id accepts as stripped.
- `_bmad-output/.../deferred-work.md` — remove epic-4 TRV bullets (accuracy re-apply; prelude-isolation ACs; expanded goldens; whitespace `_entity_id` ×2). When pruning the expanded-goldens bullet, note idle-overshoot settled by 4.1 `test_trv_independent_of_heating_demand` (+ core overshoot) so that half of C is not left open. Keep epic-3/docs hygiene bullets on purpose.
- `tickets.toml` entry 3 — description/verify already name A–D (party F1–F8); confirm only, no rewrite unless drift.
- Out of scope: house yaml, `apps.yaml.example` (already commissioned), water/trip path, epic-3 plans.

## Tasks & Acceptance
**Execution:**
- [ ] `config.py` — `_entity_id`: `strip()` then non-empty `ConfigError`, return stripped; tests: whitespace-only reject + padded accept.
- [ ] `hvac_app.py` — register `listen_state(self.control_event, accuracy)` per commissioned TRV (existing `control_event`); update initialize listener test: accuracy entity listen yes, closure listen no (keep climate attrs).
- [ ] `test_hvac_app.py` — ACs: accuracy-only state change (Plant on) re-applies law; **three** prelude-isolation tests (Outdoor-fail; empty-zone; sibling T unreadable / own-reads); multi-TRV independent latch; mixed-list plain skipped; cold-start overshoot latch (unfinished 4.1 must-fix goldens).
- [ ] `tickets.toml` — confirm entry 3 description/verify already list A–D + prune + pytest/ruff (edit only if drifted).
- [ ] `deferred-work.md` — prune settled epic-4 TRV bullets after ACs green; on expanded-goldens prune cite `test_trv_independent_of_heating_demand` for idle-overshoot; leave epic-3 blocks on purpose.
- [ ] Verify — pytest + ruff below.

**Acceptance Criteria:**
- Given a commissioned TRV and Plant on, when only the accuracy entity changes, then `_apply_trv_law` runs via the existing `control_event` and closure follows floor/100.
- Given initialize with commissioned TRV mapping, when listeners are registered, then each commissioned `accuracy` has an entity `listen_state` on `control_event` and `valve_closure` has none.
- Given Outdoor unavailable, when tick/event runs, then TRV soft-close still applied before prelude failure and SWT follows existing idle/skip.
- Given empty-zone prelude (`_go_idle` no valid zones), when tick/event runs, then TRV soft-close still applied before that failure and SWT follows existing idle/skip.
- Given sibling zone T unreadable and this TRV’s own inputs readable, when tick/event runs, then this TRV still writes per own reads (own-reads isolation).
- Given ≥2 commissioned TRVs (and a plain-string thermostat in the same list), when overshoot/clear differ per TRV, then latches and writes are independent and the plain thermostat never receives `valve_closure_degree`.
- Given cold start with T_zone > setpoint + accuracy, when the first tick runs, then closure 100 is written and the latch is set only after a successful write.
- Given any yaml entity field that is whitespace-only, when parsed, then `ConfigError`.
- Given any yaml entity field with leading/trailing whitespace and non-empty strip, when parsed, then the stored id is the stripped value.
- Given epic-4 deferred notes after this sweep, when inspected, then they no longer call out the four TRV leftovers; epic-3 deferred bullets remain on purpose (dropped epic-3 entry 4 / docs hygiene — not settled here).
- Given the suite, when `uv run pytest` and `uv run ruff check apps/ha_smart_hvac tests` run, then both are clean.

## Implementation Notes
## Plan Change Log
- 2026-11-16 party gap hunt locks F1–F8: initialize accuracy/closure listen asserts (no invert); strip-then-keep + padded matrix; three prelude ACs; drop idle-overshoot-if-thin; tickets.toml A–D verify; Plant-off+accuracy out (4.1); Design Notes control_event + 4.1 golden debt; epic-3 deferred remain-on-purpose.
- 2026-11-16 review nits: unlatched-only accuracy Error Handling + 4.1 latched cite; tickets.toml confirm-only; expanded-goldens prune cites `test_trv_independent_of_heating_demand`.
## Review Triage Log
| Finding | Verdict | Route | Evidence |
| --- | --- | --- | --- |
| BH: deferred-work prune missing idle-overshoot cite of `test_trv_independent_of_heating_demand` | low | patch | Design Notes + Manual checks require that cite on expanded-goldens prune; file only deletes bullets; tickets.toml notes omit the test name |
| EC: same deferred-work missing cite | low | patch | Same root cause as BH deferred cite |
| BH/EC: empty-zone AC “soft-close still applied” vs no closure write | false | reject | Matrix expects “TRV law ran”; test spies `_apply_trv_law` then correctly asserts per-TRV skip on unread zone T; fix would be plan-AC wording |
| BH: plan AC says `valve_closure_degree` | false | reject | Plan-only naming nit; fix is edit plan; runtime uses `valve_closure` / never writes opening |
| BH: cold-start write-fail latch untested | false | reject | Happy-path AC met (100 + latch after successful write); write-fail latch law pre-exists 4.1 and was not a deferred A–D deliverable |
| BH: Outdoor/empty isolation tests only `control_tick` | false | reject | Tick and `control_event` share `_apply_trv_law` then prelude; isolation property covered once |
| BH: accuracy AC weakly proves value-driven floor↔100 flip | false | reject | AC requires accuracy-entity `control_event` re-applies law and closure follows floor/100; test does that on undershoot |
| BH: Execution checkboxes still `[ ]` | false | reject | Finding fix is edit this build’s plan |
| BH: memlog “Approve never happened” vs shipped code | false | reject | Human approved in-session after memlog; status advanced to in-review |
| BH: tickets.toml `risk=low` vs plan `medium` | low | reject | Cosmetic metadata drift; unlikely everyday harm |
| BH: tickets.toml rewritten despite confirm-only Code Map | false | reject | Plan Change Log party locks already authorized A–D verify rewrite |
| BH: empty Implementation Notes | low | reject | Optional section; fix is plan edit |
| BH: duplicate closure listen asserts | low | reject | Cosmetic test style; no behavioral gap |
| verification-gap: none | — | — | No gap findings filed |
| intent-alignment: R2 idle-overshoot vs prune | false | reject | Frozen Never + Design Notes intentionally drop idle-overshoot-if-thin as covered by 4.1; descriptive audit only |


## Code Review
### 2026-11-16
**Code review complete.** 0 `decision-needed`, 0 `patch`, 0 `defer`, 17 rejected.

Rejected:
- R1 (blind-hunter): false — accuracy AC met by control_event re-apply + floor write; flip not required
- R2 (blind-hunter): false — single-TRV initialize exercises accuracy listen branch
- R3 (blind-hunter): false — empty-zone isolation is law-ran + own-T skip, not soft-close write
- R4 (blind-hunter): false — tick and control_event share TRV→prelude path
- R5 (blind-hunter): false — sibling AC is TRV own-reads, not SWT demand
- R6 (blind-hunter): low rejected — plan checkbox/Implementation Notes hygiene rarely visible
- R7 (blind-hunter): low rejected — risk metadata drift cosmetic
- R8 (blind-hunter): low rejected — duplicate closure-listen assert cosmetic
- R9 (blind-hunter): low rejected — deferred Settled breadcrumbs docs-only
- R10 (blind-hunter): low rejected — party memlog process artifact
- R11 (blind-hunter): false — cold-start write-fail latch out of A–D
- R12 (blind-hunter): false — multi/mixed AC is writes/latches; initialize listens covered elsewhere
- R13 (blind-hunter): false — plan `valve_closure_degree` naming nit
- R14 (blind-hunter): false — walkthrough stubs are this-session artifacts, not in HEAD
- R15 (intent-alignment): false — same as R3 (descriptive)
- R16 (intent-alignment): false — same as R4 (descriptive)
- R17 (intent-alignment): false — idle-overshoot cite-only by frozen Never
