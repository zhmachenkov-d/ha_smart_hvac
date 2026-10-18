---
id: SPEC-weather-curve-swt-only
companions:
  - brownfield.md
  - architecture-diagrams.md
  - ../../../../CONTEXT.md
sources:
  - ../forge-weather-curve-zone-actuators/forge-weather-curve-zone-actuators.md
---

> **Canonical contract.** This SPEC and the files in `companions:` are the complete, preservation-validated contract for what to build, test, and validate. Source documents listed in frontmatter are for traceability — consult them only if you need narrative rationale or prose color this contract intentionally omits.

# Weather-curve SWT only

## Why

**Pain to solve.** With Critical Zone air already near setpoint (`error ≈ 0.2°C`, `y` flat) and moderate Weather Feedforward, LADRC tracking on the water path still grows `u_track` until Set Water Temperature pegs at `setpoint_max`. Feedforward alone was not the culprit — closed-loop air→SWT keeps raising water when the room barely moves. Narrow option A replaces that law with weather-curve-only water under existing Plant Management / Heating Demand gates, without waiting on proportional TRV control.

## Capabilities

- **CAP-1**
  - **intent:** When Plant Management is on and Heating Demand is present, the system can command Set Water Temperature from Weather Feedforward alone (clamped), with no air-temperature tracking contribution.
  - **success:** On a demand tick, the written command equals `clamp(weather_feedforward)` for that outdoor/comfort inputs and current FF parameters; no `u_track` (or equivalent tracking term) is added.

- **CAP-2**
  - **intent:** When Plant Management is on and no Zone has Heating Demand, the system can idle the plant water setpoint at zero and clear water-path controller state.
  - **success:** Idle path writes `0` to Set Water Temperature and does not leave LADRC/tuner water-path state active for the next demand tick.

- **CAP-3**
  - **intent:** When Plant Management is off, the system can stay hands-off on the plant water setpoint.
  - **success:** No Set Water Temperature write occurs; controller state is cleared. Writing `0` is not used as the off representation.

- **CAP-4**
  - **intent:** Maintainers and agents can treat LADRC-on-Critical-Zone water control, online ωc auto-tune on water, and Critical Zone as an SWT driver as removed, not dormant.
  - **success:** Code on the SWT path no longer runs LADRC tracking or ωc adaptation; SWT is not driven by Critical Zone air; a **new ADR** supersedes ADR 0002 and ADR 0003; CONTEXT/AGENTS no longer describe Critical Zone air as driving Set Water Temperature (max-error zone may remain only as the CAP-7 rise-rate source).

- **CAP-5**
  - **intent:** Automated tests can lock the weather-curve-only SWT law so tracking windup cannot return silently.
  - **success:** Tests cover (a) demand → `clamp(u_ff)` only, (b) Plant-on idle → write `0` + clear, (c) Plant-off → no write + clear, (d) a near-setpoint flat-air scenario that formerly grew `u_track` to max no longer drives command above the feedforward clamp toward `setpoint_max` via tracking, (e) max-error zone air does not appear as an additive tracking term on SWT.

- **CAP-6**
  - **intent:** Operators can commission Weather Feedforward parameters for the house so the demand-path water command matches the intended outdoor curve.
  - **success:** Base/slope (or equivalent) are configurable and used by CAP-1; changing them changes `clamp(u_ff)` under the same outdoor/comfort inputs without reintroducing air→SWT tracking.

- **CAP-7**
  - **intent:** The system can auto-correct Weather Feedforward parameters from the temperature rise rate of the zone with the largest Zone Error among zones with Heating Demand.
  - **success:** Under sustained Heating Demand, FF parameters move in response to that max-error zone’s measured air temperature rise rate; SWT command remains `clamp(weather_feedforward)` with updated params — not `u_ff + u_track`. Identifying the max-error zone for rise-rate must not restore Critical Zone / air-error as an SWT tracking driver.

## Constraints

- Plant Management off means **no write** and cleared state — not “write 0”.
- Heating Demand idle write-`0` runs only when Plant Management is on.
- CH / circuit gate is the existing `plant_management` entity; no additional boiler-circuit signal.
- App does not command zone on/off actuators or TRV valve percent in this wave.
- Remove LADRC and ωc auto-tune from the SWT path now; do not leave them dormant for water.
- Do **not** use Critical Zone / max-error zone air to form an SWT tracking term; Heating Demand for the SWT gate is an any-zone boolean.
- CAP-7 may identify the zone with largest Zone Error solely as the rise-rate signal for FF auto-correct.
- `setpoint_min` stays **40**; soft weather-curve `u_ff` below min still clamps up to min — do not lower min in this wave to chase softer water.
- Document the new SWT law in a **new ADR** that supersedes 0002 and 0003.
- Domain language for Plant Management, Heating Demand, Weather Feedforward, and Set Water Temperature follows `CONTEXT.md`; retire Critical Zone as an SWT driver when docs update with the new ADR.
- CAP-7 auto-correct adjusts FF parameters only; it must not add an air-error tracking term to the SWT command.

## Non-goals

- LADRC/MADRC control of continuous Sonoff TRVZB valve opening (option B valve wave).
- Keeping LADRC on SWT with deadband / anti-windup (option C).
- App ownership of zone on/off or floor actuators.
- Adopting MADRC for this plant.
- Lowering `setpoint_min` below 40 to deliver sub-min curve water.
- Keeping Critical Zone selection for logging-only or “future valves” in this wave.
- Reintroducing Critical Zone / max-error air as a closed-loop driver of Set Water Temperature under another name.

## Success signal

Reproduce the logged windup shape (near-zero Zone Error, flat air, outdoor around +10°C, moderate `u_ff`): Set Water Temperature stays at the feedforward clamp (with `setpoint_min` still 40) and does not climb to `setpoint_max` via a tracking term; FF params are commissionable (CAP-6) and auto-correctable from the max-error zone’s rise rate (CAP-7); demonstrated by CAP-5 tests and a new ADR that supersedes 0002/0003.
