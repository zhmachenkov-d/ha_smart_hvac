# Demo: Story 7.3 Broad strokes — four entry points
Generated: 2026-11-21T09:54:00+00:00

Offline open-in-order on `main`/`chore/walkthrough-story-7-3-intent-review` after PR #166. Goal: each Broad strokes link alone explains the docs-only mechanism.

## 1. ADR 0008 § TRV soft-close
Open: `docs/adr/0008-weather-curve-trv-flame-swt.md:31`

- Closure-only; leftover `accuracy` → ConfigError; never opening; Critical Zone not TRV.
- Plant-off → closure 100 + cancel hold.
- Plant-on first all-idle → floor (80) + arm `trv_soft_close_hold_s` (300); no re-arm while holding; idle expiry → 100 stay; orphan no-op; any Heating Demand (cold start / rising-edge / sustained) → 100 cancel; return-to-idle re-floor+arm.

**Readable alone: yes.**

## 2. CONTEXT + AGENTS
Open: `CONTEXT.md:61` then `AGENTS.md:35`

- Same house-idle law (compressed “any Heating Demand” on both).
- AGENTS Verified stamp still `2026-11-17` / `928b2b6…` (`AGENTS.md:2`).

**Readable alone: yes** (depth pointer: ADR for demand-flavor enum).

## 3. knowledge primary page
Open: `knowledge/concepts/trv-soft-close.md:11` (Plant-on/off bullets `:19-20`)

- Frontmatter: house-idle floor + hold then 100 (ADR 0008).
- Cites ADR 0008 + live prelude; Plant-off/on bullets match ADR.

**Readable alone: yes.**

## 4. Historical banners (sample + siblings)
Open: `docs/decisions/adr-trv-write-gated-overshoot-latch.md:1`  
Also: `adr-trv-plant-off-no-latch-clear.md:1`, `adr-trv-accuracy-shared-control-event.md:1`

- Each leading line: Historical — …; live soft-close is house-idle floor + hold (ADR 0008).

**Readable alone: yes** (zombie demotion).

## Verdict

Broad strokes entry points work in order: ADR → CONTEXT/AGENTS → knowledge → banners. Mechanism understood without reading the full file list.
