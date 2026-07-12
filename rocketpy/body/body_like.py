"""BodyLike protocol for the multistage mission architecture.

This module defines a structural typing contract so bodies can satisfy the
interface without inheriting from a shared base class.
"""

from typing import Protocol, runtime_checkable


@runtime_checkable
class BodyLike(Protocol):
    """Structural interface that every flight-ready body must satisfy.

    Any object that can be integrated by the Flight simulation engine
    must implement this interface.  Both the native :class:`FlightBody`
    and the :class:`RocketAdapter` (which wraps a legacy :class:`Rocket`)
    satisfy it, so that the simulation layer can treat them uniformly.
    This uses structural typing, so concrete bodies do not need to inherit
    from :class:`BodyLike` to be accepted by the simulation layer.

    Attributes
    ----------
    name : str
        Human-readable identifier for the body.
    """

    @property
    def name(self) -> str:
        """Human-readable name of the body.

        Returns
        -------
        str
            Body name.
        """
        ...

    def mass(self, t: float) -> float:
        """Total mass of the body at time *t*, in kg.

        Parameters
        ----------
        t : float
            Simulation time in seconds.

        Returns
        -------
        float
            Total mass in kg.
        """
        ...

    def inertia_tensor(self, t: float):
        """Inertia tensor of the body at time *t*, in kg·m².

        Parameters
        ----------
        t : float
            Simulation time in seconds.

        Returns
        -------
        array-like
            3×3 inertia tensor in kg·m².
        """
        ...

    def center_of_mass(self, t: float) -> float:
        """Position of the center of mass along the body axis at time *t*.

        The position is measured in meters relative to the body's own
        coordinate system origin.

        Parameters
        ----------
        t : float
            Simulation time in seconds.

        Returns
        -------
        float
            Center-of-mass position in meters.
        """
        ...

    def aerodynamic_model(self):
        """Return the aerodynamic model attached to this body.

        Returns
        -------
        object
            Aerodynamic model instance.
        """
        ...

    def propulsion_model(self):
        """Return the propulsion model attached to this body.

        Returns
        -------
        object
            Propulsion model instance.
        """
        ...

    def recovery_systems(self):
        """Return the list of recovery systems attached to this body.

        Returns
        -------
        list
            Recovery systems.
        """
        ...

    def sensors(self):
        """Return the list of sensors attached to this body.

        Returns
        -------
        list
            Sensor instances.
        """
        ...

    def controllers(self):
        """Return the list of active controllers attached to this body.

        Returns
        -------
        list
            Controller instances.
        """
        ...

    def coordinate_system_orientation(self) -> str:
        """Orientation convention for the body's coordinate system.

        Returns
        -------
        str
            One of ``"tail_to_nose"`` or ``"nose_to_tail"``.
        """
        ...

    def to_branch_ready_copy(self):
        """Return a simulation-ready deep copy of this body.

        The copy is detached from user-facing state so that the
        simulation engine can mutate it freely without side-effects.

        Returns
        -------
        BodyLike
            A deep copy suitable for a :class:`FlightBranch`.
        """
        ...
