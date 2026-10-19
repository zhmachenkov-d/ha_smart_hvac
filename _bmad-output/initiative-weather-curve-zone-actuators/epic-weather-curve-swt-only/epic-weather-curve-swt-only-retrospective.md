---
epic: epic-weather-curve-swt-only
date: 2026-10-19T14:19:40Z
verdict: accepted-with-open-items
criteria: declared
headless: false
---

# Retrospective: Weather-curve SWT only

## Epic summary

**Epic:** `epic-weather-curve-swt-only` — Weather-curve SWT only  
**Initiative:** `initiative-weather-curve-zone-actuators`  
**Board epic status:** `done`  
**Going-in concerns:** none (user confirmed epic with `yes`, no weighted focus)  
**Pending / built-only tickets:** none — all seven `status: done` / `state: done`

| Ref | Title | Status | Covers | Plan baseline | Diff range |
|-----|-------|--------|--------|---------------|------------|
| 1.1 | Tracer: weather-curve SWT law | done | CAP-1..3, CAP-5 | `406b6a00` | `406b6a00..6bf761e5` |
| 1.2 | Remove LADRC and ωc from the water path | done | CAP-4 | `6bf761e5` | `6bf761e5..134ba74c` |
| 1.4 | FF rise-rate auto-correct rule (spike) | done | CAP-7 | `134ba74c` | `134ba74c..7bed334b` |
| 1.3 | New ADR and domain docs | done | CAP-4, CAP-6 | `7bed334b` | `7bed334b..d3c099bb` |
| 1.5 | Auto-correct FF from max-error zone rise rate | done | CAP-7, CAP-5 | `d3c099bb` | `d3c099bb..47759834` |
| 1.6 | Refactor sweep | done | — | `47759834` | `47759834..e8a8437a` |
| 1.7 | Live Exclusive Session windup check | done | — | `e8a8437a` | `e8a8437a..ad0acdc` (inferred end = HEAD / epic close) |

Baselines ordered by git ancestry (oldest first). Build-order in `tickets.toml` differs for parallel slots 1.2∥1.4 and 1.3∥1.5; git history serialized them (1.2 → 1.4 → 1.3 → 1.5).

**Done when (declared):** clamp(u_ff) demand path; plant idle/off clear semantics; LADRC/ωc/CZ-as-SWT removed + ADR 0004; CAP-5 suite; CAP-6/7 live without air→SWT tracking; Exclusive Session windup success signal.

### Evidence inventory

| Artifact | Available? | Path / note |
|----------|------------|-------------|
| Epic file | yes | `epic-weather-curve-swt-only.md` (Done when present → criteria **declared**) |
| Initiative Requirements | yes | parent initiative CAP-1…CAP-7 |
| Spec / companions | yes | `spec-weather-curve-swt-only/` (+ brownfield, architecture-diagrams) |
| Entries (`find`) | yes | refs 1.1–1.7; only 1.4 has `story_file` (spike refined) |
| Plans | yes | seven `*-plan.md` with baselines and `status: done` |
| Diff ranges + `git_evidence.py` | yes | seven ranges; all `merges_measured == merge_count`; no `binary_revisions` |
| Previous retrospective | **none in this initiative** | single epic; sibling prior-initiative retros exist (`epic-gate-omega-c-on-saturation-retrospective.md`) but are out of sibling follow-through scope |
| Session logs | **narrowed** | walkthroughs pr-62/63/66/70 + story-1-7 + party-mode memlog used; raw Cursor agent JSONL not treated as structured process logs |

Production churn highlights (non-merge `files` sums): `hvac_app.py` net −231 across epic then +71 in 1.5 → **216 LOC now**; deleted `ladrc.py` / `ladrc_tuner.py`; added `ff_auto_correct.py` (+225). Tests: `test_hvac_app.py` large rewrite; `test_ff_auto_correct.py` +343; LADRC test modules deleted.

## Findings

### Aggregate — architecture / size / duplication

- **F-A1 — Package is an acyclic adapter-over-pure-law DAG.** `models` → `{feedforward, coordinator, config}` → `ff_auto_correct` → `hvac_app`. No cycles. Source: import graph at HEAD (`hvac_app.py:9-23`, `ff_auto_correct.py:12-18`). **Disposition:** accept as-is. **Process:** keep Hass I/O out of CAP-7 module.
- **F-A2 — No weather_ff / clamp duplication.** Linear law only in `feedforward.py:8-10`; plant clamp via `clamp_uff` (`ff_auto_correct.py:119-121`). **Disposition:** accept as-is.
- **F-A3 — Not a god-class growth epic.** `hvac_app` shrank (~439→216 vs prior omega-c retro); `ff_auto_correct` 225 LOC (~33% of 685-LOC package). Source: line counts + `git_evidence` nets. **Disposition:** accept as-is (win).
- **F-A4 — Test harness mirrors plant clamp with inline max/min** (`tests/test_hvac_app.py:85-87`) instead of `clamp_uff`. **Disposition:** defer. **Process:** prefer shared helper in tests when clamp policy moves.

