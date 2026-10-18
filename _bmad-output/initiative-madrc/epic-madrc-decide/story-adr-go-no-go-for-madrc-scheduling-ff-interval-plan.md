---
title: 'ADR go/no-go for MADRC, scheduling, FF, interval'
type: 'feature'
ticket: '6'
created: '2026-10-18'
status: built
baseline_revision: 'fe27b358f6b8f895a6dfadbb36aa250dd9a75ebe'
route: 'full'
route_source: 'auto'
review: 'quick'
review_source: 'pinned'
lenses_ran: ['quick']
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/initiative-madrc/epic-madrc-decide/story-classify-swt-command-jumps.md'
  - '{project-root}/_bmad-output/initiative-madrc/epic-madrc-decide/story-compare-control-interval-candidates.md'
  - '{project-root}/_bmad-output/initiative-madrc/epic-madrc-decide/story-compare-weather-feedforward-on-vs-off.md'
  - '{project-root}/docs/adr/0002-ladrc-critical-zone-control.md'
  - '{project-root}/docs/adr/0003-online-ladrc-omega-c-auto-tune.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** R2/R3/R7 still have no single ADR that records go/no-go for \(G_{cp}\), \(k_p\)/\(T\) scheduling (including without-\(G_{cp}\)), ωc coexistence, regime signal, `control_interval`, Weather Feedforward keep/drop, and online \(b_0\)/ωo — so epics 2–3 and entries 7–8 lack named handoffs.

**Approach:** Write new **`docs/adr/0004-*.md`** as the decision record (all R2/R3/R7 fields + handoffs); thin cross-links only in 0002/0003 — decision prose only; no App/YAML/CONTEXT apply here.

**Decisions:**
- ADR vehicle: **new 0004** decision record; 0002/0003 get **thin** «see 0004» / Out-of-scope pointers only (party: rolled back from amend-in-place).
- \(G_{cp}\): **go** as **build authorization** for epic-madrc-compensator — **not** a verified superiority claim. Cite R1 class **(c)** (lag family implicated) and spike Screen 3 R2 stub (no compensated-vs-baseline run yet). Epic 2 unit/sim must prove or refuse improvement.
- \(k_p\)/\(T\) scheduling: **go** (epic-madrc-scheduling may implement).
- Scheduling without \(G_{cp}\): **forbidden** — epic 3 stays gated on epic 2; scheduling \(T\) is the compensator plant-channel \(T\).
- ωc vs ADR 0003: **coexist** (online ωc auto-tune stays; scheduling does not replace it).
- Regime signal: **outdoor**.
- `control_interval`: **30** (R3 recommend; apply in entry 1.8). Reject 120 at fixed ωo/n_sub without retune.
- Weather Feedforward: **drop** (entry 1.7 applies remove/disable) as **policy despite** R7 non-material Δ%≈0 on clamp-dominated verifying pins — **not** a claim that R7 proved FF worthless. Residue-at-zero = `command` when \(u_{ff}=0\).
- After FF drop: outdoor **may still** be the scheduling regime signal (not an additive \(u_{ff}\) baseline).
- Online **ωo** remains closed.
- Online **\(b_0\)**: **open as intended follow-on** (adaptation like ωc). Owning home: stub **`[[epic]]` `epic-online-b0`** in `_bmad-output/initiative-madrc/tickets.toml` (id=4; no stories this story). **Must not** implement online \(b_0\) in epic 2/3 or entries 1.7/1.8. Stub `after`: epic 3 (post scheduling) so structure lands first; slice stories later.

## Boundaries & Constraints

**Always:**
- Put **every** ticket decision field + handoff list in **0004** (single accept target), including **`epic-online-b0`** and an explicit fence: online \(b_0\) **out of** epic-madrc-compensator, epic-madrc-scheduling, and entries 1.7/1.8.
- Add stub `[[epic]]` id=4 `slug = "epic-online-b0"` to initiative `tickets.toml` (title + `after` on epic 3; empty/minimal covers; no story files / no epic folder required in 1.6).
- ADR \(G_{cp}\) prose **must** separate diagnosis from treatment: R1 (c) implicates lag; **go = authorization to build**; must **not** claim verified improvement over baseline until epic-2 evidence exists; name Screen 3 R2 stub explicitly.
- ADR FF prose **must** state **drop = policy despite** non-material Δ% / clamp-dominated pins; must **not** claim R7 proved FF worthless; outdoor-as-regime explicit for scheduling.
- 0002: append (or replace the additive-FF sentence with) an explicit supersession line, e.g. *«Weather Feedforward keep/drop and post-drop residue / outdoor-as-regime are decided in ADR 0004; additive \(u_{ff}\) baseline is no longer current policy.»* — do not rewrite Critical Zone / continuous-form / Huang paragraphs wholesale.
- 0003: Out-of-scope — replace parked «MADRC inertia compensator» with pointer to 0004 go/authorization; note ωc **coexist**; \(b_0\) follow-on → `epic-online-b0` via 0004.
- Initiative `tickets.toml` epic 3 `after`: keep aligned with without-\(G_{cp}\)=**forbidden** (no «skip this gate» branch).
- Cite: `story-classify-swt-command-jumps.md` (R1 class **(c)**); `story-compare-control-interval-candidates.md` (recommend **30**; reject 120); `story-compare-weather-feedforward-on-vs-off.md` (Δ%≈0; residue-at-zero=`command`); spike note that Screens are comparison language only (no auto go/no-go).
- Match existing ADR prose style (H1 + normative must; 0003-style `##` OK). Epic Notes → **0004** (and mention thin 0002/0003 links).
- User accepts the **0004** draft before this story is done (ticket `hitl` / verify).

