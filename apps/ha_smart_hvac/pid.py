"""Fixed-gain PI Set Water Temperature law (weighted demand zones).

Units: e in °C of air; ∫ in °C·h (e integrated over hours); ``kp`` in °C water
per °C air; ``ki`` in 1/h, so the I-term ``ki·∫`` is °C of water. The I-term is
bounded by ``i_term_min`` / ``i_term_max`` (°C water). Each periodic tick that
steps adds ``e·control_interval/3600`` (the configured interval, not measured
elapsed time; frozen or skipped ticks add nothing), so changing the control
interval does not rescale the effective Ki.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from ha_smart_hvac.models import ZoneSnapshot


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


@dataclass(frozen=True)
class PidResult:
    """Demand-path PI evaluation before the SWT write."""

    e: float
    u_pid: float
    raw: float
    command: float
    integral: float


def _demand_contributions(
    zones: Sequence[ZoneSnapshot],
) -> list[tuple[float, float, float]] | None:
    """(Tair, Tset, weight) for demand zones; None when no demand or weight sum ≤ 0."""
    contribs: list[tuple[float, float, float]] = []
    for zone in zones:
        if not zone.has_heating_eligible:
            continue
        tset = zone.heating_setpoint_max
        if tset is None:
            continue
        contribs.append((zone.zone_temp, tset, zone.weight))
    if not contribs:
        return None
    weight_sum = sum(w for _, _, w in contribs)
    if weight_sum <= 0:
        return None
    return contribs


def weighted_error(zones: Sequence[ZoneSnapshot]) -> float | None:
    """e = Tset_w − Tair_w over demand zones; None if no usable contributions."""
    contribs = _demand_contributions(zones)
    if contribs is None:
        return None
    weight_sum = sum(w for _, _, w in contribs)
    tair_w = sum(w * tair for tair, _, w in contribs) / weight_sum
    tset_w = sum(w * tset for _, tset, w in contribs) / weight_sum
    return tset_w - tair_w


def evaluate_demand(
    zones: Sequence[ZoneSnapshot],
    *,
    integral: float,
    kp: float,
    ki: float,
    base_water_temp: float,
    setpoint_min: float,
    setpoint_max: float,
    i_term_min: float,
    i_term_max: float,
    dt_hours: float,
) -> PidResult | None:
    """Compute PI command and step ∫ (tick-owned; saturation freeze applies).

    The command uses ``integral`` (°C·h) as passed in (before this step); the
    returned ``integral`` is the stepped value: ``∫ + e·dt_hours`` with the
    I-term ``ki·∫`` clamped to ``[i_term_min, i_term_max]`` °C water. With
    ``ki == 0`` the returned ∫ is 0. Call only from the periodic control tick:
    event paths must not call this, since every call advances ∫.

    Returns None when there are no demand contributions or weight sum ≤ 0
    (caller should take the idle path).
    """
    e = weighted_error(zones)
    if e is None:
        return None

    u_pid = kp * e + ki * integral
    raw = base_water_temp + u_pid
    command = round(clamp(raw, setpoint_min, setpoint_max), 1)

    new_integral = integral
    saturated_high = raw > setpoint_max and e > 0
    saturated_low = raw < setpoint_min and e < 0
    if not (saturated_high or saturated_low):
        candidate = integral + e * dt_hours
        if ki == 0:
            new_integral = 0.0
        else:
            new_integral = clamp(ki * candidate, i_term_min, i_term_max) / ki

    return PidResult(
        e=e,
        u_pid=u_pid,
        raw=raw,
        command=command,
        integral=new_integral,
    )
