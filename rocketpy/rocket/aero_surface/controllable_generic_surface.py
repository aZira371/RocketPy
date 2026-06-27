from rocketpy.rocket.aero_surface.generic_surface import GenericSurface


class ControllableGenericSurface(GenericSurface):
    """A generic aerodynamic surface whose coefficients additionally depend on
    one or more **control-deflection** variables (canards, grid fins, elevons,
    air-brake deployment, …) sourced at runtime from a controller.

    On top of the seven standard independent variables of
    :class:`GenericSurface` (``alpha``, ``beta``, ``mach``, ``reynolds``,
    ``pitch_rate``, ``yaw_rate``, ``roll_rate``), the coefficient functions take
    one extra argument per entry of ``controls`` (appended in order). The
    current control values are held in :attr:`control_state` and mutated each
    simulation step by a controller (see ``Rocket.add_controllable_surface``);
    :meth:`_coefficient_arguments` appends them to every coefficient evaluation.

    Attributes
    ----------
    ControllableGenericSurface.control_variables : list of str
        Names of the control-deflection axes, in coefficient-argument order.
    ControllableGenericSurface.control_state : dict
        Current value of each control variable (defaults to 0).
    """

    def __init__(
        self,
        reference_area,
        reference_length,
        coefficients,
        center_of_pressure=(0, 0, 0),
        name="Controllable Generic Surface",
        controls=("deflection",),
    ):
        """Create a controllable generic aerodynamic surface.

        Parameters
        ----------
        reference_area : int, float
            Reference area of the surface, in squared meters.
        reference_length : int, float
            Reference length of the surface, in meters.
        coefficients : dict
            Aerodynamic coefficients (``cL``, ``cQ``, ``cD``, ``cm``, ``cn``,
            ``cl``), each a callable/CSV/Function of the seven base variables
            **plus** the control variables listed in ``controls`` (appended in
            order). Omitted coefficients default to 0.
        center_of_pressure : tuple, list, optional
            Application point of the aerodynamic forces and moments in the local
            surface frame. Default ``(0, 0, 0)``.
        name : str, optional
            Name of the surface. Default ``"Controllable Generic Surface"``.
        controls : iterable of str, optional
            Names of the control-deflection axes. Default ``("deflection",)``.
            Each name becomes an extra coefficient argument and a key in
            :attr:`control_state`.
        """
        # These must be set before ``super().__init__`` so coefficient
        # processing (arity, CSV validation) and the derived-cp accessors see
        # the extended variable list (via the ``independent_vars`` property,
        # which appends ``control_variables``) and the current control values.
        self.control_variables = list(controls)
        self.control_state = {name: 0.0 for name in self.control_variables}

        super().__init__(
            reference_area=reference_area,
            reference_length=reference_length,
            coefficients=coefficients,
            center_of_pressure=center_of_pressure,
            name=name,
        )
        # ``self.prints``/``self.plots`` are the generic ones wired by the base.

    def _coefficient_arguments(
        self,
        alpha,
        beta,
        mach,
        reynolds,
        pitch_rate,
        yaw_rate,
        roll_rate,
        alpha_dot=0.0,
        beta_dot=0.0,
    ):
        """Append the current control-variable values (in
        ``self.control_variables`` order) to the standard inputs (which may
        already include the unsteady ``alpha_dot``/``beta_dot`` axes)."""
        base = super()._coefficient_arguments(
            alpha,
            beta,
            mach,
            reynolds,
            pitch_rate,
            yaw_rate,
            roll_rate,
            alpha_dot,
            beta_dot,
        )
        controls = tuple(self.control_state[name] for name in self.control_variables)
        return base + controls

    def _clamp_control(self, name, value):  # pylint: disable=unused-argument
        """Hook to constrain a control value before it is stored. The base class
        applies no clamping; subclasses (e.g. ``AirBrakes``) may override."""
        return value

    def set_control(self, name, value):
        """Set the current value of a control variable (applying any clamping).

        Parameters
        ----------
        name : str
            Name of the control variable; must be one of
            :attr:`control_variables`.
        value : float
            New control value.
        """
        if name not in self.control_state:
            raise KeyError(
                f"Unknown control variable '{name}'. "
                f"Valid controls are: {self.control_variables}."
            )
        self.control_state[name] = self._clamp_control(name, value)

    def get_control(self, name):
        """Return the current value of a control variable."""
        return self.control_state[name]

    def to_dict(self, include_outputs=False):  # pylint: disable=unused-argument
        return {
            "reference_area": self.reference_area,
            "reference_length": self.reference_length,
            "coefficients": {
                "cL": self.cL,
                "cQ": self.cQ,
                "cD": self.cD,
                "cm": self.cm,
                "cn": self.cn,
                "cl": self.cl,
            },
            "center_of_pressure": self.center_of_pressure,
            "name": self.name,
            "controls": self.control_variables,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            reference_area=data["reference_area"],
            reference_length=data["reference_length"],
            coefficients=data["coefficients"],
            center_of_pressure=data.get("center_of_pressure", (0, 0, 0)),
            name=data.get("name", "Controllable Generic Surface"),
            controls=data.get("controls", ("deflection",)),
        )
