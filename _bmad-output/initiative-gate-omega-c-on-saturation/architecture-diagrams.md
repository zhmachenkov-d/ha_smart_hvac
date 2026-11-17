# Tick flow (gate ωc on saturation)

```mermaid
flowchart TD
  S{Latch already active?}
  S -->|yes| C[write-path track+guard with committed ωc]
  S -->|no| A[maybe_adapt propose ωc]
  A --> P[provisional track+guard with proposed ωc]
  P --> B{Directional blocks apply?}
  B -->|yes| C
  B -->|no| D[reuse provisional u_track/guard for write-path]
  C --> F{_write_setpoint}
  D --> F
  F -->|entity unreadable| X[fail-closed: abort tick]
  F -->|same float: skip set_value| G[sticky latch; ESO reset if needed / advance]
  F -->|different: set_value| G
  G --> H{residue decay?}
  H -->|yes| I[Step ωc down max_rate_fraction; persist]
  H -->|no| J{apply_proposed?}
  J -->|yes| K[commit_omega_c]
  J -->|no| L[skip commit]
  I --> M[end tick]
  K --> M
  L --> M
```

While latch is already active, adapt is skipped for the whole tick. Decay persist is a separate branch and is not blocked by the guard-trip skip of normal `commit_omega_c`. Post-write J is `apply_proposed` (not a second `should_apply_omega_c` call).
