---
title: 'Blow-up guard in hvac_app'
type: 'bugfix'
ticket: '4'
created: '2026-10-16'
status: 'done'
baseline_revision: 'a4c0a19e2b5e4b8bf6cef3bb567948ff4463ddcb'
route: 'full'
route_source: 'auto'
review: 'quick'
review_source: 'pinned'
lenses_ran: ['quick']
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/initiative-fix-ladrc-blow-up/tickets/epic-fix-ladrc-blow-up/spec-fix-ladrc-blow-up/spec-fix-ladrc-blow-up.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** After `compute_tracking`, a non-finite or over-threshold `|u_track|` still drives `clamp(u_ff + u_track)` and can brick the loop until zone change / idle / plant-off; CAP-3(c) has no regression.

**Approach:** Add an `hvac_app`-only blow-up guard (pure Hass-free seam + WARNING formatter) that trips on non-finite or `|u_track| > u_track_max`, resets ESO, yields `clamp(u_ff)`, WARNING once per episode (Floor MUST fields), advances ESO after reset on the trip tick (decision B), and locks CAP-3(c) without AppDaemon.

## Boundaries & Constraints

**Always:**
- Guard lives only in `hvac_app` after `compute_tracking`; consume `effective_ladrc.u_track_max` (default 100 from story 1.3). Non-finite `u_track` always trips regardless of threshold.
- Pure guard seam **owns** trip-side effects: on trip it calls `ladrc.reset(measured)` and returns `command = clamp(u_ff)` to `[setpoint_min, setpoint_max]`; on healthy it does not reset and returns `clamp(u_ff + u_track)`. Then plant write as today; then **always** `advance_with_tracking_residue` with that command (decision B — advance after reset; residue ≈ 0 on trip).
- Seam inputs: `ladrc`, `measured`, `u_track`, `u_ff`, `u_track_max`, `setpoint_min`, `setpoint_max`, `latch_in`. Outputs: `command`, `tripped`, `should_warn` (`tripped and not latch_in`), `latch_out` (`True` if tripped else `False`), and `reason` when tripped (`magnitude`|`non-finite`) for the formatter.
- Episode latch owned by `HvacApp` (bool). Clear latch on healthy tick (`latch_out=False`) and set `_blow_up_latch = False` on `_hands_off` / `_go_idle` / no-demand paths (same places that `clear()` LADRC today).
- WARNING Floor MUST fields (exact prose free): `reason` (`magnitude`|`non-finite`), safe `u_track` render (finite → number; else `nan`/`inf`/`-inf`), `u_track_max`, `critical_zone`. Pure `format_blow_up_warning(...)` builds the string; `control_tick` logs it at WARNING only when `should_warn`. Zone from `decision.critical_zone` at the call site (not a LadrcState API).
- Pure module-level seams (Hass-free): function name **`guard_u_track`** + `format_blow_up_warning`; wire from `control_tick`; lock call site with `inspect.getsource` like story 1.2 (`guard_u_track` after `compute_tracking`).
- Tick INFO log: on trip, do **not** emit the normal success line with raw exploded `u_track`; emit INFO with **ff-only `command`** and a clear **`guarded`** marker (prose free). Healthy ticks keep today’s success INFO shape.
- CAP-3(c): poison `z2` and/or exploded `u_track` → ff-only command, ESO reset inside seam, latch/`should_warn`, formatter Floor fields — no Hass mock. CAP-2 “visible in HA logs” is live/manual, not asserted by pytest.

