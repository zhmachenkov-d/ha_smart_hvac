# Demo: Story 6.3 Broad strokes — exact edit surfaces
Generated: 2026-11-17T13:47:00+02:00
Branch: `docs/6-2-knowledge-live-curve-trv-flame-demote-supply-trip` @ `67ebb44`

Offline paste of the four Broad-strokes entry points. **Edit** / **Prune** / **Leave** / **Create** / **Confirm**.

---

## 1. CAP-8 — Edit (one sentence lag)

File: [adr-cap8-shared-ff-demand-writer.md](../../../../docs/decisions/adr-cap8-shared-ff-demand-writer.md) L2

Current closing clause (stale):

> … surprises anyone still reading AGENTS sticky-latch prose until epic 3.

Action: reword so the historical CAP-8 trade-off remains, without claiming AGENTS still has sticky-latch prose / “until epic 3”.

---

## 2. deferred-work.md — Prune / Settled / Leave

File: [deferred-work.md](../deferred-work.md)

### Prune (A–F + E) — claims obsolete after epic 3 / 6.1 / 6.2

| Tag | Current summary line |
| --- | --- |
| A | AGENTS.md / CONTEXT.md / ADR 0005–0006 still describe live PID/∫/RLS SWT after FF detach |
| B | Epic-1 deferred-work bullet still frames AGENTS/CONTEXT/ADR PID supersede as outstanding after epic 3.1 already rewrote those surfaces |
| C | docs/decisions/adr-cap8-shared-ff-demand-writer.md still warns about AGENTS sticky-latch prose until epic 3 *(prune after CAP-8 edit)* |
| D | AGENTS.md still says knowledge/ may lag until story 3.2 after 3.2 merged |
| E | Code-review repeat: Stale epic-1 deferred-work bullet … settle/prune in entry 4 |
| F | AGENTS.md / CONTEXT.md listener inventories still omit commissioned TRV `accuracy` as a `control_event` listen … |

### Settled I (B prune-with-cite) — move out from under Settled epic-5

Current (wrongly nested under Settled epic-5):

> house-calibration §1 wiring table still lists only Outdoor/plant/zones … without flame/`ch_active`/TRV rows or flame-clear wording.

Cite targets (no §1 table expand):

- [house-calibration.md](../../../../docs/house-calibration.md) L2–7 — intro already names flame / `ch_active` / TRV; plant-off clears flame latch; points at example for entity/nest detail
- [apps.yaml.example](../../../../apps.yaml.example) L14–17, L24, L32–36 — flame / `ch_active` / floor / Sonoff TRV nest

### Leave (G–H) — OUT of 6.3

| Tag | Current summary |
| --- | --- |
| G | No accuracy `control_event` + Outdoor-fail isolation test |
| H | Empty-zone isolation pins law-ran only via spy |

Keep existing Settled epic-4 / epic-5 sections.

---

## 3. Plan file — Create

Path (missing today):  
`_bmad-output/initiative-weather-swt-supply-trip/tickets/epic-docs-trv-flame-water-law/tickets/story-refactor-sweep-plan.md`

Must freeze Always/Never: A–F+C IN, G–H OUT, I=B, no runtime/tests/`apps.yaml`, no `control_event` docstring.

---

## 4. tickets.toml entry 3 — Confirm (no rewrite expected)

```toml
id = 3
title = "Refactor sweep"
description = "Cleans deferred review findings and orphans left by the docs supersede (including stale deferred-work.md epic-3 / entry-4 bullets); no new scope."
verify = "uv run pytest and uv run ruff check apps/ha_smart_hvac tests clean; no leftover supply-trip-as-live-law docs or stale deferred bullets called out in this epic's deferred notes."
```

Matches Intent lock; Broad strokes treat as confirm-only.