**Never:**
- Production App/LADRC/FF code, example YAML, `house-calibration.md` apply, CONTEXT/AGENTS refuse-path (entries **7–8** / R8/R6).
- Implement \(G_{cp}\) or scheduling (epics 2–3). Exclusive Session / field trials. Invent compensated-vs-baseline metrics (Screen 3 R2 still stub).
- FF auto-tune. Silent default go for MADRC because R1 is class (c). Claim «R1 proves \(G_{cp}\)» / «go = already better». Claim «R7 Δ%≈0 proves drop» / «FF worthless».
- Fold the full decision dump into 0002 or 0003 (rejected vehicle). Leave 0003 saying only «MADRC parked» with no 0004 pointer.
- Ship online \(b_0\) tuner code or full epic slice/stories in 1.6. ADR-only ghost without toml stub (rejected).

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Decision fields complete | Frozen decisions + evidence cites | **0004** states every R2/R3/R7 field + handoff list | Missing field → not ready for user accept |
| Cross-links | 0002/0003 after edit | Thin see-0004 / Out-of-scope only; plant/ωc history intact | No orphan «MADRC parked» without pointer |
| Evidence-backed interval | R3 artifact recommend 30 | 0004 records interval **30** + Euler/ωo/substep; apply deferred to 1.8 | Do not edit YAML here |
| FF policy | R7 Δ%≈0 clamp-dominated; residue=`command` | 0004 **drop as policy despite** non-material Δ%; residue + outdoor-as-regime | No metric-gate drop wording |
| MADRC without \(G_{cp}\) evidence | R1 (c); Screen 3 R2 stub | 0004 **go as authorization**; cites gap | No «R1 proves \(G_{cp}\)» |
| Downstream handoffs | Decisions frozen | Named handoffs for epic 2/3, 1.7/1.8, stub `epic-online-b0`, harness; \(b_0\) fenced out of 2/3/1.7/1.8 | Vague “later” → fail verify |
| \(b_0\) stub | initiative tickets.toml | `[[epic]]` id=4 slug epic-online-b0 present; after epic 3 | No stories required in 1.6 |

</frozen-after-approval>

## Code Map

- `docs/adr/0004-madrc-ff-interval-go-no-go.md` — **new** decision record; all fields + handoffs.
- `docs/adr/0002-ladrc-critical-zone-control.md` — **thin** supersession sentence on additive FF → 0004 (keep Critical Zone / continuous-form / Huang prose).
- `docs/adr/0003-online-ladrc-omega-c-auto-tune.md` — **thin** Out-of-scope: MADRC → 0004; ωc coexist; online \(b_0\) → `epic-online-b0` via 0004.
- Evidence (cite only): R1/R3/R7 stories + spike Screen 3 R2 stub.
- `tests/harness/runner.py`, `tests/harness/plant.py`, `tests/test_plant_lag_harness.py` — harness handoff paths (name in 0004; do not change).
- `_bmad-output/initiative-madrc/epic-madrc-decide/epic-madrc-decide.md` — Notes → 0004.
- `_bmad-output/initiative-madrc/tickets.toml` — stub epic 4 `epic-online-b0` (`after` epic 3); epic 3 `after` needs already forbid without-\(G_{cp}\) skip (sync in this story if drifted).
- `_bmad-output/initiative-madrc/epic-madrc-decide/tickets.toml` entry id=6 — description/verify aligned with 0004 + frozen Intent (board sync).

**Do not change:** App packages; example YAML; house-calibration apply; CONTEXT/AGENTS; harness/R1/R3/R7 test modules.

## Tasks & Acceptance

**Execution:**
- [x] `docs/adr/0004-madrc-ff-interval-go-no-go.md` — full decision record + evidence cites + handoff list + \(b_0\) fence — ticket verify / frozen Intent
- [x] `docs/adr/0002-ladrc-critical-zone-control.md` — supersession sentence: additive FF no longer current policy → see 0004 — coherence
- [x] `docs/adr/0003-online-ladrc-omega-c-auto-tune.md` — thin Out-of-scope → 0004; coexist note — coherence
- [x] `_bmad-output/initiative-madrc/tickets.toml` — stub `[[epic]]` id=4 `epic-online-b0` after epic 3; epic 3 `after` needs without-\(G_{cp}\) skip removed — tree + gate
- [x] `_bmad-output/initiative-madrc/epic-madrc-decide/tickets.toml` — entry 6 description/verify match 0004 + frozen Intent — board sync
- [x] `_bmad-output/initiative-madrc/epic-madrc-decide/epic-madrc-decide.md` — Notes bullet → 0004 — discoverability

