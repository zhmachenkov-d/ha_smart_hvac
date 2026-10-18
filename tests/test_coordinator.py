"""Tests for Multi-Zone Coordinator — Heating Demand gate."""

from ha_smart_hvac.coordinator import has_heating_demand
from ha_smart_hvac.models import ThermostatReading, ZoneSnapshot


def _zone(
    name: str,
    temp: float,
    setpoints: list[float],
    hvac_actions: list[str | None] | None = None,
) -> ZoneSnapshot:
    actions = hvac_actions or ["heating"] * len(setpoints)
    thermostats = tuple(
        ThermostatReading(
            f"climate.{name}_{i}",
            sp,
            actions[i],
        )
        for i, sp in enumerate(setpoints)
    )
    return ZoneSnapshot(name=name, zone_temp=temp, thermostats=thermostats)


def test_has_heating_demand_when_any_zone_positive_error():
    zones = [
        _zone("living_room", 21.0, [20.0]),
        _zone("bedroom", 17.0, [21.0]),
    ]
    assert has_heating_demand(zones) is True


def test_has_heating_demand_false_when_all_errors_non_positive():
    zones = [
        _zone("living_room", 21.0, [20.0]),
        _zone("bedroom", 20.5, [20.0]),
    ]
    assert has_heating_demand(zones) is False


def test_has_heating_demand_empty_zones():
    assert has_heating_demand([]) is False


def test_all_idle_zone_has_no_demand_via_has_heating_demand():
    zones = [
        _zone("living_room", 18.0, [22.0], ["idle"]),
    ]
    assert has_heating_demand(zones) is False


def test_has_heating_demand_ignores_non_heating_even_with_large_delta():
    zones = [
        _zone("bedroom", 10.0, [22.0], ["idle"]),
        _zone("living_room", 21.0, [20.0], ["heating"]),
    ]
    assert has_heating_demand(zones) is False
