"""MissionExecutor – high-level API to execute all mission flight branches."""

from dataclasses import dataclass

from rocketpy.body import BodyResolver, FlightCompatibleRocket
from rocketpy.mission.branch_result import BranchResult
from rocketpy.mission.flight_config import FlightConfig
from rocketpy.mission.mission_result import MissionResult
from rocketpy.mission.stage import Stage
from rocketpy.mission.stage_state import StageState
from rocketpy.simulation import Flight


@dataclass(frozen=True)
class MissionExecutionResult:
    """Single execution output for one mission item.

    .. deprecated::
        Kept for backward compatibility with :meth:`MissionExecutor.execute`.
        Use :meth:`MissionExecutor.run` and :class:`BranchResult` instead.
    """

    item_name: str
    flight: Flight


class MissionExecutor:
    """Executes all mission stages/deployables from a :class:`Mission`.

    The executor provides a mission-first API: users configure mission items
    and optional per-item flight inputs in :class:`~rocketpy.mission.Mission`,
    then call :meth:`run` once to run all corresponding flight simulations.

    Each mission item's flight is built independently and chained
    sequentially: an item's flight starts from the previous flight's final
    state unless an explicit ``initial_solution`` is configured for it. This
    is a sequential approximation of staging – it does not simulate
    diverging trajectories (e.g. a spent stage falling away while the next
    stage ascends) as two separate, simultaneous flights. True branching
    physics is future-phase work; see :class:`~rocketpy.simulation.FlightBranch`.
    """

    def __init__(
        self,
        mission,
        environment,
        rail_length: float,
        default_flight_inputs=None,
        flight_class=Flight,
    ):
        self.mission = mission
        self.environment = environment
        self.rail_length = rail_length
        self.default_flight_inputs = dict(default_flight_inputs or {})
        self.flight_class = flight_class

    def run(self) -> MissionResult:
        """Execute the root vehicle (if any) and all mission attached items.

        Returns
        -------
        MissionResult
            Aggregated result containing the root flight (if
            ``mission.root_vehicle`` is set) and one branch per attached
            item, in mission order: stages first, then deployables.
        """
        base_config = self._base_config()

        root_flight = None
        if self.mission.root_vehicle is not None:
            root_config = base_config.for_branch(
                "root", self.mission.get_root_flight_inputs()
            )
            root_flight = self._build_flight(self.mission.root_vehicle, root_config)

        branch_results = []
        previous_flight = root_flight
        for item in self.mission.attached_items():
            branch = self._build_branch(item, base_config, previous_flight)
            branch_results.append(branch)
            previous_flight = branch.flight

        return MissionResult(
            root_flight=root_flight,
            branch_flights={branch.name: branch.flight for branch in branch_results},
            branch_results=branch_results,
        )

    def dry_run(self) -> list:
        """Resolve every mission body and flight configuration without simulating.

        Validates that every mission body (including the root vehicle, if
        set) can drive a real :class:`~rocketpy.simulation.Flight`, and
        resolves the :class:`FlightConfig` each item would be built with.
        This lets callers catch body-compatibility errors (e.g. an
        unsupported :class:`~rocketpy.body.FlightBody`) or misconfigured
        flight inputs before paying for any simulation.

        Returns
        -------
        list[FlightConfig]
            Resolved configs in the same order :meth:`run` would build
            flights: the root vehicle's config first (if set), then one per
            attached item.
        """
        base_config = self._base_config()
        configs = []

        if self.mission.root_vehicle is not None:
            BodyResolver.to_flight_rocket(
                BodyResolver.to_body(self.mission.root_vehicle)
            )
            configs.append(
                base_config.for_branch("root", self.mission.get_root_flight_inputs())
            )

        for item in self.mission.attached_items():
            BodyResolver.to_flight_rocket(BodyResolver.to_body(item.body))
            configs.append(
                base_config.for_branch(item.name, self.mission.get_flight_inputs(item))
            )

        return configs

    def execute(self) -> list:
        """Execute configured mission stage/deployable flights in order.

        .. deprecated::
            Use :meth:`run` instead, which also builds the root vehicle's
            flight and returns a richer :class:`~rocketpy.mission.MissionResult`.

        Returns
        -------
        list[MissionExecutionResult]
            Flight results in mission order: stages first, then deployables.
        """
        base_config = self._base_config()
        results = []
        previous_flight = None

        for item in self.mission.attached_items():
            branch = self._build_branch(item, base_config, previous_flight)
            results.append(
                MissionExecutionResult(item_name=branch.name, flight=branch.flight)
            )
            previous_flight = branch.flight

        return results

    def _base_config(self) -> FlightConfig:
        """Build the base :class:`FlightConfig` from ``default_flight_inputs``."""
        return FlightConfig(rail_length=self.rail_length).for_branch(
            "default", self.default_flight_inputs
        )

    def _build_flight(self, body, config: FlightConfig, events=None):
        """Resolve *body* and construct a :class:`~rocketpy.simulation.Flight`.

        *events* (the item's mission-lifecycle
        :class:`~rocketpy.simulation.events.Event` instances, if any) are
        forwarded as Flight's ``custom_events``, unless the config already
        provides an explicit ``custom_events`` override.
        """
        rocket = BodyResolver.to_flight_rocket(BodyResolver.to_body(body))
        kwargs = config.to_flight_kwargs()
        if events:
            kwargs.setdefault("custom_events", list(events))
        return self.flight_class(
            rocket=rocket,
            environment=self.environment,
            rail_length=config.rail_length,
            **kwargs,
        )

    def _build_branch(
        self, item, base_config: FlightConfig, previous_flight
    ) -> BranchResult:
        """Build a single :class:`BranchResult` for *item*, chaining from
        *previous_flight* when the item has no explicit ``initial_solution``.
        """
        config = base_config.for_branch(item.name, self.mission.get_flight_inputs(item))
        if config.initial_solution is None and previous_flight is not None:
            config.initial_solution = previous_flight

        flight = self._build_flight(item.body, config, events=item.events)

        if isinstance(item, Stage):
            # Mission-level bookkeeping only: the sequential model does not
            # simulate real staging events, so a stage is considered SPENT
            # once its (fully independent) branch flight has been built.
            item.state = StageState.SPENT

        return BranchResult(
            name=item.name,
            flight=flight,
            item=item,
            event_time=flight.t_initial,
            initial_solution=(
                list(flight.initial_solution)
                if flight.initial_solution is not None
                else []
            ),
        )
