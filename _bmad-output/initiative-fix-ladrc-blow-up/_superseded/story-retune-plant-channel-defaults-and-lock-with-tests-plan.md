---
title: 'Retune plant-channel defaults and lock with tests'
type: 'bugfix'
ticket: 'superseded-retune-plant-channel-defaults'
created: '2026-10-16'
status: 'dropped'
blocked_reason: 'Superseded by 2026-10-16 epic re-slice (continuous-form ESO tracer is new entry 1.1). Do not resume this plan.'
baseline_revision: '5463eef1bf72344a7d3bc3fcc2a4d5b12760d4ff'
route: 'full'
route_source: 'auto'
review: ''
review_source: ''
lenses_ran: []
review_loop_iteration: 0
context:
  - '{project-root}/CONTEXT.md'
  - '{project-root}/docs/adr/0002-ladrc-critical-zone-control.md'
  - '{project-root}/docs/adr/0003-online-ladrc-omega-c-auto-tune.md'
  - '{project-root}/_bmad-output/initiative-fix-ladrc-blow-up/tickets/epic-fix-ladrc-blow-up/spec-fix-ladrc-blow-up/spec-fix-ladrc-blow-up.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Example plant-channel LADRC gains (`b0=2.8`, `omega_o=19.49`) at `dt=60` with absolute Set Water Temperature make the ESO/`u_track` diverge; there is no config knob for a magnitude trip that story 2 will use, and ADR 0002 does not warn maintainers off Huang gains for this plant.

**Approach:** Retune example `b0`/`omega_o` for absolute SWT at 60 s, add a `|u_track|` magnitude threshold field (default 100 °C) on `LadrcConfig` / `apps.yaml.example`, amend ADR 0002, and lock divergence + new-default boundedness with multi-tick tests (guard path stays story 2).

**Decisions:**
- OQ-1 → **C** (2026-10-16): Planning probe shows retune alone cannot meet CAP-1 as written under current `LadrcState` + absolute SWT at `dt=60`. Pause story 1 implementation; renegotiate epic/spec (possible ESO / `u` semantics) before coding defaults. Config field naming (former OQ-2) deferred until the revised contract.

## Boundaries & Constraints

**Always:**
- Keep `command = clamp(u_ff + u_track)` and advance ESO with the actually applied absolute SWT command (`apps/hvac/ladrc.py`, `hvac_app.py`).
- Online auto-tune remains ωc-only (ADR 0003 unchanged).
- Plant limits stay 40/55.
- Threshold is a config field, example/default **100** °C; story 2 consumes it — no guard logic in this story.
- `LadrcState` stays a pure tracker/ESO (no guard API).
- CAP-3 in this story: divergence under old/large gains + boundedness under new defaults only.

**Never:**
- Blow-up guard in `hvac_app` (story 2).
- Online `b0` / `omega_o` adaptation.
- Feedforward redesign, Critical Zone selection, setpoint min/max changes.
- Editing live `apps/apps.yaml` entity IDs or committing secrets.
- Changing ADR 0003's ωc-only scope.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Old/large gains multi-tick | `b0=2.8`, `omega_o=19.49`, `dt=60`, `y≈21`, `T_r` near air, applied `u∈[40,55]`, N advances | `|u_track|` and/or `z` leave the sane band (reproduce divergence) | Assert divergence (test fails if old gains look "safe") |
| New defaults multi-tick | Example `b0`/`omega_o`, same scenario | `u_track`, `z1`, `z2` finite; `|u_track|` within agreed bound (tens of °C scale, not 1e6+) | Assert finite + magnitude bound |
| Config threshold default | YAML omits new field OR sets `100` | Parsed `LadrcConfig` exposes threshold `100.0` | Parse error only if present and non-numeric |
| ADR maintainers | Read ADR 0002 after amend | Huang `b0`/`ωo` forbidden at `dt=60` + absolute SWT; new defaults = house-calibration starting points | ADR 0003 still ωc-only |

</frozen-after-approval>

## Code Map

