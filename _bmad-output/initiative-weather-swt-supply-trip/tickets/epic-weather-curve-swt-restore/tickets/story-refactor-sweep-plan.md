---
title: 'Refactor sweep'
status: built
ticket: '4'
route: full
route_source: auto
review: 'thorough'
review_source: 'auto'
risk: low
date: '2026-11-12'
baseline_revision: ba82eaed79f868626ebf05ad0b6cc047e197dbd2
lenses_ran: ['blind-hunter', 'edge-case-hunter', 'verification-gap', 'intent-alignment']
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent
**Problem:** After stories 1.1–1.3, deferred notes still leave stale ticket `verify` prose naming the PID integral (∫) on the detached path. Operator calibration docs still describe fixed-PID commissioning while the live App and `apps.yaml.example` are Outdoor temperature + weather feedforward (`weather_feedforward`) only — shorthand **Outdoor+FF** below.

**Approach:** Close epic 1 story 1.4 (entry `id=4`) deferred items: rewrite entry `id=1`/`id=2` ticket surfaces to the shipped FF path locks, remove the settled deferred-work bullet, and retarget `docs/house-calibration.md` + README Install/Layout to Outdoor+FF. Do not touch AGENTS/CONTEXT/ADR or delete `pid.py`/`rls.py` (epic 3). Until epic 3, rewritten operator docs plus `apps.yaml.example` are the commissioning source of truth; do not cite AGENTS, CONTEXT, ADR 0005/0006, or `knowledge/` as live water law.

**Decisions:**
- OQ1-A: Rewrite `docs/house-calibration.md` and README Install/Layout to Outdoor+FF aligned with `apps.yaml.example`.
- OQ2-A: Same tickets touch — scrub entry `id=1` description/`verify`/`notes`; rewrite entry `id=2` `verify` to F5-A + F7-A + F6-B (exact strings in Design Notes).
- Review apply-all (2026-11-12): embed canonical verify text; entry-1 scrub allowlist; house-calibration section inventory + domain-docs-lag note; explicit deferred-work bullet ownership; named proof tests; structure cleanup.

## Boundaries & Constraints
**Always:**
- Scope = story 1.4 only: deferred findings + orphans from the weather-curve restore; no new product behavior.
- Apply the exact entry `id=2` `verify` and entry `id=1` scrub rules in Design Notes.
- Retarget house-calibration + README per the section inventory in Design Notes; copy FF/rails numerics from `apps.yaml.example` (do not invent house-specific numbers — house yaml may differ after story 1.3).
- Keep `uv run pytest` and `uv run ruff check apps/ha_smart_hvac tests` green (canonical ruff phrase for rewritten ticket `verify` fields too).
- Leave AGENTS.md, CONTEXT.md, ADR 0005/0006, `knowledge/`, and on-disk `pid.py`/`rls.py` for epic 3.
- Board entry `id=4` `description`/`verify` stay CLI + deferred-notes focused (pytest/ruff + no entry-4-owned PID leftovers); operator-doc work is plan Always, not a board-verify expansion.

**Never:**
- Reintroduce PID/RLS onto the live SWT path or into `apps.yaml.example`.
- Change house `apps/apps.yaml` entity IDs or commission values.
- Delete or retire `pid.py` / `rls.py` / `test_pid` / `test_rls`.
- Rewrite AGENTS.md / CONTEXT.md / ADR / `knowledge/` (epic 3).
- Remove the epic-3 AGENTS/CONTEXT/ADR defer block from `deferred-work.md`.
- Run Exclusive Session or the Production AppDaemon add-on for this story.

## I/O & Edge-Case Matrix
| Scenario | Input / State | Expected Output / Behavior | Error Handling |
| --- | --- | --- | --- |
| Entry `id=2` verify | Still names “advance ∫” | Replaced with Design Notes canonical string (F5-A + F7-A + F6-B + example nest + pytest/ruff) | If pytest/ruff fail after edit, restore and recheck — no product code required |
| Entry `id=1` scrub | Interim PID/∫/RLS-until-entry-2 wording | Drop list removed; keep-list substance present (see Design Notes) | Diff against pre-scrub; if keep-list clauses missing, restore and redo |
| Deferred close | Section “Deferred from: …detach…” entry-2 verify bullet | That bullet removed **only after** both ticket edits land; top `source_plan` AGENTS/CONTEXT/ADR block untouched | Do not delete header block as “sweep complete” |
| Operator docs | PID-shaped house-calibration + README | Outdoor+FF per inventory; example is template SoT; domain-docs-lag note present | Grep README for leftover PID/`base_water_temp` pointers |
| Live App path | FF demand already shipped | No runtime change unless a true unused leftover appears in deferred notes — then minimal in-scope fix or escalate | Out-of-scope leftovers → leave for epic 3 |

</frozen-after-approval>

