---
id: 4
type: spike
title: "FF rise-rate auto-correct rule"
parent: epic-weather-curve-swt-only
covers: [CAP-7]
after: [1]
refined: true
hitl: true
risk: high
---

# FF rise-rate auto-correct rule

## Description

CAP-7 requires auto-correcting Weather Feedforward parameters from the max-error Heating Demand zone’s air temperature rise rate, without adding an air tracking term to Set Water Temperature. Stories 1.3 (ADR/docs) and 1.5 (implementation) cannot proceed until the rise-rate signal, adaptation formula, guards, persistence shape, and explicit non-goals are chosen and recorded.

## Approach

Time box: one focused design session (target under half a day). Good enough: 1.5 can implement without inventing any law, and 1.3 can state the same law in the new ADR.

1. **Signal.** Define how rise rate is measured from the max-error zone among zones with Heating Demand (window, units, missing/noisy samples, what happens when the max-error zone switches).
2. **Law.** Choose which FF parameters move (`base`, `slope`, both, or another equivalent), the update rule and direction relative to observed rise rate vs expected heating response, and how that stays consistent with yaml commissioning (CAP-6).
3. **Guards.** Decide when adaptation may run and when it must freeze or skip (Heating Demand, Plant Management, deadband, rate limits, bounds, saturation at SWT clamps, zone-identity change, and any other freeze conditions). Borrow patterns from the superseded ωc tuner only where they still fit a feedforward-only law — do not restore tracking.
4. **Persistence.** Choose where adapted parameters live across restarts, what is not persisted, and how that relates to yaml-commissioned defaults (CAP-6 is yaml-only; auto-correct must not invent new HA entities unless this spike explicitly decides otherwise and updates CAP-6’s commission boundary).
5. **Non-goals.** List what this spike rejects so 1.5 cannot reintroduce air→SWT tracking, Critical Zone as SWT driver, or ωc-style tracking-error adaptation under another name.
6. **Sign-off.** Operator (ticket owner) accepts the written decision before 1.5 starts.

No runtime prototype is required in this spike unless analysis shows the formula is unsafe without a short offline check; if so, record that check beside the decision note.

## Acceptance Criteria

1. **Given** the locked CAP-7 zone rule (max Zone Error among Heating Demand zones), **when** the spike completes, **then** a written decision defines the rise-rate signal (measurement, window, and behavior on zone switch or missing samples) so 1.5 does not invent it.
   Verify: decision note lists signal definition under a clear heading.

2. **Given** Weather Feedforward as linear `base` / `slope` / `comfort_ref`, **when** the spike completes, **then** the decision states which parameters adapt, the update formula (including direction), and how adapted values interact with yaml-commissioned defaults.
   Verify: decision note states formula and commission interaction in enough detail that 1.5 can code it without new design choices.

3. **Given** Plant Management / Heating Demand gates and SWT clamp bounds, **when** the spike completes, **then** the decision lists adaptation guards and freeze/skip conditions, including that adaptation never adds an air term to the SWT command.
   Verify: decision note has an explicit Guards section and a Non-goals / must-not line covering air→SWT tracking.

4. **Given** restarts and Exclusive Session operation, **when** the spike completes, **then** the decision names persistence shape (store location/format, what survives restart, what stays ephemeral) without requiring new HA entities unless the decision explicitly overrides the CAP-6 yaml-only commission boundary and says so.
   Verify: decision note has a Persistence section; if HA entities are introduced, epic Notes get a dated Decision amending CAP-6.

5. **Given** stories 1.3 and 1.5 wait on this answer, **when** the operator accepts the decision, **then** the chosen rule is recorded where both stories will find it, and epic Notes carry a dated Decision summarizing formula, guards, and persistence.
   Verify: decision note path named below; epic Notes Decision line present with date; operator named on that line.

## References

- parent — `_bmad-output/initiative-weather-curve-zone-actuators/epic-weather-curve-swt-only/epic-weather-curve-swt-only.md`
- spec — `_bmad-output/initiative-weather-curve-zone-actuators/spec-weather-curve-swt-only/spec-weather-curve-swt-only.md`, CAP-7 and Constraints
- companion — `_bmad-output/initiative-weather-curve-zone-actuators/spec-weather-curve-swt-only/brownfield.md`
- forge — `_bmad-output/initiative-weather-curve-zone-actuators/forge-weather-curve-zone-actuators/forge-weather-curve-zone-actuators.md`, Locked FF params / Rejected air→SWT
- domain — `CONTEXT.md`, Weather Feedforward
- adr (pattern only, to be superseded) — `docs/adr/0003-online-ladrc-omega-c-auto-tune.md`, Guards and Persistence shape as prior art — not the CAP-7 law

## Notes

- Decision target path: `_bmad-output/initiative-weather-curve-zone-actuators/epic-weather-curve-swt-only/spike-ff-rise-rate-auto-correct-rule-decision.md` (created when the spike runs).
- High-risk external check: operator sign-off on the decision note before 1.5 starts (criterion 5); 1.7 live Exclusive Session remains the later plant check, not this spike’s substitute.
- Assumption: `comfort_ref` stays commission-only and is not auto-corrected unless the decision explicitly says otherwise.
- Assumption: no runtime prototype unless the formula cannot be trusted on paper; default deliverable is the decision note only.
- Open question (settle at refine or as first spike step): should adapted FF values override yaml on disk, live in a separate persist file with yaml as defaults, or another shape? Spike owns the answer; do not leave it for 1.5.
- Waiting tickets: 1.3 (ADR must state CAP-7 law/persistence), 1.5 (implements the law).
