---
epic: epic-rls-pid-retune
date: 2026-11-09
verdict: accepted-with-open-items
criteria: declared
headless: false
---

# Retrospective — epic-rls-pid-retune

## Epic summary

**Epic:** `epic-rls-pid-retune` — RLS retune of PID gains (initiative `initiative-pid`, id 3). Going-in concerns: none (`ничего`).

| ref | title | status / state | risk | plan baseline | range used |
|-----|-------|----------------|------|---------------|------------|
| 3.1 | Tracer: RLS adaptive Kp/Ki on control tick | done / done | high | `4568fac` | `4568fac..a70c7e3` (PR #106) |
| 3.2 | Adapted-gain rails and unhealthy RLS fallback | done / done | high | `a70c7e3` | `a70c7e3..6c8e240` (PR #107) |
| 3.3 | Persist RLS state JSON across PID clears | done / done | medium | `6c8e240` | `6c8e240..30e500e` (PR #108) |
| 3.4 | Domain docs for RLS retune | done / done | medium | `30e500e` | `30e500e..f4e47b6` (PR #109–#111) |
| 3.5 | Refactor sweep | done / done | low | `f4e47b6` | `f4e47b6..17f111a` (PR #112) — end at HEAD |

- `pending_tickets`: none. Tickets still at `built`: none.
- Baselines verified oldest-first with `git merge-base --is-ancestor` (`4568fac < a70c7e3 < 6c8e240 < 30e500e < f4e47b6 < 17f111a`).
- Last plan range ends at `HEAD` (`17f111a`); no post-epic cut — HEAD is the 3.5 merge.
- Criteria: **declared** (epic R1–R5, C1–C3, Done when 1–5).
- Product review surface: `4568fac..HEAD` over `apps/`, `tests/`, `AGENTS.md`, `CONTEXT.md`, `docs/adr/`, `docs/house-calibration.md`, `knowledge/`, `apps.yaml.example` (~3076 unified-diff lines staged `/tmp/epic3-product.diff`).
- Diff-scope review: `bmad-review` render HALT (`workflow.md` missing) — lenses run **inline** (adversarial, edge-case, verification-gap). Narrowing recorded.
- Aggregate views: explore subagents + primary-source re-check.
- Phase 3: party mode (installed agents) on Phase 2 findings; Denys directed D1+D2 remediation before Sofia close.

### Evidence inventory

| evidence | status |
|----------|--------|
| Epic file `epic-rls-pid-retune.md` | read in full (C3 + Notes reconciled in remediations below) |
| Initiative file | opened only for R9 line (`initiative-pid.md:36` still says “later epic” — sync note) |
| Entries / plans | 3.1–3.5 (`story_file: null`); all `status: done` |
| Companion `rls-adaptive-algorithm.md` | read in full |
| Run folders | none |
| Previous epic retro | `epic-pid-domain-docs-retrospective.md` |
| Session logs | partial — party `.memlog.md` + plan Code Review blocks; process lessons from plans/commits/memlog |
| `git_evidence.py` | 3.1–3.5 + epic aggregate; `binary_revisions` 0; **3.3** `merge_count=2` / `merges_measured=1` (side merge `2ba96dd`) |
| `deferred-work.md` | read; **Resolved in epic-pid-domain-docs** added during remediations |

### `git_evidence.py` highlights (non-merge `files`)

| range | commits (M) | top product churn |
|-------|-------------|-------------------|
| 3.1 `4568fac..a70c7e3` | 4 (1) | `test_hvac_app.py` +363; `rls.py` +82; `hvac_app.py` +64 |
| 3.2 `a70c7e3..6c8e240` | 5 (1) | `test_hvac_app.py` +422; `hvac_app.py` +82; `test_config.py` +110 |
| 3.3 `6c8e240..30e500e` | 6 (2/1 measured) | `test_hvac_app.py` +594; `test_rls.py` +278; `rls.py` +214; `hvac_app.py` +128 |
| 3.4 `30e500e..f4e47b6` | 7 (3) | docs: ADR 0006 +23; `rls-adaptive-pid.md` +24; AGENTS/CONTEXT/0005 surgical |
| 3.5 `f4e47b6..HEAD` | 3 (1) | deferred-work + companion ownership close; plan only |

## Findings

Disposition key: **fix now** / **defer** / **accept**. Lens findings re-checked against HEAD before routing.

### Spec-to-implementation reconciliation

**SR1 — R1 / Done when 1 (adapted Kp/Ki on same clamp law; no FF/CAP-7).** *Accept (met).*
- Source: `hvac_app.py:242-368`; `test_adaptive_demand_tick_steps_and_uses_imc_gains`; `test_config.py` weather modules absent.

**SR2 — R2 / Done when 3 (JSON separate; clears do not wipe file).** *Accept (met).*
- Source: `rls.py` `STATE_FILENAME`; `hvac_app.py:198-202`; `test_clear_paths_leave_file_and_latch`.

**SR3 — R3 / Done when 4 gates (tick-only RLS; no step plant unavailable / event clear).** *Accept (met).*
- Source: `hvac_app.py:224-342`; `test_adaptive_control_event_no_rls_no_write`; `test_adaptive_plant_unreadable_no_rls_no_integral`.

**SR4 — R4 / Done when 2 (off or unhealthy → yaml fixed).** *Accept (met) for runtime latch.*
- Source: `hvac_app.py:242-327`; latch tests. After reload, latch false + JSON may restore adapted — **documented** (`docs/adr/0006-optional-rls-adaptive-pid.md:19`; `AGENTS.md:35`; `test_initialize_after_latched_restores_adapted_clears_latch`).

**SR5 — R5 (pid.adaptive default off).** *Accept (met).*
- Source: `models.py:59`; `config.py:146-153`; `apps.yaml.example:28`.

**SR6 — Done when 5 (domain docs match shipped path).** *Accept (met).*
- Source: `AGENTS.md:18,35`; `CONTEXT.md:60`; ADR 0006; `knowledge/concepts/rls-adaptive-pid.md`; companion Signals.

**SR7 — Epic Constraint C3 air-y fallback vs as-built.** *Fix now → applied (2026-11-09).*
- Was: epic C3 / Notes still said air-y fallback (`epic-rls-pid-retune.md` pre-remediation).
- Applied: C3 + Notes reconciled to party B1 / companion / ADR 0006 (`boiler_water` required when adaptive on; never demand-zone air).
- Prevention: when party/refine overrides a Constraint, rewrite the epic Constraint in the same change as the companion.

**SR8 — Initiative R9 “later epic” wording.** *Defer (bookkeeping).*
- Source: `initiative-pid.md:36` vs epic `covers: ["R9"]`.

### Architecture / duplication / size

**AD1 — New `rls.py` (285 lines), stdlib-only; sole production importer `hvac_app.py`.** *Accept (positive).*
- Source: `apps/ha_smart_hvac/rls.py`; `hvac_app.py:19-31`.

**GZ1 — `HvacApp` 229→481 lines; `test_hvac_app.py` →2315 (+~1370 RLS).** *Accept (growth noted, not god-class verdict).*
- Source: `wc -l` at HEAD; `git_evidence` product churn.

**DU1 — Dual weights-unusable idle check in `_run_demand`.** *Defer (hygiene).*
- Source: `hvac_app.py:336-338` and `:356-358`.

**DU2 — Test harness `_tick_app` omits `_load_rls_overlay` vs `initialize`.** *Accept (intentional test seam).*
- Source: `test_hvac_app.py` `_tick_app` vs `initialize:69-70`.

### Pattern divergence / process

**PD1 — `review: quick` on high-risk 3.1 and 3.2.** *Defer (process) — carry B3/D3.*
- Source: plan frontmatter `risk: high`, `review: quick` on tracer and rails plans.

**PD2 — Epic-2 deferred-work CAP-8/FF bullets still open.** *Fix now → applied (2026-11-09).*
- Applied: `## Resolved in epic-pid-domain-docs (2026-11-09)` in `_bmad-output/initiative-pid/deferred-work.md` naming the 1.2/1.3/1.4 CAP-8/FF CONTEXT/ADR/`knowledge/` deferrals closed by 2.1–2.5.

**PD3 — Logging channel: `rls.py` stdlib `_LOG` vs AppDaemon `self.log`.** *Accept.*
- Source: `rls.py:19,284`; app-path WARNs use `self.log`.

### Lens findings kept after re-check

- **L-C3-air (adversarial)** → SR7 applied.
- **L-latch-reload (adversarial)** → **accept** (ADR 0006:19).
- **L-persist-reject-θP (adversarial)** → **accept** (`test_persist_after_imc_reject_write_true`).
- **L-boiler-unread-y_prev (edge)** → **accept** (`test_adaptive_boiler_water_unreadable_no_step_leaves_y_prev`).
- **L-plant-unread-y-refresh (edge)** → **accept** (plant-unreadable test).
- **VG-adaptive-off-no-load (verification)** → **defer**.
- **VG-idle-last_u (verification)** → **defer**.
- **VG-docs-automation (verification)** → **accept**.

### Process lessons

- **PL1 — High-risk + `review: quick` survived again on 3.1/3.2** (carry B3/D3).
- **PL2 — Constraint text can lag a party override** (C3 air-y) — SR7 applied this run.
- **PL3 — Positive:** 3.5 closed its own deferred-work ownership.
- **PL4 — Positive:** ADR 0006 + AGENTS document latch RAM-only / JSON restore.
- **PL5 — deferred-work Resolved hygiene** — PD2 applied this run (prior epic-2 C2).

### Team discussion (Phase 3)

Party (installed agents) over Phase 2 findings. Room agreed product criteria were met; clash centered on **when** to fix D1/D2. Sofia owned both as pre-close remediations; Amelia warned C3 still seeds the next refine; Winston defended latch-reload as locked ADR contract (do not re-litigate). Denys directed: fix D1+D2 before Sofia closes. No new sourced findings beyond SR7/PD2/PD1 already inventoried.

## Behavior verification

- **Runtime AppDaemon / Exclusive Session:** not exercised.
- **Exercised:** `uv run pytest tests/test_rls.py tests/test_config.py tests/test_hvac_app.py` → **319 passed** (2026-11-09); ADR/AGENTS/companion reads; inline lenses on `/tmp/epic3-product.diff`.
- Closed-loop plant behavior with live HA remains unverified.

## Previous-retro follow-through

Prior file: `epic-pid-domain-docs-retrospective.md` (2026-11-08, verdict accepted-with-open-items).

| Item | Landed? | Evidence |
|------|---------|----------|
| C1 — Clarify AGENTS idle write-0 vs plant-off no-write | **partially** | `AGENTS.md:32-33` split; `:36` still shorthand |
| C2 — Add Resolved in epic-pid-domain-docs to deferred-work | **yes (this retro remediations)** | `deferred-work.md` section `Resolved in epic-pid-domain-docs (2026-11-09)` |
| C3 / B3 — Do not pin `review: quick` when risk=high | **no** | 3.1 and 3.2 plans still `risk: high`, `review: quick` |
| C4–C6 optional hygiene | **no evidence found** this epic | N/A |
| Epic-1 B6 legacy-scale `ki` WARN | **yes** (this epic) | 3.2 + `config.py` legacy ki WARNING |

## Action items

| # | Action | Kind | Owner | Status |
|---|--------|------|-------|--------|
| D1 | Reconcile epic Constraint C3 (+ Notes) to boiler_water-required / no air-y | spec reconciliation | Sofia / this run | **applied** 2026-11-09 — `epic-rls-pid-retune.md` C3 + Notes |
| D2 | Add **Resolved in epic-pid-domain-docs** to `deferred-work.md` | bookkeeping | Sofia / this run | **applied** 2026-11-09 |
| D3 | At refine, do not pin `review: quick` when `risk=high` (carry B3) | process | team | open |
| D4 | Optional: test `initialize` adaptive-off with present `rls_state.json` leaves RAM cold | defer | future | open |
| D5 | Optional: adaptive-path assert idle/plant-off write-0 does not update `last_u` | defer | future | open |
| D6 | Optional: finish AGENTS `:36` shorthand vs `:32-33` (prior C1 remainder) | defer | docs | open |
| D7 | Sync initiative R9 “later epic” wording when closing | defer | Sofia | open |

Accepted / do not re-flag: SR1–SR6, L-latch-reload, L-persist-reject-θP, L-boiler-unread-y_prev, L-plant-unread-y-refresh, AD1, DU2, PD3, GZ1.

## Decision records

Decision test applied to 3.1–3.5 frozen Intents / Decision indexes / Implementation Notes.

- Major product decisions already in `docs/adr/0006-optional-rls-adaptive-pid.md` (`e3cdd53` / PR #109) + companion HOW.
- Frozen intents do not pass as separate `docs/decisions/` files beyond ADR 0006.
- **User (2026-11-09):** confirmed — no new decision-record files written.

## Acceptance verdict

**Verdict: accepted-with-open-items**, confirmed by the user (2026-11-09). Criteria: **declared**. `pending_tickets` empty. Matches machine recommendation.

Evidence criteria met:

1. Done when 1 — adapted gains on clamp(base+u_pid); FF/CAP-7 absent (SR1).
2. Done when 2 — adaptive off / unhealthy latch → yaml fixed at runtime (SR4); reload latch semantics documented (ADR 0006).
3. Done when 3 — `rls_state.json` persists across clears (SR2).
4. Done when 4 — tick-only RLS + pytest gates/fallback/persist (SR3; 319 passed).
5. Done when 5 — AGENTS/CONTEXT/ADR 0006/knowledge match shipped path (SR6).

Open items remaining after remediations: **D3**/B3 (review pin). Optional D4–D7. D1 and D2 applied before close as directed in party.

Closing the epic remains Sofia’s (`bmad-agent-po`), confirmed by the user. This retrospective’s artifact is this document; remediations D1/D2 were applied to the epic file and `deferred-work.md` by explicit user direction during Phase 3/4. No ticket status changed.

## Open questions

- D3 process enforcement at next refine (no code change).
- D7 initiative R9 wording when Sofia closes the initiative/epic.

## Assumptions

Omit — interactive run; user confirmed verdict, decision-record choice, party discussion, and D1+D2-before-close (2026-11-09).
