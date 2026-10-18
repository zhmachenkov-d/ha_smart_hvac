---
type: Reference
title: Sonoff TRVZB — Zigbee clusters and integration maps
description: Zigbee 3.0 interview, ZCL thermostat + Sonoff 0xFC11 attributes, ZHA/Z2M exposure for the house TRV.
tags: [zigbee, thermostat, sonoff, hardware]
timestamp: 2026-10-18T10:00:00Z
resource: raw/sonoff-trvzb/
---

# Sonoff TRVZB — Zigbee clusters and integration maps

SONOFF model **TRVZB** (Zigbee thermostatic radiator valve; informal “ZBTRV” = same product). Zigbee 3.0 end device; manufacturer code **4742**.

Immutable archive: [`raw/sonoff-trvzb/`](/raw/sonoff-trvzb/) (`SOURCE.md`, `device-signature.json`).

## Status

Ingested (first pass) — identity, endpoint clusters, thermostat + `0xFC11` attribute map, project fit. Not a full ZCL schedule binary layout dump.

## Authoritative external pages

| Source | URL |
|--------|-----|
| Zigbee2MQTT exposes / MQTT API | https://www.zigbee2mqtt.io/devices/TRVZB.html |
| SONOFF product / pairing / specs | https://help.sonoff.tech/docs/trvzb/ |
| ZHA quirk (cluster `0xFC11` defs) | https://github.com/zigpy/zha-device-handlers/blob/dev/zhaquirks/sonoff/trvzb.py |
| Interview signature discussion | https://github.com/zigpy/zha-device-handlers/issues/2772 |

## Key sections (for re-ingest)

1. Endpoint 1 profile `0x0104`, device type thermostat `0x0301`
2. Input clusters: Basic, Power, Identify, On/Off, Poll Control, Thermostat `0x0201`, Sonoff `0xFC11` / `0xFC57`
3. Output: Time `0x000A`, OTA `0x0019`
4. Thermostat attrs used by HA climate vs unsupported (`pi_heating_demand`)
5. `0xFC11` vendor attrs (child lock, open window, frost, valve degrees, external temp, smart temperature control)
6. Firmware gates: valve degrees ≥ 1.1.4; temperature accuracy ≥ 1.3.0; smart control ≥ 1.4.4

## Linked concepts

- [/concepts/sonoff-trvzb.md](/concepts/sonoff-trvzb.md)
- [/concepts/zone.md](/concepts/zone.md)
- [/concepts/zone-error.md](/concepts/zone-error.md)
