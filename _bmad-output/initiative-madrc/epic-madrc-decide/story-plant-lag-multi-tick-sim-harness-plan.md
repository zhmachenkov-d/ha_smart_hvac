---
title: 'Plant-lag multi-tick sim harness'
type: 'feature'
ticket: '1'
created: '2026-10-17'
status: 'done'
baseline_revision: 'a2625210e5e4b22ca93cf9b02293d639c8a627c8'
route: 'full'
route_source: 'auto'
review: 'quick'
review_source: 'pinned'
lenses_ran: ['quick']
review_loop_iteration: 0
context:
  - '{project-root}/knowledge/concepts/madrc.md'
  - '{project-root}/docs/house-calibration.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Later decide-epic work (R1 jump classification, R3 `control_interval`, R7 FF keep/drop) needs a shared closed-loop unit/sim of LADRC on a high-order lag plant; today tests only loop LADRC with fixed `y`/`u_ff` and never close the plant or log command/y/z series.

**Approach:** Add a reusable multi-tick harness: discrete \(K/(Ts+1)^n\) plant, outdoor as input, FF-on (via `weather_feedforward`) vs `u_ff=0`, production track → `guard_u_track` → residue advance, recording command / y / u_track / z each tick; ship one verifying unit test.

**Decisions:**
- Harness lives under `tests/harness/` (test-only package; production `ha_smart_hvac` stays clean). Later stories import from there.
- Blow-up latch across ticks uses production `sticky_blow_up_latch` (CAP-4), not bare `guard.latch_out`.
- On trip after a successful simulated write: `LadrcState.reset(y)` then `advance_with_tracking_residue` (same order as App).
- Plant pins stay absolute `K=0.45` starter (not house-calibrated); series field legend lives in Design Notes.

## Boundaries & Constraints

**Always:**
- Residue to ESO is `command − u_ff` via `advance_with_tracking_residue` (not absolute SWT).
- Plant is cascade first-order lag \(K/(Ts+1)^n\) stepped at the harness `dt` (same as LADRC `config.dt`).
- Outdoor temperature is a harness input (FF and later regime discussion); not auto-tuned.
- FF-on uses `weather_feedforward(outdoor, WeatherFeedforwardConfig)`; FF-off / zero path forces `u_ff=0` without inventing a production enable flag.
- Series logged per tick include at least `command`, `y`, `u_track`, `z1`, `z2` (and latch/tripped flags useful for R1).
- Sim modules stay under `tests/harness/` — not shipped in the App package.
- Tick contract mirrors App write path: track → `guard_u_track` → record → sticky latch update → on trip `reset(y)` → `advance_with_tracking_residue` → plant step(`command`).

**Never:**
- No production MADRC \(G_{cp}\), scheduling, or AppDaemon wiring changes.
- No Exclusive Session / live plant.
- Do not modify `LadrcState.advance` / Euler substeps or frozen `_advance_exp_map` baselines.
- Do not add a YAML FF on/off switch in this story.
- Do not classify jumps or pick `control_interval` here (later entries).
- Do not place the plant/harness under `apps/ha_smart_hvac/`.
- Do not treat `guard.latch_out` as the sticky soft-kill memory.
- Do not treat harness series as go/no-go evidence for R1, R7, or the ADR — setup only; classification and keep/drop decisions stay in later entries.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| FF on, N ticks | outdoor set; FF config with non-zero slope/base; plant K,T,n | Series length N; `u_ff` from `weather_feedforward`; command from guard path; y evolves from plant | No error expected |
| FF zeroed | same plant/outdoor; `u_ff=0` mode | Series length N; residue = command − 0; command still from guard(`u_track`, 0, …) | No error expected |
| Guard trip | force `|u_track| > u_track_max` (e.g. tiny `u_track_max`) | `command` = clamp(`u_ff`); `reset(y)` then residue advance; sticky latch holds while CAP-4 decay band says so | Harness does not raise; series record `tripped` / latch |

</frozen-after-approval>

## Code Map

- `apps/ha_smart_hvac/ladrc.py` — `LadrcState.compute_tracking` / `advance` / `reset(measured)` / `z1`/`z2`; reuse as-is.
- `apps/ha_smart_hvac/hvac_app.py` — `guard_u_track`, `sticky_blow_up_latch`, `advance_with_tracking_residue`, `GuardUTrackResult`; harness calls these (App trip/write order without Hass).
- `apps/ha_smart_hvac/feedforward.py` — `weather_feedforward(outdoor_temp, config)`.
- `apps/ha_smart_hvac/models.py` — `LadrcConfig.u_track_max`; `WeatherFeedforwardConfig`; setpoint clamps are **not** on `LadrcConfig` — harness takes `setpoint_min`/`setpoint_max` as runner args (App: `HvacConfig`).
- `tests/test_ladrc.py` — `_run_thermal_c_ticks` (~L90–108): open-loop y, fixed `_U_FF`, records only `u_track`; pattern to supersede for closed-loop, do not break existing CAP-5 tests. `_example_aligned_config` for thermal-band pins.
- `tests/test_feedforward.py` — formula coverage only; leave alone.
- `tests/test_hvac_app.py` — residue/guard/sticky mirrors; do not couple harness to Hass.
- `tests/harness/` — **new** test-only package (`plant.py`, `runner.py`, `__init__.py`).
- `pyproject.toml` — `[tool.pytest.ini_options] pythonpath` currently `["apps"]`; add `"tests"` so `import harness…` works for later stories.
- No existing plant model in code — only `knowledge/concepts/madrc.md` (\(G_p=K/(Ts+1)^n\)).

