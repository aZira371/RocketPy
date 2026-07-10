from rocketpy.mathutils import Function
from rocketpy.plots.aero_surface_plots import _LinearGenericSurfacePlots
from rocketpy.prints.aero_surface_prints import _LinearGenericSurfacePrints
from rocketpy.rocket.aero_surface.generic_surface import GenericSurface


# TODO: review note: ControllableGenericSurface should also be able to be modelled
# based on LinearGenericSurface....
class LinearGenericSurface(GenericSurface):
    """An aerodynamic surface whose forces and moments vary linearly with the
    flow angles and the rotation rates. Instead of full coefficient tables, you
    give the coefficient *derivatives* (slopes) -- for example how much the normal
    force changes per radian of angle of attack -- and the surface adds them up
    linearly."""

    def __init__(
        self,
        reference_area,
        reference_length,
        coefficients,
        center_of_pressure=(0, 0, 0),
        name="Generic Linear Surface",
        interpolation=None,
        extrapolation=None,
    ):
        """Create a generic linear aerodynamic surface, defined by its
        aerodynamic coefficients derivatives. This surface is used to model any
        aerodynamic surface that does not fit the predefined classes.

        Important
        ---------
        All the aerodynamic coefficients can be input as callable functions of
        angle of attack, angle of sideslip, Mach number, Reynolds number,
        pitch rate, yaw rate and roll rate. For CSV files, the header must
        contain at least one of the following: "alpha", "beta", "mach",
        "reynolds", "pitch_rate", "yaw_rate" and "roll_rate".

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
        coefficients: dict, optional
            The coefficient derivatives (slopes), by name. Any you leave out are
            set to 0. Each one can be a constant, a function, or a path to a data
            file, and says how one force or moment coefficient changes with one
            variable (angle in radians, or a non-dimensional rotation rate). The
            names follow the pattern ``<coefficient>_<variable>``: the coefficient
            is normal force ``cN``, side force ``cY``, axial force ``cA``, pitch moment ``cm``,
            yaw moment ``cn`` or roll moment ``cl``; the variable is ``0`` (the
            value at zero angle of attack, zero sideslip and zero rates),
            ``alpha``, ``beta``, ``p`` (roll rate), ``q`` (pitch rate) or ``r``
            (yaw rate). The full list is:\n
            cN_0: callable, str, optional
                Coefficient of normal force at zero angle of attack. Default is 0.\n
            cN_alpha: callable, str, optional
                Coefficient of normal force derivative with respect to angle of attack.
                Default is 0.\n
            cN_beta: callable, str, optional
                Coefficient of normal force derivative with respect to sideslip angle.
                Default is 0.\n
            cN_p: callable, str, optional
                Coefficient of normal force derivative with respect to roll rate.
                Default is 0.\n
            cN_q: callable, str, optional
                Coefficient of normal force derivative with respect to pitch rate.
                Default is 0.\n
            cN_r: callable, str, optional
                Coefficient of normal force derivative with respect to yaw rate.
                Default is 0.\n
            cY_0: callable, str, optional
                Coefficient of side force at zero angle of attack.
                Default is 0.\n
            cY_alpha: callable, str, optional
                Coefficient of side force derivative with respect to angle of
                attack. Default is 0.\n
            cY_beta: callable, str, optional
                Coefficient of side force derivative with respect to sideslip
                angle. Default is 0.\n
            cY_p: callable, str, optional
                Coefficient of side force derivative with respect to roll rate.
                Default is 0.\n
            cY_q: callable, str, optional
                Coefficient of side force derivative with respect to pitch rate.
                Default is 0.\n
            cY_r: callable, str, optional
                Coefficient of side force derivative with respect to yaw rate.
                Default is 0.\n
            cA_0: callable, str, optional
                Coefficient of axial force at zero angle of attack. Default is 0.\n
            cA_alpha: callable, str, optional
                Coefficient of axial force derivative with respect to angle of attack.
                Default is 0.\n
            cA_beta: callable, str, optional
                Coefficient of axial force derivative with respect to sideslip angle.
                Default is 0.\n
            cA_p: callable, str, optional
                Coefficient of axial force derivative with respect to roll rate.
                Default is 0.\n
            cA_q: callable, str, optional
                Coefficient of axial force derivative with respect to pitch rate.
                Default is 0.\n
            cA_r: callable, str, optional
                Coefficient of axial force derivative with respect to yaw rate.
                Default is 0.\n
            cm_0: callable, str, optional
                Coefficient of pitch moment at zero angle of attack.
                Default is 0.\n
            cm_alpha: callable, str, optional
                Coefficient of pitch moment derivative with respect to angle of
                attack. Default is 0.\n
            cm_beta: callable, str, optional
                Coefficient of pitch moment derivative with respect to sideslip
                angle. Default is 0.\n
            cm_p: callable, str, optional
                Coefficient of pitch moment derivative with respect to roll rate.
                Default is 0.\n
            cm_q: callable, str, optional
                Coefficient of pitch moment derivative with respect to pitch rate.
                Default is 0.\n
            cm_r: callable, str, optional
                Coefficient of pitch moment derivative with respect to yaw rate.
                Default is 0.\n
            cn_0: callable, str, optional
                Coefficient of yaw moment at zero angle of attack.
                Default is 0.\n
            cn_alpha: callable, str, optional
                Coefficient of yaw moment derivative with respect to angle of
                attack. Default is 0.\n
            cn_beta: callable, str, optional
                Coefficient of yaw moment derivative with respect to sideslip angle.
                Default is 0.\n
            cn_p: callable, str, optional
                Coefficient of yaw moment derivative with respect to roll rate.
                Default is 0.\n
            cn_q: callable, str, optional
                Coefficient of yaw moment derivative with respect to pitch rate.
                Default is 0.\n
            cn_r: callable, str, optional
                Coefficient of yaw moment derivative with respect to yaw rate.
                Default is 0.\n
            cl_0: callable, str, optional
                Coefficient of roll moment at zero angle of attack.
                Default is 0.\n
            cl_alpha: callable, str, optional
                Coefficient of roll moment derivative with respect to angle of
                attack. Default is 0.\n
            cl_beta: callable, str, optional
                Coefficient of roll moment derivative with respect to sideslip
                angle. Default is 0.\n
            cl_p: callable, str, optional
                Coefficient of roll moment derivative with respect to roll rate.
                Default is 0.\n
            cl_q: callable, str, optional
                Coefficient of roll moment derivative with respect to pitch rate.
                Default is 0.\n
            cl_r: callable, str, optional
                Coefficient of roll moment derivative with respect to yaw rate.
                Default is 0.\n
        center_of_pressure : tuple, optional
            Application point of the aerodynamic forces and moments. The
            center of pressure is defined in the local coordinate system of the
            aerodynamic surface. The default value is (0, 0, 0).
        name : str, optional
            Name of the aerodynamic surface. Default is 'Generic Linear
            Surface'.
        interpolation : str or dict, optional
            How tabulated coefficient derivatives interpolate between points.
            The accepted methods depend on the coefficient's dimensionality: a
            1-D table (e.g. a Mach-only curve) accepts ``"linear"``, ``"akima"``,
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
            How tabulated coefficient derivatives behave outside their data
            range: ``"constant"`` holds the value at the nearest data edge,
            ``"natural"`` keeps following the curve, and ``"zero"`` returns 0.
            Accepts either a simple string or a dict keyed by coefficient name
            (names left out fall back to the default). ``None`` (the default)
            uses ``"constant"`` for tables built here and keeps whatever a
            pre-built ``Function`` already carries. Only affects tabulated
            sources (constants and callables are evaluated directly).
        """

        super().__init__(
            reference_area=reference_area,
            reference_length=reference_length,
            coefficients=coefficients,
            center_of_pressure=center_of_pressure,
            name=name,
            extrapolation=extrapolation,
            interpolation=interpolation,
        )

        self.compute_all_coefficients()

        self.prints = _LinearGenericSurfacePrints(self)
        self.plots = _LinearGenericSurfacePlots(self)

    def _evaluate_stability_derivatives(self):
        """Build the center-of-pressure accessors for the linear model.

        The linear model already stores the coefficient derivatives
        ``cN_alpha``/``cm_alpha`` (pitch) and ``cY_beta``/``cn_beta`` (yaw) as
        the surface's own coefficients, so there is nothing to differentiate:
        :meth:`_set_stability_accessors` reads them directly (evaluated at zero
        alpha/beta and zero rates). Damping derivatives (``_p/_q/_r``) are
        intentionally excluded from the stability center of pressure.
        """
        self._set_stability_accessors()

    def _get_default_coefficients(self):
        """Returns default coefficients

        Returns
        -------
        default_coefficients: dict
            Dictionary whose keys are the coefficients names and keys
            are the default values.
        """
        default_coefficients = {
            "cN_0": 0,
            "cN_alpha": 0,
            "cN_beta": 0,
            "cN_p": 0,
            "cN_q": 0,
            "cN_r": 0,
            "cY_0": 0,
            "cY_alpha": 0,
            "cY_beta": 0,
            "cY_p": 0,
            "cY_q": 0,
            "cY_r": 0,
            "cA_0": 0,
            "cA_alpha": 0,
            "cA_beta": 0,
            "cA_p": 0,
            "cA_q": 0,
            "cA_r": 0,
            "cm_0": 0,
            "cm_alpha": 0,
            "cm_beta": 0,
            "cm_p": 0,
            "cm_q": 0,
            "cm_r": 0,
            "cn_0": 0,
            "cn_alpha": 0,
            "cn_beta": 0,
            "cn_p": 0,
            "cn_q": 0,
            "cn_r": 0,
            "cl_0": 0,
            "cl_alpha": 0,
            "cl_beta": 0,
            "cl_p": 0,
            "cl_q": 0,
            "cl_r": 0,
        }
        return default_coefficients

    _COEFFICIENT_INPUTS = [
        "alpha",
        "beta",
        "mach",
        "reynolds",
        "pitch_rate",
        "yaw_rate",
        "roll_rate",
    ]

    def compute_forcing_coefficient(self, c_0, c_alpha, c_beta):
        """Compose the forcing coefficient ``c_0 + c_alpha*alpha + c_beta*beta``,
        evaluating only the non-zero terms.

        Two hot-loop optimizations: ``get_value_opt`` is the unvalidated fast
        evaluator (for callable-source coefficients it is the raw source), and
        terms that are identically zero are skipped entirely. For a Barrowman
        surface each forcing coefficient has at most one non-zero derivative, so
        this typically collapses to a single source call (or to a constant 0).

        Parameters
        ----------
        c_0 : AeroCoefficient
            Zero-angle derivative (constant term).
        c_alpha : AeroCoefficient
            Derivative with respect to the angle of attack ``alpha``.
        c_beta : AeroCoefficient
            Derivative with respect to the sideslip angle ``beta``.

        Returns
        -------
        Function
            Coefficient as a function of the independent variables
            ``(alpha, beta, mach, reynolds, pitch_rate, yaw_rate, roll_rate)``.
        """
        has_0 = not getattr(c_0, "is_zero_coefficient", False)
        has_alpha = not getattr(c_alpha, "is_zero_coefficient", False)
        has_beta = not getattr(c_beta, "is_zero_coefficient", False)
        c_0_opt = c_0.get_value_opt
        c_alpha_opt = c_alpha.get_value_opt
        c_beta_opt = c_beta.get_value_opt

        if not (has_0 or has_alpha or has_beta):

            def total_coefficient(  # pylint: disable=unused-argument
                alpha, beta, mach, reynolds, pitch_rate, yaw_rate, roll_rate
            ):
                return 0.0

        else:

            def total_coefficient(
                alpha, beta, mach, reynolds, pitch_rate, yaw_rate, roll_rate
            ):
                value = 0.0
                if has_0:
                    value += c_0_opt(
                        alpha, beta, mach, reynolds, pitch_rate, yaw_rate, roll_rate
                    )
                if has_alpha:
                    value += (
                        c_alpha_opt(
                            alpha, beta, mach, reynolds, pitch_rate, yaw_rate, roll_rate
                        )
                        * alpha
                    )
                if has_beta:
                    value += (
                        c_beta_opt(
                            alpha, beta, mach, reynolds, pitch_rate, yaw_rate, roll_rate
                        )
                        * beta
                    )
                return value

        return Function(total_coefficient, self._COEFFICIENT_INPUTS, ["coefficient"])

    def compute_damping_coefficient(self, c_p, c_q, c_r):
        """Compose the damping coefficient
        ``c_p*roll_rate + c_q*pitch_rate + c_r*yaw_rate``, evaluating only the
        non-zero terms (see :meth:`compute_forcing_coefficient`). For a Barrowman
        surface only ``cl_p`` (roll damping) is non-zero, so most damping
        coefficients collapse to a constant 0.

        Parameters
        ----------
        c_p : AeroCoefficient
            Derivative with respect to the roll rate ``roll_rate``.
        c_q : AeroCoefficient
            Derivative with respect to the pitch rate ``pitch_rate``.
        c_r : AeroCoefficient
            Derivative with respect to the yaw rate ``yaw_rate``.

        Returns
        -------
        Function
            Coefficient as a function of the independent variables
            ``(alpha, beta, mach, reynolds, pitch_rate, yaw_rate, roll_rate)``.
        """
        has_p = not getattr(c_p, "is_zero_coefficient", False)
        has_q = not getattr(c_q, "is_zero_coefficient", False)
        has_r = not getattr(c_r, "is_zero_coefficient", False)
        c_p_opt = c_p.get_value_opt
        c_q_opt = c_q.get_value_opt
        c_r_opt = c_r.get_value_opt

        if not (has_p or has_q or has_r):

            def total_coefficient(  # pylint: disable=unused-argument
                alpha, beta, mach, reynolds, pitch_rate, yaw_rate, roll_rate
            ):
                return 0.0

        else:

            def total_coefficient(
                alpha, beta, mach, reynolds, pitch_rate, yaw_rate, roll_rate
            ):
                value = 0.0
                if has_p:
                    value += (
                        c_p_opt(
                            alpha, beta, mach, reynolds, pitch_rate, yaw_rate, roll_rate
                        )
                        * roll_rate
                    )
                if has_q:
                    value += (
                        c_q_opt(
                            alpha, beta, mach, reynolds, pitch_rate, yaw_rate, roll_rate
                        )
                        * pitch_rate
                    )
                if has_r:
                    value += (
                        c_r_opt(
                            alpha, beta, mach, reynolds, pitch_rate, yaw_rate, roll_rate
                        )
                        * yaw_rate
                    )
                return value

        return Function(total_coefficient, self._COEFFICIENT_INPUTS, ["coefficient"])

    def compute_all_coefficients(self):
        """Compute all the aerodynamic coefficients from the derivatives."""
        # pylint: disable=invalid-name
        self.cNf = self.compute_forcing_coefficient(
            self.cN_0, self.cN_alpha, self.cN_beta
        )
        self.cNd = self.compute_damping_coefficient(self.cN_p, self.cN_q, self.cN_r)

        self.cYf = self.compute_forcing_coefficient(
            self.cY_0, self.cY_alpha, self.cY_beta
        )
        self.cYd = self.compute_damping_coefficient(self.cY_p, self.cY_q, self.cY_r)

        self.cAf = self.compute_forcing_coefficient(
            self.cA_0, self.cA_alpha, self.cA_beta
        )
        self.cAd = self.compute_damping_coefficient(self.cA_p, self.cA_q, self.cA_r)

        self.cmf = self.compute_forcing_coefficient(
            self.cm_0, self.cm_alpha, self.cm_beta
        )
        self.cmd = self.compute_damping_coefficient(self.cm_p, self.cm_q, self.cm_r)

        self.cnf = self.compute_forcing_coefficient(
            self.cn_0, self.cn_alpha, self.cn_beta
        )
        self.cnd = self.compute_damping_coefficient(self.cn_p, self.cn_q, self.cn_r)

        self.clf = self.compute_forcing_coefficient(
            self.cl_0, self.cl_alpha, self.cl_beta
        )
        self.cld = self.compute_damping_coefficient(self.cl_p, self.cl_q, self.cl_r)

        self.cN = self.cNf
        self.cY = self.cYf
        self.cA = self.cAf
        self.cm = self.cmf
        self.cn = self.cnf
        self.cl = self.clf

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
        alpha_dot=0.0,  # pylint: disable=unused-argument
        beta_dot=0.0,  # pylint: disable=unused-argument
    ):
        """Compute the aerodynamic forces and moments from the aerodynamic
        coefficients.

        The linear (Barrowman) model does not use the unsteady ``alpha_dot`` /
        ``beta_dot`` terms; they are accepted for signature compatibility.

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
            Non-dimensional angle-of-attack rate. Ignored by the linear model;
            accepted for signature compatibility. Defaults to 0.
        beta_dot : float, optional
            Non-dimensional sideslip-angle rate. Ignored by the linear model;
            accepted for signature compatibility. Defaults to 0.

        Returns
        -------
        tuple of float
            The body-frame force components ``(R1, R2, R3)`` and the moments
            ``(pitch, yaw, roll)``.
        """
        # Precompute common values
        dyn_pressure_area = 0.5 * rho * stream_speed**2 * self.reference_area
        dyn_pressure_area_length = dyn_pressure_area * self.reference_length
        args = (alpha, beta, mach, reynolds, pitch_rate, yaw_rate, roll_rate)

        # Body-frame forces (forcing + reduced-rate damping), straight from the
        # body-frame coefficients: normal cN, side cY, axial cA.
        normal = dyn_pressure_area * (
            self.cNf.get_value_opt(*args) + self.cNd.get_value_opt(*args)
        )
        yaw_side = dyn_pressure_area * (
            self.cYf.get_value_opt(*args) + self.cYd.get_value_opt(*args)
        )
        axial = dyn_pressure_area * (
            self.cAf.get_value_opt(*args) + self.cAd.get_value_opt(*args)
        )
        r1 = yaw_side
        r2 = -normal
        r3 = -axial

        # Compute aerodynamic moments (forcing + reduced-rate damping)
        pitch = dyn_pressure_area_length * (
            self.cmf.get_value_opt(*args) + self.cmd.get_value_opt(*args)
        )
        yaw = dyn_pressure_area_length * (
            self.cnf.get_value_opt(*args) + self.cnd.get_value_opt(*args)
        )
        roll = dyn_pressure_area_length * (
            self.clf.get_value_opt(*args) + self.cld.get_value_opt(*args)
        )

        return r1, r2, r3, pitch, yaw, roll
