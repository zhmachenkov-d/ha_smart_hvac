# Smart HVAC

Python automations that control heating, ventilation, and air conditioning through Home Assistant, hosted by AppDaemon.

## Language

**App**:
A Python automation that runs inside AppDaemon and acts on Home Assistant entities to control HVAC behavior.
_Avoid_: Script, automation (HA automation), integration, add-on

**AppDaemon**:
The sandboxed Python execution environment that loads and runs Apps. This project consumes AppDaemon; it does not develop it.
_Avoid_: Framework, HA core, add-on (as a synonym for AppDaemon or for an App)

**Home Assistant**:
The home automation platform whose entities, services, and events Apps observe and control.
_Avoid_: HAOS, supervisor (unless referring specifically to those products)

**Production Add-on**:
The Home Assistant AppDaemon add-on that normally hosts the house's Apps.
_Avoid_: Prod container, live AD (as the only name)

**Exclusive Session**:
A development period in which the Production Add-on is stopped so a local AppDaemon is the sole runtime talking to Home Assistant for those Apps.
_Avoid_: Dual-run, parallel AD (those are failures of an Exclusive Session)

**Zone**:
A controllable heating area of the house that participates in shared boiler demand. A Zone has a temperature reading and one or more Home Assistant thermostats (climate entities).
_Avoid_: Room (unless a Zone is exactly one room), entity

**Plant**:
The boiler and primary water circuit that supplies heat to Zones, commanded via OpenTherm.
_Avoid_: HVAC system (too broad), heater (ambiguous with zone emitters)

**Set Water Temperature**:
The OpenTherm boiler water setpoint the App commands on the Plant (the boiler's target water temperature via OpenTherm).
_Avoid_: Room setpoint, climate temperature (those are Zone air targets), mixer setpoint

**Plant Management**:
When enabled, the App may command Set Water Temperature on the Plant. When disabled, the App does not write the Plant setpoint and clears PID ephemeral state (∫) — not “write 0”.
_Avoid_: CH override (integration-specific), boiler on (plant state)

**Zone Error**:
Per thermostat: setpoint minus zone sensor temperature. Zone-level error is the maximum across thermostats in that Zone whose `hvac_action` is `heating`; thermostats with idle, off, cooling, or unavailable action do not contribute. A Zone with no such thermostats has no eligible Zone Error. Among Zones with Heating Demand, Zone Error ranks Critical Zone selection for diagnostics and logging only (error may be ≤ 0).
_Avoid_: Demand (use Heating Demand for the boolean need), delta (ambiguous)

**Heating Demand**:
A Zone (or the house) needs heat when any of its thermostats reports `hvac_action` of `heating`. Idle, off, cooling, or unavailable action do not demand — Zone Error sign does not gate demand.
_Avoid_: Call for heat (informal), boiler on (plant state, not zone need)

**Critical Zone**:
The Zone with the largest Zone Error among Zones with Heating Demand. Retained for diagnostics and logging only — it must not drive Set Water Temperature.
_Avoid_: Master zone, primary room

**Outdoor Temperature**:
The measured outdoor air temperature. Not on the Set Water Temperature path or live commissioning.
_Avoid_: Weather, forecast (unless forecast is explicitly in scope)

**PID**:
The fixed-gain PI term on weighted demand-zone air error that produces `u_pid`. Under Plant Management and Heating Demand, demand Set Water Temperature is `round-to-0.1(clamp(base_water_temp + u_pid))`. Only the periodic `control_interval` (`control_tick`) advances PID and writes demand SWT; event listeners (Plant Management, zone air, thermostat `hvac_action` / setpoint — not Outdoor) re-evaluate gates via `control_event` and may clear on idle / plant-off / no-valid-zones without a demand write or PID advance. RLS retune of gains is planned, not current commissioning.
_Avoid_: Weather Feedforward, CAP-7, weather compensation, curve (superseded SWT path)

**Multi-Zone Coordinator**:
The part of the HVAC App that computes Zone Error per Zone, Heating Demand, and Critical Zone selection. It does not own the OpenTherm Set Water Temperature write. Critical Zone selection is for diagnostics and logging only and must not drive Set Water Temperature.
_Avoid_: Thermostat, scheduler (unless that is all it does)

## Example dialogue

> **Dev:** When I change the thermostat schedule logic, am I editing Home Assistant or an App?
> **Expert:** An App. Home Assistant exposes the climate entity; the App decides when and how to call it.
> **Dev:** So AppDaemon is part of what we ship?
> **Expert:** No — AppDaemon is the runtime that hosts our Apps. We pin and configure it; we don't maintain its source here.
> **Dev:** Can I start AppDaemon in the Dev Container while the Production Add-on is still running?
> **Expert:** No. That isn't an Exclusive Session — both would drive the same entities. Stop the add-on first, then run locally.
> **Dev:** Two Zones want heat; which one moves the boiler?
> **Expert:** Neither zone alone owns the water write. Under Plant Management and Heating Demand the App writes `round-to-0.1(clamp(base_water_temp + u_pid))` from weighted demand-zone averages, or writes `0` and clears ∫ when idle. The Multi-Zone Coordinator still picks the Critical Zone — largest Zone Error among demand zones — for diagnostics and logging only; it must not drive Set Water Temperature.
> **Dev:** Is Set Water Temperature the same as a Zone thermostat setpoint?
> **Expert:** No. Zone thermostats set air temperature targets. Set Water Temperature is the OpenTherm boiler water setpoint.
> **Dev:** A Zone has Heating Demand but Plant Management is off — does the App still write zero?
> **Expert:** No. Plant Management off means hands off entirely: no setpoint write, PID ephemeral state (∫) cleared — not “write 0”. Heating Demand only matters when Plant Management is on.
> **Dev:** If Plant Management, zone air, or a thermostat `hvac_action` / setpoint changes, do we wait for the next control tick?
> **Expert:** For demand SWT and ∫ advance, yes — only `control_tick` writes demand and advances PID. Those listeners fire `control_event`, which re-evaluates the shared gate prelude and may clear on idle / plant-off / no-valid-zones without a demand write or PID advance. Outdoor Temperature is not a control listener.
