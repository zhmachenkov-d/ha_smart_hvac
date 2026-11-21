---
epic: epic-trv-house-idle-soft-close
date: 2026-11-21
verdict: accepted-with-open-items
criteria: declared
headless: false
---

# Retrospective: TRV house-idle soft-close
## Epic summary
**Epic:** `epic-trv-house-idle-soft-close` (id 7) — replace plant-on floor + overshoot soft-close with house-idle floor → hold → 100  
**Folder:** `_bmad-output/initiative-weather-swt-supply-trip/tickets/epic-trv-house-idle-soft-close/`  
**Going-in concerns:** none (user: «yes; no»).  
**Tickets still at `built`:** none.  
**Unfinished (`pending_tickets`):** none — all four tickets `status`/`state` = `done` (7.2 HITL approved 2026-11-21; plan frontmatter restored + `status: done`).  
**Epic Requirements / Done when:** declared in `epic-trv-house-idle-soft-close.md` (R1–R2; Done when 1–5).  
**Phase status:** Phases 1–5 complete. Phase 3 product-team (seeded round). Phase 4 human: actions #1–6 ok; ADR D1+D3 written; verdict `accepted-with-open-items`.

| Ref | Title | Status / state | Covers | Plan |
| --- | --- | --- | --- | --- |
| 7.1 | Tracer: TRV house-idle soft-close | done / done | R1, R2 | `tickets/story-tracer-trv-house-idle-soft-close-plan.md` |
| 7.2 | Commission house apps.yaml for house-idle soft-close | done / done (HITL) | R1, R2 | `tickets/story-commission-house-apps-yaml-for-house-idle-soft-close-plan.md` |
| 7.3 | Docs: amend ADR/CONTEXT/AGENTS/knowledge for house-idle soft-close | done / done | R1, R2 | `tickets/story-docs-amend-adr-context-agents-knowledge-for-house-idle-soft-plan.md` |
| 7.4 | Refactor sweep | done / done | — | `tickets/story-refactor-sweep-plan.md` |

### Plan ranges (baselines oldest → newest)
| Ticket | `baseline_revision` | Range | Notes |
| --- | --- | --- | --- |
| 7.1 | `468ac9fe5aeafedd64cad5fd0c40c849cd796f1a` | `468ac9fe..a6e52d40` | Next recorded baseline = 7.3; range **includes** 7.2 plan/refine commits + releases 3.12.0/3.13.0 + tip commit `a6e52d40` (7.3 refine) |
| 7.2 | **missing** | no VCS range of its own | Plan had no frontmatter until HITL close 2026-11-21; house yaml gitignored — commit/diff evidence **narrowed** (folded into 7.1 range as stories `7.1,7.2`) |
| 7.3 | `a6e52d4084d977ba8bda42b655553b0a53cb3af1` | `a6e52d40..4881d04b` | Docs amend + walkthrough; tip includes 7.4 freeze commit at boundary |
| 7.4 | `4881d04b2df87ea853ba2a1a1e8557bd63708827` | `4881d04b..48b0952c` | Inferred end = epic tip = PR #168 merge (`HEAD` at gather) |

`git_evidence.py`: `468ac9fe..a6e52d40` (`7.1,7.2`), `a6e52d40..4881d04b` (`7.3`), `4881d04b..HEAD` (`7.4`). All three: `merge_count` == `merges_measured`. No `binary_revisions`.

**7.1/7.2 code churn (non-merge `files`, product paths):** `hvac_app.py` (+121/−98), `test_hvac_app.py` (+385/−389), `test_config.py` (+45/−22), `config.py` (+19/−10), `apps.yaml.example` (+3/−2), `models.py` (+3/−3 net 0); plan/ticket markdown dominate net.  
**7.3 churn:** docs/`knowledge` + walkthrough artifacts; plan (+259/−1); no App runtime.  
**7.4 churn:** plan-only settle (+59/−9); empty prune — no product diff.

