---
title: 'Adapted-gain rails and unhealthy RLS fallback'
type: 'feature'
ticket: '2'
created: '2026-11-09'
status: 'built'
baseline_revision: 'a70c7e3e2fb487b85eb2636b5b3abf46f52cb429'
route: 'full'
route_source: 'auto'
risk: 'high'
review: 'quick'
review_source: 'pinned'
lenses_ran: ['quick']
review_loop_iteration: 1
context:
  - _bmad-output/initiative-pid/tickets/epic-rls-pid-retune/rls-adaptive-algorithm.md
  - docs/house-calibration.md
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Tracer adaptive path can publish any finite IMC gains and keeps last-good on IMC failure; there are no YAML rails, no unhealthy→fixed fallback, and no WARNING for legacy per-second-scale `pid.ki` (`0 < ki < 1`).

**Approach:** Add YAML min/max rails for adapted Kp/Ki; when RLS is unhealthy or a proposed adapted gain is out of band, keep YAML fixed `kp`/`ki` in force. At parse, detect legacy-scale `pid.ki` and log one WARNING (still parse). Adaptive-off fallback stays entry 1 (tracer RLS adaptive).

**Done when:** adaptive-on commissions all four rails; unhealthy/out-of-band latches demand onto YAML fixed until healthy in-band publish; legacy `ki` WARNING once; matrix + pytest/ruff green.

## Boundaries & Constraints

**Always:**
- Demand SWT law, gates, tick-only RLS step, `boiler_water` y, and clear/`y_prev` bookkeeping from entry 1 stay unchanged except how adapted gains are accepted and selected for `_gains_for_demand`.
- Unhealthy = `rls_step` returns False **or** after a True step `imc_gains` is `None` **or** the mapped kp/ki are not both finite. Out-of-band = both finite and outside inclusive rails.
- Latch evaluation order (one reason per tick): `rls_noop` (False) → `imc_none` (None or non-finite) → `out_of_band` (finite outside rails). Mutually exclusive.
- Out-of-band or unhealthy → demand uses YAML fixed `kp`/`ki`. Park prior `adapted_*` in memory (no-op if already None); `_gains_for_demand` ignores them until a later healthy in-band publish (do not clear park; do not apply parked or rejected values). Fallback latch survives ephemeral clear (idle / plant-off / no-valid-zones / weights-unusable) with the same lifetime as parked `adapted_*`; only a later healthy in-band publish clears the latch (not clear paths). Latch is in-memory only: App initialize starts with latch False.
- After `rls_step` returns True, θ/P stay committed even if IMC is None/non-finite or out-of-band; only `adapted_*` publish is skipped. False leaves θ/P unchanged.
- Skip-step paths (non-finite/unreadable `boiler_water` y, `plant_ok` False, missing priors / seed tick) do **not** enter or refresh the latch; `_gains_for_demand` still honors an already-set latch (YAML fixed). Entry-1 y WARNING and seed/`y_prev` rules unchanged.
- Rails keys `pid.kp_min` / `kp_max` / `ki_min` / `ki_max`: all four required when `adaptive: true` (ConfigError if any missing); may omit when adaptive off. Each rail ≥0 and min≤max (**equal allowed**). In-band iff `kp_min <= kp <= kp_max` and `ki_min <= ki <= ki_max` (inclusive; plain float compare). Rails constrain adapted proposals only; YAML fixed `kp`/`ki` stay ≥0 as today and are **not** checked against rails.
- Explicit `pid.ki` with `0 < ki < 1` → one WARNING (legacy-scale); config still parses (not ConfigError); no auto ×3600. Flag lives on `PidConfig`; log once from App `initialize`.
- Weather/FF/Outdoor stay absent; JSON persistence stays entry 3; RLS domain docs stay entry 4. `boiler_water` required when adaptive — entry 1, unchanged.

