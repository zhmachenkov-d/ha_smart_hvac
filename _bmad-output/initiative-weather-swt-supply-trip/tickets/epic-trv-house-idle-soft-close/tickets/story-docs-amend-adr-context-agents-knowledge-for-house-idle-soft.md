---
id: 3
type: story
title: "Docs: amend ADR/CONTEXT/AGENTS/knowledge for house-idle soft-close"
parent: epic-trv-house-idle-soft-close
covers: [R1, R2]
after: [1]
hitl: false
risk: medium
refined: true
---

# Docs: amend ADR/CONTEXT/AGENTS/knowledge for house-idle soft-close

## Description
Amend live ADR 0008, CONTEXT.md, AGENTS.md, and knowledge/ so they document the house-idle soft-close law already shipped in entry 1 — without inventing App behavior or touching house yaml.

1. Replaces plant-on overshoot hysteresis and accuracy-listen soft-close teaching with house-idle floor → hold-or-demand → 100 so epic R1/R2 read true in agent-facing docs.
2. Marks overshoot/accuracy TRV decision notes historical and drops them from live cite lists so agents cannot treat them as current law.
3. Clears accuracy from live `control_event` listener inventories and states leftover yaml accuracy is ConfigError.
4. Leaves CAP-7 out of live commissioning language and keeps Critical Zone / never-opening fences.

## Requirements
1. **Source of truth is tracer law** (R1, R2)
   **Given** ADR 0008, CONTEXT.md, AGENTS.md, and live knowledge soft-close prose
   **When** an agent reads how soft-close behaves
   **Then** the prose matches entry 1 Requirements 1–7 (first Plant-on all-idle observe floors and arms hold once; no re-arm while hold active; hold expiry while idle writes 100 and stays at 100 without re-floor; orphan/token-mismatch expiry is a no-op; any Heating Demand — cold start, rising-edge, or sustained — writes 100 and cancels/never arms hold; return to all-idle floors and arms a new hold; plant-off writes 100 and cancels hold)
   **And** epic R1 “rising-edge only” wording is not copied into live docs
   **Failure:** docs teach rising-edge-only cancel, omit hold arm/orphan/return-to-idle, or invent law not in entry 1

2. **ADR 0008 TRV and Event path** (R1, R2, epic C4, C5, C7)
   **Given** ADR 0008 after amend
   **When** the TRV soft-close section and Event-path listener list are read
   **Then** plant-on soft-close is house-idle floor + `trv_soft_close_hold_s` hold (defaults 80 / 300) with demand and plant-off cancel as in entry 1
   **And** plant-off writes closure 100 and cancels the soft-close hold (no `_trv_overshoot_latched` keep/clear prose)
   **And** commissioned = closure-only; leftover `accuracy` is ConfigError; accuracy is absent from the Event-path listener list and from soft-close law
   **And** App never writes `valve_opening_degree`; Critical Zone does not drive soft-close
   **And** the live cite list no longer treats the three overshoot/accuracy TRV decisions as live soft-close law
   **Failure:** overshoot hysteresis, accuracy listen, or overshoot-latch plant-off prose remains as live ADR law

3. **CONTEXT and AGENTS match** (R1, R2, epic C5)
   **Given** CONTEXT.md TRV soft-close / Weather Feedforward listener text and AGENTS.md `bmad:context` Conventions
   **When** those passages are read
   **Then** they describe the same house-idle soft-close law as ADR 0008 (floor + hold + any-demand/plant-off cancel; closure-only; no overshoot latch; no accuracy soft-close listen)
   **And** AGENTS edits stay inside `<!-- bmad:context -->` … `<!-- /bmad:context -->`; the Verified stamp line is unchanged
   **Failure:** CONTEXT/AGENTS still teach overshoot/accuracy soft-close, or AGENTS is edited outside the markers / stamp bumped

4. **Knowledge live pages** (R1, R2)
   **Given** `knowledge/concepts/trv-soft-close.md`, `knowledge/concepts/index.md`, and other live knowledge pages that still commission accuracy or overshoot as soft-close law
   **When** those pages are amended
   **Then** `trv-soft-close.md` (frontmatter + body + citations) teaches house-idle soft-close and cites ADR 0008 plus live TRV prelude (not overshoot/accuracy decisions as live)
   **And** the concepts index TRV blurb no longer says plant-off keeps overshoot latch
   **And** `outdoor-temperature.md` (and any other live listener inventory under knowledge/) no longer lists commissioned accuracy as a soft-close/`control_event` input
   **And** `knowledge/log.md` gains an append-only Fact for the house-idle soft-close docs amend
   **Failure:** primary page fixed but index/outdoor (or siblings) still teach overshoot/accuracy as live

