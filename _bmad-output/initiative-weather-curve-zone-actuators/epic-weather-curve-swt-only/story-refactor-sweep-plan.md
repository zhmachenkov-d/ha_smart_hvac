---
title: 'Refactor sweep'
type: 'chore'
ticket: '6'
created: '2026-10-19'
status: 'built'
baseline_revision: '47759834a191621456ea355dbf410546c47b6287'
route: 'full'
route_source: 'auto'
review: 'quick'
review_source: 'pinned'
lenses_ran: ['quick']
review_loop_iteration: 0
context:
  - '{project-root}/CONTEXT.md'
  - '{project-root}/docs/adr/0004-weather-curve-swt.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** After weather-curve SWT (stories 1.1–1.5), live water-path code is clean, but README still tells operators to calibrate LADRC; SWT / Coordinator / Critical Zone concept pages (and their `index.md` table rows) still describe ADRC/LADRC as SWT owner or CZ as Plant driver; `ZoneSnapshot.reference_setpoint` is an unused orphan kept “for possible CAP-7”.

**Approach:** Ship README + those three concept pages + matching `index.md` rows for CZ and Coordinator; delete `reference_setpoint`. ADRC/LADRC/MADRC/Huang project notes stay deferred. SWT index blurb already accurate — leave it.

## Boundaries & Constraints

**Always:**
- Source of truth: `CONTEXT.md` + ADR 0004 (HVAC App owns `clamp(u_ff)`; Coordinator = Zone Error / Heating Demand / Critical Zone for CAP-7 rise-rate only; no air→SWT tracking).
- Plant gates in any SWT prose: demand → `clamp(u_ff)`; plant-on idle → write `0` + clear ephemeral; plant-off → no write + clear ephemeral (JSON untouched). Never collapse plant-off into “idle writes 0”.
- In touched knowledge files: hard wording — removed / superseded by ADR 0004 — not soft “retired / still open / undecided”. Do not reintroduce “ADRC Controller” as a live component.
- `index.md`: rewrite only the Critical Zone and Multi-Zone Coordinator description cells to match the updated concept pages; leave ADRC/LADRC/MADRC/other rows alone.
- Ticket verify reading: “no unused water-path LADRC leftovers in deferred notes” = no code/module leftovers listed there; B1 knowledge-note deferral in `deferred-work.md` is intentional and allowed.
- After code change: `uv run pytest` and ruff check/format clean.

**Never:**
- Edit `adrc.md` / `ladrc.md` / `madrc.md` / Huang reference / `zone-error.md` project notes in this story (deferred).
- Rewrite ADRC/LADRC/MADRC (or other) `index.md` rows beyond CZ + Coordinator.
- New control features, CAP-7 law changes, reopen accepted-as-is / already-patched review findings.
- Edit ADR 0002/0003 bodies, ADR 0004, CONTEXT, AGENTS, house-calibration.
- Delete literature concept pages; invent Weather Feedforward concept file; touch house `apps/apps.yaml` / HA entities; story 1.7; `_bmad-output/` archives; `__pycache__` tasks.

</frozen-after-approval>

## Code Map

- `README.md` L26/L36 — replace “LADRC gains / LADRC for a house” with feedforward + rise-rate auto-correct → `docs/house-calibration.md`.
- `knowledge/concepts/set-water-temperature.md` L15 — HVAC App owns write: demand → `clamp(u_ff)`; plant-on idle → `0`; plant-off → no write; ephemeral clear on idle/off; no LADRC tracking / no “ADRC Controller”; state LADRC-on-water removed / superseded by ADR 0004.
- `knowledge/concepts/multi-zone-coordinator.md` frontmatter + body — Zone Error / Heating Demand / CZ for CAP-7 only; does not own SWT; no ADRC handoff. Keep Huang literature line (“single zone LADRC loop”) if present.
- `knowledge/concepts/critical-zone.md` — CZ = max Zone Error among demand zones; CAP-7 rise-rate signal only (not “drives Plant demand” as SWT); hard superseded wording vs old SWT-driver role.
- `knowledge/concepts/index.md` — CZ + Coordinator table cells only (align with pages above); SWT row already OK; leave ADRC/LADRC/MADRC rows byte-stable vs `baseline_revision`.
- `apps/ha_smart_hvac/models.py` L38–47 — delete unused `reference_setpoint`.
- `_bmad-output/.../deferred-work.md` — confirm only B1 knowledge deferral (no water-path LADRC module leftovers listed).
- Leave: `zone-error.md`; `adrc`/`ladrc`/`madrc`/Huang (deferred); live control modules; ADRs/CONTEXT.

## Tasks & Acceptance

**Execution:**
- [ ] `README.md` -- Drop LADRC calibration wording; point at house-calibration for feedforward + rise-rate auto-correct -- docs entry
- [ ] `knowledge/concepts/set-water-temperature.md` -- Rewrite ownership + both plant gates + hard removed/superseded -- SWT note
- [ ] `knowledge/concepts/multi-zone-coordinator.md` -- Rewrite to CAP-7-only coordinator; drop ADRC handoff; keep Huang lit line -- coordinator note
- [ ] `knowledge/concepts/critical-zone.md` -- Rewrite description + body: CAP-7 signal, not SWT driver; hard wording -- CZ note
- [ ] `knowledge/concepts/index.md` -- Rewrite CZ + Coordinator description cells only -- index entry door
- [ ] `apps/ha_smart_hvac/models.py` -- Remove `reference_setpoint` -- orphan API
- [ ] Verify -- pytest + ruff; `rg` on touched paths + `tests/`; index-row diff vs baseline; deferred-work check -- green