**Never:**
- Changing Heating Demand, Exclusive Session, Kd≠0, air-`y`, or restoring outdoor/FF.
- Treating adaptive-off as this story’s work (already entry 1).
- Auto-migrating / rewriting YAML `ki` values.
- Persisting RLS θ/P or the fallback latch to disk.
- Defaulting omitted rail keys when adaptive is on.
- Entering latch solely because a tick skipped the RLS step (y/plant/priors).

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Adaptive on, IMC valid finite, gains inside rails (inclusive) | Demand tick after True step | Publish adapted; clear latch; demand uses adapted kp/ki | No error expected |
| Adaptive on, IMC valid finite, kp or ki outside rails | Demand tick after True step | θ/P kept; do not overwrite adapted with proposal; latch; YAML fixed in force | WARNING once on latch enter (`out_of_band` + proposed + rails); silent while same reason; re-WARN once if reason changes |
| Adaptive on, `rls_step` False | Demand tick after step attempt | θ/P unchanged; park adapted; latch; YAML fixed | WARNING once (`rls_noop`); silent while latched |
| Adaptive on, True step then IMC None or non-finite | Demand tick after step | θ/P kept; do not publish adapted; latch; YAML fixed | WARNING once (`imc_none`) |
| Adaptive on, skip step (y missing / plant_ok False / no priors) | Demand tick | No new latch; gains = YAML if latched else adapted-if-any else YAML; entry-1 y WARNING if y missing | — |
| Adaptive off | Demand tick | YAML fixed; no RLS step (unchanged) | — |
| Adaptive on, missing any rail key | Parse | ConfigError | Fail closed |
| Adaptive on, rail min>max or rail <0 | Parse | ConfigError | Fail closed |
| Adaptive on, rail min==max | Parse | OK (single-point band) | — |
| Explicit `0 < ki < 1` | Parse / initialize | Config OK; one legacy-scale ki WARNING from initialize | Not ConfigError |
| Healthy in-band after parked fallback | Later demand tick | Publish adapted; clear latch; demand uses adapted again | No required WARNING on clear |
| Latched, then ephemeral clear, then demand before healthy publish | Clear then demand tick(s) | Latch still set; YAML fixed; parked ignored; seed tick still no step | — |
| App initialize / process restart | Cold start | Latch False; in-memory park empty until first publish | — |

## Decisions (2026-11-09)

- OQ1 **B** — unhealthy = `rls_step` False **or** IMC None/non-finite after a True step.
- OQ2 **B** — park `adapted_*`; YAML in force until next healthy in-band publish.
- OQ2b **A** — fallback latch survives ephemeral clear; only healthy in-band publish clears it.
- OQ3 **C** — four rails required when adaptive on; no defaults.
- OQ4 **B** — WARNING when explicit `0 < ki < 1`.
- OQ5 **1** — `rls_step` → `bool`; mutate θ/P only on success; no pre/post compare.
- OQ6 **W1+** — WARNING once on latch enter; silent while same reason; **re-WARN once when latch reason changes**; no per-tick spam; healthy publish clears latch without required WARNING.
- OQ7 **R1** — rails on adapted only; fixed may sit outside rails (no parse INFO required).
- OQ8 **P1** — latch WARNING = reason + numbers; no θ/P/φ dump.
- OQ9 **inclusive** — in-band iff min≤gain≤max for kp and ki.
- OQ10 **keep θ/P** — True step commits θ/P even when gains rejected (None/non-finite/OOB).
- OQ11 **no latch on skip** — y/plant/priors skip does not enter latch; existing latch still forces YAML.
- OQ12 **min==max OK** — zero-width band allowed; min>max ConfigError.
- OQ13 **PidConfig flag** — `legacy_ki_warning` on `PidConfig`; one initialize WARNING.
- OQ14 **helper in rls.py** — `gains_within_rails(...)` pure helper; `hvac_app` calls after IMC.

</frozen-after-approval>

## Code Map

- `apps/ha_smart_hvac/models.py` — `PidConfig` rail fields `kp_min`/`kp_max`/`ki_min`/`ki_max` as `float | None`; `legacy_ki_warning: bool` on `PidConfig` (not `HvacConfig`).
- `apps/ha_smart_hvac/config.py` — rail keys in `_PID_KEYS`; adaptive requires four finite ≥0 with min≤max (equal OK); do not require fixed inside rails; set `legacy_ki_warning` when explicit ki in `(0, 1)`; keep negative kp/ki ConfigError.
- `apps/ha_smart_hvac/hvac_app.py` — fallback latch + reason; `_maybe_rls_step` uses bool step, IMC, rails; `_gains_for_demand` returns YAML while latched; skip-step does not latch; initialize logs legacy ki WARNING once; latch starts False.
- `apps/ha_smart_hvac/rls.py` — `rls_step` → `bool`; `gains_within_rails(kp, ki, kp_min, kp_max, ki_min, ki_max) -> bool`; keep math; no JSON.
- `apps.yaml.example` — comment that adaptive true needs all four rails + `boiler_water`; leave `adaptive: false`.
- `docs/house-calibration.md` — short note: adapted rails required when adaptive; WARNING on `0 < ki < 1`. No ADR/CONTEXT/AGENTS.
- `tests/test_config.py`, `tests/test_hvac_app.py`, `tests/test_rls.py` — matrix rows + missing-rail ConfigError + legacy ki WARNING; **replace** entry-1 `test_adaptive_imc_invalid_keeps_last_good_gains` with yaml-fixed-on-invalid/OOB; keep clear/`y_prev`/last-u behaviors.

