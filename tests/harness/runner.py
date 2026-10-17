"""Multi-tick closed-loop LADRC runner on a cascade lag plant (Hass-free)."""

from __future__ import annotations

from dataclasses import dataclass, field

from ha_smart_hvac.feedforward import weather_feedforward
from ha_smart_hvac.hvac_app import (
    advance_with_tracking_residue,
    guard_u_track,
    sticky_blow_up_latch,
)
from ha_smart_hvac.ladrc import LadrcState
from ha_smart_hvac.models import LadrcConfig, WeatherFeedforwardConfig
from harness.plant import CascadeLagPlant


@dataclass
class ClosedLoopSeries:
    """Per-tick logged fields (see plan series legend)."""

    command: list[float] = field(default_factory=list)
    y: list[float] = field(default_factory=list)
    u_track: list[float] = field(default_factory=list)
    z1: list[float] = field(default_factory=list)
    z2: list[float] = field(default_factory=list)
    u_ff: list[float] = field(default_factory=list)
    tripped: list[bool] = field(default_factory=list)
    latch: list[bool] = field(default_factory=list)

    def __len__(self) -> int:
        return len(self.command)


def run_closed_loop(
    *,
    n_ticks: int,
    y0: float,
    reference: float,
    critical_zone: str,
    outdoor: float,
    plant_k: float,
    plant_t: float,
    plant_n: int,
    setpoint_min: float,
    setpoint_max: float,
    ladrc_config: LadrcConfig,
    ff_config: WeatherFeedforwardConfig,
    zero_uff: bool = False,
) -> ClosedLoopSeries:
    """Run N closed-loop ticks; fresh plant/LADRC/latch each call.

    Tick contract (App write path, simulated write always succeeds):
    u_ff → track → guard → sticky latch → reset-on-trip → residue advance → plant.step.
    """
    plant = CascadeLagPlant(plant_k, plant_t, plant_n, ladrc_config.dt, y0=y0)
    ladrc = LadrcState()
    latch = False
    series = ClosedLoopSeries()

    for _ in range(n_ticks):
        y = plant.y
        u_ff = 0.0 if zero_uff else weather_feedforward(outdoor, ff_config)
        u_track = ladrc.compute_tracking(y, reference, ladrc_config, critical_zone)
        guard = guard_u_track(
            u_track,
            u_ff,
            ladrc_config.u_track_max,
            setpoint_min,
            setpoint_max,
            latch,
        )
        latch = sticky_blow_up_latch(
            latch,
            guard.tripped,
            u_track,
            ladrc_config.u_track_max,
        )
        if guard.tripped:
            ladrc.reset(y)
        advance_with_tracking_residue(
            ladrc,
            y,
            guard.command,
            u_ff,
            ladrc_config,
        )
        plant.step(guard.command)

        series.command.append(guard.command)
        series.y.append(y)
        series.u_track.append(u_track)
        series.z1.append(ladrc.z1)
        series.z2.append(ladrc.z2)
        series.u_ff.append(u_ff)
        series.tripped.append(guard.tripped)
        series.latch.append(latch)

    return series
