# House calibration
How to calibrate the HVAC App for a specific house. Calibration is **manual `apps.yaml` commissioning** of Outdoor Temperature, Weather Feedforward (`weather_feedforward`), and plant rails. Optional Zone `weight` is wiring residual only (parsed/validated; not water-law commission). There is no relay/step commissioning procedure.

Copy [`apps.yaml.example`](../apps.yaml.example) to `apps.yaml` next to the installed `ha_smart_hvac/` package, then work through the sections below. Never commit live house entity IDs.

**Domain-docs lag:** [`CONTEXT.md`](../CONTEXT.md), ADR 0005/0006, and AGENTS.md may still describe fixed PID / RLS as the live water law until epic 3 supersedes them. Until then, **this document and [`apps.yaml.example`](../apps.yaml.example) are the commissioning source of truth** (Outdoor Temperature + Weather Feedforward only). Exclusive Session: [ADR 0001](adr/0001-exclusive-session-against-production-ha.md).

## 1. House wiring (required)
Replace every `YOUR_*` placeholder:

| Key | Role |
| --- | --- |
| `outdoor_temperature` | Outdoor air temperature sensor used by Weather Feedforward |
| `plant_management` | Switch: when off, the App stops Set Water Temperature writes and leaves SWT untouched |
| `plant_setpoint` | OpenTherm Set Water Temperature (`number` entity) |
| `zones[]` | Per Zone: air temperature sensor + one or more climate thermostats; optional `weight` (default `1.0`) |

Without correct wiring the App is not bound to the house.

## 2. Plant clamps and interval
```yml
setpoint_min: 50
setpoint_max: 60
control_interval: 300
```
`setpoint_min` / `setpoint_max` bound the commanded Set Water Temperature; match them to the boiler / primary circuit limits. The example template uses `50` / `60` — house yaml may differ after commissioning. `control_interval` (a whole number of seconds, at most `86400`, default `300`) is the periodic schedule for demand Set Water Temperature writes under Plant Management and Heating Demand.

## 3. Weather Feedforward (yaml commission)
Under Heating Demand the App commands:

\[
\text{SWT} = \operatorname{quantize\_command}(u_{ff}),\quad u_{ff} = \texttt{base} + \texttt{slope} \times (\texttt{comfort\_ref} - T_{out})
\]

where \(T_{out}\) is Outdoor Temperature and `quantize_command` is round-to-0.1(clamp(…)) into `setpoint_min`…`setpoint_max`.

```yml
weather_feedforward:
  base: 37
  slope: 0.9
  comfort_ref: 20
```

Copy these keys/values from [`apps.yaml.example`](../apps.yaml.example) as the starting template; house yaml may differ after commissioning. Mild Outdoor with these defaults can pin SWT to `setpoint_min` (e.g. ~10 °C outdoor → \(u_{ff}\) ≈ 46, still below 50) until rails or FF coefficients are retuned under operator HITL.

Units / meaning:

| Key | Unit | Meaning |
| --- | --- | --- |
| `base` | °C water | FF baseline water temperature |
| `slope` | °C water / °C outdoor | Gain on `(comfort_ref − T_out)`; negative slopes are allowed |
| `comfort_ref` | °C outdoor | Outdoor temperature where FF equals `base` |

Omitted `base` / `slope` / `comfort_ref` under a present `weather_feedforward:` mapping take the example defaults (`37` / `0.9` / `20`). Optional `zones[].weight` is accepted and validated at parse time but unused on the live Outdoor+FF demand path (Heating Demand gates on thermostat `hvac_action`; SWT is Outdoor+FF only).

### Rejected commission values
Each of these logs `HVAC config error: …` at startup and the App does not run:

- Missing `outdoor_temperature` or `weather_feedforward`
- A non-numeric value (text that is not a number, `null`, a list, or `true` / `false`) or a non-finite one (`nan`, `inf`) for `setpoint_min`, `setpoint_max`, `control_interval`, any `weather_feedforward` numeric (`base` / `slope` / `comfort_ref`), or a Zone `weight`
- A fractional `control_interval` (`60.7`, `0.5`); `60.0` is accepted as `60`
- A non-positive `control_interval` (`0`, `-1`)
- A `control_interval` above `86400` (one day)
- A Zone `weight` < `0`
- `weather_feedforward` that is not a mapping, or that includes unknown sub-keys (e.g. `auto_correct`)
- Empty / non-string entity IDs for Outdoor, plant, or Zones
- `setpoint_min` ≥ `setpoint_max`

Leftover top-level `pid`, `base_water_temp`, and `boiler_water` keys are ignored (logged once as `HVAC config: ignoring legacy or unknown keys: …`) and do not drive Set Water Temperature — delete them.

## 4. Safe order on a live house
1. Fill entity IDs (including `outdoor_temperature`) and Zones.
2. Set sensible `setpoint_min` / `setpoint_max`.
3. Commission `weather_feedforward` (`base` / `slope` / `comfort_ref`).
4. Enable Plant Management; watch water temperature and Zone air under demand and idle (write `0`).
5. Disable Plant Management to stop all Set Water Temperature writes and leave SWT untouched.

## Upgrading from fixed PID commissioning
Outdoor Temperature + Weather Feedforward is the live water law. Leftover `pid`, `base_water_temp`, and `boiler_water` keys in `apps.yaml` are ignored and logged as one WARNING at startup (`HVAC config: ignoring legacy or unknown keys: …`, which also names any other unknown key, including unknown zone sub-keys such as a misspelled `weigth`); delete them. `rls_state.json` in the AppDaemon app directory is no longer written on the demand path and can be deleted. Unknown `weather_feedforward` sub-keys (including CAP-7 `auto_correct`) are a config error — strip them.

## What is not calibrated here
- Relay or open-loop step commissioning
- Adaptive RLS / `rls_state.json` / fixed PID gains — not on the live water path (modules may remain on disk until epic 3)
- CAP-7 rise-rate auto-correct / `ff_auto_correct_state.json` — stay out
