"""R1 Screen-2 classification of commanded SWT jumps (one-knob ablations)."""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass, replace
from typing import Literal

from ha_smart_hvac.models import LadrcConfig, LadrcTuneConfig, WeatherFeedforwardConfig
from harness.runner import ClosedLoopSeries, run_closed_loop

# Verifying baseline pins (same shape as tests/test_plant_lag_harness.py).
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

# Accepted spike thresholds (Screen 2 ranking). X is not a pick gate.
_EPSILON_PP = 10.0
_Z_LATCH = 0.2

Family = Literal["tuning", "dt", "plant"]
OutcomeKind = Literal["a", "b", "c", "d", "inseparable"]

_FAMILY_TO_CLASS: dict[Family, OutcomeKind] = {
    "tuning": "a",
    "dt": "b",
    "plant": "c",
}


def _example_aligned_config(**overrides: float) -> LadrcConfig:
    """Same b0/ωo/ωc/dt/u_track_max shape as apps.yaml.example / CAP-3(b)."""
    base = LadrcConfig(
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
        dt=60.0,
        u_track_max=250.0,
    )
    return replace(base, **overrides) if overrides else base


def _ff_config() -> WeatherFeedforwardConfig:
    return WeatherFeedforwardConfig(base=25.0, slope=1.2, comfort_ref=20.0)


def _run(
    *,
    ladrc_config: LadrcConfig | None = None,
    plant_n: int | None = None,
    plant_t: float | None = None,
) -> ClosedLoopSeries:
    return run_closed_loop(
        n_ticks=_N,
        y0=_Y0,
        reference=_T_R,
        critical_zone=_ZONE,
        outdoor=_OUTDOOR,
        plant_k=_PLANT_K,
        plant_t=_PLANT_T if plant_t is None else plant_t,
        plant_n=_PLANT_N if plant_n is None else plant_n,
        setpoint_min=_SETPOINT_MIN,
        setpoint_max=_SETPOINT_MAX,
        ladrc_config=ladrc_config or _example_aligned_config(),
        ff_config=_ff_config(),
        zero_uff=False,
    )


def _assert_finite_series(series: ClosedLoopSeries) -> None:
    assert len(series) == _N
    for name in ("command", "y", "u_track", "z1", "z2", "u_ff"):
        values = getattr(series, name)
        assert len(values) == _N
        assert all(math.isfinite(v) for v in values), name


# --- R1 metrics (M1/M2/M3/M5 only; M4/M6 deferred) ---


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


def metric_m5(series: ClosedLoopSeries) -> float:
    """Pearson corr(z1, y) over the run."""
    z1 = series.z1
    y = series.y
    n = len(z1)
    mean_z = sum(z1) / n
    mean_y = sum(y) / n
    num = sum((a - mean_z) * (b - mean_y) for a, b in zip(z1, y, strict=True))
    den_z = math.sqrt(sum((a - mean_z) ** 2 for a in z1))
    den_y = math.sqrt(sum((b - mean_y) ** 2 for b in y))
    if den_z == 0.0 or den_y == 0.0:
        return 0.0
    return num / (den_z * den_y)


def delta_pct(
    m_baseline: float, m_candidate: float, *, higher_is_better: bool
) -> float:
    """Relative Δ% for ranking; invert numerator when higher-is-better."""
    if m_baseline == 0.0:
        return math.nan
    if higher_is_better:
        return 100.0 * (m_candidate - m_baseline) / abs(m_baseline)
    return 100.0 * (m_baseline - m_candidate) / abs(m_baseline)


@dataclass(frozen=True)
class AblationRun:
    """One recorded one-knob ablation vs the verifying baseline."""

    name: str
    family: Family
    series: ClosedLoopSeries
    knobs: dict[str, float | int]


@dataclass(frozen=True)
class Screen2Result:
    outcome: OutcomeKind
    conflict_pair: tuple[Family, Family] | None = None
    no_pick: bool = False
    m3_trigger: str | None = None
    picks: dict[str, Family | None] | None = None
    family_abs_delta: dict[str, dict[Family, float]] | None = None


def _family_abs_delta(
    baseline: ClosedLoopSeries,
    ablations: list[AblationRun],
    metric_fn,
    *,
    higher_is_better: bool,
) -> dict[Family, float]:
    """Per-family max |Δ%| across that family's recorded knobs."""
    m_b = metric_fn(baseline)
    best: dict[Family, float] = {}
    for run in ablations:
        d = abs(
            delta_pct(m_b, metric_fn(run.series), higher_is_better=higher_is_better)
        )
        if run.family not in best or d > best[run.family]:
            best[run.family] = d
    return best


def _pick_family(
    abs_by_family: dict[Family, float], *, epsilon: float
) -> Family | None:
    ranked = sorted(abs_by_family.items(), key=lambda kv: kv[1], reverse=True)
    if not ranked:
        return None
    if len(ranked) == 1:
        return ranked[0][0] if ranked[0][1] >= epsilon else None
    lead = ranked[0][1] - ranked[1][1]
    if lead >= epsilon:
        return ranked[0][0]
    return None


