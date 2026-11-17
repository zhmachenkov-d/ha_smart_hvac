# Demo: Story 6.1 Broad strokes
Generated: 2026-11-17T09:28:00+00:00

Offline (no Exclusive Session). Five Broad-strokes entry points in order.

## 1. ADR 0008 — live agent law (`docs/adr/0008-weather-curve-trv-flame-swt.md`)

```
---
status: accepted
---

# Weather-curve Set Water Temperature with TRV soft-close and flame short-on
...
This ADR is **agent law** for the live App — MUST-floor only. Cite ... adr-zone-rising-edge-decision-a.md ...
```

Sections present: SWT gates · Feedforward law · CAP-8 listeners · TRV soft-close · Flame trip latch · Idle clear (Decision C) · Dual-gate · Out of scope (CAP-7 hard out).

**Observed:** Accepted live SoT for curve + TRV + flame.

## 2. ADR 0007 — historical (`docs/adr/0007-weather-curve-supply-trip-swt.md`)

```
---
status: superseded by ADR-0008
---

# Weather-curve Set Water Temperature with supply rise-rate trip
Historical — supply rise-rate trip era (epic 2). Live water law is ADR-0008 ...
This ADR is **historical** (superseded by ADR-0008) ... For live agent law, follow ADR-0008.
```

Live pointers also retargeted:

| File | status / pointer |
| --- | --- |
| `0004` | status still →0005; Live water law: ADR-0008 |
| `0005` / `0006` | superseded by ADR-0008; Live water law: ADR-0008 |
| `house-calibration.md` | Live water law → ADR 0008 + anti-cycle wiring sentence |

**Observed:** Supply-trip era demoted; agents sent to 0008.

## 3. AGENTS.md — Conventions + knowledge hard-warn

```
- Architecture decisions: ... 0008 weather-curve SWT + TRV soft-close + flame short-on — do not follow superseded 0004/0005/0006/0007 for live SWT
- Algorithm depth / citations: knowledge/ (... **knowledge/ SWT/anti-cycle pages are not live until story 6.2 — do not follow for water law**)
```

Water-law bullets cover plant-off `_clear_flame_trip_state`, Decision C, FF demand, TRV-before-prelude, flame short-on (rising-edge helper + prelude zones), dual-gate.

**Observed:** Agent conventions match 0008; knowledge deferred to 6.2.

## 4. CONTEXT.md — TRV / Flame / Supply terms

```
**TRV soft-close**: ... before Outdoor water prelude on tick / control_event / flame hold expiry ...
**Flame short-on trip**: ... Clears on hold expiry (... when prelude returns zones), ... rising-edge ... (`_clear_flame_trip_state`) ...
**Supply rise-rate trip**: Historical (epic 2 / ADR 0007). ... Live anti-cycle is flame short-on + TRV soft-close (ADR 0008).
```

**Observed:** Glossary teaches live TRV+flame; supply only under Historical / `_Avoid_`.

## 5. Live Decision C (`docs/decisions/adr-idle-flame-clear-after-write.md`)

```
# Idle flame clear: disarm hold always; latch after idle write 0
On idle (_go_idle), ... always disarms ... via _disarm_flame_trip_hold; _flame_trip_latched becomes false only when the idle SWT 0 write succeeds.
```

Frozen supply-era note:

```
Historical — ... / ADR 0008). Live Decision C: [adr-idle-flame-clear-after-write.md](...)
# Idle trip clear: ...
```

**Observed:** Live Decision C file present; historical idle banners + forward link.

## Verdict

Broad-strokes map holds: open 0008 → 0007 → AGENTS → CONTEXT → idle-flame Decision C in that order and the docs-only supersede is clear without reading every changed file.
