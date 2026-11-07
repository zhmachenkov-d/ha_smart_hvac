---
epic: epic-immediate-swt-reactivity
date: 2026-10-20T06:42:53Z
verdict: accepted
criteria: declared
headless: false
---

# Retrospective: Immediate SWT gate reactivity

## Epic summary

**Epic:** `epic-immediate-swt-reactivity` — Immediate SWT gate reactivity  
**Initiative:** `initiative-weather-curve-zone-actuators`  
**Board epic status:** `done`  
**Going-in concerns:** none (user selected epic 2; no weighted focus)  
**Pending / built-only tickets:** none — both `status: done` / `state: done`

| Ref | Title | Status | Covers | Plan baseline | Diff range |
|-----|-------|--------|--------|---------------|------------|
| 2.1 | Tracer: event-driven SWT gate re-evaluation | done | CAP-8 | `aeac9876` | `aeac9876..1231fa16` |
| 2.2 | Document CAP-8 reactivity in ADR and domain docs | done | CAP-8 | `1231fa16` | `1231fa16..d42bfab` (cut: merge PR #77; excludes heating-demand PR #78 on HEAD) |

Baselines ordered by git ancestry (oldest first). Build order matches.

**Done when (declared):** CAP-8 triggers apply CAP-1…3 without waiting solely on periodic tick; event path does not advance CAP-7; periodic still runs CAP-7; tests + ADR/docs state the contract (Hass stubs, not live timer race).

### Evidence inventory

| Artifact | Available? | Path / note |
|----------|------------|-------------|
| Epic file | yes | `epic-immediate-swt-reactivity.md` (Done when → criteria **declared**) |
| Initiative Requirements | yes | parent initiative + spec CAP-8 |
| Spec / companions | yes | `spec-weather-curve-swt-only/` (+ brownfield, architecture-diagrams) |
| Entries (`find`) | yes | refs 2.1, 2.2; no `story_file` (plans carry intent) |
| Plans | yes | two `*-plan.md` with baselines and `status: done` |
| Diff ranges + `git_evidence.py` | yes | two ranges; `merges_measured == merge_count`; no `binary_revisions` |
| Previous retrospective | yes | `epic-weather-curve-swt-only/epic-weather-curve-swt-only-retrospective.md` |
| Session logs | **narrowed** | `walkthrough-pr-75/` + plan Review Triage; raw agent JSONL unused |

Production churn (non-merge `files`): `hvac_app.py` net +48 → **269 LOC**; `tests/test_hvac_app.py` net +302; ADR +9 / CONTEXT +2 / AGENTS +1.

`bmad-review` lenses (adversarial, edge-case-hunter, verification-gap) run on staged `/tmp/epic2-cap8-retro.diff` via independent reviewers [adversarial](056f7b6b-d400-4380-ae02-25ac2470b16b), [edge](cb5dc7c9-a126-4007-8968-879f8d5637f4), [verification](4e9a3f4e-c242-410b-8ba7-771e91921457). Findings below re-checked against primary sources before routing.

## Findings

### Aggregate — architecture / size / duplication

- **F-A1 — Dual entrypoints share one prelude; demand forks by method.** `_gate_prelude` (`hvac_app.py:60-90`) → `control_tick` calls `process_demand` (`:99`); `control_event` calls `clamp_uff` only (`:126`). No `advance_cap7` flag. Import DAG unchanged (acyclic). **Disposition:** accept as-is. **Process:** keep the hard fork; do not collapse paths with a boolean.
- **F-A2 — Not a god-class growth epic.** `hvac_app.py` +48 net / 269 LOC; CAP-7 law untouched in `ff_auto_correct.py`. Test file +302 is the main volume. **Disposition:** accept as-is (win).
- **F-A3 — No duplicated gate law across tickets.** 2.2 docs-only; no second implementation. **Disposition:** accept as-is.

### Aggregate — spec-to-implementation

- **F-S1 — Done when 1–4 met.** Listeners (`hvac_app.py:45-58`); event clamp / no `process_demand` (tests `test_cap8_*`); periodic still `process_demand` (`test_cap8_periodic_still_runs_process_demand`); ADR `## CAP-8 reactivity`, AGENTS CAP-8 bullet, brownfield Reactivity, architecture-diagrams labels. **Disposition:** accept as-is.
- **F-S2 — “Must not advance CAP-7” vs shared clears.** Event path uses the same fail/idle branches that call `clear_ephemeral()` (`hvac_app.py:65-88`). Spec/ADR say must not *advance* samples / persist FF — they do not say ephemeral is immutable on events. Behavior matches CAP-1…3 on both schedules; CAP-8 outdoor-missing / no-zones / idle / plant-off tests assert clears. **Disposition:** accept as-is (behavior). **Process / docs:** clarify in ADR/AGENTS that fail/idle clears still run on events (A1).
- **F-S3 — CONTEXT dialogue understates trigger set.** Dialogue names outdoor + `hvac_action`; omits Plant Management, zone air, setpoint that code/ADR/AGENTS list (`CONTEXT.md` CAP-8 dialogue vs ADR `:20`). **Disposition:** defer (A1 can widen).
- **F-S4 — AGENTS omits event demand = `clamp_uff` only.** CAP-8 bullet states no CAP-7 advance; ADR/brownfield/code state clamp-only demand fork. **Disposition:** defer → propose in A1.

### Diff-scope review — adversarial (ticket-boundary weighted)

- **F-R1 (=F-S2)** — Docs incomplete on clear-vs-advance. Source: ADR `:15-21` vs `_gate_prelude` clears. **Disposition:** fix now → A1 (docs).
- **F-R2 — INFO log on every demand event even when equality-skip.** `control_event` logs after successful `_write_setpoint` path; equality skip still returns True after evaluation… check: `_write_setpoint` returns False only on fail; equality skip returns True without set_value? Re-check needed.
- **F-R3 — No-debounce / equality-skip tradeoff not in ADR/AGENTS.** Locked in story 2.1 plan Design Notes; 2.2 docs omitted. **Disposition:** fix now → A1.
- **F-R4 — architecture-diagrams event→`ac` dashed edge.** May read as a related path. **Disposition:** defer.
- **F-R5 — Module docstring / “this tick” idle string still periodic-flavored.** **Disposition:** defer.
- **F-R6 — Full zone re-read on every event for demand boolean only.** **Disposition:** accept as-is (correctness over micro-optimization).
- **F-R7 — Climate `hvac_action` + `temperature` can double-fire.** **Disposition:** accept as-is (document under A1).
- **F-R8 — Post-epic heating-demand PR #78 outside range.** Demand inputs can change without updating CAP-8 listen set in the same epic. **Disposition:** process lesson → A2. (At HEAD, #78 still uses `hvac_action` — listeners remain aligned; risk is future demand-input drift.)
- **F-R9 — Structural risk of later collapsing dual entrypoints.** **Disposition:** accept as-is; process in F-A1.

### Diff-scope review — edge cases

- **F-E1 — Sensor chatter → log / clear storms** (plant-off / idle / zone-air). Story explicitly chose no debounce. **Disposition:** accept as-is; document (A1). Revisit only if live log/CPU pain observed.
- **F-E2 — Sole-zone unavailable flicker → SWT 0↔clamp thrash.** **Disposition:** defer (same as tick path; CAP-8 makes it more frequent).
- **F-E3 — Idle write-fail still logs success-ish idle message.** Pre-existing pattern on tick. **Disposition:** defer.

### Diff-scope review — verification gaps

- **F-V1 — Behavioral CAP-8 tests always `_fire_control_event` as plant/`state`.** Args ignored today (`hvac_app.py:119`); registration test covers listener shapes. Early entity filter would break production but not these tests. **Disposition:** defer.
- **F-V2 — Event write-fail (plant setpoint unavailable) untested** (tick has `test_demand_fail_write_aborts_without_success_info`). **Disposition:** fix now → **done** (A3): `test_cap8_demand_fail_write_aborts_without_success_info`.
- **F-V3 — ConfigError initialize does not assert no listeners.** **Disposition:** defer.
- **F-V4 — Multi-thermostat single zone not in registration fixture.** **Disposition:** defer.
- **F-V5 — No live Exclusive Session for CAP-8.** Done when explicitly Hass stubs. **Disposition:** accept as-is.

### F-R2 re-check (equality skip + log)

`_write_setpoint` (`hvac_app.py` ~205+): on equal float returns `True` without `set_value`; `control_event` then logs `command=`. So demand chatter with unchanged setpoint still INFO-logs. **Disposition:** accept as-is (story throttle = write bus only); document in A1; optional later log-on-write-only.

## Behavior verification

| Exercise | Result | Source |
|----------|--------|--------|
| `uv run pytest tests/test_hvac_app.py tests/test_coordinator.py -q` | **59 passed** | this retro run (HEAD includes post-epic #78) |
| CAP-8 Hass-stub matrix (demand / outdoor-flip / plant-off / idle / outdoor-missing / no-zones / CAP-7 untouched / seed→event→tick / equality / listeners / periodic) | **locked in suite** | `tests/test_hvac_app.py` CAP-8 block |
| Live Exclusive Session CAP-8 immediacy | **not exercised** | epic Done when: stubs, not live timer race; walkthrough-pr-75 is code walkthrough |

Runtime success signal for this epic is stub-driven by design. Live CAP-8 latency vs tick was not re-run on the house.

## Previous-retro follow-through

Prior file: `epic-weather-curve-swt-only/epic-weather-curve-swt-only-retrospective.md` (verdict **accepted**; human queue empty at close).

| Item | Landed? |
|------|---------|
| A1 dropped (W15 denominator) | n/a (dropped) |
| A2 soft-fail `save_ff_state` | **yes** — `ff_auto_correct.py` `save_ff_state` → bool + `os.replace` (prior retro evidence; not re-opened) |
| A3 D-cmd lower@min tests | **yes** — prior retro |
| A4 restore intra-zone eligibility tests | **yes** — prior retro |
| A5 knowledge notes vs ADR 0004 | **yes** — prior retro |
| A6 optional CAP-7 live adapt | **skipped** at epic 1 close |
| Deferred F-R4/6/7, F-E2/3, F-V2/4 | **still deferred** — no evidence they were closed in this epic (out of CAP-8 scope) |

**Note:** Epic 1 Open question #3 recorded parent initiative `status: done` prematurely; initiative was reopened for CAP-8, then closed correctly 2026-10-20 after both epics done (A2).

## Action items

| ID | Item | Owner | Kind |
|----|------|-------|------|
| A1 | Clarify CAP-8 docs: (1) event path may still `clear_ephemeral` on plant-off / idle / unavailable (same as tick); “must not advance” ≠ immutable ephemeral; (2) no debounce — equality-skip is write throttle; INFO may still fire; double climate attr callbacks expected; (3) AGENTS + CONTEXT trigger/clamp wording to match ADR | Denys | **done** (2026-10-20): ADR 0004 CAP-8 + AGENTS + CONTEXT dialogue + brownfield Reactivity |
| A2 | Process: do not mark initiative `done` until every epic in its `tickets.toml` is done; when demand inputs change, update CAP-8 listeners + ADR trigger list in the same change | Denys | **done** (2026-10-20): initiative closed correctly; AGENTS CAP-8 + initiative-close bullets |
| A3 | CAP-8 event write-fail regression mirroring tick `test_demand_fail_write_aborts_without_success_info` | Denys | **done** (2026-10-20): `test_cap8_demand_fail_write_aborts_without_success_info` |

**Queue (human):** empty (A1–A3 done).

## Acceptance verdict

**accepted** — criteria **declared** (epic Done when). Remediations A1–A3 closed 2026-10-20 (was accepted-with-open-items).

- All tickets finished (`pending_tickets` empty).
- Done when 1–4 demonstrably met (code + CAP-8 tests + ADR/companions/AGENTS).
- No blocking defect that falsifies CAP-8. Deferred F-V1/F-V3/F-V4, F-E2/E3, F-R4/R5 remain recorded, not queued.
- Human may override this machine verdict.

## Open questions

1. ~~Apply A1 docs patch~~ — done 2026-10-20.
2. ~~Close parent initiative~~ — closed 2026-10-20 (`initiative-weather-curve-zone-actuators` `status: done`).
3. ~~A2 / A3~~ — done 2026-10-20 (AGENTS process bullets + CAP-8 write-fail test).
