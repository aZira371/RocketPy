"""FlightConfig – typed per-branch Flight construction parameters."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class FlightConfig:
    """Typed configuration for constructing a single mission branch's Flight.

    A :class:`FlightConfig` mirrors the subset of
    :class:`~rocketpy.simulation.Flight` constructor arguments that mission
    items are expected to override on a per-branch basis. It replaces ad hoc
    keyword-argument dicts as the value passed around by
    :class:`~rocketpy.mission.MissionExecutor`.

    Parameters
    ----------
    rail_length : float
        Length in meters of the launch rail for this branch.
    inclination : float, optional
        Rail inclination relative to the ground, in degrees. Defaults to
        ``80.0``.
    heading : float, optional
        Launch heading relative to north, in degrees. Defaults to ``90.0``.
    initial_solution : object, optional
        Initial solution passed to ``Flight``. May be a state vector or a
        previously built ``Flight`` (chained by
        :class:`~rocketpy.mission.MissionExecutor`). Defaults to ``None``.
    max_time : float, optional
        Maximum simulation time, in seconds. Defaults to ``600``.
    terminate_on_apogee : bool, optional
        Whether to stop the simulation at apogee. Defaults to ``False``.
    time_overshoot : bool, optional
        Whether ``Flight`` is allowed to overshoot requested time steps.
        Defaults to ``True``.
    extra_kwargs : dict, optional
        Any additional keyword arguments forwarded to ``Flight`` verbatim.

    Attributes
    ----------
    rail_length : float
    inclination : float
    heading : float
    initial_solution : object or None
    max_time : float
    terminate_on_apogee : bool
    time_overshoot : bool
    extra_kwargs : dict
    """

    rail_length: float
    inclination: float = 80.0
    heading: float = 90.0
    initial_solution: Any = None
    max_time: float = 600
    terminate_on_apogee: bool = False
    time_overshoot: bool = True
    extra_kwargs: dict = field(default_factory=dict)

    _KNOWN_FIELDS = (
        "rail_length",
        "inclination",
        "heading",
        "initial_solution",
        "max_time",
        "terminate_on_apogee",
        "time_overshoot",
    )

    def to_flight_kwargs(self) -> dict:
        """Return keyword arguments to pass to ``Flight`` (excluding ``rail_length``,
        which :class:`~rocketpy.mission.MissionExecutor` passes separately
        alongside ``rocket``/``environment``).

        Returns
        -------
        dict
            Merged mapping of ``inclination``, ``heading``,
            ``initial_solution``, ``max_time``, ``terminate_on_apogee``,
            ``time_overshoot``, and any entries from :attr:`extra_kwargs`.
        """
        kwargs = {
            "inclination": self.inclination,
            "heading": self.heading,
            "initial_solution": self.initial_solution,
            "max_time": self.max_time,
            "terminate_on_apogee": self.terminate_on_apogee,
            "time_overshoot": self.time_overshoot,
        }
        kwargs.update(self.extra_kwargs)
        return kwargs

    def for_branch(self, name: str, overrides: dict = None) -> "FlightConfig":
        """Return a new :class:`FlightConfig` with *overrides* applied on top.

        Parameters
        ----------
        name : str
            Name of the branch these overrides apply to. Used only for
            error messages; it is not stored on the returned config.
        overrides : dict, optional
            Values to override. Keys matching a known :class:`FlightConfig`
            field are applied directly; any other keys are merged into the
            returned config's :attr:`extra_kwargs`.

        Returns
        -------
        FlightConfig
            A new, independent :class:`FlightConfig` instance.
        """
        overrides = dict(overrides or {})
        known = {k: v for k, v in overrides.items() if k in self._KNOWN_FIELDS}
        extra = {k: v for k, v in overrides.items() if k not in self._KNOWN_FIELDS}

        merged_extra = dict(self.extra_kwargs)
        merged_extra.update(extra)

        return FlightConfig(
            rail_length=known.get("rail_length", self.rail_length),
            inclination=known.get("inclination", self.inclination),
            heading=known.get("heading", self.heading),
            initial_solution=known.get("initial_solution", self.initial_solution),
            max_time=known.get("max_time", self.max_time),
            terminate_on_apogee=known.get(
                "terminate_on_apogee", self.terminate_on_apogee
            ),
            time_overshoot=known.get("time_overshoot", self.time_overshoot),
            extra_kwargs=merged_extra,
        )
