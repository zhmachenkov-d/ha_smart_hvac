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
When enabled, the App may command Set Water Temperature on the Plant. When disabled, the App does not write the Plant setpoint and clears ephemeral / water-path state (rise-rate window, steady count, I1 previous, selected-zone id). Persisted FF auto-correct JSON is left untouched.
_Avoid_: CH override (integration-specific), boiler on (plant state)

**Zone Error**:
Per thermostat: setpoint minus zone sensor temperature. Zone-level error is the maximum across thermostats in that Zone whose `hvac_action` is `heating`; thermostats with idle, off, cooling, or unavailable action do not contribute. A Zone with no such thermostats has no eligible Zone Error. Eligible Zone Errors feed Heating Demand and Critical Zone selection for CAP-7 rise-rate auto-correct only.
_Avoid_: Demand (use Heating Demand for the boolean need), delta (ambiguous)

**Heating Demand**:
A Zone (or the house) needs heat when its Zone Error is positive — the Zone air is colder than its thermostat setpoint.
_Avoid_: Call for heat (informal), boiler on (plant state, not zone need)

**Critical Zone**:
The Zone with the largest Zone Error among Zones with Heating Demand. Its air temperature rise rate is the signal for Weather Feedforward rise-rate auto-correct (CAP-7) only — it never drives Set Water Temperature as a closed-loop air→water tracking term.
_Avoid_: Master zone, primary room

**Outdoor Temperature**:
The measured outdoor air temperature used when calculating an appropriate Set Water Temperature.
_Avoid_: Weather, forecast (unless forecast is explicitly in scope)

**Weather Feedforward**:
The outdoor-temperature baseline that **is** Set Water Temperature under Plant Management and Heating Demand gates: `u_ff = base + slope × (comfort_ref − T_out)`, then `clamp(u_ff)`. Not an add-on to a tracking term.
_Avoid_: Weather compensation (related idea, may differ in formula), curve (unless referring to the configured parameters)

**Multi-Zone Coordinator**:
The part of the HVAC App that computes Zone Error per Zone, Heating Demand, and Critical Zone selection for CAP-7 rise-rate auto-correct. It does not own the OpenTherm Set Water Temperature write.
_Avoid_: Thermostat, scheduler (unless that is all it does)

## Example dialogue

> **Dev:** When I change the thermostat schedule logic, am I editing Home Assistant or an App?
> **Expert:** An App. Home Assistant exposes the climate entity; the App decides when and how to call it.
> **Dev:** So AppDaemon is part of what we ship?
> **Expert:** No — AppDaemon is the runtime that hosts our Apps. We pin and configure it; we don't maintain its source here.
> **Dev:** Can I start AppDaemon in the Dev Container while the Production Add-on is still running?
> **Expert:** No. That isn't an Exclusive Session — both would drive the same entities. Stop the add-on first, then run locally.
> **Dev:** Two Zones want heat; which one moves the boiler?
> **Expert:** Neither zone's air error drives water closed-loop. The HVAC App writes `clamp(u_ff)` from Weather Feedforward whenever any Zone has Heating Demand (and Plant Management is on), or writes `0` when idle. The Multi-Zone Coordinator still picks the Critical Zone — largest Zone Error among demand zones — but only as the rise-rate source when discussing FF auto-correct.
> **Dev:** Is Set Water Temperature the same as a Zone thermostat setpoint?
> **Expert:** No. Zone thermostats set air temperature targets. Set Water Temperature is the OpenTherm boiler water setpoint.
> **Dev:** A Zone has Heating Demand but Plant Management is off — does the App still write zero?
> **Expert:** No. Plant Management off means hands off entirely: no setpoint write, ephemeral / water-path state cleared. Heating Demand only matters when Plant Management is on.
