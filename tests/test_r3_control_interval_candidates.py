"""R3: compare control_interval candidates under fixed Euler/ωo/substeps."""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass, replace
from pathlib import Path

from ha_smart_hvac.ladrc import _ESO_EULER_SUBSTEPS
from ha_smart_hvac.models import LadrcConfig, LadrcTuneConfig, WeatherFeedforwardConfig
from harness.runner import ClosedLoopSeries, run_closed_loop

# Verifying baseline pins (same shape as tests/test_plant_lag_harness.py / R1).
_N = 40
_Y0 = 20.0
_T_R = 21.0
_ZONE = "living_room"
_OUTDOOR = 0.0
_PLANT_K = 0.45
_PLANT_T = 300.0
_PLANT_N = 3
_SETPOINT_MIN = 40.0
_SETPOINT_MAX = 55.0
_OMEGA_O = 0.03

# Accepted spike thresholds (R3 material / latch floor).
_X_MATERIAL = 30.0
_Z_LATCH = 0.2

_CANDIDATES = (30.0, 60.0, 120.0)
_BASELINE_DT = 60.0


def _example_aligned_config(**overrides: float) -> LadrcConfig:
    """Same b0/ωo/ωc/dt/u_track_max shape as apps.yaml.example / CAP-3(b)."""
    base = LadrcConfig(
        b0=5e-4,
        omega_o=_OMEGA_O,
        omega_c=0.03,
        omega_c_min=0.02,
        omega_c_max=0.15,
        tune=LadrcTuneConfig(
            ki=0.005,
            deadband=0.2,
            min_steady_ticks=5,
            max_rate_fraction=0.05,
        ),
        dt=60.0,
        u_track_max=250.0,
    )
    return replace(base, **overrides) if overrides else base


def _ff_config() -> WeatherFeedforwardConfig:
    return WeatherFeedforwardConfig(base=25.0, slope=1.2, comfort_ref=20.0)


def _run(dt: float) -> ClosedLoopSeries:
    return run_closed_loop(
        n_ticks=_N,
        y0=_Y0,
        reference=_T_R,
        critical_zone=_ZONE,
        outdoor=_OUTDOOR,
        plant_k=_PLANT_K,
        plant_t=_PLANT_T,
        plant_n=_PLANT_N,
        setpoint_min=_SETPOINT_MIN,
        setpoint_max=_SETPOINT_MAX,
        ladrc_config=_example_aligned_config(dt=dt),
        ff_config=_ff_config(),
        zero_uff=False,
    )


def series_is_finite(series: ClosedLoopSeries) -> bool:
    if len(series) != _N:
        return False
    for name in ("command", "y", "u_track", "z1", "z2", "u_ff"):
        values = getattr(series, name)
        if len(values) != _N or not all(math.isfinite(v) for v in values):
            return False
    return True


def euler_factor(dt: float, omega_o: float = _OMEGA_O) -> float:
    """ρ = |1 − 2·h·ωo| with h = dt / _ESO_EULER_SUBSTEPS (= |1 − dt·ωo| at n_sub=2)."""
    h = dt / _ESO_EULER_SUBSTEPS
    return abs(1.0 - 2.0 * h * omega_o)


def euler_band_stable(dt: float, omega_o: float = _OMEGA_O) -> bool:
    """Production Euler gate: ρ < 1 (equiv. ωo < 2/dt at n_sub=2)."""
    return euler_factor(dt, omega_o) < 1.0


# --- Local M1/M2/M3 (prefer copies; avoid coupling to R1 module) ---


def metric_m1(series: ClosedLoopSeries) -> float:
    """Max |Δcommand| over consecutive ticks."""
    cmd = series.command
    return max(abs(cmd[t] - cmd[t - 1]) for t in range(1, len(cmd)))


def metric_m2(series: ClosedLoopSeries) -> float:
    """Sample variance of command."""
    return statistics.variance(series.command)


def metric_m3(series: ClosedLoopSeries) -> float:
    """Latch duty (mean of boolean latch over the run)."""
    return sum(1 for latched in series.latch if latched) / len(series.latch)


def delta_pct(m_baseline: float, m_candidate: float) -> float:
    """Lower-is-better Δ% vs baseline (spike formula)."""
    if m_baseline == 0.0:
        return math.nan
    return 100.0 * (m_baseline - m_candidate) / abs(m_baseline)


@dataclass(frozen=True)
class CandidateResult:
    dt: float
    euler_factor: float
    euler_stable: bool
    finite: bool
    stable: bool
    m1: float | None
    m2: float | None
    m3: float | None
    d_m1: float | None
    d_m2: float | None


