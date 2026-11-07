---
epic: epic-fix-ladrc-blow-up
date: 2026-10-16T20:00:36+00:00
verdict: accepted
criteria: declared
headless: false
---

# Retrospective: epic-fix-ladrc-blow-up

## Epic summary

**Epic:** `epic-fix-ladrc-blow-up` — Fix LADRC u_track blow-up  
**Initiative:** `initiative-fix-ladrc-blow-up`  
**Board epic status:** `done` (closed AI-8, 2026-10-17; was `in-progress` at retro time)  
**Going-in concerns:** none (user: без приоритетов)  
**Pending / built-only tickets:** none — all five `status: done` / `state: done`

| Ref | Title | Status | Covers | Plan baseline | Diff range |
|-----|-------|--------|--------|---------------|------------|
| 1.1 | Continuous-form ESO in LadrcState | done | CAP-5, CAP-3 | `a3b10592` | `a3b10592..42dfd834` |
| 1.2 | Tracking-residue known input in hvac_app | done | CAP-1 | `42dfd834` | `42dfd834..8048e80` |
| 1.3 | Retune defaults, u_track_max config, ADR amend | done | CAP-1, CAP-3, CAP-4 | `8048e80` | `8048e80..a4c0a19` |
| 1.4 | Blow-up guard in hvac_app | done | CAP-2, CAP-3 | `a4c0a19` | `a4c0a19..039c8e5` |
| 1.5 | Refactor sweep | done | — | `039c8e5` | `039c8e5..31d7f9d` (inferred end = HEAD / PR #28 merge) |

**Done when (declared in epic file):** continuous-form + thermal defaults + C known-input keep `|u_track|` in tens of °C; guard → FF-only + reset + WARNING; pytest fails old path / passes fixed; ADR 0002 amended, ADR 0003 ωc-only unchanged.

### Evidence inventory

| Artifact | Available? | Path / note |
|----------|------------|-------------|
| Epic file | yes | `epic-fix-ladrc-blow-up.md` (Done when present → criteria **declared**) |
| Initiative Requirements | yes | parent `initiative-fix-ladrc-blow-up.md` CAP-1..CAP-5 |
| Spec | yes | `spec-fix-ladrc-blow-up/spec-fix-ladrc-blow-up.md` |
| Entries (`find`) | yes | refs 1.1–1.5; all `story_file: null` (no refined story files) |
| Plans | yes | five `*-plan.md` with baselines and `status: done` |
| Diff ranges + `git_evidence.py` | yes | five distinct ranges (table above); epic-wide `a3b10592..31d7f9d`: 32 commits, `merge_count=8` / `merges_measured=7` (one merge unmeasured); 1.2 range also `3/2` |
| Previous retrospective | **no** | only epic in initiative |
| Session logs | **narrowed** | walkthroughs + party memlog used; raw Cursor agent JSONL not treated as structured process logs → process-why analysis limited |
| Walkthroughs | yes | pr-22, pr-24, pr-26, 18e21d1, pr-28 |
| Deferred work | cleared | initiative `deferred-work.md` — Huang+absolute CAP-3a shipped AI-3 (2026-10-17) |
| Architecture / PRD folders | **no** | spec + ADR used instead |

**Code churn highlights (non-merge `files`, epic-wide):** `tests/test_hvac_app.py` +346/−7; `apps/hvac/hvac_app.py` +145/−11 (file now 326 LOC); `tests/test_ladrc.py` +130/−12; `apps/hvac/ladrc.py` small net (continuous-form rewrite).

**`bmad-review`:** staged `/tmp/epic-fix-ladrc-blow-up.diff` (apps/tests/docs); lenses `adversarial`, `edge-case-hunter`, `verification-gap`. Findings below re-checked against primary sources before routing.

## Findings

Dispositions: **fix now** / **defer** / **accept**. Each finding lists source then disposition.

### Aggregate views

#### Architecture delta

- **F-A1 — Layering stayed clean.** Production deps remain `hvac_app` → `{ladrc, config, coordinator, feedforward, tuner, models}`; no new import cycles. Guard / residue seams live in `hvac_app` (epic Boundary / Notes).  
  **Source:** import graph of `apps/hvac/*.py` (2026-10-16); epic Boundaries.  
  **Disposition:** accept (positive).

#### Duplication map

- **F-A2 — No cross-ticket duplicate solvers.** Residue advance is one helper (`advance_with_tracking_residue`); guard is one seam (`guard_u_track`); latch hygiene is one helper (`latch_after_zone_change`).  
  **Source:** `apps/hvac/hvac_app.py:24–109`; ranges 1.2 / 1.4 / 1.5.  
  **Disposition:** accept (positive).

#### God-class / size growth

- **F-A3 — `hvac_app.py` grew materially but remains a single AppDaemon entrypoint (~326 LOC).** Highest production churn in epic (`+145/−11`); not a multi-thousand-line god class. Tests absorbed most lines (`test_hvac_app.py` +346).  
  **Source:** `git_evidence.py` epic-wide `files`; `wc -l apps/hvac/hvac_app.py`.  
  **Disposition:** accept — watch if more control policy lands in the same file.

#### Pattern divergence

- **F-A4 — Inspect/`getsource` locks for `control_tick` wiring** (residue call presence, guard-after-compute, warn-before-write) were chosen deliberately over Hass doubles.  
  **Source:** `tests/test_hvac_app.py` (e.g. residue / guard order / warn-before-write); plans 1.2–1.5.  
  **Disposition:** accept for this epic; note verification-gap F-V3 that inspect still misses `should_warn` / `latch_out`.

#### Spec-to-implementation reconciliation

- **F-S1 — Done when #3 / CAP-3 “Huang defaults” fail-lock was only partially delivered (fixed AI-3).** Epic Done when #3 says the suite fails on Huang defaults; `deferred-work.md` had deferred Huang+absolute CAP-3a. Exp_map+thermal diverge was already locked (`test_cap5_exp_map_thermal_c_diverges`). **AI-3 (2026-10-17):** shipped `test_cap3a_huang_absolute_exp_map_diverges`; deferred-work cleared. Huang numbers remain adversarial fixtures (`_default_config`).  
  **Source:** `epic-fix-ladrc-blow-up.md:38`; `tests/test_ladrc.py` CAP-3a + CAP-5; initiative `deferred-work.md` (empty).  
  **Disposition:** fix now (done) — ship Huang diverge test.  
  **Process lesson:** keep Done when in sync when CAP halves are deferred mid-epic.

- **F-S2 — tickets.toml entry 5 `verify` still claims “no behavior change” while the approved plan intentionally clears `_blow_up_latch` on Critical Zone change.** Plan and walkthrough-pr-28 correctly frame cleanup + latch hygiene.  
  **Source:** `tickets.toml` entry 5 `verify`; `story-refactor-sweep-plan.md:23–35`; `walkthrough-pr-28.md:20–22`.  
  **Disposition:** fix now (docs/board hygiene) — update entry 5 `verify` / notes to match Decision A.  
  **Process lesson:** when plan Intent overrides the entry `verify`, amend the entry in the same session.

- **F-S3 — Cross-ticket interaction: example `b0`/`ωc` × `u_track_max=100` trips the guard on routine under-temperature, not only numerical blow-up.** After zone reset, `u_track = ωc·e/b0`. With example `ωc=0.053`, `b0=5e-4`: `|e|≳0.94°C` → `|u_track|>100`. Reproduced: `e=2` → `u_track=212` (trips). CAP-5/CAP-3(b) multi-tick locks use `T_r−y=0.2°C` and stay in tens (`~21–36`). Done when #1’s “tens of °C” is true for that locked scenario, not for cold Critical Zone entry under shipped example gains.  
  **Source:** `apps/apps.yaml.example` ladrc block; `apps/hvac/models.py` `kp→omega_c`; `LadrcState.compute_tracking`; PYTHONPATH=apps reproduction 2026-10-16; `tests/test_ladrc.py:8–10,192–200`.  
  **Disposition:** fix now (proposed remediation — calibration/threshold joint story; not auto-applied).  
  **Process lesson:** gains story (1.3) and guard threshold (1.3→1.4) need a joint AC with `|e|≥1°C` cold-start, not only `e≈0.2` multi-tick.

- **F-S4 — ADR 0002 / 0003 and continuous-form + C known-input match as-built.** ADR 0002 carries exp_map/`dt=60`, continuous-form, C known-input, Huang forbidden, house calibration; `git diff` ADR 0003 over epic range is empty (0 bytes).  
  **Source:** `docs/adr/0002-ladrc-critical-zone-control.md:7–9`; `git diff a3b10592..31d7f9d -- docs/adr/0003-…` → empty.  
  **Disposition:** accept (Done when #4 met).

- **F-S5 — Optional refuse-to-advance after guard trip was in epic Notes scope but rejected in the guard plan (decision B: advance after reset).** Not a silent drop — explicit Never in plan.  
  **Source:** `epic-fix-ladrc-blow-up.md:57`; `story-blow-up-guard-in-hvac-app-plan.md:40`.  
  **Disposition:** accept as documented deviation.

### Diff-scope review (`bmad-review`)

#### Adversarial (re-verified subset)

- **F-R1 (=F-S3)** — Example gains × `u_track_max` soft kill-switch for `|e|≳1°C`. **Disposition:** fix now (proposed).  
- **F-R2 — `commit_omega_c` can still run on a trip tick** after guard reset: `maybe_adapt` uses pre-guard `tracking_error`; commit is after successful write with no `if not guard.tripped` gate.  
  **Source:** `apps/hvac/hvac_app.py:162–218`.  
  **Disposition:** fix now (done AI-5) — skip `commit_omega_c` when `guard.tripped`.  
- **F-R3 — Documented `omega_o` band ~0.01–0.05 includes unstable Euler points at `dt=60`, `n=2`.** `|1−2·h·ωo|` at `ωo=0.05` = 2 > 1; comment in `ladrc.py` documents thermal `ωo=0.03` needs 2 substeps.  
  **Source:** `docs/house-calibration.md:50–51`; `apps/hvac/ladrc.py:9–11,55–61`; stability calc 2026-10-16.  
  **Disposition:** fix now (docs / band / substep policy — proposed).  
- **F-R4 — Guard resets ESO + sets latch before `_write_setpoint`; write failure returns without advance** → observer wiped, plant may keep prior SWT.  
  **Source:** `apps/hvac/hvac_app.py:186–208`.  
  **Disposition:** fix now (done AI-6) — reset-after-success: `guard_u_track` pure detect; `control_tick` resets ESO only after successful write, then advance.  
- **F-R5 — On trip, known input is still `(clamp(u_ff)−u_ff)`, nonzero when `u_ff` outside plant clamps.**  
  **Source:** `guard_u_track` + `advance_with_tracking_residue`; `hvac_app.py:64–66,210–216`.  
  **Disposition:** defer (also F-V2 test gap).  
- **F-R6 — `u_track_max` parse has no positivity/finiteness check.**  
  **Source:** `apps/hvac/config.py` `_parse_ladrc`.  
  **Disposition:** fix now (done AI-7) — reject non-finite / ≤0.  
- **F-R7 — Huang-scale fixtures remain default in unit helpers while ADR forbids them on the plant.**  
  **Source:** `tests/test_ladrc.py:18–32`; ADR 0002.  
  **Disposition:** defer (test hygiene; linked to F-S1).  
- **F-R8 — Fixed `_ESO_EULER_SUBSTEPS=2` does not scale with `dt`/`ωo`.** `dt=120`, `ωo=0.03` unstable.  
  **Source:** `ladrc.py:11`; stability calc.  
  **Disposition:** defer (epic Non-goal: not changing `control_interval` as the fix; still a footgun).  
- Other adversarial items (None→zone latch preserve, `|u_track|==max` exclusive, opaque `u_applied` name): **accept** — match approved Matrix / intentional seams.

#### Edge-case hunter

Overlaps F-R2, F-R4, F-R6, F-R8 — same dispositions; no additional unique finding after re-check.

#### Verification gap

- **F-V1 (=F-S1)** — Huang diverge lock missing. **Disposition:** fix now (done AI-3).  
- **F-V2 — Trip path never tested with `u_ff` outside `[setpoint_min, setpoint_max]`.** Trip tests use in-band `u_ff` and assert `command==u_ff`.  
  **Source:** `tests/test_hvac_app.py` guard trip tests; `guard_u_track` clamp on trip.  
  **Disposition:** fix now (done AI-7) — `test_guard_trip_clamps_out_of_band_uff`.  
- **F-V3 — `control_tick` inspect locks do not assert `if guard.should_warn` or `self._blow_up_latch = guard.latch_out`.** Once-per-episode Floor is unit-tested on the seam, not the call site.  
  **Source:** `tests/test_hvac_app.py` vs `hvac_app.py` warn/latch wiring.  
  **Disposition:** fix now (done AI-7) — `test_control_tick_wires_should_warn_and_latch_out`.  
- **F-V4 — `test_hvac_app_config_matches_cap5_thermal_band` asserts helper constants against themselves.** Real example lock is `test_parse_apps_yaml_example`.  
  **Source:** `tests/test_hvac_app.py`; `tests/test_ladrc_tuner.py`.  
  **Disposition:** fix now (done AI-7) — deleted tautological helper test.

## Behavior verification

| Exercise | Result |
|----------|--------|
| `uv run pytest` on `test_ladrc.py`, `test_hvac_app.py`, `test_ladrc_tuner.py` | **47 passed** (2026-10-16) |
| Cold-start / `|e|≥1` under example gains | Reproduced outside pytest: `u_track=212` trips (`PYTHONPATH=apps`) — informs F-S3 |
| Live AppDaemon / Exclusive Session / plant write | **Not exercised** — Exclusive Session not opened; runtime behavior beyond unit seams **never checked** |

Passing unit tests do not substitute for a live heating-demand run under Plant Management.

## Team discussion (Phase 3)

Ran via `bmad-party-mode` (`product-team`, subagent rounds) over sourced Phase 2 findings. Room pressure on **AI-1 as product contract**, not a leftover bug. **Human decision (2026-10-17):** choose **тепло** — under example defaults, comfort tracking wins; guard must not soft-kill routine `|e|≳1°C` cold start. User then asked **оба, подбери**. Party proposed package A; **human CONFIRMED (2026-10-17):** `omega_c=0.03`, `b0=5e-4` unchanged, `u_track_max=250`. Matrix: e≤3 no-trip, e=5 may trip. AC: e=2 no-trip under example; non-finite always trips; WARN «blow-up» only on real trip. Implementation still proposed (AI-1) — not applied by this retro. F-S2/AI-4 kept as cheap separate hygiene. Did not change machine verdict (`accepted-with-open-items`).

## Previous-retro follow-through

No previous retrospective file in this initiative (only epic). Nothing to follow through on — missing prior file, not “no outstanding items.”

## Action items

Proposed only — not applied by this retro. Owners are suggestions.

| ID | Item | Owner | From |
|----|------|-------|------|
| AI-1 | **Done (2026-10-17):** package A in example/defaults/docs + tests; live `apps/apps.yaml` synced (was Huang `b0=2.8`/`ωo=19.49` → thermal `5e-4`/`0.03`, `ωc=0.03`, `u_track_max=250`; entity IDs untouched) | — | F-S3, F-R1 |
| AI-2 | **Done (docs path, 2026-10-17):** house-calibration replaces ~0.01…0.05 with Euler-stable band (`ωo` below ≈0.033 at `dt=60`/`n=2`); notes `control_interval` footgun. Dynamic substeps from `ωo·dt` left for a future story if needed | — | F-R3 |
| AI-3 | **Done (2026-10-17):** shipped `test_cap3a_huang_absolute_exp_map_diverges` (Huang `b0=2.8`/`ωo=19.49` + absolute SWT on frozen exp_map); cleared initiative `deferred-work.md`; Done when #3 Huang fail-lock met | — | F-S1, F-V1 |
| AI-4 | **Done (2026-10-17):** `tickets.toml` entry 5 description/verify/notes aligned with Decision A latch hygiene (no longer claims “no behavior change”) | — | F-S2 |
| AI-5 | **Done (2026-10-17):** `commit_omega_c` gated by `not guard.tripped`; inspect lock in `test_hvac_app.py` | — | F-R2 |
| AI-6 | **Done (2026-10-17):** reset-after-success — `guard_u_track` no longer mutates ESO; `control_tick` resets after successful write then advances; seam + inspect locks | — | F-R4 |
| AI-7 | **Done (2026-10-17):** out-of-band `u_ff` trip clamp test; `should_warn`/`latch_out` inspect lock; deleted tautological CAP-5 helper test; `u_track_max` finite-positive parse validation | — | F-V2–V4, F-R6 |
| AI-8 | **Done (2026-10-17):** epic `status: done`; closure against Done when #1–#4 + all stories done; retro verdict → `accepted` | — | workflow |

**Process lessons (no code change):** keep entry `verify` in sync when plan Intent moves; joint-test gain×threshold across ticket boundaries; when deferring a Done when half, amend Done when in the same change.

## Acceptance verdict

**Machine verdict at retro: `accepted-with-open-items` → human closed epic AI-8 (2026-10-17): `accepted`**  
**Criteria: declared** (epic Done when)  
**Unfinished tickets:** none. Open items AI-1…AI-7 all done before close.

| Done when | Evidence | Met? |
|-----------|----------|------|
| 1. Continuous-form + thermal/example path keeps `|u_track|` in tens over multi-tick `y≈21` | CAP-5/CAP-3(b) bounded tests + package A cold-start AC (AI-1) | **Yes** |
| 2. Poisoned/exploded `u_track` → FF-only + reset + WARNING; recover without zone/idle/plant-off | Guard seam + latch; reset-after-success (AI-6); skip ωc commit on trip (AI-5) | **Yes** (unit) |
| 3. Suite fails old path / passes fixed | exp_map thermal+C + Huang+absolute diverge + continuous bounded + guard (AI-3, AI-7) | **Yes** |
| 4. ADR 0002 amended; ADR 0003 ωc-only unchanged | ADR 0002 text; empty ADR 0003 diff | **Yes** |

Initiative `initiative-fix-ladrc-blow-up` closed `done` (2026-10-17) with the epic — same single-epic Done when.

## Open questions

1. Should example defaults prioritize “never trip below ~2°C error” or “hard-cap `|u_track|` at 100 even if that means FF-only on cold start”? (AI-1)  
2. If cold-start FF-only is intentional, should WARNING language say “tracking saturated / ff-only mode” rather than “blow-up”? (party / Sally)  
3. Is live Exclusive Session verification required before closing the initiative, given unit-only behavior check?  
4. Keep Huang numbers as adversarial fixtures, or migrate fixtures to thermal-band to stop contradicting ADR prose? (AI-3 / F-R7)

## Assumptions

_Omitted — interactive run; facts recorded where confirmed (Epic summary going-in concerns; finished tickets)._
