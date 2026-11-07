---
title: 'Continuous-form ESO in LadrcState'
type: 'bugfix'
ticket: '1'
created: '2026-10-16'
status: done
baseline_revision: 'a3b10592ebafdcc25c8766583a1ddac3c4df622b'
route: 'full'
route_source: 'auto'
review: 'quick'
review_source: 'pinned'
lenses_ran: ['quick']
review_loop_iteration: 0
context:
  - '{project-root}/knowledge/concepts/ladrc.md'
  - '{project-root}/knowledge/concepts/extended-state-observer.md'
  - '{project-root}/_bmad-output/initiative-fix-ladrc-blow-up/tickets/epic-fix-ladrc-blow-up/spec-fix-ladrc-blow-up/spec-fix-ladrc-blow-up.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Production `LadrcState.advance` uses exp_map (`α = 1 − exp(−ωo·dt)`, `g1=2α`, `g2=α²`). At `dt=60` that discrete map is wrong: Huang-scale `omega_o` saturates (`α→1`); thermal-band gains need not saturate `α`, yet multi-tick runs still diverge. CAP-5 requires continuous-form ESO.

**Approach:** Replace production exp_map with continuous-form integration (`β1=2ωo`, `β2=ωo²` over the sample; RK/substeps — reject single-step Euler over full `dt` if AC fails). Lock CAP-5 with a **mandatory frozen exp_map helper**: same thermal+C scenario diverges under the helper and stays bounded under production `advance`. Tracer may merge before story 1.2; does not close epic Success. Huang+absolute CAP-3a case deferred (see `deferred-work.md`).

## Boundaries & Constraints

**Always:**
- Continuous-form ESO: `ż1 = z2 + β1(y−z1) + b0·u`, `ż2 = β2(y−z1)`, `β1=2ωo`, `β2=ωo²`.
- No guard API; `compute_tracking` / `reset` / `clear` unchanged.
- Locked test scenario (not example YAML): `y=21`, `T_r=21.2`, `u_ff=40`, clamp `[40,55]`, `dt=60`, `N=80`, `b0=5e-4`, `omega_o=0.03`, `omega_c=0.01`, known input `u=command−u_ff`, every-tick `|u_track|<100`. Nudge `b0`/`omega_o` only inside `b0 ~ 1e-4–1e-3`, `omega_o ~ 0.01–0.05`; if `omega_c` must change to meet the AC, record that too in Implementation Notes (do not silently keep Huang `0.053`).
- Frozen helper = copied pre-change `alpha/g1/g2` body on the **same** `LadrcState` instance that `compute_tracking` reads/writes; required for CAP-5 contrast (not optional Huang-under-continuous).
- Tracer merge OK before 1.2; PR messaging = ESO discretization / CAP-5 tracer, not “blow-up fixed.”
- ωc-only auto-tune; do not adapt `b0`/`omega_o`.

**Never:**
- Touch `hvac_app` known-input, example `b0`/`omega_o`, `u_track_max`, guard, ADR 0002/0003.
- Leave exp_map in production `advance`, or keep it behind a feature flag.
- Claim epic Success / live bang-bang fixed by this story alone.
- Change `dt`/limits/ff/Critical Zone/MADRC.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected | Error Handling |
|----------|--------------|----------|----------------|
| Same scenario under exp_map | Frozen helper, thermal gains, C known-input, locked numbers, `N=80` | Diverges (non-finite or `|u_track|≥1e6`) | CAP-5 contrast |
| Continuous + thermal + C | Production `advance`, same scenario | Finite; `|u_track|<100` each tick | CAP-5 pass |
| Existing API tests | `tests/test_ladrc.py` contracts | Still pass; retarget `test_eso_bounded_with_60s_dt` | See Design Notes |

</frozen-after-approval>

## Code Map

- `apps/hvac/ladrc.py` — replace `advance` L39–55 exp_map with continuous-form integration; keep tracking/reset/clear/`_last_u_applied`; refresh module docstring.
- `apps/hvac/models.py` — reuse `LadrcConfig.beta2`/`kp`/`dt` only.
- `apps/hvac/hvac_app.py` — still absolute `command`; **do not change**.
- `tests/test_ladrc.py` — frozen exp_map helper mutating the same `LadrcState` as `compute_tracking`; CAP-5 pair; thermal config (`b0=5e-4`, `omega_o=0.03`, `omega_c=0.01`, `dt=60`); update module docstring; retarget/remove Huang one-step `|Δz1|<50` test.
- `tests/test_ladrc_tuner.py` — **do not change**.
- Spec CAP-5: `spec-fix-ladrc-blow-up/spec-fix-ladrc-blow-up.md`.