5. **Zombie TRV decisions historical** (R1, epic C5)
   **Given** `docs/decisions/adr-trv-write-gated-overshoot-latch.md`, `docs/decisions/adr-trv-plant-off-no-latch-clear.md`, and `docs/decisions/adr-trv-accuracy-shared-control-event.md`
   **When** each is opened
   **Then** a leading historical banner states they are not live soft-close law and points live soft-close to ADR 0008 house-idle hold
   **And** no new soft-close hold decision file is required — hold/token/orphan law lives in ADR 0008 (and CONTEXT/AGENTS/knowledge)
   **Failure:** any of the three still reads as live law without a banner, or live docs keep citing them as current soft-close

6. **CAP-7 out; hygiene verify** (R1)
   **Given** the amended live docs set
   **When** CAP-7 / `ff_auto_correct_state.json` commissioning language and the verify commands are checked
   **Then** CAP-7 stays absent from live commissioning language in ADR 0008, CONTEXT, AGENTS, and live knowledge soft-close/SWT pages
   **And** `rg` over those live paths finds no live soft-close teaching of `_trv_overshoot_latched` or commissioned accuracy listen except inside historical banners / clearly marked historical lines
   **And** `uv run pytest` and `uv run ruff check apps/ha_smart_hvac tests` are clean
   **Failure:** CAP-7 reappears as live commission, overshoot/accuracy strings remain as live law, or pytest/ruff fail

## Boundaries
- Must not change: weather-curve Set Water Temperature law; flame short-on observe/latch/clear; Exclusive Session; Heating Demand = thermostat `hvac_action=heating`
- Must not: edit App runtime or tests beyond running them; edit `apps.yaml.example`; edit house `apps/apps.yaml` (entry 2); restore temperature overshoot as live soft-close; require accuracy for commissioned TRV; invent runtime not in entry 1
- Soft-close docs must not depend on house yaml state — example schema and entry 1 law are enough (parallel with entry 2 is fine)
- This story makes all *live* soft-close pointers safe; entry 4 only prunes deferred dead code/tests/orphan mentions already parked in plans — not live-law corrections left undone here
- Keep `docs/decisions/adr-trv-before-water-prelude.md` as live (prelude ordering unchanged) unless a one-line stale overshoot cross-cite must be fixed
- Do not author a new ADR number; amend ADR 0008 in place

## References
- parent — `_bmad-output/initiative-weather-swt-supply-trip/tickets/epic-trv-house-idle-soft-close/epic-trv-house-idle-soft-close.md`, Requirements R1–R2; Constraints C4, C5, C7; Done when (4–5); Notes hold Decision
- prerequisite — `_bmad-output/initiative-weather-swt-supply-trip/tickets/epic-trv-house-idle-soft-close/tickets/story-tracer-trv-house-idle-soft-close.md`, Requirements 1–7 (docs SoT for soft-close behavior)
- sibling pattern — `_bmad-output/initiative-weather-swt-supply-trip/tickets/epic-docs-trv-flame-water-law/tickets/story-tracer-adr-agents-context-for-trv-flame-water-law-plan.md`, Always/Never historical-banner + AGENTS `bmad:context` + Verified stamp leave-as-is

## Notes
- Decision: Docs SoT for soft-close is entry 1 Requirements 1–7; do not copy epic R1 “rising-edge only” into live docs (2026-11-20).
- Decision: Mark the three overshoot/accuracy TRV decisions historical with live-pointer to ADR 0008; no new soft-close hold decision file (2026-11-20).
- Decision: Edit AGENTS only inside `bmad:context`; leave Verified stamp unchanged (match epic 6.2) (2026-11-20).
- Decision: 7.3 owns live-pointer safety; 7.4 owns deferred prune only (2026-11-20).
- Decision: knowledge amend includes `trv-soft-close.md`, concepts index TRV blurb, `outdoor-temperature.md` accuracy listener cleanup, and append-only `knowledge/log.md` Fact (2026-11-20).
- Source conflict: parent R1 once said rising-edge-only → 100; settled 2026-11-20 on epic (R1 + hold Decision) and by this story’s SoT Decision — both match tracer Req 3 any Heating Demand.
- Risk reason: wrong docs leave agents following overshoot/accuracy as live soft-close after the App already runs house-idle hold.
- High-risk check beyond criteria: `rg` that ADR 0008, CONTEXT, AGENTS `bmad:context`, and live knowledge concepts have zero live soft-close hits for `_trv_overshoot_latched` / commissioned accuracy listen outside historical banners.
- R1/R2 split: documentary truth here; App law in entry 1; house yaml in entry 2.
- Can run in parallel with entry 2; docs must not require house `apps.yaml`.
- House HITL stays on entry 2 per re-slice Decision (2026-11-20); this story only amends docs after epic 6.
- Waits on entry 1 because: App + example law must exist before docs claim it.
- Builder file matrix (Notes only): `docs/adr/0008-weather-curve-trv-flame-swt.md`; `CONTEXT.md`; `AGENTS.md` (`bmad:context`); `knowledge/concepts/trv-soft-close.md`; `knowledge/concepts/index.md`; `knowledge/concepts/outdoor-temperature.md`; `knowledge/log.md`; historical banners on the three `docs/decisions/adr-trv-*` listed in Requirements 5.
