# First supply trip latch only after successful SWT 0 write

On `r_obs > r_max` under Plant∧Demand, the App latches and arms the hold timer only after `_write_setpoint(0.0)` returns success; a failed first write leaves the latch clear and does not advance the sample into a latched state. Recorded from story 2.1 code-review Decision (write-fail latch) in `story-tracer-supply-rise-rate-trip-plan.md` and commits `fbe647f` / `d7e5262`, because latching without a confirmed plant write would claim protection while SWT may stay hot.
