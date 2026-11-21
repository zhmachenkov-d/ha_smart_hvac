Historical — plant-off keep-overshoot-latch soft-close (epic 4); live soft-close is house-idle floor + hold (ADR 0008).

# Plant-off writes closure 100 without clearing overshoot latch

Under Plant Management off, `_apply_trv_law` writes `valve_closure_degree` 100 on every commissioned Sonoff TRV and does not clear `_trv_overshoot_latched`; on plant return the latched hysteresis (keep 100 until `T_zone ≤ setpoint`) still applies. Recorded from story 4.1 plan Intent / Review Triage (`story-tracer-trv-idle-max-close-soft-close-plan.md`) and commits `784fc71` / `b4d7603`, because forcing a latch wipe on plant-off would reopen soft-close in the accuracy dead-band on the next plant-on without re-crossing overshoot.
