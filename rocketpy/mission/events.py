"""Mission-lifecycle events, built directly on rocketpy.simulation.events.Event.

The mission architecture does not define its own event base class: each
event below is a thin :class:`~rocketpy.simulation.events.Event` subclass
that fixes the *callback* to a specific mission-lifecycle action (deployment,
stage separation, ignition, recovery), while the *trigger* is supplied by the
caller using the same ``trigger(**kwargs) -> bool`` convention as any other
:class:`~rocketpy.simulation.events.Event` (``kwargs`` includes ``time``,
``state``, ``flight``, ``rocket``, ...; see :class:`~rocketpy.simulation.events.Event`
for the full list).

Each event fires at most once (``trigger_only_once=True``): deployment,
separation, and ignition are one-shot lifecycle transitions, not continuous
conditions, so a trigger that stays true after firing (e.g. ``vz <= 0``
during descent) must not repeatedly re-invoke the callback.
"""

from rocketpy.simulation.events.event import Event


class DeploymentEvent(Event):
    """Event that triggers the deployment of a :class:`Deployable`.

    Parameters
    ----------
    name : str
        Human-readable name.
    trigger : callable
        ``trigger(**kwargs) -> bool`` – returns ``True`` when the deployable
        should be released.
    priority : int, optional
        Event evaluation priority (see
        :class:`~rocketpy.simulation.events.Event`). Defaults to ``4``
        (custom/user-defined), since deployment is a mission-level, not a
        core-flight, event.
    """

    def __init__(self, name, trigger, priority=4):
        super().__init__(
            callback=self._deploy,
            trigger=trigger,
            name=name,
            priority=priority,
            trigger_only_once=True,
        )

    def _deploy(self, **kwargs):
        """Deploy the associated :class:`Deployable`.

        Notes
        -----
        The actual separation logic is delegated to the Deployable's
        :class:`~rocketpy.mission.SeparationModel` and
        :class:`~rocketpy.mission.ParentUpdate`.

        .. todo::
            Wire up ``Deployable.separation.apply()`` and
            ``Deployable.parent_update.apply()`` via this callback's
            ``event.commands`` once the mission executor drives branch
            spawning (see :class:`~rocketpy.simulation.FlightBranch`).
        """


class StageSeparationEvent(Event):
    """Event that triggers the mechanical separation of a :class:`Stage`.

    Parameters
    ----------
    name : str
        Human-readable name.
    trigger : callable
        ``trigger(**kwargs) -> bool``.
    priority : int, optional
        Event evaluation priority. Defaults to ``4``.
    """

    def __init__(self, name, trigger, priority=4):
        super().__init__(
            callback=self._separate,
            trigger=trigger,
            name=name,
            priority=priority,
            trigger_only_once=True,
        )

    def _separate(self, **kwargs):
        """Separate the stage from its parent branch.

        .. todo::
            Invoke ``Stage.separation.apply()`` and
            ``Stage.parent_update.apply()``, and spawn a new child
            :class:`~rocketpy.simulation.FlightBranch` for the separated
            stage, via this callback's ``event.commands``.
        """


class IgnitionEvent(Event):
    """Event that triggers motor ignition on a :class:`Stage`.

    Parameters
    ----------
    name : str
        Human-readable name.
    trigger : callable
        ``trigger(**kwargs) -> bool``.
    priority : int, optional
        Event evaluation priority. Defaults to ``4``.
    """

    def __init__(self, name, trigger, priority=4):
        super().__init__(
            callback=self._ignite,
            trigger=trigger,
            name=name,
            priority=priority,
            trigger_only_once=True,
        )

    def _ignite(self, **kwargs):
        """Ignite the stage motor.

        .. todo::
            Activate the propulsion model on the stage body and transition
            :attr:`Stage.state` to :attr:`~rocketpy.mission.StageState.IGNITED`.
        """


class RecoveryEvent(Event):
    """Event that triggers a recovery system (e.g. parachute deployment).

    Parameters
    ----------
    name : str
        Human-readable name.
    trigger : callable
        ``trigger(**kwargs) -> bool``.
    priority : int, optional
        Event evaluation priority. Defaults to ``4``.
    """

    def __init__(self, name, trigger, priority=4):
        super().__init__(
            callback=self._recover,
            trigger=trigger,
            name=name,
            priority=priority,
            trigger_only_once=True,
        )

    def _recover(self, **kwargs):
        """Activate the recovery system.

        .. todo::
            Deploy the parachute or other recovery device attached to the
            branch body.
        """
