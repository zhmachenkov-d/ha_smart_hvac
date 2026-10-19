# House calibration

How to calibrate the HVAC App for a specific house. Calibration is **manual `apps.yaml` commissioning of Weather Feedforward** plus optional **rise-rate auto-correct** of `base` / `slope` ([ADR 0004](adr/0004-weather-curve-swt.md)). There is no relay/step commissioning procedure.

Copy [`apps.yaml.example`](../apps.yaml.example) to `apps.yaml` next to the installed `ha_smart_hvac/` package, then work through the sections below. Never commit live house entity IDs.

Domain terms: [`CONTEXT.md`](../CONTEXT.md). Control decisions: [ADR 0004](adr/0004-weather-curve-swt.md). Exclusive Session: [ADR 0001](adr/0001-exclusive-session-against-production-ha.md).

## 1. House wiring (required)

Replace every `YOUR_*` placeholder:

| Key | Role |
|-----|------|
| `outdoor_temperature` | Outdoor Temperature sensor |
| `plant_management` | Switch: when off, the App does not write Set Water Temperature and clears ephemeral / water-path state; `ff_auto_correct_state.json` is left untouched |
| `plant_setpoint` | OpenTherm Set Water Temperature (`number` entity) |
| `zones[]` | Per Zone: air temperature sensor + one or more climate thermostats |

Without correct wiring the App is not bound to the house.

## 2. Plant clamps

```yaml
setpoint_min: 40
setpoint_max: 55
control_interval: 60
```

These bound the commanded Set Water Temperature. Match them to the boiler / primary circuit limits.

## 3. Weather Feedforward (yaml commission)

Linear outdoor baseline that **is** the demand-path water command (`clamp(u_ff)`):

\[
u_{ff} = \texttt{base} + \texttt{slope} \times (\texttt{comfort\_ref} - T_{out})
\]

Commission `base`, `slope`, and `comfort_ref` in yaml only — no Home Assistant entities for FF. Example starting point: `base: 25`, `slope: 1.2`, `comfort_ref: 20`.

Tune so that in typical winter weather `clamp(u_ff)` already produces a sensible water temperature.

## 4. Rise-rate auto-correct (operator summary)

Under sustained Heating Demand, rise-rate auto-correct may adapt **`base` and `slope` only** from the Critical Zone’s measured air temperature rise rate (W15 window; default expected rate `r_expected = 0.25` °C/h). `comfort_ref` stays commission-only.

Adapted `base` / `slope` persist in `ff_auto_correct_state.json` under the AppDaemon app directory. Yaml commission loads first; a valid JSON overlays `base` / `slope`. To restore yaml commission defaults, **delete that JSON file** (idle / Plant Management off do not clear it). Full formula, guards, and edge tables: [ADR 0004](adr/0004-weather-curve-swt.md) → spike decision note.

## 5. Safe order on a live house

1. Fill entity IDs and Zones.
2. Set sensible `setpoint_min` / `setpoint_max`.
3. Commission Weather Feedforward (`base` / `slope` / `comfort_ref`) to a familiar outdoor curve.
4. Enable Plant Management; watch water temperature and Zone air under demand (`clamp(u_ff)`) and idle (write `0`).
5. If rise-rate auto-correct is in use, watch adapted `base` / `slope` in `ff_auto_correct_state.json`; delete the file to restore yaml commission.
6. Disable Plant Management to stop all Set Water Temperature writes and clear ephemeral / water-path state; `ff_auto_correct_state.json` is left untouched.

## What is not calibrated here

- Relay or open-loop step commissioning
- Air→SWT tracking / LADRC on water — removed from this path (not dormant)
- Adapting `comfort_ref`
- New HA entities for Weather Feedforward
