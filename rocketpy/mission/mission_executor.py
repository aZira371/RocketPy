"""MissionExecutor – high-level API to execute all mission flight branches."""

from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

from rocketpy.body import RocketAdapter
from rocketpy.simulation import Flight


@runtime_checkable
class FlightCompatibleRocket(Protocol):
    """Structural contract for rocket objects accepted by Flight."""

    def add_motor(self, motor, position):
        """Add a motor to the rocket body."""

    def total_mass(self, t: float) -> float:
        """Return total mass at time *t*."""

    def center_of_mass(self, t: float) -> float:
        """Return center-of-mass position at time *t*."""


@dataclass(frozen=True)
class MissionExecutionResult:
    """Single execution output for one mission item."""

    item_name: str
    flight: Flight


class MissionExecutor:
    """Executes all mission stages/deployables from a :class:`Mission`.

    The executor provides a mission-first API: users configure mission items
    and optional per-item flight inputs in :class:`~rocketpy.mission.Mission`,
    then call :meth:`execute` once to run all corresponding flight simulations.
    """

    def __init__(
        self,
        mission,
        environment,
        rail_length: float,
        default_flight_inputs=None,
        flight_class=Flight,
    ):
        self.mission = mission
        self.environment = environment
        self.rail_length = rail_length
        self.default_flight_inputs = dict(default_flight_inputs or {})
        self.flight_class = flight_class

    def execute(self) -> list[MissionExecutionResult]:
        """Execute configured mission stage/deployable flights in order.

        Returns
        -------
        list[MissionExecutionResult]
            Flight results in mission order: stages first, then deployables.
        """
        results: list[MissionExecutionResult] = []
        previous_flight = None

        for item in self.mission.attached_items():
            rocket = self._extract_rocket(item.body)
            item_inputs = self.mission.get_flight_inputs(item)
            flight_inputs = dict(self.default_flight_inputs)
            flight_inputs.update(item_inputs)

            if "initial_solution" not in flight_inputs and previous_flight is not None:
                flight_inputs["initial_solution"] = previous_flight

            flight = self.flight_class(
                rocket=rocket,
                environment=self.environment,
                rail_length=self.rail_length,
                **flight_inputs,
            )
            results.append(MissionExecutionResult(item_name=item.name, flight=flight))
            previous_flight = flight

        return results

    @staticmethod
    def _extract_rocket(body: Any):
        """Extract a Flight-compatible rocket object from a mission body."""
        if isinstance(body, RocketAdapter):
            return body.rocket
        if isinstance(body, FlightCompatibleRocket):
            return body
        raise TypeError(
            "MissionExecutor currently supports Stage/Deployable bodies backed "
            "by RocketAdapter or by objects satisfying FlightCompatibleRocket."
        )
