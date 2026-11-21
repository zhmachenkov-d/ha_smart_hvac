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
When enabled, the App may command Set Water Temperature on the Plant. When disabled, the App does not write the Plant setpoint and clears flame trip state — not “write 0”; TRV soft-close still writes closure 100 and cancels any soft-close hold.
_Avoid_: CH override (integration-specific), boiler on (plant state)

**Zone Error**:
Per thermostat: setpoint minus zone sensor temperature. Zone-level error is the maximum across thermostats in that Zone whose `hvac_action` is `heating`; thermostats with idle, off, cooling, or unavailable action do not contribute. A Zone with no such thermostats has no eligible Zone Error. Among Zones with Heating Demand, Zone Error ranks Critical Zone selection for diagnostics and logging only (error may be ≤ 0).
_Avoid_: Demand (use Heating Demand for the boolean need), delta (ambiguous)

**Heating Demand**:
A Zone (or the house) needs heat when any of its thermostats reports `hvac_action` of `heating`. Idle, off, cooling, or unavailable action do not demand — Zone Error sign does not gate demand.
_Avoid_: Call for heat (informal), boiler on (plant state, not zone need)

**Critical Zone**:
The Zone with the largest Zone Error among Zones with Heating Demand. Retained for diagnostics and logging only — it must not drive Set Water Temperature, TRV soft-close, or the flame short-on trip.
_Avoid_: Master zone, primary room

**Outdoor Temperature**:
The measured outdoor air temperature. On the Set Water Temperature path: required for Weather Feedforward, and a `control_event` listener that re-evaluates the Outdoor-gated demand writer.
_Avoid_: Weather alone as a synonym for Outdoor Temperature (not Weather Feedforward), forecast (unless forecast is explicitly in scope)

**Weather Feedforward**:
Linear outdoor→water baseline `u_ff = base + slope × (comfort_ref − T_out)` with yaml-commissioned `base` / `slope` / `comfort_ref`. Under Plant Management and Heating Demand (and when the flame trip is not latched), demand Set Water Temperature is `round-to-0.1(clamp(u_ff))`. `initialize` runs one full `control_tick`; tick and every eligible `control_event` share that Outdoor-gated writer — every eligible event may rewrite demand SWT (not a one-shot rising-edge demand latch). Event listeners include Plant Management, Outdoor Temperature, zone air, and thermostat `hvac_action` / setpoint. CAP-7 / adapting `base`/`slope` / `ff_auto_correct_state.json` are not on the water path, must not be commissioned, and are out of scope (ADR 0008).
_Avoid_: PID, fixed-gain PI on demand-zone air error, online RLS retune, CAP-7, weather-curve auto-correct JSON (historical / out of scope — not live water law)

**TRV soft-close**:
Sonoff TRV numbers are **mode limits**, not commanded stem position: `valve_closure_degree` = max how far the valve may close while the TRV is in **idle**; `valve_opening_degree` = max how far it may open while in **heating**. The App writes only `valve_closure_degree` (never `valve_opening_degree` — heating max-open stays with the TRV). `_apply_trv_law` runs before the Outdoor water prelude on tick / `control_event` / flame hold expiry; soft-close hold expiry writes 100 while idle and does not run the Outdoor prelude. Plant-off writes closure 100 and cancels any soft-close hold. Plant-on house-idle: first all-idle observe writes `valve_closure_floor` (default 80) and arms one `trv_soft_close_hold_s` hold (default 300) with no re-arm while holding; hold expiry while idle writes 100 and stays at 100; orphan/token-mismatch expiry is a no-op (no soft-close write); any Heating Demand writes 100 and cancels/never arms hold; return to all-idle re-floors and arms a new hold. Critical Zone never drives TRV. Sonoff TRV mappings are closure-only; a leftover yaml `accuracy` key is a ConfigError.
_Avoid_: treating closure/opening as instantaneous position; valve_opening_degree writes; tying TRV to Outdoor-only gates; Critical Zone closed-loop TRV

