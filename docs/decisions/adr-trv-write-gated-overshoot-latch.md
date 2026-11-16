# TRV overshoot latch only after successful closure write

Plant-on overshoot sets `_trv_overshoot_latched` for a `valve_closure` entity id only when `_write_number(..., 100)` returns True; clear to floor discards the latch only after a successful floor write (including equal-float True). Recorded from story 4.1 plan Intent Always (`story-tracer-trv-idle-max-close-soft-close-plan.md`) and commits `784fc71` / `b4d7603`, because latching without a confirmed number write would claim max-close while the valve may still sit at floor.