- `apps/hvac/models.py` — `LadrcConfig` (L74–101): add magnitude threshold field with default `100.0`; update `with_omega_c` to copy it.
- `apps/hvac/config.py` — `_parse_ladrc` (L73–93): parse new field (`raw.get(..., 100)` or require); leave tune/`omega_c` validation unchanged.
- `apps/apps.yaml.example` — `ladrc:` (L16–26): new `b0`/`omega_o`; add threshold key default `100`. Do not touch zone entity placeholders.
- `apps/hvac/ladrc.py` — `LadrcState.compute_tracking` / `advance` / `reset`: reuse for tests; **do not** add guard API.
- `apps/hvac/hvac_app.py` — tick path uses `compute_tracking` then `advance(measured, command, …)` (L79–93); **no guard this story**.
- `tests/test_ladrc.py` — split helpers: intentional **old** Huang gains for divergence; **new** defaults for boundedness; add multi-tick loops (`compute_tracking` → `advance` with absolute `u`).
- `tests/test_ladrc_tuner.py` — `LadrcConfig(...)` sites: only touch if new field has no default; keep Huang-era `b0`/`omega_o` (tuner scope).
- `docs/adr/0002-ladrc-critical-zone-control.md` — amend Huang/`dt=60`/absolute-SWT warning + house-calibration note.
- `docs/adr/0003-online-ladrc-omega-c-auto-tune.md` — verify unchanged ωc-only (no edit unless accidental drift).

## Tasks & Acceptance

**Execution:**
- [ ] `apps/hvac/models.py` -- Add `|u_track|` magnitude threshold field (default `100.0`) and thread it through `with_omega_c` -- handoff for story 2; safe default for existing constructors.
- [ ] `apps/hvac/config.py` -- Parse the threshold into `LadrcConfig` -- YAML → runtime config.
- [ ] `apps/apps.yaml.example` -- Set retuned `b0`/`omega_o` and document threshold `100` -- operators get safe starting example.
- [ ] `tests/test_ladrc.py` -- Add multi-tick divergence (old/large gains) and boundedness (new defaults) tests per I/O matrix -- locks CAP-1/CAP-3 for this story.
- [ ] `docs/adr/0002-ladrc-critical-zone-control.md` -- Amend Huang/`dt=60`/absolute-SWT + house-calibration prose -- CAP-4.
- [ ] `docs/adr/0003-online-ladrc-omega-c-auto-tune.md` -- Confirm still ωc-only (no content change) -- CAP-4.

**Acceptance Criteria:**
- Given old/large gains (`b0=2.8`, `omega_o=19.49`) and absolute SWT advances at `dt=60` with `y≈21`, when N ticks run, then the test asserts divergence (non-finite or `|u_track|` beyond the sane band).
- Given the new example defaults and the same multi-tick scenario, when N ticks run, then `u_track`/`z1`/`z2` stay finite and `|u_track|` stays within the agreed bound.
- Given `apps.yaml.example` / parsed config, when loaded, then threshold is `100` and example `b0`/`omega_o` match the values locked by the boundedness test.
- Given ADR 0002 after the change, when read, then it warns against Huang gains at `dt=60` with absolute SWT and notes house calibration; ADR 0003 remains ωc-only.

## Implementation Notes

- superseded by 2026-10-16 re-slice — new tracer is story Continuous-form ESO in LadrcState (ref 1.1).

## Plan Change Log

## Review Triage Log

## Design Notes

- Prefer field name `u_track_max` (float °C) on `LadrcConfig`, YAML key `u_track_max` under `ladrc:` — matches existing `setpoint_max` / `omega_c_max` style. Default `100.0` on the dataclass so tuner tests need not pass it.
- Parse with default `100` when omitted so live `apps.yaml` without the key keeps working until operators add it.
- Keep `tests/test_ladrc_tuner.py` on Huang-era `b0`/`omega_o`; those tests are about ωc adaptation, not plant-channel stability.
- Exact numeric `b0`/`omega_o` are locked by the boundedness test (spec), not by copying Huang. Spec starting bands: `b0 ~ 1e-4–1e-3`, `omega_o ~ 0.01–0.05` with `omega_o*dt` moderate — planning probe could not find values in that band that meet “tens of °C” under open multi-tick absolute-SWT advances with constant `y≈21` (blocked pending renegotiation per OQ-1=C).

## Verification

**Commands:**
- `uv run pytest tests/test_ladrc.py -q` -- expected: divergence + boundedness tests pass; existing LADRC unit tests still pass.
- `uv run pytest tests/test_ladrc_tuner.py -q` -- expected: still pass (Huang fixtures / optional new field default).
- `uv run ruff check apps/hvac tests/test_ladrc.py` -- expected: clean on touched Python.
- Manual: read ADR 0002 amendment + confirm ADR 0003 body unchanged (`git diff docs/adr/0003-online-ladrc-omega-c-auto-tune.md` empty).
