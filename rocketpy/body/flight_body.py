"""FlightBody – a first-class, fully configurable flight body."""

from copy import deepcopy


class FlightBody:
    """A fully configurable flight body composed of interchangeable models.

    Unlike :class:`~rocketpy.rocket.Rocket`, which is a rich user-facing
    builder object, :class:`FlightBody` is designed as a clean value object
    that holds just enough information for the simulation engine to integrate
    the equations of motion.  Users who need the full Rocket builder
    experience can convert a :class:`~rocketpy.rocket.Rocket` to a
    :class:`FlightBody` via :class:`RocketAdapter`.  It satisfies the
    :class:`~rocketpy.body.BodyLike` protocol.

    Parameters
    ----------
    name : str
        Human-readable name for this body.
    geometry : object
        External geometry description (e.g. a reference radius value or a
        geometry model object).
    mass_model : callable
        Callable ``mass_model(t) -> float`` returning total mass in kg at
        time *t* (seconds).
    inertia_model : callable
        Callable ``inertia_model(t)`` returning a 3×3 inertia tensor (kg·m²)
        at time *t*.
    center_of_mass_model : callable
        Callable ``center_of_mass_model(t) -> float`` returning the axial
        position of the center of mass in meters at time *t*.
    aero_model : object, optional
        Aerodynamic model for the body.
    propulsion : object, optional
        Propulsion model for the body.
    recovery_systems : list, optional
        Recovery systems attached to this body.
    sensors : list, optional
        Sensors attached to this body.
    controllers : list, optional
        Active controllers attached to this body.
    coordinate_system_orientation : str, optional
        Orientation of the body's coordinate system.  Must be
        ``"tail_to_nose"`` (default) or ``"nose_to_tail"``.

    Attributes
    ----------
    name : str
    geometry : object
    mass_model : callable
    inertia_model : callable
    aero_model : object
    propulsion_model : object
    recovery_systems : list
    sensors : list
    controllers : list
    coordinate_system_orientation : str
    """

    def __init__(
        self,
        name,
        geometry,
        mass_model,
        inertia_model,
        center_of_mass_model,
        aero_model=None,
        propulsion=None,
        recovery_systems=None,
        sensors=None,
        controllers=None,
        coordinate_system_orientation="tail_to_nose",
    ):
        self._name = name
        self.geometry = geometry
        self.mass_model = mass_model
        self.inertia_model = inertia_model
        self._center_of_mass_model = center_of_mass_model
        self.aero_model = aero_model
        self._propulsion_model = propulsion
        self._recovery_systems = list(recovery_systems or [])
        self._sensors = list(sensors or [])
        self._controllers = list(controllers or [])
        self._coordinate_system_orientation = coordinate_system_orientation

    # ------------------------------------------------------------------
    # BodyLike interface
    # ------------------------------------------------------------------

    @property
    def name(self) -> str:
        return self._name

    def mass(self, t: float) -> float:
        """Total body mass at time *t*, in kg."""
        return self.mass_model(t)

    def inertia_tensor(self, t: float):
        """3×3 inertia tensor at time *t*, in kg·m²."""
        return self.inertia_model(t)

    def center_of_mass(self, t: float) -> float:
        """Axial position of the center of mass at time *t*, in m."""
        return self._center_of_mass_model(t)

    def aerodynamic_model(self):
        return self.aero_model

    def propulsion_model(self):
        return self._propulsion_model

    def recovery_systems(self):
        """Return the recovery systems attached to this body."""
        return self._recovery_systems

    def sensors(self):
        return self._sensors

    def controllers(self):
        return self._controllers

    def coordinate_system_orientation(self) -> str:
        return self._coordinate_system_orientation

    def to_branch_ready_copy(self):
        """Return a deep copy suitable for use in a :class:`FlightBranch`."""
        return deepcopy(self)

    # ------------------------------------------------------------------
    # Mutating helpers
    # ------------------------------------------------------------------

    def add_recovery_system(self, system):
        """Attach a recovery system to this body.

        Parameters
        ----------
        system : object
            Recovery system to add.
        """
        self._recovery_systems.append(system)

    def add_sensor(self, sensor):
        """Attach a sensor to this body.

        Parameters
        ----------
        sensor : object
            Sensor to add.
        """
        self._sensors.append(sensor)

    def add_controller(self, controller):
        """Attach a controller to this body.

        Parameters
        ----------
        controller : object
            Controller to add.
        """
        self._controllers.append(controller)