### Aggregate — spec-to-implementation

- **F-S1 — Done when 1–4 and 6 met with evidence.** Demand clamp path (`hvac_app.py:73-74`); idle/off (`:48-51,:67-71`); ADR 0004 + superseded 0002/0003; CAP-5 tests (`test_hvac_app.py:115-273`); live 1.7 pass 4A (`walkthrough-story-1-7.md:5,114-123`). **Disposition:** accept as-is.
- **F-S2 — Done when 5 / CAP-7: code+pytest live; mid-window adapt not shown in 1.7.** Overlay absent; near-setpoint shape freezes adapt (`ff_auto_correct.py:169-170`, eps default 0.3). Walkthrough marks N/A (`walkthrough-story-1-7.md:105,120`). **Disposition:** accept as-is (DW5 satisfied by automated CAP-7 locks + code on path; live adapt is a separate HITL scenario). **Process:** if a future epic needs live CAP-7 proof, schedule a non-freeze demand shape — do not overload the windup Exclusive Session.
- **F-S3 — Knowledge ADRC/LADRC/MADRC/Huang notes deferred by Story 1.6 B1.** **Disposition:** defer → **done** (A5): project notes aligned to ADR 0004; `deferred-work.md` cleared.
- **F-S4 — Extras not in CAP prose (brownfield):** outdoor/empty-zones → idle write 0 (`hvac_app.py:53-65`); write-on-change skip (`:209-210`); auto_correct nest defaults on (`config.py:45-46`, `apps.yaml.example:17`). **Disposition:** accept as-is (document if a later reader confuses them with CAP-2 / opt-in).

### Diff-scope review — adversarial (ticket-boundary weighted)

- **F-R1 — W15 `hours` uses `WINDOW_SIZE` intervals, not sample-span.** `ff_auto_correct.py:224`: `hours = WINDOW_SIZE * control_interval / 3600.0` with 15 samples → ~6.7% vs wall span of 14 intervals. **Disposition:** accept as-is (2026-10-19 party + human). Spike already locks this: physical span ~14×dt, **denominator stays 15×dt** (`spike-ff-rise-rate-auto-correct-rule-decision.md:38`). Code/ADR match the contract; retro adversarial mis-flagged it as a bug.
- **F-R2 — `save_ff_state` unguarded / non-atomic** (`ff_auto_correct.py` was `:73-76`). **Disposition:** fix now → **done** (A2): atomic `os.replace`, returns `bool`; `_persist_ff_state` logs WARNING on False.
- **F-R3 — Near-setpoint / freeze ticks still append W15** (`ff_auto_correct.py:158-170`). Flat samples enter the window before freeze return. **Disposition:** defer (law as spike 1A; changing append-before-freeze is a CAP-7 contract change). **Process:** if overshoot after leaving freeze is observed live, revisit.
- **F-R4 — Yaml commission base/slope not bounded like B1 JSON** (`config.py` weather_ff parse vs `params_in_bounds`). **Disposition:** defer.
- **F-R5 — No CAP-7 `enabled` off switch** (nest omitted → E2 on). **Disposition:** accept as-is (epic Decision CAP-7 stays live 1A); optional future opt-out. **Process:** document in ADR/AGENTS that omit means on.
- **F-R6 — Superseded ADR 0002/0003 keep full normative bodies.** Frontmatter superseded; risk of reimplementation from archive text. **Disposition:** defer (stub/archive).
- **F-R7 — Mutate-before-write / persist on equality-skip** (adversarial). Memory can nudge before plant write; persist can fire when `_write_setpoint` no-ops on equal float. Partially intentional (spike 2C on write fail). **Disposition:** defer (needs product call on atomicity). Re-check before treating as defect: spike decision owns 2C.

### Diff-scope review — edge cases

- **F-E1 (=F-R2)** — OSError on persist after write. Same disposition.
- **F-E2 — Non-finite outdoor / zone_error / yaml floats** not rejected at config or tick. **Disposition:** defer (fail-closed idle already covers unread/None outdoor; NaN entities are rare HA states).
- **F-E3 — `outdoor_gate_delta_k ≤ hysteresis` / `near_setpoint_eps_k ≤ 0` accepted by parse.** **Disposition:** defer (config validation hardening).

