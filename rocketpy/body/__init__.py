"""rocketpy.body – body abstraction layer for multistage simulation."""

from rocketpy.body.body_like import BodyLike
from rocketpy.body.flight_body import FlightBody
from rocketpy.body.rocket_adapter import RocketAdapter

__all__ = ["BodyLike", "FlightBody", "RocketAdapter"]
