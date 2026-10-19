"""Multi-Zone Coordinator — Heating Demand gate and CAP-7 zone selection."""

from __future__ import annotations

from ha_smart_hvac.models import ZoneSnapshot


def has_heating_demand(zones: list[ZoneSnapshot]) -> bool:
    """True when any zone has positive Zone Error among heating-eligible thermostats.

    Same eligibility as ZoneSnapshot.zone_error: -inf only when a zone has no
    heating-eligible thermostats; heating with non-positive error is finite and
    does not demand.
    """
    return any(z.zone_error > 0 for z in zones)


def select_max_error_demand_zone(
    zones: list[ZoneSnapshot], previous_name: str | None
) -> ZoneSnapshot | None:
    """Select the max Zone Error demand zone for CAP-7 rise-rate (FF params only).

    Among zones with Heating Demand (`zone_error > 0`), pick the largest error.
    T-hold: keep ``previous_name`` while it remains in the max-error tie set;
    otherwise break ties by lexicographic ``name``.
    """
    demand = [z for z in zones if z.zone_error > 0]
    if not demand:
        return None
    max_error = max(z.zone_error for z in demand)
    tie_set = [z for z in demand if z.zone_error == max_error]
    if previous_name is not None:
        for zone in tie_set:
            if zone.name == previous_name:
                return zone
    return min(tie_set, key=lambda z: z.name)
