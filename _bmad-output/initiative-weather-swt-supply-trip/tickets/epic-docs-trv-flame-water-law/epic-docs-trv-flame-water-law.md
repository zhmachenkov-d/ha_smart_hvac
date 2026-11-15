---
type: epic
title: "Docs: TRV + flame water law"
parent: initiative-weather-swt-supply-trip
covers: ["R4", "R7", "R8"]
sources:
  - _bmad-output/initiative-weather-swt-supply-trip/initiative-weather-swt-supply-trip.md
companions: []
after: []
refined: false
risk: medium
---

# Docs: TRV + flame water law

## Description
Align ADR, CONTEXT, AGENTS, and `knowledge/` with the shipped weather-curve + TRV soft-close + flame short-on water law. Amend or supersede the supply-trip portion of ADR 0007; remove live supply rise-rate trip language; keep CAP-7 out. Does not change runtime behavior owned by epics 4–5.

## Outcome
Operators and agents read one water law — weather curve, TRV idle max-close, flame short-on trip — matching the App.

## Done when
1. Live ADR/CONTEXT/AGENTS describe curve + TRV soft-close + flame trip (not supply rise-rate trip as live anti-cycle).
2. `knowledge/` live pages match; supply-trip-only pages are historical or removed from live law.
3. CAP-7 / `ff_auto_correct_state.json` remain absent from live commissioning language.

## Boundaries
Owns domain-doc amend after TRV + flame ship. Does not own TRV or flame runtime (epics 4–5). Must not restore CAP-7 or supply rise-rate as live law.

- Touch point: `docs/adr/`, `CONTEXT.md`, `AGENTS.md`, `knowledge/` — owner: this epic
- Must not change: Exclusive Session; runtime from epics 4–5 except doc accuracy

## References
- parent — `_bmad-output/initiative-weather-swt-supply-trip/initiative-weather-swt-supply-trip.md`, Requirements R4, R7, R8
- adr — `docs/adr/0007-weather-curve-supply-trip-swt.md` (trip portion to amend/supersede)
- sibling — `_bmad-output/initiative-weather-swt-supply-trip/tickets/epic-trv-idle-max-close/epic-trv-idle-max-close.md`
- sibling — `_bmad-output/initiative-weather-swt-supply-trip/tickets/epic-replace-supply-trip-with-flame/epic-replace-supply-trip-with-flame.md`

## Notes
- Waits on epic-replace-supply-trip-with-flame because: TRV soft-close and flame short-on must be shipped so docs match the App.
- Shared covers: R4 with epic 1/3 (path/prior docs there; this epic amends live docs for TRV+flame); R7/R8 wording refresh here.
- Decision: Envelope approved thin (`refined: false`) — re-slice 2026-11-15; refine before stories.
- Offer: `bmad-architecture` / ADR authoring when this epic is refined (0007 amend vs new ADR).
