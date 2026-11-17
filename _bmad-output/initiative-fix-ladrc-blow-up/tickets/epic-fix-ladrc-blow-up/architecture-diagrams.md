# Architecture diagrams — LADRC blow-up

## Saturation thrashing loop (observed failure)

When `u_track` diverges, `clamp(u_ff + u_track)` to `[setpoint_min, setpoint_max]` produces bang-bang commands. Under the broken path the ESO used absolute SWT (and/or saturated `exp_map` gains at `dt=60`), so divergence persisted.

```mermaid
flowchart LR
  u_ff["u_ff ~ 40"] --> sum["u_ff + u_track"]
  u_track["u_track → ±1e12…1e24"] --> sum
  sum --> clamp["clamp 40..55"]
  clamp --> cmd["command bang-bang"]
  cmd --> eso["ESO advance absolute SWT + exp_map"]
  eso --> u_track
```

## Target control / observer split

Plant write stays absolute SWT; ESO known input is the post-clamp tracking residue. ESO advance is continuous-form (`β1=2ωo`, `β2=ωo²`), not `exp_map`.

```mermaid
flowchart LR
  u_ff["u_ff"] --> sum["u_ff + u_track"]
  u_track["u_track"] --> sum
  sum --> clamp["clamp 40..55"]
  clamp --> plant["plant write = command"]
  clamp --> sub["command − u_ff"]
  u_ff --> sub
  sub --> eso["ESO continuous-form advance"]
  y["y measured"] --> eso
  eso --> z["z1, z2"]
  z --> law["u_track = (u0 − z2) / b0"]
  law --> u_track
```
