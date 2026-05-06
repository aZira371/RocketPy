"""Attachment – describes the mechanical link between two bodies."""


class Attachment:
    """Encodes how a child body is attached to a parent body.

    The attachment resolves the child's initial pose (position + orientation)
    given the parent's current state, and records any mechanical constraints
    that apply while the link is active.

    Parameters
    ----------
    parent_frame_position : array-like
        Position of the attachment point in the **parent** body frame,
        in meters.  Typically a 3-vector ``[x, y, z]``.
    child_frame_position : array-like
        Position of the attachment point in the **child** body frame,
        in meters.
    orientation : array-like or None, optional
        Relative orientation of the child frame with respect to the parent
        frame.  Can be a rotation matrix, quaternion, or any representation
        that the caller chooses to interpret.  ``None`` means co-aligned
        frames.
    constraints : str, optional
        Textual description of the mechanical constraint (e.g.
        ``"rigid"``, ``"hinged"``).  Purely informational at this stage.
    tags : dict, optional
        Arbitrary key-value metadata for downstream consumers.

    Attributes
    ----------
    parent_frame_position : array-like
    child_frame_position : array-like
    orientation : array-like or None
    constraints : str
    tags : dict
    """

    def __init__(
        self,
        parent_frame_position,
        child_frame_position,
        orientation=None,
        constraints="rigid",
        tags=None,
    ):
        self.parent_frame_position = parent_frame_position
        self.child_frame_position = child_frame_position
        self.orientation = orientation
        self.constraints = constraints
        self.tags = dict(tags or {})

    def resolve_child_pose(self, parent_state):
        """Compute the initial child pose from the parent state.

        .. note::
            **Stub implementation** – this method currently returns
            *parent_state* unchanged and does *not* apply the attachment
            offsets (:attr:`parent_frame_position`,
            :attr:`child_frame_position`) or :attr:`orientation`.  A full
            6-DOF pose resolver will be implemented in a future iteration of
            the multistage simulation engine.

        Parameters
        ----------
        parent_state : object
            Current state of the parent body (position, orientation, …).

        Returns
        -------
        object
            Initial state for the child body (currently equal to
            *parent_state*).
        """
        # TODO: compose parent_state with attachment offsets and orientation
        # to produce the true initial child pose.
        return parent_state

    def __repr__(self) -> str:
        return (
            f"Attachment("
            f"parent_frame_position={self.parent_frame_position!r}, "
            f"child_frame_position={self.child_frame_position!r}, "
            f"constraints={self.constraints!r})"
        )
