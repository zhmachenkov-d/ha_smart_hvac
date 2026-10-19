# Brownfield: water path today → weather-curve only

## Today (to be replaced on the SWT path)

- Multi-Zone Coordinator selects Critical Zone; ADRC Controller runs LADRC on Critical Zone air temperature and commands Set Water Temperature as `clamp(u_ff + u_track)` (ADR 0002).
- Online ωc auto-tune adapts Controller Bandwidth from tracking error while Plant Management is on (ADR 0003); persistence in `ladrc_tune_state.json`.
- Blow-up soft-kill, latch decay, and directional ωc gates exist to limit LADRC-on-water failure modes — they become obsolete when tracking is removed from SWT.

## Target law (this spec)

| Plant Management | Heating Demand | Set Water Temperature |
| --- | --- | --- |
| off | any | no write; clear controller state |
| on | none | write `0`; clear water-path controller state |
| on | yes | write `clamp(weather_feedforward)` only |

Heating Demand is an any-zone boolean. **Critical Zone is not an SWT driver.**

Weather Feedforward parameters: house-commissioned (CAP-6) and **auto-corrected from the rise rate of the zone with largest Zone Error** among zones with Heating Demand (CAP-7). That max-error identification feeds FF params only — never an air tracking term on SWT.

## Clamp note

- `setpoint_min` stays **40**. Soft weather-curve `u_ff` below 40 still writes at least 40 under demand; windup-to-`setpoint_max` is what this wave removes, not soft sub-min water.

## Removal surface (code + docs)

- LADRC observer/controller use for forming SWT; `u_track` in the water command.
- ωc auto-tune and its persistence for the water path.
- Critical Zone selection on the SWT / control-tick path.
- ADR 0002 / ADR 0003 as governing water-control decisions — **superseded by a new ADR** stating weather-curve-only SWT + FF commissioning/auto-correct.
- CONTEXT.md / AGENTS.md language that states Critical Zone air drives LADRC for Set Water Temperature — update with the new ADR.

## Reactivity (CAP-8 follow-on)

- **Today:** SWT evaluation runs on periodic `control_interval` only (`run_every` in the HVAC App).
- **Target:** Same CAP-1…CAP-3 gate law also re-runs when Plant Management, any configured thermostat `hvac_action` or setpoint, any configured zone air temperature, or Outdoor Temperature changes, without waiting solely for the next periodic tick.
- **CAP-7:** Rise-rate window / I1 sampling advance **only** on periodic `control_interval` evaluations; event re-evaluations must not advance those samples.

## Out of this brownfield wave

- Zone climate on/off and Sonoff TRVZB continuous opening remain HA / later initiatives.
- MADRC remains undecided (unchanged).
- Event-only (no periodic) scheduling is a non-goal unless later decided.
