"""Multi-Zone Coordinator — Critical Zone selection."""

from __future__ import annotations

from ha_smart_hvac.models import ControlDecision, ZoneSnapshot


def has_heating_demand(zones: list[ZoneSnapshot]) -> bool:
    """True when any zone has positive Zone Error among heating-eligible thermostats.

    Same eligibility as ZoneSnapshot.zone_error: -inf only when a zone has no
    heating-eligible thermostats; heating with non-positive error is finite and
    does not demand.
    """
    return any(z.zone_error > 0 for z in zones)


def select_critical_zone(zones: list[ZoneSnapshot]) -> ControlDecision:
    """Pick the zone with the largest positive zone error."""
    if not zones:
        return ControlDecision(
            critical_zone=None,
            reference=None,
            measured=None,
            zone_error=0.0,
            has_demand=False,
        )

    best = max(zones, key=lambda z: z.zone_error)
    has_demand = best.zone_error > 0

    if not has_demand:
        return ControlDecision(
            critical_zone=None,
            reference=None,
            measured=None,
            zone_error=best.zone_error,
            has_demand=False,
        )

    return ControlDecision(
        critical_zone=best.name,
        reference=best.reference_setpoint(),
        measured=best.zone_temp,
        zone_error=best.zone_error,
        has_demand=True,
    )
