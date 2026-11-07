---
epic: epic-gate-omega-c-on-saturation
date: 2026-10-17T02:55:28+00:00
verdict: accepted-with-open-items
criteria: declared
headless: false
---

# Retrospective: epic-gate-omega-c-on-saturation

## Epic summary

**Epic:** `epic-gate-omega-c-on-saturation` — Gate ωc on saturation  
**Initiative:** `initiative-gate-omega-c-on-saturation`  
**Board epic status:** `done`  
**Going-in concerns:** none (user: без акцентов)  
**Pending / built-only tickets:** none — all five `status: done` / `state: done`

| Ref | Title | Status | Covers | Plan baseline | Diff range |
|-----|-------|--------|--------|---------------|------------|
| 1.1 | Directional clamp + strict apply | done | CAP-1, CAP-2, CAP-6 | `8ad563af` | `8ad563af..a0557794` |
| 1.2 | Latch decay + skip adapt | done | CAP-4, CAP-6 | `a0557794` | `a0557794..0082f93d` |
| 1.3 | Write-on-change setpoint | done | CAP-3, CAP-6 | `0082f93d` | `0082f93d..fdfc03b4` |
| 1.4 | ADR 0003 + house-calibration | done | CAP-5 | `fdfc03b4` | `fdfc03b4..d4487ca9` |
| 1.5 | Refactor sweep | done | — | `d4487ca9` | `d4487ca9..d021ec8` (inferred end = HEAD / PR #40 wrap-up) |

**Done when (declared in epic file):** CAP-1/2 Hass-free saturated no-ratchet; CAP-3 write-on-change + fail-closed; CAP-4 latched skip-adapt + decay; CAP-5 docs criterion A; CAP-6 pytest green on touched modules.

### Evidence inventory

| Artifact | Available? | Path / note |
|----------|------------|-------------|
| Epic file | yes | `epic-gate-omega-c-on-saturation.md` (Done when present → criteria **declared**) |
| Initiative Requirements | yes | parent initiative CAP-1..CAP-6 (Requirements mirrored on epic) |
| Spec / companions | yes | `spec-gate-omega-c-on-saturation/` (+ control-tick-behaviors, architecture-diagrams) |
| Entries (`find`) | yes | refs 1.1–1.5; all `story_file: null` |
| Plans | yes | five `*-plan.md` with baselines and `status: done` |
| Diff ranges + `git_evidence.py` | yes | five ranges + epic-wide `8ad563af..d021ec8`: 28 commits, `merge_count=11` / `merges_measured=10` (one merge unmeasured); 1.2 range also `3/2` |
| Previous retrospective | yes | sibling initiative `epic-fix-ladrc-blow-up-retrospective.md` (prior epic in product history) |
| Session logs | **narrowed** | walkthroughs pr-31/34/36/39 used; raw Cursor agent JSONL not treated as structured process logs |
| Walkthroughs | yes | pr-31, pr-34, pr-36, pr-39 |
| Deferred work | partial | initiative `deferred-work.md` — Package C framing closed; AI-4/AI-5 still deferred |
| Architecture / PRD folders | **no** | spec companions + ADR used instead |

**Code churn highlights (non-merge `files`, epic-wide apps/tests/docs):** `tests/test_hvac_app.py` +496/−55; `apps/hvac/hvac_app.py` +218/−106 (file 327 → 439 LOC); docs ADR 0003 +4 / house-calibration +2.

**`bmad-review`:** staged `/tmp/epic-gate-omega-c-on-saturation.diff` (apps/tests/docs); lenses adversarial, edge-case-hunter, verification-gap via parallel subagents. Findings re-checked against primary sources before routing.

## Findings

Dispositions: **fix now** / **defer** / **accept**. Each finding lists source then disposition.

### Aggregate views

#### Architecture delta

- **F-A1 — Layering stayed clean.** Production deps remain `hvac_app` → `{ladrc, config, coordinator, feedforward, tuner, models}`; no new import cycles. New seams (`should_apply_omega_c`, latch-decay helpers, sticky latch) live in `hvac_app`.  
  **Source:** import graph of `apps/hvac/*.py` (2026-10-17); epic Boundaries.  
  **Disposition:** accept (positive).

#### Duplication map

- **F-A2 — No cross-ticket duplicate solvers.** Directional gate is one predicate; decay step/band/sticky are one helper cluster; write-on-change is one `_write_setpoint` path. Refactor 1.5 renamed `should_commit_*` → `should_apply_*` and collapsed duplicate track+guard branches.  
  **Source:** `apps/hvac/hvac_app.py:112–161,239–328`; range 1.5 churn net −29 on `hvac_app.py`.  
  **Disposition:** accept (positive).

#### God-class / size growth

- **F-A3 — `hvac_app.py` grew 327 → 439 LOC over the epic** (highest production net +112). Still a single AppDaemon entrypoint, not a multi-thousand-line god class; tests absorbed most lines (+441 net).  
  **Source:** `git_evidence.py` epic `files`; `wc -l` before/after baselines.  
  **Disposition:** accept — watch if more control policy lands in the same file.

#### Pattern divergence

- **F-A4 — CAP-6 locks lean on inspect/`getsource` and Hass-free mirrors** (`_mirror_decay_tick`, saturated ratchet loop) rather than a stubbed `HvacApp.control_tick`. Consistent with prior epic’s pattern, but weak at ticket boundaries (see F-V*).  
  **Source:** `tests/test_hvac_app.py` CAP-1..CAP-6 sections; plans 1.1–1.3 verify text.  
  **Disposition:** accept for this epic’s chosen verify style; process lesson under F-V*.

#### Spec-to-implementation reconciliation

- **F-S1 — CAP-1..CAP-5 as-built match declared Done when at the unit/docs level.** Directional `should_apply_omega_c`, strict re-track on block, write-on-change equality skip, latched skip-adapt + decay helpers, ADR 0003 Guards + house-calibration §5 criterion A.  
  **Source:** `hvac_app.py:112–328,423–439`; `docs/adr/0003-…:15–21`; `docs/house-calibration.md:72`; epic Done when #1–#4.  
  **Disposition:** accept (criteria met).

- **F-S2 — CAP-4 skip-adapt freezes tuner steady; first unlatched tick can re-propose immediately**, undoing decay until directional clamp hits max again. Spec requires skip `maybe_adapt` while latched, not `clear_steady`. Reproduced: warm `_steady_ticks=5` → latch freeze → first unlatched `maybe_adapt` returns upward proposal; after `clear_steady`, first adapt returns `None` (`steady=1`).  
  **Source:** `hvac_app.py:214–225`; `ladrc_tuner.py:39–80`; PYTHONPATH=apps reproduction 2026-10-17.  
  **Disposition:** fix now (proposed remediation — clear steady when `latch_at_start`).  
  **Process lesson:** when a ticket skips a side-effecting call, name which frozen counters are intentional.

- **F-S3 — Initiative inception Notes vs build order.** Parent initiative Description once sketched tracer as directional → write-on-change → latch; epic Notes / tickets.toml order is directional → latch → write → docs → sweep (as built). Not a capability drop.  
  **Source:** `initiative-gate-omega-c-on-saturation.md:37`; `epic-gate-omega-c-on-saturation.md:60`; `tickets.toml` `after` edges.  
  **Disposition:** accept — board order won; keep epic Notes as source of build order.

### Diff-scope review (`bmad-review`)

#### Adversarial (re-verified subset)

- **F-R1 (=F-S2)** — Steady freeze / post-latch rebound. **Disposition:** fix now (proposed).  
- **F-R2 — Trip-edge WARN spam when plant write fails.** `should_warn = tripped and not latch_in`; sticky latch only after successful write (`:293–300`). Fail-write returns before sticky → latch never sticks → every flaky tick re-warns; decay/ESO reset also stall.  
  **Source:** `guard_u_track` `:70–74`; `control_tick` `:283–294`.  
  **Disposition:** fix now (proposed — warn-emitted sticky independent of write success, or latch residue intent separately).  
- **F-R3 — Idle / no-demand ignore `_write_setpoint` failure** while clearing latch/ESO (`:203–207`, `_go_idle` `:352–356`). Demand path aborts (`:293–294`). CAP-3 text covers idle/0 equality skip; fail-closed abort is demand-shaped in as-built.  
  **Source:** `hvac_app.py` as cited; CAP-3 entry verify.  
  **Disposition:** defer — pre-existing idle asymmetry; not required to fail Done when #2 as written for demand.  
- **F-R4 — Write-on-change bare `current == value`.** Spec CAP-3 intentionally uses entity state, not last-written cache. Optimistic HA state can skip retries.  
  **Source:** `hvac_app.py:432–433`; entry 1.3 description.  
  **Disposition:** accept as-is (specified).  
- **F-R5 — Provisional apply gate vs final write-path guard.** Documented intentional: apply decided on provisional; blocked path re-tracks committed ωc without re-eval.  
  **Source:** `hvac_app.py:258–278` comments.  
  **Disposition:** accept.  
- **F-R6 — Gray-band sticky (`0.8·max < |u_track| ≤ max`) still commands full tracking.** CAP-4 is adapt/decay soft-kill, not ff-only.  
  **Source:** `sticky_blow_up_latch`; `guard_u_track` non-trip branch; spec CAP-4.  
  **Disposition:** accept.

#### Edge-case hunter

- **F-E1 (=F-R2)** — Fail-write stalls sticky/decay. Same disposition.  
- **F-E2 — Zone change same tick as `latch_at_start`:** adapt skipped from pre-clear latch, then `latch_after_zone_change` clears. One tick of frozen adapt after zone recovery.  
  **Source:** `hvac_app.py:214–237`.  
  **Disposition:** defer.  
- **F-E3 — Zone clear does not re-stick from high residue alone** (needs trip). Intentional recovery path.  
  **Source:** `latch_after_zone_change`; `sticky_blow_up_latch`.  
  **Disposition:** accept.  
- Other float-epsilon / NaN plant read edges: **defer** (no evidence they break Done when locks; `_read_float` already fail-closes unavailable/unparseable).

#### Verification gap

- **F-V1 — CAP-6 mostly inspect + mirrors, not stubbed `control_tick`.** Source scrapes prove token order; `_mirror_decay_tick` / ratchet loop do not drive adapt → provisional → write-on-change → sticky → decay XOR `apply_proposed`.  
  **Source:** `tests/test_hvac_app.py` CAP sections; F-ADV-7 / F-VG-1..10.  
  **Disposition:** fix now (proposed — one Hass-stubbed multi-tick sequence covering skip-adapt×decay and fail-write trip).  
  **Process lesson:** for shared `control_tick` epics, require at least one integration lock that cannot pass on helpers alone.  
- **F-V2 — Min-side ratchet and relieving commit paths lack end-to-end mirror coverage** (matrix covers predicate only; ratchet only max+upward).  
  **Source:** `test_should_apply_omega_c_matrix` vs `test_saturated_upward_proposal_*`.  
  **Disposition:** defer.  
- **F-V3 — No test for latched-at-start + Critical Zone change in one tick.**  
  **Source:** absence in `test_hvac_app.py`; F-VG-7.  
  **Disposition:** defer (paired with F-E2).

## Behavior verification

| Exercise | Result |
|----------|--------|
| `uv run pytest` on `test_hvac_app.py`, `test_ladrc_tuner.py`, `test_ladrc.py` | **96 passed** (2026-10-17) |
| Steady freeze rebound (PYTHONPATH=apps) | Reproduced: latched skip leaves `_steady_ticks` hot → immediate post-clear proposal — informs F-S2 |
| Live AppDaemon / Exclusive Session / plant write | **Not exercised** — Exclusive Session not opened; runtime behavior beyond unit seams **never checked** |

Passing unit tests do not substitute for a live heating-demand run under Plant Management.

## Team discussion (Phase 3)

Ran via `bmad-party-mode` (`product-team`, session mode) over sourced Phase 2 findings. Room framed open items as recovery-story risk (post-latch ωc rebound, WARN spam) vs test hygiene. **Human decision (2026-10-17):** package **C** — AI-1 `clear_steady` on `latch_at_start` + AI-2 WARN/fail-write hygiene + AI-3 one Hass-stubbed `control_tick` integration lock. Idle fail-closed (AI-4) and min-side/zone×latch tests (AI-5) stay deferred. Did not change machine verdict (`accepted-with-open-items`).

### Package C close-out (2026-10-17)

AI-1 / AI-2 / AI-3 from the table below landed after this retrospective:

| ID | Landed? | Evidence |
|----|---------|----------|
| AI-1 | yes | `hvac_app.py` `clear_steady()` on `latch_at_start`; Hass rebound lock in Package C (`plan-package-c-latch-hygiene`, PR #41) |
| AI-2 | yes | app-level `_blow_up_warned` episode WARN gate in `hvac_app.py`; fail-write does not sticky/decay; companion CAP-4 / WARN episode wording (PR #41) |
| AI-3 | yes | Hass-stubbed `control_tick` locks in Package C + deferred Q5 multi-tick decay persist and equal-value write-on-change side effects (PR #41 / #43) |

Phase 2 Findings dispositions above remain the retro-time snapshot (`fix now` / `defer`); follow-through is this close-out table, not rewritten finding text. ADR 0003 Guards Package C wording is synced separately in `plan-package-c-adr-closeout`.

AI-4 and AI-5 remain deferred backlog. Machine verdict stays `accepted-with-open-items` for those (and live Exclusive Session still unexercised).

## Previous-retro follow-through

Prior file: `_bmad-output/initiative-fix-ladrc-blow-up/tickets/epic-fix-ladrc-blow-up/epic-fix-ladrc-blow-up-retrospective.md`.

| Item | Owner (as spelled) | Landed? | Evidence |
|------|--------------------|---------|----------|
| AI-1 package A (`ωc=0.03`, `b0=5e-4`, `u_track_max=250`) | — | yes | `docs/house-calibration.md:52–56`; `tests/test_ladrc.py` package A tests |
| AI-2 Euler-stable `ωo` band docs | — | yes | `docs/house-calibration.md:51,58` |
| AI-3 Huang CAP-3a diverge test | — | yes | `tests/test_ladrc.py:195` `test_cap3a_huang_absolute_exp_map_diverges` |
| AI-4 tickets.toml entry 5 hygiene | — | yes | prior retro marks done; this epic’s entry 5 is a new story |
| AI-5 skip `commit_omega_c` on trip | — | yes | `hvac_app.py:324–328` commit gated by `apply_proposed` (trip blocks apply) |
| AI-6 reset-after-success | — | yes | `guard_u_track` docstring + `control_tick:302–304` |
| AI-7 parse/tests package | — | yes | `config.py:86–88`; trip/warn inspect locks in `test_hvac_app.py` |
| AI-8 close epic | — | yes | prior epic `status: done`; verdict `accepted` |

Deferred from prior retro (not committed as AI): F-R5 out-of-band known-input on trip, F-R7 Huang fixtures as defaults, F-R8 fixed Euler substeps — **no evidence of landing** (still present as prior-era design); out of this epic’s scope. Recorded as still open from the previous retro’s defer list, not as failures of this epic.

## Action items

Proposed only — not applied by this retro. Owners are suggestions.

| ID | Item | Owner | From |
|----|------|-------|------|
| AI-1 | On `latch_at_start`, call `self._tuner.clear_steady()` (or equivalent) so CAP-4 decay is not immediately undone by a hot steady counter; add a regression that warm-steady → N latched ticks → clear does not propose on the first unlatched tick | Amelia / Package C | F-S2, F-R1 — **closed** (see Package C close-out) |
| AI-2 | Fix trip-edge WARN / latch interaction when `_write_setpoint` fails: preserve once-per-episode warn without claiming plant success; ensure flaky reads do not spam WARNING every 60 s | Amelia / Package C | F-R2, F-E1 — **closed** (see Package C close-out) |
| AI-3 | Add one Hass-stubbed `control_tick` integration lock: latched skip-adapt + decay persist; fail-write trip does not sticky/decay; optional equal-value write-on-change still completes tick side effects | Amelia / Package C | F-V1 — **closed** (see Package C close-out) |
| AI-4 | Defer: idle/`_go_idle` fail-closed symmetry with demand abort | backlog | F-R3 |
| AI-5 | Defer: min-side ratchet + zone-change×latch_at_start tests | backlog | F-V2, F-V3, F-E2 |

**Process lessons (no code change):** when skip-adapt freezes a callee, declare counter policy; for multi-ticket `control_tick` epics, budget one integration test that crosses seams; keep initiative Description tracer sketches from drifting away from `tickets.toml` order.

## Acceptance verdict

**Machine verdict: `accepted-with-open-items`**  
**Criteria: declared** (epic Done when)  
**Unfinished tickets:** none (`pending_tickets` empty).

| Done when | Evidence | Met? |
|-----------|----------|------|
| 1. CAP-1/2 saturated upward no-ratchet; blocked proposal not applied | `should_apply_omega_c` + strict re-track; CAP-6(a)(b) tests; 96 passed | **Yes** (unit) |
| 2. CAP-3 equal skip without abort; unreadable aborts | `_write_setpoint`; CAP-6(c)(d) tests | **Yes** (demand path); idle asymmetry deferred F-R3 |
| 3. CAP-4 latched skip-adapt + decay to band | helpers + mirrors + inspect skip-adapt; Package C `clear_steady` + Hass locks | **Yes** (unit + Package C) |
| 4. CAP-5 docs criterion A | ADR 0003 Guards; house-calibration §5 | **Yes** |
| 5. CAP-6 pytest green | **96 passed** on touched modules | **Yes** |

AI-1..AI-3 closed by Package C (see close-out above). Remaining open items AI-4/AI-5 (and live Exclusive Session) keep the machine call at `accepted-with-open-items`; they do not flip it to rejected.

## Open questions

1. Should skip-adapt also freeze `_last_critical_zone` / other tuner state beyond the Package C `_steady_ticks` clear?  
2. ~~Is WARN-on-every-failed-trip-write acceptable ops noise, or must once-per-episode survive flaky HA?~~ **Settled by Package C:** once-per-episode via `_blow_up_warned`.  
3. Is live Exclusive Session verification required before treating the initiative as production-proven, given unit-only behavior check?  
4. Should gray-band sticky remain tracking-on (current CAP-4), or move toward ff-only while decaying?

## Assumptions

_Omitted — interactive run; facts recorded where confirmed (Epic summary going-in concerns; finished tickets)._