## Code Map
- `deferred-work.md` — **Remove:** under `## Deferred from: code review of story-detach…`, the bullet “Entry-2 ticket verify still names ∫…”. **Keep:** top `source_plan` AGENTS/CONTEXT/ADR 0005–0006 block (epic 3).
- `tickets/tickets.toml` — entry `id=2` `verify`; entry `id=1` `description`/`verify`/`notes` scrub; leave entry `id=4` board text as-is.
- Entry-2 plan Design Notes — F5-A = FF + no `rls_state.json`; F7-A = `hvac_app` import lock; F6-B = no pid re-export of clamp/quantize.
- Proof tests (prefer names over line numbers): `test_hvac_app_does_not_import_rls_or_pid_quantize`, `test_pid_does_not_reexport_clamp_or_quantize`, `test_demand_tick_writes_ff_command_no_rls_state`, `test_demand_event_writes_ff_same_as_tick`, `test_initialize_under_demand_runs_first_tick` (no `rls_state.json`).
- `apps.yaml.example` — FF-only commission template (`weather_feedforward` base/slope/comfort_ref + rails 50/60); copy into house-calibration.
- `docs/house-calibration.md` — full rewrite per Design Notes inventory.
- `README.md` — Install step + Layout row: Outdoor+FF / house-calibration (grep all PID pointers).
- `hvac_app.py` / `__init__.py` — already Outdoor+FF; expect no edit.
- Out of scope: `pid.py`, `rls.py`, `test_pid.py`, `test_rls.py`, AGENTS.md, CONTEXT.md, `docs/adr/*`, house `apps/apps.yaml`.

## Tasks & Acceptance
**Execution** (live App already clean after entry `id=2` — tickets + deferred-work + operator docs):
- [ ] `tickets.toml` — set entry `id=2` `verify` to Design Notes canonical string; scrub entry `id=1` per drop/keep lists.
- [ ] `deferred-work.md` — after both ticket edits, remove only the entry-2 verify bullet; leave epic-3 AGENTS/CONTEXT/ADR block.
- [ ] `docs/house-calibration.md` — rewrite per section inventory; add domain-docs-lag note; copy FF/rails from `apps.yaml.example`.
- [ ] `README.md` — retarget Install + Layout; grep-clean PID/`base_water_temp` pointers.
- [ ] Verify — commands + manual checks below.

**Acceptance Criteria:**
- Given entry `id=2` `verify` still references ∫, when updated, then it matches the Design Notes canonical string (F5-A + F7-A + F6-B), not ∫ advance.
- Given entry `id=1` still has interim-until-entry-2 PID/∫/RLS wording, when scrubbed, then every drop-list phrase is gone and every keep-list clause remains.
- Given the detach code-review defer bullet in `deferred-work.md`, when both ticket edits are done, then that bullet is gone and the epic-3 AGENTS/CONTEXT/ADR block remains.
- Given operators read house-calibration and README, when this story lands, then they commission Outdoor+FF from the example template (with domain-docs-lag note), not live PID/`base_water_temp`.
- Given the live package, when `uv run pytest` and `uv run ruff check apps/ha_smart_hvac tests` run, then both are clean with no new PID-on-path wiring.

**Verify commands:**
- `uv run pytest` — all pass
- `uv run ruff check apps/ha_smart_hvac tests` — clean
- Confirm `deferred-work.md` has no open entry-4-owned PID-on-path leftover bullets; only the epic-3 AGENTS/CONTEXT/ADR block may remain

**Manual checks:**
- Entry `id=2` `verify` = canonical string; entry `id=1` matches drop/keep lists
- house-calibration inventory complete; README has no PID commission pointers
- Example-parity: house-calibration FF/rails match `apps.yaml.example` keys/values used as template

## Design Notes

### Canonical entry `id=2` `verify` (paste as-is)
```
Demand SWT follows quantize_command(u_ff) with no rls_state.json on the demand path (F5-A); hvac_app import-locks forbid pid/rls imports (F7-A; test_hvac_app_does_not_import_rls_or_pid_quantize); pid does not re-export clamp/quantize (F6-B; test_pid_does_not_reexport_clamp_or_quantize); apps.yaml.example has no live pid / base_water_temp water-law nest; uv run pytest and uv run ruff check apps/ha_smart_hvac tests clean.
```

### Entry `id=1` scrub
**Drop** (stale interim):
- description trailing: `PID/RLS may remain unwired until entry 2.`
- verify clause: `demand path does not advance ∫ or step/persist RLS`
- notes: `Interim: pid.py / rls.py may remain until entry 2; R4 'no PID on path' is entry 2, not this tracer.`

