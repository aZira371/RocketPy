"""SeparationModel – interface for child/parent separation dynamics."""

from abc import ABC, abstractmethod


class SeparationModel(ABC):
    """Interface for modelling the separation impulse between two bodies.

    When a :class:`~rocketpy.mission.Deployable` or
    :class:`~rocketpy.mission.Stage` separates from its parent, a
    :class:`SeparationModel` is responsible for computing any
    velocity/orientation perturbations applied to both the parent and
    child bodies at the instant of separation.

    Implementors should override :meth:`apply` and may store any physical
    parameters (e.g. spring constant, separation charge energy) as
    instance attributes.
    """

    @abstractmethod
    def apply(self, parent_state, child_state, context):
        """Apply separation dynamics and return updated states.

        Parameters
        ----------
        parent_state : object
            State of the parent body just before separation.
        child_state : object
            State of the child body just before separation.
        context : object
            Simulation context (provides environment, time, etc.).

        Returns
        -------
        tuple[object, object]
            Updated ``(parent_state, child_state)`` after applying the
            separation model.
        """


class InstantaneousSeparation(SeparationModel):
    """Trivial separation model that applies no impulse.

    Both bodies continue with whatever velocity they had at the moment of
    separation.  This is the default model when no physical separation
    mechanism is specified.
    """

    def apply(self, parent_state, child_state, context):
        """Return states unchanged.

        Parameters
        ----------
        parent_state : object
            Parent state.
        child_state : object
            Child state.
        context : object
            Simulation context.

        Returns
        -------
        tuple[object, object]
            ``(parent_state, child_state)`` unmodified.
        """
        return parent_state, child_state
