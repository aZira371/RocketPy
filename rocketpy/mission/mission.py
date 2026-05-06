"""Mission – top-level container for a multistage rocket mission."""


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
            raise TypeError(
                f"Expected a Stage instance, got {type(stage).__name__!r}."
            )
        stage.validate()
        self.stages.append(stage)

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
