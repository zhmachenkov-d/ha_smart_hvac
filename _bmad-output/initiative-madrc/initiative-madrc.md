---
tracker_id: ""
key: ""
type: initiative
title: "MADRC for high-order plant lag"
parent: none
covers: [R1, R2, R3, R4, R5, R6, R7, R8]
after: []
assignee: ""
risk: high
estimate: ""
estimate_basis: ""
---

# MADRC for high-order plant lag

## Description

Decide whether the ADRC Controller should use Modified Active Disturbance Rejection Control — an inertia compensator \(G_{cp}\) on the ESO command path, plus optional gain/time-constant scheduling — for this house’s high-order / delayed OpenTherm plant. Also decide whether Weather Feedforward (outdoor baseline \(u_{ff}\)) stays, is zeroed, or is removed, given that total-disturbance rejection may already absorb outdoor load. Observed Set Water Temperature jumps and the choice of `control_interval` are in scope for diagnosis and decision; success for this initiative is unit tests and/or offline simulation, not Exclusive Session field proof. If go, deliver the structures; if no-go, lock the refusal in an ADR with evidence so MADRC and FF policy stay explicit.

## Outcome

Maintainers know whether MADRC (compensator and/or \(k_p\)/\(T\) scheduling) belongs on this Plant, whether Weather Feedforward remains, with a recorded control_interval choice and a classified account of SWT jumps; the signal is an ADR plus failing-today unit/sim checks that pass under the chosen path (implement or explicit refuse).

## Requirements

- R1 — Diagnose Set Water Temperature jumps: with unit or simulation evidence, classify dominant causes among (a) tuning (`b0` / ωc / ωo / feedforward), (b) sample period / `control_interval`, (c) ESO \(u\)–\(y\) lag mismatch that MADRC targets, (d) other (Critical Zone switch, latch/guard, write path). Do not treat MADRC as the default fix.
- R2 — Go/no-go decision for (i) MADRC inertia compensator \(G_{cp}\) and (ii) adaptive scheduling of \(k_p\) (ωc) and compensation \(T\) vs an operating-regime analogue; record both in an ADR (new or amend 0002/0003). Online \(b_0\) / ωo adaptation remains out unless that ADR explicitly opens it.
- R3 — Select and document `control_interval` (and the coupled Euler / ωo / substep constraints) with unit or simulation justification for this Plant; update house-calibration and example config when the value changes.
- R4 — If R2(i) is go: implement \(G_{cp}\) on the ESO \(u\) path (\(u_f = G_{cp}u\)), configurable order/time-constant, with unit/sim proof of better observer alignment and/or milder commanded SWT motion vs baseline on a high-order lag plant model; if no-go, no production \(G_{cp}\) code.
- R5 — If R2(ii) is go: implement scheduling of \(k_p\) and \(T\) vs the chosen regime signal (outdoor / demand / other — decided under R2), leaving \(b_0\) and ωo fixed online; coexist with or replace ADR 0003 ωc auto-tune rules as the ADR states; if no-go, no scheduling code.
- R6 — CONTEXT, house-calibration, and agent context state the ADR outcomes for MADRC, Weather Feedforward policy, and how `control_interval` was chosen (no longer “undecided” silence).
- R7 — Go/no-go on Weather Feedforward: keep the outdoor \(u_{ff}\) baseline, or drop it (zero / remove path) and rely on LADRC/MADRC total-disturbance rejection; unit/sim compares tracking and SWT command motion with vs without FF. ADR records the choice and how known-input residue (`command − u_ff`) behaves when \(u_{ff}=0\). Outdoor Temperature may still exist as a scheduling regime signal under R2/R5 even if FF is dropped — say so explicitly.
- R8 — If R7 is drop: remove or disable Weather Feedforward in the App, config, and calibration docs, with unit/sim gates; if keep: no removal code, and house-calibration still documents manual FF tuning. Not Weather Feedforward *auto-tune* either way.

## Done when

