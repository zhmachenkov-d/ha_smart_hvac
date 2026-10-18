"""Tests for Multi-Zone Coordinator."""

from ha_smart_hvac.coordinator import has_heating_demand, select_critical_zone
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


def test_picks_zone_with_largest_error():
    zones = [
        _zone("living_room", 18.0, [20.0]),
        _zone("bedroom", 17.0, [21.0]),
    ]
    decision = select_critical_zone(zones)
    assert decision.critical_zone == "bedroom"
    assert decision.zone_error == 4.0
    assert decision.reference == 21.0
    assert decision.measured == 17.0
    assert decision.has_demand is True


def test_multi_thermostat_zone_uses_max_error():
    zones = [
        _zone("living_room", 19.0, [20.0, 22.0]),
    ]
    decision = select_critical_zone(zones)
    assert decision.zone_error == 3.0
    assert decision.reference == 22.0


def test_no_demand_when_all_errors_non_positive():
    zones = [
        _zone("living_room", 21.0, [20.0]),
        _zone("bedroom", 20.5, [20.0]),
    ]
    decision = select_critical_zone(zones)
    assert decision.has_demand is False
    assert decision.critical_zone is None
    assert decision.zone_error == -0.5


def test_empty_zones():
    decision = select_critical_zone([])
    assert decision.has_demand is False


def test_idle_thermostat_does_not_beat_heating_thermostat():
    zones = [
        _zone("living_room", 19.0, [22.0, 24.0], ["heating", "idle"]),
    ]
    decision = select_critical_zone(zones)
    assert decision.critical_zone == "living_room"
    assert decision.zone_error == 3.0
    assert decision.reference == 22.0
    assert decision.has_demand is True


def test_all_idle_zone_has_no_demand():
    zones = [
        _zone("living_room", 18.0, [22.0], ["idle"]),
    ]
    decision = select_critical_zone(zones)
    assert decision.has_demand is False
    assert decision.critical_zone is None
    assert decision.reference is None
    assert decision.zone_error == float("-inf")


def test_unavailable_hvac_action_is_excluded():
    zones = [
        _zone("living_room", 18.0, [22.0, 24.0], ["heating", None]),
    ]
    decision = select_critical_zone(zones)
    assert decision.critical_zone == "living_room"
    assert decision.zone_error == 4.0
    assert decision.reference == 22.0
    assert decision.has_demand is True


def test_zone_with_only_idle_thermostats_cannot_win_contention():
    zones = [
        _zone("bedroom", 17.0, [21.0], ["idle"]),
        _zone("living_room", 18.0, [21.0], ["heating"]),
    ]
    decision = select_critical_zone(zones)
    assert decision.critical_zone == "living_room"
    assert decision.zone_error == 3.0
    assert decision.reference == 21.0
    assert decision.has_demand is True
