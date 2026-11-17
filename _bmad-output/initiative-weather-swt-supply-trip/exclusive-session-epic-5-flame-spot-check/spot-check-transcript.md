# Exclusive Session spot-check — epic 5 flame short-on

**When:** 2026-11-17  
**Mode:** Exclusive Session (Production AppDaemon add-on stopped; local `./scripts/run-appdaemon`)  
**Log:** `ad-exclusive.log`

## Method
API-forced observe gate (not a live boiler short cycle): bathroom `hvac_action=heating`, `ch_active=on`, then `flame_on` off→on→off with ~11s True duration. Clear via Plant Management off. Restore plant on; force flame/ch off; bathroom idle attrs.

## Observed
1. `HVAC weather-curve SWT app initialized` (no ConfigError).
2. Under forced demand: weather-curve write `command=50.0` (`outdoor=4.80`).
3. Short flame: `Flame short-on trip: duration=11.02s < flame_on_min_s=300.00s; latching SWT 0`; plant setpoint `0.0`.
4. Outdoor poke while latched: SWT stayed `0.0`.
5. Plant off: `Plant Management disabled` (latch clear path).
6. TRV livingroom closure read `100` during session (soft-close path alive; not a dedicated ADV8 hold-expiry live run — hold is 900s).

## Not claimed
- Natural OpenTherm flame cycle / real CH from the bridge.
- Hold-expiry ADV8 live (unit tests cover; 900s hold not waited).
- Zone rising-edge clear live.

## Teardown
Local AppDaemon stopped. **Operator must start the Production AppDaemon add-on again.**

## Production restore
`hassio.addon_start` addon=`a0d7b954_appdaemon` → HTTP 200 (2026-11-17). Supervisor info API 401 with long-lived token — confirm Running in HA UI if needed.
