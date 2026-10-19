"""Tests for Multi-Zone Coordinator — Heating Demand gate and CAP-7 selection."""

from ha_smart_hvac.coordinator import has_heating_demand, select_max_error_demand_zone
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


def test_multi_thermostat_zone_uses_max_error():
    """Intra-zone: zone_error is max over heating thermostats only."""
    zone = _zone("living_room", 19.0, [20.0, 22.0])
    assert zone.zone_error == 3.0
    assert has_heating_demand([zone]) is True


def test_idle_thermostat_does_not_beat_heating_thermostat():
    """Idle setpoint must not inflate zone_error past heating peers."""
    zone = _zone("living_room", 19.0, [22.0, 24.0], ["heating", "idle"])
    assert zone.zone_error == 3.0
    assert has_heating_demand([zone]) is True
    selected = select_max_error_demand_zone([zone], None)
    assert selected is not None
    assert selected.name == "living_room"


def test_unavailable_hvac_action_is_excluded():
    """hvac_action is None is not eligible — same as non-heating."""
    zone = _zone("living_room", 18.0, [22.0, 24.0], ["heating", None])
    assert zone.zone_error == 4.0
    assert has_heating_demand([zone]) is True


def test_zone_with_only_idle_thermostats_cannot_win_contention():
    zones = [
        _zone("bedroom", 17.0, [21.0], ["idle"]),
        _zone("living_room", 18.0, [21.0], ["heating"]),
    ]
    assert has_heating_demand(zones) is True
    selected = select_max_error_demand_zone(zones, None)
    assert selected is not None
    assert selected.name == "living_room"
    assert selected.zone_error == 3.0


def test_select_max_error_picks_largest_demand_error():
    zones = [
        _zone("living_room", 21.0, [22.0]),  # error 1
        _zone("bedroom", 17.0, [21.0]),  # error 4
    ]
    selected = select_max_error_demand_zone(zones, None)
    assert selected is not None
    assert selected.name == "bedroom"


def test_select_max_error_t_hold_keeps_previous_in_tie_set():
    zones = [
        _zone("alpha", 20.0, [22.0]),  # error 2
        _zone("beta", 20.0, [22.0]),  # error 2
    ]
    selected = select_max_error_demand_zone(zones, "beta")
    assert selected is not None
    assert selected.name == "beta"


def test_select_max_error_lex_when_no_previous_in_tie():
    zones = [
        _zone("alpha", 20.0, [22.0]),
        _zone("beta", 20.0, [22.0]),
    ]
    selected = select_max_error_demand_zone(zones, None)
    assert selected is not None
    assert selected.name == "alpha"


def test_select_max_error_ignores_non_demand_pool():
    zones = [
        _zone("satisfied", 22.0, [20.0]),  # error -2, no demand
        _zone("cold", 18.0, [22.0]),  # error 4
    ]
    selected = select_max_error_demand_zone(zones, "satisfied")
    assert selected is not None
    assert selected.name == "cold"


def test_select_max_error_empty_or_no_demand():
    assert select_max_error_demand_zone([], None) is None
    zones = [_zone("warm", 22.0, [20.0])]
    assert select_max_error_demand_zone(zones, None) is None
