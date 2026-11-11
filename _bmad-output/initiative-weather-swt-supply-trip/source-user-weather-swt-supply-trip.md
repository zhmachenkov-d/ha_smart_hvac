# Source: weather-curve SWT + supply rise-rate trip

Captured from owner session with Sofia (Product Owner), 2026-11-11.

## Intent

Remove the PID controller from the Set Water Temperature path. Regulate plant water with a weather-dependent algorithm. Detect when supply water heats too fast (interpreted as all thermostatic valves closed) and, in that case, write SWT to 0. Clear that latched state after a timer (~15 min) or when a thermostat opens (Heating Demand appears on a zone that previously had none).

## Decisions (owner-approved)

| Id | Choice |
|----|--------|
| D1 | Path B: restore ADR 0004 feedforward law `u_ff = base + slope × (comfort_ref − T_out)`; CAP-7 curve auto-correct is **out** of this initiative |
| D2 | Rise-rate signal = **supply** water temperature (подача) |
| D3 | Trip only when Plant Management is on **and** Heating Demand is present |
| D4 | Threshold style A: yaml-commissioned `r_max`; default **2 °C/min** |
| D5 | Latch clear: yaml timer default **900 s**, **or** rising-edge Heating Demand on a zone that did not previously have demand |
| D6 | Compute `r_obs` on **every** supply temperature change (not only on `control_interval`) |
| D7 | Remove fixed PID / ∫ / `base_water_temp + u_pid` and optional RLS / `rls_state.json` from live SWT and commissioning |
| D8 | While latched under demand: write **SWT = 0**; do not apply the weather curve until latch clears |
| D9 | Idle / plant-off gate law unchanged in spirit: idle → write 0 + clear ephemeral; plant-off → no write + clear |

## Constraints (owner-approved)

| Id | Rule |
|----|------|
| C1 | AppDaemon `ha_smart_hvac` + existing HA plant entity only |
| C2 | Exclusive Session (ADR 0001) and Heating Demand (`hvac_action=heating`) unchanged |
| C3 | Round-to-0.1 + clamp `setpoint_min`…`setpoint_max` |
| C4 | Critical Zone diagnostics/logging only — not SWT, not trip |
| C5 | Supply entity id yaml-commissioned |
| C6 | No CAP-7 / no `ff_auto_correct_state.json` in this initiative |

## Closed after capture (2026-11-11)

- Q1: New FF defaults — `base=37`, `slope=0.9`, `comfort_ref=20` (from house 72h demand SWT p50≈51.6 / max≈55 and outdoor −0.3…7.6; Tout=0 → 55, Tout=5 → 50.5).
- Q2: Supply / `boiler_water` = `sensor.opentherm_bridge_boiler_water_temperature_degc`.
