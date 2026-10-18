# MADRC, scheduling, Weather Feedforward, and control_interval go/no-go

This ADR is the single decision record for R2/R3/R7 go/no-go fields and named handoffs to later epics and decide-epic apply stories. Screens and unit/sim artifacts are comparison language only — they do **not** auto-decide go/no-go. Production structure, YAML apply, and refuse-path docs are **out of scope** here.

## Context (evidence cited)

- **R1** (`_bmad-output/initiative-madrc/epic-madrc-decide/story-classify-swt-command-jumps.md`): Screen-2 class **(c)** — plant-lag family implicated. Evidence: `tests/test_r1_jump_classification.py`.
- **R3** (`_bmad-output/initiative-madrc/epic-madrc-decide/story-compare-control-interval-candidates.md`): recommend **30**; reject **120** at fixed ωo / `_ESO_EULER_SUBSTEPS=2` without retune. Evidence: `tests/test_r3_control_interval_candidates.py`.
- **R7** (`_bmad-output/initiative-madrc/epic-madrc-decide/story-compare-weather-feedforward-on-vs-off.md`): Δ% ≈ 0 on M1/M2/M4 on clamp-dominated verifying pins; residue-at-zero = `command` when \(u_{ff}=0\). Evidence: `tests/test_r7_weather_feedforward_compare.py`.
- **Screen 3 R2 stub** (`_bmad-output/initiative-madrc/epic-madrc-decide/spike-metrics-for-jump-madrc-and-ff-decisions.md`): baseline-vs-compensated compare contract exists; **no** compensated harness path or compensated-vs-baseline run yet.

Harness paths (unchanged by this ADR): `tests/harness/runner.py`, `tests/harness/plant.py`, `tests/test_plant_lag_harness.py`.

## \(G_{cp}\) (MADRC inertia compensator)

**Go as build authorization** for `epic-madrc-compensator` — **not** a verified superiority claim over baseline.

R1 class (c) implicates the plant-lag family; that is diagnosis, not proof that \(G_{cp}\) improves the plant. The Screen 3 R2 stub still has no compensated-vs-baseline run. Epic 2 unit/sim **must** prove or refuse improvement before treating \(G_{cp}\) as verified better. Maintainers **must not** read this go as “R1 proves \(G_{cp}\)” or “already better than baseline.”

## \(k_p\) / \(T\) scheduling

**Go** — `epic-madrc-scheduling` may implement regime scheduling of \(k_p\) and plant-channel \(T\).

## Scheduling without \(G_{cp}\)

**Forbidden.** Epic 3 stays gated on epic 2. Scheduling \(T\) **must** be the compensator plant-channel \(T\). There is no “skip this gate if without-\(G_{cp}\) allowed” branch.

## ωc coexistence (ADR 0003)

Online ωc auto-tune **coexists**. Scheduling does **not** replace ADR 0003. Thin pointer: see this ADR from 0003 Out-of-scope; plant/ωc history in 0003 stays intact.

## Regime signal

**Outdoor** temperature is the scheduling regime signal.

## `control_interval`

**30** (R3 recommend). Apply is deferred to entry 1.8 (YAML / house-calibration). Maintainers **must** keep Euler / ωo / `_ESO_EULER_SUBSTEPS=2` coupling in mind: **reject 120** at fixed example ωo without ωo↓ or substep retune.

## Weather Feedforward

**Drop** as **policy despite** R7 non-material Δ% ≈ 0 on clamp-dominated verifying pins — **not** a claim that R7 proved FF worthless. Entry 1.7 applies remove/disable.

Residue-at-zero = `command` when \(u_{ff}=0\) (R7). After FF drop, outdoor **may still** be the scheduling regime signal; that is not an additive \(u_{ff}\) baseline. Additive Weather Feedforward as current policy is superseded — see thin supersession in ADR 0002.

## Online ωo

**Closed.** Online Observer Bandwidth adaptation remains out of scope (unchanged from ADR 0003 intent).

## Online \(b_0\)

**Open as intended follow-on** (adaptation in the spirit of ωc). Owning home: stub epic `epic-online-b0` in `_bmad-output/initiative-madrc/tickets.toml` (id=4; `after` epic 3). Slice stories later.

Online \(b_0\) **must not** be implemented in `epic-madrc-compensator`, `epic-madrc-scheduling`, or decide-epic entries 1.7 / 1.8.

## Handoffs

| Downstream | What this ADR hands off |
|------------|-------------------------|
| `epic-madrc-compensator` (epic 2) | \(G_{cp}\) **go = authorization**; must prove/refuse vs baseline; Screen 3 R2 stub still open; harness at `tests/harness/…`; online \(b_0\) **out** |
| `epic-madrc-scheduling` (epic 3) | Scheduling **go**; regime = **outdoor**; ωc **coexist**; without-\(G_{cp}\)** forbidden** (gated on epic 2); online \(b_0\) **out** |
| Entry 1.7 (FF apply) | FF **drop** (policy despite R7); residue-at-zero = `command`; outdoor remains regime, not additive \(u_{ff}\); online \(b_0\) **out** |
| Entry 1.8 (interval / refuse-path docs) | `control_interval` = **30**; reject 120 without retune; MADRC/FF/interval outcomes from this ADR; online \(b_0\) **out** |
| `epic-online-b0` (stub epic 4) | Intended follow-on for online \(b_0\); `after` epic 3; no stories required in decide epic 1.6 |
| Harness | Reuse `tests/harness/runner.py`, `tests/harness/plant.py`, verifying pins in `tests/test_plant_lag_harness.py` — do not reinvent for epic 2/3 evidence |

## Out of scope

- Production App / LADRC / FF code, example YAML, house-calibration apply, CONTEXT / AGENTS refuse-path (entries 1.7–1.8 / R8/R6).
- Implementing \(G_{cp}\) or scheduling (epics 2–3). Exclusive Session / field trials.
- Inventing compensated-vs-baseline metrics beyond the Screen 3 stub; FF auto-tune; online ωo; shipping online \(b_0\) tuner code or full `epic-online-b0` story slice in this decide story.
