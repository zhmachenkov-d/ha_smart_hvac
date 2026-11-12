---
epic: epic-weather-curve-swt-restore
date: 2026-11-12
verdict: accepted-with-open-items
criteria: declared
headless: false
---

# Retrospective: epic-weather-curve-swt-restore

## Epic summary

**Epic:** `epic-weather-curve-swt-restore` (id 1) — Weather-curve SWT restore  
**Folder:** `_bmad-output/initiative-weather-swt-supply-trip/tickets/epic-weather-curve-swt-restore/`  
**Going-in concerns:** none (user: «без акцентов»).  
**Tickets still at `built`:** none.  
**Unfinished (`pending_tickets`):** none — all four tickets `status`/`state` = `done`.  
**Phase 4 human decisions (2026-11-12):** machine verdict accepted; action items = recommended set; decision records = recommended three written; open Q2 = reconcile epic R2/R3 **now** (action for Sofia; epic file not edited by this skill).

| Ref | Title | Status / state | Covers | Plan |
| --- | --- | --- | --- | --- |
| 1.1 | Tracer: weather-curve SWT law | done / done | R1, R2, R3, R7, R8 | `tickets/story-tracer-weather-curve-swt-law-plan.md` |
| 1.2 | Detach PID/RLS from live SWT and example commissioning | done / done | R4 | `tickets/story-detach-pid-rls-from-live-swt-and-example-commissioning-plan.md` |
| 1.3 | Commission house apps.yaml for weather FF | done / done (HITL) | R7 | `tickets/story-commission-house-apps-yaml-for-weather-ff-plan.md` |
| 1.4 | Refactor sweep | done / done | — | `tickets/story-refactor-sweep-plan.md` |

### Plan ranges (baselines oldest → newest)

| Ticket | `baseline_revision` | Range | Notes |
| --- | --- | --- | --- |
| 1.1 | `6cd2b2d7efbc0bb294464a5aff0cc69a9257fa96` | `6cd2b2d7..4d921dd2` | Next baseline = 1.2 |
| 1.2 | `4d921dd2f68ccd9ef4223148abd37e16b9d50a48` | `4d921dd2..63c38441` | Includes mark-1.1-done + detach feat |
| 1.3 | `63c38441661e4ec94a93e5dc040705f58f94cddc` | `63c38441..ba82eaed` | Plan + mark-done only in git |
| 1.4 | `ba82eaed79f868626ebf05ad0b6cc047e197dbd2` | `ba82eaed..ba1004cc` | Cut at last epic commit (= HEAD at inventory) |

`git_evidence.py` run once per distinct range with matching `--stories`. `merge_count` == `merges_measured` on all four; no binary churn gaps reported.

**1.1:** `test_hvac_app.py` (−1378), plan (+147), `config.py` (+38), `hvac_app.py` (−51), `feedforward.py` (+10), `apps.yaml.example` (+8).  
**1.2:** `test_hvac_app` (−327), `test_config` (−243), `hvac_app.py` (−239), `config.py` (−122), detach plan (+147).  
**1.3:** commission plan only (+141); house yaml gitignored.  
**1.4:** refactor plan (+176), house-calibration rewrite, `deferred-work.md` (−4).

### Evidence inventory

| Artifact | Available? | Note |
| --- | --- | --- |
| Epic file | yes | Requirements + Done when declared |
| Ticket entries / plans | yes | 1.1–1.4; `story_file` null |
| Diff ranges | yes | four `git_evidence.py` runs |
| Run folders / companions | none | — |
| Previous retrospective | none | first epic |
| Session logs | partial | process-lesson analysis skipped |

## Findings

`bmad-review` narrowing: adversarial / edge-case-hunter / verification-gap on `6cd2b2d7..ba1004cc` scoped to `apps/`, `apps.yaml.example`, `tests/`, `docs/`, `README.md`. Edge-case-hunter `[]`. Plan-locked adversarial surfaces → accept as-is.

