---
title: 'Domain docs for RLS retune'
type: 'chore'
ticket: '4'
created: '2026-11-09'
status: 'built'
baseline_revision: '30e500e2f0dac5602786271aca345b0e8f63484d'
route: 'full'
route_source: 'auto'
risk: 'medium'
review: 'quick'
review_source: 'pinned'
lenses_ran: ['quick']
review_loop_iteration: 0
context:
  - _bmad-output/initiative-pid/tickets/epic-rls-pid-retune/rls-adaptive-algorithm.md
  - docs/adr/0005-fixed-pid-swt.md
  - docs/house-calibration.md
---

<!-- Read order: 1 Intent → 2 Boundaries → 3 Code Map → 4 Tasks & Acceptance → 5 Verification -->

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Runtime RLS retune (entries 1–3) is shipped, but AGENTS / CONTEXT / ADR / knowledge still describe fixed-gain-only commissioning or call RLS “planned”, so agents and operators contradict the App.

**Approach:** Document the shipped adaptive path on those domain surfaces: optional `pid.adaptive` default off, YAML fixed `kp`/`ki` fallback when adaptive is off or unhealthy, `rls_state.json` separate from PID ephemeral clears, SWT law unchanged, Weather Feedforward / CAP-7 still absent. Add accepted ADR 0006 for optional RLS; surgically patch 0005 to cite it; add a short knowledge concept; narrow house-calibration’s “online retuning” bullet so deep λ/IMC knobs stay “not here” while `pid.adaptive` is not denied.

## Boundaries & Constraints

**Always:**
- Docs-only. No App / test / yaml schema changes except comments already owned by entries 1–3 (do not re-litigate rails, latch, persist dirty rules).
- State these facts everywhere the ticket `verify` requires (AGENTS, CONTEXT, ADR, knowledge): (1) adaptive optional, default off; (2) adaptive off or unhealthy → yaml fixed `kp`/`ki`; (3) RLS JSON state is separate from PID ∫ / `y_prev` clears — idle / plant-off / no-valid-zones / weights-unusable do not wipe the file; (4) Outdoor / Weather Feedforward / CAP-7 / `ff_auto_correct_state.json` stay off the water path.
- **OQ1 A + party S:** Add `docs/adr/0006-optional-rls-adaptive-pid.md` (`status: accepted`). Patch 0005 surgically only: drop intro “RLS planned / not current commissioning”, drop “shipping RLS gain retune” from Out of scope, cite 0006. Do not retitle 0005, do not rewrite fixed-PID SWT law / tick vs event / anti-windup / Critical Zone diagnostics-only body.
- **OQ2 A + party S:** Add short `knowledge/concepts/rls-adaptive-pid.md` (Outdoor-length: facts + Related/Citations, no ARX/IMC equations); update `knowledge/concepts/index.md`, `knowledge/index.md` (live path cites 0005 + optional 0006), and `set-water-temperature.md` body + frontmatter/index description so they no longer read fixed-gain-only.
- **OQ3 A + party N:** Narrow house-calibration “Online retuning of PID gains” under “What is not calibrated here” to deep RLS λ / IMC design knobs not calibrated there; point online Kp/Ki via `pid.adaptive` at the existing adaptive section — do not delete into silence that implies retune is absent, and do not claim adaptive is absent.
- **AGENTS party F:** In `bmad:context`, cite 0005 and 0006 under Where things are; put all four verify facts in Conventions (dense bullets OK); no RLS math. Update Verified stamp; stay inside the managed block.
- **CONTEXT party T:** Keep “fixed-gain” lead and existing gate/tick prose; replace only the “RLS … planned” tail with the four facts + cite 0006. Do not rewrite the whole PID glossary paragraph.
- **ADR 0006 party H (MUST-floor):** optional `pid.adaptive` default off; Kp/Ki only; tick-only RLS step; off or unhealthy → yaml fixed; `rls_state.json` ≠ PID clears; FF/CAP-7/Outdoor absent; plus `boiler_water` required when adaptive on; reset learned state = delete JSON; latch is RAM-only (JSON may restore adapted gains with latch false). No ARX/λ/rails tables; companion stays planning-only.
- **Latch party P:** Design Notes / 0006 Persistence state latch RAM-only explicitly (positive MUST, not Never-only). Verification checks 0006/AGENTS do not claim durable latch across reload.
- Algorithm companion stays a planning artifact; domain docs cite shipped behavior and ADR numbers only.