**Keep** (substance — assert present after scrub):
- description: `quantize_command(u_ff…)` / Weather Feedforward / Outdoor / Plant+Heating Demand gates / idle `0`+clear / plant-off no write+clear / Outdoor listener / missing Outdoor → `_go_idle` / CAP-8 shared writer / Critical Zone diagnostics-only / CAP-7 out / example Outdoor+FF rails 50/60
- verify: Plant on + Heating Demand tracks `quantize_command(u_ff)`; idle SWT 0; plant-off leaves SWT untouched; automated locks for demand→quantize, idle→0+clear, plant-off→no write+clear, Outdoor listeners, missing Outdoor vs plant-unreadable, weights-unusable, Critical Zone, example FF+Outdoor no CAP-7; `uv run pytest` and ruff clean
- notes: plan-approved / tracer bullet / R7 Outdoor+FF only / R1 latch epic 2 — keep; do not invent epic-3 module-deletion notes here

### house-calibration section inventory
| Section | Action |
| --- | --- |
| Intro | Retarget to Outdoor+FF commissioning; **domain-docs-lag note**: CONTEXT/ADR/AGENTS may still describe PID until epic 3 — this doc + `apps.yaml.example` are commissioning SoT |
| §1 House wiring | Add `outdoor_temperature`; keep plant/zones; ephemeral-clear language OK (not PID-specific) |
| §2 Plant clamps / interval | Rails + `control_interval` as demand write schedule — **not** “advances the PID” |
| §3 (was Base/PID) | Replace with Weather Feedforward commission; copy `weather_feedforward` + example rails from `apps.yaml.example`; state example is template, house may differ |
| Rejected commission values | Retarget to Outdoor+FF / rails parse rejects; drop `pid.*` / adaptive / `base_water_temp` rejects |
| §4 Safe order | Commission Outdoor+FF (not base/pid) |
| Upgrading from Weather Feedforward | **Delete** (inverted; FF is live law) |
| Upgrading to hour-based PID integral | **Delete** |
| Upgrading to strict commission parsing | Delete or rewrite without `base_water_temp`/PID |
| What is not calibrated here | Drop adaptive/`rls_state` calibration pointers; CAP-7 / rise-rate stay out |

Risk remains `low` (docs/ticket hygiene; no plant write-path change). Route `full`.

## Plan Change Log
- 2026-11-12: Initial draft for ticket 1.4 / entry 4 from deferred-work + entry 1–3 continuity.
- 2026-11-12: OQ1-A + OQ2-A folded into frozen Intent; Open Questions removed.
- 2026-11-12: Review apply-all — canonical verify; entry-1 drop/keep; calibration inventory + lag note; deferred bullet ownership; named tests; Verify merged into Tasks; empty Review Triage removed; Design Notes carry implementer detail.

## Review Triage Log
- 2026-11-12 plan review (adversarial / edge / structure / prose): applied recommended set into frozen Intent + Design Notes + Tasks; declined expanding entry `id=4` board verify to list docs (CLI+deferred-notes by design).
- 2026-11-12 implement review (blind-hunter / edge-case / verification-gap / intent-alignment):
  - BH1 house-calibration weight “count more when Heating Demand / idle gates” — verdict `medium` — live `has_heating_demand` / FF SWT ignore weight; only `hvac_action` gates demand. Route: patch (grouped with BH2).
  - BH2 intro lists Zone weights as first-class Outdoor+FF commission target — verdict `medium` — same root as BH1; weight is residual yaml. Route: patch.
  - BH3 plant-off “clears ephemeral / water-path state” + no “leave SWT untouched” — verdict `medium` — `_hands_off` only logs; does not clear or write. Route: patch.
  - BH4 rejected list omits `control_interval <= 0` and `weight < 0` — verdict `low` — both still ConfigError in `config.py`; rewrite authored incomplete reject list. Route: patch.
  - BH5 upgrade section dropped strict-parsing hard-fail note — verdict `false` — Rejected section already states startup hard-fail for bad FF/rails values.
  - BH6 plan Execution checkboxes still `- [ ]` while `in-review` — verdict `false` — rejected: fix would edit this build's plan.
  - BH7 README Layout `apps.yaml.example` still “Placeholder entity IDs only” — verdict `low` — understates FF commission template role after Outdoor+FF retarget. Route: patch.
  - BH8 formula uses `quantize` not `quantize_command` — verdict `low` — cosmetic symbol drift vs tickets/code. Route: patch.
  - BH9 entry-2 verify omits three F5-A proof test names from Code Map — verdict `false` — Intent requires Design Notes canonical verify string (only F7-A/F6-B named).
  - BH10 entry-1 “weights-unusable” without FF gloss — verdict `false` — keep-list clause; still true (`test_weights_unusable_under_demand_still_writes_ff`).
  - EC: no findings.
  - VG: no verification gaps (docs/tickets-only diff).
  - IA1 deferred section header removed with sole bullet — verdict `false` — empty section cleanup; epic-3 block kept.
  - IA2 plan checkboxes lag deliverables — verdict `false` — rejected: plan-edit fix (same as BH6).
  - IA3 named proof tests live in prose not test hunks — verdict `false` — R1 expected; no product/test change.
  - IA4 lag note cites CONTEXT/ADR/AGENTS — verdict `false` — required domain-docs-lag note; not citing them as live water law.
