---
title: 'Document CAP-8 reactivity in ADR and domain docs'
type: 'chore'
ticket: '2'
created: '2026-10-19'
status: 'built'
baseline_revision: '1231fa164a3747681e54b6c7720db80504480cd3'
route: 'oneshot'
route_source: 'auto'
review: 'quick'
review_source: 'pinned'
lenses_ran: ['quick']
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/initiative-weather-curve-zone-actuators/spec-weather-curve-swt-only/spec-weather-curve-swt-only.md'
  - '{project-root}/_bmad-output/initiative-weather-curve-zone-actuators/epic-immediate-swt-reactivity/epic-immediate-swt-reactivity.md'
  - '{project-root}/_bmad-output/initiative-weather-curve-zone-actuators/epic-immediate-swt-reactivity/story-tracer-event-driven-swt-gate-re-evaluation-plan.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** CAP-8 event-driven SWT gate re-evaluation shipped in entry 1, but ADR 0004, CONTEXT/AGENTS, and brownfield still read as periodic-only (or “follow-on”), so the documented contract lags the code.

**Approach:** Update ADR 0004, CONTEXT.md / AGENTS.md as needed, and companions `brownfield.md` / `architecture-diagrams.md` so they state CAP-8 triggers, that event evaluations do not advance CAP-7 samples, and that periodic `control_interval` still runs CAP-7.

</frozen-after-approval>

## Implementation Notes

Oneshot: docs-only alignment to shipped CAP-8 + parent spec (~50–70 lines across ADR/CONTEXT/AGENTS/companions); no code or test changes. Continuity from story 1: dual entrypoints `control_tick` / `control_event`; listeners on plant, outdoor, zone air, thermostat `hvac_action`/`temperature`; event demand = `clamp_uff` only.

**Must document:**
- CAP-8 trigger set: Plant Management, thermostat `hvac_action` and setpoint, zone air, Outdoor Temperature.
- Event path re-applies CAP-1…CAP-3; does not advance CAP-7 window / I1.
- Periodic `control_interval` still runs full path including CAP-7.
- brownfield: retire “CAP-8 follow-on” / “Today: periodic only” — describe shipped state.
- architecture-diagrams: keep contract; name `control_tick` / `control_event` only if it clarifies without inventing new law.
- Do not change `apps/ha_smart_hvac` or tests; do not reopen CAP-7 law.

**Touch:**
- `docs/adr/0004-weather-curve-swt.md` — add CAP-8 reactivity after SWT gates (or equivalent); CAP-7 Rate already implies periodic samples.
- `CONTEXT.md` — domain/dialogue so agents learn event gates vs CAP-7 periodic sampling.
- `AGENTS.md` — convention bullet(s) under “differ from defaults” if needed (inside bmad:context block).
- `_bmad-output/.../spec-weather-curve-swt-only/brownfield.md` — Reactivity section → current.
- `_bmad-output/.../spec-weather-curve-swt-only/architecture-diagrams.md` — align labels if helpful.

**Done (2026-10-19):**
- ADR 0004: new `## CAP-8 reactivity` after SWT gates (triggers, `control_tick`/`control_event`, no CAP-7 advance on events, periodic retained).
- CONTEXT: Plant Management glossary + example dialogue for CAP-8 vs CAP-7 cadence.
- AGENTS: CAP-8 convention bullet (inside bmad:context).
- brownfield: Reactivity section rewritten as shipped (not follow-on).
- architecture-diagrams: node labels name `control_tick` / `control_event`.

## Plan Change Log

## Review Triage Log

- 2026-10-19 | quick | medium | patch | architecture-diagrams periodic node `Periodic control_interval control_tick` flattened period vs callback. Evidence: `run_every(control_tick, …, control_interval)` — distinct roles; ADR keeps paren form. Fixed to `Periodic control_interval (control_tick)`.
- 2026-10-19 | quick | medium | patch | CONTEXT Plant Management glossary overloaded with CAP-8 schedule/triggers. Evidence: term is enable/disable + clear ephemeral; dialogue already teaches CAP-8. Removed glossary CAP-8 sentence; kept dialogue.

## Verification

**Manual checks:**
- ADR 0004 states CAP-8 triggers, event path does not advance CAP-7, periodic still runs CAP-7.
- brownfield no longer frames CAP-8 as future-only / periodic-only today.
- CONTEXT and/or AGENTS (if touched) match that contract; architecture-diagrams still show event + periodic split with CAP-7 on periodic only.
- No application code diffs.
