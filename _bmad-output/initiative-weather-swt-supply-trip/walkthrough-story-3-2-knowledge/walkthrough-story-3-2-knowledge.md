# Walkthrough: Story 3.2 — knowledge live curve+trip; demote PID/RLS
Target: [PR #143](https://github.com/zhmachenkov-d/ha_smart_hvac/pull/143) · branch `docs/3-2-knowledge-live-curve-trip-demote-pid-rls` · `3291a01`

**Current block:** Wrap-up (awaiting follow-through)

## Blocks
- [x] **Intent** — done
- [x] **Broad strokes** — done
- [x] **Slice: Live SWT pages** — done
- [x] **Slice: Historical demotions** — done
- [x] **Slice: Indexes + log** — done
- [x] **Periphery** — done (presented; Wrap-up chosen)
- [ ] **Wrap-up** — awaiting follow-through

---

### Intent
Source: frozen Intent from plan [story-knowledge-live-curve-trip-demote-pid-rls-plan.md](../tickets/epic-supersede-pid-domain-docs/tickets/story-knowledge-live-curve-trip-demote-pid-rls-plan.md) (Problem + Approach).

**Problem:** ADR 0007 + AGENTS/CONTEXT already teach weather-curve SWT + supply rise-rate trip, but `knowledge/` still presents fixed-PID / RLS (ADR 0005/0006) as the live water law.

**Approach:** Rewrite live SWT-facing knowledge pages to `clamp(u_ff)` + supply trip under ADR 0007; demote PID/RLS pages and ADRC/LADRC/MADRC live-pointers to historical prior art (LADRC pattern); update indexes and append `knowledge/log`. Docs-only — no CAP-7 restore, no module deletes.

---

### Broad strokes
Docs-only realign of knowledge so live water law matches ADR 0007; PID/RLS become historical.

1. [set-water-temperature.md](../../../knowledge/concepts/set-water-temperature.md) — live law rewrite: Weather FF `round-to-0.1(clamp(u_ff))` + dual-gate + supply trip under ADR 0007
2. [outdoor-temperature.md](../../../knowledge/concepts/outdoor-temperature.md) — Outdoor on the demand path / `control_event` listener
3. [rls-adaptive-pid.md](../../../knowledge/concepts/rls-adaptive-pid.md) — LADRC-like demotion: Project note fence; technical body kept as history
4. [knowledge/index.md](../../../knowledge/index.md) — root live-path blurb now ADR 0007
5. [knowledge/log.md](../../../knowledge/log.md) — append-only align Fact for this cutover

Review notes: Test passed — 11/11 rg; 343 pytest; ruff clean.

---

### Slice: Live SWT pages
The primary rewrite replaces fixed-PID/`u_pid`/sticky demand-edge language with Weather Feedforward and supply rise-rate trip. Outdoor moves from «off path» to required `T_out` on the demand writer. Critical Zone stays diagnostics-only but retargets live cite 0005→0007 and clarifies it does not drive the trip.

Places:

- [set-water-temperature.md](../../../knowledge/concepts/set-water-temperature.md)
- [outdoor-temperature.md](../../../knowledge/concepts/outdoor-temperature.md)
- [critical-zone.md](../../../knowledge/concepts/critical-zone.md)

Review notes: Test PASS — rg guards + MUST-floor spot-read on three live SWT pages.

---

### Slice: Historical demotions
Same LADRC project-note pattern — keep literature/mechanics bodies; fence them off the live path; live pointer → ADR 0007 SWT. Decision 1A also retargets one-line companions so nothing still asserts live fixed-PID under 0005.

Worked example: [rls-adaptive-pid.md](../../../knowledge/concepts/rls-adaptive-pid.md)

Same treatment:

- [adrc.md](../../../knowledge/concepts/adrc.md), [ladrc.md](../../../knowledge/concepts/ladrc.md), [madrc.md](../../../knowledge/concepts/madrc.md)
- [multi-zone-coordinator.md](../../../knowledge/concepts/multi-zone-coordinator.md)
- [huang-2018-ladrc-hvac.md](../../../knowledge/references/huang-2018-ladrc-hvac.md), [wang-2026-madrc-sst.md](../../../knowledge/references/wang-2026-madrc-sst.md)

Review notes: Test PASS.

---

### Slice: Indexes + log
Indexes and the append-only log make the cutover discoverable without rewriting historical Facts.

- [knowledge/index.md](../../../knowledge/index.md)
- [concepts/index.md](../../../knowledge/concepts/index.md)
- [log.md](../../../knowledge/log.md) — new `## 2026-11-14` Fact only

Review notes: Test PASS.

---

### Periphery
- [story-knowledge-live-curve-trip-demote-pid-rls-plan.md](../tickets/epic-supersede-pid-domain-docs/tickets/story-knowledge-live-curve-trip-demote-pid-rls-plan.md) — approved build plan + verification guards
- Epic [tickets.toml](../tickets/epic-supersede-pid-domain-docs/tickets/tickets.toml) — entry id=2 (story 3.2)
- Out of scope this PR: [apps/](../../../apps/), [tests/](../../../tests/), ADR bodies, [AGENTS.md](../../../AGENTS.md), [CONTEXT.md](../../../CONTEXT.md); pid/rls module delete = story 3.3

---

### Wrap-up
Review finished; follow-through proposed (commit knowledge + plan + walkthrough, push branch, update/merge [PR #143](https://github.com/zhmachenkov-d/ha_smart_hvac/pull/143)) — awaiting user confirm before any git/gh action.