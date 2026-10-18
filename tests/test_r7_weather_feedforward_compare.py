"""R7: compare Weather Feedforward on vs zero_uff (Screen-3 metrics)."""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass
from pathlib import Path

import pytest

from ha_smart_hvac.models import LadrcConfig, LadrcTuneConfig, WeatherFeedforwardConfig
from harness.runner import ClosedLoopSeries, run_closed_loop

# Verifying pins (same shape as tests/test_plant_lag_harness.py / R1 / R3).
_N = 40
_Y0 = 20.0
_T_R = 21.0
_ZONE = "living_room"
_PLANT_K = 0.45
_PLANT_T = 300.0
_PLANT_N = 3
_SETPOINT_MIN = 40.0
_SETPOINT_MAX = 55.0
_DT = 60.0

# Accepted spike threshold (Screen 3 / R7 material bar).
_X_MATERIAL = 30.0

_OUTDOOR_COLD = 0.0
_OUTDOOR_HOT = 10.0
_UFF_COLD = 49.0  # 25 + 1.2*(20-0)
_UFF_HOT = 37.0  # 25 + 1.2*(20-10)

# Locked absolutes / Δ% matching story-compare-weather-feedforward-on-vs-off.md
# (clamp-dominated plant pins → FF-on ≈ zero_uff on M1/M2/M4; no material Δ%).
_M1 = 11.530
_M2 = 53.671
_M4 = 1914.237
_M6 = 53.671
_DELTA_PCT = 0.0


def _example_aligned_config() -> LadrcConfig:
    """Same b0/ωo/ωc/dt/u_track_max shape as apps.yaml.example / CAP-3(b)."""
    return LadrcConfig(
        b0=5e-4,
        omega_o=0.03,
        omega_c=0.03,
        omega_c_min=0.02,
        omega_c_max=0.15,
        tune=LadrcTuneConfig(
            ki=0.005,
            deadband=0.2,
            min_steady_ticks=5,
            max_rate_fraction=0.05,
        ),
        dt=_DT,
        u_track_max=250.0,
    )


def _ff_config() -> WeatherFeedforwardConfig:
    return WeatherFeedforwardConfig(base=25.0, slope=1.2, comfort_ref=20.0)


def _run(*, outdoor: float, zero_uff: bool) -> ClosedLoopSeries:
    return run_closed_loop(
        n_ticks=_N,
        y0=_Y0,
        reference=_T_R,
        critical_zone=_ZONE,
        outdoor=outdoor,
        plant_k=_PLANT_K,
        plant_t=_PLANT_T,
        plant_n=_PLANT_N,
        setpoint_min=_SETPOINT_MIN,
        setpoint_max=_SETPOINT_MAX,
        ladrc_config=_example_aligned_config(),
        ff_config=_ff_config(),
        zero_uff=zero_uff,
    )


def series_is_finite(series: ClosedLoopSeries) -> bool:
    if len(series) != _N:
        return False
    for name in ("command", "y", "u_track", "z1", "z2", "u_ff"):
        values = getattr(series, name)
        if len(values) != _N or not all(math.isfinite(v) for v in values):
            return False
    return True


# --- Local M1/M2/M4/M6 + delta_pct (prefer copies; do not import R1/R3) ---


def metric_m1(series: ClosedLoopSeries) -> float:
    """Max |Δcommand| over consecutive ticks."""
    cmd = series.command
    return max(abs(cmd[t] - cmd[t - 1]) for t in range(1, len(cmd)))


def metric_m2(series: ClosedLoopSeries) -> float:
    """Sample variance of command."""
    return statistics.variance(series.command)


def metric_m4(
    series: ClosedLoopSeries, *, reference: float = _T_R, dt: float = _DT
) -> float:
    """Σ |reference − y[t]| · dt (reference run kwarg; dt from ladrc_config)."""
    return sum(abs(reference - y) * dt for y in series.y)


def metric_m6(series: ClosedLoopSeries) -> float:
    """Sample variance of command − u_ff (residue)."""
    residue = [c - u for c, u in zip(series.command, series.u_ff, strict=True)]
    return statistics.variance(residue)


def delta_pct(m_baseline: float, m_candidate: float) -> float:
    """Lower-is-better Δ% vs baseline (spike formula)."""
    if m_baseline == 0.0:
        return math.nan
    return 100.0 * (m_baseline - m_candidate) / abs(m_baseline)


def material_label(d_pct: float, *, x: float = _X_MATERIAL) -> str:
    return "material" if d_pct >= x else "not"


@dataclass(frozen=True)
class ModeMetrics:
    outdoor: float
    zero_uff: bool
    u_ff: float
    finite: bool
    m1: float
    m2: float
    m4: float
    m6: float
    residue_is_command: bool


@dataclass(frozen=True)
class OutdoorCompare:
    outdoor: float
    ff_on: ModeMetrics
    zero_uff: ModeMetrics
    d_m1: float
    d_m2: float
    d_m4: float
    label_m1: str
    label_m2: str
    label_m4: str


def _mode_metrics(*, outdoor: float, zero_uff: bool) -> ModeMetrics:
    series = _run(outdoor=outdoor, zero_uff=zero_uff)
    finite = series_is_finite(series)
    assert finite
    u_ff0 = series.u_ff[0]
    assert all(u == u_ff0 for u in series.u_ff)
    residue = [c - u for c, u in zip(series.command, series.u_ff, strict=True)]
    return ModeMetrics(
        outdoor=outdoor,
        zero_uff=zero_uff,
        u_ff=u_ff0,
        finite=finite,
        m1=metric_m1(series),
        m2=metric_m2(series),
        m4=metric_m4(series),
        m6=metric_m6(series),
        residue_is_command=all(
            r == c for r, c in zip(residue, series.command, strict=True)
        ),
    )


