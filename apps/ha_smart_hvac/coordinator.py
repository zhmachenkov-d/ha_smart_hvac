"""Multi-Zone Coordinator — Heating Demand gate."""

from __future__ import annotations

from ha_smart_hvac.models import ZoneSnapshot


def has_heating_demand(zones: list[ZoneSnapshot]) -> bool:
    """True when any zone has positive Zone Error among heating-eligible thermostats.

    Same eligibility as ZoneSnapshot.zone_error: -inf only when a zone has no
    heating-eligible thermostats; heating with non-positive error is finite and
    does not demand.
    """
    return any(z.zone_error > 0 for z in zones)
