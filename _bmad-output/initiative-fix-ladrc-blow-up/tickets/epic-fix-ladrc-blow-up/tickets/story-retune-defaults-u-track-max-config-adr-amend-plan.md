---
title: 'Retune defaults, u_track_max config, ADR amend'
type: 'bugfix'
ticket: '3'
created: '2026-10-16'
status: 'done'
baseline_revision: '8048e80caec66ef74ea8a33de7474384abf3b00e'
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

**Problem:** Example LADRC gains are still Huang (`b0=2.8`, `omega_o=19.49`); there is no `u_track_max` config handoff for the guard story; ADR 0002 lacks the CAP-4 amendment bullets.

**Approach:** Retune `apps.yaml.example` `b0`/`omega_o` to the CAP-5 thermal band; add `u_track_max` (default 100) on `LadrcConfig` / parse / example (field only — guard wires it in entry 4); lock CAP-3(b) boundedness on those example defaults under continuous-form + C known-input; amend ADR 0002; leave ADR 0003 untouched (ωc-only).

## Boundaries & Constraints

**Always:**
- Example `b0=5e-4`, `omega_o=0.03` (same as CAP-5 thermal); keep example `omega_c=0.053` and existing ωc bounds (party lock A: product YAML ≠ CAP-5 test `omega_c=0.01`).
- Comment on example `omega_c`: starting point for online ωc tune (ADR 0003), not the CAP-5 unit-test value.
- `u_track_max: float` on `LadrcConfig`, YAML key under `ladrc:` in example, dataclass default `100.0`; omit in YAML → 100 (live configs keep working). Party lock Stay: field ships in this story; guard wires it in entry 4.
- Mandatory comment on example `u_track_max`: magnitude guard threshold (°C); not enforced until blow-up recovery lands.
- CAP-3(b) multi-tick: continuous-form `advance` + known input `u=command−u_ff`, plant `clamp(u_ff+u_track)`, locked scenario (`y=21`, `T_r=21.2`, `u_ff=40`, clamp `[40,55]`, `dt=60`, `N=80`) with **example-aligned** gains (`b0=5e-4`, `omega_o=0.03`, `omega_c=0.053`); every tick finite and `|u_track|<100` (ticket “tens of °C” ⇒ same CAP-5 bar `<100`, not a tighter bound).
- `with_omega_c` must preserve `u_track_max` (live tuner path copies config each tick).
- If CAP-3(b) fails, nudge only `b0`/`omega_o` within `b0 ~ 1e-4–1e-3`, `omega_o ~ 0.01–0.05`; **`omega_c` stays `0.053`** unless human renegotiates party A. Record nudges in Implementation Notes; sync example + test. Do not replace example `omega_c` with CAP-5 `0.01`.
- ADR 0002 must-language (party lock Hard / CAP-4): `exp_map` @ `dt=60` **fails** and must not return; ESO **must** use continuous-form advance (`β1=2ωo`, `β2=ωo²` over the sample — no integrator recipe); known input **must** be post-clamp `(command − u_ff)`; Huang `b0`/`ωo` **must not** be used on this plant; new example defaults **need house calibration**.
- ADR 0003: no edit; verify empty `git diff`.

**Never:**
- Wire the blow-up guard in `hvac_app` (entry 4).
- Change `LadrcState.advance`, known-input seam, setpoint min/max, `control_interval`, ff, Critical Zone, MADRC, or online `b0`/`omega_o` adaptation.
- Force CAP-5 test `omega_c=0.01` into the example (would break `omega_c_min=0.02` parse).
- Soften ADR 0002 to “not copy-paste” / discourage — use must / must not.
- Put Euler substep count or other integrator recipe into ADR 0002.
- Edit ADR 0003 body.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected | Error Handling |
|----------|--------------|----------|----------------|
| Example defaults + C | Continuous `advance`, example-aligned gains, locked scenario, `N=80` | Finite; `|u_track|<100` each tick | CAP-3(b) |
| Parse omit `u_track_max` | `parse_config` without key | `ladrc.u_track_max == 100.0` | Default |
| Parse / example expose | Load real `apps/apps.yaml.example` via `parse_config` | `b0`/`omega_o` match CAP-3(b); `u_track_max=100` | CAP-1/verify |
| `with_omega_c` preserve | Parsed config with any `u_track_max` | `.with_omega_c(x).u_track_max` unchanged | Tuner handoff |
| ADR 0003 | After story | Unchanged ωc-only | Empty diff |

</frozen-after-approval>

## Code Map

- `apps/hvac/models.py` — `LadrcConfig` L74–101: add `u_track_max: float = 100.0`; thread through `with_omega_c`.
- `apps/hvac/config.py` — `_parse_ladrc` L73–93: read optional `u_track_max` (default 100); keep required `b0`/`omega_o`/`omega_c`/bounds/`tune`.
- `apps/apps.yaml.example` — `ladrc:` L16–26: set `b0: 5.0e-4`, `omega_o: 0.03`; add `u_track_max: 100` + unused-until-guard comment; leave `omega_c: 0.053` with ADR-0003-start comment; leave bounds / tune / zone placeholders.
- `tests/test_ladrc.py` — reuse `_run_thermal_c_ticks` / CAP-5 harness; add CAP-3(b) with example-aligned config (`omega_c=0.053`); do not weaken CAP-5 (`omega_c=0.01`).
- `tests/test_ladrc_tuner.py` — extend parse tests for `u_track_max` default/explicit + `with_omega_c` preserve; add test that loads real `apps/apps.yaml.example` into `parse_config` (strip AppDaemon wrapper / resolve `hvac:` args as existing dual-layout patterns do if any); keep Huang fixtures for ωc-tuner scope.
- `docs/adr/0002-ladrc-critical-zone-control.md` — amend with Hard CAP-4 must-language into existing short prose (L1–5); no integrator recipe.
- `docs/adr/0003-online-ladrc-omega-c-auto-tune.md` — **do not change**.
- Continuity: story 1 (`ticket: 1`) continuous-form ESO done; story 2 (`ticket: 2`) tracking-residue seam done — do not retouch those paths.