1. R1 classification exists with cited unit/sim artifacts; jumps are not left as an unexamined “maybe MADRC” claim.
2. R2 ADR records go/no-go for \(G_{cp}\) and for \(k_p\)/\(T\) scheduling, and keeps online \(b_0\)/ωo closed unless explicitly opened.
3. R3 `control_interval` (and ωo/substep coupling) is documented and reflected in example/calibration docs.
4. R7 ADR records keep vs drop Weather Feedforward, including residue/`u_ff` semantics and outdoor-vs-scheduling relationship.
5. R4, R5, and R8 match the ADR: structures present with green unit/sim gates, or explicitly absent with no lingering stubs.
6. R6 docs/CONTEXT match the ADR; AGENTS.md / pitfall language no longer treats MADRC or FF policy as an open silent option.

## Boundaries

Capability boundary: ADRC Controller structure (ESO \(u\) path, optional gain/\(T\) schedule), Weather Feedforward keep/drop policy, `control_interval` selection, and diagnosis of commanded Set Water Temperature jumps. Not Exclusive Session field trials as the initiative gate; not Critical Zone selection redesign; not Weather Feedforward *auto-tune*; not HACS packaging; not online \(b_0\)/ωo unless R2’s ADR opens them. Tracer path: diagnose jumps + interval → ADR go/no-go (MADRC + FF) → FF drop if go → compensator if go → scheduling if go → docs.

- Touch point: `LadrcState` / ESO advance — consumed when wiring \(u_f\); owner: epic that implements R4
- Touch point: ADR 0003 ωc auto-tune — coexistence or replacement decided under R2; owner: opening decide epic
- Touch point: `feedforward` module / Weather Feedforward config — keep or remove under R7/R8; owner: opening decide epic
- Touch point: Plant clamps / OpenTherm write path — read for jump diagnosis; no epic owns a write-path redesign unless R1 forces one (then amend Boundaries)

## References

- concept — knowledge/concepts/madrc.md
- reference — knowledge/references/wang-2026-madrc-sst.md
- constraint — docs/adr/0002-ladrc-critical-zone-control.md (continuous-form ESO; known-input residue; Weather Feedforward additive; Huang gains forbidden)
- constraint — docs/adr/0003-online-ladrc-omega-c-auto-tune.md (ωc-only online; MADRC out of scope today; FF auto-tune out)
- calibration — docs/house-calibration.md §2–4 (`control_interval`, Euler ωo band, manual FF)
- language — CONTEXT.md (MADRC glossary; Weather Feedforward; undecided MADRC today)

## Notes

- Decision: 2026-10-17 — path A: go/no-go (spike + ADR) before production structure; user confirmed.
- Decision: 2026-10-17 — scope includes both \(G_{cp}\) and adaptive \(k_p\)/\(T\) scheduling (subject to R2); user confirmed.
- Decision: 2026-10-17 — verification ceiling is unit/simulation, not live Exclusive Session proof; user confirmed. “Production delivery” for Done when means merged App code + docs with green unit/sim gates, not field trials.
- Decision: 2026-10-17 — observed boiler carrier / Set Water Temperature jumps and control_interval selection are in initiative scope (R1, R3).
- Decision: 2026-10-17 — consider abandoning Weather Feedforward (R7/R8); not FF auto-tune; user requested.
- Decision: 2026-10-17 — no platform-baseline epic — brownfield LADRC/AppDaemon already runs; initiative opens with decide-first diagnosis and ADR.
- Decision: 2026-10-17 — slice approved: three epics (decide → compensator → scheduling); R6 refuse in decide, ship slices in 2/3; R7/R8 in decide; no separate FF epic; user confirmed.
- Decision: 2026-10-17 — whether \(k_p\)/\(T\) scheduling may ship without \(G_{cp}\) is settled in epic-madrc-decide ADR (R2); epic-madrc-scheduling’s after on compensator is conditional on that ADR.
- Assumption: scheduling regime analogue (outdoor vs demand vs other) is settled under R2, not presupposed as Wang’s electrical load \(P\).
- Open question: whether SWT jumps are primarily tuning/`control_interval` vs ESO lag mismatch — owned by R1; MADRC is one hypothesis, not the answer.
- Unknown: whether a no-go on MADRC still requires a separate command-rate / slew mitigation; park unless R1 names it.
- Decision: 2026-10-17 — repo ticketing store; `active_initiative` = `initiative-madrc`.
