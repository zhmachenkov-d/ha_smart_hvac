---
title: 'Refactor sweep'
type: 'refactor'
ticket: '5'
created: '2026-10-16'
status: 'done'
baseline_revision: '039c8e504e644e0953662f6a6311e908a4a237ef'
route: 'full'
route_source: 'auto'
review: 'quick'
review_source: 'pinned'
lenses_ran: ['quick']
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Entries 1–4 left deferred review nits (hand-listed `with_omega_c` copy, weak CAP-5 diverge OR, missing WARNING-before-write inspect lock) plus latch hygiene gap: Critical Zone change resets the ESO but can leave `_blow_up_latch` set and suppress the next WARNING.

**Approach:** Closing sweep = mechanical cleanup/test hardenings **and** latch hygiene on Critical Zone change (Decision A). No new capabilities (Huang CAP-3a, validation, refuse-to-advance stay out). Do not claim “no production behavior change” — latch clear is intentional, small, and in scope.

**Decisions:**
- Critical-zone latch: **A** — when Critical Zone changes under demand, clear `_blow_up_latch` before guard so a trip in the new zone can emit WARNING (walkthrough-18e21d1).
- Framing: Intent names **cleanup + latch hygiene**, not “strictly no prod behavior.”
- Zone-latch AC: pure Hass-free helper + Matrix rows for `None→first`, `A→A`, `A→B` (party #2) — not inspect-only.
- `last_u_applied` API: **drop** — leave residue tests on `_last_u_applied` (pr-24 accepted pragmatic); no new public property (party #3).

## Boundaries & Constraints

**Always:**
- Scope is the deferred cleanup items in Tasks (walkthroughs pr-22/24/26/18e21d1) plus latch hygiene (Decision A). No Huang/validation/refuse/ADR/example-retune.
- Production control math, ESO integrator, guard trip rules, warn-before-write order, and example defaults stay unchanged; the only intentional production behavior delta is clearing `_blow_up_latch` on Critical Zone change.
- Prefer `dataclasses.replace` for `with_omega_c`. Do not add a public `last_u_applied` property; residue tests may keep asserting `_last_u_applied`.
- CAP-5 diverge assert must require non-finite or `|u_track|≥1e6` on the track sequence (z-only finite path insufficient).
- Inspect lock (demand path only): after the `has_demand` early-return, `format_blow_up_warning` appears before the `_write_setpoint(guard.command)` call. Do **not** compare against the no-demand `_write_setpoint(0)` earlier in the same method.
- Pure helper (name free, e.g. `latch_after_zone_change(prev_zone, new_zone, latch_in) → latch_out`) owns the rule: clear only when `prev_zone is not None` and `prev_zone != new_zone`; otherwise return `latch_in` unchanged. `control_tick` captures `prev = self._ladrc.critical_zone`, sets `_blow_up_latch = helper(prev, decision.critical_zone, self._blow_up_latch)` **before** `compute_tracking`, then passes that `_blow_up_latch` as `latch_in` into `guard_u_track` (guard later overwrites with `latch_out`). Unit-test the Matrix rows without Hass; inspect: helper call index &lt; `compute_tracking` index.

**Never:**
- Huang+absolute CAP-3a test (`deferred-work.md`), `u_track_max` sign/range validation, refuse-to-advance, MADRC, retune gains, change `_ESO_EULER_SUBSTEPS`, rename `guard_u_track` / `advance_with_tracking_residue` / `u_track_max`.
- Edit ADR 0002/0003, `apps.yaml.example` comments, or story plan checkbox archaeology.
- Mock Hass / full `control_tick` for new coverage.
- Put latch clear inside `LadrcState` (app owns latch).

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| CAP-5 diverge | frozen exp_map thermal+C | assert fails unless some `u_track` non-finite or `|u|≥1e6` | z-only non-finite alone does not pass |
| Warn-before-write inspect | demand slice of `control_tick` (after `has_demand` return) | `format_blow_up_warning` before `_write_setpoint(guard.command)` | ignore no-demand write |
| with_omega_c | config with non-default `u_track_max` | preserved after `with_omega_c` (replace-based) | Existing parse tests |
| Zone A→B + latch | `prev=A`, `new=B`, `latch_in=True` | helper → `False`; trip can WARNING | Decision A |
| Zone A→A + latch | `prev=A`, `new=A`, `latch_in=True` | helper → `True` (unchanged) | same episode |
| None→first + latch | `prev=None`, `new=B`, `latch_in=True` | helper → `True` (no clear) | first assign ≠ change |
| Latch already False | any zones, `latch_in=False` | helper → `False` | no-op |

</frozen-after-approval>

## Code Map

- `apps/hvac/models.py` — `LadrcConfig.with_omega_c` L93–103: replace hand-list with `dataclasses.replace(self, omega_c=…)`.
- `apps/hvac/ladrc.py` — **do not change** (`_last_u_applied` stays private; zone reset stays in `compute_tracking`).
- `apps/hvac/hvac_app.py` — pure `latch_after_zone_change` (or equiv.); `control_tick`: `prev = self._ladrc.critical_zone` → `_blow_up_latch = helper(...)` → `compute_tracking` → `guard_u_track(..., latch_in=self._blow_up_latch)`; demand-path warn-before-write stays.
- `tests/test_hvac_app.py` — leave residue `_last_u_applied` asserts; demand-slice warn-before-write inspect; unit-test helper Matrix (`None→first`, `A→A`, `A→B`, latch False); inspect `helper` index &lt; `compute_tracking`.
- `tests/test_ladrc.py` — `test_cap5_exp_map_thermal_c_diverges` L173–183: drop z-only OR arm; require track blow.
- `tests/test_ladrc_tuner.py` — existing `test_with_omega_c_preserves_u_track_max` must still pass; no new validation.
- Out of scope continuity: CAP-5 continuous bounded, guard seam I/O, `advance` substeps — untouched.

## Tasks & Acceptance

**Execution:**
- [x] `apps/hvac/models.py` -- `with_omega_c` via `dataclasses.replace` -- walkthrough-pr-26 footgun.
- [x] `apps/hvac/hvac_app.py` -- `latch_after_zone_change` + wire before `compute_tracking` -- Decision A / party #2.
- [x] `tests/test_hvac_app.py` -- warn-before-write inspect; Matrix unit tests for latch helper -- 18e21d1 + #2.
- [x] `tests/test_ladrc.py` -- tighten CAP-5 diverge to track blow only -- walkthrough-pr-22.

**Acceptance Criteria:**
- Given a `LadrcConfig` with non-default `u_track_max`, when `with_omega_c` runs, then `u_track_max` is unchanged and `with_omega_c` uses `dataclasses.replace` (no hand-maintained field list).
- Given `test_cap5_exp_map_thermal_c_diverges`, when it passes, then at least one `u_track` is non-finite or `|u_track|≥1e6` (z-only divergence insufficient).
- Given the demand path of `HvacApp.control_tick` source (after the `has_demand` early-return), when inspected, then `format_blow_up_warning` appears before `_write_setpoint` of `guard.command` (no-demand `_write_setpoint(0)` ignored).
- Given latch helper with `prev=A`, `new=B`, `latch_in=True`, when called, then returns `False`.
- Given latch helper with `prev=A`, `new=A`, `latch_in=True`, when called, then returns `True`.
- Given latch helper with `prev=None`, `new=B`, `latch_in=True`, when called, then returns `True` (first zone is not a change).
- Given latch helper with any zones and `latch_in=False`, when called, then returns `False`.
- Given `control_tick` source, when inspected, then the latch helper call appears before `compute_tracking`.
- Given the suite, when `uv run pytest` and `uv run ruff check apps/hvac tests` run, then green; diff is cleanup + latch hygiene only (no Huang/validation/refuse/ADR/example-retune).

## Implementation Notes

## Plan Change Log

- 2026-10-16 plan-review patch-all: demand-slice warn-before-write inspect (ignore no-demand write); latch helper → latch_in to guard; Matrix/AC for latch_in=False; call-site `helper < compute_tracking`; with_omega_c AC tightened to `u_track_max` + replace.

## Review Triage Log

- 2026-10-16 plan-review: high=1 medium=3 low=2 false=6 — patched all (blocker + mediums + lows).

## Design Notes

```text
In-scope: cleanup nits + latch hygiene (honest framing).
  pr-26: with_omega_c → dataclasses.replace
  pr-22: CAP-5 diverge = track blow (drop z-only OR)
  18e21d1: inspect WARNING/format before _write_setpoint
  18e21d1 zone-latch: Decision A + helper Matrix (None/A→A/A→B)

Out: last_u_applied public API (party #3 — keep _last_u_ asserts);
     Huang CAP-3a, u_track_max validation, refuse-to-advance,
     Euler substep band, rename seams, ADR/example prose.
```

## Verification

**Commands:**
- `uv run pytest tests/test_ladrc.py tests/test_hvac_app.py tests/test_ladrc_tuner.py -q` -- all green; CAP-5 diverge + residue + with_omega_c + inspect locks hold
- `uv run ruff check apps/hvac tests` -- clean
- `git diff --stat 039c8e504e644e0953662f6a6311e908a4a237ef` -- only Code Map files; no ADR/example/Huang additions
