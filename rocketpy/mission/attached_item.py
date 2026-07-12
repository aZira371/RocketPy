"""AttachedItem – abstract base for items that can be attached to a body."""

from abc import ABC, abstractmethod


class AttachedItem(ABC):
    """Abstract base class for objects that can be attached to a parent body.

    Every mission item (a :class:`Deployable` or a :class:`Stage`) is an
    :class:`AttachedItem`.  It owns a :class:`~rocketpy.body.BodyLike`
    instance (the physical body), an :class:`~rocketpy.mission.Attachment`
    (the mechanical link), and a list of :class:`~rocketpy.mission.Event`
    objects that govern its lifecycle.

    Parameters
    ----------
    name : str
        Human-readable identifier for this item.
    body : :class:`~rocketpy.body.BodyLike`
        The physical body associated with this item.
    attachment : :class:`~rocketpy.mission.Attachment`
        The mechanical link that positions and orients this item relative
        to its parent.
    events : list[:class:`~rocketpy.mission.Event`], optional
        Events that can be fired while this item is attached.

    Attributes
    ----------
    name : str
    body : BodyLike
    attachment : Attachment
    events : list[Event]
    """

    def __init__(self, name, body, attachment, events=None):
        self.name = name
        self.body = body
        self.attachment = attachment
        self.events = list(events or [])

    @abstractmethod
    def validate(self):
        """Validate that this item is correctly configured.

        Raises
        ------
        ValueError
            If any required field is missing or inconsistent.
        """

    def __repr__(self) -> str:
        return f"{type(self).__name__}(name={self.name!r})"
