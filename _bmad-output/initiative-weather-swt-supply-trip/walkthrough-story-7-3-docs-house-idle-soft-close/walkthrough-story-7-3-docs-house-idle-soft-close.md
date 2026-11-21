# Walkthrough: Docs amend house-idle soft-close (story 7.3)

Target: [PR #166](https://github.com/zhmachenkov-d/ha_smart_hvac/pull/166) · merged on `main` · story `7.3` plan status `built`

Ticket: [story-docs-amend-adr-context-agents-knowledge-for-house-idle-soft.md](../tickets/epic-trv-house-idle-soft-close/tickets/story-docs-amend-adr-context-agents-knowledge-for-house-idle-soft.md)
Plan: [story-docs-amend-adr-context-agents-knowledge-for-house-idle-soft-plan.md](../tickets/epic-trv-house-idle-soft-close/tickets/story-docs-amend-adr-context-agents-knowledge-for-house-idle-soft-plan.md)

**Current block:** Broad strokes (in progress)

## Blocks
- [x] **Intent** — done (Demo + Test + Formal review clean)
- [ ] **Broad strokes** — in progress
- [ ] **Slices** — open (to be shaped after broad strokes)
- [ ] **Periphery** — open
- [ ] **Wrap-up** — open

---

### Intent
Source: frozen Intent from plan [story-docs-amend-adr-context-agents-knowledge-for-house-idle-soft-plan.md](../tickets/epic-trv-house-idle-soft-close/tickets/story-docs-amend-adr-context-agents-knowledge-for-house-idle-soft-plan.md) (Problem + Approach).

**Problem:** Live ADR 0008, CONTEXT, AGENTS `bmad:context`, and knowledge still teach plant-on overshoot hysteresis and commissioned accuracy soft-close after entry 1 already ships house-idle floor + hold.

**Approach:** Amend those live surfaces to match entry 1 Requirements 1–7; banner the three overshoot/accuracy TRV decisions as historical; leave App/tests/yaml untouched beyond verify.

Review notes: First pass patched mediums (plant-off parenthetical; orphan no-op; outdoor timestamp). Follow-up code review clean (18 rejected, 0 patch). PR #166 merged 2026-11-21. Demo — [demo-intent-live-docs-transcript.md](demo-intent-live-docs-transcript.md) (Match). Test — 370 pytest + ruff + hygiene clean. Formal review 2026-11-21 — clean (17 rejected, 0 patch).

---

### Broad strokes
Docs-only: live soft-close teaching moves from overshoot/accuracy to house-idle floor + hold → 100; zombies get historical banners; App/yaml untouched.

1. [0008-weather-curve-trv-flame-swt.md](../../../../docs/adr/0008-weather-curve-trv-flame-swt.md) — § TRV soft-close + Event-path: house-idle floor/`trv_soft_close_hold_s` (80/300), demand/plant-off cancel, closure-only ConfigError
2. [CONTEXT.md](../../../../CONTEXT.md) + [AGENTS.md](../../../../AGENTS.md) — glossary / `bmad:context` Conventions match ADR; no accuracy listeners; Verified stamp unchanged
3. [trv-soft-close.md](../../../../knowledge/concepts/trv-soft-close.md) — primary knowledge page for house-idle law (cites ADR 0008 + live prelude)
4. [adr-trv-write-gated-overshoot-latch.md](../../../../docs/decisions/adr-trv-write-gated-overshoot-latch.md) (+ two siblings) — leading Historical banner → ADR 0008 house-idle hold

---

### Findings
(none open)
