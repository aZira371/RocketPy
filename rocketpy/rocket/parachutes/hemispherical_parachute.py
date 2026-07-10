from .parachute import Parachute


class HemisphericalParachute(Parachute):
    """Implements a hemispherical parachute.

    Specializes the generic :class:`Parachute
    <rocketpy.rocket.parachutes.parachute.Parachute>` model for hemispherical
    canopies, making the canopy geometry explicit. The descent dynamics are
    the same as the generic model, which already computes the added mass from
    an equivalent hemispheroid.

    Unlike the generic ``Parachute``, this class does not expose the ``noise``
    parameter. To simulate noisy trigger readings, attach a sensor with
    measurement noise to the rocket (see :class:`Barometer
    <rocketpy.sensors.barometer.Barometer>`) and read it from the trigger
    function instead.

    See Also
    --------
    :class:`Parachute <rocketpy.rocket.parachutes.parachute.Parachute>` for
    the documentation of all inherited attributes and of the descent dynamics.

    Attributes
    ----------
    HemisphericalParachute.parachute_type : string
        Set to "hemispherical".
    HemisphericalParachute.drag_coefficient : float
        Drag coefficient of the inflated hemispherical canopy, used only when
        ``radius`` is not provided to estimate the parachute radius from
        ``cd_s``: ``R = sqrt(cd_s / (drag_coefficient * pi))``. Default value
        is 1.4 (NASA SP-8066).
    HemisphericalParachute.radius : float
        Length of the non-unique semi-axis (radius) of the inflated
        hemispherical parachute in meters. If not provided at construction
        time, it is estimated from ``cd_s`` and ``drag_coefficient``.
    HemisphericalParachute.height : float
        Length of the unique semi-axis (height) of the inflated hemispherical
        parachute in meters. Default value is the radius of the parachute.
    """

    parachute_type = "hemispherical"

    def __init__(
        self,
        name,
        cd_s,
        trigger,
        sampling_rate,
        lag=0,
        radius=None,
        height=None,
        porosity=0.0432,
        drag_coefficient=1.4,
    ):
        """Initializes HemisphericalParachute class.

        Parameters
        ----------
        name : string
            Parachute name, such as drogue and main. Has no impact in
            simulation, as it is only used to display data in a more
            organized matter.
        cd_s : float
            Drag coefficient times reference area of the parachute.
        trigger : callable, float, str
            Defines the trigger condition for the parachute ejection system.
            See :class:`Parachute
            <rocketpy.rocket.parachutes.parachute.Parachute>` for the
            supported forms.
        sampling_rate : float
            Sampling rate in which the parachute trigger will be checked at.
            It is used to simulate the refresh rate of onboard sensors such
            as barometers. Default value is 100. Value must be given in hertz.
        lag : float, optional
            Time between the parachute ejection system is triggered and the
            parachute is fully opened. During this time, the simulation will
            consider the rocket as flying without a parachute. Default value
            is 0. Must be given in seconds.
        radius : float, optional
            Length of the non-unique semi-axis (radius) of the inflated
            hemispherical parachute. If not provided, it is estimated from
            ``cd_s`` and ``drag_coefficient`` using:
            ``radius = sqrt(cd_s / (drag_coefficient * pi))``.
            Units are in meters.
        height : float, optional
            Length of the unique semi-axis (height) of the inflated
            hemispherical parachute. Default value is the radius of the
            parachute. Units are in meters.
        porosity : float, optional
            Geometric porosity of the canopy (ratio of open area to total
            canopy area), in [0, 1]. Affects only the added-mass scaling
            during descent; it does not change ``cd_s`` (drag). The default
            value of 0.0432 is chosen so that the resulting
            ``added_mass_coefficient`` equals approximately 1.0 ("neutral"
            added-mass behavior).
        drag_coefficient : float, optional
            Drag coefficient of the inflated hemispherical canopy, used only
            when ``radius`` is not provided. It relates the aerodynamic
            ``cd_s`` to the physical canopy area via
            ``cd_s = drag_coefficient * pi * radius**2``. Default value is
            1.4 (NASA SP-8066). Has no effect when ``radius`` is explicitly
            provided.
        """
        super().__init__(
            name=name,
            cd_s=cd_s,
            trigger=trigger,
            sampling_rate=sampling_rate,
            lag=lag,
            radius=radius,
            height=height,
            porosity=porosity,
            drag_coefficient=drag_coefficient,
        )

    @classmethod
    def from_dict(cls, data):
        return cls(
            name=data["name"],
            cd_s=data["cd_s"],
            trigger=cls._decode_trigger(data["trigger"]),
            sampling_rate=data["sampling_rate"],
            lag=data.get("lag", 0),
            radius=data.get("radius", None),
            height=data.get("height", None),
            porosity=data.get("porosity", 0.0432),
            drag_coefficient=data.get("drag_coefficient", 1.4),
        )
