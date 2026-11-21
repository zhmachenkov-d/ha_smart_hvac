---
id: 4
type: story
title: "Refactor sweep"
parent: epic-trv-house-idle-soft-close
covers: []
after: [1, 2, 3]
hitl: false
risk: low
refined: true
---

# Refactor sweep
## Description
Close epic-7 deferred cleanup using the frozen punch-list below: the prune set is empty after 7.1–7.3 (no dead overshoot/accuracy soft-close helpers left in the live App/tests/docs tree). Record that settle, keep the named live-contract and Historical guards, and leave out-of-scope items untouched. No new product laws; leave epic-6.3 CAP-8 hygiene to that story.

1. Freezes scope before `bmad-build-auto` so the agent does not invent prune targets.
2. Settles the empty epic-7 deferred prune set with hygiene evidence (not a silent no-op).
3. Protects live ConfigError/`accuracy` contract tests and Historical overshoot/accuracy decision records.
4. Keeps 7.3 residuals and 6.3 CAP-8 work out of this sweep.

## Requirements
1. **Punch-list P — prune (empty settle)** 
   **Given** `apps/ha_smart_hvac/`, `tests/`, and live soft-close docs paths after 7.1–7.3
   **When** the start-of-work inventory runs
   **Then** there are **no** deferred dead overshoot/accuracy soft-close helpers or obsolete overshoot soft-close test suites to delete
   **And** the plan records **Settled — empty prune set** with the hygiene `rg` evidence below (do not invent deletes to look busy)
   **Failure:** agent deletes live ConfigError paths, contract tests, Historical decision bodies, or other keep-listed items

2. **Punch-list K — keep (do not touch)** 
   **Given** the keep list K1–K4
   **When** the sweep runs
   **Then** all keep items remain byte-stable in intent (no “cleanup” edits):
   - **K1:** `config.py` leftover-`accuracy` → `ConfigError` and tests `test_parse_rejects_trv_accuracy_in_mapping`, `test_initialize_trv_no_accuracy_listen`
   - **K2:** Historical banners **and** bodies of `docs/decisions/adr-trv-write-gated-overshoot-latch.md`, `adr-trv-plant-off-no-latch-clear.md`, `adr-trv-accuracy-shared-control-event.md`
   - **K3:** Live house-idle soft-close App path (`_apply_trv_law`, `_arm_trv_soft_close_hold` / disarm / expiry token)
   - **K4:** Live ADR 0008 / CONTEXT / AGENTS `bmad:context` / `knowledge/concepts/trv-soft-close.md` (+ index / outdoor) house-idle teaching from 7.3
   **Failure:** keep item rewritten, deleted, or “simplified” as obsolete

3. **Punch-list O — out of scope** 
   **Given** the out-of-scope list O1–O5
   **When** the sweep runs
   **Then** none of these are edited:
   - **O1:** `knowledge/concepts/set-water-temperature.md` plant-off soft-close “still applies” residual (rejected from 7.3 Notes matrix; not overshoot teaching; not deferred prune)
   - **O2:** epic-6.3 CAP-8 hygiene and deferred G–H prelude-isolation test gaps
   - **O3:** gitignored house `apps/apps.yaml` and `apps/apps.yaml.pre-*` backups (incl. old “closure/accuracy” header comments)
   - **O4:** AGENTS Verified stamp bump; new product laws; Exclusive Session / `run-appdaemon`
   - **O5:** `_bmad-output/` walkthrough / demo transcripts as process evidence
   **Failure:** sweep amends O1–O5 under a cleanup rationale

4. **Hygiene + suite verify** 
   **Given** the punch-list above
   **When** verify runs
   **Then** `rg` on the live soft-close path set shows no `_trv_overshoot_latched` / live overshoot-latch / commissioned-accuracy-listen teaching (Historical decision files are outside that path set)
   **And** `uv run pytest` and `uv run ruff check apps/ha_smart_hvac tests` are clean
   **And** App `rg '_trv_overshoot'` under `apps/ha_smart_hvac` is empty
   **Failure:** live-law overshoot/accuracy soft-close hits remain, or suite/ruff fails

## Boundaries
- Owns: epic-7 closing sweep punch-list freeze + empty-prune settle + keep/out guards + verify.
- Does not own: new soft-close product law; 7.3 live-pointer corrections already done; house yaml; epic-6.3 CAP-8.
- Must not: invent prune targets; touch K1–K4 or O1–O5; restore overshoot/accuracy as live soft-close.

## References
- parent — `_bmad-output/initiative-weather-swt-supply-trip/tickets/epic-trv-house-idle-soft-close/epic-trv-house-idle-soft-close.md`
- prerequisite — entries 1–3 plans `status: done` (tracer / house yaml / docs amend)
- sibling pattern — `_bmad-output/initiative-weather-swt-supply-trip/tickets/epic-trv-idle-max-close/tickets/story-refactor-sweep-plan.md` (deferred punch-list then prune)
- pre-build review — chat review 2026-11-21 (empty deferred sources; invent-scope risk)

## Notes
- Decision: Punch-list frozen 2026-11-21 from start-of-work inventory — **P empty**; **K1–K4 keep**; **O1–O5 out** (path 1 before bmad-build-auto).
- Decision: 7.3 owns live-pointer safety; 7.4 owns deferred prune only — with empty deferred arrays in 7.1–7.3 plans and no epic-7 bullets in `_bmad-output/deferred-work.md`, settle is verify+record, not code delete.
- `covers = []` stays empty (no new R*); punch-list IDs P/K/O are the scope anchors.
- Risk reason: invent-scope deletes against keep list; mitigated by frozen punch-list + hitl=false only after this freeze.