**Never:**
- Restoring Outdoor / FF / CAP-7 as live commissioning.
- Claiming adaptive is required or default on.
- Documenting latch as durable across reload (latch is RAM-only; JSON may restore adapted gains with latch False — do not invent the opposite).
- Editing epic/ticket files, runtime code, or pytest for this story.
- Dumping the full RLS math / φ / λ tables into AGENTS, CONTEXT, ADR 0006, or knowledge concepts.
- Rewriting ADR 0004 body; leaving 0005’s “RLS planned” lines in place; retitling or substance-rewriting 0005’s fixed-PID law sections.

## Decision index (2026-11-09)

| ID | Rule |
|----|------|
| OQ1 **A** | New accepted ADR 0006 for optional RLS; 0005 drops “planned” and cites 0006. |
| OQ2 **A** | New `rls-adaptive-pid` concept + index/SWT cite patches. |
| OQ3 **A** | house-calibration “not calibrated” bullet fixed in this story. |
| Party **S** (0005) | Surgical 0005 only — planned + Out-of-scope RLS gone; cite 0006; no title/body rewrite. |
| Party **F** (AGENTS) | Cite 0005+0006; Conventions carry all four verify facts; no math. |
| Party **N** (house-cal) | Narrow bullet: λ/IMC not calibrated here; point `pid.adaptive` to existing section. |
| Party **T** (CONTEXT) | Tail-only PID edit — keep fixed-gain lead + gate/tick; planned → four facts + 0006. |
| Party **H** (0006) | House MUST-floor (see Always); no ARX/λ/rails dump. |
| Party **S** (knowledge) | Short concept + SWT description/index + knowledge index patches. |
| Party **P** (latch) | Positive MUST in Design Notes/0006 + verify no durable-latch claim. |

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Agent opens AGENTS | Fresh session | Where cites 0005+0006; Conventions state all four facts (F) | N/A |
| Reader opens CONTEXT PID term | Glossary | Lead/gates intact (T); “planned” gone; four facts + 0006 in tail | N/A |
| Reader opens ADR 0005 | Live ADR | Fixed law body intact (S); planned/RLS-shipping gone; cites 0006 | N/A |
| Reader opens ADR 0006 | Live ADR | House MUST-floor (H) incl. boiler_water, reset=delete JSON, latch RAM-only; no equation dump | N/A |
| Reader opens knowledge | SWT + RLS concept + indexes | Short concept (S); SWT/index not fixed-only; cite 0006; no FF | N/A |
| Operator reads house-calibration “not calibrated” | After edit | Narrow λ/IMC bullet (N); does not deny `pid.adaptive` | N/A |
| Agent reads latch wording | 0006 / AGENTS | May describe unhealthy→yaml; must not claim latch survives reload (P) | N/A |

</frozen-after-approval>

## Code Map

- `AGENTS.md` — Where: cite 0005 + 0006; Conventions: all four facts (F); Verified stamp; managed block only.
- `CONTEXT.md` — PID term tail-only (T): drop “planned”; four facts + 0006; leave lead/gate/tick prose.
- `docs/adr/0005-fixed-pid-swt.md` — surgical (S): drop planned sentence; drop RLS from Out of scope; cite 0006; body law untouched.
- `docs/adr/0006-optional-rls-adaptive-pid.md` — **create** accepted ADR per House MUST-floor (H) + latch RAM-only (P).
- `docs/adr/0004-weather-curve-swt.md` — leave alone (historical FF).
- `knowledge/concepts/rls-adaptive-pid.md` — **create** short concept (S).
- `knowledge/concepts/set-water-temperature.md` + `knowledge/concepts/index.md` + `knowledge/index.md` — cite optional RLS / 0006; fix fixed-gain-only descriptions (S).
- `docs/house-calibration.md` — narrow “Online retuning” bullet (N).
- `apps.yaml.example` — leave alone (ops already correct).
- Companion `rls-adaptive-algorithm.md` — cite only; do not paste into domain docs.

## Tasks & Acceptance

