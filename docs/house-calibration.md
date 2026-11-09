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

`setpoint_min` / `setpoint_max` bound the commanded Set Water Temperature; match them to the boiler / primary circuit limits. `control_interval` (a whole number of seconds, at most `86400`, default `300`) is the only schedule that advances the PID and writes a demand Set Water Temperature.

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
  ki: 1.0
  i_term_min: -10
  i_term_max: 15
```

Units:

| Key | Unit | Meaning |
|-----|------|---------|
| `kp` | °C water per °C air | Proportional gain on \(e\) |
| `ki` | 1/h | Integral gain; \(\int e\,dt\) is accumulated in °C·h (hours, not seconds or ticks) |
| `i_term_min` / `i_term_max` | °C of water | Bounds on the I-term \(K_i \int e\,dt\) |

With `ki: 1.0`, a sustained 1 °C air error adds about 1 °C of water per hour (about 1/12 °C per tick at `control_interval: 300`). Changing `control_interval` does not rescale the effective Ki: each periodic tick that steps the integral adds the error times the configured interval in hours (not measured elapsed time), so one hour of ticks adds the same amount at 60 s or 300 s. Ticks where the integral is held (plant setpoint unavailable, or the freeze below) add nothing. The integral only advances on the periodic tick and freezes when the unclamped command (`base_water_temp` + Kp·e + I-term) is past `setpoint_min` / `setpoint_max` in the direction of the error.

When `pid.adaptive` is true, commission `boiler_water` and all four adapted-gain rails (`kp_min` / `kp_max` / `ki_min` / `ki_max`, each ≥ 0 with min ≤ max). Rails constrain adapted Kp/Ki proposals only; YAML fixed `kp` / `ki` are not checked against them. An explicit `pid.ki` with `0 < ki < 1` still parses but logs one WARNING at startup (legacy per-second scale; expected unit is 1/h — not auto-migrated).

When `base_water_temp` equals `setpoint_min` (as in the example), a negative error with a non-positive I-term already sits at `setpoint_min`, so the integral freezes and `i_term_min` is reachable only when `base_water_temp` is above `setpoint_min`.

`base_water_temp` must lie within `setpoint_min`…`setpoint_max` (bounds inclusive); an explicit value outside them is a config error and the App does not start. When `base_water_temp` is omitted, the default `40` is clamped into the bounds (with `setpoint_min: 42` the base is `42`; with `setpoint_max: 35` it is `35`).

These are starting defaults, not house-proven. Raise `zones[].weight` for Zones that should count more in the averages.

### Rejected commission values

Each of these logs `HVAC config error: …` at startup and the App does not run:

- A non-numeric value (text that is not a number, `null`, a list, or `true` / `false`) or a non-finite one (`nan`, `inf`) for `setpoint_min`, `setpoint_max`, `control_interval`, `base_water_temp`, any `pid.*` gain or bound, or a Zone `weight`
- A fractional `control_interval` (`60.7`, `0.5`); `60.0` is accepted as `60`
- A `control_interval` above `86400` (one day)
- A negative `pid.kp` or `pid.ki` (`0` is accepted)
- When `pid.adaptive` is true: a missing `boiler_water`, or any missing / negative / min>max adapted-gain rail (`kp_min` / `kp_max` / `ki_min` / `ki_max`)
- An I-term range that does not include `0` (`i_term_min` must be ≤ 0 ≤ `i_term_max`)
- An explicit `base_water_temp` outside `setpoint_min`…`setpoint_max`

## 4. Safe order on a live house

1. Fill entity IDs and Zones.
2. Set sensible `setpoint_min` / `setpoint_max`.
3. Commission `base_water_temp` and `pid` gains.
4. Enable Plant Management; watch water temperature and Zone air under demand and idle (write `0`).
5. Disable Plant Management to stop all Set Water Temperature writes and clear ephemeral / water-path state.

## Upgrading from Weather Feedforward

Outdoor Temperature, Weather Feedforward, and rise-rate auto-correct are removed. Leftover `outdoor_temperature` and `weather_feedforward` keys in `apps.yaml` are ignored and logged as one WARNING at startup (`HVAC config: ignoring legacy or unknown keys: …`, which also names any other unknown key, including unknown zone sub-keys such as a misspelled `weigth`); delete them. `ff_auto_correct_state.json` in the AppDaemon app directory is no longer read and can be deleted.

## Upgrading to hour-based PID integral

`pid.integral_min` / `pid.integral_max` are replaced by `pid.i_term_min` / `pid.i_term_max`, which bound the I-term in °C of water rather than the raw integral. The old keys are ignored and logged as one WARNING at startup; replace them. The integral is now accumulated in °C·h with `ki` in 1/h, so the I-term builds over hours rather than per tick, and an old `ki` value does not carry the same meaning: the old `ki` was per second, so an explicit old value × 3600 is the equivalent per-hour `ki` (old `0.1` ≈ `360`, far above the new default). Delete an old `ki` to take the default `1.0`, or set a per-hour value deliberately. A yaml without a `pid:` section picks up the new defaults (`kp 1.0`, `ki 1.0`, `i_term_min -10`, `i_term_max 15`) on update.

## Upgrading to strict commission parsing

An explicit `base_water_temp` outside `setpoint_min`…`setpoint_max`, or any value in the rejection list in §3, now stops the App at startup with `HVAC config error: …` instead of being accepted. An omitted `base_water_temp` now defaults to `40` clamped into the bounds, so a house with `setpoint_min` above `40` and no `base_water_temp` now starts from `setpoint_min`.

## What is not calibrated here

- Relay or open-loop step commissioning
- Air→SWT tracking / LADRC on water — removed from this path (not dormant)
- Online retuning of PID gains
