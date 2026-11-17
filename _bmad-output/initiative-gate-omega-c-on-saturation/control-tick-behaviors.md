# Control-tick behaviors (gate ωc on saturation)

Load-bearing rules for R1–R4. Kernel holds intent; this file holds the matrices.

## Directional commit clamp (R1)

Skip `commit_omega_c` when any of:

| Condition | Skip commit? |
| --- | --- |
| Guard tripped (existing) | yes |
| `command >= setpoint_max` and proposed ωc **increases** | yes |
| `command <= setpoint_min` and proposed ωc **decreases** | yes |
| `command >= setpoint_max` and proposed ωc **decreases** | no (allow) |
| `command <= setpoint_min` and proposed ωc **increases** | no (allow) |
| Interior command (strictly inside clamp) and not tripped | no (allow) |

Full freeze on any SWT clamp is out of scope.

## Strict apply (R2)

On a tick with a proposed ωc, directional clamp and guard trip decide whether that proposal may enter write-path tracking and later persist:

1. May run a **provisional** track+guard with `with_omega_c(proposed)` solely as the apply-signal (to evaluate `should_apply_omega_c`).
2. If blocked: discard provisional; **write-path** track/guard/write/advance use **committed** ωc; do **not** re-evaluate apply/commit on the final guard.
3. If allowed: reuse provisional `u_track`/guard for write-path (no second track); persist only when `apply_proposed` after a successful write (outside decay).
4. Gate-only-on-persistence (apply proposed, skip commit) remains rejected — it reopens the one-tick ratchet.

## Write-on-change (R3)

Inside `_write_setpoint` for **all** paths (demand and idle/0):

1. Read current plant entity state.
2. If state is `None` / `unavailable` / `unknown` or not parseable as float → **fail-closed** (existing): no `set_value`, return false, **control tick aborts** (no advance).
3. If desired equals the parsed float (exact compare), skip `number/set_value` but return success so the tick continues (ESO reset / advance / gates / decay).
4. Otherwise call `number/set_value`.

Baseline for equality is entity state, not a last-written cache. Equality-skip must not early-return the tick; unreadability abort is separate and intentional.

## Latch ωc decay (R4)

While the blow-up soft-kill latch is **already active at tick start**:

1. **Skip `maybe_adapt` entirely** — no propose, no propose-then-override. Also call `clear_steady()` on `latch_at_start` so a warm steady counter cannot propose upward ωc on the first unlatched tick after decay.
2. After `u_track` for the tick is known: if `|u_track| > 0.8 · u_track_max` **or** `u_track` is non-finite → step committed ωc down by existing tuner `max_rate_fraction`, clamp to `≥ omega_c_min`, **persist**.
3. Stop decaying when `u_track` is finite and `|u_track| ≤ 0.8 · u_track_max` (still skip adapt while latch remains active).
4. This persist path runs even though normal `commit_omega_c` is skipped on guard trip.
5. Criterion uses **actual tick `|u_track|`**, not `|ωc · e / b0|`.
6. `0.8` is a fixed code constant — not a yaml knob. Step/floor reuse existing tuner config.

On the trip-edge tick (latch was inactive at start), adapt may still have proposed before the guard; commit remains skipped by guard trip; decay applies from that tick onward when the residue condition holds.

Soft-kill latch (sticky R4):

- Soft-kill latch assigned only **after successful `_write_setpoint`** via sticky: `tripped ∨ (latch_in ∧ residue_holds)` where residue is `|u| > 0.8·u_track_max` or non-finite.
- Latch **holds** while residue is in `(0.8·u_track_max, u_track_max]` (even if not currently tripped); clears when finite `|u| ≤ 0.8·u_track_max`.
- On write failure, leave `_blow_up_latch` unchanged.

Episode WARN (app-level, independent of sticky latch):

- Gate WARNING with `guard.should_warn and not self._blow_up_warned`; set `_blow_up_warned` on emit. Sticky latch + decay + ESO reset remain after successful write only — do not set `_blow_up_latch` on fail-write to suppress WARN.
- Clear `_blow_up_warned` on every successful demand tick that ends with `_blow_up_latch` False, and on `_hands_off` / `_go_idle` / no-demand (same paths that clear the latch). Never clear on fail-write early-return.

Rejected as sufficient recovery alone: one step on trip edge (R1), hard reset to `config.omega_c` (R3), one-shot safe-ωc jump (R4).
