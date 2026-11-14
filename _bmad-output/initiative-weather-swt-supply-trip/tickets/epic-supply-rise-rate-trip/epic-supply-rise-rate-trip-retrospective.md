---
epic: epic-supply-rise-rate-trip
date: 2026-11-14
verdict: accepted-with-open-items
criteria: declared
headless: false
---

# Retrospective: Supply rise-rate trip

## Epic summary

**Epic:** `epic-supply-rise-rate-trip` (id 2) — Supply rise-rate trip  
**Folder:** `_bmad-output/initiative-weather-swt-supply-trip/tickets/epic-supply-rise-rate-trip/`  
**Going-in concerns:** none (user: «гонять как есть»).  
**Tickets still at `built`:** none.  
**Unfinished (`pending_tickets`):** none — all four tickets `status`/`state` = `done`.  
**Epic Requirements / Done when:** declared in `epic-supply-rise-rate-trip.md` (R5–R7; Done when 1–5).  
**Phase 4 human decisions (2026-11-14):** machine verdict approved; action items = recommended set approved; decision records = all five proposed written.

| Ref | Title | Status / state | Covers | Plan |
| --- | --- | --- | --- | --- |
| 2.1 | Tracer: supply rise-rate trip | done / done | R5, R6, R7 | `tickets/story-tracer-supply-rise-rate-trip-plan.md` |
| 2.2 | Zone rising-edge latch clear | done / done | R6 | `tickets/story-zone-rising-edge-latch-clear-plan.md` |
| 2.3 | House: accept boiler_water | done / done (HITL) | R7 | `tickets/story-house-accept-boiler-water-plan.md` |
| 2.4 | Refactor sweep | done / done | — | `tickets/story-refactor-sweep-plan.md` |

### Plan ranges (baselines oldest → newest)

| Ticket | `baseline_revision` | Range | Notes |
| --- | --- | --- | --- |
| 2.1 | `93157eee2504bc820fd872bf41d4109dfb4aef9e` | `93157eee..d19294cf` | Next baseline = 2.2; feat+harden trip |
| 2.2 | `d19294cf1009afd8d5175f015db526d931ce8968` | `d19294cf..bade2292` | Rising-edge + release 3.7.0/3.8.0 + party memlog |
| 2.3 | `bade2292d5f530f6157d666e2671a76684b4c108` | `bade2292..40e6a2a1` | Plan + mark-done only; house yaml gitignored |
| 2.4 | `40e6a2a1806328aaded7ada74f3490ee1fdda257` | `40e6a2a1..a84b9ca` | Cut at last epic commit (= HEAD at inventory) |

`git_evidence.py` once per distinct range. **2.1 / 2.3 / 2.4:** `merge_count` == `merges_measured`. **2.2:** `merge_count` 4 vs `merges_measured` 2 (gap recorded).

**2.1 churn:** `test_hvac_app.py` (+331), `hvac_app.py` (+116), `test_config.py` (+67), tracer plan (+49), `config.py` (+23).  
**2.2 churn:** `test_hvac_app.py` (+385), 2.2 plan (+132), `CHANGELOG.md` (+43), `hvac_app.py` (+31).  
**2.3 churn:** house-accept plan only (+99).  
**2.4 churn:** refactor plan (+81), `test_hvac_app.py` (+47), `deferred-work.md` (−9).

### Evidence inventory

| Artifact | Available? | Note |
| --- | --- | --- |
| Epic file | yes | R5–R7 + Done when 1–5 declared |
| Initiative file | not opened | covers restated on epic |
| Ticket entries / plans | yes | `story_file` null for all |
| Diff ranges | yes | four `git_evidence.py` runs; epic code diff `93157eee..HEAD` |
| Run folders / companions | none | — |
| Previous retrospective | yes | `epic-weather-curve-swt-restore-retrospective.md` |
| Session logs | partial | process-lesson analysis **skipped** |
| Deferred-work (post-2.4) | yes | only epic-3 AGENTS/CONTEXT/ADR PID contradiction |

## Findings

`bmad-review` narrowing: adversarial / edge-case-hunter / verification-gap on `93157eee..HEAD` scoped to `apps/`, `apps.yaml.example`, `tests/`. Plan-locked Intent surfaces → accept as-is where noted. Phase 3 team discussion: skipped (opt-in; not requested).

