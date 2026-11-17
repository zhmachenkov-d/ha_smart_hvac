# Flame short-on latch only after SWT 0 write and hold timer scheduled

On a short `flame_on` True→False under the observe gate, the App latches and retains protection only after `_write_setpoint(0.0)` succeeds and `run_in` for `_flame_trip_hold_expired` is scheduled with a new token; a failed write leaves the latch clear and wipes `_flame_on_since`. Recorded from story 5.1 plan Intent Always and commits `918debc` / `02bc705`, because latching without a confirmed plant write (or without an armed hold) would claim anti-cycle protection while SWT may stay hot or the hold path may never run.
