# Walkthrough: Story 6.1 — Tracer: ADR + AGENTS/CONTEXT for TRV+flame water law
Target: branch `docs/adr-0008-trv-flame-water-law` · `5ee3974`+`6b116b2` (no PR yet)

**Current block:** Periphery (in progress)

## Blocks
- [x] **Intent** — done (Formal review 6 patch; Test 362 + ruff; Demo)
- [x] **Broad strokes** — done (Demo transcript)
- [x] **Slice: ADR 0008 + historical 0007 / pointers** — done (Demo)
- [x] **Slice: AGENTS + CONTEXT** — done (Demo)
- [x] **Slice: Decisions (idle flame + zombies)** — done (Demo)
- [ ] **Periphery** — in progress
- [ ] **Wrap-up** —

---

### Intent
Source: frozen Intent from plan [story-tracer-adr-agents-context-for-trv-flame-water-law-plan.md](../../tickets/epic-docs-trv-flame-water-law/tickets/story-tracer-adr-agents-context-for-trv-flame-water-law-plan.md) (Problem + Approach).

**Problem:** Live App already runs weather-curve SWT + TRV soft-close + flame short-on, but ADR 0007 / AGENTS / CONTEXT still teach supply rise-rate trip as live anti-cycle and omit TRV/flame.

**Approach:** Add ADR 0008 as agent-law live water law (curve + TRV soft-close + flame short-on; CAP-7 hard out), mark 0007 historical (supply-trip era), retarget live-pointers on 0004–0006 and [docs/house-calibration.md](../../../../docs/house-calibration.md), rewrite [AGENTS.md](../../../../AGENTS.md) + [CONTEXT.md](../../../../CONTEXT.md) to match the shipped App, and mark zombie supply-trip [docs/decisions/](../../../../docs/decisions/) historical — no `knowledge/` demotion (6.2), no runtime changes.

Review notes: Formal review — 6 patch applied (F1–F6); 12 rejected. Test — 362 pytest + ruff clean (+ spot greps). Demo — [demo-intent-adr-vs-app-transcript.md](demo-intent-adr-vs-app-transcript.md) (ADR↔App Match).

---

### Broad strokes
Docs-only: live agent water law moves from supply-trip ADR 0007 to ADR 0008 (curve + TRV soft-close + flame short-on); AGENTS/CONTEXT and pointers follow; zombies get historical banners.

1. [0008-weather-curve-trv-flame-swt.md](../../../../docs/adr/0008-weather-curve-trv-flame-swt.md) — accepted agent-law MUST-floor (gates, FF, TRV, flame, Decision C, dual-gate; CAP-7 out)
2. [0007-weather-curve-supply-trip-swt.md](../../../../docs/adr/0007-weather-curve-supply-trip-swt.md) — superseded historical supply-trip era + live-pointer to 0008
3. [AGENTS.md](../../../../AGENTS.md) — water-law Conventions rewrite; hard knowledge-not-live-until-6.2
4. [CONTEXT.md](../../../../CONTEXT.md) — TRV soft-close + Flame short-on terms; Supply rise-rate demoted
5. [adr-idle-flame-clear-after-write.md](../../../../docs/decisions/adr-idle-flame-clear-after-write.md) — live Decision C; supply-era idle banner + forward link

Review notes: Demo — [demo-broad-strokes-transcript.md](demo-broad-strokes-transcript.md) (five entry points).

---

### Slice: ADR 0008 + historical 0007 / pointers
ADR 0008 is the accepted agent-law MUST-floor for curve + TRV soft-close + flame short-on (CAP-7 out). ADR 0007 keeps its supply-trip body but is framed historical and superseded; live-pointers on 0004–0006 and house-calibration retarget to 0008 (0005/0006 status → superseded by ADR-0008; 0004 status stays →0005).

Places:
- [0008-weather-curve-trv-flame-swt.md](../../../../docs/adr/0008-weather-curve-trv-flame-swt.md) — accepted; gates / TRV / flame / Decision C / dual-gate
- [0007-weather-curve-supply-trip-swt.md](../../../../docs/adr/0007-weather-curve-supply-trip-swt.md) — superseded + historical framing + live-pointer
- [0004](../../../../docs/adr/0004-weather-curve-swt.md) / [0005](../../../../docs/adr/0005-fixed-pid-swt.md) / [0006](../../../../docs/adr/0006-optional-rls-adaptive-pid.md) — Live water law → ADR-0008
- [house-calibration.md](../../../../docs/house-calibration.md) — Live water law → 0008; anti-cycle wiring in lead

Review notes: Demo — [demo-slice-adr-transcript.md](demo-slice-adr-transcript.md).

---

### Slice: AGENTS + CONTEXT
AGENTS Conventions and CONTEXT glossary are rewritten to the 0008 water law: Outdoor-gated clamp(u_ff), TRV soft-close (incl. accuracy listen), flame short-on clears (hold / rising-edge `_clear_flame_trip_state` / plant-off / Decision C), dual-gate, Critical Zone diagnostics-only, CAP-7 out, and a hard knowledge-not-live-until-6.2 warning. Supply rise-rate survives only as a Historical / `_Avoid_` term in CONTEXT.

Places:
- [AGENTS.md](../../../../AGENTS.md) — Where things are (0008 + knowledge warn); Conventions water-law bullets
- [CONTEXT.md](../../../../CONTEXT.md) — Weather Feedforward / TRV soft-close / Flame short-on / Supply rise-rate (historical)

Review notes: Demo — [demo-slice-agents-context-transcript.md](demo-slice-agents-context-transcript.md).

---

### Slice: Decisions (idle flame + zombies)
Live Decision C is a new flame-era note; supply-era idle / supply-event / write-gated-supply / token-orphan notes get a historical banner (idle also forward-links). TRV-before-prelude drops stale `supply_event` and titles hold-expiry callers.

Places:
- [adr-idle-flame-clear-after-write.md](../../../../docs/decisions/adr-idle-flame-clear-after-write.md) — live Decision C
- [adr-idle-trip-clear-after-write.md](../../../../docs/decisions/adr-idle-trip-clear-after-write.md) — historical + Live Decision C link
- [adr-supply-event-no-outdoor-prelude.md](../../../../docs/decisions/adr-supply-event-no-outdoor-prelude.md) / [adr-write-gated-supply-trip-latch.md](../../../../docs/decisions/adr-write-gated-supply-trip-latch.md) / [adr-trip-hold-token-orphan-guard.md](../../../../docs/decisions/adr-trip-hold-token-orphan-guard.md) — historical banners
- [adr-trv-before-water-prelude.md](../../../../docs/decisions/adr-trv-before-water-prelude.md) — title + body include hold expiry; no supply_event

Review notes: Demo — [demo-slice-decisions-transcript.md](demo-slice-decisions-transcript.md).

---

### Periphery
- [deferred-work.md](../../deferred-work.md) — notes deferred house-calibration §1 table / related hygiene for later sweep
- [story-tracer-adr-agents-context-for-trv-flame-water-law-plan.md](../../tickets/epic-docs-trv-flame-water-law/tickets/story-tracer-adr-agents-context-for-trv-flame-water-law-plan.md) — build plan + Formal review findings recorded
- `knowledge/**` — intentionally untouched (story 6.2)
- App runtime / `apps.yaml.example` / house `apps.yaml` — intentionally untouched

---

### Wrap-up
_TBD — parent will supply._