def screen2(
    baseline: ClosedLoopSeries,
    ablations: list[AblationRun],
    *,
    epsilon: float = _EPSILON_PP,
    z_latch: float = _Z_LATCH,
) -> Screen2Result:
    """Accepted Screen-2 fallthrough (M3 gate → lex M1→M2→M5 → conflict check)."""
    if metric_m3(baseline) >= z_latch:
        return Screen2Result(outcome="d", m3_trigger="baseline")
    for run in ablations:
        if metric_m3(run.series) >= z_latch:
            return Screen2Result(outcome="d", m3_trigger=run.name)

    specs: list[tuple[str, object, bool]] = [
        ("M1", metric_m1, False),
        ("M2", metric_m2, False),
        ("M5", metric_m5, True),
    ]
    family_abs: dict[str, dict[Family, float]] = {}
    picks: dict[str, Family | None] = {}
    for mid, fn, hib in specs:
        abs_map = _family_abs_delta(baseline, ablations, fn, higher_is_better=hib)
        family_abs[mid] = abs_map
        picks[mid] = _pick_family(abs_map, epsilon=epsilon)

    provisional: Family | None = None
    for mid in ("M1", "M2", "M5"):
        if picks[mid] is not None:
            provisional = picks[mid]
            break
    if provisional is None:
        return Screen2Result(
            outcome="inseparable",
            no_pick=True,
            picks=picks,
            family_abs_delta=family_abs,
        )

    for mid in ("M1", "M2", "M5"):
        other = picks[mid]
        if other is not None and other != provisional:
            return Screen2Result(
                outcome="inseparable",
                conflict_pair=(provisional, other),
                picks=picks,
                family_abs_delta=family_abs,
            )

    return Screen2Result(
        outcome=_FAMILY_TO_CLASS[provisional],
        picks=picks,
        family_abs_delta=family_abs,
    )


# Recorded one-knob ablations (concrete finite-series values for the artifact).
_RECORDED_KNOBS: list[tuple[str, Family, dict[str, float | int]]] = [
    ("tuning_omega_c_0.08", "tuning", {"omega_c": 0.08}),
    ("tuning_b0_1e-3", "tuning", {"b0": 1e-3}),
    ("dt_30", "dt", {"dt": 30.0}),
    ("plant_n_8", "plant", {"plant_n": 8}),
    ("plant_T_600", "plant", {"plant_t": 600.0}),
]


def _ablation_from_knobs(
    name: str, family: Family, knobs: dict[str, float | int]
) -> AblationRun:
    ladrc_keys = ("omega_c", "b0", "omega_o", "dt")
    ladrc_overrides = {k: v for k, v in knobs.items() if k in ladrc_keys}
    plant_n = knobs.get("plant_n")
    plant_t = knobs.get("plant_t")
    ladrc = _example_aligned_config(**ladrc_overrides) if ladrc_overrides else None
    series = _run(
        ladrc_config=ladrc,
        plant_n=int(plant_n) if plant_n is not None else None,
        plant_t=float(plant_t) if plant_t is not None else None,
    )
    return AblationRun(name=name, family=family, series=series, knobs=dict(knobs))


def _recorded_ablations() -> tuple[ClosedLoopSeries, list[AblationRun]]:
    baseline = _run()
    ablations = [_ablation_from_knobs(n, f, k) for n, f, k in _RECORDED_KNOBS]
    return baseline, ablations


def test_recorded_ablations_finite_and_screen2_class_c():
    """One-knob ablations vs verifying baseline → Screen-2 class (c); series finite."""
    baseline, ablations = _recorded_ablations()
    _assert_finite_series(baseline)
    for run in ablations:
        _assert_finite_series(run.series)

    result = screen2(baseline, ablations)
    assert result.outcome == "c"
    assert result.conflict_pair is None
    assert result.no_pick is False
    assert result.m3_trigger is None
    assert result.picks is not None
    assert result.picks["M1"] is None
    assert result.picks["M2"] == "plant"
    assert result.picks["M5"] is None


def test_same_recorded_knobs_replay_same_screen2_outcome():
    """Replaying the ablation-table knobs yields the same Screen-2 outcome."""
    first = screen2(*_recorded_ablations())
    second = screen2(*_recorded_ablations())
    assert first.outcome == second.outcome == "c"
    assert first.picks == second.picks
    assert first.conflict_pair == second.conflict_pair
    assert first.no_pick == second.no_pick


def test_classification_artifact_has_verdict_and_citations():
    """Written classification: Never-disclaimer, R1 verdict, dt≠YAML, test citations."""
    from pathlib import Path

    artifact = (
        Path(__file__).resolve().parents[1]
        / "_bmad-output/initiative-madrc/epic-madrc-decide"
        / "story-classify-swt-command-jumps.md"
    )
    text = artifact.read_text(encoding="utf-8")
    assert "Never-disclaimer" in text
    assert "ladrc_config.dt" in text
    assert "control_interval" in text
    assert "Class (c)" in text
    assert "test_recorded_ablations_finite_and_screen2_class_c" in text
    assert "test_same_recorded_knobs_replay_same_screen2_outcome" in text
    assert "ADR go/no-go" in text