| ID | Finding | Source | Instance disposition | Upstream lesson |
| --- | --- | --- | --- | --- |
| A1 | Live path → `feedforward`; `pid`/`rls` on disk for epic 3 | `hvac_app.py:9-12`; plans; Boundaries | accept as-is | path-vs-delete split worked |
| A2 | App/tests shrank (531→241; 2629→924) | `wc -l` / git_evidence | checked and clean | — |
| D1 | Single clamp/quantize in feedforward | `rg` | checked and clean | — |
| G1 | Top churn = net deletes | git_evidence | checked and clean | — |
| P1 | CAP-8 vs AGENTS sticky-latch prose | `hvac_app.py:96-110`; AGENTS; deferred-work | accept as-is → epic 3 | AGENTS lag is agent hazard |
| P2 | House FF 30/1.0 vs example 37/0.9 (HITL S2) | 1.3 plan; house parse | accept as-is | surface pin risk in HITL |
| S1 | Epic R2/R3 “clear ephemeral” vs vacuous clear (F1-A) | epic R2/R3; 1.2 F1-A | **fix now** (Sofia reconcile) | update epic when mechanism vacated |
| S2 | R4 docs/ADR → epic 3 | deferred-work.md | accept as-is → epic 3 | — |
| S3 | R7 supply → epic 2 | epic Notes | accept as-is → epic 2 | — |
| S4 | R1 latch → epic 2 | epic Notes | accept as-is → epic 2 | — |
| S5 | AGENTS/CONTEXT still PID | AGENTS; CONTEXT; deferred-work | accept as-is → epic 3 | — |
| ADV1 | No `.strip()` on outdoor entity id | `config.py:185-186` | defer | strip all entity ids |
| E1 | Edge lens clean | `[]` | checked and clean | — |
| V1 | Listener test membership-only | `tests/test_hvac_app.py:915-924` | defer | keep full listener golden |
| V2 | F6-B AST-only re-export lock | `tests/test_hvac_app.py:255` | defer | pair AST with hasattr |
| PROC1 | Session logs skipped | inventory | accept narrowing | — |
| PROC2 | Mark-1.1-done in 1.2 range | git_evidence 1.2 | accept as-is | mark-done nearer merge |
| PROC3 | Plan checkboxes lag status | review triage | accept as-is | frontmatter SoT |
| PROC4 | Exclusive Session unevidenced | 1.1 Manual verify | defer (open item) | record live pass/fail or waive |

## Behavior verification

| Check | Result |
| --- | --- |
| `uv run pytest` | 294 passed (2026-11-12) |
| `uv run ruff check apps/ha_smart_hvac tests` | clean |
| House offline `parse_config` | PASS — Outdoor; FF 30/1.0/20; `ignored_keys=('boiler_water',)` |
| Exclusive Session / live AppDaemon E2E | **Not exercised / unevidenced** — narrowed to unit + offline |

## Previous-retro follow-through

No previous epic retrospective file in this initiative (first epic). Nothing to follow through on — missing file, not “no outstanding items.”

## Action items

| # | Item | Owner | Kind |
| --- | --- | --- | --- |
| 1 | Reconcile epic R2/R3 “clear ephemeral / water-path state” with vacuous clear after 1.2 (or point at trip-state epic 2) — **do now** | Sofia (`bmad-agent-po`) | Spec reconciliation — **proposed, not applied** (this skill does not edit the epic file) |
| 2 | Carry-forward: AGENTS/CONTEXT/ADR supersede + delete `pid.py`/`rls.py` | epic 3 | Already in `deferred-work.md` |
| 3 | Carry-forward: supply entity commission + rise-rate latch | epic 2 | Epic Notes / shared covers |
| 4 | Harden `test_initialize_registers_outdoor_listener` (full CAP-8 set + `control_event` callback) | Dev | Remediation — deferred |
| 5 | Optional F6-B runtime `hasattr` lock (or drop when pid deleted) | Dev | Remediation — deferred |
| 6 | Strip/reject whitespace `outdoor_temperature` | Dev | Remediation — deferred |
| 7 | Decide waive vs run Exclusive Session live verify for Outdoor-driven SWT; record result | Operator / Dev | Process — open |

## Decision records

| Proposal | Plan / commit | Written? |
| --- | --- | --- |
| CAP-8 shared FF writer, no sticky latch | 1.1 Intent CAP-8; `17d4960e` / `75cae7cf` | **yes** → `docs/decisions/adr-cap8-shared-ff-demand-writer.md` |
| Outdoor unavailable → `_go_idle` write 0 | 1.1 Outdoor-fail A; same commits | **yes** → `docs/decisions/adr-outdoor-unavailable-idle-zero.md` (ADR 0004 mentions missing-outdoor clear but is superseded and does not spell write-0) |
| Vacuous clear after PID detach | 1.2 F1-A; `a5f49190` / `d5e0a0f4` | **yes** → `docs/decisions/adr-vacuous-clear-after-pid-detach.md` |
| House HITL S2 coeffs | 1.3 | **not proposed** (house-local; fails ADR test) |

## Acceptance verdict

**Verdict:** `accepted-with-open-items`  
**Criteria:** declared  
**Human:** confirmed machine draft 2026-11-12.

**Met in evidence:** Done when 1–6 via unit tests, example FF commission, house offline parse, CZ diagnostics-only, CAP-7 absent, PID/RLS off live path; all tickets finished.

**Open items:** action #1 (Sofia reconcile now); #2–3 epic 2/3 carry-forward; #4–6 deferred remediations; #7 Exclusive Session unevidenced; findings S2–S5/P1 accept→later epics.

## Open questions

1. Exclusive Session after 1.1/1.2 — **unanswered**; remains action #7 / PROC4.  
2. Reconcile epic R2/R3 clear — **now** (action #1).  
3. House base=30 pin — **unanswered**; left as accepted HITL (P2) unless operator retunes.

## Assumptions

_(interactive run — omit)_