**Acceptance Criteria:**
- Given **frozen Intent** Decisions, when **0004** is opened, then every decision field there is present as normative prose (single accept target) — including \(G_{cp}\) **authorization**, FF **policy despite**, without-\(G_{cp}\)=forbidden, outdoor regime, interval 30, ωc coexist, ωo closed, `epic-online-b0` fence out of epic 2/3 and 1.7/1.8.
- Given 0002 and 0003, when opened, then each has a thin pointer to 0004; 0002 does not leave additive FF as silent current policy; 0003 does not leave «MADRC forever parked» without 0004 pointer.
- Given initiative `tickets.toml`, when read, then stub epic **`epic-online-b0`** (id=4) exists with `after` on epic 3, and epic 3 `after` has **no** «skip if without-\(G_{cp}\) allowed» branch; no \(b_0\) story files required in this PR.
- Given entry 6 in epic `tickets.toml`, when read, then description/verify name **0004** and match frozen Intent (not amend-0002/0003 / not b0+ωo both closed).
- Given 0004 handoffs, when read, then they name go flags, interval **30**, regime **outdoor**, ωc **coexist**, without-\(G_{cp}\)=forbidden, **`epic-online-b0`**, and harness (`tests/harness/…`).
- Given R1/R3/R7 artifacts, when cited in 0004, then class (c), recommend-30 / reject-120, residue-at-zero=`command` appear; Screen 3 R2 stub named.
- Given this PR diff, when reviewed, then no App/YAML/CONTEXT/house-calibration-apply / harness behavior changes; 0002/0003 diffs stay thin.
- Given user accept of **0004**, when this story closes, then epic Notes points at 0004.

## Implementation Notes

## Plan Change Log

## Review Triage Log

| finding | verdict | evidence |
|---------|---------|----------|
| 0004 Screen 3 R2 stub cited as bare `spike-metrics-…md` (unresolvable from docs/adr or repo root) | medium | Confirmed: only path is `_bmad-output/initiative-madrc/epic-madrc-decide/spike-metrics-for-jump-madrc-and-ff-decisions.md`; R1/R3/R7 cites in same ADR use full `_bmad-output/…` paths. Routed **patch**. |
| epic-madrc-decide Notes still say epic-3 `after` on epic 2 is “conditional on that ADR” | medium | Confirmed at Notes line still present; ADR 0004 + initiative `tickets.toml` now forbid without-\(G_{cp}\) with no skip. New 0004 Notes bullet leaves the old “conditional” claim contradictory. Routed **patch**. |

## Design Notes

**Vehicle (party 2026-10-18):** Rejected full amend of 0002+0003. **0004** = decision door; 0002/0003 thin pointers.

**Evidence gap / party:**
- \(G_{cp}\): **go = build authorization** — not verified superiority; name Screen 3 R2 stub.
- FF: **drop = policy despite** R7 Δ%≈0 / clamp-dominated pins — not «R7 proved worthless»; outdoor remains regime.
- \(b_0\): stub epic in toml (not ADR-only ghost); fence out of 2/3/1.7/1.8; `after` epic 3.

**0004 skeleton:** Context (R1/R3/R7 cites) → Decisions (`##` per field) → Handoffs (epic 2/3, 1.7/1.8, `epic-online-b0`, harness) → Out of scope (no production structure here; no R6 apply).

**Board sync (plan review 2026-10-18):** entry 6 description/verify + initiative epic 3 `after` updated to match frozen Intent (0004 vehicle; without-\(G_{cp}\) no-skip; online \(b_0\) stub).

## Verification

**Commands:**
- `test -f docs/adr/0004-madrc-ff-interval-go-no-go.md` — expected: 0004 exists
- `rg -n "G_cp|scheduling|control_interval|Feedforward|b0|ωo|handoff|harness|outdoor|authorization|policy despite" docs/adr/0004-madrc-ff-interval-go-no-go.md` — expected: fields + framings present
- `rg -n "0004" docs/adr/0002-ladrc-critical-zone-control.md docs/adr/0003-online-ladrc-omega-c-auto-tune.md` — expected: thin pointers
- `rg -n "epic-online-b0" _bmad-output/initiative-madrc/tickets.toml` — expected: stub epic present
- `rg -n "skip this gate" _bmad-output/initiative-madrc/tickets.toml` — expected: no matches (without-\(G_{cp}\) skip removed)

**Manual checks:**
- User accepts **0004** draft (entry 6 verify / frozen Intent).
- Diff: 0002/0003 thin; toml stub epic 4 + epic 3 needs + entry 6 sync; no App/YAML/CONTEXT/calibration-apply/harness edits; no \(b_0\) stories.
- Epic Notes → 0004.