**Reuse:** production FF + guard + sticky latch + residue seams; example-aligned `LadrcConfig` + `apps.yaml.example` FF/clamps as verifying-test defaults.

**Do not change:** production ESO math; AppDaemon `control_tick`; CAP-5 locked scenarios in `test_ladrc.py`.

## Tasks & Acceptance

**Execution:**
- [x] `pyproject.toml` — add `"tests"` to pytest `pythonpath` — enable `import harness` for this and later stories
- [x] `tests/harness/__init__.py`, `tests/harness/plant.py`, `tests/harness/runner.py` — Euler cascade plant + multi-tick runner (outdoor; FF-on vs `u_ff=0`; track → guard → sticky latch → reset-on-trip → residue → plant; append series) — shared setup for R1/R3/R7
- [x] `tests/test_plant_lag_harness.py` — N-tick closed-loop with pinned defaults; FF-on and `u_ff=0` series assertions; one forced guard-trip case — verify ticket AC + I/O matrix

**Acceptance Criteria:**
- Given a \(K/(Ts+1)^n\) plant and outdoor temperature, when the harness runs N ticks with FF on (pinned defaults below), then logged series for `command` and `u_track` (and `y`, `z1`, `z2`) have length N and all finite.
- Given the same plant/outdoor, when the harness runs with `u_ff=0`, then series length is N and ESO advances with residue `command − 0`.
- Given harness reuse from a second import site in the same test module, when two modes are run back-to-back, then neither mode mutates the other's recorded series (fresh state per run).
- Given a run with `u_track_max` small enough to force a trip, when a tick trips, then that tick’s `command` equals clamp(`u_ff`) within setpoint bounds and sticky latch is true on that tick (and held while decay band applies).

## Implementation Notes

## Plan Change Log

## Review Triage Log

- 2026-10-17 quick: high=0 medium=1 low=1 false=0 maybe-false=0
  - low → rejected — `tests/harness/runner.py` append-after-plant vs Always “record after guard”: command/y/u_track/tripped are post-guard values; z/latch post-update matches Design Notes legend; everyday harm is append-site pedantry, not series semantics — rejected (low + non-trivial reorder vs legend)
  - medium → patch — forced-trip test never sees latch True with tripped False; CAP-4 decay-band hold from I/O matrix / AC parenthetical unexercised with `u_track_max=1.0` (all 40 ticks re-trip) — evidence: ran setup; `sticky_blow_up_latch` needs `latch_in and |u|>0.8·max` without trip

## Design Notes

- Discrete plant (Euler @ `dt`): cascade \( \dot x_1=(K\cdot u-x_1)/T \), \( \dot x_i=(x_{i-1}-x_i)/T \) for \(i=2..n\); \(y=x_n\). API `(K, T, n, dt)` — no Wang SST constants.
- Tick order (App write path, no Hass): `u_ff` → `compute_tracking(y, T_r, config, critical_zone)` → `guard_u_track(..., latch_in)` → append series → `sticky_blow_up_latch` → if tripped: `reset(y)` → `advance_with_tracking_residue` → `plant.step(command)`. Assume simulated write always succeeds.
- Runner must take `critical_zone` (required by `compute_tracking`).
- Series: dataclass or dict-of-lists; include `tripped` / `latch` for later R1.
- Import: `from harness.runner import …` after `pythonpath` includes `tests`.
- **Pinned verifying-test defaults** — starter pins for finite series, **not a house plant model** (absolute water→air with `K=0.45` is convenient, not calibrated): `N=40`, `y0=20.0`, `T_r=21.0`, `critical_zone="living_room"`, `outdoor=0.0`, plant `(K=0.45, T=300.0, n=3)`, `setpoint_min=40`, `setpoint_max=55`, FF `base=25, slope=1.2, comfort_ref=20`, LADRC = `_example_aligned_config()` shape (`b0=5e-4`, `omega_o=0.03`, `omega_c=0.03`, `u_track_max=250`, `dt=60`). Forced-trip case: same setup with tiny `u_track_max` (e.g. `1.0`).
- **Series legend** (per-tick fields the runner records):

  | Field | Meaning |
  |-------|---------|
  | `command` | Post-guard clamped Set Water Temperature (°C) |
  | `y` | Plant output (lag state); not house-calibrated air °C |
  | `u_track` | LADRC tracking correction before guard |
  | `z1`, `z2` | ESO states after the tick’s advance |
  | `u_ff` | Feedforward baseline this tick (`weather_feedforward` or `0`) |
  | `tripped` | `guard.tripped` this tick |
  | `latch` | Sticky CAP-4 latch after this tick’s update |

## Verification

**Commands:**
- `uv run pytest tests/test_plant_lag_harness.py -q` -- expected: all pass
- `uv run pytest tests/test_ladrc.py tests/test_feedforward.py -q` -- expected: existing CAP-5 / FF tests still pass
- `uv run ruff check tests/harness tests/test_plant_lag_harness.py` -- expected: clean