def evaluate_candidates(
    dts: tuple[float, ...] = _CANDIDATES,
) -> dict[float, CandidateResult]:
    """Run each candidate; label stable iff Euler band + finite series."""
    raw: dict[float, tuple[ClosedLoopSeries, float, bool, bool]] = {}
    for dt in dts:
        series = _run(dt)
        factor = euler_factor(dt)
        band = euler_band_stable(dt)
        finite = series_is_finite(series)
        raw[dt] = (series, factor, band, finite)

    baseline = raw[_BASELINE_DT][0]
    assert series_is_finite(baseline)
    m1_b = metric_m1(baseline)
    m2_b = metric_m2(baseline)

    out: dict[float, CandidateResult] = {}
    for dt, (series, factor, band, finite) in raw.items():
        stable = band and finite
        if finite:
            m1 = metric_m1(series)
            m2 = metric_m2(series)
            m3 = metric_m3(series)
            d1 = 0.0 if dt == _BASELINE_DT else delta_pct(m1_b, m1)
            d2 = 0.0 if dt == _BASELINE_DT else delta_pct(m2_b, m2)
        else:
            m1 = m2 = m3 = d1 = d2 = None
        out[dt] = CandidateResult(
            dt=dt,
            euler_factor=factor,
            euler_stable=band,
            finite=finite,
            stable=stable,
            m1=m1,
            m2=m2,
            m3=m3,
            d_m1=d1,
            d_m2=d2,
        )
    return out


def recommend_interval(
    results: dict[float, CandidateResult],
    *,
    x_material: float = _X_MATERIAL,
    z_latch: float = _Z_LATCH,
) -> float:
    """Among stable + M3<Z: material M1|M2 vs 60 → best by M1 then M2; else keep 60.

    Never returns 120 (must be rejected via Euler/finite gate before ranking).
    """
    eligible: list[CandidateResult] = []
    for dt, row in results.items():
        if dt == 120.0:
            continue
        if not row.stable:
            continue
        assert row.m3 is not None
        if row.m3 >= z_latch:
            continue
        eligible.append(row)

    material = [
        r
        for r in eligible
        if r.dt != _BASELINE_DT
        and r.d_m1 is not None
        and r.d_m2 is not None
        and (r.d_m1 >= x_material or r.d_m2 >= x_material)
    ]
    if not material:
        return _BASELINE_DT

    # Best by M1 Δ% then M2 Δ% (higher improvement wins; lower-is-better metrics).
    material.sort(key=lambda r: (r.d_m1 or 0.0, r.d_m2 or 0.0), reverse=True)
    return material[0].dt


def _recorded_results() -> dict[float, CandidateResult]:
    return evaluate_candidates()


def test_eso_substeps_authority_is_two():
    """Stability authority: production _ESO_EULER_SUBSTEPS=2 (read-only cite)."""
    assert _ESO_EULER_SUBSTEPS == 2


def test_candidates_euler_labels_and_finite_series():
    """30/60 Euler-stable + finite; 120 Euler-unstable → rejected (never recommend)."""
    results = _recorded_results()

    r30 = results[30.0]
    assert r30.euler_stable is True
    assert r30.finite is True
    assert r30.stable is True
    assert r30.euler_factor == abs(1.0 - 30.0 * _OMEGA_O)

    r60 = results[60.0]
    assert r60.euler_stable is True
    assert r60.finite is True
    assert r60.stable is True
    assert r60.euler_factor == abs(1.0 - 60.0 * _OMEGA_O)
    assert r60.d_m1 == 0.0
    assert r60.d_m2 == 0.0

    r120 = results[120.0]
    assert r120.euler_stable is False
    assert r120.euler_factor >= 1.0
    assert r120.stable is False  # reject: Euler factor ≥ 1 (finite or not)


def test_recommendation_rule_matches_artifact():
    """Material M1|M2 vs 60 → best by M1 then M2; else keep 60; never 120."""
    results = _recorded_results()
    choice = recommend_interval(results)
    assert choice != 120.0
    assert choice == 30.0

    r30 = results[30.0]
    assert r30.stable is True
    assert r30.m3 is not None and r30.m3 < _Z_LATCH
    assert r30.d_m1 is not None and r30.d_m1 >= _X_MATERIAL

    # 120 must never win even if metrics look attractive when finite.
    assert results[120.0].stable is False


def test_same_dts_replay_same_stability_and_recommendation():
    """Re-running the candidate set yields the same labels and recommendation."""
    first = _recorded_results()
    second = _recorded_results()
    assert recommend_interval(first) == recommend_interval(second) == 30.0
    for dt in _CANDIDATES:
        a, b = first[dt], second[dt]
        assert a.euler_stable == b.euler_stable
        assert a.finite == b.finite
        assert a.stable == b.stable
        assert a.m1 == b.m1
        assert a.m2 == b.m2
        assert a.m3 == b.m3


def test_interval_artifact_has_disclaimer_table_recommendation_citations():
    """Written artifact: Never-disclaimer, table, recommendation, test citations."""
    artifact = (
        Path(__file__).resolve().parents[1]
        / "_bmad-output/initiative-madrc/epic-madrc-decide"
        / "story-compare-control-interval-candidates.md"
    )
    text = artifact.read_text(encoding="utf-8")
    assert "Never-disclaimer" in text
    assert "ladrc_config.dt" in text
    assert "control_interval" in text
    assert "Recommendation:" in text
    rec_line = text.split("Recommendation:")[1].splitlines()[0].lower()
    assert "30" in rec_line
    assert "120" not in rec_line
    assert "F-R8" in text
    assert "_ESO_EULER_SUBSTEPS" in text
    assert "house-calibration" in text
    assert "test_candidates_euler_labels_and_finite_series" in text
    assert "test_recommendation_rule_matches_artifact" in text
    assert "test_same_dts_replay_same_stability_and_recommendation" in text
    assert "YAML" in text or "apps.yaml" in text
