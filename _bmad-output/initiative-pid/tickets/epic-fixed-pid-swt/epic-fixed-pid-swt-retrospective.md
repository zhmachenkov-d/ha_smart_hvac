---
epic: epic-fixed-pid-swt
date: 2026-11-07
verdict: accepted-with-open-items
criteria: declared
headless: false
---

# Retrospective — epic-fixed-pid-swt

## Epic summary

**Epic:** `epic-fixed-pid-swt` — Fixed-gain PID Set Water Temperature (initiative `initiative-pid`), selected by the user from the offer (the only epic with finished tickets). User raised no going-in concerns.

| ref | title | status / state | risk | plan baseline | range used |
|-----|-------|----------------|------|---------------|------------|
| 1.1 | Tracer: fixed-gain PID SWT law | done / done | high | `dcedf7d` | `dcedf7d..7644c86` (PR #84) |
| 1.2 | Tick-owned PID advance and event clear-only | done / done | high | `7644c86` | `7644c86..3d44e49` (PR #85; includes release commits `0667c02` 1.6.0, `3d44e49` 1.7.0) |
| 1.3 | Remove Outdoor, Weather Feedforward, and CAP-7 from the App | done / done | medium | `3d44e49` | `3d44e49..e510dfd` (PR #86) — **cut**: recorded range runs to `21ec330`; `25ebb42` (release 1.7.1) and `417efe8`/`21ec330` (PR #87, bmad skills, unrelated) excluded |
| 1.4 | Refactor sweep | done / done | low | `21ec330` | `21ec330..HEAD` = `..39e6e75` (PR #88) — **inferred** end (last plan runs to HEAD) |

- `pending_tickets`: none. Tickets still at `built`: none.
- Baselines verified oldest-first with `git merge-base --is-ancestor` (`dcedf7d < 7644c86 < 3d44e49 < 21ec330 < HEAD`). Every range: `merges_measured == merge_count` except 1.2 (2 merges, 1 measured — the unmeasured one is `c584a8b`, a `main`→branch sync merge).
- Epic-wide review diff: `dcedf7d..39e6e75` over `apps/`, `tests/`, `apps.yaml.example`, `README.md`, `docs/house-calibration.md` (3327 diff lines).

### Evidence inventory

| evidence | status |
|----------|--------|
| Epic file `epic-fixed-pid-swt.md` | read in full — declares Requirements R1–R9, Constraints C1–C4, Done when 1–6 → criteria **declared** |
| Initiative file `initiative-pid.md` | not opened — every `covers` id is restated in the epic file |
| Entries (`tickets.py find`) | read for 1.1–1.4 (description, verify, covers, notes) |
| Story files | none — no ticket was pulled (`story_file: null` for all four); entries hold the spec |
| Plans | all four read in full: frozen intent, I/O matrices (1.1, 1.2), Design / Implementation Notes, Plan Change Log, Review Triage Log, Verification, Code Review blocks |
| `git_evidence.py` | run once per range (4 runs) |
| Run folders (`<type>-*/`) | none exist in the epic folder |
| Companions | none (`companions: []`) |
| `deferred-work.md`, `.memlog.md` | read (initiative-level) |
| Previous retrospective | none — this is the initiative's first epic (`epics` order: id 1, `after: []`) |
| Session logs | **partial**: only story 1.4 build (`9cf62282…`) and 1.4 code review (`e31f7d8b…`) transcripts are in `~/.claude/projects/-workspaces-ha-smart-hvac/`. 1.1–1.3 were built in Cursor (commit trailers `Co-authored-by: Cursor`) and left no session record here → process-lesson analysis for 1.1–1.3 is **skipped**, limited to what plans and commits record |
| Gates re-run at HEAD (`39e6e75`) | `uv run pytest` 130 passed; `uv run ruff check apps tests` clean; `ruff format --check` clean; plan 1.3/1.4 `rg` absence greps: no matches |

## Findings

Scope: aggregate views computed inline over the four ranges (import graph from `git show <rev>:<file>` at `dcedf7d` vs `39e6e75`; sizes from `git_evidence.py` + current files). Diff-scope review: `bmad-review` with the adversarial, edge-case-hunter and verification-gap lenses, run in parallel over `git diff dcedf7d..39e6e75 -- apps/ tests/ apps.yaml.example README.md docs/house-calibration.md`, with the 1.1→1.2→1.3→1.4 boundaries weighted. The verification-gap lens ran mutants on a copy of the code. Every lens finding below was re-checked against the primary source before it was kept. The known epic-2 drift (AGENTS.md / CONTEXT.md / ADR 0004 still describe FF/CAP-7/CAP-8) was excluded from the lenses. It appears only as process lesson PL2.

Disposition key: **fix now** = before live commissioning or before epic 3; **defer** = tracked, not blocking; **accept** = recorded deviation, do not re-flag.

### Spec-to-implementation reconciliation

**SR1 — With the C4 default commission, the integral term acts as a ±5 °C relay and cannot supply the water temperature the house needs.** *Fix now (spec reconciliation + defaults).*
- Source: `apps/ha_smart_hvac/pid.py:91` steps `∫ += e·dt`, where `dt = control_interval` in seconds (`hvac_app.py:110`). The defaults `ki=0.1` and `integral_min/max=±50` come from `models.py:54-58`, `apps.yaml.example:18-20` and epic C4.
- One tick rails the integral: with `dt=300` (or `dt=60`), any |e| ≥ 0.17 °C (or 0.83 °C) hits ±50 in a single tick. The tests assert exactly this: `tests/test_hvac_app.py:476-477` expects ∫ = 50 after one tick at e = 2, and the comment at `tests/test_pid.py:114` reads "600 → clamp to 50".
- The I-term can contribute at most `ki·integral_max = 5 °C`. Steady-state SWT is therefore at most `40 + Kp·e + 5`.
- The house needs more than that. Its own weather curve in `apps/apps.yaml` (`base 25, slope 1.2, comfort_ref 20`) commanded about 49 °C at 0 °C outdoors. Fixed PID can only reach that with a sustained zone error of about 4 °C.
- Retro trace of `evaluate_demand` (example bounds, dt = 300): e = +0.2 → ∫ goes 0 → 50 in one tick. Then e = −0.1 → ∫ goes 50 → 20 → −10, and the command swings from 45.2 to 40 within three ticks.
- Prevention: the numeric defaults were frozen at planning (`.memlog.md` D12) with no check on units or steady-state authority. Four stories and four reviews then tested *around* the rail without questioning it.

**SR2 — The R7 "equal to last commanded" skip stops the App from repairing external plant drift, and it advances ∫ without any plant write.** *Decision needed (reconcile R7).*
- Source: `hvac_app.py:119-122` returns before `_write_setpoint` reads the plant. Before the epic there was no `_last_commanded` (`git show dcedf7d:apps/ha_smart_hvac/hvac_app.py`): every tick compared against the live plant value, so drift healed within one tick.
- If a person, another automation or the boiler integration changes the setpoint while the rounded command holds, the App never writes it back.
- The same path advances ∫ even when the plant entity is unavailable. This contradicts commit `19b5b33` ("Advance integral only after a successful plant write"). `tests/test_hvac_app.py:462-478` locks the advance with the plant at 45 and a command of 42.
- The 1.1 review rejected the two-layer skip as "R15 false — intentional" without discussing drift.
- Proposed reconciliation: skip only when `command == last_commanded` **and** the plant reads `command`. Otherwise let `_write_setpoint` decide.

**SR3 — An event can turn the boiler off, but only the next tick can turn it back on.** *Decision needed (accept or reconcile R6).*
- Source: `hvac_app.py:85-95` with `_gate_prelude` at 60-76. The event path writes 0 and clears ∫ on idle, no-zones or plant-off. On demand it does nothing (1.2 frozen intent).
- Any of these causes an off gap of up to `control_interval` and resets ∫:
  - a TRV `hvac_action` flap (heating → idle → heating);
  - a zone sensor blipping `unavailable` on the only demanding zone (the A1 skip makes demand false);
  - Plant Management being switched on.
- The default `control_interval` also went from 60 s (`dcedf7d` `config.py:104`) to 300 s.
- This complies with R6 as written. The latency and the reset-on-blip are recorded nowhere: not in the epic file, not in the 1.2 I/O matrix.

**SR4 — The live house commission was not migrated, and the parser accepts the stale config silently.** *Fix now (operator, before any Exclusive Session).*
- The epic Boundaries name `apps/apps.yaml` as a touch point. Yet `apps/apps.yaml` still contains `outdoor_temperature`, `weather_feedforward`, `control_interval: 60` and `setpoint_min: 42`, and has no `base_water_temp` or `pid`.
- The 1.3 decision (option 1) made legacy keys silently ignored, and `config.py` has no unknown-key check. The implicit `base_water_temp` 40 sits below that house's floor of 42.
- Mitigation in place: an operator HITL note in `epic-pid-domain-docs.md` Notes says not to commission live until epic 2 closes.
- Policy: the AGENTS.md rule "ask before changing house entity IDs" covers entity IDs, not these numeric keys.

**SR5 — `knowledge/` has no owner in epic 2.** *Fix now (Sofia).*
- `deferred-work.md` (the 1.3 and 1.4 entries) hands `knowledge/` to epic 2.
- `epic-pid-domain-docs.md` Description, Boundaries and Done when name only `docs/adr/`, `CONTEXT.md` and `AGENTS.md`.
- These files still describe weather-curve SWT or Outdoor as an input: `knowledge/concepts/set-water-temperature.md:15`, `outdoor-temperature.md`, `adrc.md:17`, `critical-zone.md`, `multi-zone-coordinator.md` and `index.md:17`.

**SR6 — The release metadata understates the change.** *Defer (low).*
- `CHANGELOG.md` v1.7.0 lists only `a66917e` (fix) and `30fa193` (chore). The 1.2 behavior commit `b0e1b6a` `feat(hvac): make demand SWT tick-owned…` is missing.
- The removal of the whole FF/CAP-7 law, of `ff_auto_correct_state.json` and of required keys (`a305049`, type `refactor`) shipped as patch v1.7.1.
- No commit in the epic carries a `BREAKING CHANGE:` footer, although the `control_interval` default changed from 60 to 300.

### Pattern divergence

**PD1 — Commission values parse inconsistently, so a bad value crashes the App or is accepted silently.** *Fix now.*
- Zone `weight` wraps `float()` in `ConfigError` (`config.py:39-45`). `pid.*`, `base_water_temp` and `control_interval` do not (`config.py:63-69, 89-93`).
- `initialize` catches only `ConfigError` (`hvac_app.py:21-25`). A value like `pid: {kp: "abc"}` raises a raw `ValueError`, and no listeners or tick are registered.
- Also accepted:
  - `nan`/`inf` gains and bounds: `clamp(nan, lo, hi)` returns `hi`, so every demand tick commands `setpoint_max`;
  - negative `kp`/`ki`;
  - an integral range that excludes 0;
  - `base_water_temp` outside `[setpoint_min, setpoint_max]`.
- The 1.1 review hardened non-finite *readings* but not commission values, although commit `19b5b33` claims "reject … bad weight/integral commission".
- Lenses: adversarial and edge-case both raised this (overlap).

**PD2 — CAP-era naming remains in runtime code after the sweep.** *Defer (fold into epic 2).* `hvac_app.py:58` still has the docstring "Shared CAP-1…CAP-3 prelude", and `_hands_off` is now a one-line log wrapper.

### Duplication map

**DU1 — "Write 0 + clear + log" is implemented three ways.** *Defer (low).* The three copies are `_go_idle` (`hvac_app.py:143-146`), the inline no-demand block in `_gate_prelude` (`hvac_app.py:70-74`, pre-epic) and the 1.1 weight-unusable branch in `_run_demand` (`hvac_app.py:112-116`). The third is the same as `_go_idle(…)`.

### Architecture delta and size growth

**AD1 — The structure is clean.** *Accept (positive).*
- The package shrank from 759 to 556 lines.
- `feedforward.py` and `ff_auto_correct.py` were deleted. The new `pid.py` is pure and depends only on `models`.
- `hvac_app` imports `config`, `coordinator`, `models` and `pid`; it used to import `feedforward` and `ff_auto_correct` as well. There are no cycles.
- `hvac_app.py` went from 269 to 233 lines, and `tests/test_hvac_app.py` from 1007 to 688. No file is a god-class candidate.

### Lens: verification gap

All four are confirmed: the mutation survived all 82 pid/app/config/coordinator tests, and the retro re-checked each one with grep. All four are **fix now (tests)**.

- **VG1 — Kp is never exercised.** It is never anything other than 1.0 when the law is evaluated (`tests/test_pid.py:35`, `tests/test_hvac_app.py:16`). The mutant `u_pid = e + ki*∫` passes.
- **VG2 — No app test carries ∫ across ticks.** Every demand test starts at `_integral = 0` and checks a single tick. The mutants `integral=0.0` and `ki=pid.kp` in `_run_demand` pass, so a P-only controller would go unnoticed (Done when 1).
- **VG3 — The `integral_min` clamp is never reached.** It is not hit at unit level or app level, and the mutant `min(∫+e·dt, integral_max)` passes.
- **VG4 — The equal-rounded skip test sits exactly on the 0.1 grid** (raw 42.0 at `tests/test_hvac_app.py:462`). A pre-rounding compare would pass, so R7 is not locked.

### Lens: edge case

- **EC1 — Rounding after the clamp can exceed `setpoint_max`.** `pid.py:84` rounds after clamping, so bounds with more than one decimal (for example 55.06 → 55.1) break C1. *Defer (low).*
- **EC2 — Weight-0 zones are accepted.** Demand from weight-0 zones goes to idle on a tick but is a no-op on an event. *Accept*: it is designed in the 1.1 I/O matrix ("Zero weight sum → idle") and in the 1.2 decision ("weight-unusable fail stays tick-only"). A parse-time guard against an all-zero weight sum is optional.
- **EC3 — The fail-safe that idled on unavailable outdoor was removed.** *Accept*: this is R4 by design.

### Dropped after re-check

- The lazy-init guard `_ensure_corrector` was removed, so a callback could raise `AttributeError`. Dropped: when `initialize` returns early on a config error, it registers no listeners and no tick (`hvac_app.py:21-34`).
- After 1.4, event immunity from the ∫ step "rests on convention, no failing test". Dropped: `test_demand_event_no_write_no_integral_change` and `test_tick_then_demand_event_leaves_integral_and_last` lock it.
- "About 170 vendored tooling files in the epic diff." Dropped: 188 of the 216 files come from PR #87 (`417efe8`), a separate chore PR between 1.3 and 1.4 and outside every story's range. Only `_bmad-output/party-mode/memories/installed/.memlog.md` (+16) landed inside 1.1.

### Process lessons

- **PL1 — The quick build review consistently left patch-worthy defects.** All four plans pin `review: quick` (one lens), including the high-risk 1.1 and 1.2. Every story's separate code review then found more patches:
  - 1.1: 8 patches (including the NaN poisoning of ∫ and the ∫ advance on a failed write);
  - 1.2: 3 patches;
  - 1.3: 4 patches and 2 decisions;
  - 1.4: 5 patches, including two vacuous tests confirmed by hand mutants (1.4 review log `e31f7d8b` L318, commit `40eb190`).

  Lesson: for high-risk tickets, treat the full code review as mandatory, or do not pin `quick`.
- **PL2 — AGENTS.md contradicted the runtime for the whole epic.** The docs drift was re-deferred in three consecutive reviews (1.2, 1.3, 1.4). Meanwhile `AGENTS.md:32-35`, which loads into every agent session, kept telling agents that `ff_auto_correct_state.json`, `weather_feedforward.auto_correct` and CAP-8 event `clamp(u_ff)` writes are live. Lesson: agent-context conventions should change in the same change as the code they describe. Slicing them into a later docs epic leaves every intervening session misinformed.
- **PL3 — The planning numbers were never sanity-checked against units or the plant** (see SR1). Lesson: tuning constants frozen in an epic constraint need a short dimensional and steady-state check at refinement.
- **PL4 — Evidence for 1.1–1.3 is thin.** Those stories were built in Cursor and left no session logs, so process analysis for them rests on plans and commits only. Lesson: keep a session reference per ticket.
- **PL5 — Minor tooling issues.** In the 1.4 build (`9cf62282` L197-210), `git push … | tail -3` hid an SSH `Permission denied`, which was resolved by pushing over HTTPS. The branch was then left without upstream tracking.

## Behavior verification

- **Not exercised end to end in AppDaemon.** Running `./scripts/run-appdaemon` requires an Exclusive Session with the Production add-on stopped (ADR 0001). That was not established, and the house yaml is not migrated (SR4), so a live run would also have tested the wrong commission.
- **Exercised instead:**
  - `uv run pytest` at `39e6e75` (130 passed), which covers the app with a mocked Hass;
  - the mutation runs from the verification-gap lens;
  - a retro multi-tick trace of `pid.evaluate_demand` with the C4 defaults under the example bounds and the live bounds, which demonstrated SR1.
- The gate, listener and tick/event behavior is therefore verified at unit and app-mock level only. Closed-loop behavior against the real plant is unverified.

## Previous-retro follow-through

There was nothing to follow through on because no previous retrospective file exists. `epic-fixed-pid-swt` is the first epic of `initiative-pid` (id 1, `after: []`, per `tickets.py status`).

## Action items

Everything below is proposed. None of it has been applied. Code fixes go through the normal dev loop (`bmad-build`). Spec changes go through Sofia (`bmad-agent-po`), confirmed by the user.

| # | Action | Kind | Owner | From |
|---|--------|------|-------|------|
| A1 | Retune the fixed-PI commission with explicit units. Decide what `ki` and the integral bounds are measured in. Size `ki·integral_max` to the SWT authority the house needs; its weather curve asked for about 49–60 °C on a base of 40. Reconcile epic C4 and the initiative decision D12 to the new numbers. Update `models.py` defaults, `apps.yaml.example` and `docs/house-calibration.md`. Add a multi-tick test with small `e` that does not hit the rail. | spec reconciliation + remediation | Sofia (C4/D12) → dev | SR1, PL3 |
| A2 | Reconcile R7: skip the plant call only when the rounded command equals `last_commanded` **and** the plant entity reads that value. Do not advance ∫ when the plant entity is unavailable. Add tests for drift repair (last 45, plant 50 → write 45) and for plant-unavailable equal-skip (∫ unchanged). | spec reconciliation + remediation | Sofia (R7) → dev | SR2 (user chose *reconcile*) |
| A3 | Harden commission parsing. Wrap every numeric key in `ConfigError` (`pid.*`, `base_water_temp`, `control_interval`). Require finite values, `kp ≥ 0`, `ki ≥ 0`, an integral range that contains 0, and `setpoint_min ≤ base_water_temp ≤ setpoint_max`. Add parse tests. | remediation | dev | PD1 |
| A4 | Close the test gaps: a test with `kp ≠ 1`; an app test that carries ∫ across two ticks; a test that reaches `integral_min`; an equal-rounded skip whose raw value is off the 0.1 grid. | remediation (tests) | dev | VG1–VG4 |
| A5 | Before any Exclusive Session, migrate the non-entity keys in `apps/apps.yaml`: add `base_water_temp` (≥ `setpoint_min` 42) and `pid`, set `control_interval` (300, or keep 60 deliberately once A1's units are settled), and remove `outdoor_temperature` and `weather_feedforward`. Optional code part: log a WARNING for unknown or legacy top-level and `pid.*` keys. | operator + remediation | operator (Denys Zhmachenkov); dev for the WARNING | SR4 |
| A6 | Add `knowledge/` (concepts `set-water-temperature`, `outdoor-temperature`, `adrc`, `critical-zone`, `multi-zone-coordinator`, `index`) to the Boundaries and Done when of `epic-pid-domain-docs`. | spec reconciliation | Sofia | SR5 |
| A7 | Hand epic 2's superseding ADR its inputs: tick-owned demand with clear-only events, **including** the accepted demand-onset latency (up to `control_interval`) and the ∫ reset when a TRV flaps or a sensor blips (SR3, accepted by the user); anti-windup as integral clamps plus a same-sign saturation freeze; and the ∫-vs-write rule as revised by A2. | spec reconciliation | Sofia (epic 2 refinement) | SR3, Decision records |
| A8 | Land the AGENTS.md convention fixes first in epic 2, before any other docs work. Process rule for future slicing: conventions in AGENTS.md change in the same PR as the code they describe. | process | Sofia / team (`bmad-project-context` for AGENTS.md) | PL2 |
| A9 | Do not pin `review: quick` on high-risk tickets, or keep the separate multi-lens code review mandatory for them. | process | team | PL1 |
| A10 | Give config-breaking changes a `BREAKING CHANGE:` footer. Find out why `b0e1b6a` (feat) is missing from the v1.7.0 notes. | remediation (release hygiene) | dev | SR6 (deferred) |

A1–A4 are the open items with the highest priority; A1, A3 and A5 block live commissioning. They fit in one follow-up story in this epic, for example "1.5 PID commission and skip hardening". Sofia decides the slicing. Deferred and not in the table: PD2 (CAP docstring, to epic 2), DU1 (idle-path duplication), EC1 (rounding vs bounds with more than one decimal). Accepted and not to be flagged again: EC2 (weight-0 idle on tick only), EC3 (outdoor fail-safe removed by R4), SR3 (latency accepted by the user and documented via A7).

## Decision records

The decision test was applied to the plans' frozen blocks, Design Notes and Implementation Notes. Three decisions pass: hard to reverse or surprising, the result of a real trade-off, and not recorded in any ADR (ADR 0004 still describes CAP-8).

1. **Demand SWT is tick-owned and events only clear.** Source: 1.2 plan frozen intent; commit `b0e1b6a`. The plan records the why: R5/R6, keeping the integral consistent with `dt`.
2. **Anti-windup is integral clamps plus a same-sign SWT saturation freeze.** Source: 1.1 plan, Plan Change Log "party C2", Design Notes; commit `f09eb2c`.
3. **∫ advances on the equal-rounded skip but not on a failed write.** Source: 1.1 Code Review "decision A"; commit `19b5b33`. A2 will revise this rule.

**User decision:** do not write separate ADR files now. Pass all three to epic 2, which owns the new ADR that supersedes 0004 (action item A7). **No decision-record files were written.**

## Acceptance verdict

**Verdict: accepted-with-open-items**, confirmed by the user. The user first chose **rejected**, then revised the decision to accepted-with-open-items, which matches the machine verdict. Criteria: **declared** (epic Requirements R1–R9, Constraints C1–C4, Done when 1–6).

- Evidence for the criteria:
  - Done when 1–6 are each met in code and locked by tests at `39e6e75` (130 passed; ruff clean; the absence greps from plans 1.3/1.4 are empty).
  - `pending_tickets` is empty, and no ticket is still at `built`.
- Open items, tracked as action items:
  - SR1 / A1: the I-term authority is capped at ±5 °C, and ∫ rails in a single tick. The epic's Outcome ("The house holds zone comfort…") is not achievable with the shipped default commission.
  - SR2 / A2: the R7 skip does not repair plant drift.
  - SR4 / A5: the house yaml has not been migrated.
  - PD1 / A3: a malformed commission value crashes the App.
  - VG1–VG4 / A4: test gaps.
  - SR5 / A6: `knowledge/` has no owner.
  - Closed-loop behavior was never exercised (see Behavior verification).
- Live commissioning stays blocked: until A1, A3 and A5 land, and epic 2 closes per its operator HITL note.
- Closing the epic or changing any ticket state is Sofia's job, confirmed by the user. This retrospective changed no status.

## Open questions

- ~~Is the Production AppDaemon add-on already running v1.6.0 or later?~~ **Answered (user): Production runs v1.5.1**, the pre-epic weather-curve law. The house is not affected by SR1, SR4 or PD1 today. Do not upgrade Production to v1.6.0 or later until A1, A3 and A5 have landed and epic 2 has closed (operator HITL).
- **What SWT authority and integral units should A1 target?** This needs house data or a decision: for example the coldest-day SWT, and whether to integrate in °C·s, °C·min or °C·h. The answer sets A1's numbers and whether `control_interval` changes rescale the effective Ki.
- **Should the release history be corrected?** For example, a note on v1.7.1 that it was in effect a breaking config change, or should SR6 only apply going forward?
- **Unresolved by this retrospective:** process lessons for 1.1–1.3 (no session logs), and closed-loop behavior on the real plant (not exercised).
