"""Mission – top-level container for a multistage rocket mission."""

from typing import Any


class Mission:
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

    Attributes
    ----------
    name : str
        Mission name.
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

    def __init__(self, name: str = "Mission"):
        self.name = name
        self.stages: list = []
        self.deployables: list = []
        self._flight_inputs: dict[str, dict[str, Any]] = {}

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

    def _item_key(self, item) -> str:
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
