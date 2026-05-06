"""ParentUpdate – interface for modifying a parent body after separation."""

from abc import ABC, abstractmethod


class ParentUpdate(ABC):
    """Interface for updating a parent body when a child separates.

    When a :class:`~rocketpy.mission.Deployable` or
    :class:`~rocketpy.mission.Stage` separates from its parent, the
    parent body may need to be updated to account for the mass and
    inertia change caused by the separation.  Concrete implementations
    of this interface perform that update in place.
    """

    @abstractmethod
    def apply(self, parent_body):
        """Mutate *parent_body* to reflect the separation.

        Parameters
        ----------
        parent_body : :class:`~rocketpy.body.BodyLike`
            The parent body to update.  Implementations may, for example,
            remove a nose-cone mass component or re-parametrize the mass
            model.
        """


class NoOpParentUpdate(ParentUpdate):
    """A :class:`ParentUpdate` that makes no changes to the parent.

    Use this when the parent body's properties do not change as a result
    of the separation (e.g. the separated mass is negligible compared to
    the remaining body).
    """

    def apply(self, parent_body):
        """Do nothing.

        Parameters
        ----------
        parent_body : :class:`~rocketpy.body.BodyLike`
            Ignored.
        """
