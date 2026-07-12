"""BodyResolver – resolves mission bodies to BodyLike / Flight-compatible rockets."""

from typing import Any, Protocol, runtime_checkable

from rocketpy.body.body_like import BodyLike
from rocketpy.body.flight_body import FlightBody
from rocketpy.body.rocket_adapter import RocketAdapter


@runtime_checkable
class FlightCompatibleRocket(Protocol):
    """Structural contract for rocket objects accepted by Flight."""

    def add_motor(self, motor, position):
        """Add a motor to the rocket body."""

    def total_mass(self, t: float) -> float:
        """Return total mass at time *t*."""

    def center_of_mass(self, t: float) -> float:
        """Return center-of-mass position at time *t*."""


class BodyResolver:
    """Resolves mission bodies (``Rocket``, ``RocketAdapter``, ``FlightBody``, ...)
    into the shapes the simulation engine needs.

    This is a two-step resolver:

    1. :meth:`to_body` resolves any supported source into a :class:`BodyLike`.
       This step is intentionally permissive – a bare :class:`FlightBody` is a
       legitimate ``BodyLike`` for mission-level bookkeeping (e.g.
       :meth:`~rocketpy.mission.Mission.describe`), even though it cannot yet
       drive a real :class:`~rocketpy.simulation.Flight`.
    2. :meth:`to_flight_rocket` takes a resolved :class:`BodyLike` and returns
       an object that can be passed as ``Flight(rocket=...)``. This is where
       bodies that cannot actually fly (today, a bare :class:`FlightBody`) are
       rejected with a clear, actionable error instead of failing silently or
       deep inside ``Flight``'s constructor.
    """

    @staticmethod
    def to_body(source: Any) -> BodyLike:
        """Resolve *source* to a :class:`BodyLike`.

        Parameters
        ----------
        source : Rocket, RocketAdapter, FlightBody, or FlightCompatibleRocket
            The mission body to resolve.

        Returns
        -------
        BodyLike
            A body satisfying the :class:`BodyLike` interface.

        Raises
        ------
        TypeError
            If *source* cannot be resolved to a :class:`BodyLike`.
        """
        if isinstance(source, (RocketAdapter, FlightBody)):
            return source
        if isinstance(source, BodyLike):
            return source
        if hasattr(source, "as_body"):
            return source.as_body()
        if isinstance(source, FlightCompatibleRocket):
            return RocketAdapter(source)
        raise TypeError(
            f"BodyResolver cannot resolve {type(source).__name__!r} to a BodyLike. "
            "Supported sources: Rocket, RocketAdapter, FlightBody, or objects "
            "satisfying FlightCompatibleRocket."
        )

    @staticmethod
    def to_flight_rocket(body: BodyLike):
        """Return a Flight-compatible rocket object for *body*.

        Parameters
        ----------
        body : BodyLike
            A body previously resolved via :meth:`to_body`.

        Returns
        -------
        FlightCompatibleRocket
            An object that can be passed as ``Flight(rocket=...)``.

        Raises
        ------
        TypeError
            If *body* cannot drive a :class:`~rocketpy.simulation.Flight` yet.
            This is always the case for a bare :class:`FlightBody`, since it
            does not implement ``total_mass()``/``add_motor()``.
        """
        if isinstance(body, RocketAdapter):
            return body.rocket
        if isinstance(body, FlightCompatibleRocket):
            return body
        if isinstance(body, FlightBody):
            raise TypeError(
                f"Cannot build a Flight from FlightBody {body.name!r}: FlightBody "
                "does not implement total_mass()/add_motor() and cannot drive "
                "Flight's physics engine directly yet. Use a Rocket (optionally "
                "wrapped in RocketAdapter) for real flight execution; "
                "FlightBody-driven Flight integration is planned future work."
            )
        raise TypeError(
            f"BodyResolver cannot use {type(body).__name__!r} to construct a "
            "Flight. Supported bodies: a Rocket (optionally wrapped in "
            "RocketAdapter), or any object satisfying FlightCompatibleRocket "
            "(add_motor, total_mass, center_of_mass). A bare FlightBody is also "
            "not yet supported for Flight execution."
        )