## Tasks & Acceptance

**Execution:**
- [x] `apps/hvac/models.py` -- Add `u_track_max` (default 100) + `with_omega_c` -- handoff for entry 4.
- [x] `apps/hvac/config.py` -- Parse optional `u_track_max` (default 100) -- YAML → config.
- [x] `apps/apps.yaml.example` -- Thermal `b0`/`omega_o` + `u_track_max: 100` with guard-handoff comment + `omega_c` ADR-0003-start comment -- CAP-1 operators / party A+Stay.
- [x] `tests/test_ladrc.py` -- CAP-3(b) boundedness on example-aligned defaults under continuous + C -- CAP-3(b).
- [x] `tests/test_ladrc_tuner.py` -- Assert parse default/explicit `u_track_max`, `with_omega_c` preserve, and real `apps.yaml.example` → `b0`/`omega_o`/`u_track_max=100` -- verify wiring.
- [x] `docs/adr/0002-ladrc-critical-zone-control.md` -- CAP-4 Hard must-language (no integrator recipe) -- CAP-4 / party Hard.
- [x] `docs/adr/0003-online-ladrc-omega-c-auto-tune.md` -- Confirm empty diff (no edit) -- CAP-4.

**Acceptance Criteria:**
- Given example-aligned gains (`b0=5e-4`, `omega_o=0.03`, `omega_c=0.053`) + continuous-form + C known-input + locked scenario, when `N=80` ticks run, then finite `u_track`/`z` and every tick `|u_track|<100` (ticket “tens” bar = CAP-5 `<100`).
- Given real `apps/apps.yaml.example` loaded through `parse_config`, when parsed, then `b0`/`omega_o` match CAP-3(b) and `u_track_max=100`.
- Given `parse_config` without `u_track_max`, when parsed, then `ladrc.u_track_max == 100.0`.
- Given a `LadrcConfig` with any `u_track_max`, when `with_omega_c(x)` runs, then `u_track_max` is unchanged.
- Given ADR 0002 after the change, when read, then it uses must / must not for exp_map@dt=60 failure, continuous-form ESO, C known-input `(command − u_ff)`, Huang `b0`/`ωo` on this plant, and house calibration — without an integrator recipe.
- Given `apps.yaml.example`, when read, then `omega_c` and `u_track_max` carry the party-required comments (tune-start vs CAP-5; unused until guard).
- Given ADR 0003, when `git diff` runs on that file, then empty (ωc-only).

## Implementation Notes

- CAP-3(b) passed on locked example-aligned gains (`b0=5e-4`, `omega_o=0.03`, `omega_c=0.053`); no b0/ωo nudge required.
- `u_track_max` is config-only in this story; blow-up guard wiring remains entry 4.

## Plan Change Log

- 2026-10-16 party (A / Stay / Hard): keep example `omega_c=0.053` with tune-start comment; keep `u_track_max` in 1.3 with unused-until-guard comment; ADR 0002 must-language, no integrator recipe.
- 2026-10-16 plan review patches: tens⇒`<100` CAP-5 bar; `with_omega_c` preserve AC; nudge b0/ωo only (freeze example ωc); real `apps.yaml.example` parse test; ADR 0002 must-language check in Verification.

## Review Triage Log

- 2026-10-16 plan-review: high=0 medium=4 low=2 false=0 maybe-false=0 — patched all medium + ADR 0002 verify low; token-trim low deferred.

## Design Notes

```text
Example (retune) — party A + Stay:
  b0: 5.0e-4
  omega_o: 0.03
  omega_c: 0.053   # starting point for online ωc tune (ADR 0003); not CAP-5 test value
  u_track_max: 100 # magnitude guard (°C); not enforced until blow-up recovery

CAP-3(b) vs CAP-5:
  same harness / C path; CAP-5 keeps omega_c=0.01;
  CAP-3(b) uses example omega_c=0.053.

ADR 0002 Hard (must-language, no Euler/substep recipe).
```

Field name `u_track_max` matches `setpoint_max` / `omega_c_max` style. Guard consumption is entry 4 only.

## Verification

**Commands:**
- `uv run pytest tests/test_ladrc.py tests/test_ladrc_tuner.py -q` -- CAP-3(b) + parse/`u_track_max`/`with_omega_c`/example file; CAP-5 still green
- `uv run ruff check apps/hvac/models.py apps/hvac/config.py tests/test_ladrc.py tests/test_ladrc_tuner.py` -- clean
- `git diff -- docs/adr/0003-online-ladrc-omega-c-auto-tune.md` -- empty
- Manual/rg on `docs/adr/0002-ladrc-critical-zone-control.md` -- must/must-not language for exp_map, continuous-form, `(command − u_ff)`, Huang, house calibration; no integrator recipe
