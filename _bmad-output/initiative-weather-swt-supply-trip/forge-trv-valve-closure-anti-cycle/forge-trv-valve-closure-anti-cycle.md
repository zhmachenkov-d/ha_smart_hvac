---
title: TRV idle max-close + flame short-on trip
status: hardened
created: 2026-11-15
updated: 2026-11-15
---

# TRV idle max-close + flame short-on trip

## Locked

- **Weather-curve SWT stays.** Supply rise-rate trip (`r_obs` / `r_max` / `boiler_water` trip path) is fully removed (code, yaml, ADR/CONTEXT/tests) in the same initiative as the new law.
- **Primary anti-cycle — Sonoff TRV:** AppDaemon writes only `valve_closure_degree` (idle **max-close** limit, not instantaneous position). Never writes `valve_opening_degree` (heating max-open stays with TRV).
- **Plant on:** default idle max-close = yaml `valve_closure_floor` (**80**); overshoot `T_zone > setpoint + accuracy` → **100**; clear when `T_zone ≤ setpoint` → floor again. Applies with or without Heating Demand.
- **Plant off:** write **100** on all commissioned Sonoff TRVs.
- **Overshoot inputs (per TRV):** `T` = zone `temperature` (apps.yaml SNZB); `setpoint` + `accuracy` from that TRV; living_room may share one SNZB across two TRVs.
- **Wiring:** explicit yaml per Sonoff TRV thermostat for closure number + accuracy source — no name guessing. Generic thermostats (bathroom/kitchen/wc) have no TRV-law keys.
- **Fallback anti-cycle — flame trip:** if `flame_on` **True duration** (True→False) &lt; yaml `flame_on_min_s` (**300**), attempt SWT `0`; **latch only after successful write**.
- **Flame observe gate:** Plant on ∧ Heating Demand ∧ bridge `ch_active` ∧ latch clear. `flame_on` and `ch_active` are **separate** yaml entities ≠ `plant_management` (`ch_enabled`).
- **Flame clear:** same as ADR 0007 supply-trip clear — hold `flame_trip_hold_s` (**900**) **or** zone Heating Demand rising-edge; then weather-curve when gates allow.
- **Layers independent:** while flame-latched, TRV soft-close law keeps running.
- **Success:** less boiler short-cycling **and** more stable zone temperature.

## Rejected

- Constant hold of closure=80 during heating as a position command (would choke open).
- App managing `valve_opening_degree`.
- Supply rise-rate trip as the anti-cycle mechanism.
- Flame metric = off-gap or full-cycle period (chosen: short **on**).
- Collapsing `ch_active` into `plant_management`.
- Inferring TRV number/accuracy entities from climate id by naming convention.
- Freezing or forcing TRV closure=100 for the duration of flame latch.

## Why (load-bearing)

- Soft-close idle max-close leaves residual flow when TRVs satisfy — addresses closed-circuit cycling at the valve, not via SWT guesswork from supply rise.
- Non-TRV zones can still fully shut; flame short-on trip is the plant safety net when residual flow is not enough.
- Limit semantics (idle max-close / heating max-open) keep TRV mode logic; App only commissions the idle close ceiling.

## Open (implementation / commission — not idea)

- Concrete house entity ids for `flame_on`, `ch_active`, per-TRV closure numbers and accuracy sources (owner confirm).
- ADR supersede/amend of 0007 for flame trip + TRV soft-close; Sofia replan of active initiative boundaries.
