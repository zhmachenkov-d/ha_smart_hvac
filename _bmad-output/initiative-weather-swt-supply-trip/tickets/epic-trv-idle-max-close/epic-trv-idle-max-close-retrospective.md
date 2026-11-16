---
epic: epic-trv-idle-max-close
date: 2026-11-16
verdict: accepted-with-open-items
criteria: declared
headless: false
---

# Retrospective: TRV idle max-close soft-close
## Epic summary
**Epic:** `epic-trv-idle-max-close` (id 4) — TRV idle max-close soft-close  
**Folder:** `_bmad-output/initiative-weather-swt-supply-trip/tickets/epic-trv-idle-max-close/`  
**Going-in concerns:** none (user: «let's go»).  
**Tickets still at `built`:** none.  
**Unfinished (`pending_tickets`):** none — all three tickets `status`/`state` = `done`.  
**Epic Requirements / Done when:** declared in `epic-trv-idle-max-close.md` (R1–R2; Done when 1–4).  
**Phase status:** Phases 1–5 complete. Phase 3 product-team: ADR D1+D2+D4+D5; revised actions; ADV8 → epic 5. Phase 4 human: verdict `accepted-with-open-items`.

| Ref | Title | Status / state | Covers | Plan |
| --- | --- | --- | --- | --- |
| 4.1 | Tracer: TRV idle max-close soft-close | done / done | R1, R2 | `tickets/story-tracer-trv-idle-max-close-soft-close-plan.md` |
| 4.2 | Commission house apps.yaml for TRV soft-close | done / done (HITL) | R1, R2 | `tickets/story-commission-house-apps-yaml-for-trv-soft-close-plan.md` |
| 4.3 | Refactor sweep | done / done | — | `tickets/story-refactor-sweep-plan.md` |

### Plan ranges (baselines oldest → newest)
| Ticket | `baseline_revision` | Range | Notes |
| --- | --- | --- | --- |
| 4.1 | `9c7bc3697a9fa155bea1ee7c60bd1ef26a17d201` | `9c7bc369..3539f091` | Next baseline = 4.2; feat+fix TRV + release 3.9.0 |
| 4.2 | `3539f091467cbb4e976994d32493f1d3f2ab93d1` | `3539f091..165eb56e` | Plan + walkthrough only; house yaml gitignored |
| 4.3 | `165eb56e849dc42cbeef665fa81491a0c8d8c4a0` | `165eb56e..b6286e80` | Inferred end = `HEAD` (PR #148 merge); last epic commit |

`git_evidence.py` once per distinct range. All three: `merge_count` == `merges_measured` (1). No `binary_revisions`.

**4.1 churn (non-merge `files`):** `test_hvac_app.py` (+312/−1), tracer plan (+138), `test_config.py` (+113), `CHANGELOG.md` (+97), `hvac_app.py` (+66/−7), `config.py` (+38/−4), `models.py` (+15), `apps.yaml.example` (+8).  
**4.2 churn:** commission plan (+143), walkthrough artifacts only — no `apps/ha_smart_hvac` code.  
**4.3 churn:** `test_hvac_app.py` (+233), refactor plan (+179), `test_config.py` (+70), `deferred-work.md` (+9/−18), `hvac_app.py` (+3/−1), `config.py` (+17/−17 net 0).

### Evidence inventory
| Artifact | Available? | Note |
| --- | --- | --- |
| Epic file | yes | R1–R2 + Done when 1–4 declared; Constraints C1/C2/C4/C5/C7 |
| Initiative file | not opened | covers R1/R2 restated on epic (parent R9–R10) |
| Ticket entries | yes | `find` for 4.1–4.3; `story_file` null for all — description/verify on entries |
| Plans | yes | all three `status: done`; frozen Intent + Review Triage + Code Review |
| Diff ranges | yes | three `git_evidence.py` runs; epic code span `9c7bc369..b6286e80` |
| Run folders in epic folder | none | no `<type>-*/` under epic folder |
| Walkthroughs (initiative) | yes | `walkthrough-story-4-1-*`, `4-2-*`, `4-3-*` (+ demos/logs) — outside epic folder |
| Companions | none listed | epic References name parent initiative + forge |
| Previous retrospective | **missing** | previous epic = `epic-supersede-pid-domain-docs` — no `*-retrospective.md` |
| Session logs | partial | walkthroughs + demos exist; full chat logs absent → process-lesson analysis **narrowed** |
| Deferred-work (post-4.3) | yes | Settled epic-4 A–D; remaining: AGENTS/CONTEXT accuracy listen (epic-6); Outdoor-fail event + empty-zone spy defers |

## Findings
`bmad-review` narrowing: adversarial / edge-case / verification-gap over staged diff `9c7bc369..b6286e80` scoped to `apps/`, `apps.yaml.example`, `tests/` (`/tmp/epic4-retro/epic4-code.diff`), ticket boundaries 4.1→4.3. Parent inline pass plus corroboration from [Epic4 adversarial review](e80c8683-140f-447b-82ff-1c63ddc6eb41) and [Epic4 edge+verify lenses](9fe05571-98fb-43f0-838e-b7fc0db8d340); every row below was **re-checked against primary sources** before routing. Agent-only claims that duplicate Intent (mild-overshoot floor, no closure listen, both-keys ConfigError, zone-yaml T vs climate setpoint) were dropped as non-findings. Phase 3: product-team discussion started 2026-11-16 (user: «обсуждение»).

| ID | Finding | Source | Instance disposition | Upstream lesson |
| --- | --- | --- | --- | --- |
| A1 | No new modules; import graph unchanged; `coordinator`/`feedforward` untouched; TRV collocated in `hvac_app` | `git log` empty on those paths; `hvac_app.py` imports vs `9c7bc369` | checked and clean | thin TRV path stayed in App |
| A2 | Dual gate preserved: `_apply_trv_law` before `_gate_prelude` on tick/event; `supply_event` never calls TRV | `hvac_app.py:231-251`, `:160+`; 4.1/4.3 Intent Always | **accept as-is** | document TRV-before-prelude in domain docs (epic 6) |
| A3 | Size growth: `hvac_app.py` 388→449; `test_hvac_app.py` 1663→2207; TRV helpers clustered (`_write_number`, `_apply_trv_law`) | `wc -l` at baseline vs HEAD; git_evidence 4.1/4.3 | **accept as-is** (coherent cluster) | keep TRV next to plant helpers |
| A4 | `_write_number` parallels `_write_setpoint` (equal-float + `number/set_value`) — intentional, not cross-ticket duplication | `hvac_app.py:371-386`, `:426+`; 4.1 Always | **accept as-is** | — |
| A5 | `ThermostatConfig.commissioned` unused by runtime (runtime checks both ids) | `models.py:17-18`; 4.3 Code Map “do not refactor” | **accept as-is** | optional later cleanup |
| S1 | Done when 1–3 / R1–R2: plant-on floor/100/hysteresis; plant-off 100; never `valve_opening_degree`; plain-string no TRV keys — locked in tests + example | epic Done when; `test_trv_*` ~1744–1989; `apps.yaml.example:23-37` | checked and clean | — |
| S2 | Done when 4 house ids: HITL plan + local gitignored yaml; offline `parse_config` OK (floor 80; 4 commissioned; 3 plain) | 4.2 plan Verification; house parse 2026-11-16 | **accept as-is** (HITL + Intent) | — |
| S3 | 4.1 deferred A–D closed in 4.3 (accuracy listen, prelude ACs, goldens, `_entity_id` strip); Settled cites `test_trv_independent_of_heating_demand` | `deferred-work.md` Settled; `e1a3c81`; tests ~1992–2180 | checked and clean | tracer→sweep deferral worked |
| P1 | `control_event` docstring still says “no sticky latch” after trip latch **and** TRV overshoot latch | `hvac_app.py:246`; epic-2 retro action #1 | **fix now** | update docs with runtime latches |
| P2 | AGENTS.md listener inventory omits commissioned `accuracy` `control_event` listen (can re-enter SWT via shared handler); CONTEXT has no TRV soft-close law | `AGENTS.md:36`; `deferred-work.md` 2026-11-16; 4.3 CR defer | **accept as-is → epic 6** | agent-context with product change |
| P3 | Epic-3 deferred bullets still say settle/prune in “entry 4” after 4.3 intentionally left them | `deferred-work.md` top bullets; 4.3 Intent Never | **defer** (PO / docs hygiene) | epic owning deferred must prune its pointers |
| ADV1 | Plant-off writes 100 without clearing `_trv_overshoot_latched` | `hvac_app.py:399-401`; 4.1 triage reject | **accept as-is** (Intent) | — |
| ADV2 | Accuracy listen shares `control_event` → TRV then full Outdoor-gated demand writer | `hvac_app.py:73-74`, `:248-255`; 4.3 Intent | **accept as-is** (shared path); docs → P2 | — |
| ADV3 | TRV latch is RAM-only (lost on AppDaemon reload), same class as supply trip | `hvac_app.py:45`; epic Done when omits persist | **accept as-is** | — |
| ADV4 | `_write_number` returns True after `call_service` without readback (same pattern as plant) | `hvac_app.py:371-386`; 4.1 triage | **accept as-is** | — |
| ADV5 | Unlatched + unreadable accuracy: skip (no floor/100 write) — prior valve may linger | `hvac_app.py:417-419`; matrix Error Handling | **accept as-is** (Intent) | — |
| ADV6 | No dedicated Critical Zone × TRV isolation test (CZ only on demand log path; TRV iterates yaml zones) | C4; `hvac_app.py:274-290` vs `:389+`; no `test_trv_*critical*` | **defer** | thin CZ×TRV non-driver AC optional |
| ADV7 | Latched path shares the same `t_zone`/`setpoint` None→`continue` — no 100 refresh while sensors gap | `hvac_app.py:403-406`; edge/adversarial lenses | **accept as-is** (Intent skip); test → V3 | — |
| ADV8 | `_trip_hold_expired` re-runs prelude+demand only — no `_apply_trv_law` | `hvac_app.py:155-164`; edge lens | **defer → epic 5** (human 2026-11-16) | revisit with flame/trip replacement |
| ADV9 | Supply-trip latched still allows plant-on TRV floor/100 writes on the same tick (TRV before demand zero) | `hvac_app.py:231-233`, `:256-261`; adversarial lens | **accept as-is** (separate concerns; epic Boundaries) | revisit if epic 5 couples flame/TRV |
| ADV10 | `valve_closure_floor: 0` parses; idle path can command full open | `config.py:259-263`; adversarial lens | **accept as-is** (explicit 0..100) | commissioning caution only |
| E1 | Whitespace-only / padded entity ids: strip-then-reject / strip-then-keep — covers prior epic-2 outdoor strip leftover for all `_entity_id` fields | `config.py:118-124`, `:217-224`; `test_parse_rejects_whitespace_*`, `test_parse_strips_padded_*` | checked and clean | — |
| E2 | Floor bounded 0..100 at parse | `config.py:259-263`; config tests | checked and clean | — |
| E3 | Outdoor-fail / empty-zone / sibling own-reads prelude isolation covered on tick; accuracy-event×Outdoor-fail and empty-zone spy strength deferred | tests ~2000–2034; `deferred-work.md` CR defers | **defer** (already filed) | — |
| E4 | No `listen_state` on `valve_closure` — external HA edits wait for tick/other listener | `hvac_app.py:59-74`; 4.3 Never | **accept as-is** (Intent) | — |
| V1 | Exclusive Session / live AppDaemon soft-close unevidenced (unit + offline house only) | walkthroughs; 4.2 Never Exclusive Session | **defer** (open item) | record live pass/fail or waive |
| V2 | Deferred verification: accuracy `control_event` + Outdoor-fail; empty-zone spy-only | `deferred-work.md`; 4.3 CR | **defer** | — |
| V3 | No test: latched + unreadable zone/setpoint keeps latch without refresh | ADV7; tests cover accuracy-unavailable latched only (~1958–1966) | **defer** | pin skip-while-latched |
| V4 | No test: `supply_event` must not call `_apply_trv_law` / write closures | supply tests; edge verification-gap | **defer** | assert no TRV side effects on supply |
| V5 | Outdoor-fail isolation spy does not lock call order before prelude | `test_trv_outdoor_fail_*`; verification-gap | **defer** (overlaps E3/V2) | order assert or shared-path ADR |
| V6 | `test_trv_no_valve_opening_degree_entity_writes` is source substring; runtime entity asserts exist elsewhere | `tests/test_hvac_app.py:1987+`; 4.1 triage | **accept as-is** (belt + entity filters) | — |
| PROC1 | Previous epic (`epic-supersede-pid-domain-docs`) has no retrospective file | inventory | accept narrowing | run retros before next epic |
| PROC2 | Session/chat logs incomplete → process-lesson analysis narrowed to walkthrough + plan CR | inventory | accept narrowing | — |
| PROC3 | 4.2 house yaml correctly untracked; plan is SoT for commission | 4.2 plan; gitignore | checked and clean | — |

## Behavior verification
| Check | Result |
| --- | --- |
| `uv run pytest` | **335 passed** (2026-11-16) |
| `uv run ruff check apps/ha_smart_hvac tests` | clean |
| House offline `parse_config` | **PASS** — `valve_closure_floor=80`; 4 commissioned Sonoff mappings; bathroom/kitchen/wc plain |
| Exclusive Session / live AppDaemon TRV soft-close | **Not exercised / unevidenced** — narrowed to unit + offline |

## Previous-retro follow-through
Previous epic in order: `epic-supersede-pid-domain-docs` — **no retrospective file**, so no Action items section to follow through. Recorded as missing file (not “no outstanding items”).

Cross-check against nearest prior initiative retro (`epic-supply-rise-rate-trip-retrospective.md`) leftovers that this epic’s ranges could have closed:

| Item (epic-2 wording) | Owner | Landed in epic 4? |
| --- | --- | --- |
| Fix `control_event` docstring “no sticky latch” | Dev | **no evidence found** — still `hvac_app.py:246` (P1) |
| AGENTS/CONTEXT/ADR supersede + delete pid/rls | epic 3 | **out of scope here** — epic 3 work; deferred bullets still stale (P3) |
| Strip/reject whitespace entity ids | Dev | **yes** — `config.py:118-124` + tests in 4.3 (`e1a3c81`) |
| Decide waive vs Exclusive Session live verify | Operator / Dev | **no evidence found** — still open (V1) |

## Action items
Human approved revised set 2026-11-16 (Phase 3 product-team). Remediation/spec items below are **proposed, not applied** by this skill (except decision records written under Decision records).

| # | Item | Owner | Kind |
| --- | --- | --- | --- |
| 1 | Fix `control_event` docstring: remove “no sticky latch”; name supply-trip latched-zero **and** TRV overshoot latch | Dev | Remediation — awaiting apply |
| 2 | Carry-forward: AGENTS/CONTEXT document TRV soft-close + accuracy `control_event` listen | epic 6 | Spec/docs — already in `deferred-work.md` |
| 3 | Prune/rewrite epic-3 deferred bullets that still point at “entry 4” after 4.3 left them | Sofia / docs hygiene | Spec — proposed |
| 4 | Deferred tests (narrowed): V4 supply no-TRV side effects; V3 latched+unread; E3/V2 accuracy×Outdoor-fail / empty-zone spy as already filed. CZ×TRV and order-spy dropped from action list. | Dev | Remediation — deferred |
| 5 | Exclusive Session live TRV soft-close: **waive for this retro** (unit + offline house accepted); optional operator spot-check after AD reload remains informal | Operator / Dev | Process — waived for verdict |
| 6 | ADV8 hold-expiry without `_apply_trv_law` → **defer to epic 5** (`epic-replace-supply-trip-with-flame`) | epic 5 | Carry-forward — human 2026-11-16 |

## Decision records
Human approved package **D1+D2+D4+D5** (skip D3 → AGENTS/C7 / epic 6) 2026-11-16; written:

| Proposal | Plan / commit | Written? |
| --- | --- | --- |
| TRV idle max-close before water `_gate_prelude` | 4.1 Intent; `784fc71` / `b4d7603` | **yes** → `docs/decisions/adr-trv-before-water-prelude.md` |
| Overshoot latch only after successful `_write_number` | 4.1 Intent; same | **yes** → `docs/decisions/adr-trv-write-gated-overshoot-latch.md` |
| Never write `valve_opening_degree` / closure is limit (D3) | 4.1 Never; C7 | **no** — deferred to AGENTS / epic 6 (not ADR) |
| Plant-off writes 100 without clearing overshoot latch | 4.1 triage; Intent | **yes** → `docs/decisions/adr-trv-plant-off-no-latch-clear.md` |
| Accuracy listens on shared `control_event` | 4.3 Intent; `e1a3c81` | **yes** → `docs/decisions/adr-trv-accuracy-shared-control-event.md` |

## Acceptance verdict
**Verdict:** `accepted-with-open-items`  
**Criteria:** declared  
**Human:** confirmed 2026-11-16 (answers: ADR package Winston; revised actions; ADV8 → epic 5).

**Met in evidence:** Done when 1–4 via unit tests (floor/100/hysteresis/plant-off/never-opening/plain-string), example yaml, house offline commission, 4.1 deferred A–D closed in 4.3; all tickets finished; `pending_tickets` empty.

**Open items:** action #1 docstring; #2 epic-6 docs; #3 stale epic-3 deferred pointers; #4 narrowed deferred tests; #6 ADV8 carried to epic 5. Exclusive Session (#5) waived for this verdict.

## Open questions
1. Phase 3 / ADR / actions / ADV8 — **closed** (human 2026-11-16).  
2. Exclusive Session — **waived for retro**; optional informal AD-reload spot-check left to operator.  
3. Epic close — Sofia (`bmad-agent-po`), not this skill.

## Assumptions
_(interactive — omit)_
