"""MissionExecutor – high-level API to execute all mission flight branches."""

from copy import deepcopy
from dataclasses import dataclass
from numbers import Real
from typing import Any, Protocol, runtime_checkable

from rocketpy.body import FlightBody, RocketAdapter
from rocketpy.rocket import PointMassRocket
from rocketpy.simulation import Flight

DEFAULT_FLIGHT_BODY_DRAG_COEFFICIENT = 0.75


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
        if isinstance(body, FlightBody):
            return MissionExecutor._build_point_mass_from_flight_body(body)
        if isinstance(body, FlightCompatibleRocket):
            return body
        raise TypeError(
            "MissionExecutor currently supports Stage/Deployable bodies backed "
            "by RocketAdapter, FlightBody, or by objects satisfying "
            "FlightCompatibleRocket."
        )

    @staticmethod
    def _build_point_mass_from_flight_body(body: FlightBody) -> PointMassRocket:
        """Build a PointMassRocket proxy from a FlightBody mission item.

        Notes
        -----
        This proxy uses the `FlightBody` snapshot at ``t=0`` for dry mass and
        center of mass. This is a pragmatic approximation for mission execution
        of deployables, especially passive payloads and recovery-only bodies,
        and may be less representative for strongly time-varying bodies.
        """
        radius = MissionExecutor._extract_reference_radius(body.geometry)
        # Use t=0 as a stable initialization snapshot for point-mass proxy setup.
        mass = body.mass(0.0)
        center_of_mass = body.center_of_mass(0.0)
        # Conservative default Cd for a generic bluff-body payload proxy.
        # These can be superseded by parachute/recovery deployment dynamics.
        default_drag_coefficient = DEFAULT_FLIGHT_BODY_DRAG_COEFFICIENT
        rocket = PointMassRocket(
            radius=radius,
            mass=mass,
            center_of_mass_without_motor=center_of_mass,
            power_off_drag=default_drag_coefficient,
            power_on_drag=default_drag_coefficient,
        )
        rocket.name = body.name

        orientation = body.coordinate_system_orientation()
        # PointMassRocket currently has no public API to re-evaluate `_csys`
        # after initialization, so we synchronize both orientation fields here.
        # TODO: Replace this with a public PointMassRocket orientation API.
        rocket.coordinate_system_orientation = orientation
        rocket._csys = 1 if orientation == "tail_to_nose" else -1

        # Recovery systems are pre-built Parachute objects on FlightBody; assign
        # deep-copied instances directly to preserve trigger/lags/noise settings.
        rocket.parachutes = [deepcopy(system) for system in body.recovery_systems()]

        propulsion = body.propulsion_model()
        if propulsion is not None:
            nozzle_position = getattr(propulsion, "nozzle_position", 0.0)
            rocket.add_motor(deepcopy(propulsion), position=nozzle_position)

        return rocket

    @staticmethod
    def _extract_reference_radius(geometry: Any) -> float:
        """Extract a positive reference radius from a FlightBody geometry field."""
        candidates = [geometry]
        for attr in ("radius", "reference_radius"):
            candidates.append(getattr(geometry, attr, None))

        for candidate in candidates:
            if isinstance(candidate, Real):
                radius = float(candidate)
                if radius > 0:
                    return radius
                raise ValueError(
                    "FlightBody geometry radius must be a positive value, got "
                    f"{radius}."
                )

        raise TypeError(
            "MissionExecutor could not infer a reference radius from FlightBody "
            "geometry. Provide a numeric geometry value or an object exposing "
            "'radius' or 'reference_radius'."
        )
