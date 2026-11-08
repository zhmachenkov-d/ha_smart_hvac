---
epic: epic-pid-domain-docs
date: 2026-11-08
verdict: accepted-with-open-items
criteria: declared
headless: false
---

# Retrospective — epic-pid-domain-docs

## Epic summary

**Epic:** `epic-pid-domain-docs` — PID domain language and ADR (initiative `initiative-pid`, id 2). Going-in concerns: none (`go`).

| ref | title | status / state | risk | plan baseline | range used |
|-----|-------|----------------|------|---------------|------------|
| 2.1 | AGENTS.md fixed-PID SWT conventions | done / done | medium | `0a3bf9b` | `0a3bf9b..85a2e22` (PR #98) |
| 2.2 | ADR superseding weather-curve SWT | done / done | high | `85a2e22` | `85a2e22..e69cc2a` (PR #99) |
| 2.3 | CONTEXT.md PID domain language | done / done | medium | `e69cc2a` | `e69cc2a..023d931` (PR #100) |
| 2.4 | knowledge concept pages for PID SWT | done / done | medium | `023d931` | `023d931..ae26c32` (PR #101) |
| 2.5 | Refactor sweep | done / done | low | `ae26c32` | `ae26c32..56e739c` (PR #102) — **cut** end (not HEAD) |

- `pending_tickets`: none. Tickets still at `built`: none.
- Baselines verified oldest-first with `git merge-base --is-ancestor` (`0a3bf9b < 85a2e22 < e69cc2a < 023d931 < ae26c32 < 56e739c`).
- After epic end `56e739c`: PR #103 (`a679843`, cursor tooling cleanup) — **excluded**.
- Epic product diff: `0a3bf9b..56e739c` over `AGENTS.md`, `CONTEXT.md`, `docs/adr/`, `knowledge/` (~470 unified-diff lines staged for review).
- `git_evidence.py`: one run per range; `merges_measured == merge_count` (1) each; `binary_revisions` null. Story files: none.
- Criteria: **declared** (epic R1–R2, C1, Done when 1–3).
- Diff-scope review: `bmad-review` render HALT (`workflow.md` missing) — lenses run **inline** over `/tmp/epic2-docs.diff` + HEAD files (adversarial, edge-case-hunter, structure). Verification-gap lens skipped (`applies_to: code`; no `apps/` churn). Narrowing recorded.

### Evidence inventory

| evidence | status |
|----------|--------|
| Epic file `epic-pid-domain-docs.md` | read in full |
| Initiative file | not opened — covers restated as R1/R2 |
| Entries / plans | 2.1–2.5 (`story_file: null`) |
| `git_evidence.py` | 2.1–2.5 cut at `56e739c` |
| Run folders / companions | none |
| Previous epic retro | `epic-fixed-pid-swt-retrospective.md` |
| Session logs | partial (Cursor transcripts); process lessons from plans + commits |
| `deferred-work.md` | read — epic-1→epic-2 deferrals still open as bullets; 2.5 Resolved for ladrc/madrc |

## Findings

Disposition key: **fix now** / **defer** / **accept**. Lens findings re-checked against HEAD before routing.

### Spec-to-implementation reconciliation

**SR1 — Done when 1 (ADR supersedes 0004).** *Accept (met).*
- Source: `docs/adr/0005-fixed-pid-swt.md:1-7` `status: accepted`, supersedes 0004; `docs/adr/0004-weather-curve-swt.md:2` `superseded by ADR-0005`.
- Commits: `e519ad9`, `07e4a07` (PR #99).

**SR2 — Done when 2–3 (AGENTS / CONTEXT / named knowledge pages match App; no live weather/CAP-7 commissioning).** *Accept (met).*
- Source: `AGENTS.md:18,34-36`; `CONTEXT.md:52-61,76-82`; concept pages + `knowledge/concepts/index.md` / `knowledge/index.md` cite ADR 0005 / fixed-PID; ladrc/madrc Project notes (`ladrc.md:30`, `madrc.md:31`) historical, not live weather-curve.
- Repo search for live `clamp(u_ff)` / CAP-7-on commissioning in owned surfaces: only `_Avoid_`, historical ADR 0004 body, and “not a control listener” negatives.

**SR3 — C1 RLS not current commissioning.** *Accept (met).*
- Source: `docs/adr/0005-fixed-pid-swt.md:7,40`; `CONTEXT.md:60`.

**SR4 — Epic Notes ADR inputs (tick/event, clear latency, anti-windup, ∫ °C·h, R7) landed in ADR 0005.** *Accept (met).*
- Source: `docs/adr/0005-fixed-pid-swt.md:15-36`.

**SR5 — AGENTS event clear wording vs idle write-0.** *Fix now (docs clarity).*
- Source: `AGENTS.md:35` “may clear … without a demand write” vs `CONTEXT.md:60,82` and ADR `0005:22` — idle/no-valid-zones **write `0`** and clear ∫; plant-off no write. “Demand write” means PI demand command, but agents can misread as no plant write at all.
- Prevention: when AGENTS shortens ADR law, keep the idle write-0 / plant-off no-write split explicit.

**SR6 — R7 plant-readback absent from CONTEXT / SWT concept.** *Accept (prior decision).*
- Source: 2.3 Code Review Decision **B** — leave readback throttle in AGENTS/ADR only (`story-context-md-pid-domain-language-plan.md`). ADR/AGENTS still carry R7 (`0005:24`, `AGENTS.md:35`).
- Do not re-flag unless a later story expands CONTEXT altitude.

### Pattern divergence / process

**PD1 — `review: quick` on high-risk story 2.2.** *Defer (process) — same as epic-1 B3/A9.*
- Source: `story-adr-superseding-weather-curve-swt-plan.md` frontmatter `risk: high`, `review: quick`. Full multi-lens still ran via practice (Code Review block), but the pin contradicts refine discipline B3.
- Prevention: at refine, do not pin quick when risk=high (B3 still open).

**PD2 — `deferred-work.md` still presents epic-2-owned CONTEXT/ADR/`knowledge/` CAP-8/FF deferrals as open.** *Fix now (bookkeeping).*
- Source: `deferred-work.md` bullets under 1.2 / 1.3 / 1.4 deferrals (lines ~7–21) still say CONTEXT/ADR/`knowledge/` “still describe” live weather path after epic 2 closed those surfaces.
- Prevention: closing an epic that owns deferred items adds a dated **Resolved** section naming them.

**PD3 — ADR 0004 body still narrates live weather-curve law.** *Accept (historical ADR pattern).*
- Source: `0004-weather-curve-swt.md` body unchanged; only frontmatter supersedes. Done when required supersession, not body rewrite.
- Optional later banner is defer hygiene, not a criteria miss.

### Architecture / duplication / size

**AD1 — Docs-only; no `apps/` / `tests/` churn in `0a3bf9b..56e739c`.** *Accept (positive).*
- Structure: ADR 0005 is canonical schedule law; AGENTS/CONTEXT/knowledge intentionally overlap for agent load order. Structure lens MERGE/CONDENSE suggestions recorded as **accept** (duplication by design for this epic’s D18/AGENTS-first tracer).

**DU1 — Four-way tick/event restatement.** *Accept.*
- Same as AD1; PRESERVE ADR § Tick vs event (structure lens).

**GZ1 — God-class growth.** *N/A / checked clean.*
- Highest non-merge churn is plan artifacts (~70–88 net lines each); product files are small rewrites (AGENTS net +1, CONTEXT net 0, ADR 0005 +40). No god-class candidate.

### Lens findings kept after re-check

- **L-AGENTS-idle (adversarial)** → SR5 fix now.
- **L-R7-CONTEXT (adversarial/edge)** → SR6 accept (Decision B).
- **L-0004-body (adversarial)** → PD3 accept.
- **L-deferred-work-stale (adversarial)** → PD2 fix now.
- **L-review-quick-high (process)** → PD1 defer.
- **L-zone-error-diagnostics (adversarial)** → **defer**: `knowledge/concepts/zone-error.md` still omits “diagnostics-only” on Critical Zone ranking; not in epic Done-when file list. Out of epic 2 primary scope.
- **L-0002/0003-chain (adversarial)** → **defer**: frontmatter still “superseded by ADR-0004”; archaeology ends one hop early.
- **L-log-historical (adversarial)** → **accept**: append-only `knowledge/log.md` Fact; 2.5 Verification explicitly excluded log.
- **L-antiwindup-R7-precedence (edge)** → **defer**: ADR does not order saturation freeze vs equal-float ∫ advance; runtime owned by epic 1; optional ADR footnote later.
- **L-PI-vs-PID naming (adversarial)** → **accept**: house idiom is “PID” for fixed-gain PI (C4 D=0).
- Structure MERGE/CONDENSE → **accept** (intentional overlap).

Dropped (did not hold): claim that deferred-work “still commissions” as a product defect (it is planning bookkeeping); claim that bundling stories in one unified review diff caused missed gates (each story had its own PR #98–#102).

### Process lessons

- **PL1 — High-risk + `review: quick` pin survived again on 2.2** (carry B3).
- **PL2 — AGENTS shorthand can reintroduce ambiguity the ADR already resolved** (idle write-0 vs “no demand write”) — SR5.
- **PL3 — Deferred-work open bullets outlive the owning epic** unless a Resolved section is written at close (PD2).
- **PL4 — Positive:** AGENTS-first tracer (epic Notes / prior A8) landed before ADR/CONTEXT/knowledge; agent sessions stopped loading weather-curve law after PR #98.

## Behavior verification

- **Runtime AppDaemon / Exclusive Session:** not exercised — epic Boundaries: docs only; `git diff --stat 0a3bf9b..56e739c -- apps/ tests/` empty.
- **Exercised instead (Done-when verify):**
  - File reads of ADR 0005 / 0004 frontmatter, AGENTS, CONTEXT, listed knowledge pages, ladrc/madrc
  - `rg` for live weather-curve commissioning language on owned surfaces
  - Inline adversarial / edge-case / structure lenses on staged docs diff
- Closed-loop plant behavior remains unverified (unchanged from epic-1 retro).

## Previous-retro follow-through

Prior file: `epic-fixed-pid-swt-retrospective.md` (2026-11-08, verdict accepted-with-open-items).

| Item | Landed? | Evidence |
|------|---------|----------|
| B2 / A8 — Land AGENTS / CONTEXT / ADR / `knowledge/` first | **yes** | PR #98–#102; `AGENTS.md:34-36`, ADR 0005, `CONTEXT.md:60`, knowledge concept pages |
| A6 — Add `knowledge/` to epic 2 | **yes** (already at refine) | epic Done when / Boundaries; stories 2.4–2.5 |
| A7 — Hand ADR inputs to epic 2 | **yes** | epic Notes + ADR 0005 body (tick/event, SR3 clear latency, anti-windup, R7, °C·h) |
| B3 / A9 — Do not pin `review: quick` when risk=high | **no evidence of pin change** | 2.2 plan still `risk: high`, `review: quick` |
| B4 — Optional two-tick plant-drift test | **no evidence found** in this epic (runtime; still deferred-work) | N/A docs epic |
| B6 — Optional legacy-scale `ki` WARN | **no evidence found** in this epic | N/A docs epic |
| Decisions 1–6 → superseding ADR | **yes** | `docs/adr/0005-fixed-pid-swt.md` (not separate `docs/decisions/` files) |

## Action items

Proposed only — not applied by this retrospective. Docs → small follow-up / Sofia; process → team.

| # | Action | Kind | Owner | From |
|---|--------|------|-------|------|
| C1 | Clarify `AGENTS.md` control_event bullet: idle/no-valid-zones write `0` + clear ∫; plant-off clear ∫ no write; “no demand write” = no PI demand SWT | remediation (docs) | Amelia / docs patch | SR5, PL2 |
| C2 | Add **Resolved in epic-pid-domain-docs** to `deferred-work.md` for the epic-1 CAP-8/FF/CONTEXT/ADR/`knowledge/` deferrals now closed by 2.1–2.5 | bookkeeping | Sofia / docs | PD2, PL3 |
| C3 | At refine, do not pin `review: quick` when `risk=high` (carry B3) | process | team | PD1, B3 |
| C4 | Optional: `zone-error.md` + index row — Critical Zone diagnostics-only / ADR 0005 | defer | future / knowledge hygiene | L-zone-error |
| C5 | Optional: ADR 0004 body banner; 0002/0003 supersession chain → 0005 | defer | docs hygiene | PD3, L-chain |
| C6 | Optional: ADR footnote on anti-windup vs R7 ∫ precedence | defer | docs | L-antiwindup |

Accepted / do not re-flag: SR1–SR4, SR6 (Decision B), PD3 body-as-history, DU1 overlap, PI-vs-PID idiom, append-only log Fact, structure PRESERVE ADR.

## Decision records

Decision test applied to 2.1–2.5 frozen Intents / Implementation Notes / prior epic decisions 1–6.

- Frozen intents for 2.1–2.5 are delivery intents (rewrite AGENTS/ADR/CONTEXT/knowledge) — **do not pass** as separate decision records; the irreversible architectural record is **ADR 0005** itself (`e519ad9` / PR #99).
- Prior decisions 1–6 (tick-owned demand, anti-windup, R7/D22, °C·h, ∫-only clear, commission parse) — **already recorded** in `docs/adr/0005-fixed-pid-swt.md` (and epic-1 code). **No new `adr-*.md` / `docs/decisions/` files proposed.**

**User (2026-11-08):** confirmed — no separate decision-record files written.

## Acceptance verdict

**Verdict: accepted-with-open-items**, confirmed by the user (2026-11-08). Criteria: **declared**. `pending_tickets` empty. Matches machine verdict.

Evidence criteria met:

1. Done when 1 — ADR 0005 accepted; 0004 superseded (SR1).
2. Done when 2 — AGENTS, CONTEXT, named knowledge pages + index describe PID path, tick/event, Critical Zone diagnostics-only; no live weather/CAP-7 commissioning on those surfaces (SR2).
3. Done when 3 — language matches App; `apps/` unchanged this epic; negatives align with epic-1 conventions (SR2).
4. R1/R2/C1 — met (SR1–SR3).

Open items tracked: **C1** (AGENTS idle wording), **C2** (deferred-work Resolved), **C3**/B3 (review pin). Optional deferrals C4–C6. Action items remain proposed — not applied by this retrospective.

Closing the epic remains Sofia’s (`bmad-agent-po`), confirmed by the user. This retrospective wrote only this document; no ticket status changed.

## Open questions

- Production AppDaemon version / Exclusive Session HITL note from epic Notes (do not commission live until the epic is closed by Sofia) — unchanged by this retro.
- C1 timing: tiny docs patch before epic close vs deferred-work — left to the owner when executing C1.

## Assumptions

Omit — interactive run; user confirmed verdict and decision-record choice 2026-11-08.
