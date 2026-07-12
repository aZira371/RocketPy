"""BranchResult – execution record for a single mission item's flight."""

from dataclasses import dataclass
from typing import Any


@dataclass
class BranchResult:
    """Execution record for one mission item's :class:`~rocketpy.simulation.Flight`.

    Parameters
    ----------
    name : str
        Name of the attached item this branch was built for.
    flight : :class:`~rocketpy.simulation.Flight`
        The simulated flight for this branch.
    item : :class:`~rocketpy.mission.AttachedItem`
        The mission item (``Stage`` or ``Deployable``) this branch was built
        from.
    event_time : float
        Simulation time, in seconds, at which this branch's flight begins.
    initial_solution : list
        Initial solution state vector used to start this branch's flight.
        Empty when the flight started from a fresh launch-rail state.

    Attributes
    ----------
    name : str
    flight : Flight
    item : AttachedItem
    event_time : float
    initial_solution : list
    """

    name: str
    flight: Any
    item: Any
    event_time: float
    initial_solution: list