def evaluate_outdoors(
    outdoors: tuple[float, ...] = (_OUTDOOR_COLD, _OUTDOOR_HOT),
) -> dict[float, OutdoorCompare]:
    """FF-on baseline vs zero_uff candidate per outdoor; Δ% and material-vs-X labels."""
    out: dict[float, OutdoorCompare] = {}
    for outdoor in outdoors:
        ff_on = _mode_metrics(outdoor=outdoor, zero_uff=False)
        zero = _mode_metrics(outdoor=outdoor, zero_uff=True)
        d1 = delta_pct(ff_on.m1, zero.m1)
        d2 = delta_pct(ff_on.m2, zero.m2)
        d4 = delta_pct(ff_on.m4, zero.m4)
        out[outdoor] = OutdoorCompare(
            outdoor=outdoor,
            ff_on=ff_on,
            zero_uff=zero,
            d_m1=d1,
            d_m2=d2,
            d_m4=d4,
            label_m1=material_label(d1),
            label_m2=material_label(d2),
            label_m4=material_label(d4),
        )
    return out


def _recorded_results() -> dict[float, OutdoorCompare]:
    return evaluate_outdoors()


def test_cold_and_hot_finite_uff_and_residue_at_zero():
    """Cold/hot finite; FF-on u_ff pinned constant; zero path all 0; residue=command."""
    results = _recorded_results()

    cold = results[_OUTDOOR_COLD]
    assert cold.ff_on.finite and cold.zero_uff.finite
    assert cold.ff_on.u_ff == _UFF_COLD
    assert cold.zero_uff.u_ff == 0.0
    assert cold.zero_uff.residue_is_command is True

    hot = results[_OUTDOOR_HOT]
    assert hot.ff_on.finite and hot.zero_uff.finite
    assert hot.ff_on.u_ff == _UFF_HOT
    assert hot.zero_uff.u_ff == 0.0
    assert hot.zero_uff.residue_is_command is True


def test_screen3_metrics_match_artifact_absolutes_and_material_labels():
    """M1/M2/M4/M6 + Δ% vs FF-on baseline; material iff Δ% ≥ X=30% (relative only)."""
    results = _recorded_results()

    for outdoor in (_OUTDOOR_COLD, _OUTDOOR_HOT):
        row = results[outdoor]
        for mode in (row.ff_on, row.zero_uff):
            assert mode.m1 == pytest.approx(_M1, abs=5e-4)
            assert mode.m2 == pytest.approx(_M2, abs=5e-4)
            assert mode.m4 == pytest.approx(_M4, abs=5e-3)
            assert mode.m6 == pytest.approx(_M6, abs=5e-4)
        assert row.d_m1 == pytest.approx(_DELTA_PCT, abs=1e-6)
        assert row.d_m2 == pytest.approx(_DELTA_PCT, abs=1e-6)
        assert row.d_m4 == pytest.approx(_DELTA_PCT, abs=1e-6)
        assert row.label_m1 == "not"
        assert row.label_m2 == "not"
        assert row.label_m4 == "not"


def test_same_outdoors_replay_same_metrics_and_labels():
    """Re-run both outdoors × modes → same metrics and material labels."""
    first = _recorded_results()
    second = _recorded_results()
    for outdoor in (_OUTDOOR_COLD, _OUTDOOR_HOT):
        a, b = first[outdoor], second[outdoor]
        assert a.ff_on.m1 == b.ff_on.m1
        assert a.ff_on.m2 == b.ff_on.m2
        assert a.ff_on.m4 == b.ff_on.m4
        assert a.ff_on.m6 == b.ff_on.m6
        assert a.zero_uff.m1 == b.zero_uff.m1
        assert a.zero_uff.m2 == b.zero_uff.m2
        assert a.zero_uff.m4 == b.zero_uff.m4
        assert a.zero_uff.m6 == b.zero_uff.m6
        assert a.d_m1 == b.d_m1
        assert a.d_m2 == b.d_m2
        assert a.d_m4 == b.d_m4
        assert a.label_m1 == b.label_m1 == "not"
        assert a.label_m2 == b.label_m2 == "not"
        assert a.label_m4 == b.label_m4 == "not"
        assert a.zero_uff.residue_is_command is b.zero_uff.residue_is_command is True


def test_ff_compare_artifact_has_disclaimer_table_residue_citations():
    """Artifact: Never-disclaimer, cold/hot table, residue-at-zero, citations."""
    artifact = (
        Path(__file__).resolve().parents[1]
        / "_bmad-output/initiative-madrc/epic-madrc-decide"
        / "story-compare-weather-feedforward-on-vs-off.md"
    )
    text = artifact.read_text(encoding="utf-8")
    assert "Never-disclaimer" in text
    assert "Residue-at-zero" in text
    assert "| 0 |" in text
    assert "| 10 |" in text
    # Locked Screen-3 cells must match module constants (artifact↔constant parity).
    assert f"{_M1:.3f}" in text
    assert f"{_M2:.3f}" in text
    assert f"{_M4:.3f}" in text
    assert f"{_M6:.3f}" in text
    assert f"{_DELTA_PCT:.2f}" in text
    assert "not" in text
    assert "X=30%" in text or "X = 30%" in text
    assert "test_cold_and_hot_finite_uff_and_residue_at_zero" in text
    assert "test_screen3_metrics_match_artifact_absolutes_and_material_labels" in text
    assert "test_same_outdoors_replay_same_metrics_and_labels" in text
    # Relative Δ only — no policy-lean wording for entry 6.
    lowered = text.lower()
    banned = (
        "keep/drop",
        "keep vs drop",
        "lean keep",
        "lean drop",
        "recommend keep",
        "recommend drop",
    )
    for phrase in banned:
        assert phrase not in lowered
