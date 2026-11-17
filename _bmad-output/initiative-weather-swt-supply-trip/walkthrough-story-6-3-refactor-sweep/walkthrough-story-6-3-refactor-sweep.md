# Walkthrough: Story 6.3 — Refactor sweep
Target: [PR #159](https://github.com/zhmachenkov-d/ha_smart_hvac/pull/159) · branch `chore/6-3-refactor-sweep-plan` · `c4eeb9a`

**Current block:** Wrap-up (done — PR #159 open; merge when ready)

## Blocks
- [x] **Intent** — done (Demo; Second opinion I→B)
- [x] **Broad strokes** — done (Demo)
- [x] **Slice: Plan draft** — done (Formal review patch-all)
- [x] **Periphery** — done (presented)
- [x] **Wrap-up** — done (commit · push+PR · implement; 362 pytest + ruff + blocking rg)

## Review status
Complete — PR #159 open.

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
Follow-through done: CAP-8 reword + deferred Settled epic-6; [PR #159](https://github.com/zhmachenkov-d/ha_smart_hvac/pull/159). Verify: 362 pytest, ruff clean, blocking `rg`/spot-read. Merge when ready.
