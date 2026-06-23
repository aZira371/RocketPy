"""Minimal-dimension aerodynamic coefficient storage.

A :class:`AeroCoefficient` stores a single aerodynamic coefficient at its
*intrinsic* dimensionality - a constant, or a :class:`Function` over only the
variables the coefficient actually depends on (its ``depends_on``) - and maps
the full coefficient argument tuple (in ``independent_vars`` order) down to that
subset on every call.

This avoids forcing a Mach-only (or constant) coefficient into a full seven
dimensional :class:`Function`: interpolation happens at the right dimension (so
a Mach-only table is not smeared across a 7-D domain) and evaluation passes only
the arguments that matter. It generalizes the per-call ``dict(zip(...))`` subset
selection that the CSV loader used to do inline.
"""

import inspect

from rocketpy.mathutils import Function


class AeroCoefficient:
    """A single aerodynamic coefficient stored at minimal dimensionality.

    Parameters
    ----------
    source : int, float, callable, or Function
        The coefficient value. A number is stored as a constant; a callable or
        :class:`Function` is stored over ``depends_on``.
    depends_on : sequence of str
        The independent variables the coefficient depends on, a (possibly
        empty) subset of ``independent_vars``. The order is normalized to the
        order of ``independent_vars``.
    independent_vars : sequence of str
        The full, ordered list of independent variables of the owning surface
        (e.g. ``alpha, beta, mach, reynolds, pitch_rate, yaw_rate, roll_rate``
        plus any control or unsteady axes). Defines the argument order accepted
        by :meth:`__call__`.
    name : str, optional
        Name of the coefficient, used for the underlying ``Function`` output.
    """

    def __init__(self, source, depends_on, independent_vars, name="coefficient"):
        self.name = name
        self.independent_vars = tuple(independent_vars)
        # ``depends_on`` is kept in the given order because it matches the
        # positional argument order of the stored source (callable parameters,
        # CSV columns, …). ``_indices`` therefore maps the full argument tuple
        # to the source's own argument order.
        self.depends_on = tuple(depends_on)
        unknown = [var for var in self.depends_on if var not in self.independent_vars]
        if unknown:
            raise ValueError(
                f"{name} depends on unknown variable(s) {unknown}; "
                f"valid variables are {list(self.independent_vars)}."
            )
        self._indices = tuple(
            self.independent_vars.index(var) for var in self.depends_on
        )

        self.is_zero = False
        self._constant = None
        if isinstance(source, Function):
            self.function = source
        elif callable(source):
            self.function = Function(
                source,
                list(self.depends_on) or ["x"],
                [name],
                interpolation="linear",
                extrapolation="natural",
            )
        else:
            # Scalar constant.
            self._constant = float(source)
            self.is_zero = self._constant == 0.0
            self.function = Function(self._constant)

        self._evaluate = self.function.get_value_opt

    @classmethod
    def from_input(cls, input_data, name, independent_vars, csv_loader=None):
        """Build an :class:`AeroCoefficient` from a user coefficient input.

        Mirrors the accepted coefficient inputs of
        :class:`GenericSurface`: a number, a callable, a :class:`Function`, or a
        path to a CSV file, inferring ``depends_on`` from each.

        Parameters
        ----------
        input_data : int, float, str, callable, or Function
            The coefficient value (number, CSV path, callable, or Function).
        name : str
            Coefficient name, used for error messages and the Function output.
        independent_vars : sequence of str
            The owning surface's ordered independent variables.
        csv_loader : callable, optional
            Callable ``(file_path, name) -> (function, depends_on)`` used to
            load a CSV coefficient at minimal dimension. Required when
            ``input_data`` is a string path.

        Returns
        -------
        AeroCoefficient
        """
        independent_vars = list(independent_vars)
        n_vars = len(independent_vars)
        vars_repr = ", ".join(independent_vars)

        if isinstance(input_data, AeroCoefficient):
            # Already an AeroCoefficient (e.g. a to_dict/from_dict round trip):
            # re-key it to the requested independent-variable order.
            return cls(
                input_data._constant
                if input_data._constant is not None
                else input_data.function,
                input_data.depends_on,
                independent_vars,
                name,
            )

        if isinstance(input_data, str):
            if csv_loader is None:  # pragma: no cover - defensive
                raise ValueError("A csv_loader is required for CSV coefficients.")
            function, depends_on = csv_loader(input_data, name)
            return cls(function, depends_on, independent_vars, name)

        if isinstance(input_data, Function):
            dom_dim = input_data.__dom_dim__
            if dom_dim == n_vars:
                depends_on = independent_vars
            elif dom_dim == 1:
                # A 1-D Function is taken to depend on the first independent
                # variable (alpha) unless its input name matches one of them.
                depends_on = [cls._infer_single_var(input_data, independent_vars)]
            else:
                raise ValueError(
                    f"{name} Function must have {n_vars} input arguments "
                    f"({vars_repr}) or be one-dimensional."
                )
            return cls(input_data, depends_on, independent_vars, name)

        if callable(input_data):
            depends_on = cls._infer_callable_depends_on(
                input_data, independent_vars, name
            )
            return cls(input_data, depends_on, independent_vars, name)

        # Anything else must be a scalar number.
        try:
            float(input_data)
        except (TypeError, ValueError) as exc:
            raise TypeError(
                f"Invalid input for {name}: must be a number, a CSV file path, "
                "a callable, or a Function."
            ) from exc
        return cls(input_data, (), independent_vars, name)

    @staticmethod
    def _infer_single_var(function, independent_vars):
        """Best-effort name of the variable a 1-D Function depends on."""
        try:
            label = function.__inputs__[0]
        except (AttributeError, IndexError, TypeError):
            return independent_vars[0]
        label_lower = str(label).lower()
        for var in independent_vars:
            if var in label_lower:
                return var
        return independent_vars[0]

    @staticmethod
    def _infer_callable_depends_on(func, independent_vars, name):
        """Infer ``depends_on`` for a plain callable.

        Two conventions are accepted, checked in order:

        1. *Named subset* - every parameter name is an independent variable, so
           the parameters themselves name the dependency subset (e.g.
           ``lambda alpha, mach: ...``).
        2. *Positional full-arity* - the parameter count equals the number of
           independent variables, so the callable depends on all of them
           regardless of how its parameters are named (e.g.
           ``lambda a, b, m, r, p, q, rr: ...``).
        """
        n_vars = len(independent_vars)
        try:
            params = list(inspect.signature(func).parameters.values())
        except (TypeError, ValueError):  # pragma: no cover - builtins
            params = []
        names = [p.name for p in params]

        if names and set(names) <= set(independent_vars):
            return names
        if len(names) == n_vars:
            return list(independent_vars)
        raise ValueError(
            f"{name} callable must accept {n_vars} positional arguments "
            f"({', '.join(independent_vars)}) or name its parameters after the "
            "independent variables it depends on."
        )

    @property
    def is_zero_coefficient(self):
        """Back-compat alias used by the linear model's hot-loop term skipping."""
        return self.is_zero

    @property
    def __dom_dim__(self):
        """Number of full independent variables (the call arity)."""
        return len(self.independent_vars)

    def get_value_opt(self, *args):
        """Fast, unvalidated evaluation (mirrors :meth:`Function.get_value_opt`).

        Maps the full ``independent_vars`` argument tuple down to the source's
        own ``depends_on`` arguments before evaluating; a constant short-circuits.
        """
        if self._constant is not None:
            return self._constant
        return self._evaluate(*(args[i] for i in self._indices))

    # Calling the coefficient is the same as the fast evaluator; the linear
    # model grabs ``get_value_opt`` directly for the hot loop.
    __call__ = get_value_opt

    def __repr__(self):
        if self._constant is not None:
            return f"AeroCoefficient({self.name}={self._constant})"
        return f"AeroCoefficient({self.name}, depends_on={self.depends_on})"
