# Online LADRC ωc auto-tune

The HVAC App slowly adapts LADRC **Controller Bandwidth (ωc)** during normal heating when Plant Management is on. **Observer Bandwidth (ωo)** and plant gain **b₀** stay fixed at config time; Weather Feedforward stays manual.

## Why ωc only

- **ωc** sets outer-loop tracking speed (`kp = ωc`). Sustained Critical Zone tracking error (`reference − z₁`) indicates the loop is too slow or too aggressive; a small integral nudge on ωc is safe with rate limits and bounds.
- **b₀** appears in the denominator of `u = (u₀ − z₂) / b₀`. Online changes would shift the control law discontinuously and confuse the ESO's disturbance estimate.
- **ωo** trades noise rejection against disturbance tracking in the ESO. That trade-off is commissioning work, separate from outer-loop tracking speed.

## Why tracking error, not Zone Error

Zone Error uses raw zone sensor temperature. LADRC tracks against the ESO estimate **z₁**, which lags the sensor and smooths noise. Adaptation uses `reference − z₁` so the tuner responds to what the controller actually sees.

## Guards

Adaptation runs only when there is Heating Demand, the Critical Zone has been stable for `min_steady_ticks`, `|tracking error| ≥ deadband`, and the per-tick change is clamped to `max_rate_fraction × ωc` and to `[omega_c_min, omega_c_max]`. On Critical Zone switch the tuner freezes for that tick and resets its steady counter (ESO reset is handled separately per ADR 0002).

Commit is also directionally gated against plant saturation under **criterion A** (stop soft-kill after sustained underheat — not “adapt only with actuation headroom”): skip committing an upward ωc when the tick’s Set Water Temperature command is already at `setpoint_max`, and a downward ωc at `setpoint_min`; relieving moves still commit; a blow-up guard trip still blocks normal commit. When commit is blocked, that tick’s tracking uses the current committed ωc — the blocked proposal must not enter the control law. This is not a full freeze whenever Set Water Temperature sits at either clamp.

While the blow-up soft-kill latch is already active at tick start, `maybe_adapt` is skipped for the whole tick and the tuner steady counter is cleared (`clear_steady()`) so a warm counter cannot propose upward ωc on the first unlatched tick after decay. Separately, whenever the latch is held after a successful plant write (including the trip-edge tick) and `|u_track| > 0.8 · u_track_max` (or non-finite), committed ωc steps down by `max_rate_fraction × ωc`, floored at `omega_c_min`, and persists until finite `|u_track|` leaves that band — recovery is not ops-reset-only. Soft-kill sticky latch, decay, and ESO reset still run only after a successful plant write; fail-write leaves the latch unchanged. Episode WARNING is gated at the app with `_blow_up_warned` (independent of the sticky latch) so a trip-edge that fails the plant write does not re-warn every tick: set the flag when WARNING emits; clear it on successful demand ticks that end unlatched and on idle / hands-off / no-demand paths; never clear it on fail-write early-return. Plant Set Water Temperature writes are write-on-change: skip `number/set_value` when the entity float already equals the desired value; unreadable or unparseable entity state stays fail-closed (abort the tick).

## Persistence

Adapted ωc is stored in `ladrc_tune_state.json` under the AppDaemon app directory. Steady-tick state is not persisted.

## Out of scope

Weather Feedforward auto-tune, online ωo adaptation, and relay/step commissioning remain out of scope. MADRC inertia compensator \(G_{cp}\) go/authorization, scheduling coexistence with this ωc tuner, and related gates are decided in ADR 0004 (ωc auto-tune **coexists**; scheduling does not replace it). Online \(b_0\) is an intended follow-on via stub epic `epic-online-b0` (see ADR 0004) — not implemented here.