### Evidence inventory
| Artifact | Available? | Note |
| --- | --- | --- |
| Epic file | yes | R1–R2 + Done when 1–5 declared; Constraints C1/C2/C4/C5/C7 |
| Initiative file | not opened | covers R1/R2 restated on epic (parent R9–R10) |
| Ticket entries | yes | `find` 7.1–7.4; story files present for all |
| Story files | yes | all four under `tickets/` |
| Plans | yes | all `status: done`; 7.1/7.3/7.4 have Intent + Review Triage + Auto Run; 7.2 Intent-contract + Auto Run (frontmatter restored at HITL close) |
| Diff ranges | yes (narrowed for 7.2) | three `git_evidence.py` runs; product span `468ac9fe..HEAD` on apps/example/tests/docs |
| Run folders in epic folder | none | no `<type>-*/` under epic folder |
| Walkthroughs (initiative) | yes | `walkthrough-story-7-3-docs-house-idle-soft-close/` (+ demos/log) — outside epic folder; no 7.1/7.2/7.4 walkthrough folders found |
| Companions | none listed on epic | References name parent initiative + siblings + research |
| Previous retrospective | **missing** | previous epic by order = `epic-docs-trv-flame-water-law` (id 6) — no `*-retrospective.md` (6.3 still unfinished) |
| Session logs | partial | 7.3 walkthrough + demos; full chat logs absent → process-lesson analysis **narrowed** |
| HITL house verify | yes | 2026-11-21 offline `parse_config` script `ok`; owner approve |
| Phase 3 | yes | product-team party (`--party product-team`); seeded round [Epic7 product-team](8f612121-14cc-4508-bad6-b0f50d9820b8) |

## Findings
`bmad-review` narrowing: adversarial / edge-case / verification-gap over staged `/tmp/epic7-retro/epic7-code.diff` (`468ac9fe..HEAD` apps+example+tests+docs). Corroboration: [Epic7 adversarial](91e618df-cef4-40b7-a4b6-908ed081813d), [Epic7 edge-case](8d60e882-0a43-4eec-9192-32073260a89d), [Epic7 verification-gap](f831c3fc-423e-4845-8458-a5f5968b0106). Intent-restating agent rows dropped or **accept as-is** after primary-source re-check. Aggregate views computed inline (import graph + `wc` + Done-when spot `rg`). Phase 3: no new sourced defect; ship-safety rank ADV2 > V1 > P1.

