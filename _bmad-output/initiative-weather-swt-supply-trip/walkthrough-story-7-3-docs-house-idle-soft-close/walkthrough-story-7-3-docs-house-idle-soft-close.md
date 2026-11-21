# Walkthrough: Docs amend house-idle soft-close (story 7.3)

Target: [PR #166](https://github.com/zhmachenkov-d/ha_smart_hvac/pull/166) · merged on `main` · story `7.3` plan status `built` · branch `chore/walkthrough-story-7-3-intent-review`

Ticket: [story-docs-amend-adr-context-agents-knowledge-for-house-idle-soft.md](../tickets/epic-trv-house-idle-soft-close/tickets/story-docs-amend-adr-context-agents-knowledge-for-house-idle-soft.md)
Plan: [story-docs-amend-adr-context-agents-knowledge-for-house-idle-soft-plan.md](../tickets/epic-trv-house-idle-soft-close/tickets/story-docs-amend-adr-context-agents-knowledge-for-house-idle-soft-plan.md)

**Current block:** Slice: ADR 0008 TRV + Event path (in progress)

## Blocks
- [x] **Intent** — done (Demo + Test + Formal review clean)
- [x] **Broad strokes** — done (Demo + Test; Formal review 1 patch applied — link depth)
- [ ] **Slice: ADR 0008 TRV + Event path** — in progress
- [ ] **Slice: CONTEXT + AGENTS** — open
- [ ] **Slice: Knowledge + historical banners** — open
- [ ] **Periphery** — open
- [ ] **Wrap-up** — open

---

### Intent
Source: frozen Intent from plan [story-docs-amend-adr-context-agents-knowledge-for-house-idle-soft-plan.md](../tickets/epic-trv-house-idle-soft-close/tickets/story-docs-amend-adr-context-agents-knowledge-for-house-idle-soft-plan.md) (Problem + Approach).

**Problem:** Live ADR 0008, CONTEXT, AGENTS `bmad:context`, and knowledge still teach plant-on overshoot hysteresis and commissioned accuracy soft-close after entry 1 already ships house-idle floor + hold.

**Approach:** Amend those live surfaces to match entry 1 Requirements 1–7; banner the three overshoot/accuracy TRV decisions as historical; leave App/tests/yaml untouched beyond verify.

Review notes: Demo — [demo-intent-live-docs-transcript.md](demo-intent-live-docs-transcript.md). Test — 370 + ruff + hygiene. Formal review Intent — clean (17 rejected).

---

### Broad strokes
Docs-only: live soft-close teaching moves from overshoot/accuracy to house-idle floor + hold → 100; zombies get historical banners; App/yaml untouched.

1. [0008-weather-curve-trv-flame-swt.md](../../../docs/adr/0008-weather-curve-trv-flame-swt.md) — § TRV soft-close + Event-path
2. [CONTEXT.md](../../../CONTEXT.md) + [AGENTS.md](../../../AGENTS.md) — glossary / Conventions
3. [trv-soft-close.md](../../../knowledge/concepts/trv-soft-close.md) — primary knowledge page
4. [adr-trv-write-gated-overshoot-latch.md](../../../docs/decisions/adr-trv-write-gated-overshoot-latch.md) (+ siblings) — Historical banners

Review notes: Demo — [demo-broad-strokes-transcript.md](demo-broad-strokes-transcript.md). Test — 370 + ruff + hygiene. Formal review — 1 patch applied (`../../../../`→`../../../`).

---

### Slice: ADR 0008 TRV + Event path
Agent-law soft-close now lives in ADR 0008 § TRV: house-idle floor + hold (defaults 80/300), demand/plant-off cancel, orphan no-op, closure-only ConfigError; Event-path no longer lists accuracy; live cites drop the three overshoot/accuracy decisions; plant-off SWT gate parenthetical states closure 100 + cancel hold.

Places:
- [0008-weather-curve-trv-flame-swt.md](../../../docs/adr/0008-weather-curve-trv-flame-swt.md) — § TRV soft-close + Event-path listener list + live cite list + SWT gates plant-off parenthetical

---

### Slice: CONTEXT + AGENTS
Status: open

(placeholder)

---

### Slice: Knowledge + historical banners
Status: open

(placeholder)

---

### Findings
- [x] Broad strokes relative link depth (Formal review F1) — fixed `../../../`