**Never:**
- Guard API or magnitude check inside `LadrcState`.
- Skip `advance` on a trip tick (refuse path A/C rejected).
- Lock a full WARNING sentence template (Floor fields only; prose free).
- On a trip tick, log INFO that formats raw non-finite / over-threshold `u_track` as if the tick were a normal success.
- Change continuous-form `advance`, known-input seam math, defaults/`u_track_max` parse, setpoint min/max, `control_interval`, ff, Critical Zone selection, MADRC, or online `b0`/`omega_o` adaptation.
- Mock full `HvacApp.control_tick` / Hass for CAP-3(c).

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected | Error Handling |
|----------|--------------|----------|----------------|
| Healthy | finite `\|u_track\| ≤ u_track_max`, `latch_in=False` | `clamp(u_ff+u_track)`; no reset; `should_warn=False`; `latch_out=False`; advance as today | Normal path |
| Magnitude trip | `\|u_track\| > u_track_max`, `latch_in=False` | reset; `clamp(u_ff)`; `should_warn=True`; `latch_out=True`; advance residue ≈ 0 | CAP-2 / CAP-3(c) |
| Non-finite trip | `u_track` NaN/Inf, `latch_in=False` | same as magnitude; `reason=non-finite` | Always trip |
| Consecutive trips | N>1 trip inputs, latch carried | `should_warn` only on first; later `should_warn=False`; still reset + ff-only + advance each trip | episode latch AC |
| Latch clear | healthy after trip, then trip again | mid healthy → `latch_out=False`; next trip `should_warn=True` | recover without idle |
| Poisoned z2 | large `z2` → exploded `u_track` via `compute_tracking` then seam | ff-only; post-reset `z2==0` | CAP-3(c) |
| Format Floor | magnitude or non-finite + zone | string contains reason, safe u_track, u_track_max, critical_zone; nan/inf no `.2f` crash | Floor MUST |
| Latch idle clear | `_hands_off` / `_go_idle` / no-demand source | assigns `_blow_up_latch = False` (with existing `clear()`) | inspect lock |
| Call site | `control_tick` source | calls `guard_u_track` after `compute_tracking`; logs via formatter when `should_warn`; no `LadrcState` guard API | inspect lock |
| Trip INFO | trip tick log path | INFO uses ff-only `command` + `guarded` marker; not raw exploded `u_track` success line | inspect / source |

</frozen-after-approval>

## Code Map

- `apps/hvac/hvac_app.py` — **`guard_u_track`** (inputs above; **calls `ladrc.reset(measured)` on trip**) + `format_blow_up_warning`; reuse `advance_with_tracking_residue` L21–29; wire `control_tick` after `compute_tracking` (~L91–111); `_blow_up_latch` on `HvacApp` (`initialize`; `= False` on `_hands_off`/`_go_idle`/no-demand); WARNING via formatter when `should_warn`; trip INFO = ff-only command + `guarded` marker.
- `apps/hvac/ladrc.py` — `reset` / `compute_tracking`: **reuse only**; no guard API. `reset` does not clear `critical_zone`.
- `apps/hvac/models.py` — `u_track_max` already default 100 — **read only**.
- `apps/apps.yaml.example` — L23–24: comment that `u_track_max` is the live magnitude guard (°C).
- `tests/test_hvac_app.py` — CAP-3(c) seam + consecutive-trip latch + formatter Floor + inspect (`guard_u_track` after `compute_tracking`, latch clears, trip INFO `guarded`); keep residue tests.
- Continuity: stories 1.2–1.3 seams/config done — do not retouch `LadrcState.advance` / CAP-3(a)(b).

## Tasks & Acceptance

**Execution:**
- [ ] `apps/hvac/hvac_app.py` -- `guard_u_track` (full I/O; owns `reset` on trip) + `format_blow_up_warning` Floor MUST + wire `control_tick` (advance B; latch clears; trip INFO ff-only + `guarded`) -- CAP-2.
- [ ] `apps/apps.yaml.example` -- Comment: live magnitude guard (°C) -- operator truth.
- [ ] `tests/test_hvac_app.py` -- I/O matrix: seam, N consecutive trips, formatter Floor, inspect `guard_u_track` + latch-clear + `guarded` INFO; no Hass -- CAP-3(c).

