"""MissionResult – aggregated output of a full MissionExecutor.run()."""

from dataclasses import dataclass, field
from typing import Any

from rocketpy.mission.branch_result import BranchResult


@dataclass
class MissionResult:
    """Aggregated result of running a :class:`~rocketpy.mission.Mission`.

    Parameters
    ----------
    root_flight : :class:`~rocketpy.simulation.Flight` or None
        Flight of the root vehicle, or ``None`` if the mission has no
        ``root_vehicle`` set.
    branch_flights : dict[str, Flight]
        Mapping of attached item name to its simulated flight, in mission
        order.
    branch_results : list[:class:`BranchResult`]
        Ordered, richer per-item execution records.

    Attributes
    ----------
    root_flight : Flight or None
    branch_flights : dict[str, Flight]
    branch_results : list[BranchResult]
    """

    root_flight: Any
    branch_flights: dict
    branch_results: list = field(default_factory=list)

    def all_flights(self) -> list:
        """Return every flight produced by this mission, in mission order.

        Returns
        -------
        list[Flight]
            ``[root_flight]`` (if set) followed by each branch's flight.
        """
        flights = []
        if self.root_flight is not None:
            flights.append(self.root_flight)
        flights.extend(branch.flight for branch in self.branch_results)
        return flights

    def get_flight(self, name: str):
        """Return the flight for the given name.

        Parameters
        ----------
        name : str
            ``"root"`` for the root vehicle's flight, or an attached item's
            name.

        Returns
        -------
        Flight
            The matching flight.

        Raises
        ------
        KeyError
            If *name* is ``"root"`` but no root flight exists, or if *name*
            does not match any branch.
        """
        if name == "root":
            if self.root_flight is None:
                raise KeyError("Mission has no root_flight.")
            return self.root_flight
        return self.branch_flights[name]

    def get_branch_result(self, name: str) -> BranchResult:
        """Return the :class:`BranchResult` for the given attached item name.

        Parameters
        ----------
        name : str
            Attached item name.

        Returns
        -------
        BranchResult
            The matching branch result.

        Raises
        ------
        KeyError
            If *name* does not match any branch.
        """
        for branch in self.branch_results:
            if branch.name == name:
                return branch
        raise KeyError(f"No branch result named {name!r}.")

    def summary(self) -> str:
        """Return a one-line-per-flight human-readable summary.

        Returns
        -------
        str
            For each flight: name, apogee, and impact velocity.
        """
        lines = []
        if self.root_flight is not None:
            lines.append(
                f"root: apogee = {self.root_flight.apogee:.2f} m, "
                f"impact velocity = {self.root_flight.impact_velocity:.2f} m/s"
            )
        for branch in self.branch_results:
            lines.append(
                f"{branch.name}: apogee = {branch.flight.apogee:.2f} m, "
                f"impact velocity = {branch.flight.impact_velocity:.2f} m/s"
            )
        return "\n".join(lines)

    def plot_all(self):
        """Plot the 3D trajectories of every flight in this mission result.

        Returns
        -------
        CompareFlights
            The comparison object used to render the plot.
        """
        from rocketpy.plots import CompareFlights  # local: avoid import-time dep

        comparison = CompareFlights(self.all_flights())
        comparison.trajectories_3d(legend=True)
        return comparison
