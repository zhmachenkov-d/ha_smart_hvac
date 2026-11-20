---
id: 1
type: story
title: "Tracer: TRV house-idle soft-close"
parent: epic-trv-house-idle-soft-close
covers: [R1, R2]
after: [6.2]
hitl: false
risk: high
refined: true
---

# Tracer: TRV house-idle soft-close
## Description
Replace plant-on floor+overshoot soft-close with house-idle soft-close (config + hold + writes + example yaml) so epic R1/R2 are true in the App and tests, leaving house `apps.yaml` and live docs to later stories.

1. Ships the live soft-close law change (house-idle → floor → hold-or-heating → 100) that epic R1 requires.
2. Retires accuracy commission and overshoot latch from the App soft-close path so epic C5/C7 and Done-when (4) hold.
3. Commissions `trv_soft_close_hold_s` and closure-only TRV keys in `apps.yaml.example` as the schema house story 7.2 will apply.
4. Locks the law with automated tests, including hold cancel/orphan behavior.

## Requirements
1. **House-idle floor + arm hold** (R1)
   **Given** Plant Management on and no zone has Heating Demand, and at least one Sonoff TRV is commissioned with a closure entity only
   **When** the App first observes house all-idle under Plant on (cold start / initialize while already idle, or a later transition into all-idle — not every subsequent idle tick)
   **Then** every commissioned TRV receives `valve_closure_degree` = yaml `valve_closure_floor` (default **80**)
   **And** a soft-close hold of yaml `trv_soft_close_hold_s` (default **300**) is armed once; while still all-idle with that hold active, later ticks/events do not restart the timer
   **Failure:** floor not written on first all-idle observe, hold never armed, or hold restarts every idle pass

2. **Hold expiry while idle → 100** (R1)
   **Given** Plant on, house still all-idle, and a soft-close hold was armed
   **When** the hold expires with a matching token
   **Then** every commissioned TRV receives `valve_closure_degree` = **100**
   **And** a stale/orphan expiry (token mismatch after cancel) performs no soft-close write
   **Failure:** expiry while idle leaves floor, or cancelled hold still writes on expiry

3. **Demand → 100 and cancel hold** (R1)
   **Given** Plant on and any zone has Heating Demand — including cold start / first soft-close pass while already heating (never all-idle), rising-edge off an armed hold, or sustained demand after floor was written
   **When** soft-close runs
   **Then** every commissioned TRV receives `valve_closure_degree` = **100**, no soft-close hold is left armed (cancel with token bump if one was armed; never arm hold while demand is present)
   **Failure:** demand leaves floor or an armed hold, or cold-start-with-demand writes floor / arms hold

4. **Return to all-idle restarts floor+hold** (R1)
   **Given** Plant on and Heating Demand was present (closure at 100, hold cancelled)
   **When** the house returns to all-idle
   **Then** commissioned TRVs receive floor again and a new soft-close hold is armed
   **Failure:** return to idle leaves 100 without re-arming floor+hold

5. **Plant off → 100 and cancel hold** (R2)
   **Given** a soft-close hold may be armed and commissioned TRVs may be at floor
   **When** Plant Management is off
   **Then** every commissioned TRV receives `valve_closure_degree` = **100** and any soft-close hold is cancelled
   **Failure:** plant-off leaves floor or leaves hold armed

6. **Closure-only commission; accuracy retired; hold key** (R1, epic C5)
   **Given** thermostat and top-level yaml
   **When** a Sonoff TRV mapping includes `valve_closure` and omits `accuracy`, and `trv_soft_close_hold_s` is omitted or set
   **Then** parse succeeds; that TRV is commissioned for soft-close; omitted hold defaults to **300** (same whole-second rules as flame hold: positive int after truncate)
   **And** a mapping that still includes `accuracy` is rejected (`ConfigError`)
   **And** invalid `trv_soft_close_hold_s` is rejected (`ConfigError`)
   **And** the App does not register accuracy state listeners for soft-close
   **And** overshoot latch state is not part of the live soft-close law
   **Failure:** closure-only mapping rejected, accuracy still required or listened, hold key missing/default wrong, or overshoot latch still drives writes

7. **Never opening; Critical Zone out; example yaml** (R1, R2, epic C4, C7)
   **Given** any soft-close path (tick, control event, flame-hold expiry, soft-close hold expiry, plant-off)
   **When** writes run
   **Then** the App never writes `valve_opening_degree`
   **And** Critical Zone selection does not drive soft-close writes
   **And** `apps.yaml.example` commissions `trv_soft_close_hold_s` (default 300), `valve_closure_floor`, and per-TRV closure-only keys (no accuracy)
   **And** `uv run pytest` and `uv run ruff check apps/ha_smart_hvac tests` are clean
   **Failure:** opening write, Critical Zone drives TRV, example still requires accuracy / omits hold, or tests/ruff fail

## Boundaries
- Must not change: weather-curve Set Water Temperature law; flame short-on observe/latch/clear; Exclusive Session; Heating Demand = thermostat `hvac_action=heating`
- Must not: edit house `apps/apps.yaml` (story 7.2); amend ADR/CONTEXT/AGENTS/`knowledge/` (story 7.3); restore temperature overshoot as live soft-close; infer TRV entities by name; write `valve_opening_degree`
- Soft-close still runs on tick / eligible control event / flame-hold expiry paths before the Outdoor water prelude; Outdoor unreadability must not block soft-close; flame latch must not freeze soft-close
- Equal-float plant/TRV readback skip remains the write throttle; unreadable or non-finite closure readback skips the write
- Soft-close hold mirrors flame hold: single timer, token bump on cancel, orphan expiry no-op
- House entity ids stay for 7.2 HITL; this story owns example + App schema only

## References
- parent — `_bmad-output/initiative-weather-swt-supply-trip/tickets/epic-trv-house-idle-soft-close/epic-trv-house-idle-soft-close.md`, Requirements R1–R2; Constraints C4, C5, C7; Notes hold Decision
- research — `_bmad-output/initiative-weather-swt-supply-trip/research-trv-soft-close-and-hold-timers/research-trv-soft-close-and-hold-timers.md`, §§1–4, §6 (live overshoot law, accuracy commission, flame hold pattern, tests, call sites)
- prerequisite — `_bmad-output/initiative-weather-swt-supply-trip/tickets/epic-docs-trv-flame-water-law/tickets/story-knowledge-live-curve-trv-flame-demote-supply-trip-plan.md`, status done (entry 6.2)

## Notes
- Decision: Plant on + any Heating Demand (rising-edge or sustained) → write closure 100 and cancel hold (2026-11-20).
- Decision: Arm soft-close hold on first Plant-on all-idle observe (including cold start while already idle) and on later return to all-idle; do not restart while still idle with hold active (2026-11-20).
- Decision: Leftover yaml `accuracy` on a TRV mapping → `ConfigError` (2026-11-20).
- Decision: Soft-close hold cancel mirrors flame token/orphan; expiry writes 100 only while still all-idle (2026-11-20).
- Risk reason: wrong soft-close leaves valves soft-closed under Heating Demand or skips soft-close when idle, cycling the boiler or choking zones.
- High-risk check beyond criteria: automated test that after heating-edge cancel, a stale soft-close hold callback performs no soft-close write.
- Waits on epic-docs-trv-flame-water-law entry 6.2 because: substantive docs landed; do not after 6.3 (blocked on this epic — cycle).
- Tracer scope: config parse + house-idle/hold/edge/plant-off law + example yaml + tests in one path; docs and house yaml are 7.3 / 7.2.