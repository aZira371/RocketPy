"""Mission – top-level container for a multistage rocket mission."""

import warnings
from typing import Any


class Mission:  # pylint: disable=too-many-instance-attributes
    """Container that stores all mission items for a multistage flight.

    A :class:`Mission` groups together all the :class:`~rocketpy.mission.Stage`
    and :class:`~rocketpy.mission.Deployable` objects that together define a
    complete rocket mission.  It acts as the single source-of-truth for the
    simulation engine: when :class:`~rocketpy.simulation.Flight` is initialised
    with a :class:`Mission`, it reads the stages and deployables from here.

    Parameters
    ----------
    name : str, optional
        Human-readable name for the mission (e.g. ``"Falcon9_Demo"``).
        Defaults to ``"Mission"``.
    root_vehicle : Rocket or FlightBody, optional
        The assembled vehicle before any stage/deployable event occurs.
        Defaults to ``None``.

    Attributes
    ----------
    name : str
        Mission name.
    root_vehicle : Rocket, FlightBody, or None
        The assembled vehicle flown before any stage/deployable event.
        Not part of :meth:`attached_items` – it is the vehicle that
        attached items detach *from*.
    stages : list[:class:`~rocketpy.mission.Stage`]
        Ordered list of rocket stages (first-to-fire first).
    deployables : list[:class:`~rocketpy.mission.Deployable`]
        List of deployable items that will be released during the mission.

    Examples
    --------
    >>> from rocketpy.mission import Mission, Stage, Deployable
    >>> mission = Mission(name="Demo")
    >>> # mission.add_stage(some_stage)
    >>> # mission.add_deployable(some_deployable)
    >>> len(mission.stages)
    0
    """

    def __init__(self, name: str = "Mission", root_vehicle=None):
        self.name = name
        self.root_vehicle = root_vehicle
        self.stages: list = []
        self.deployables: list = []
        self._flight_inputs: dict[str, dict[str, Any]] = {}
        self._root_flight_inputs: dict[str, Any] = {}

    # ------------------------------------------------------------------
    # Mutating helpers
    # ------------------------------------------------------------------

    def add_stage(self, stage):
        """Append a stage to this mission.

        Parameters
        ----------
        stage : :class:`~rocketpy.mission.Stage`
            The stage to add.  Will be validated before appending.

        Raises
        ------
        ValueError
            If *stage* fails its own :meth:`~rocketpy.mission.Stage.validate`
            check.
        TypeError
            If *stage* is not a :class:`~rocketpy.mission.Stage` instance.
        """
        from rocketpy.mission.stage import Stage  # local import to avoid circularity

        if not isinstance(stage, Stage):
            raise TypeError(f"Expected a Stage instance, got {type(stage).__name__!r}.")
        stage.validate()
        self.stages.append(stage)
        self._flight_inputs.setdefault(self._item_key(stage), {})

    def add_deployable(self, deployable):
        """Append a deployable to this mission.

        Parameters
        ----------
        deployable : :class:`~rocketpy.mission.Deployable`
            The deployable to add.  Will be validated before appending.

        Raises
        ------
        ValueError
            If *deployable* fails its own
            :meth:`~rocketpy.mission.Deployable.validate` check.
        TypeError
            If *deployable* is not a
            :class:`~rocketpy.mission.Deployable` instance.
        """
        from rocketpy.mission.deployable import Deployable  # local import

        if not isinstance(deployable, Deployable):
            raise TypeError(
                f"Expected a Deployable instance, got {type(deployable).__name__!r}."
            )
        deployable.validate()
        self.deployables.append(deployable)
        self._flight_inputs.setdefault(self._item_key(deployable), {})

    def set_root_vehicle(self, vehicle):
        """Set the assembled vehicle flown before any stage/deployable event.

        Parameters
        ----------
        vehicle : Rocket or FlightBody
            The root vehicle. Unlike stages/deployables, it is not wrapped
            in an :class:`~rocketpy.mission.AttachedItem` and is not
            returned by :meth:`attached_items`.
        """
        self.root_vehicle = vehicle

    def set_root_flight_inputs(self, **flight_inputs):
        """Set flight inputs used for the root vehicle's flight.

        Parameters
        ----------
        **flight_inputs
            Keyword arguments forwarded to ``rocketpy.simulation.Flight``
            when the root vehicle is executed.
        """
        self._root_flight_inputs.update(flight_inputs)

    def get_root_flight_inputs(self) -> dict[str, Any]:
        """Return configured flight inputs for the root vehicle.

        Returns
        -------
        dict[str, Any]
            Copy of configured inputs. Empty dict when not configured.
        """
        return dict(self._root_flight_inputs)

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------

    def attached_items(self):
        """Return all attached items (stages and deployables) in priority order.

        Stages are listed before deployables.

        Returns
        -------
        list[:class:`~rocketpy.mission.AttachedItem`]
            Combined list of :attr:`stages` followed by :attr:`deployables`.
        """
        return list(self.stages) + list(self.deployables)

    @property
    def number_of_stages(self) -> int:
        """Number of stages registered in this mission."""
        return len(self.stages)

    def connection_map(self) -> dict[str, dict[str, Any]]:
        """Return mission attachment metadata keyed by item name.

        Returns
        -------
        dict[str, dict[str, Any]]
            For each stage/deployable item, stores its parent/child attachment
            frame positions, orientation and constraints.
        """
        connections = {}
        for item in self.attached_items():
            attachment = item.attachment
            connections[item.name] = {
                "parent_frame_position": attachment.parent_frame_position,
                "child_frame_position": attachment.child_frame_position,
                "orientation": attachment.orientation,
                "constraints": attachment.constraints,
            }
        return connections

    def set_flight_inputs(self, item, **flight_inputs):
        """Set per-item inputs used by :class:`MissionExecutor`.

        Parameters
        ----------
        item : :class:`~rocketpy.mission.AttachedItem` or str
            Attached item instance, or its name.
        **flight_inputs
            Keyword arguments forwarded to ``rocketpy.simulation.Flight``
            when this mission item is executed.

        Raises
        ------
        KeyError
            If *item* does not belong to this mission.
        """
        key = self._resolve_item_key(item)
        current = dict(self._flight_inputs.get(key, {}))
        current.update(flight_inputs)
        self._flight_inputs[key] = current

    def get_flight_inputs(self, item) -> dict[str, Any]:
        """Return configured per-item flight inputs.

        Parameters
        ----------
        item : :class:`~rocketpy.mission.AttachedItem` or str
            Attached item instance, or its name.

        Returns
        -------
        dict[str, Any]
            Copy of configured inputs. Empty dict when not configured.

        Raises
        ------
        KeyError
            If *item* does not belong to this mission.
        """
        key = self._resolve_item_key(item)
        return dict(self._flight_inputs.get(key, {}))

    def describe(self) -> str:
        """Return a human-readable, multi-line summary of this mission.

        Returns
        -------
        str
            Summary including the mission name, root vehicle, stage states,
            deployables, and configured per-item flight inputs.
        """
        lines = [f"Mission: {self.name!r}"]
        if self.root_vehicle is None:
            lines.append("root_vehicle: not set")
        else:
            root_name = getattr(self.root_vehicle, "name", None)
            lines.append(
                f"root_vehicle: {type(self.root_vehicle).__name__}"
                + (f" (name={root_name!r})" if root_name else "")
            )
        lines.append(f"stages ({self.number_of_stages}):")
        for stage in self.stages:
            lines.append(f"  - {stage.name!r}: state={stage.state.name}")
        lines.append(f"deployables ({len(self.deployables)}):")
        for deployable in self.deployables:
            lines.append(f"  - {deployable.name!r}")
        for item in self.attached_items():
            inputs = self.get_flight_inputs(item)
            if inputs:
                lines.append(f"flight_inputs[{item.name!r}]: {inputs}")
        return "\n".join(lines)

    def validate(self, require_root_vehicle: bool = False):
        """Validate the whole mission's configuration.

        Re-validates every attached item and checks mission-wide invariants
        that individual item validation cannot catch, such as duplicate
        item names and root vehicle presence.

        Parameters
        ----------
        require_root_vehicle : bool, optional
            If ``True``, raise when :attr:`root_vehicle` is unset instead of
            only warning. Defaults to ``False``.

        Raises
        ------
        ValueError
            If any attached item fails validation, if two items share the
            same name, or if *require_root_vehicle* is ``True`` and
            :attr:`root_vehicle` is unset.
        """
        errors = []

        names_seen = set()
        for item in self.attached_items():
            if item.name in names_seen:
                errors.append(f"Duplicate attached item name: {item.name!r}.")
            names_seen.add(item.name)

            try:
                item.validate()
            except ValueError as exc:
                errors.append(f"{item.name!r}: {exc}")

        if errors:
            raise ValueError(
                f"Mission {self.name!r} failed validation:\n"
                + "\n".join(f"  - {error}" for error in errors)
            )

        if self.root_vehicle is None:
            message = f"Mission {self.name!r} has no root_vehicle set."
            if require_root_vehicle:
                raise ValueError(message)
            warnings.warn(message)

    def _item_key(self, item) -> str:
        # Internal opaque identifier used only as dict key to avoid collisions
        # between Stage and Deployable items sharing the same name.
        return f"{type(item).__name__}:{item.name}"

    def _resolve_item_key(self, item) -> str:
        if isinstance(item, str):
            for attached_item in self.attached_items():
                if attached_item.name == item:
                    return self._item_key(attached_item)
            raise KeyError(f"No attached mission item named {item!r}.")

        for attached_item in self.attached_items():
            if attached_item is item:
                return self._item_key(attached_item)
        raise KeyError("Attached mission item does not belong to this mission.")

    # ------------------------------------------------------------------
    # Dunder
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"Mission(name={self.name!r}, "
            f"stages={len(self.stages)}, "
            f"deployables={len(self.deployables)})"
        )

    def __len__(self) -> int:
        return len(self.stages) + len(self.deployables)
