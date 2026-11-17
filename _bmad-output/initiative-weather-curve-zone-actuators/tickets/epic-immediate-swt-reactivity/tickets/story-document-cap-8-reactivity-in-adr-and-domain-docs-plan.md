---
title: 'Document R8 reactivity in ADR and domain docs'
type: 'chore'
ticket: '2'
created: '2026-10-19'
status: done
baseline_revision: '1231fa164a3747681e54b6c7720db80504480cd3'
route: 'oneshot'
route_source: 'auto'
review: 'quick'
review_source: 'pinned'
lenses_ran: ['quick']
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/initiative-weather-curve-zone-actuators/initiative-weather-curve-zone-actuators.md'
  - '{project-root}/_bmad-output/initiative-weather-curve-zone-actuators/tickets/epic-immediate-swt-reactivity/epic-immediate-swt-reactivity.md'
  - '{project-root}/_bmad-output/initiative-weather-curve-zone-actuators/tickets/epic-immediate-swt-reactivity/tickets/story-tracer-event-driven-swt-gate-re-evaluation-plan.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** R8 event-driven SWT gate re-evaluation shipped in entry 1, but ADR 0004, CONTEXT/AGENTS, and brownfield still read as periodic-only (or “follow-on”), so the documented contract lags the code.

**Approach:** Update ADR 0004, CONTEXT.md / AGENTS.md as needed, and companions `brownfield.md` / `architecture-diagrams.md` so they state R8 triggers, that event evaluations do not advance R7 samples, and that periodic `control_interval` still runs R7.

</frozen-after-approval>

## Implementation Notes

Oneshot: docs-only alignment to shipped R8 + parent spec (~50–70 lines across ADR/CONTEXT/AGENTS/companions); no code or test changes. Continuity from story 1: dual entrypoints `control_tick` / `control_event`; listeners on plant, outdoor, zone air, thermostat `hvac_action`/`temperature`; event demand = `clamp_uff` only.

**Must document:**
- R8 trigger set: Plant Management, thermostat `hvac_action` and setpoint, zone air, Outdoor Temperature.
- Event path re-applies R1…R3; does not advance R7 window / I1.
- Periodic `control_interval` still runs full path including R7.
- brownfield: retire “R8 follow-on” / “Today: periodic only” — describe shipped state.
- architecture-diagrams: keep contract; name `control_tick` / `control_event` only if it clarifies without inventing new law.
- Do not change `apps/ha_smart_hvac` or tests; do not reopen R7 law.

**Touch:**
- `docs/adr/0004-weather-curve-swt.md` — add R8 reactivity after SWT gates (or equivalent); R7 Rate already implies periodic samples.
- `CONTEXT.md` — domain/dialogue so agents learn event gates vs R7 periodic sampling.
- `AGENTS.md` — convention bullet(s) under “differ from defaults” if needed (inside bmad:context block).
- `_bmad-output/.../spec-weather-curve-swt-only/brownfield.md` — Reactivity section → current.
- `_bmad-output/.../spec-weather-curve-swt-only/architecture-diagrams.md` — align labels if helpful.

**Done (2026-10-19):**
- ADR 0004: new `## R8 reactivity` after SWT gates (triggers, `control_tick`/`control_event`, no R7 advance on events, periodic retained).
- CONTEXT: Plant Management glossary + example dialogue for R8 vs R7 cadence.
- AGENTS: R8 convention bullet (inside bmad:context).
- brownfield: Reactivity section rewritten as shipped (not follow-on).
- architecture-diagrams: node labels name `control_tick` / `control_event`.

## Plan Change Log

## Review Triage Log

- 2026-10-19 | quick | medium | patch | architecture-diagrams periodic node `Periodic control_interval control_tick` flattened period vs callback. Evidence: `run_every(control_tick, …, control_interval)` — distinct roles; ADR keeps paren form. Fixed to `Periodic control_interval (control_tick)`.
- 2026-10-19 | quick | medium | patch | CONTEXT Plant Management glossary overloaded with R8 schedule/triggers. Evidence: term is enable/disable + clear ephemeral; dialogue already teaches R8. Removed glossary R8 sentence; kept dialogue.

## Verification

**Manual checks:**
- ADR 0004 states R8 triggers, event path does not advance R7, periodic still runs R7.
- brownfield no longer frames R8 as future-only / periodic-only today.
- CONTEXT and/or AGENTS (if touched) match that contract; architecture-diagrams still show event + periodic split with R7 on periodic only.
- No application code diffs.