**Acceptance Criteria:**
- Given finite `|u_track| ≤ u_track_max`, when `guard_u_track` runs, then command is `clamp(u_ff+u_track)`, ESO not reset, `should_warn=False`, `latch_out=False`.
- Given `|u_track| > u_track_max` or non-finite `u_track` with `latch_in=False`, when `guard_u_track` runs, then it calls `reset(measured)`, returns `clamp(u_ff)`, `should_warn=True`, `latch_out=True`.
- Given N>1 consecutive trip inputs with latch carried, when `guard_u_track` runs each time, then `should_warn` is true only on the first.
- Given a trip then a healthy input then a trip, when `guard_u_track` runs, then the later trip has `should_warn=True`.
- Given Floor inputs (magnitude and non-finite), when `format_blow_up_warning` runs, then the string includes reason, safe u_track, u_track_max, and critical_zone without crashing on nan/inf.
- Given a trip tick after write, when advance runs, then `advance_with_tracking_residue` uses the ff-only command (decision B).
- Given poisoned `z2` → exploded `u_track`, when `guard_u_track` runs, then ff-only command and post-reset `z2 == 0` (reset owned by seam).
- Given `HvacApp.control_tick` source, when inspected, then it calls `guard_u_track` after `compute_tracking` and does not call a `LadrcState` guard API.
- Given `_hands_off` / `_go_idle` / no-demand paths in `hvac_app.py`, when inspected, then each sets `_blow_up_latch = False`.
- Given `control_tick` source, when inspected, then a trip path logs INFO with a `guarded` marker and does not format raw trip `u_track` in the normal success line.

## Implementation Notes

## Plan Change Log

- 2026-10-16 party (Floor/Must/B/AC): WARNING Floor MUST fields + `format_blow_up_warning`; seam `should_warn`/`latch_out` ACs (no Hass); consecutive-trip latch AC; advance-after-trip B kept.
- 2026-10-16 plan-review patch-all: seam owns `reset(measured)`; full seam I/O in Always; latch-clear inspect AC on idle/hands-off/no-demand; Design Notes show reset.
- 2026-10-16 lows locked: seam name `guard_u_track`; trip INFO = ff-only command + `guarded` marker (no raw exploded u_track success line).

## Review Triage Log

- 2026-10-16 plan-review: high=1 medium=2 low=2 false=4 — patched blocker (reset ownership) + both mediums; lows later locked by human (`guard_u_track`, guarded INFO).
- 2026-10-16 quick: medium — `control_tick` sets `_blow_up_latch` and can early-return on failed `_write_setpoint` before WARNING; first-trip `should_warn` is lost for the episode. Evidence: L179–181 latch+return before L193–202 WARNING; `_write_setpoint` returns False when plant unavailable. Route: patch.
- 2026-10-16 quick: false — README.md / docs/house-calibration.md / party-mode .memlog.md appear in baseline→HEAD dirty tree but were not authored by this story’s implementation (Code Map only touches hvac_app / apps.yaml.example / test_hvac_app). Pre-existing WIP noise, not a scope violation of the guard change.

## Design Notes

```text
guard_u_track(ladrc, measured, u_track, u_ff, u_track_max,
              setpoint_min, setpoint_max, latch_in):
  if trip: ladrc.reset(measured); command = clamp(u_ff)
  else:    command = clamp(u_ff + u_track)
  return command, tripped, should_warn, latch_out, reason?

control_tick (demand path):
  u_track = compute_tracking(...)
  result = guard_u_track(self._ladrc, measured, u_track, u_ff,
                         effective_ladrc.u_track_max, min, max,
                         latch_in=self._blow_up_latch)
  self._blow_up_latch = result.latch_out
  write(result.command)
  advance_with_tracking_residue(...)  # always, incl. after trip (B)
  if result.should_warn:
      self.log(format_blow_up_warning(...), level="WARNING")
  if result.tripped:
      self.log(... command=ff-only ... guarded ...)  # INFO
  else:
      self.log(... normal success with u_track ...)

Trip: (not isfinite(u_track)) or abs(u_track) > u_track_max
```

## Verification

**Commands:**
- `uv run pytest tests/test_hvac_app.py -q` -- CAP-3(c) seam/latch/formatter + residue green
- `uv run pytest tests/test_ladrc.py tests/test_ladrc_tuner.py -q` -- CAP-3(a)(b) / parse unchanged
- `uv run ruff check apps/hvac/hvac_app.py tests/test_hvac_app.py` -- clean

**Manual (CAP-2 HA visibility):** confirm WARNING appears in AppDaemon/HA logs on a live trip — not covered by pytest.
