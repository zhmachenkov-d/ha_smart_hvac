# House calibration

How to calibrate the HVAC App for a specific house. Calibration is **manual `apps.yaml` commissioning** of the base water temperature, fixed PID gains, and Zone weights. There is no relay/step commissioning procedure.

Copy [`apps.yaml.example`](../apps.yaml.example) to `apps.yaml` next to the installed `ha_smart_hvac/` package, then work through the sections below. Never commit live house entity IDs.

Domain terms: [`CONTEXT.md`](../CONTEXT.md). Exclusive Session: [ADR 0001](adr/0001-exclusive-session-against-production-ha.md).

## 1. House wiring (required)

Replace every `YOUR_*` placeholder:

| Key | Role |
|-----|------|
| `plant_management` | Switch: when off, the App does not write Set Water Temperature and clears ephemeral / water-path state |
| `plant_setpoint` | OpenTherm Set Water Temperature (`number` entity) |
| `zones[]` | Per Zone: air temperature sensor + one or more climate thermostats; optional `weight` (default `1.0`) |

Without correct wiring the App is not bound to the house.

## 2. Plant clamps and interval

```yaml
setpoint_min: 40
setpoint_max: 55
control_interval: 300
```

`setpoint_min` / `setpoint_max` bound the commanded Set Water Temperature; match them to the boiler / primary circuit limits. `control_interval` (seconds, default `300`) is the only schedule that advances the PID and writes a demand Set Water Temperature.

## 3. Base water temperature and PID (yaml commission)

Under Heating Demand the App commands:

\[
\text{SWT} = \operatorname{round}_{0.1}\big(\operatorname{clamp}(\texttt{base\_water\_temp} + K_p e + K_i \textstyle\int e\,dt)\big),\quad e = T_{set,w} - T_{air,w}
\]

where \(T_{set,w}\) and \(T_{air,w}\) are weight-normalized averages over Zones with Heating Demand only.

```yaml
base_water_temp: 40
pid:
  kp: 1.0
  ki: 0.1
  integral_min: -50
  integral_max: 50
```

These are starting defaults, not house-proven. Raise `zones[].weight` for Zones that should count more in the averages.

## 4. Safe order on a live house

1. Fill entity IDs and Zones.
2. Set sensible `setpoint_min` / `setpoint_max`.
3. Commission `base_water_temp` and `pid` gains.
4. Enable Plant Management; watch water temperature and Zone air under demand and idle (write `0`).
5. Disable Plant Management to stop all Set Water Temperature writes and clear ephemeral / water-path state.

## Upgrading from Weather Feedforward

Outdoor Temperature, Weather Feedforward, and rise-rate auto-correct are removed. Leftover `outdoor_temperature` and `weather_feedforward` keys in `apps.yaml` are ignored; delete them. `ff_auto_correct_state.json` in the AppDaemon app directory is no longer read and can be deleted.

## What is not calibrated here

- Relay or open-loop step commissioning
- Air→SWT tracking / LADRC on water — removed from this path (not dormant)
- Online retuning of PID gains