### Diff-scope review — verification gaps

- **F-V1 — D-cmd lower@min untested.** **Disposition:** fix now → **done** (A3): `test_d_cmd_blocks_lower_at_min`, `test_d_cmd_allows_relieving_from_min`, `test_cap7_d_cmd_blocks_lower_at_min_no_json`.
- **F-V2 — Hass CAP-7 never multi-zone through `control_tick`.** Pure Z1/selector tested; Hass CAP-7 single-zone only. **Disposition:** defer.
- **F-V3 — Intra-zone thermostat eligibility tests removed in 1.1/1.2 rewrite.** **Disposition:** fix now → **done** (A4): restored under current `zone_error` / `has_heating_demand` / `select_max_error_demand_zone` API.
- **F-V4 — I1 hysteresis mid-band hold untested.** **Disposition:** defer.
- **F-V5 — Live success signal is HITL-only (by design of 1.7).** CAP-5(d) stub ≠ Exclusive Session. **Disposition:** accept as-is.

## Behavior verification

| Exercise | Result | Source |
|----------|--------|--------|
| `uv run pytest tests/test_hvac_app.py tests/test_ff_auto_correct.py tests/test_config.py tests/test_coordinator.py` | **78 passed** | this retro run |
| Live Exclusive Session windup (≈5 × 60 s) | **pass 4A** — `command=40` five ticks; Production restored; `plant_setpoint` operator-confirmed | `walkthrough-story-1-7.md` |
| Live CAP-7 mid-window adapt | **not exercised** (near-setpoint freeze / no overlay) | same walkthrough |

Runtime behavior of the epic’s primary success signal was exercised on the house path; CAP-7 adapt under non-freeze demand was not re-run live in this epic.

## Previous-retro follow-through

No previous retrospective file in this initiative (single epic). Prior-initiative retros (e.g. `epic-gate-omega-c-on-saturation-retrospective.md`) are not sibling follow-through targets; note only that many of that epic’s open ωc/LADRC items are **mooted by CAP-4 deletion** in this epic (modules removed), not re-verified item-by-item here.

## Action items

| ID | Item | Owner | Kind |
|----|------|-------|------|
| A1 | ~~Fix W15 rate denominator to `(N−1)`~~ | — | **dropped** (2026-10-19): spike `…decision.md:38` keeps 15×dt; F-R1 accept as-is |
| A2 | Soft-fail `save_ff_state` / `_persist_ff_state` on `OSError` (log; do not abort tick after SWT write); prefer atomic write | Denys | **done** (2026-10-19): `save_ff_state` → bool + `os.replace`; `_persist_ff_state` WARNING; ADR B1 note; tests |
| A3 | Add D-cmd lower@min pure + Hass regression (mirror raise@max) | Denys | **done** (2026-10-19): pure + Hass + relieving-from-min |
| A4 | Restore intra-zone thermostat eligibility tests removed from `test_coordinator.py` | Denys | **done** (2026-10-19): multi-thermostat / idle / None / idle-cannot-win |
| A5 | Align ADRC/LADRC/MADRC/Huang knowledge notes with ADR 0004 | Denys | **done** (2026-10-19): project notes + refs + deferred-work cleared |
| A6 | Optional later HITL: CAP-7 adapt under non-near-setpoint demand (not a windup re-run) | Denys | process / defer |

**Queue (human, one-by-one):** A6 (A1 dropped; A2–A5 done).

## Acceptance verdict

**accepted-with-open-items** — criteria **declared** (epic Done when).

- All tickets finished (`pending_tickets` empty).
- Done when 1–4 and 6 demonstrably met (tests + ADR + live 1.7 pass 4A).
- Done when 5 met for CAP-6 and for CAP-7 as code+pytest on the demand path; live mid-window adapt not shown (accepted gap, tracked as F-S2 / A6).
- Named open items: A2–A4 (fix-now proposed), A5 (deferred-work), A6 (HITL defer); A1 dropped (F-R1 accept); plus deferred findings F-R3/4/6/7, F-E2/3, F-V2/4.

Machine verdict is not **rejected** (no unfinished tickets; criteria not failed). Open remediations keep the human-facing spelling at **accepted-with-open-items**.

## Open questions

1. Should CAP-7 stay always-on when the `auto_correct` nest is omitted, or should yaml grow an explicit `enabled` switch (F-R5)?
2. Is append-before-freeze (1A) still desired after live observation, or should near-setpoint ticks skip W15 append (F-R3)?
3. Close the parent initiative now that its only epic is done and this retro is filed?
