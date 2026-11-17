---
epic: epic-replace-supply-trip-with-flame
date: 2026-11-17
verdict: accepted-with-open-items
criteria: declared
headless: false
---

# Retrospective: Replace supply trip with flame short-on
## Epic summary
**Epic:** `epic-replace-supply-trip-with-flame` (id 5) — replace supply rise-rate trip with flame short-on  
**Folder:** `_bmad-output/initiative-weather-swt-supply-trip/tickets/epic-replace-supply-trip-with-flame/`  
**Going-in concerns:** none (user: «let's go»).  
**Tickets still at `built`:** none.  
**Unfinished (`pending_tickets`):** none — all three tickets `status`/`state` = `done`.  
**Epic Requirements / Done when:** declared in `epic-replace-supply-trip-with-flame.md` (R1–R3; Done when 1–5).  
**Phase status:** Phases 1–5 complete. Phase 3 product-team: A+B locked; Exclusive Session spot-check PASS; ADR D1–D4 written. Phase 4 human: verdict `accepted-with-open-items`.

| Ref | Title | Status / state | Covers | Plan |
| --- | --- | --- | --- | --- |
| 5.1 | Tracer: replace supply trip with flame short-on | done / done | R1, R2, R3 | `tickets/story-tracer-replace-supply-trip-with-flame-short-on-plan.md` |
| 5.2 | Commission house apps.yaml for flame short-on | done / done (HITL) | R1 | `tickets/story-commission-house-apps-yaml-for-flame-short-on-plan.md` |
| 5.3 | Refactor sweep | done / done | — | `tickets/story-refactor-sweep-plan.md` |

### Plan ranges (baselines oldest → newest)
| Ticket | `baseline_revision` | Range | Notes |
| --- | --- | --- | --- |
| 5.1 | `b9352a3cc9cd3fd3b887560a729da12a970cdffb` | `b9352a3..e8798ff` | Next recorded baseline = 5.3; range **includes** 5.2 walkthrough/plan commits and unrelated `#153` bmad-fold churn |
| 5.2 | **missing** | no VCS range | Plan has `status: done` but no `baseline_revision` — commit/diff evidence **narrowed** |
| 5.3 | `e8798fff5909d165d7ce7e64f489c363538ef5a1` | `e8798ff..9809460` | Inferred end = `HEAD` = PR #154 merge |

`git_evidence.py`: `b9352a3..e8798ff` (`5.1,5.2`), `e8798ff..HEAD` (`5.3`). Both: `merge_count` == `merges_measured`. No `binary_revisions`.

### Evidence inventory
| Artifact | Available? | Note |
| --- | --- | --- |
| Epic file | yes | R1–R3 + Done when 1–5 |
| Ticket entries / plans | yes | all `done`; 5.2 missing `baseline_revision` |
| Diff ranges | yes (narrowed for 5.2) | two `git_evidence.py` runs |
| Walkthroughs | yes | 5.1, 5.2; no 5.3 walkthrough folder |
| Previous retrospective | yes | epic-4; ADV8 → epic 5 |
| Exclusive Session spot-check | yes | `exclusive-session-epic-5-flame-spot-check/` (2026-11-17) |
| Session logs | partial | walkthroughs + spot-check; full chat absent → process lessons **narrowed** |

## Findings
`bmad-review` narrowing: adversarial / edge-case / verification-gap over `/tmp/epic5-retro/epic5-code.diff` (`b9352a3..HEAD` apps+tests). Corroboration: [Epic5 adversarial](c71f02b9-3a90-412c-a3e0-28cf507facc9), [Epic5 edge-case](d51c45d9-3b70-4824-94a1-f2ae75203d48), [Epic5 verification-gap](122465b1-0928-4ee6-ac31-b8ce04d777f7). Intent-restating agent rows dropped or **accept as-is**. Phase 3 product-team 2026-11-17.

| ID | Finding | Source | Instance disposition | Upstream lesson |
| --- | --- | --- | --- | --- |
| A1 | Import graph unchanged; coordinator/feedforward untouched | `ast` imports `b9352a3` vs `HEAD` | checked and clean | thin replace in App |
| A2 | Supply path deleted; flame observe gate never Outdoor | App/example `rg`; `hvac_app.py:133-145` | checked and clean | dual-gate: Outdoor vs flame/`ch_active` |
| A3 | `hvac_app.py` 449→457; `test_hvac_app.py` 2207→2569 | `wc -l`; git_evidence | **accept as-is** | keep flame next to plant helpers |
| A4 | 5.3 tests+deferred only; no product-law churn | 5.3 `files` | checked and clean | tracer→sweep deferral worked |
| S1–S4 | Done when 1–5: remove+flame+clears+ADV8+TRV-while-latched+house+tests | App/example; tests; house parse; Settled deferred | checked and clean | — |
| P1 | `control_event` docstring still “no sticky latch” | `hvac_app.py:254`; epic-4 #1 | **fix now** | update docs with runtime latches |
| P2 | AGENTS/CONTEXT/ADR 0007 still supply-trip law | `AGENTS.md`; `CONTEXT.md`; Boundaries → epic 6 | **accept as-is → epic 6 ticket 1** (Phase 3 B) | agent-context with product change |
| P3 | Stale epic-3 “entry 4” deferred bullets | `deferred-work.md` | **defer** | prune pointers |
| P4 | 5.2 plan missing `baseline_revision` | 5.2 frontmatter | **accept as-is**; process #6 | require baseline on HITL plans |
| ADV1–ADV7, ADV9, E1–E3 | Intent-aligned edges (TRV while latched, clears, RAM-only, equal-float, etc.) | Intent + tests | **accept as-is** / checked | — |
| ADV8 | Hold-expiry `_apply_trv_law` then prelude | `hvac_app.py:160-170`; tests | checked and clean | epic-4 ADV8 closed |
| E4 | Transient empty zones at fall miss trip | `hvac_app.py:142-145` | **defer** | optional last-known demand |
| V1 | Exclusive Session flame spot-check | `exclusive-session-epic-5-flame-spot-check/` | **checked** (API-forced gate; PASS) | — |
| V2–V4 | Deferred spies / outdoor-miss hold / AST lock | verification-gap | **defer** | — |
| V5 | House yaml not in CI | 5.2 HITL | **accept as-is** | — |

## Behavior verification
**Unit:** 64 focused flame/latch/hold/TRV-while-latched pytest green (2026-11-17). Offline house `parse_config` OK (confirmed flame entities, 300/900, no trip keys).

**Exclusive Session (2026-11-17):** Local AD initialized; API-forced bathroom heating + `ch_active`; short `flame_on` (~11s) → log latch + SWT `0.0`; outdoor poke kept `0.0`; plant-off → `Plant Management disabled`. Artifact: `_bmad-output/initiative-weather-swt-supply-trip/exclusive-session-epic-5-flame-spot-check/`. Not claimed: natural bridge flame cycle; live 900s ADV8 hold-expiry.

## Previous-retro follow-through
| Item (epic-4) | Owner | Landed? |
| --- | --- | --- |
| #1 docstring “no sticky latch” | Dev | **no** — still `hvac_app.py:254` (P1) |
| #2 AGENTS/CONTEXT TRV+accuracy | epic 6 | **out of scope** — reinforced as epic-6 ticket 1 with flame supersede (P2) |
| #3 epic-3 deferred “entry 4” | Sofia | **no evidence found** (P3) |
| #4 deferred TRV tests | Dev | **partial** — supply V4 moot; others out of Boundaries |
| #5 Exclusive Session TRV waived | Operator | **n/a** — flame spot-check **done** this retro (V1) |
| #6 ADV8 → epic 5 | epic 5 | **yes** — code + tests + ADR D2 |

## Action items
Human approved set 2026-11-17; Phase 3 revised #2/#5 (A+B). Remediation/spec items **proposed, not applied** by this skill (except decision records written).

| # | Item | Owner | Kind |
| --- | --- | --- | --- |
| 1 | Fix `control_event` docstring: remove “no sticky latch”; name flame latched-zero **and** TRV overshoot latch | Dev | Remediation — proposed |
| 2 | Epic 6 **ticket 1**: supersede AGENTS/CONTEXT/ADR 0007 (+ zombie supply `docs/decisions/*`) to flame short-on + TRV soft-close — before other docs polish | Sofia / epic 6 | Spec/docs — Phase 3 B |
| 3 | Prune/rewrite stale epic-3 deferred “entry 4” bullets | Sofia / docs hygiene | Spec — proposed |
| 4 | Deferred tests: V2 flame/`ch_active` no-TRV spy; V3 hold-expiry×Outdoor-unavailable; optional V4 supply AST lock; E4 last-known demand | Dev | Remediation — deferred |
| 5 | Exclusive Session flame spot-check — **done** 2026-11-17 (API-forced); optional natural-bridge cycle remains informal | Operator / Dev | Process — completed for verdict |
| 6 | Require `baseline_revision` on HITL commission plans (5.2 gap) | Sofia / build | Process — proposed |

## Decision records
Human approved **D1–D4** 2026-11-17; written:

| Proposal | Plan / commit | Written? |
| --- | --- | --- |
| D1 Flame observe gate never Outdoor | 5.1 Intent; `918debc` | **yes** → `docs/decisions/adr-flame-observe-gate-no-outdoor.md` |
| D2 ADV8 hold expiry = TRV then Outdoor prelude | 5.1 / epic-4 ADV8; `918debc` / `202389c` | **yes** → `docs/decisions/adr-flame-hold-expiry-trv-then-prelude.md` |
| D3 Latch only after SWT 0 write + hold scheduled | 5.1; `918debc` / `02bc705` | **yes** → `docs/decisions/adr-write-gated-flame-latch.md` |
| D4 Flame latch RAM-only; no observer re-assert | 5.1 Never; `918debc` | **yes** → `docs/decisions/adr-flame-latch-ram-only-no-reassert.md` |
| D5 Decision C / plant-off rename | existing supply ADRs | **skipped** — supersede in epic 6 |

## Acceptance verdict
**Verdict:** `accepted-with-open-items`  
**Criteria:** declared  
**Human:** confirmed 2026-11-17 (accept; actions ok; ADR D1–D4; Phase 3 A+B; Exclusive Session before finalize).

**Met in evidence:** Done when 1–5 via unit tests, example, house offline commission, Exclusive Session API-forced latch/clear; all tickets finished; ADV8 from epic 4 closed; D1–D4 recorded.

**Open items:** action #1 docstring; #2 epic-6 ticket-1 docs supersede; #3 deferred hygiene; #4 deferred tests; #6 HITL baseline process.

## Open questions
1. Phase 3 A+B / Exclusive Session / ADR / verdict — **closed** (human 2026-11-17).  
2. Natural OpenTherm flame cycle — optional informal; not required for this verdict.  
3. Epic close — Sofia (`bmad-agent-po`), not this skill.  
4. **Operator:** restart Production AppDaemon add-on (Exclusive Session teardown).