**Execution:**
- [x] `docs/adr/0006-optional-rls-adaptive-pid.md` — create accepted ADR (House MUST-floor H + latch P).
- [x] `docs/adr/0005-fixed-pid-swt.md` — surgical drop planned / RLS-shipping; cite 0006 (S).
- [x] `CONTEXT.md` — PID tail-only: planned → four facts + 0006 (T).
- [x] `AGENTS.md` — cite 0005+0006; Conventions four facts (F); Verified stamp.
- [x] `knowledge/concepts/rls-adaptive-pid.md` + indexes + `set-water-temperature.md` — short concept + fixed-only description fixes (S).
- [x] `docs/house-calibration.md` — narrow “Online retuning” bullet (N).

**Acceptance Criteria:**
- Given AGENTS / CONTEXT / ADR / knowledge, when an agent or operator reads them for live SWT commissioning, then they state optional default-off adaptive RLS, YAML fixed fallback when off or unhealthy, JSON state separate from PID clears, and Weather Feedforward absent — with no “RLS planned / not commissioning” contradiction.
- Given ADR 0005’s fixed-PID law, when this story lands, then tick/event, anti-windup, clamp(base+u_pid), and Critical Zone diagnostics-only remain true (surgical patch only); 0006 is accepted with House MUST-floor and cited from 0005 / AGENTS / knowledge.
- Given house-calibration after edit, when reading “What is not calibrated here”, then the bullet is narrowed to deep λ/IMC knobs and does not deny shipped `pid.adaptive`.
- Given 0006 / AGENTS latch wording, when read after reload semantics, then latch is not documented as durable across reload (JSON may restore gains with latch false).
- Given docs-only scope, when verifying, then the Manual checks below pass (no App test changes).

## Implementation Notes

- **0006 skeleton (H):** decision blurb on top of 0005; commission (`pid.adaptive` default off, `boiler_water` when on); tick-only step; unhealthy/off → yaml fixed; Persistence (`rls_state.json`, clears do not wipe file, reset=delete JSON, latch RAM-only); Out of scope (FF/CAP-7, ARX dump, rails tables). Style like ADR 0003 length, not the companion.
- **AGENTS (F):** prefer one or two dense Conventions bullets over a second ADR; still must carry all four facts inline.
- **CONTEXT (T):** search-replace the planned sentence; do not reflow gate/tick sentences.
- **Latch (P):** state the positive pair once in 0006 Persistence — JSON may restore θ/P / adapted gains; unhealthy/rails latch is process memory only and starts false after reload.

## Plan Change Log

- 2026-11-09 party: locked 0005=S, AGENTS=F, house-cal=N, CONTEXT=T, 0006=H, knowledge=S, latch=P; plan patched for Approve checkpoint.
- 2026-11-09 human Approve → `ready-for-dev` (party locks frozen).

## Review Triage Log

## Design Notes

- Epic boundary: “RLS-specific doc lines” on ADR/CONTEXT/AGENTS/knowledge; 0006 holds adaptive decision record; 0005 stays the epic-2 fixed-PID artifact (surgical cite only).
- Ops (`apps.yaml.example`, most of house-calibration) already shipped with entries 1–3; domain lag plus one calibration contradiction are the defect.
- Latch durability is a doc footgun: Never forbids the wrong claim; party **P** requires an explicit correct claim in 0006 + a verify line.

## Verification

**Manual checks (if no CLI):**
- Grep AGENTS / CONTEXT / `docs/adr/0005*` / `docs/adr/0006*` / knowledge concepts+indexes: no “RLS … planned” / “not current commissioning” for adaptive retune.
- Those four surfaces state: adaptive optional default-off; YAML fixed fallback; `rls_state.json` (or equivalent) separate from PID clear; Weather Feedforward / CAP-7 absent.
- ADR 0005 fixed-PID law sections unchanged in substance (S); 0006 exists with `status: accepted` and House MUST-floor (H); AGENTS cites 0005 and 0006 and states all four facts (F).
- CONTEXT PID lead/gate/tick prose retained; only planned tail replaced (T).
- knowledge: short `rls-adaptive-pid` concept; SWT + indexes not fixed-gain-only; cite 0006 (S).
- house-calibration “not calibrated” narrowed to λ/IMC (N); does not deny `pid.adaptive`.
- 0006 / AGENTS do not claim unhealthy/rails latch survives process reload (P).