**Flame short-on trip**:
Anti-cycle protection: a `flame_on` True duration shorter than yaml `flame_on_min_s` on True→False fall under `_flame_observe_gate` (Plant∧Demand∧`ch_active` on∧¬latch — never Outdoor) latches SWT `0` only after a successful trip write and hold schedule. Latched demand keeps `0`. Clears on hold expiry (TRV then Outdoor prelude + demand when prelude returns zones), zone Heating Demand rising-edge under `_gate_prelude` (`_clear_flame_trip_state`), plant-off (`_clear_flame_trip_state`), and `_go_idle` after successful idle write `0` (write-fail keeps `_flame_trip_latched` — Decision C).
_Avoid_: Outdoor-gated flame observe, re-asserting SWT from flame observers while latched, Critical Zone closed-loop trip

**Supply rise-rate trip**:
Historical (epic 2 / ADR 0007). Formerly compared supply water rise rate `r_obs` (°C/min) to yaml `r_max` on `supply_event` under Plant∧Demand (never Outdoor prelude), latching SWT `0` after a successful trip write. Live anti-cycle is flame short-on + TRV soft-close (ADR 0008).
_Avoid_: Treating supply rise-rate / `supply_event` / `r_obs` / `r_max` / `boiler_water` / `_clear_trip_state` / `_supply_trip_latched` as live water law; CAP-7 zone rise-rate auto-correct; Critical Zone closed-loop trip

**Multi-Zone Coordinator**:
The part of the HVAC App that computes Zone Error per Zone, Heating Demand, and Critical Zone selection. It does not own the OpenTherm Set Water Temperature write. Critical Zone selection is for diagnostics and logging only and must not drive Set Water Temperature, TRV soft-close, or the flame short-on trip.
_Avoid_: Thermostat, scheduler (unless that is all it does)

## Example dialogue
> **Dev:** When I change the thermostat schedule logic, am I editing Home Assistant or an App?
> **Expert:** An App. Home Assistant exposes the climate entity; the App decides when and how to call it.
> **Dev:** So AppDaemon is part of what we ship?
> **Expert:** No — AppDaemon is the runtime that hosts our Apps. We pin and configure it; we don't maintain its source here.
> **Dev:** Can I start AppDaemon in the Dev Container while the Production Add-on is still running?
> **Expert:** No. That isn't an Exclusive Session — both would drive the same entities. Stop the add-on first, then run locally.
> **Dev:** Two Zones want heat; which one moves the boiler?
> **Expert:** Neither zone alone owns the water write. Under Plant Management and Heating Demand the App writes `round-to-0.1(clamp(u_ff))` from Outdoor Weather Feedforward, or writes `0` on idle / other Plant-on non-demand exits. A flame short-on trip can latch SWT `0` after a successful trip write and hold schedule; TRV soft-close runs before the Outdoor prelude. The Multi-Zone Coordinator still picks the Critical Zone — largest Zone Error among demand zones — for diagnostics and logging only; it must not drive Set Water Temperature, TRV, or the flame trip.
> **Dev:** Is Set Water Temperature the same as a Zone thermostat setpoint?
> **Expert:** No. Zone thermostats set air temperature targets. Set Water Temperature is the OpenTherm boiler water setpoint.
> **Dev:** A Zone has Heating Demand but Plant Management is off — does the App still write zero?
> **Expert:** No. Plant Management off means hands off entirely: no setpoint write, flame trip state cleared — not “write 0”. TRV soft-close still writes closure 100 on commissioned valves and cancels any soft-close hold. Heating Demand only matters for SWT when Plant Management is on.
> **Dev:** If Plant Management, Outdoor, zone air, or a thermostat `hvac_action` / setpoint changes, do we wait for the next control tick?
> **Expert:** No — those listeners fire `control_event`, which runs `_apply_trv_law` then the Outdoor-gated prelude and may rewrite demand SWT the same way as `control_tick` (including the initialize first tick). Every eligible event may rewrite demand SWT; it is not a one-shot rising-edge demand latch. Flame observe is separate: `_flame_observe_gate` is Plant∧Demand∧`ch_active` on∧¬latch and never requires Outdoor. Idle / no-valid-zones / unavailable Outdoor / non-finite `u_ff` take `_go_idle` (write `0`; Decision C disarms hold always and clears `_flame_trip_latched` only after a successful idle write). Plant-off clears flame trip state with no write.
