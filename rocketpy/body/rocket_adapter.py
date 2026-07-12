"""RocketAdapter – wraps a legacy :class:`Rocket` as a :class:`BodyLike`."""

from copy import deepcopy


class RocketAdapter:
    """Adapts a legacy :class:`~rocketpy.rocket.Rocket` to the
    :class:`BodyLike` interface.

    This allows the existing :class:`~rocketpy.rocket.Rocket` builder to be
    consumed by the new multistage simulation infrastructure without any
    changes to the ``Rocket`` class itself.

    Parameters
    ----------
    rocket : :class:`~rocketpy.rocket.Rocket`
        The rocket instance to adapt.

    Attributes
    ----------
    rocket : :class:`~rocketpy.rocket.Rocket`
        The wrapped rocket instance.
    """

    def __init__(self, rocket):
        self.rocket = rocket

    # ------------------------------------------------------------------
    # BodyLike interface
    # ------------------------------------------------------------------

    @property
    def name(self) -> str:
        """Name of the underlying rocket.

        Returns
        -------
        str
            ``rocket.name`` if present, otherwise ``"<unnamed>"``.
        """
        return getattr(self.rocket, "name", "<unnamed>")

    def mass(self, t: float) -> float:
        """Total rocket mass at time *t*, in kg.

        Delegates to ``rocket.total_mass(t)``.

        Parameters
        ----------
        t : float
            Simulation time in seconds.

        Returns
        -------
        float
            Total mass in kg.
        """
        return self.rocket.total_mass(t)

    def inertia_tensor(self, t: float):
        """Inertia tensor at time *t*, in kg·m².

        Returns a 3×3 matrix built from the scalar inertia components
        available on the rocket.

        Parameters
        ----------
        t : float
            Simulation time in seconds.

        Returns
        -------
        tuple[float, float, float, float, float, float]
            Components ``(I_11, I_22, I_33, I_12, I_13, I_23)`` in kg·m².
        """
        r = self.rocket
        return (
            r.I_11(t),
            r.I_22(t),
            r.I_33(t),
            r.I_12(t),
            r.I_13(t),
            r.I_23(t),
        )

    def center_of_mass(self, t: float) -> float:
        """Axial position of the center of mass at time *t*, in m.

        Parameters
        ----------
        t : float
            Simulation time in seconds.

        Returns
        -------
        float
            Center-of-mass position in meters.
        """
        return self.rocket.center_of_mass(t)

    def aerodynamic_model(self):
        """Return the rocket's aerodynamic surfaces collection.

        Returns
        -------
        list
            ``rocket.aerodynamic_surfaces``.
        """
        return self.rocket.aerodynamic_surfaces

    def propulsion_model(self):
        """Return the rocket's motor.

        Returns
        -------
        Motor
            ``rocket.motor``.
        """
        return self.rocket.motor

    def recovery_systems(self):
        """Return the rocket's parachute list.

        Returns
        -------
        list
            ``rocket.parachutes``.
        """
        return self.rocket.parachutes

    def sensors(self):
        """Return the sensors attached to the rocket.

        Accesses ``rocket.sensors`` when available, which is a public
        :class:`~rocketpy.rocket.Components` collection on the
        :class:`~rocketpy.rocket.Rocket` class in newer Rocket
        configurations.

        Returns
        -------
        list or Components
            ``rocket.sensors``, or an empty list if the attribute is absent.
        """
        return getattr(self.rocket, "sensors", [])

    def controllers(self):
        """Return the active controllers attached to the rocket.

        Accesses ``rocket._controllers``, which is a private list on the
        :class:`~rocketpy.rocket.Rocket` class.

        Returns
        -------
        list
            ``rocket._controllers``, or an empty list if the attribute is
            absent.
        """
        return getattr(self.rocket, "_controllers", [])

    def coordinate_system_orientation(self) -> str:
        """Coordinate system orientation of the underlying rocket.

        Returns
        -------
        str
            ``rocket.coordinate_system_orientation``.
        """
        return self.rocket.coordinate_system_orientation

    def to_branch_ready_copy(self):
        """Return a deep copy of this adapter suitable for a FlightBranch.

        Returns
        -------
        RocketAdapter
            Deep copy with a cloned rocket.
        """
        return deepcopy(self)
