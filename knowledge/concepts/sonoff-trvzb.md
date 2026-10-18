---
type: Concept
title: Sonoff TRVZB
description: Zigbee 3.0 thermostatic radiator valve used as a Zone climate thermostat; HA exposes setpoint and heating/idle running state.
tags: [zigbee, thermostat, zone, hardware]
timestamp: 2026-10-18T10:00:00Z
---

# Sonoff TRVZB

**Sonoff TRVZB** (Zigbee model id `TRVZB`; sometimes written ZBTRV) is a battery Zigbee 3.0 thermostatic radiator valve. In this house it appears as Home Assistant `climate.*_sonoff_trvzb_*` entities wired under [Zone](/concepts/zone.md) `thermostats` in `apps.yaml`.

The App **reads** TRV climate setpoint and `hvac_action` to compute [Zone Error](/concepts/zone-error.md) and Heating Demand. It does **not** command the TRV valve or air setpoint for boiler control — the [ADRC Controller](/concepts/adrc.md) writes [Set Water Temperature](/concepts/set-water-temperature.md) on the OpenTherm [Plant](/concepts/plant.md). Zone air temperature for the control loop comes from separate zone sensors (e.g. SNZB-02D), not from the TRV’s local temperature attribute.

## Zigbee identity

| Field | Value |
|-------|--------|
| Manufacturer | `SONOFF` |
| Model | `TRVZB` |
| Manufacturer code | `4742` |
| Profile | HA (`0x0104`) |
| Device type | Thermostat (`0x0301`) |
| Role | End device, sleepy (receiver off when idle), battery |

Single endpoint **1**.

## Clusters (endpoint 1)

### Input

| Cluster | Id | Role for this project |
|---------|----|------------------------|
| Basic | `0x0000` | Identity |
| Power Configuration | `0x0001` | Battery % |
| Identify | `0x0003` | Pairing / identify |
| On/Off | `0x0006` | Present; not used by the HVAC App |
| Poll Control | `0x0020` | Sleepy check-in |
| Thermostat (HVAC) | `0x0201` | Standard climate: setpoint, local temp, system mode, running state |
| Sonoff custom | `0xFC11` | Valve limits, open-window, frost, external temp, smart control, etc. |
| Sonoff custom | `0xFC57` | Manufacturer-specific (quirk may leave empty) |

### Output

| Cluster | Id | Role |
|---------|----|------|
| Time | `0x000A` | Client |
| OTA | `0x0019` | Firmware updates |

## Thermostat cluster (`0x0201`) — what HA climate uses

Attributes that matter for Zone coordination (via HA climate):

| Attribute | Meaning |
|-----------|---------|
| `occupied_heating_setpoint` | Air setpoint (°C, typically 4–35, 0.5 step) → App thermostat `setpoint` |
| `local_temperature` | On-device sensor (°C); **not** the Zone sensor the App uses for control |
| `local_temperature_calibration` | Offset on local temp (−12.7…12.7 °C, 0.2 step) |
| `system_mode` | `off` / `auto` / `heat` |
| `running_state` | `idle` / `heat` → HA `hvac_action` (`idle` / `heating`); only `heating` contributes Zone Error |

`pi_heating_demand` is unsupported on interview — the valve does not expose ZCL PI demand the way some other TRVs do.

## Manufacturer cluster `0xFC11` (Sonoff)

Documented in ZHA quirk / Zigbee2MQTT converters (attribute ids hex):

| Attr | Name | Notes |
|------|------|--------|
| `0x0000` | child_lock | bool |
| `0x6000` | open_window | auto shutoff on sharp local-temp drop |
| `0x6002` | frost_protection_temperature | int16, ×0.01 °C |
| `0x6003`–`0x6007` | idle/closing steps, valve limit/motor voltages | mostly read-only calibration telemetry |
| `0x600B` / `0x600C` | valve_opening_degree / valve_closing_degree | 0–100 % (fw ≥ 1.1.4) |
| `0x600D` / `0x600E` | external temperature value / sensor select | remote sensor path; sync is outside Zigbee alone |
| `0x6011` | temperature_control_accuracy | −1.0…−0.2 °C (fw ≥ 1.3.0) |
| `0x6014`–`0x6016` | temporary / timer modes | boost vs timed setpoint |
| `0x6017` | smart_temperature_control | adaptive/PID valve mode (fw ≥ 1.4.4); disables manual opening % + accuracy when on |

Weekly schedule when `system_mode=auto` is exposed by integrations (ZCL schedule path / converter mapping); the HVAC App does not write schedules.

## Fit to this project

- Eligible heating: `hvac_action == "heating"` maps from Zigbee `running_state = heat`.
- Idle / off TRVs do not win Critical Zone contention even if setpoint ≫ zone temp.
- Custom `0xFC11` features (valve %, smart PID, open-window) are **device-local**; they can change how the radiator valve behaves but are outside the App’s OpenTherm command path.
- Prefer zone SNZB sensors for App temperature; TRV `local_temperature` is for the valve’s own loop (and optional external-temp feed into the TRV).

## Related

- [/concepts/zone.md](/concepts/zone.md)
- [/concepts/zone-error.md](/concepts/zone-error.md)
- [/concepts/set-water-temperature.md](/concepts/set-water-temperature.md)
- [/references/sonoff-trvzb-zigbee.md](/references/sonoff-trvzb-zigbee.md)

# Citations

- [/references/sonoff-trvzb-zigbee.md](/references/sonoff-trvzb-zigbee.md)
- [`raw/sonoff-trvzb/`](/raw/sonoff-trvzb/)
- [`CONTEXT.md`](../../CONTEXT.md) — Zone, Zone Error, Set Water Temperature
