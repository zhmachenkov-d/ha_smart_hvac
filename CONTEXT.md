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
When enabled, the App may command Set Water Temperature on the Plant. When disabled, the App does not write the Plant setpoint and clears supply-trip state — not “write 0”.
_Avoid_: CH override (integration-specific), boiler on (plant state)

**Zone Error**:
Per thermostat: setpoint minus zone sensor temperature. Zone-level error is the maximum across thermostats in that Zone whose `hvac_action` is `heating`; thermostats with idle, off, cooling, or unavailable action do not contribute. A Zone with no such thermostats has no eligible Zone Error. Among Zones with Heating Demand, Zone Error ranks Critical Zone selection for diagnostics and logging only (error may be ≤ 0).
_Avoid_: Demand (use Heating Demand for the boolean need), delta (ambiguous)

**Heating Demand**:
A Zone (or the house) needs heat when any of its thermostats reports `hvac_action` of `heating`. Idle, off, cooling, or unavailable action do not demand — Zone Error sign does not gate demand.
_Avoid_: Call for heat (informal), boiler on (plant state, not zone need)

**Critical Zone**:
The Zone with the largest Zone Error among Zones with Heating Demand. Retained for diagnostics and logging only — it must not drive Set Water Temperature or the supply rise-rate trip.
_Avoid_: Master zone, primary room

**Outdoor Temperature**:
The measured outdoor air temperature. On the Set Water Temperature path: required for Weather Feedforward, and a `control_event` listener that re-evaluates the Outdoor-gated demand writer.
_Avoid_: Weather (as a synonym for Outdoor Temperature), forecast (unless forecast is explicitly in scope)

**Weather Feedforward**:
Linear outdoor→water baseline `u_ff = base + slope × (comfort_ref − T_out)` with yaml-commissioned `base` / `slope` / `comfort_ref`. Under Plant Management and Heating Demand (and when the supply trip is not latched), demand Set Water Temperature is `round-to-0.1(clamp(u_ff))`. `initialize` runs one full `control_tick`; tick and every eligible `control_event` share that Outdoor-gated writer — every eligible event may rewrite demand SWT (not a one-shot rising-edge demand latch). Event listeners include Plant Management, Outdoor Temperature, zone air, and thermostat `hvac_action` / setpoint. CAP-7 / adapting `base`/`slope` / `ff_auto_correct_state.json` are not on the water path, must not be commissioned, and are out of scope (ADR 0007).
_Avoid_: PID, fixed-gain PI on demand-zone air error, online RLS retune, CAP-7, weather-curve auto-correct JSON (historical / out of scope — not live water law)

**Supply rise-rate trip**:
On `supply_event` under Plant Management on ∧ Heating Demand only (never Outdoor prelude), the App compares supply water rise rate `r_obs` (°C/min) to yaml `r_max`. Trip latches only after a successful SWT write `0`; latched demand keeps `0`. Clears on hold expiry, a zone Heating Demand rising-edge under the Outdoor prelude, and on `_go_idle` after a successful idle write `0` (write-fail keeps the latch — Decision C covers every Plant-on non-demand exit: no demand, unavailable Outdoor, no valid zones, non-finite `u_ff`). Plant-off clears trip state with no write.
_Avoid_: CAP-7 zone rise-rate auto-correct, Critical Zone closed-loop trip

**Multi-Zone Coordinator**:
The part of the HVAC App that computes Zone Error per Zone, Heating Demand, and Critical Zone selection. It does not own the OpenTherm Set Water Temperature write. Critical Zone selection is for diagnostics and logging only and must not drive Set Water Temperature or the supply rise-rate trip.
_Avoid_: Thermostat, scheduler (unless that is all it does)

## Example dialogue
> **Dev:** When I change the thermostat schedule logic, am I editing Home Assistant or an App?
> **Expert:** An App. Home Assistant exposes the climate entity; the App decides when and how to call it.
> **Dev:** So AppDaemon is part of what we ship?
> **Expert:** No — AppDaemon is the runtime that hosts our Apps. We pin and configure it; we don't maintain its source here.
> **Dev:** Can I start AppDaemon in the Dev Container while the Production Add-on is still running?
> **Expert:** No. That isn't an Exclusive Session — both would drive the same entities. Stop the add-on first, then run locally.
> **Dev:** Two Zones want heat; which one moves the boiler?
> **Expert:** Neither zone alone owns the water write. Under Plant Management and Heating Demand the App writes `round-to-0.1(clamp(u_ff))` from Outdoor Weather Feedforward, or writes `0` on idle / other Plant-on non-demand exits. A supply rise-rate trip can latch SWT `0` after a successful trip write. The Multi-Zone Coordinator still picks the Critical Zone — largest Zone Error among demand zones — for diagnostics and logging only; it must not drive Set Water Temperature or the trip.
> **Dev:** Is Set Water Temperature the same as a Zone thermostat setpoint?
> **Expert:** No. Zone thermostats set air temperature targets. Set Water Temperature is the OpenTherm boiler water setpoint.
> **Dev:** A Zone has Heating Demand but Plant Management is off — does the App still write zero?
> **Expert:** No. Plant Management off means hands off entirely: no setpoint write, supply-trip state cleared — not “write 0”. Heating Demand only matters when Plant Management is on.
> **Dev:** If Plant Management, Outdoor, zone air, or a thermostat `hvac_action` / setpoint changes, do we wait for the next control tick?
> **Expert:** No — those listeners fire `control_event`, which re-runs the Outdoor-gated prelude and may rewrite demand SWT the same way as `control_tick` (including the initialize first tick). Every eligible event may rewrite demand SWT; it is not a one-shot rising-edge demand latch. Supply rise-rate observation is separate: `supply_event` gates on Plant∧Demand only and never requires Outdoor. Idle / no-valid-zones / unavailable Outdoor / non-finite `u_ff` take `_go_idle` (write `0`; Decision C disarms hold always and clears latch only after a successful idle write). Plant-off clears trip state with no write.