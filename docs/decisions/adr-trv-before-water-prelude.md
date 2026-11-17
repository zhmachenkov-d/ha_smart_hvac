# TRV idle max-close before water prelude

Every `control_tick`, `control_event`, and flame hold expiry runs `_apply_trv_law` before `_gate_prelude`, so commissioned Sonoff soft-close applies with or without readable Outdoor / Heating Demand; flame observe / latch handlers do not run `_apply_trv_law`. Recorded from story 4.1 plan Intent Always (`story-tracer-trv-idle-max-close-soft-close-plan.md`) and commits `784fc71` / `b4d7603`, because tying TRV to the Outdoor-gated water prelude would skip soft-close on Outdoor flake and contradict the epic’s anti-cycle independence from demand SWT.
