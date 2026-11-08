---
epic: epic-fixed-pid-swt
date: 2026-11-08
verdict: accepted-with-open-items
criteria: declared
headless: false
---

# Retrospective — epic-fixed-pid-swt

## Epic summary

**Epic:** `epic-fixed-pid-swt` — Fixed-gain PID Set Water Temperature (initiative `initiative-pid`). Re-run 2026-11-08 after tickets **1.5–1.8** closed the 2026-11-07 retro's A1–A5 / DU1 / EC1. User raised no going-in concerns before Phase 1; analysis weighted prior-retro follow-through and the 1.5→1.7→1.6→1.8 boundaries.

| ref | title | status / state | risk | plan baseline | range used |
|-----|-------|----------------|------|---------------|------------|
| 1.1 | Tracer: fixed-gain PID SWT law | done / done | high | `dcedf7d` | `dcedf7d..7644c86` (PR #84) |
| 1.2 | Tick-owned PID advance and event clear-only | done / done | high | `7644c86` | `7644c86..3d44e49` (PR #85; includes releases 1.6.0 / 1.7.0) |
| 1.3 | Remove Outdoor, Weather Feedforward, and CAP-7 from the App | done / done | medium | `3d44e49` | `3d44e49..e510dfd` (PR #86) — **cut** (prior retro): exclude release 1.7.1 + PR #87 bmad skills |
| 1.4 | Refactor sweep | done / done | low | `21ec330` | `21ec330..39e6e75` (PR #88) — end of first retro |
| 1.5 | PID integral units and R7 skip hardening | done / done | high | `9488039` | `9488039..c642f92` (PR #91 + release 2.0.0) |
| 1.7 | Commission parse hardening and legacy-key warning | done / done | medium | `c642f92` | `c642f92..de5f84c` (PR #92) — **cut**: recorded next baseline is `8342bf2`; exclude release 3.0.0 and PR #93 (claude-rules) |
| 1.6 | Commission house apps.yaml for fixed PID | done / done | medium (hitl) | `8342bf2` | `8342bf2..4789d79` (PR #94) |
| 1.8 | Refactor sweep 2 | done / done | medium | `4789d79` | `4789d79..HEAD` = `..d037933` (PR #95 + release 3.0.1) — **inferred** end |

- `pending_tickets`: none. Tickets still at `built`: none.
- Baselines verified oldest-first with `git merge-base --is-ancestor` (`dcedf7d < 7644c86 < 3d44e49 < 21ec330 < 9488039 < c642f92 < 8342bf2 < 4789d79 < HEAD`).
- Between 1.4 and 1.5: PR #89 (this retro v1) and PR #90 (replan) — not story ranges.
- Post-replan review diff: `9488039..d037933` over `apps/`, `tests/`, `apps.yaml.example`, `docs/house-calibration.md`, `.gitignore` (1766 diff lines). Full epic runtime range remains `dcedf7d..d037933`.
- `git_evidence.py` run once per new range (1.5, 1.7-cut, 1.6, 1.8); `merges_measured == merge_count` on each cut range.

### Evidence inventory

| evidence | status |
|----------|--------|
| Epic file `epic-fixed-pid-swt.md` | read in full — Requirements R1–R9, Constraints C1–C5, Done when 1–6 → criteria **declared** (C4/C5/R7 re-rendered after first retro) |
| Initiative file | not opened — every `covers` id is restated in the epic file |
| Entries (`tickets.py find`) | read for 1.1–1.8 |
| Story files | none (`story_file: null` for all eight); entries hold the spec |
| Plans | all eight read (frozen intent; 1.5/1.7/1.8 I/O matrices; Review / Code Review / Verification) |
| `git_evidence.py` | 1.1–1.4 retained from prior retro; 1.5 / 1.7-cut / 1.6 / 1.8 re-run |
| Run folders | none in the epic folder |
| Companions | none (`companions: []`) |
| `deferred-work.md` | read — Resolved in 1.6 / 1.7 / 1.8 sections present; AGENTS/CONTEXT/ADR/`knowledge/` still deferred to epic 2 |
| Previous epic retrospective | none — this is still initiative epic id 1 (`after: []`) |
| Same-epic prior retro (2026-11-07) | loaded and reconciled; its A1–A10 are the follow-through checklist below |
| Session logs | **partial**: Cursor agent transcripts exist under `agent-transcripts/` for recent work; Claude session logs for 1.1–1.3 remain absent (same gap as prior retro). Process-lesson claims for 1.5–1.8 use plans' Code Review blocks + commits |
| Gates at HEAD (`d037933`) | `uv run pytest` **288 passed**; `uv run ruff check apps tests` clean |

## Findings

Scope: prior-retro findings for 1.1–1.4 are **reconciled** against HEAD (closed / still open / accepted). New aggregate views and lenses cover `9488039..d037933`. Diff-scope review: three lenses (adversarial, edge-case-hunter, verification-gap) over that staged diff via a review agent; every kept finding was re-checked against live files. Known epic-2 docs drift stays a process/follow-through item, not a new runtime defect.

Disposition key: **fix now** = before Exclusive Session / before treating the epic as fully closed in language; **defer** = tracked; **accept** = recorded deviation, do not re-flag; **closed** = prior finding landed in 1.5–1.8.

### Prior-finding reconciliation (from 2026-11-07)

| Prior | Disposition now | Evidence |
|-------|-----------------|----------|
| SR1 I-term ±5 °C relay | **closed** | `pid.py` uses `dt_hours = control_interval/3600`, I-term clamps; defaults `ki=1.0`, `i_term_min/max=±10/15` (`models.py:54-58`); tests `test_constant_error_ramps_about_one_twelfth_per_tick`, `test_multi_tick_trace_constant_error` |
| SR2 R7 last_commanded skip | **closed** | `_write_setpoint` skips only when plant reads command (`hvac_app.py:213-225`); `_last_commanded` deleted in 1.8 (`8f09384`); tests `test_plant_drift_rewrites_command`, `test_plant_unavailable_no_integral_step`, `test_equal_rounded_skip_no_set_value` |
| SR3 event off-gap / ∫ reset | **accept** (unchanged) | R6 as written; handed to epic 2 ADR inputs |
| SR4 house yaml unmigrated | **closed** | local `apps/apps.yaml`: `ignored_keys==()`, `base=42`, `pid kp=2 ki=1 i_term±15`, `interval=300` (operator verify 1.6); `.gitignore` covers `apps/apps.yaml.*` |
| SR5 `knowledge/` unowned | **closed** (ownership) | `epic-pid-domain-docs.md` Boundaries/Done when name `knowledge/` |
| SR6 release understatement | **closed** for 1.5+ | `fix(pid)!` / `fix(config)!` → majors **v2.0.0** / **v3.0.0**; v3.0.1 documents 1.8. Historical v1.7.0 note remains archive-only |
| PD1 commission parse crash | **closed** | C5 / `config.py` `_number` + range checks; initialize logs `HVAC config error` |
| PD2 CAP-era docstring | **still open → defer** | `hvac_app.py:62` still `"""Shared CAP-1…CAP-3 prelude…"""` |
| DU1 triple idle write | **closed** | `_go_idle` serves write-0+clear paths (`8f09384`) |
| VG1–VG4 test gaps | **closed** | distinct kp (`test_distinct_gains_wire_kp_and_ki_into_tick`), ∫ across ticks (`test_integral_from_tick_one_appears_in_tick_two_command`), `i_term_min` (`test_lower_rail_i_term_stops_at_i_term_min`), off-grid skip (`test_equal_rounded_skip_no_set_value` raw 41.96) |
| EC1 round-after-clamp over max | **closed** | `quantize_command` (`pid.py:24-33`) |
| EC2 weight-0 / EC3 outdoor fail-safe | **accept** (unchanged) | designed |

### Spec-to-implementation reconciliation (new)

**SR7 — Epic R2 / Done when 2 still required clearing "last commanded SWT" after 1.8 deleted that state.** *Closed (spec reconciliation, party fork 3 A).*
- Was: epic R2 / Done when 2 / Notes named last commanded SWT while as-built clear is ∫ only (`8f09384`).
- Now: epic file re-rendered 2026-11-08 (R2, Done when 2, Notes) — integral only; D22 / entry 8 cited.
- Prevention: when a closing sweep deletes a named Done-when inventory item, re-render the epic Requirements / Done when in the same change.

**SR8 — Operator upgrade that keeps a pre-migration numeric `pid.ki` (e.g. `0.1`) silently reinterprets it as 1/h.** *Accept (documented) / defer product hardening.*
- Source: `_PID_KEYS` still treats `ki` as known (`config.py:41`); only `integral_min/max` land in `ignored_keys`. Docs warn explicitly (`docs/house-calibration.md:91`).
- This house was re-commissioned in 1.6 (`ki: 1.0`). Lenses flagged the footgun; it is not a silent house defect today.
- Optional later: WARN when legacy integral_* keys appear alongside an explicit `ki`, or require deleting `ki` to take the new default.

### Pattern divergence

**PD2 — CAP-era naming in runtime docstring.** *Closed (party B5 B).* `hvac_app.py:62` now: Plant Management / Heating Demand prelude.

**PD3 — Plans still pin `review: quick` on high-risk work after retro A9.** *Process (see PL1).*
- Source: 1.5 plan frontmatter `risk: high`, `review: quick`; ticket Notes and Code Review block say full multi-lens was run anyway (`story-pid-integral-units-and-r7-skip-hardening-plan.md` Code Review: blind-hunter, edge-case, verification-gap, intent-alignment; 8 patches).
- The pin and the practice disagree; the next high-risk ticket can miss the extra review if Notes are ignored.

### Duplication map

No new cross-ticket duplication in `9488039..HEAD`. DU1 closed.

### Architecture delta and size growth

**AD1 — Structure remains clean.** *Accept (positive).*
- Package at HEAD: `hvac_app` → `config`, `coordinator`, `models`, `pid`; `pid` → `models`; `config` → `models`. No cycles. FF modules still absent.
- Line counts: `hvac_app.py` 229, `config.py` 232, `pid.py` 131, `models.py` 75, `coordinator.py` 36. Tests grew with 1.5–1.8 (`test_hvac_app.py` 950, `test_config.py` 430, `test_pid.py` 293). No god-class candidate from epic growth.
- 1.5–1.8 churn (non-merge `files`): dominated by tests + `config.py` (+110 net in 1.7-cut) + `pid.py` / plans / CHANGELOG — expected for hardening.

### Lens findings (1.5–1.8 diff) after re-check

Kept:

- **VG5 — Drift-repair test is a single tick with plant already at 50.** *Defer (tests).* Docstring at `tests/test_hvac_app.py:591-592` says "after we commanded 42.0"; body never writes then drifts. A restored `_last_commanded` short-circuit before `_write_setpoint` would still pass this test and `test_integral_from_tick_one_*` (echo plant stays at command). Prefer a two-tick echo then mutate plant → assert rewrite.
- **EC4 — Off-grid `quantize_command` fallback can command a value a 0.1-step plant never stores.** *Accept (in scope of 1.5 Assumes / 1.8 matrix).* Write-then-True without readback is existing AppDaemon pattern; exotic bounds only. Do not re-flag unless plant step ≠ 0.1 becomes in-scope.
- **EC5 — Exact float equality for R7.** *Accept under verified 0.1 plant step* (1.5 Assumes). Half-step tolerance not required by current plant evidence.
- **AD-legacy-ki** — same as SR8.
- **gitignore / no CI house yaml** — *Accept (policy).* Entity IDs must stay local; 1.6 verify is operator `parse_config` HITL, not CI.

Dropped after re-check:

- Idle `_go_idle` clears ∫ when plant write-0 fails — designed (R2/R3 clear on idle/fail); demand R7 hold-on-unavailable does not apply to idle clear.
- Parse-time max weight — overflow path now idles via non-finite `e` (1.8); not a silent `setpoint_max` command anymore.

### Process lessons

- **PL1 (repeat) — `review: quick` pin on high-risk tickets survived A9.** 1.5 still pinned quick; separate full code review again found 8 patches. Lesson stands: change the pin or make the multi-lens review a hard gate in the build route, not only a ticket Note.
- **PL2 — AGENTS.md / CONTEXT still describe FF/CAP-7/CAP-8** while runtime is PID since 1.3. Still open until epic 2; every intervening agent session remains misinformed. A8 not yet executed.
- **PL3 — Units/sanity check** was applied in the replan (D15 °C·h) — positive follow-through on the prior lesson.
- **PL6 — Done-when inventory drifted after a sweep deleted state.** 1.8 removed `_last_commanded` without re-rendering epic R2 / Done when 2 (SR7). Closing sweeps need a Sofia/spec pass for named inventory.

## Behavior verification

- **Not exercised end to end in AppDaemon.** Exclusive Session (ADR 0001) still required; epic-pid-domain-docs still owns the live commissioning HITL note.
- **Exercised instead:**
  - `uv run pytest` at `d037933` — **288 passed**
  - `uv run ruff check apps tests` — clean
  - Operator parse of house `apps/apps.yaml` — `ignored_keys == ()`, base 42, interval 300, house pid nest present
  - Lens pass over `9488039..HEAD` staged diff
- Closed-loop comfort on the real plant remains unverified.

## Previous-retro follow-through

No **previous epic** retrospective exists (`epic-fixed-pid-swt` is initiative epic 1).

**Same-epic prior retrospective (2026-11-07) action items:**

| Item | Landed? | Evidence |
|------|---------|----------|
| A1 Retune integral units / C4 | **yes** | 1.5 / D15; `pid.py`, `models.py`, `apps.yaml.example`, `docs/house-calibration.md`; multi-tick tests |
| A2 Reconcile R7 plant readback | **yes** | 1.5 / D22; `hvac_app.py:213-225`; drift + unavailable tests |
| A3 Harden commission parsing | **yes** | 1.7 / C5; `config.py` `_number` + range checks; `tests/test_config.py` |
| A4 Close VG1–VG4 tests | **yes** | 1.5 tests listed under reconciliation table |
| A5 Migrate house apps.yaml (+ legacy WARNING) | **yes** | 1.6 HITL parse; 1.7 `ignored_keys` WARNING |
| A6 Add `knowledge/` to epic 2 | **yes** (spec) | `epic-pid-domain-docs.md` Description / Done when / Boundaries |
| A7 Hand ADR inputs to epic 2 | **yes** (spec) | `epic-pid-domain-docs.md` Notes decision listing tick-owned, SR3, anti-windup, R7/D22, °C·h |
| A8 AGENTS.md first in epic 2 | **not yet** | `AGENTS.md:32-35` and `CONTEXT.md` still FF/CAP-7/CAP-8; epic 2 not built |
| A9 Do not pin `review: quick` on high-risk | **no evidence of pin change** | 1.5 still `review: quick`; full review done via Notes/practice only |
| A10 BREAKING CHANGE / release hygiene | **yes** going forward | `fix(pid)!`, `fix(config)!`, majors 2.0.0 / 3.0.0 |

## Action items

Everything below is proposed. None applied by this retrospective. Code → `bmad-build`; spec → Sofia (`bmad-agent-po`), confirmed by the user.

| # | Action | Kind | Owner | From |
|---|--------|------|-------|------|
| B1 | Re-render epic R2, Done when 2, and the clear-inventory Note: ephemeral clear is ∫ only (no last commanded SWT). | spec reconciliation | Sofia | SR7, PL6 — **done 2026-11-08** (party fork 3 A) |
| B2 | In epic 2, land AGENTS.md / CONTEXT / ADR / `knowledge/` **first** (carry A8). | process / docs | Sofia / `bmad-project-context` | PL2, A8 — **party: keep open; epic 2 opens with AGENTS** (A) |
| B3 | At refine, do not pin `review: quick` when `risk=high` (team discipline; no bmad-build customize now). | process | team | PD3, PL1, A9 — **party locked A** |
| B4 | Optional two-tick plant-drift R7 test (VG5). | remediation (tests) | deferred-work | VG5 — **party locked A → deferred-work.md** |
| B5 | Rename `_gate_prelude` docstring away from CAP-1…CAP-3. | remediation (cosmetic) | Amelia | PD2 — **party locked B → done 2026-11-08** (`hvac_app.py`) |
| B6 | Optional WARN/migrate for legacy-scale `ki` with `integral_*`. | defer | future / epic 3 | SR8 — **party locked A → deferred-work.md** |

Open items that **block Exclusive Session** from the prior retro (A1, A3, A5) are closed. Live run still waits on epic-pid-domain-docs HITL + B2 agent-context truthfulness.

Still open after party: **B2**, **B3** (process). Deferred: B4, B6. Done in-session: B1, B5.

Accepted / do not re-flag: SR3, EC2, EC3, EC4, EC5, gitignore house yaml policy, SR8 as documented for this house (hardening deferred).

## Decision records

Decision test applied to 1.5–1.8 frozen blocks / Design Notes (1.1–1.4 decisions unchanged from prior retro).

Prior three (still pass; still destined for epic 2 ADR per prior user decision — **no new ADR files written then**):

1. Demand SWT tick-owned; events clear-only.
2. Anti-windup = I-term clamps + same-sign SWT saturation freeze.
3. ∫ / skip rule as revised by D22 (plant readback; no ∫ while unavailable) — supersedes the 1.1 "∫ on equal-rounded skip" wording.

New candidates from 1.5–1.8:

4. **Integral in °C·h with I-term limits in °C of water (D15 / C4).** Source: 1.5 frozen intent; commit `4ca3a84`. Hard to reverse (commission + units); trade-off vs per-tick integral.
5. **Clear inventory is ∫ only — `_last_commanded` removed (D22 / 1.8).** Source: 1.8 frozen intent; commit `8f09384`. Epic R2 / Done when 2 re-rendered to match (B1).
6. **Commission parse rejects bad numbers with ConfigError and reports ignored_keys (C5 / D20).** Source: 1.7 frozen intent; commit `712cc9c`.

**User decision (party 2026-11-08, fork 2 A):** do not write ADR files now. Pass decisions 1–6 into epic 2's superseding ADR. **No decision-record files were written.**

## Acceptance verdict

**Verdict: accepted-with-open-items**, confirmed by the user (party fork 1 A; matches machine). Criteria: **declared**. `pending_tickets` empty.

Evidence criteria met in code/tests at `d037933`:

- Done when 1–6: locked by package absence of FF/CAP-7, house yaml commission (local verify), tick-owned demand, R7 plant readback tests, Critical Zone log-only; Done when 2 prose re-rendered to ∫-only clear (B1 done).
- Prior blocking open items A1–A5 closed via 1.5–1.7–1.6.

Open items still tracked: B2 (epic 2 / A8 AGENTS), B3 (process refine discipline). B4/B6 deferred. B1/B5 done in-session. No live Exclusive Session.

Closing the epic or changing ticket state remains Sofia's job, confirmed by the user. This retrospective changed epic prose (B1) and one docstring (B5); no ticket status changed.

## Open questions

- **Production AppDaemon version?** Prior answer was v1.5.1 (pre-epic). Confirm whether Production has been upgraded past that; do not upgrade until epic 2 HITL closes if still on 1.5.1.
- Closed-loop plant behavior still unverified (Exclusive Session not run).

## Assumptions

Omit — interactive run; facts confirmed above in Epic summary / follow-through.

## Team discussion

Opt-in party (Product Team, session mode) 2026-11-08. Seeded with Phase 2 findings.

Locks: fork 1 A (verdict accepted-with-open-items), fork 2 A (no ADR files — pass 1–6 to epic 2), fork 3 A (B1 now — applied). B2 A (epic 2 opens with AGENTS), B3 A (refine: no quick on high-risk), B4 A (deferred-work), B5 B (docstring fixed), B6 A (deferred-work). Party closed 2026-11-08; Phase 5 finalized.
