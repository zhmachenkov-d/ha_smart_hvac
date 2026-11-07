---
id: SPEC-fix-ladrc-blow-up
companions:
  - architecture-diagrams.md
  - ../../../../docs/adr/0002-ladrc-critical-zone-control.md
  - ../../../../docs/adr/0003-online-ladrc-omega-c-auto-tune.md
sources:
  - /home/vscode/.cursor/plans/fix_ladrc_blow-up_4f4b86eb.plan.md
---

> **Canonical contract.** This SPEC and the files in `companions:` are the complete, preservation-validated contract for what to build, test, and validate. Source documents listed in frontmatter are for traceability — consult them only if you need narrative rationale or prose color this contract intentionally omits.

# Fix LADRC u_track blow-up

## Why

**Pain to solve.** On the live plant, LADRC `u_track` is numerically exploding (~10^12–10^24) while weather feedforward `u_ff` stays sane (~40). The clamp to `[setpoint_min, setpoint_max]` turns the sum into bang-bang Set Water Temperature (40↔55), so zone error stays stuck and the boiler thrashing looks like “steering jumps.” The primary failure is the production ESO discretization (`α = 1 − exp(−ωo·dt)`) at `dt=60`, which saturates observer gains; Huang-era example gains (`b0=2.8`, `omega_o=19.49`) remain invalid for this OpenTherm plant, but retune alone under the current discrete map cannot stabilize thermal-band gains. There is no finite/magnitude recovery today. Until code lands, operators should turn Plant Management off (or stop demand) so the app stops writing SWT and clears LADRC. Failure-mode diagram: `architecture-diagrams.md`.

## Capabilities

- **CAP-1**
  - **intent:** Operators get plant-channel LADRC example defaults (`b0`, `omega_o`) in a thermal starting band that stay numerically stable with the fixed ESO and tracking-residue known input at the app’s 60 s sample time.
  - **success:** With the new example defaults (not Huang `2.8` / `19.49`), multi-tick runs at realistic `y≈21`, `T_r` near zone air, plant write `command = clamp(u_ff + u_track)`, and ESO known input `(command − u_ff)` keep `u_track`, `z1`, and `z2` finite with `|u_track|` in a sane band (tens of °C, not 1e6+). `apps/apps.yaml.example` carries the new values.

- **CAP-2**
  - **intent:** On a bad control tick the app detects non-finite or magnitude-exploded `u_track`, clears diverged ESO state, and still issues a safe feedforward-only water command for that tick.
  - **success:** In the `hvac_app` tick path, after `compute_tracking`, when `u_track` is non-finite or `|u_track|` exceeds the configured magnitude threshold (example/default **100** °C), the tick yields `command = clamp(u_ff)`, ESO `reset(measured)`, and a WARNING visible in HA logs once per episode; the loop does not remain bricked until zone change / idle / plant-off.

- **CAP-3**
  - **intent:** Automated tests lock the blow-up diagnosis and the fix so the broken discrete map, Huang gains, or an unguarded explode path cannot silently return.
  - **success:** Tests (a) reproduce divergence under the old `exp_map` discretization and/or Huang-scale gains, (b) assert continuous-form ESO + new defaults + tracking-residue known input stay bounded over N ticks, and (c) assert the guard path resets and returns feedforward-only command.

- **CAP-4**
  - **intent:** Maintainers reading ADR 0002 know why `exp_map` at `dt=60` fails, that the ESO must use a continuous-form advance and tracking-residue known input, that Huang `b0`/`ωo` must not be used here, and that new defaults need house calibration.
  - **success:** ADR 0002 carries that amendment; ADR 0003 remains ωc-only (no claim of online `b0`/`omega_o` adaptation).

- **CAP-5**
  - **intent:** The LADRC ESO advances with a continuous-form observer (`β1 = 2ωo`, `β2 = ωo²` over the sample) that remains usable at `dt=60` with thermal-band `omega_o`, instead of the production `α = 1 − exp(−ωo·dt)` gain map.
  - **success:** With continuous-form advance and known input `(command − u_ff)`, multi-tick runs using thermal-band gains (`b0 ~ 1e-4–1e-3`, `omega_o ~ 0.01–0.05`, including `omega_o` on the order of a few×`omega_c`) keep `u_track`/`z` finite with `|u_track|` in tens of °C; the same scenario under `exp_map` diverges. Integrator choice (RK, substeps, matrix-exp equivalent) is free if these tests pass.

## Constraints

- Plant write stays `command = clamp(u_ff + u_track)` (absolute SWT). After clamp, ESO known input is **`(command − u_ff)`**, not absolute `command` and not pre-clamp `u_track`.
- `LadrcState.advance` must **not** use the `α = 1 − exp(−ωo·dt)` gain map at `dt=60`; use continuous-form integration locked by CAP-5 tests. Integrator choice (RK, matrix-exp, or equivalent) and substep count are free if those tests pass.
- Online auto-tune remains **ωc only** (ADR 0003); this work must not introduce online `b0` or `omega_o` adaptation.
- Do not change `setpoint_min`/`setpoint_max` (plant limits 40/55); bang-bang was clamp thrashing from diverged `u_track`, not a limits bug.
- Exact numeric example defaults are locked by CAP-3 boundedness tests. Starting-point band: `b0 ~ 1e-4–1e-3` °C_air/(°C_water·s); `omega_o ~ 0.01–0.05`. **`omega_o > omega_c` is not a hard constraint** at this sample time.
- The `|u_track|` magnitude blow-up threshold is a **config field** with example/default **100** (°C); non-finite `u_track` always trips regardless of that value.
- Blow-up guard lives in **`hvac_app` only** (after `compute_tracking`); `LadrcState` stays a pure tracker/ESO and does not grow a guard API.
- Optionally refuse to `advance` with non-finite state after a guard trip.

## Non-goals

- Changing feedforward structure or Critical Zone selection.
- Adapting `b0` / `omega_o` online.
- Changing Set Water Temperature min/max (40/55).
- Treating the `omega_c` tuner as the fault or changing its bounds.
- Putting the blow-up guard inside `LadrcState`.
- Adding MADRC / inertia-compensator on the ESO u-path.
- Changing `control_interval` away from 60 s as the fix.

## Success signal

After continuous-form ESO + tracking-residue known input + retuned example defaults + guard, multi-tick simulation (and live ticks under demand) no longer produce non-finite or astronomical `u_track`; command leaves bang-bang thrashing — meaning **oscillating** between plant limits under diverged `u_track`, not merely dwelling on `setpoint_min` when `u_ff≈40` and `u_track≈0` — and stays a smooth `clamp(u_ff + u_track)` within plant limits, with regression tests failing if `exp_map`, Huang defaults, or an unguarded explode path return.
