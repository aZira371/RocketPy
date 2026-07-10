import copy
import inspect
import math

import numpy as np

from rocketpy.mathutils import Function
from rocketpy.mathutils.vector_matrix import Matrix, Vector
from rocketpy.plots.aero_surface_plots import _GenericSurfacePlots
from rocketpy.prints.aero_surface_prints import _GenericSurfacePrints
from rocketpy.rocket.aero_surface.aero_coefficient import (
    AeroCoefficient,
    build_independent_vars,
)


def _as_function(func, independent_vars, name):
    """Wrap a variadic callable as a :class:`Function` over ``independent_vars``.

    ``Function`` reads its domain dimension from the callable's parameter count,
    so a variadic wrapper is given an explicit signature to advertise one
    parameter per independent variable.
    """
    func.__signature__ = inspect.Signature(
        inspect.Parameter(var, inspect.Parameter.POSITIONAL_OR_KEYWORD)
        for var in independent_vars
    )
    return Function(func, list(independent_vars), [name])


def wind_to_body_coefficients(c_lift, c_drag, c_side, independent_vars):
    """Rotate wind-frame force coefficients into the body frame.

    Given the lift, drag and side-force coefficients (each callable over the
    surface's independent-variable tuple, with the angle of attack and sideslip
    as the first two variables), return the body-frame normal, side and axial
    coefficients ``(cN, cY, cA)`` as :class:`Function`s over the same variables.
    """
    lift, drag, side = c_lift.get_value_opt, c_drag.get_value_opt, c_side.get_value_opt

    def normal(*args):
        alpha, beta = args[0], args[1]
        transverse = math.sin(beta) * side(*args) + math.cos(beta) * drag(*args)
        return math.cos(alpha) * lift(*args) + math.sin(alpha) * transverse

    def yaw_side(*args):
        beta = args[1]
        return math.cos(beta) * side(*args) - math.sin(beta) * drag(*args)

    def axial(*args):
        alpha, beta = args[0], args[1]
        transverse = math.sin(beta) * side(*args) + math.cos(beta) * drag(*args)
        return -math.sin(alpha) * lift(*args) + math.cos(alpha) * transverse

    return (
        _as_function(normal, independent_vars, "cN"),
        _as_function(yaw_side, independent_vars, "cY"),
        _as_function(axial, independent_vars, "cA"),
    )


def body_to_wind_coefficients(c_normal, c_side, c_axial, independent_vars):
    """Rotate body-frame force coefficients into the wind frame.

    Inverse of :func:`wind_to_body_coefficients`: given the body-frame normal,
    side and axial coefficients, return the wind-frame lift, drag and
    side-force coefficients ``(cL, cD, cQ)`` as :class:`Function`s.
    """
    normal = c_normal.get_value_opt
    side = c_side.get_value_opt
    axial = c_axial.get_value_opt

    def lift(*args):
        alpha = args[0]
        return math.cos(alpha) * normal(*args) - math.sin(alpha) * axial(*args)

    def drag(*args):
        alpha, beta = args[0], args[1]
        longitudinal = math.sin(alpha) * normal(*args) + math.cos(alpha) * axial(*args)
        return -math.sin(beta) * side(*args) + math.cos(beta) * longitudinal

    def yaw_side(*args):
        alpha, beta = args[0], args[1]
        longitudinal = math.sin(alpha) * normal(*args) + math.cos(alpha) * axial(*args)
        return math.cos(beta) * side(*args) + math.sin(beta) * longitudinal

    return (
        _as_function(lift, independent_vars, "cL"),
        _as_function(drag, independent_vars, "cD"),
        _as_function(yaw_side, independent_vars, "cQ"),
    )