## Design Notes

- This story overrides tracer last-good-on-IMC-invalid: while latched, demand uses YAML fixed even if parked `adapted_*` remain.
- Legacy WARNING is operator-only; parsed `ki` stays the YAML number.
- Reason codes: `rls_noop` | `imc_none` | `out_of_band` (OQ8 numbers on OOB).

## Tasks & Acceptance

**Execution:**
- [x] `models.py` + `config.py` — required rails when adaptive + `legacy_ki_warning` on `PidConfig`.
- [x] `rls.py` + `hvac_app.py` — bool step, `gains_within_rails`, park/latch → YAML fixed, reason WARN policy.
- [x] `apps.yaml.example` + `docs/house-calibration.md` — document required rails + legacy WARNING.
- [x] Tests — I/O matrix; missing-rail ConfigError; replace last-good IMC-invalid test; latch-survives-clear seed tick uses YAML.
- [x] If entry-1 epic verify text still says last-good on IMC-invalid, update that verify note to point at this story’s fallback (same change set or follow-up before epic close).

**Acceptance Criteria:**
- Given adaptive on and finite IMC kp/ki outside inclusive rails, when a demand tick steps RLS True, then demand SWT uses YAML fixed kp/ki, θ/P stay updated, parked adapted is not applied, and WARNING logs once on latch enter (`out_of_band` + numbers).
- Given adaptive on and `rls_step` returns False, when that demand tick runs, then demand SWT uses YAML fixed, θ/P unchanged, WARNING once (`rls_noop`).
- Given adaptive on and True step then IMC None/non-finite, when that demand tick runs, then demand SWT uses YAML fixed, θ/P stay committed, WARNING once (`imc_none`).
- Given adaptive on and a skip-step tick (y missing / plant_ok False / seed), when latch is already set, then demand SWT uses YAML fixed and latch reason is unchanged (no new WARNING).
- Given adaptive on and any of `kp_min`/`kp_max`/`ki_min`/`ki_max` missing or min>max or rail <0, when config is parsed, then ConfigError is raised.
- Given explicit `pid.ki` with `0 < ki < 1`, when App initializes, then one WARNING is logged and parse still succeeds.
- Given adaptive on after a parked fallback, when a later tick publishes healthy in-band IMC gains, then demand uses those adapted gains and latch clears.
- Given adaptive on and fallback latched, when an ephemeral clear runs and demand later returns before a healthy in-band publish (including seed tick), then demand SWT still uses YAML fixed kp/ki.
- Given latch reason changes while still latched (e.g. `rls_noop` → `out_of_band`), when that tick runs, then one additional WARNING is logged for the new reason.
- Given `pid.adaptive` false/omitted, when a demand tick runs, then behavior stays YAML fixed with no RLS step.
- Given you run `uv run pytest` and `uv run ruff check`, then both succeed.

## Plan Change Log

- 2026-11-09 party: OQ2b A, OQ5 bool step, OQ6 W1, OQ7 R1, OQ8 P1.
- 2026-11-09 review triage: OQ6→W1+ reason-change re-WARN; OQ9–OQ14; matrix/AC expanded; deferred hysteresis / fixed-outside-rails INFO / structure mega-condense.

## Review Triage Log

**Must-fix (locked into plan):**
- Inclusive rail bounds (OQ9).
- Non-finite IMC → `imc_none` unhealthy (OQ1 refine).
- θ/P keep after True step when gains rejected (OQ10).
- No latch on skip-step; existing latch still forces YAML (OQ11).
- Reason-change re-WARN required once (OQ6 W1+).
- `min==max` OK (OQ12); `legacy_ki_warning` on `PidConfig` (OQ13); `gains_within_rails` in `rls.py` (OQ14).
- Replace entry-1 last-good IMC-invalid test; seed-tick YAML assert under latch.
- Latch False on initialize (not persisted).
- Mutually exclusive reason order documented.

