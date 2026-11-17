# Walkthrough: Story 6.3 — Refactor sweep
Target: Plan draft — [story-refactor-sweep-plan.md](../tickets/epic-docs-trv-flame-water-law/tickets/story-refactor-sweep-plan.md) · branch `chore/6-3-refactor-sweep-plan` · `5f4b661`+

**Current block:** Wrap-up (follow-through 1–3 in progress)

## Blocks
- [x] **Intent** — done (Demo; Second opinion I→B)
- [x] **Broad strokes** — done (Demo)
- [x] **Slice: Plan draft** — done (Formal review patch-all)
- [x] **Periphery** — done (presented)
- [x] **Wrap-up** — done (user confirmed follow-through 1–3: commit · push+PR · implement)

## Review status
Wrap-up follow-through in progress — commit narrative, push+PR, implement plan.

---

### Intent
**Problem:** Deferred-work still lists settled documentation debt after 6.1/6.2 aligned live agent law.

**Approach:** Documentation-only hygiene — CAP-8 lag reword; prune A–F (+ E); I=B prune-with-cite; leave G–H and `control_event` docstring.

Review notes: [demo-intent-deferred-inventory.md](demo-intent-deferred-inventory.md); I→B accepted.

---

### Broad strokes
1. [deferred-work.md](../deferred-work.md) — prune / Settled I / leave G–H  
2. [adr-cap8-shared-ff-demand-writer.md](../../../../docs/decisions/adr-cap8-shared-ff-demand-writer.md) — drop AGENTS sticky-latch «until epic 3»  
3. [story-refactor-sweep-plan.md](../tickets/epic-docs-trv-flame-water-law/tickets/story-refactor-sweep-plan.md) — frozen Always/Never  
4. [tickets.toml](../tickets/epic-docs-trv-flame-water-law/tickets/tickets.toml) entry `id=3` — verify aligned  

Review notes: [demo-broad-strokes-transcript.md](demo-broad-strokes-transcript.md).

---

### Slice: Plan draft
Frozen plan + ordered Tasks + blocking Verify. Formal review patch-all applied.

---

### Periphery
OUT: G–H tests; `control_event` docstring; ADR 0005/0006 body demotion; §1 table expand; build after 6.2 base (merged).

---

### Wrap-up
User confirmed follow-through: (1) commit narrative/log, (2) push + PR, (3) implement 6.3 per frozen plan.