class GenericSurface:
    """Defines a generic aerodynamic surface with custom force and moment
    coefficients. The coefficients can be nonlinear functions of the angle of
    attack, sideslip angle, Mach number, Reynolds number, pitch rate, yaw rate
    and roll rate."""

    # Whether this surface contributes identically to the pitch and yaw planes.
    # ``False`` for a generic surface (its coefficients may differ between planes)
    is_axisymmetric = False

    def __init__(
        self,
        reference_area,
        reference_length,
        coefficients,
        center_of_pressure=(0, 0, 0),
        name="Generic Surface",
        unsteady_aero=False,
        interpolation=None,
        extrapolation=None,
        force_convention=None,
    ):
        """Create a generic aerodynamic surface, defined by its aerodynamic
        coefficients. This surface is used to model any aerodynamic surface
        that does not fit the predefined classes.

        Important
        ---------
        All the aerodynamic coefficients can be input as callable functions of
        angle of attack, angle of sideslip, Mach number, Reynolds number,
        pitch rate, yaw rate and roll rate. For CSV files, the header must
        contain at least one of the following: "alpha", "beta", "mach",
        "reynolds", "pitch_rate", "yaw_rate" and "roll_rate". The
        independent variable columns can be provided in any order.

        When ``unsteady_aero`` is True, the coefficients may additionally be
        functions of the flow-angle rates "alpha_dot" and "beta_dot", which are
        appended (in that order) after "roll_rate": callables must accept the
        two extra trailing arguments and CSV files may include "alpha_dot" and
        "beta_dot" columns.

        The angular-rate inputs ("pitch_rate", "yaw_rate", "roll_rate") are the
        conventional **non-dimensional reduced rates**, ``q* = q * L_ref / (2 * V)``
        (and likewise for ``r``/``p``), matching how published and tool-generated
        aerotables (Missile DATCOM, OpenVSP, CFD/wind-tunnel data) tabulate rate
        derivatives. Provide coefficient tables against the reduced rates, not the
        raw body rates in rad/s.

        See Also
        --------
        :ref:`genericsurfaces`.

        Parameters
        ----------
        reference_area : int, float
            Reference area of the aerodynamic surface. Has the unit of meters
            squared. Commonly defined as the rocket's cross-sectional area.
        reference_length : int, float
            Reference length of the aerodynamic surface. Has the unit of meters.
            Commonly defined as the rocket's diameter.
        coefficients: dict
            The six force and moment coefficients, by name. Any you leave out are
            set to 0. Each one can be a constant number, a function of the flow
            variables, a list of data points, or a path to a CSV file. By default
            the force coefficients are the body-frame ones (see
            ``force_convention``); the wind-frame names ``cL``/``cQ``/``cD`` are
            also accepted. The coefficients are:\n
            cN: str, callable, optional
                Normal force coefficient (body frame). Default is 0.\n
            cY: str, callable, optional
                Side force coefficient (body frame). Default is 0.\n
            cA: str, callable, optional
                Axial force coefficient (body frame). Default is 0.\n
            cm: str, callable, optional
                Pitch moment coefficient. Default is 0.\n
            cn: str, callable, optional
                Yaw moment coefficient. Default is 0.\n
            cl: str, callable, optional
                Roll moment coefficient. Default is 0.\n
        center_of_pressure : tuple, list, optional
            Application point of the aerodynamic forces and moments. The
            center of pressure is defined in the local coordinate system of the
            aerodynamic surface. The default value is (0, 0, 0).
        name : str, optional
            Name of the aerodynamic surface. Default is 'Generic Surface'.
        unsteady_aero : bool, optional
            If True, the coefficients additionally depend on the time
            derivatives of the flow angles, and ``alpha_dot`` and ``beta_dot``
            are appended (in that order) to the independent variables. CSV files
            may then include "alpha_dot"/"beta_dot" columns, and callables must
            accept the two extra trailing arguments. Default is False.
        interpolation : str or dict, optional
            How tabulated coefficients interpolate between points. The accepted
            methods depend on the coefficient's dimensionality: a 1-D table
            (e.g. a Mach-only curve) accepts ``"linear"``, ``"akima"``,
            ``"spline"`` and ``"polynomial"``; a multi-dimensional scattered
            table accepts ``"linear"``, ``"shepard"`` and ``"rbf"``; and a
            multi-dimensional table on a regular Cartesian grid accepts
            ``"linear"``, ``"nearest"``, ``"slinear"``, ``"cubic"``,
            ``"quintic"`` and ``"pchip"`` (with ``"spline"`` mapped to
            ``"cubic"`` and ``"akima"`` to ``"pchip"``). Accepts either a simple
            string or a dict keyed by coefficient name (names left out fall back
            to the default). ``None`` (the default) uses ``"linear"`` for tables
            built here and keeps a pre-built ``Function``'s own setting.
        extrapolation : str or dict, optional
            How tabulated coefficients behave outside their data range:
            ``"constant"`` holds the value at the nearest data edge,
            ``"natural"`` keeps following the curve, and ``"zero"`` returns 0.
            Accepts either a simple string or a dict keyed by coefficient name
            (names left out fall back to the default). ``None`` (the default)
            uses ``"constant"`` for tables built here and keeps whatever a
            pre-built ``Function`` already carries. Only affects tabulated
            sources (constants and callables are evaluated directly).
        force_convention : str, optional
            The frame your force coefficients are given in. ``"wind"`` for the
            aerodynamic-frame coefficients ``cL`` (lift), ``cQ`` (side) and
            ``cD`` (drag); ``"body"`` for the body-frame coefficients ``cN``
            (normal), ``cY`` (side) and ``cA`` (axial), the convention used by
            Missile DATCOM, wind tunnels and Barrowman. The moment coefficients
            (``cm``, ``cn``, ``cl``) are the same in both. ``None`` (the default)
            infers the frame from the coefficient names you pass. Whichever frame
            you use, all nine coefficients are available as attributes afterwards
            (the other frame is computed on demand).
        """

        self._unsteady_aero = unsteady_aero
        # Externally-supplied axes (e.g. control deflections). Subclasses set
        # this before ``super().__init__``. Defaults to none for plain surfaces.
        self.control_variables = getattr(self, "control_variables", ())
        # Ordered independent variables accepted by every coefficient: the seven
        # base axes, plus ``alpha_dot``/``beta_dot`` when ``unsteady_aero`` is
        # enabled, plus any ``control_variables``
        self.independent_vars = build_independent_vars(
            self._unsteady_aero, self.control_variables
        )

        self.reference_area = reference_area
        self.reference_length = reference_length
        self.center_of_pressure = center_of_pressure
        self.cp = center_of_pressure
        self.cpx = center_of_pressure[0]
        self.cpy = center_of_pressure[1]
        self.cpz = center_of_pressure[2]
        self.name = name

        self._rotation_surface_to_body = self._default_surface_rotation()

        default_coefficients = self._get_default_coefficients()
        self.force_convention = self._resolve_force_convention(
            coefficients, force_convention
        )
        # The wind->body conversion only applies to surfaces whose coefficients
        # are the full body-frame forces (cN/cY/cA). The linear model uses
        # coefficient derivatives (cN_alpha, ...) whose frame is fixed by name.
        # A non-dict input falls through to _check_coefficients, which rejects it.
        if (
            self.force_convention == "wind"
            and "cN" in default_coefficients
            and isinstance(coefficients, dict)
        ):
            coefficients = self._wind_input_to_body(coefficients)
        self._check_coefficients(coefficients, default_coefficients)
        coefficients = self._complete_coefficients(coefficients, default_coefficients)
        for coeff, coeff_value in coefficients.items():
            value = AeroCoefficient(
                coeff_value,
                unsteady_aero=self._unsteady_aero,
                control_variables=self.control_variables,
                name=coeff,
                extrapolation=self._coefficient_option(extrapolation, coeff),
                interpolation=self._coefficient_option(interpolation, coeff),
            )
            setattr(self, coeff, value)

        self.evaluate_coefficients()
        self._evaluate_stability_derivatives()

        # Reporting layers. Subclasses override these with their own (more
        # specific) prints/plots after calling ``super().__init__``.
        self.prints = _GenericSurfacePrints(self)
        self.plots = _GenericSurfacePlots(self)

    def _default_surface_rotation(self):
        """Rotation from the surface-local frame to the body frame. It is applied
        to the :attr:`force_application_point` when the rocket locates each
        surface's center of pressure relative to the center of dry mass. A plain
        generic surface takes its center of pressure as already body-aligned
        (the identity); geometry-defined (Barrowman) surfaces override this.
        """
        return Matrix([[1, 0, 0], [0, 1, 0], [0, 0, 1]])

    @property
    def force_application_point(self):
        """Local point (surface frame) at which the resultant force is applied
        when transporting its moment to the rocket's center of dry mass. This is
        the center of pressure ``self.cp``; any residual couple is carried by the
        ``cm``/``cn``/``cl`` coefficients.
        """
        return Vector([self.cpx, self.cpy, self.cpz])

    @property
    def cL(self):  # pylint: disable=invalid-name
        """Wind-frame lift coefficient, as a :class:`Function` of the surface's
        independent variables. Derived from the canonical body-frame ``cN``,
        ``cY`` and ``cA`` by the angle-of-attack/sideslip rotation."""
        return body_to_wind_coefficients(
            self.cN, self.cY, self.cA, self.independent_vars
        )[0]

    @property
    def cD(self):  # pylint: disable=invalid-name
        """Wind-frame drag coefficient (derived from ``cN``/``cY``/``cA``)."""
        return body_to_wind_coefficients(
            self.cN, self.cY, self.cA, self.independent_vars
        )[1]

    @property
    def cQ(self):  # pylint: disable=invalid-name
        """Wind-frame side-force coefficient (derived from ``cN``/``cY``/``cA``)."""
        return body_to_wind_coefficients(
            self.cN, self.cY, self.cA, self.independent_vars
        )[2]

    def info(self):
        """Prints a summary of the surface's geometry and aerodynamic
        coefficients. Subclasses override this with surface-specific summaries.

        Returns
        -------
        None
        """
        self.prints.geometry()
        self.prints.coefficients()

    def all_info(self):
        """Prints and plots all available information of the surface.

        Returns
        -------
        None
        """
        self.prints.all()
        self.plots.all()

    def evaluate_coefficients(self):
        """Hook for subclasses to (re)populate the aerodynamic coefficient
        ``Function``s from their geometry. The base class builds coefficients
        directly from the user-provided dictionary, so this is a no-op here.
        Subclasses that derive coefficients from geometry (e.g. the Barrowman
        surfaces) override this and call it again whenever their geometry
        changes.

        Returns
        -------
        None
        """

    def _evaluate_stability_derivatives(self):
        """Compute the coefficient derivatives used for stability and store them
        as the ``cN_alpha``, ``cm_alpha``, ``cY_beta`` and ``cn_beta``
        attributes, then build the center-of-pressure accessors from them.

        A plain generic surface recovers each derivative from its body-frame
        force and moment coefficients by numerical differentiation at
        ``alpha = beta = 0`` with zero rates. The Barrowman surfaces instead set
        these four attributes directly from geometry and only reuse
        :meth:`_set_stability_accessors` (see the :class:`LinearGenericSurface`
        override).

        Returns
        -------
        None
        """
        self.cN_alpha = self._derivative_coefficient(self.cN, "alpha", "cN_alpha")
        self.cm_alpha = self._derivative_coefficient(self.cm, "alpha", "cm_alpha")
        self.cY_beta = self._derivative_coefficient(self.cY, "beta", "cY_beta")
        self.cn_beta = self._derivative_coefficient(self.cn, "beta", "cn_beta")
        self._set_stability_accessors()

    def _derivative_coefficient(self, coefficient, axis, name):
        """Numerically differentiate ``coefficient`` along ``axis`` at the
        linearization point and wrap the Mach-only result as an
        :class:`AeroCoefficient`, so every surface exposes ``cN_alpha`` and its
        siblings in the same form (a coefficient callable over the full
        argument tuple that depends only on Mach).

        Parameters
        ----------
        coefficient : AeroCoefficient
            The force or moment coefficient to differentiate.
        axis : str
            Either ``"alpha"`` or ``"beta"``.
        name : str
            Name of the resulting derivative coefficient.

        Returns
        -------
        AeroCoefficient
            The Mach-only derivative ``d(coefficient)/d(axis)``.
        """
        slope = self._partial_slope(coefficient, axis=axis)
        return AeroCoefficient(
            slope,
            depends_on=("mach",),
            unsteady_aero=self._unsteady_aero,
            control_variables=self.control_variables,
            name=name,
        )

    def _set_stability_accessors(self):
        """Build the pitch- and yaw-plane center-of-pressure accessors from the
        stored coefficient derivatives (``cN_alpha``/``cm_alpha`` and
        ``cY_beta``/``cn_beta``), each evaluated at ``alpha = beta = 0`` with
        zero rates.

        Each accessor is a Mach-only :class:`Function` giving the surface's
        center of pressure along the body z-axis. It combines the surface's
        local application point with the offset implied by its moment
        coefficient (``cp = application point - (moment slope / force slope) *
        L_ref``). When a surface produces no force at some Mach the center of
        pressure is undefined, so it falls back to the geometric application
        point and drops out of the force-weighted average.

        Returns
        -------
        None
        """
        reference_length = self.reference_length
        local_cpz = self.force_application_point[2]

        def _cp_z(force_coeff, moment_coeff):
            def cp_z(mach):
                slope = force_coeff.get_value_opt(0.0, 0.0, mach, 0.0, 0.0, 0.0, 0.0)
                if slope == 0:
                    return local_cpz
                moment = moment_coeff.get_value_opt(0.0, 0.0, mach, 0.0, 0.0, 0.0, 0.0)
                return local_cpz - moment / slope * reference_length

            return Function(cp_z, "Mach", "Center of pressure to local origin (m)")

        self.center_of_pressure_z = _cp_z(self.cN_alpha, self.cm_alpha)
        self.center_of_pressure_z_yaw = _cp_z(self.cY_beta, self.cn_beta)

    def _partial_slope(self, coefficient, axis):
        """Partial derivative ``d(coefficient)/d(axis)`` at ``alpha = beta = 0``
        and zero rates, returned as a mach-only ``Function``.

        Reuses :meth:`Function.differentiate` on a single-variable slice of the
        coefficient taken along ``axis`` (``"alpha"`` or ``"beta"``) with all
        other base inputs frozen at zero. Extra axes (control deflections) are
        frozen at their current value via :meth:`_coefficient_arguments`.

        Parameters
        ----------
        coefficient : Function
            A coefficient ``Function`` over ``self.independent_vars``.
        axis : str
            Either ``"alpha"`` or ``"beta"``.

        Returns
        -------
        Function
            ``d(coefficient)/d(axis)`` evaluated at the zero point, vs. mach.
        """

        def slope(mach):
            if axis == "alpha":
                sliced = Function(
                    lambda alpha: coefficient(
                        *self._coefficient_arguments(
                            alpha, 0.0, mach, 0.0, 0.0, 0.0, 0.0
                        )
                    )
                )
            else:
                sliced = Function(
                    lambda beta: coefficient(
                        *self._coefficient_arguments(
                            0.0, beta, mach, 0.0, 0.0, 0.0, 0.0
                        )
                    )
                )
            return sliced.differentiate(0)

        return Function(slope, "Mach", "Coefficient derivative")

    @staticmethod
    def _coefficient_option(option, coeff_name):
        """Resolve a per-coefficient interpolation/extrapolation setting.

        ``option`` may be a single value applied to every coefficient, a dict
        mapping coefficient names to values (coefficients absent from the dict
        fall back to the ``AeroCoefficient`` default), or ``None``.

        Parameters
        ----------
        option : str, dict, or None
            The interpolation/extrapolation argument passed to ``__init__``.
        coeff_name : str
            Name of the coefficient being built (e.g. ``"cD"``, ``"cm_alpha"``).

        Returns
        -------
        str or None
            The value to forward to :class:`AeroCoefficient` for this coefficient.
        """
        if isinstance(option, dict):
            return option.get(coeff_name)
        return option

    # Force-coefficient names in each frame. Moments (cm/cn/cl) are frame-shared.
    _WIND_FORCE_NAMES = ("cL", "cQ", "cD")
    _BODY_FORCE_NAMES = ("cN", "cY", "cA")

    def _resolve_force_convention(self, coefficients, force_convention):
        """Decide whether the input force coefficients are given in the wind
        frame (``cL``/``cQ``/``cD``) or the body frame (``cN``/``cY``/``cA``).

        When ``force_convention`` is ``None`` the frame is inferred from the
        coefficient names; mixing the two frames is rejected.
        """
        keys = set(coefficients)
        has_wind = bool(keys & set(self._WIND_FORCE_NAMES))
        has_body = bool(keys & set(self._BODY_FORCE_NAMES))
        if force_convention is None:
            if has_wind and has_body:
                raise ValueError(
                    "Mixed wind (cL/cQ/cD) and body (cN/cY/cA) force "
                    "coefficients; pass force_convention='wind' or 'body'."
                )
            return "body" if has_body else "wind"
        if force_convention not in ("wind", "body"):
            raise ValueError(
                f"force_convention must be 'wind' or 'body', got {force_convention!r}."
            )
        return force_convention

    def _wind_input_to_body(self, coefficients):
        """Convert a wind-frame force-coefficient input (``cL``/``cQ``/``cD``)
        into the canonical body-frame coefficients (``cN``/``cY``/``cA``),
        leaving the moment coefficients untouched."""
        wind = {}
        passthrough = {}
        for name, value in coefficients.items():
            if name in self._WIND_FORCE_NAMES:
                wind[name] = value
            else:
                passthrough[name] = value

        def as_coefficient(source, name):
            return AeroCoefficient(
                source,
                unsteady_aero=self._unsteady_aero,
                control_variables=self.control_variables,
                name=name,
            )

        c_normal, c_yaw, c_axial = wind_to_body_coefficients(
            as_coefficient(wind.get("cL", 0), "cL"),
            as_coefficient(wind.get("cD", 0), "cD"),
            as_coefficient(wind.get("cQ", 0), "cQ"),
            self.independent_vars,
        )
        return {"cN": c_normal, "cY": c_yaw, "cA": c_axial, **passthrough}

    def _get_default_coefficients(self):
        """Returns default coefficients

        Returns
        -------
        default_coefficients: dict
            Dictionary whose keys are the coefficients names and keys
            are the default values.
        """
        default_coefficients = {
            "cN": 0,
            "cY": 0,
            "cA": 0,
            "cm": 0,
            "cn": 0,
            "cl": 0,
        }
        return default_coefficients

    def _complete_coefficients(self, input_coefficients, default_coefficients):
        """Creates a copy of the input coefficients dict and fill it with missing
        keys with default values

        Parameters
        ----------
        input_coefficients : str, dict
            Coefficients dictionary passed by the user. If the user only specifies some
            of the coefficients, the remaining are completed with class default
            values
        default_coefficients : dict
            Default coefficients of the class

        Returns
        -------
        coefficients : dict
            Coefficients dictionary used to setup coefficient attributes
        """
        coefficients = copy.deepcopy(input_coefficients)
        for coeff, value in default_coefficients.items():
            if coeff not in coefficients.keys():
                coefficients[coeff] = value

        return coefficients

    def _check_coefficients(self, input_coefficients, default_coefficients):
        """Check if input coefficients have only valid keys

        Parameters
        ----------
        input_coefficients : str, dict
            Coefficients dictionary passed by the user. If the user only specifies some
            of the coefficients, the remaining are completed with class default
            values
        default_coefficients : dict
            Default coefficients of the class

        Raises
        ------
        ValueError
            Raises a value error if the input coefficient has an invalid key
        """
        invalid_keys = set(input_coefficients) - set(default_coefficients)
        if invalid_keys:
            raise ValueError(
                f"Invalid coefficient name(s) used in key(s): {', '.join(invalid_keys)}. "
                "Check the documentation for valid names."
            )

    def _compute_from_coefficients(
        self,
        rho,
        stream_speed,
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
        """Compute the aerodynamic forces and moments from the aerodynamic
        coefficients.

        Parameters
        ----------
        rho : float
            Air density.
        stream_speed : float
            Magnitude of the airflow speed.
        alpha : float
            Angle of attack in radians.
        beta : float
            Sideslip angle in radians.
        mach : float
            Mach number.
        reynolds : float
            Reynolds number.
        pitch_rate : float
            Non-dimensional (reduced) pitch rate, ``q * L_ref / (2 * V)``.
        yaw_rate : float
            Non-dimensional (reduced) yaw rate, ``r * L_ref / (2 * V)``.
        roll_rate : float
            Non-dimensional (reduced) roll rate, ``p * L_ref / (2 * V)``.
        alpha_dot : float, optional
            Non-dimensional angle-of-attack rate, used by unsteady surfaces.
            Defaults to 0.
        beta_dot : float, optional
            Non-dimensional sideslip-angle rate, used by unsteady surfaces.
            Defaults to 0.

        Returns
        -------
        tuple of float
            The body-frame force components ``(R1, R2, R3)`` and the moments
            ``(pitch, yaw, roll)``.
        """
        # Precompute common values
        dyn_pressure_area = 0.5 * rho * stream_speed**2 * self.reference_area
        dyn_pressure_area_length = dyn_pressure_area * self.reference_length

        # Coefficient arguments (base 7 vars, plus any extra axes appended by
        # subclasses such as control deflections or the unsteady alpha_dot/
        # beta_dot terms).
        args = self._coefficient_arguments(
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

        # Body-frame force components straight from the body-frame coefficients
        # (normal cN, side cY, axial cA); no wind-to-body rotation needed.
        normal = dyn_pressure_area * self.cN(*args)
        yaw_side = dyn_pressure_area * self.cY(*args)
        axial = dyn_pressure_area * self.cA(*args)
        r1 = yaw_side
        r2 = -normal
        r3 = -axial

        # Compute aerodynamic moments
        pitch = dyn_pressure_area_length * self.cm(*args)
        yaw = dyn_pressure_area_length * self.cn(*args)
        roll = dyn_pressure_area_length * self.cl(*args)

        return r1, r2, r3, pitch, yaw, roll

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
        """Returns the argument tuple passed to every coefficient ``Function``,
        in ``self.independent_vars`` order. The base class provides the seven
        standard inputs, plus ``alpha_dot``/``beta_dot`` when ``unsteady_aero``
        is enabled. Subclasses (e.g. :class:`ControllableGenericSurface`)
        override this to append further axes such as control deflections.
        """
        base = (alpha, beta, mach, reynolds, pitch_rate, yaw_rate, roll_rate)
        if self._unsteady_aero:
            return base + (alpha_dot, beta_dot)
        return base

    def compute_forces_and_moments(
        self,
        stream_velocity,
        stream_speed,
        stream_mach,
        rho,
        cp,
        omega,
        density,
        dynamic_viscosity,
        z,
        alpha_dot=0.0,
        beta_dot=0.0,
    ):
        """Computes the forces and moments acting on the aerodynamic surface.
        Used in each time step of the simulation.  This method is valid for
        both linear and nonlinear aerodynamic coefficients.

        Parameters
        ----------
        stream_velocity : tuple of float
            The velocity of the airflow relative to the surface.
        stream_speed : float
            The magnitude of the airflow speed.
        stream_mach : float
            The Mach number of the airflow.
        rho : float
            Air density.
        cp : Vector
            Center of pressure coordinates in the body frame.
        omega: tuple[float, float, float]
            Tuple containing angular velocities around the x, y, z axes.
        density : Function
            Atmospheric density as a function of altitude. Used to compute the
            Reynolds number at the surface altitude.
        dynamic_viscosity : Function
            Atmospheric dynamic viscosity as a function of altitude. Used to
            compute the Reynolds number at the surface altitude.
        z : float
            Altitude of the surface, used to evaluate ``density`` and
            ``dynamic_viscosity``.
        alpha_dot : float, optional
            Non-dimensional angle-of-attack rate, used by unsteady surfaces.
            Defaults to 0.
        beta_dot : float, optional
            Non-dimensional sideslip-angle rate, used by unsteady surfaces.
            Defaults to 0.

        Returns
        -------
        tuple of float
            The aerodynamic forces (lift, side_force, drag) and moments
            (pitch, yaw, roll) in the body frame.
        """
        # Reynolds number at the surface altitude. Computed here (rather than in
        # the flight loop) since it is only needed by generic surfaces.
        comp_density = density.get_value_opt(z)
        comp_dynamic_viscosity = dynamic_viscosity.get_value_opt(z)
        reynolds = (
            comp_density * stream_speed * self.reference_length / comp_dynamic_viscosity
            if comp_dynamic_viscosity > 0
            else 0
        )

        # Stream velocity in standard aerodynamic frame
        stream_velocity = -stream_velocity

        # Angles of attack and sideslip
        alpha = np.arctan2(stream_velocity[1], stream_velocity[2])
        beta = np.arctan2(stream_velocity[0], stream_velocity[2])

        # Non-dimensionalize the body angular rates into the conventional reduced
        # rates (e.g. ``q* = q * L_ref / (2 * V)``).
        reduced_rate_factor = (
            self.reference_length / (2 * stream_speed) if stream_speed > 0 else 0.0
        )

        # Body-frame force components and moments straight from the body-frame
        # coefficients (no wind-to-body rotation: the coefficients already live
        # in the body frame). ``alpha``/``beta`` are still passed to the
        # coefficients, they just no longer rotate the force.
        R1, R2, R3, pitch, yaw, roll = self._compute_from_coefficients(
            rho,
            stream_speed,
            alpha,
            beta,
            stream_mach,
            reynolds,
            omega[0] * reduced_rate_factor,  # q*  reduced pitch rate
            omega[1] * reduced_rate_factor,  # r*  reduced yaw rate
            omega[2] * reduced_rate_factor,  # p*  reduced roll rate
            alpha_dot,
            beta_dot,
        )

        # Dislocation of the aerodynamic application point to CDM
        M1, M2, M3 = Vector([pitch, yaw, roll]) + (cp ^ Vector([R1, R2, R3]))

        return R1, R2, R3, M1, M2, M3