**Deferred / wontfix this story:**
- Rail-edge float rounding/ndigits — plain inclusive float compare.
- Hysteresis/dwell before clearing latch — W1+ sufficient for ops noise.
- Parse INFO when fixed sits outside rails — OQ7 R1 intentional.
- Structure mega-MERGE (Decisions/Design Notes/AC dedupe) — clarity nits applied; full reshuffle not required for build.
- Entry-3 restart θ/P reload semantics — owned by persistence story; this story only: latch not on disk.
- Runtime mid-flight YAML reload of rails — AppDaemon re-init; rails frozen at initialize.

**Code review (quick, 2026-11-09):**
- `medium` → patch — `tests/test_hvac_app.py` `_count_rls_steps` returns `True` without committing θ/P; any can_step call (e.g. second tick of `test_adaptive_after_clear_seed_then_last_good_gains`) takes the success path on default θ→`imc_none` latch. Evidence: stub body returns True only; `imc_gains(0,0,ts)` is None. **Resolved** — `_count_rls_steps` delegates to real `rls_step`.
- `medium` → patch — True+reject tests (`test_adaptive_imc_invalid_latches_yaml_fixed`, `test_adaptive_out_of_band_latches_yaml_fixed`, `test_adaptive_nonfinite_imc_latches_imc_none`) do not assert θ/P stayed committed after True step; OQ10/AC θ/P-keep clause unverified. Evidence: no before/after θ/P asserts; nonfinite stubs True with no mutation. **Resolved** — True+reject tests assert θ/P before/after.

## Verification

**Commands:**
- `uv run pytest` -- expected: all tests pass
- `uv run ruff check` -- expected: clean

## Code Review

### 2026-11-09

**Code review complete.** 0 `decision-needed`, 9 `patch`, 1 `defer`, 8 rejected.

- [x] [Review][Patch] ki_min > ki_max ConfigError has no test twin of kp [`tests/test_config.py:534`]
- [x] [Review][Patch] legacy_ki_warning open-interval edges (ki=0, ki=1) unpinned [`apps/ha_smart_hvac/config.py:208`]
- [x] [Review][Patch] Inclusive rail acceptance never hit through `_maybe_rls_step` [`apps/ha_smart_hvac/hvac_app.py:193`]
- [x] [Review][Patch] Skip-step does-not-enter-latch locked only for seed, not plant_ok False / unreadable y [`tests/test_hvac_app.py:1516`]
- [x] [Review][Patch] nonfinite IMC latch test under-asserts latched flag, park, and WARNING [`tests/test_hvac_app.py:1408`]
- [x] [Review][Patch] house-calibration rejected-values understate rail validation when adaptive is false [`docs/house-calibration.md:76`]
- [x] [Review][Patch] Plan Review Triage Log still lists patched medium items as open [`story-adapted-gain-rails-and-unhealthy-rls-fallback-plan.md` Review Triage Log]
- [x] [Review][Patch] Clear-path comment still says last-good, omits latch lifetime [`apps/ha_smart_hvac/hvac_app.py:78`]
- [x] [Review][Patch] after_clear_seed_then_last_good_gains stale name and weak second-tick asserts [`tests/test_hvac_app.py:1575`]
- [x] [Review][Defer] Entry-1 tickets.toml description still says last-good without entry-2 override [`tickets.toml` entry 1] — deferred: fix edits a ticket file

**Rejected**
- R3 Operator docs omit latch behavior — deferred to entry 4 / out of this story plan Tasks scope
- R4 CHANGELOG buries rails — false: CHANGELOG delta is 3.1.0 release only; rails commit does not touch it
- R12 apps.yaml.example rail band guidance — low; speculative house bands add complexity
- R13 Adaptive-off invalid rails underspec — false: fail-closed on present invalid rails is protective
- R14 healthy clear no WARNING assert — low; negative assert rarely worth the noise
- R18 Plan-only latch WARN beyond short intent — false: approved plan owns W1+
- R19 pytest/ruff not in diff — false: gates are outside the patch text
- R21 Latch-protocol vs control-law surface mismatch — false: descriptive observation only
