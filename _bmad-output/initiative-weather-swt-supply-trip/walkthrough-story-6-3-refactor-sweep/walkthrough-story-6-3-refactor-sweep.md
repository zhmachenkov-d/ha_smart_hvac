# Walkthrough: Story 6.3 — Refactor sweep
Target: Plan draft (pre-build) — [story-refactor-sweep-plan.md](../tickets/epic-docs-trv-flame-water-law/tickets/story-refactor-sweep-plan.md) · epic-docs entry 3

**Current block:** Periphery (open)

## Blocks
- [x] **Intent** — done (Demo inventory; Second opinion I→B; user accepted)
- [x] **Broad strokes** — done (Demo transcript)
- [x] **Slice: Plan draft** — done (Formal review patch-all; tickets.toml entry 3)
- [ ] **Periphery** — open
- [ ] **Wrap-up** — open

## Review status
In progress — Periphery.

---

### Intent
Source: ticket + Demo scope lock → frozen in [story-refactor-sweep-plan.md](../tickets/epic-docs-trv-flame-water-law/tickets/story-refactor-sweep-plan.md).

**Problem:** Deferred-work still lists settled documentation debt after 6.1/6.2 aligned live agent law.

**Approach:** Documentation-only hygiene — CAP-8 lag reword; prune A–F (+ E); I=B prune-with-cite; leave G–H and `control_event` docstring.

Review notes: Demo — [demo-intent-deferred-inventory.md](demo-intent-deferred-inventory.md). Second opinion — I→B. Intent done.

---

### Broad strokes
1. [deferred-work.md](../deferred-work.md) — prune / Settled I / leave G–H
2. [adr-cap8-shared-ff-demand-writer.md](../../../../docs/decisions/adr-cap8-shared-ff-demand-writer.md) — drop AGENTS sticky-latch «until epic 3»
3. [story-refactor-sweep-plan.md](../tickets/epic-docs-trv-flame-water-law/tickets/story-refactor-sweep-plan.md) — frozen Always/Never
4. [tickets.toml](../tickets/epic-docs-trv-flame-water-law/tickets/tickets.toml) entry `id=3` — description/verify aligned in Formal review

Review notes: Demo — [demo-broad-strokes-transcript.md](demo-broad-strokes-transcript.md). Broad strokes done.

---

### Slice: Plan draft
Frozen Intent + ordered Tasks + blocking Verify in [story-refactor-sweep-plan.md](../tickets/epic-docs-trv-flame-water-law/tickets/story-refactor-sweep-plan.md). Formal review patch-all: CAP-8→C order, tickets path+verify (G–H exempt), heading cites, narrow A, blocking `rg`.

Review notes: Formal review — patch-all applied; triage log filled. Plan draft done.

---

### Periphery
Status: Open

Adjacent debt **not** in 6.3 (plan Never/OUT) — know it exists so the sweep does not accidentally absorb it.

1. [deferred-work.md](../deferred-work.md) (Prelude-isolation header) — **G–H** accuracy×Outdoor-fail / empty-zone spy isolation tests (code/test)
2. `apps/ha_smart_hvac/hvac_app.py` (`control_event` docstring) — still “shared prelude + FF…” while body runs `_apply_trv_law` first; epic Boundaries keep code remediation out
3. [0005-fixed-pid-swt.md](../../../../docs/adr/0005-fixed-pid-swt.md) / [0006-optional-rls-adaptive-pid.md](../../../../docs/adr/0006-optional-rls-adaptive-pid.md) — live-pointer to 0008; historical bodies still present-tense PID/RLS (A narrowed: no body demotion in 6.3)
4. [house-calibration.md](../../../../docs/house-calibration.md) §1 — table stays Outdoor/plant/zones; intro vs §1 plant-off flame-clear gap called out in Settled note only
5. Open PR #158 (`docs/6-2-…`) — 6.3 build should wait on / branch from post-6.2 base; plan step 1 re-spot-reads inventory on the implementing branch

---

### Wrap-up
Status: Open

(placeholder)