**Acceptance Criteria:**
- Given README + SWT/Coordinator/CZ concept pages + `index.md` CZ/Coordinator cells, when searched for `LADRC gains`, `ADRC Controller`, `LADRC tracking`, `drives Plant demand`, or Coordinator “desired Plant water temperature” as ownership, then no matches on those touched paths.
- Given those pages/cells, when read against CONTEXT, then SWT / Coordinator / Critical Zone match ADR 0004 with hard removed/superseded wording (not soft retired); SWT prose distinguishes plant-on idle write-0 from plant-off no-write.
- Given `index.md`, when compared to `baseline_revision`, then ADRC/LADRC/MADRC rows are unchanged; only CZ + Coordinator cells moved.
- Given `ZoneSnapshot`, when inspected, then `reference_setpoint` is gone and no remaining callers under `apps/ha_smart_hvac/` or `tests/`.
- Given `deferred-work.md`, when read, then it lists only the B1 knowledge-note deferral (no water-path LADRC module leftovers).
- Given the suite, when `uv run pytest` and ruff check/format run on `apps/ha_smart_hvac` + `tests`, then they pass.

## Implementation Notes

## Plan Change Log

- 2026-10-19 party (narrow ship): Denys chose README + `reference_setpoint` + CZ/SWT/Coordinator only; deferred ADRC/LADRC/MADRC/Huang notes; dropped `__pycache__`; leave `zone-error.md`; hard wording ban on live “ADRC Controller” in touched files.
- 2026-10-19 party (A2 B1 C1): +`index.md` CZ + Coordinator cells only; ADRC/LADRC project notes stay deferred (B1); keep `reference_setpoint` removal (C1); SWT index row leave. KEEP: hard wording; no control-law changes.
- 2026-10-19 plan review patch-all: plant-on idle vs plant-off gates in Always/Code Map/SWT task/AC; hard-wording exemplar in Design Notes; AC3 via `git show` baseline index rows; `rg` includes `tests/`; README task = FF + rise-rate; ticket-verify reading = water-path leftovers none, B1 knowledge deferral OK + deferred-work AC. KEEP: A2 B1 C1; Huang lit line on coordinator; no control-law changes.

## Review Triage Log

| finding | verdict | route | evidence |
|---------|---------|-------|----------|
| Design Notes lack hard removed/superseded exemplar | medium | patch | Always/AC2 vs golden shape present-tense only |
| AC3 index rows unchanged — no Verify command | medium | patch | Need `git show baseline:index.md` / diff for ADRC/LADRC/MADRC rows |
| `rg` omits `tests/` for AC4 callers | medium | patch | AC4 names tests/; Verify did not |
| SWT Code Map idle→0 collapses plant-off | medium | patch | CONTEXT/0004: plant-off = no write + clear |
| Ticket verify vs B1 knowledge in deferred-work | medium | patch | Clarify water-path leftovers ≠ knowledge B1; add deferred-work AC |
| README task FF-only vs Code Map +rise-rate | medium | patch | Align task with L26/L36 Code Map |
| Huang “single zone LADRC loop” leftover | low | reject | Literature; outside stale-phrase `rg` |
| Ghost `apps/hvac` reference_setpoint | low | reject | Not on disk; outside caller scope |
| Coordinator body missing removed/superseded | medium | patch | Always + AC2 + Design Notes; SWT/CZ have exemplar; `rg removed\|superseded` empty on coordinator |
| Heating Demand linked to zone-error.md | medium | patch | CONTEXT separates terms; CZ leaves HD unlinked; link conflates concepts onto stale ZE page |

## Design Notes

Hard-wording exemplar (use this shape, not soft “retired”):

> LADRC-on-water (ADR 0002) and ωc auto-tune (ADR 0003) are **removed** from the water path — **superseded by ADR 0004**. Live law is weather-curve-only SWT: demand → `clamp(u_ff)`; plant-on idle → write `0` + clear ephemeral; plant-off → no write + clear ephemeral. Critical Zone is the CAP-7 rise-rate signal only. Coordinator does not own the OpenTherm write. Do not name an ADRC Controller as a live App component.

## Verification

**Commands:**
- `uv run pytest` -- expected: pass
- `uv run ruff check apps/ha_smart_hvac tests && uv run ruff format --check apps/ha_smart_hvac tests` -- expected: clean
- `rg -n "ADRC Controller|LADRC tracking|drives Plant demand|LADRC gains|calibrate.*LADRC|desired Plant water temperature|reference_setpoint" README.md knowledge/concepts/set-water-temperature.md knowledge/concepts/multi-zone-coordinator.md knowledge/concepts/critical-zone.md knowledge/concepts/index.md apps/ha_smart_hvac tests` -- expected: no matches on stale live-control claims (Huang “LADRC loop” literature OK if left; ADRC/LADRC literature titles in other index rows OK)
- `git show 47759834a191621456ea355dbf410546c47b6287:knowledge/concepts/index.md | rg -n "ADRC|LADRC|MADRC|Critical Zone|Multi-Zone Coordinator"` then diff those three literature rows vs working tree -- expected: ADRC/LADRC/MADRC rows unchanged; CZ + Coordinator cells updated
- Manual: `_bmad-output/initiative-weather-curve-zone-actuators/deferred-work.md` -- expected: only B1 knowledge deferral; no water-path LADRC module leftovers listed