| ID | Finding | Source | Instance disposition | Upstream lesson |
| --- | --- | --- | --- | --- |
| A1 | Import graph unchanged; `coordinator`/`feedforward` untouched | `ast` imports baseline vs HEAD | checked and clean | thin replace in App |
| A2 | Dual gate: `_apply_trv_law` before prelude on tick/event/flame-hold expiry; soft-close hold expiry no prelude; flame observe never TRV | `hvac_app.py:160-170`, `:302+`, `:216-218`, `:235+` | checked and clean | keep TRV-before-prelude + soft-close expiry fence |
| A3 | Size: `hvac_app.py` 491→514; `test_hvac_app.py` 2640→2636 (rewrite); soft-close clustered | `wc -l`; git_evidence | **accept as-is** | keep hold helpers next to flame hold |
| A4 | Soft-close hold mirrors flame token/`run_in`/`cancel_timer` — intentional parallel, not accidental dup | `hvac_app.py:172-186` vs flame hold | **accept as-is** | document parallel pattern |
| S1 | Done when 1–3: floor → hold/demand → 100; plant-off 100; never opening — locked in tests | epic Done when; `test_trv_*`; 77 focused pytest green | checked and clean | — |
| S2 | Done when 4: closure-only; accuracy ConfigError; overshoot retired | `config.py:137-138`; example; 7.4 hygiene `rg` | checked and clean | — |
| S3 | Done when 5 docs: ADR 0008 / CONTEXT / AGENTS / knowledge house-idle | 7.3 plan Auto Run; walkthrough; live `rg` | checked and clean | — |
| S4 | Done when 5 house yaml: HITL offline parse hold 300 / floor 80 / 4 commissioned | 7.2 plan + 2026-11-21 verify | **accept as-is** (HITL) | — |
| S5 | 7.4 empty prune settle — no invent-scope deletes | 7.4 Implementation Notes; plan-only diff | checked and clean | freeze punch-list before sweep |
| P1 | `control_event` docstring still “no sticky latch” (carryover epic-4/5) | `hvac_app.py:317` | **fix now** | update docs with runtime latches |
| P2 | 7.2 plan missing `baseline_revision` (and lacked frontmatter until HITL close) | 7.2 frontmatter; epic-5 action #6 | **accept as-is**; process | require baseline+frontmatter on HITL plans |
| P3 | `set-water-temperature.md` plant-off “TRV soft-close still applies” without hold/cancel detail (7.4 O1) | `knowledge/concepts/set-water-temperature.md:15`; 7.3 reject R1 | **defer** (O1) | companion depth vs live ADR |
| P4 | `docs/house-calibration.md` names TRV anti-cycle but no hold/floor/`accuracy` ConfigError keys | `house-calibration.md:2-6` | **defer** | calibration guide tracks example keys |
| P5 | AGENTS Verified stamp still `2026-11-17` / pre-epic-7 SHA while prose is house-idle | `AGENTS.md` stamp; 7.3 Never bump | **accept as-is** (Intent) | stamp bump is separate chore |
| ADV1 | Soft-close demand via `_any_climate_heating` (hvac_action) while SWT uses `_read_zones` — intentional F1 | `hvac_app.py:188-198`, `:461-477`; 7.1 Code Review F1 | **accept as-is** (ADR D1 written) | — |
| ADV2 | Partial hold-expiry success → episode `None` → next tick can re-floor TRVs already at 100 | `hvac_app.py:228-233`, `:480-489`; 7.1 residual Auto Run | **defer** | pin second-tick behavior or all-or-nothing expiry |
| ADV3 | Idle episode / soft-close hold RAM-only (lost on AppDaemon reload) | `hvac_app.py:45-47` | **accept as-is** (same class as flame) | — |
| ADV4 | No upper bound on `trv_soft_close_hold_s` (unlike control_interval) | `config.py` hold parse | **accept as-is** | commissioning caution |
| ADV5 | Flame-latched + house-idle still floors/arms soft-close | `hvac_app.py:461+`; tests idle-while-latched | **accept as-is** (separate concerns) | — |
| ADV6 | Demand/plant-off discard write `all_ok` (no retry loop) | `hvac_app.py:466-477` | **accept as-is** (Intent throttle) | — |
| E1 | Orphan/token-mismatch expiry returns without clearing `holding` if cancel_timer fails while still idle | `hvac_app.py:216-219`; edge lens | **defer** | clear episode on orphan or assert handle after mismatch |
| E2 | Multi-TRV partial floor: no arm; retry each tick — write-gated by Intent | `hvac_app.py:483-489`; tests cover expiry partial only | **defer** (test) | add partial-floor multi-TRV test |
| E3 | `closed_idle` / `holding` early-return: no re-assert if HA edits closure out of band | `hvac_app.py:480-481` | **accept as-is** (Intent) | — |
| E4 | Unavailable `hvac_action` treated as non-heating for soft-close | `hvac_app.py:196-197` | **accept as-is** | optional unavailable→fail-closed later |
| V1 | Exclusive Session / live AppDaemon soft-close unevidenced | 7.2 Never Exclusive Session; no run folder | **defer** (open item) | record live pass/fail or waive |
| V2 | House yaml not in CI (example-only + HITL) | `test_dual_layout`; 7.2 | **accept as-is** | — |
| V3 | Soft-close hold expiry: no `_gate_prelude`/`_run_demand` spy (proxy = no plant write) | tests hold-expiry | **defer** | strengthen oracle like flame |
| V4 | Flame/`ch_active` observe: no negative `_apply_trv_law` spy | flame tests | **defer** | negative dual-gate assert |
| V5 | Flame-hold expiry × house-idle episode (`holding`/`closed_idle`) lightly covered | ADV8 tests use heating TRV | **defer** | idle-episode on flame-hold expiry |

## Behavior verification
**Unit:** 77 focused `trv|soft_close|accuracy|valve_closure|hold` pytest green (2026-11-21). Full suite cited in plans: 365–370 passed during builds.

**Offline house:** 2026-11-21 `parse_config` → hold 300, floor 80.0, 4 commissioned; accuracy re-insert ConfigError; gitignore OK. Owner HITL **approve**.

