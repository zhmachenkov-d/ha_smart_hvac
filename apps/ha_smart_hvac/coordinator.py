"""Multi-Zone Coordinator — Heating Demand gate and CAP-7 zone selection."""

from __future__ import annotations

import math

from ha_smart_hvac.models import ZoneSnapshot


def has_heating_demand(zones: list[ZoneSnapshot]) -> bool:
    """True when any zone has a thermostat with hvac_action == heating.

    Same eligibility as ZoneSnapshot.has_heating_eligible / zone_error
    contributors. Zone Error sign does not gate demand.
    """
    return any(z.has_heating_eligible for z in zones)


def select_max_error_demand_zone(
    zones: list[ZoneSnapshot], previous_name: str | None
) -> ZoneSnapshot | None:
    """Select the max Zone Error demand zone for CAP-7 rise-rate (FF params only).

    Among zones with Heating Demand (has_heating_eligible), pick the largest
    finite error (may be ≤ 0). Non-finite errors rank below any finite; if all
    demand errors are non-finite, still return a zone from that pool (CAP-7 M2
    flush). T-hold: keep ``previous_name`` while it remains in the max-error
    tie set; otherwise break ties by lexicographic ``name``.
    """
    demand = [z for z in zones if z.has_heating_eligible]
    if not demand:
        return None
    finite = [z for z in demand if math.isfinite(z.zone_error)]
    if finite:
        max_error = max(z.zone_error for z in finite)
        tie_set = [z for z in finite if z.zone_error == max_error]
    else:
        tie_set = demand
    if previous_name is not None:
        for zone in tie_set:
            if zone.name == previous_name:
                return zone
    return min(tie_set, key=lambda z: z.name)