| ID | Finding | Source | Instance disposition | Upstream lesson |
| --- | --- | --- | --- | --- |
| A1 | Trip latch gates CAP-8 `_run_demand` (writes 0, skips FF); no new modules; imports acyclic | `hvac_app.py:253-257`; epic Boundaries | checked and clean | trip-as-gate split worked |
| A2 | Parallel gates: `_gate_prelude` (Outdoor) vs `_plant_and_heating_demand` (supply) | `hvac_app.py:73-137`; 2.1 Intent | **accept as-is** | document dual-gate in domain docs (epic 3) |
| A3 | `hvac_app.py` 241→388; `test_hvac_app.py` 924→1687; trip methods clustered | `wc -l`; git_evidence | accept as-is (large but coherent) | keep trip helpers colocated |
| D1 | Two clear shapes: `_clear_trip_state` vs `_go_idle` Decision C (disarm always; latch after write) | `hvac_app.py:139-142,292-296`; 2.1 Decision C | **accept as-is** | ADR written |
| S1 | Done when 1–3 / R5–R6 met in code+tests (trip, latched 0, hold/edge/idle/plant-off clears) | epic Done when; tests ~998–1573 | checked and clean | — |
| S2 | Done when 4 house id: HITL plan only (gitignored yaml); RAM latch stated, no reload test | 2.3 plan; `hvac_app.py:40-44` | **accept as-is** (HITL + Intent) | — |
| S3 | Done when 5 suite present; CZ×trip locked in 2.4 | `test_latched_trip_path_does_not_use_critical_zone` | checked and clean | — |
| S4 | Non-finite supply on unlatched path: code maps via `_read_float`; only latched bad-supply test | epic Notes; `test_bad_supply_warns_without_trip` | **defer** | pin unlatched bad-supply sample immutability |
| P1 | `control_event` docstring still says “no sticky latch” after trip latch | `hvac_app.py:242` | **fix now** | update docs with runtime |
| P2 | AGENTS/CONTEXT/ADR still PID — epic 3 | `deferred-work.md` | **accept as-is → epic 3** | — |
| ADV1 | Rising-edge clears latch before curve write; failed write leaves latch false | `hvac_app.py:100-101,259-268`; Intent 2.2 | **defer** | optional write-gated edge clear |
| ADV2 | Idle Decision C: failed write keeps latch without hold | `hvac_app.py:292-296`; plan Decision C | **accept as-is** | ADR written |
| ADV3 | Supply can trip while Outdoor unavailable (then tick may idle-clear) | `hvac_app.py:171-174` vs `81-86`; `test_supply_trip_under_demand_outdoor_unavailable` | **accept as-is** (Intent) | — |
| ADV4 | Event-driven `r_obs` / unbounded `dt_s` / strict `>` threshold | `hvac_app.py:185-198`; epic D6 | **accept as-is** (spec) | optional MAX_DT / boundary test |
| ADV5 | RAM latch lost on AppDaemon reload | epic Done when 4; Intent | **accept as-is** | — |
| ADV6 | Missing rising-edge clear log | `hvac_app.py:100-101`; 2.2 triage rejected distinct log | **accept as-is** | — |
| E1 | Already-latched `supply_event` re-write ignores write failure | `hvac_app.py:199-202` | **defer** | warn/return on fail |
| E2 | Ungated `supply_event` wipes sample only (latch/hold stay) | `hvac_app.py:172-174`; Intent | **accept as-is** (prelude owns clear) | — |
| E3 | Rising-edge clear only on `_gate_prelude`, not `supply_event` | 2.2 Intent Always | **accept as-is** | — |
| E4 | Claim “idle clears trip” vs write-fail keep-latch | Decision C; claim lens | **accept as-is** (documented Decision C) | ADR written |
| V1 | No test: latched `_run_demand` with unreadable plant | verification-gap; `_run_demand:253-257` | **defer** | mirror idle write-fail test |
| V2 | No `r_obs == r_max` boundary test (strict `>`) | verification-gap; `197-198` | **defer** | add equal-rate no-trip test |
| V3 | Already-latched re-trip does not assert SWT re-write | `test_already_latched_does_not_restart_hold` | **defer** | assert `_set_value_writes` |
| V4 | No-demand ungated sample wipe untested (plant-off covered) | `test_supply_event_no_heating_demand_does_not_trip` | **defer** | assert `_supply_sample is None` |
| V5 | Empty-zone idle while latched: latch/hold teardown untested | `test_empty_zone_read_leaves_prior_unchanged` | **defer** | arm latch then assert clear |
| V6 | Unlatched bad supply sample immutability untested | same as S4 | **defer** | — |
| PROC1 | Session logs incomplete → process lessons skipped | inventory | accept narrowing | — |
| PROC2 | 2.2 `merge_count`≠`merges_measured` | git_evidence 2.2 | accept as-is | release merges in range |
| PROC3 | 2.2 Execution checkboxes still unchecked | 2.2 plan; triage false | accept as-is | frontmatter SoT |
| PROC4 | Exclusive Session / live AppDaemon E2E unevidenced | 2.1 Manual checks | **defer** (open item) | record live pass/fail or waive |

## Behavior verification

