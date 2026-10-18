# Walkthrough — PR #54: Compare Weather Feedforward on vs off

Target: [PR #54](https://github.com/zhmachenkov-d/ha_smart_hvac/pull/54) — branch `feat/madrc-1-5-compare-weather-ff`, commit `6aba90a`
Focus: human review of R7 FF-on vs zero_uff Screen-3 evidence (story 1.5)
Current block: closed — walkthrough complete; wrap-up done (walkthrough+memlog in `e68a365`; plan `done`; PR #54 MERGED; wrap-up log via PR #55)

## Blocks

- [x] **Intent** — done
- [x] **Broad strokes** — done
- [x] **Screen-3 metrics + scenarios** — done
- [x] **Evidence artifact + epic Notes** — done
- [x] **Periphery** — done

## Intent

Source: [story-compare-weather-feedforward-on-vs-off-plan.md](../epic-madrc-decide/story-compare-weather-feedforward-on-vs-off-plan.md) (frozen-after-approval Intent).

**Problem:** R7 needs unit/sim evidence comparing Weather Feedforward on vs `u_ff=0` on tracking and SWT command-motion metrics, plus residue semantics at zero — before any ADR keep/drop prose (entry 6).

**Approach:** On verifying pins, run FF-on vs `zero_uff=True` at two outdoor points (cold and hot), compute Screen-3 metrics (M1/M2/M4/M6) with relative Δ% vs X, and write a comparison artifact only — no keep/drop lean, no production FF changes.

**Decisions:**
- Pins (shared): `_example_aligned_config`, plant `K=0.45,T=300,n=3`, N=40, FF config `base=25,slope=1.2,comfort_ref=20`, reference=21. Within a scenario only `zero_uff` flips.
- Outdoor scenarios (HITL): **cold** `outdoor=0` (verifying-pin continuity; `u_ff=49` when FF-on); **hot** `outdoor=10` (milder; `u_ff=37` when FF-on). Both keep `u_ff` non-zero and below comfort clamp concerns.
- Baseline = FF-on (`zero_uff=False`); candidate = `zero_uff=True`. Per outdoor: report M1/M2/M4 absolutes + improvement Δ% vs that outdoor’s FF-on baseline; material iff Δ% ≥ **X=30%**.
- M6: always document sample variance of `command − u_ff`; on every zero path state residue-at-zero = `command` (observed as `command − 0`).
- Artifact + epic Notes pointer; own test module. Relative Δ only — **no keep/drop-lean** wording (ADR outdoor-vs-scheduling stays in entry 6).
- Duplicate M1/M2/M4/M6 + `delta_pct` locally (no `tests/harness/metrics.py`; do not import R1/R3).
- Token risk accepted (Keep full ~1773).

**Review notes (Intent):**
1. Frozen Intent matches shipped evidence-only scope — Never/Always held; `apps/` and harness tick contract untouched; no R1/R3/`metrics.py` imports.
2. Clamp-dominated Δ%≈0 is relative evidence already in the artifact, not an Intent miss; no renegotiation needed.

## Broad strokes

What the change is: R7 evidence-only — new test module + markdown compare artifact + epic Notes bullet; production and harness tick contract untouched.

Entry points (open in this order):

1. [tests/test_r7_weather_feedforward_compare.py](../../../tests/test_r7_weather_feedforward_compare.py) — local M1/M2/M4/M6; cold/hot × FF-on vs zero_uff
2. [story-compare-weather-feedforward-on-vs-off.md](../epic-madrc-decide/story-compare-weather-feedforward-on-vs-off.md) — Never-disclaimer → table → residue → citations
3. [run_closed_loop(..., zero_uff=)](../../../tests/harness/runner.py) — harness FF toggle (read-only reuse)
4. [epic-madrc-decide.md Notes](../epic-madrc-decide/epic-madrc-decide.md) — discoverability pointer
5. [story plan](../epic-madrc-decide/story-compare-weather-feedforward-on-vs-off-plan.md) — frozen Intent / AC

**Review notes (Broad strokes):**
1. Entry order test → artifact → harness hook → Notes → plan is sound for the evidence-only mechanism.
2. Harness is read-only reuse (`zero_uff`); Notes/plan OK as discoverability/contract anchors.

## Screen-3 metrics + scenarios

Mechanism: duplicate Screen-3 metrics locally; for each outdoor run FF-on baseline and `zero_uff` candidate via the harness hook; compute Δ% vs X=30%; assert finite series, pinned constant `u_ff`, residue-at-zero on zero paths, material labels, replay, and artifact cell parity.

- [evaluate_outdoors / metrics](../../../tests/test_r7_weather_feedforward_compare.py) — M1/M2/M4/M6 + `delta_pct` + material labels
- [test_cold_and_hot_finite_uff_and_residue_at_zero](../../../tests/test_r7_weather_feedforward_compare.py) — cold `u_ff=49` / hot `37`; zero path all 0; residue=`command`
- [test_screen3_metrics_match_artifact_absolutes_and_material_labels](../../../tests/test_r7_weather_feedforward_compare.py) — locked absolutes; Δ%≈0 / not material on these pins
- [test_same_outdoors_replay_same_metrics_and_labels](../../../tests/test_r7_weather_feedforward_compare.py) — replay stability

**Review notes (Screen-3 metrics + scenarios):**
1. Matrix covered; live `evaluate_outdoors` matches locked absolutes; Δ%≈0 / not material on these pins.
2. Cold ≡ hot on command metrics (clamp); M6=M2 when `u_ff` is constant — expected, not a soft assert.

## Evidence artifact + epic Notes

Mechanism: human-readable evidence for entry 6 later — relative Δ only, no policy lean.

- [story-compare-weather-feedforward-on-vs-off.md](../epic-madrc-decide/story-compare-weather-feedforward-on-vs-off.md) — Never-disclaimer, cold/hot table, Residue-at-zero, Citations
- [test_ff_compare_artifact_has_disclaimer_table_residue_citations](../../../tests/test_r7_weather_feedforward_compare.py) — string + locked-cell checks; bans keep/drop lean phrases
- [epic Notes bullet](../epic-madrc-decide/epic-madrc-decide.md) — points at the artifact

**Review notes (Evidence artifact + epic Notes):**
1. Skeleton + Notes + banned lean phrases verified by artifact test and manual checks.
2. Entry 6 named without policy lean — intentional framing, not a keep/drop recommendation.

## Periphery

- [deferred-work.md](../deferred-work.md) — notes unrelated party memlog left dirty beside this PR
- [story-compare-weather-feedforward-on-vs-off-plan.md](../epic-madrc-decide/story-compare-weather-feedforward-on-vs-off-plan.md) — build plan (`status: built`)

**Review notes (Periphery):**
1. Plan `status: built` is in the PR; memlog still dirty as deferred (not this story’s scope).
2. Walkthrough files still untracked — wrap-up commit candidate.
