"""Module containing the Event class used to record discrete occurrences
during a rocket flight simulation.

Design rationale
----------------
Events are fundamentally a **simulation-time** concept: they mark the instant
at which something happens to the rocket during flight (e.g. a parachute
deploys, a stage separates, or a deployable is released). Because the timing
of an event is determined by the ODE solver running inside
:class:`~rocketpy.simulation.flight.Flight`, the natural home for this class
is the ``simulation`` sub-package, not the ``rocket`` sub-package.

The ``rocket`` sub-package defines *what* components exist on the rocket
(motors, fins, parachutes …). The ``simulation`` sub-package records *when*
and *how* those components become active. Placing :class:`Event` here keeps
the ``rocket`` sub-package free of simulation state and allows future
simulation components (e.g. ``MonteCarlo``, multistage managers) to import
:class:`Event` without creating circular dependencies.
"""


class Event:
    """Records a discrete event that occurs during a flight simulation.

    An :class:`Event` captures the simulation time at which something
    happened (e.g. a parachute deployed, a stage separated, a deployable
    was released) together with metadata about *why* it happened and
    *what* object was involved.

    This class is the intended building block for deployable-deployment
    tracking and future multistage simulation support in RocketPy.

    .. note::

        For **backward compatibility**, :class:`Event` also supports
        index-based access (``event[0]`` → ``event.time``,
        ``event[1]`` → ``event.action``), matching the legacy
        ``[time, parachute]`` list format previously stored in
        :attr:`~rocketpy.simulation.flight.Flight.parachute_events`.

    Attributes
    ----------
    time : float
        Simulation time, in seconds, at which the event was triggered.
    trigger : callable, float, or str
        The condition or mechanism that caused the event. For parachutes
        this is the same object as :attr:`~rocketpy.rocket.Parachute.trigger`
        (a callable, a float height, or the string ``"apogee"``).
    event_type : str
        A string label that categorises the event. Common values are:

        - ``"parachute"`` — a parachute deployment.
        - ``"stage_separation"`` — a rocket-stage separation event.
        - ``"deployable"`` — release of a generic deployable payload.
    action : object or None
        The object associated with the event (e.g. the
        :class:`~rocketpy.rocket.Parachute` instance that was deployed).
        ``None`` when no specific action object is present.

    Examples
    --------
    Creating an event that records a parachute deployment:

    >>> from rocketpy.simulation.event import Event
    >>> drogue = object()  # stand-in for a Parachute instance
    >>> ev = Event(time=45.3, trigger="apogee", event_type="parachute",
    ...            action=drogue)
    >>> ev.time
    45.3
    >>> ev.event_type
    'parachute'
    >>> ev[0]  # backward-compatible index access
    45.3
    >>> ev[1] is drogue
    True
    """

    def __init__(self, time, trigger, event_type="parachute", action=None):
        """Initialise a new :class:`Event`.

        Parameters
        ----------
        time : float
            Simulation time, in seconds, at which the event was triggered.
        trigger : callable, float, or str
            The condition or mechanism that caused the event to fire.
        event_type : str, optional
            Category label for the event. Typical values are
            ``"parachute"``, ``"stage_separation"``, and
            ``"deployable"``. Default is ``"parachute"``.
        action : object or None, optional
            The object linked to the event (e.g. the
            :class:`~rocketpy.rocket.Parachute` that was deployed).
            Default is ``None``.
        """
        self.time = time
        self.trigger = trigger
        self.event_type = event_type
        self.action = action

    # ------------------------------------------------------------------
    # Backward-compatibility interface
    # ------------------------------------------------------------------

    def __getitem__(self, index):
        """Allow index-based access for backward compatibility.

        The legacy ``parachute_events`` list stored plain
        ``[time, parachute]`` two-element lists. Code that accesses
        ``event[0]`` (time) or ``event[1]`` (action / parachute) will
        continue to work unchanged.

        Parameters
        ----------
        index : int
            ``0`` returns :attr:`time`; ``1`` returns :attr:`action`.

        Returns
        -------
        float or object
            The requested attribute value.

        Raises
        ------
        IndexError
            If ``index`` is not ``0`` or ``1``.
        """
        if index == 0:
            return self.time
        if index == 1:
            return self.action
        raise IndexError(
            f"Event index {index} is out of range. "
            "Use index 0 for 'time' or 1 for 'action'."
        )

    # ------------------------------------------------------------------
    # Dunder helpers
    # ------------------------------------------------------------------

    def __repr__(self):
        return (
            f"<Event("
            f"time={self.time:.3f} s, "
            f"event_type='{self.event_type}', "
            f"action={self.action!r})>"
        )

    def __str__(self):
        return (
            f"Event of type '{self.event_type}' triggered at t={self.time:.3f} s"
        )

    def __eq__(self, other):
        """Two events are equal when all their attributes match."""
        if not isinstance(other, Event):
            return NotImplemented
        return (
            self.time == other.time
            and self.trigger == other.trigger
            and self.event_type == other.event_type
            and self.action == other.action
        )