| Check | Result |
| --- | --- |
| `uv run pytest` | **343 passed** (2026-11-14) |
| `uv run ruff check apps/ha_smart_hvac tests` | clean |
| House offline `parse_config` | **PASS** — `boiler_water=sensor.opentherm_bridge_boiler_water_temperature_degc`; `ignored_keys=()`; `r_max=2.0`; `hold=900` |
| Exclusive Session / live AppDaemon E2E | **Not exercised / unevidenced** — narrowed to unit + offline |

## Previous-retro follow-through

Prior: `epic-weather-curve-swt-restore-retrospective.md` Action items.

| Item (prior wording) | Owner | Landed? |
| --- | --- | --- |
| Reconcile epic R2/R3 “clear ephemeral…” with vacuous clear / trip-state epic 2 | Sofia | **yes** — `epic-weather-curve-swt-restore.md` R2/R3 + Notes Decision (2026-11-12 retrospective); epic 2 Description owns trip clear |
| Carry-forward: AGENTS/CONTEXT/ADR supersede + delete `pid.py`/`rls.py` | epic 3 | **no evidence in this epic** — still `deferred-work.md` sole entry |
| Carry-forward: supply entity + rise-rate latch | epic 2 | **yes** — this epic (2.1–2.4 done; code+tests+house accept) |
| Harden outdoor listener test (full CAP-8 set + `control_event` callback) | Dev | **partial** — `test_initialize_registers_outdoor_and_supply_listeners` asserts outdoor entity + supply callback identity; outdoor/`control_event` callback golden still membership-style for plant/outdoor |
| Optional F6-B runtime `hasattr` lock | Dev | **no evidence found** |
| Strip/reject whitespace `outdoor_temperature` | Dev | **no evidence found** (`config.py` still non-empty str only) |
| Decide waive vs run Exclusive Session live verify | Operator / Dev | **no evidence found** — still open (PROC4) |

## Action items

Human approved recommended set 2026-11-14. Remediation/spec items below are **proposed, not applied** by this skill (except decision records written under Decision records).

| # | Item | Owner | Kind |
| --- | --- | --- | --- |
| 1 | Fix `control_event` docstring: remove “no sticky latch”; name trip latched-zero override | Dev | Remediation — awaiting apply |
| 2 | Carry-forward: AGENTS/CONTEXT/ADR supersede + delete dead `pid`/`rls` | epic 3 | Spec/docs — already in `deferred-work.md` |
| 3 | Deferred hardening tests: V1–V6 / S4 / E1 / ADV1 | Dev | Remediation — deferred |
| 4 | Decide waive vs run Exclusive Session live verify for trip+curve; record result | Operator / Dev | Process — open |
| 5 | Optional: rising-edge clear structured log | Dev | accept as-is (prior reject) — no action |

## Decision records

Human approved all five proposed records 2026-11-14; written:

| Proposal | Plan / commit | Written? |
| --- | --- | --- |
| Supply path Plant∧Demand only — never Outdoor prelude | 2.1 Intent; `fbe647f` / `d7e5262` | **yes** → `docs/decisions/adr-supply-event-no-outdoor-prelude.md` |
| First latch only after successful SWT `0` write | 2.1 review Decision; same | **yes** → `docs/decisions/adr-write-gated-supply-trip-latch.md` |
| Idle: always disarm hold/wipe samples; clear latch only after idle write `0` succeeds | 2.1 Decision C | **yes** → `docs/decisions/adr-idle-trip-clear-after-write.md` |
| Rising-edge: missing zone → False; empty prior seeds without clear | 2.2 Decision A; `70d4ccb` / `52320dc` | **yes** → `docs/decisions/adr-zone-rising-edge-decision-a.md` |
| Hold `token` invalidates orphan `_trip_hold_expired` callbacks | 2.1 harden; `d7e5262` | **yes** → `docs/decisions/adr-trip-hold-token-orphan-guard.md` |

House HITL boiler_water accept (2.3) was not proposed (fails ADR test).

## Acceptance verdict

**Verdict:** `accepted-with-open-items`  
**Criteria:** declared  
**Human:** confirmed machine draft 2026-11-14.

**Met in evidence:** Done when 1–5 via unit tests (trip/latch/clears/CZ), example+parse commission, house offline accept, RAM latch Intent, CAP-7 absent; all tickets finished.

**Open items:** action #1 docstring; #2 epic 3; #3 deferred tests; #4 Exclusive Session unevidenced; prior-retro leftovers (strip/hasattr/listener golden).

## Open questions

1. Exclusive Session after epic 2 — waive or run? (action #4) — **unanswered**.  
2. Decision records — **closed** (all five written).  
3. Verdict / action-item set — **closed** (human approved).

## Assumptions

_(interactive — omit)_