**Exclusive Session / live AppDaemon:** **not exercised** this epic (7.2 config-only). Recorded as V1 open item — not a silent pass.

## Previous-retro follow-through
Previous epic by order = `epic-docs-trv-flame-water-law` — **no retrospective file** → nothing formal to follow through (missing file, not “no outstanding items”).

Contextual check against epic-5 action items (not formal previous):

| Item (epic-5) | Owner | Landed? |
| --- | --- | --- |
| #1 docstring “no sticky latch” | Dev | **no** — still `hvac_app.py:317` (P1) |
| #2 AGENTS/CONTEXT/ADR → flame + TRV | epic 6 | **partial** — epic 7.3 rewrote TRV soft-close to house-idle; flame docs owned by epic 6 |
| #6 Require `baseline_revision` on HITL plans | Sofia / build | **no** — 7.2 gap recurred (P2) |

## Action items
Human approved set 2026-11-21 (user: «2. ok»). Remediation/spec items **proposed, not applied** by this skill (except decision records written).

| # | Item | Owner | Kind |
| --- | --- | --- | --- |
| 1 | Fix `control_event` docstring: remove “no sticky latch”; name flame latched-zero **and** TRV soft-close hold/episode | Dev | Remediation — proposed |
| 2 | Require plan YAML frontmatter + `baseline_revision` on HITL commission stories before mark-done | Sofia / build | Process — proposed |
| 3 | Deferred tests: V3 prelude spy on soft-close expiry; V4 flame no-TRV spy; E2 partial floor; ADV2 second-tick after partial expiry; E1 orphan episode; V5 flame-hold×idle | Dev | Remediation — deferred |
| 4 | Docs hygiene: P3 `set-water-temperature.md` hold-cancel; P4 `house-calibration.md` hold/floor/accuracy | Sofia / docs | Spec — deferred |
| 5 | Exclusive Session soft-close spot-check or explicit waive | Operator / Dev | Process — open |
| 6 | Optional: ADV2 harden multi-TRV expiry (all-or-nothing or no re-floor of already-100) | Dev | Remediation — deferred |

Phase 3 ship-safety rank for open items: **ADV2 > V1 > P1**.

## Decision records
Human approved **D1 + D3** 2026-11-21 (user: «3. yes»); written:

| Proposal | Plan / commit | Written? |
| --- | --- | --- |
| D1 Soft-close Heating Demand = climate `hvac_action` probe (not `_read_zones`) | 7.1 F1; `90dcc7a` | **yes** → `docs/decisions/adr-trv-soft-close-demand-hvac-action.md` |
| D2 Soft-close hold expiry = closure 100 only (no Outdoor prelude/SWT) | 7.1 Intent; ADR 0008 | **skipped** — already in ADR 0008 |
| D3 Write-gated floor/arm + `closed_idle` only when all commissioned writes succeed | 7.1 F2/F3; `90dcc7a` | **yes** → `docs/decisions/adr-trv-soft-close-write-gated-episode.md` |
| D4 Idle episode `none` → `holding` → `closed_idle` | 7.1 Implementation Notes; ADR 0008 | **skipped** — ADR 0008 prose |
| D5 Leftover yaml `accuracy` → ConfigError | 7.1 Intent; ADR 0008 | **skipped** — ADR 0008 |

## Acceptance verdict
**Verdict:** `accepted-with-open-items`  
**Criteria:** declared  
**Human:** confirmed 2026-11-21 (recommended machine lean; actions ok; ADR D1+D3; Phase 3 yes).

**Evidence:** Done when 1–5 met via unit tests (S1–S2), offline HITL house commission (S4), and live docs/knowledge amend (S3); 7.4 empty prune settled (S5). Open tracked items: P1 docstring fix-now; ADV2/V1/E*/V3–V5 deferred; Exclusive Session unevidenced (V1). `pending_tickets` empty — machine not forced to rejected.

## Open questions
- Whether to waive or schedule Exclusive Session soft-close spot-check (action #5) before closing the initiative.
- Whether ADV2 hardening (#6) becomes a follow-on ticket or stays deferred residual.
