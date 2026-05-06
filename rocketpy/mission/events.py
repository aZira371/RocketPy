"""Event hierarchy for the mission architecture."""

from abc import ABC, abstractmethod


class Event(ABC):
    """Abstract base class for all mission events.

    An event monitors simulation state and, when its trigger condition is
    met, applies a transformation to a :class:`FlightBranch`.

    Parameters
    ----------
    name : str
        Human-readable name for the event (e.g. ``"main_chute"``).
    priority : int, optional
        Ordering priority when multiple events fire at the same instant.
        Lower values are processed first.  Defaults to ``0``.

    Attributes
    ----------
    name : str
    priority : int
    """

    def __init__(self, name: str, priority: int = 0):
        self.name = name
        self.priority = priority

    @abstractmethod
    def should_fire(self, state, context) -> bool:
        """Determine whether this event should fire given the current state.

        Parameters
        ----------
        state : object
            Current simulation state vector.
        context : object
            Simulation context object providing environment, time, etc.

        Returns
        -------
        bool
            ``True`` if the event should be triggered.
        """

    @abstractmethod
    def apply(self, branch, context):
        """Apply the event's effect to a flight branch.

        Parameters
        ----------
        branch : :class:`~rocketpy.simulation.FlightBranch`
            The branch that is currently being integrated.
        context : object
            Simulation context.
        """

    def __repr__(self) -> str:
        return f"{type(self).__name__}(name={self.name!r}, priority={self.priority})"


# ---------------------------------------------------------------------------
# Concrete event types
# ---------------------------------------------------------------------------


class DeploymentEvent(Event):
    """Event that triggers the deployment of a :class:`Deployable`.

    Parameters
    ----------
    name : str
        Human-readable name.
    trigger : callable
        ``trigger(state, context) -> bool`` – returns ``True`` when the
        deployable should be released.
    priority : int, optional
        Processing priority.  Defaults to ``0``.
    """

    def __init__(self, name: str, trigger, priority: int = 0):
        super().__init__(name, priority)
        self._trigger = trigger

    def should_fire(self, state, context) -> bool:
        return bool(self._trigger(state, context))

    def apply(self, branch, context):
        """Deploy the associated :class:`Deployable` from *branch*.

        Parameters
        ----------
        branch : FlightBranch
            Active branch.
        context : object
            Simulation context.
        """
        # The actual separation logic is delegated to the Deployable's
        # SeparationModel and ParentUpdate.  This stub is intentional;
        # the simulation engine is responsible for the full orchestration.


class StageSeparationEvent(Event):
    """Event that triggers the mechanical separation of a :class:`Stage`.

    Parameters
    ----------
    name : str
        Human-readable name.
    trigger : callable
        ``trigger(state, context) -> bool``.
    priority : int, optional
        Processing priority.  Defaults to ``0``.
    """

    def __init__(self, name: str, trigger, priority: int = 0):
        super().__init__(name, priority)
        self._trigger = trigger

    def should_fire(self, state, context) -> bool:
        return bool(self._trigger(state, context))

    def apply(self, branch, context):
        """Separate the stage from its parent branch.

        Parameters
        ----------
        branch : FlightBranch
            Active branch.
        context : object
            Simulation context.
        """


class IgnitionEvent(Event):
    """Event that triggers motor ignition on a :class:`Stage`.

    Parameters
    ----------
    name : str
        Human-readable name.
    trigger : callable
        ``trigger(state, context) -> bool``.
    priority : int, optional
        Processing priority.  Defaults to ``0``.
    """

    def __init__(self, name: str, trigger, priority: int = 0):
        super().__init__(name, priority)
        self._trigger = trigger

    def should_fire(self, state, context) -> bool:
        return bool(self._trigger(state, context))

    def apply(self, branch, context):
        """Ignite the stage motor.

        Parameters
        ----------
        branch : FlightBranch
            Active branch.
        context : object
            Simulation context.
        """


class RecoveryEvent(Event):
    """Event that triggers a recovery system (e.g. parachute deployment).

    Parameters
    ----------
    name : str
        Human-readable name.
    trigger : callable
        ``trigger(state, context) -> bool``.
    priority : int, optional
        Processing priority.  Defaults to ``0``.
    """

    def __init__(self, name: str, trigger, priority: int = 0):
        super().__init__(name, priority)
        self._trigger = trigger

    def should_fire(self, state, context) -> bool:
        return bool(self._trigger(state, context))

    def apply(self, branch, context):
        """Activate the recovery system.

        Parameters
        ----------
        branch : FlightBranch
            Active branch.
        context : object
            Simulation context.
        """