## Tasks & Acceptance

**Execution:**
- [x] `apps/hvac/ladrc.py` -- Continuous-form `advance` (`β1=2ωo`, `β2=ωo²` over `dt`); docstring -- CAP-5 production.
- [x] `tests/test_ladrc.py` -- Frozen helper: thermal+C diverges; production continuous: thermal+C `|u_track|<100` for `N=80`; retarget `test_eso_bounded_with_60s_dt`; docstring -- CAP-5 lock.

**Acceptance Criteria:**
- Given production `advance`, when loaded, then it does not use the `α=1−exp(−ωo·dt)` gain map (`g1=2α`, `g2=α²`). Matrix-exp or other integrators that call `math.exp` are allowed if multi-tick ACs pass.
- Given frozen exp_map helper + locked thermal+C scenario (`omega_c=0.01`, `N=80`) on the same `LadrcState` as `compute_tracking`, when ticks run, then divergence (non-finite or `|u_track|≥1e6`).
- Given production continuous-form + same scenario, when `N=80` ticks run, then finite `u_track`/`z` and every tick `|u_track|<100`.
- Given existing `compute_tracking` / `clear` / `u_applied` tests, when suite runs, then they pass (`test_eso_bounded_with_60s_dt` retargeted or removed per Design Notes).

## Implementation Notes

- **Integrator:** continuous-form ESO (`β1=2ωo`, `β2=ωo²`) with forward Euler over **2 equal substeps** of `dt`. Single-step Euler over full `dt=60` failed CAP-5 (`|u_track|` grew to ~840); two substeps (`h=30`) keeps every-tick `|u_track|<100` (peak ~19 on the locked scenario).
- **Gains:** locked thermal band used as-is — `b0=5e-4`, `omega_o=0.03`, `omega_c=0.01` (no nudge).
- **`test_eso_bounded_with_60s_dt`:** retargeted to thermal config + one-step continuous-form bound `|Δz1|<5` (replacing Huang `|Δz1|<50`).

## Plan Change Log

- 2026-10-16 review patches (CAP-5 contrast, locked numbers, anti-Euler, sketches).
- 2026-10-16 split: deferred Huang+absolute CAP-3a divergence to `deferred-work.md`; regenerated lean CAP-5 tracer plan.
- 2026-10-16 review#2: lock `dt=60`/`omega_c=0.01`; AC forbids α-map not all `math.exp`; helper mutates same `LadrcState`; nudge notes include `omega_c`.

## Review Triage Log

- 2026-10-16 quick: high=0 medium=1 low=1 false=0 maybe-false=0
  - medium | patch | `tests/test_ladrc.py` `test_eso_bounded_with_60s_dt`: z1=measured=21 and u=0 ⇒ Δz1≡0, so `|Δz1|<5` cannot fail — vacuous retarget vs pre-change nonzero innovation.
  - low | patch | `apps/hvac/ladrc.py` comment above `_ESO_EULER_SUBSTEPS`: cites `|1+h·(−ωo)|` but β1=2ωo ⇒ factor is `|1−2h·ωo|`; wrong rationale for 2 substeps (code/tests still correct).

## Design Notes

```text
β1 = 2·ωo,  β2 = ωo²
ż1 = z2 + β1·(y − z1) + b0·u
ż2 = β2·(y − z1)
```

Prefer simplest integrator that meets `|u_track|<100` @ `N=80`. Reject single-step Euler over full `dt=60` if AC fails.

```python
# CAP-5 contrast / pass — same LadrcState instance throughout:
for _ in range(80):
    u_track = state.compute_tracking(y, T_r, thermal_cfg, zone)
    command = min(55.0, max(40.0, u_ff + u_track))
    u = command - u_ff
    # contrast: _advance_exp_map(state, y, u, thermal_cfg)  # mutates state.z*
    # pass:     state.advance(y, u, thermal_cfg)
```

Retarget `test_eso_bounded_with_60s_dt`: use thermal config + explicit one-step bound, or delete if multi-tick CAP-5 covers it.

## Verification

**Commands:**
- `uv run pytest tests/test_ladrc.py -q` -- divergence + boundedness + existing API pass
- `uv run ruff check apps/hvac/ladrc.py tests/test_ladrc.py` -- clean
