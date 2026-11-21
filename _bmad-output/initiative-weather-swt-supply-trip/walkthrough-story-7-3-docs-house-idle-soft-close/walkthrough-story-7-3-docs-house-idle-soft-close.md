# Walkthrough: Docs amend house-idle soft-close (story 7.3)

Target: [PR #166](https://github.com/zhmachenkov-d/ha_smart_hvac/pull/166) · merged on `main` · story `7.3` plan status `done` · branch `chore/walkthrough-story-7-3-intent-review`

Ticket: [story-docs-amend-adr-context-agents-knowledge-for-house-idle-soft.md](../tickets/epic-trv-house-idle-soft-close/tickets/story-docs-amend-adr-context-agents-knowledge-for-house-idle-soft.md)
Plan: [story-docs-amend-adr-context-agents-knowledge-for-house-idle-soft-plan.md](../tickets/epic-trv-house-idle-soft-close/tickets/story-docs-amend-adr-context-agents-knowledge-for-house-idle-soft-plan.md)

**Current block:** Wrap-up (done — commit+push+PR+mark story; merge deferred)

## Blocks
- [x] **Intent** — done (Demo + Test + Formal review clean)
- [x] **Broad strokes** — done (Demo + Test; Formal review 1 patch applied — link depth)
- [x] **Slice: ADR 0008 TRV + Event path** — done (Demo + Test + Formal review clean)
- [x] **Slice: CONTEXT + AGENTS** — done (Demo + Test + Formal review clean)
- [x] **Slice: Knowledge + historical banners** — done (accepted without further moves)
- [x] **Periphery** — done (Demo)
- [x] **Wrap-up** — done (follow-through 1–3)

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

Review notes: Demo — [demo-slice-adr-transcript.md](demo-slice-adr-transcript.md) (Req 2 checklist Match). Test — 370 pytest + ruff; ADR hygiene clean; floor/hold/ConfigError/orphan/cold-start anchors present; no live overshoot decision cites. Formal review Slice ADR 2026-11-21 — clean (14 rejected, 0 patch).

---

### Slice: CONTEXT + AGENTS
CONTEXT glossary and AGENTS `bmad:context` Conventions carry the same house-idle soft-close law as ADR 0008 (floor + hold + any-demand/plant-off cancel; orphan no-op; closure-only; leftover `accuracy` ConfigError; no accuracy soft-close listen). AGENTS edits stay inside markers; Verified stamp unchanged. Demand flavors stay compressed as “any Heating Demand” (ADR/knowledge keep the enum).

Places:
- [CONTEXT.md](../../../CONTEXT.md) — Plant Management off dialogue + **TRV soft-close** glossary + Weather Feedforward listeners (no accuracy)
- [AGENTS.md](../../../AGENTS.md) — plant-off TRV line; TRV soft-close Conventions bullet; Event listeners inventory; Verified stamp

Review notes: Demo — [demo-slice-context-agents-transcript.md](demo-slice-context-agents-transcript.md) (Req 3 Match; demand compressed). Test — 370 pytest + ruff; CONTEXT/AGENTS hygiene clean; markers+stamp OK; floor/hold/orphan/ConfigError anchors present. Formal review 2026-11-21 — clean (16 rejected, 0 patch).

---

### Slice: Knowledge + historical banners
Primary knowledge teaches house-idle soft-close (cite ADR 0008 + live prelude); concepts index TRV blurb no longer says plant-off keeps overshoot latch; outdoor listener inventory has no commissioned accuracy; `knowledge/log.md` has an append-only Fact. The three overshoot/accuracy TRV decisions open with a leading Historical banner → ADR 0008; no new soft-close hold decision file.

Places:
- [trv-soft-close.md](../../../knowledge/concepts/trv-soft-close.md) — primary page (frontmatter + body + Related)
- [index.md](../../../knowledge/concepts/index.md) — TRV blurb
- [outdoor-temperature.md](../../../knowledge/concepts/outdoor-temperature.md) — listener inventory
- [log.md](../../../knowledge/log.md) — append-only Fact
- [adr-trv-write-gated-overshoot-latch.md](../../../docs/decisions/adr-trv-write-gated-overshoot-latch.md), [adr-trv-plant-off-no-latch-clear.md](../../../docs/decisions/adr-trv-plant-off-no-latch-clear.md), [adr-trv-accuracy-shared-control-event.md](../../../docs/decisions/adr-trv-accuracy-shared-control-event.md) — Historical banners

---


### Periphery
Docs-only story: no App/runtime/test/yaml product changes. Verify gates (hygiene `rg`, pytest, ruff) live in plan Auto Run and walkthrough Test notes. Residual called out earlier and left out of Notes matrix: `knowledge/concepts/set-water-temperature.md` plant-off “still applies” without 100+cancel detail (companion link to trv-soft-close). Entry 4 owns deferred dead-code/test prune — not this story. Walkthrough/plan artifacts under `_bmad-output/` are process evidence for this review.

Places (references only):
- Plan Verification / Auto Run Result in [story-docs-amend-…-plan.md](../tickets/epic-trv-house-idle-soft-close/tickets/story-docs-amend-adr-context-agents-knowledge-for-house-idle-soft-plan.md)
- [set-water-temperature.md](../../../knowledge/concepts/set-water-temperature.md) — residual plant-off soft-close pointer (out of Notes matrix)
- Story Boundaries: no App / `apps.yaml*` / house yaml; entry 4 deferred prune

Review notes: Demo — [demo-periphery-transcript.md](demo-periphery-transcript.md) (verify evidence + SWT residual confirmed out of matrix).

---

### Wrap-up
Story 7.3 docs amend already merged in [PR #166](https://github.com/zhmachenkov-d/ha_smart_hvac/pull/166). This walkthrough accepted Intent → Broad strokes → ADR → CONTEXT+AGENTS → Knowledge+banners → Periphery. Formal reviews: Intent/ADR/CONTEXT clean; Broad strokes 1 patch (relative links). Plan status still `built` (user marks ticket done).

Suggested follow-through:
1. Commit remaining walkthrough dirt on `chore/walkthrough-story-7-3-intent-review`
2. Push branch + open PR for walkthrough/plan evidence
3. Mark story 7.3 plan `done` (`tickets.py mark` / Sofia board)
4. Next board: **7.2** HITL house yaml (ready) and/or **7.4** after 7.2+7.3 done

Do not run push/mark until the user confirms.

---
### Findings
- [x] Broad strokes relative link depth (Formal review F1) — fixed `../../../`
