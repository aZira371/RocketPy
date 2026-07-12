"""Unit tests for rocketpy.mission package.

Covers: Mission, AttachedItem, Deployable, Stage, Attachment, Event
hierarchy, SeparationModel, ParentUpdate, StageState.
"""

import pytest

from rocketpy.body import FlightBody, RocketAdapter
from rocketpy.mission import (
    Attachment,
    Deployable,
    DeploymentEvent,
    Event,
    FlightConfig,
    IgnitionEvent,
    InstantaneousSeparation,
    Mission,
    MissionExecutor,
    NoOpParentUpdate,
    ParentUpdate,
    RecoveryEvent,
    SeparationModel,
    Stage,
    StageSeparationEvent,
    StageState,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_body(name="body", **kwargs):
    """Return a minimal FlightBody for testing."""
    defaults = dict(
        name=name,
        geometry=0.05,
        mass_model=lambda t: 10.0,
        inertia_model=lambda t: (1.0, 1.0, 0.05, 0.0, 0.0, 0.0),
        center_of_mass_model=lambda t: 0.5,
    )
    defaults.update(kwargs)
    return FlightBody(**defaults)


def _make_attachment():
    """Return a minimal Attachment."""
    return Attachment(
        parent_frame_position=[0.0, 0.0, 1.0],
        child_frame_position=[0.0, 0.0, 0.0],
    )


def _always_trigger(state, context):
    return True


def _never_trigger(state, context):
    return False


def _make_deployment_event(name="deploy", trigger=None):
    return DeploymentEvent(name, trigger or _always_trigger)


def _make_deployable(**kwargs):
    defaults = {
        "name": "payload",
        "body": _make_body("payload_body"),
        "attachment": _make_attachment(),
        "deployment_event": _make_deployment_event(),
    }
    defaults.update(kwargs)
    return Deployable(**defaults)


def _make_stage(**kwargs):
    defaults = {
        "name": "stage_2",
        "body": _make_body("stage_body"),
        "attachment": _make_attachment(),
    }
    defaults.update(kwargs)
    return Stage(**defaults)


class FakeRocket:
    """Minimal fake rocket object for MissionExecutor tests."""

    def __init__(self, name="fake_rocket"):
        self.name = name

    def add_motor(self, motor, position):
        """No-op helper to satisfy rocket-like interface in tests."""

    def total_mass(self, t):
        """Return a deterministic mass for test doubles."""
        return 1.0

    def center_of_mass(self, t):
        """Return a deterministic center-of-mass value for test doubles."""
        return 0.0


class _UnsupportedBody:
    """Minimal stub used to assert unsupported-body TypeError paths."""


def _make_rocket_adapter(name="rocket_body"):
    """Create a RocketAdapter with a minimal fake rocket object."""
    return RocketAdapter(FakeRocket(name=name))


# ---------------------------------------------------------------------------
# StageState
# ---------------------------------------------------------------------------


class TestStageState:
    """StageState enum covers all lifecycle states."""

    def test_all_states_exist(self):
        """All four expected states are present."""
        assert StageState.ATTACHED
        assert StageState.IGNITED
        assert StageState.SEPARATED
        assert StageState.SPENT

    def test_states_are_distinct(self):
        """Each state is a unique enum member."""
        states = [
            StageState.ATTACHED,
            StageState.IGNITED,
            StageState.SEPARATED,
            StageState.SPENT,
        ]
        assert len(set(states)) == 4


# ---------------------------------------------------------------------------
# Attachment
# ---------------------------------------------------------------------------


class TestAttachment:
    """Attachment stores positions and resolves child pose."""

    def test_stores_positions(self):
        """parent_frame_position and child_frame_position are stored."""
        parent_pos = [1.0, 0.0, 0.5]
        child_pos = [0.0, 0.0, 0.0]
        attachment = Attachment(parent_pos, child_pos)
        assert attachment.parent_frame_position == parent_pos
        assert attachment.child_frame_position == child_pos

    def test_default_constraints(self):
        """Default constraint string is 'rigid'."""
        attachment = Attachment([0, 0, 0], [0, 0, 0])
        assert attachment.constraints == "rigid"

    def test_custom_tags_stored(self):
        """Custom tags dict is stored."""
        tags = {"zone": "aft"}
        attachment = Attachment([0, 0, 0], [0, 0, 0], tags=tags)
        assert attachment.tags["zone"] == "aft"

    def test_resolve_child_pose_returns_parent_state(self):
        """resolve_child_pose returns the parent state unchanged (stub)."""
        attachment = _make_attachment()
        state = {"x": 0, "y": 0, "z": 100}
        result = attachment.resolve_child_pose(state)
        assert result is state


# ---------------------------------------------------------------------------
# Event hierarchy
# ---------------------------------------------------------------------------


class TestEventHierarchy:
    """Event ABC and concrete subtypes."""

    def test_event_is_abstract(self):
        """Event cannot be instantiated directly."""
        with pytest.raises(TypeError):
            Event("abstract")  # type: ignore[abstract]

    def test_deployment_event_fires_on_true_trigger(self):
        """DeploymentEvent.should_fire returns True when trigger is True."""
        ev = DeploymentEvent("deploy", _always_trigger)
        assert ev.should_fire(None, None) is True

    def test_deployment_event_does_not_fire_on_false_trigger(self):
        """DeploymentEvent.should_fire returns False when trigger is False."""
        ev = DeploymentEvent("deploy", _never_trigger)
        assert ev.should_fire(None, None) is False

    def test_stage_separation_event_fires(self):
        """StageSeparationEvent respects its trigger."""
        ev = StageSeparationEvent("sep", _always_trigger)
        assert ev.should_fire(None, None) is True

    def test_ignition_event_fires(self):
        """IgnitionEvent respects its trigger."""
        ev = IgnitionEvent("ignite", _always_trigger)
        assert ev.should_fire(None, None) is True

    def test_recovery_event_fires(self):
        """RecoveryEvent respects its trigger."""
        ev = RecoveryEvent("recover", _always_trigger)
        assert ev.should_fire(None, None) is True

    def test_event_priority_stored(self):
        """priority attribute is stored correctly."""
        ev = DeploymentEvent("hi_prio", _always_trigger, priority=5)
        assert ev.priority == 5

    @pytest.mark.parametrize(
        "event_class",
        [DeploymentEvent, StageSeparationEvent, IgnitionEvent, RecoveryEvent],
    )
    def test_apply_does_not_raise(self, event_class):
        """apply() can be called without raising on concrete event types."""
        ev = event_class("ev", _always_trigger)
        ev.apply(None, None)  # must not raise


# ---------------------------------------------------------------------------
# SeparationModel
# ---------------------------------------------------------------------------


class TestSeparationModel:
    """SeparationModel ABC and InstantaneousSeparation."""

    def test_separation_model_is_abstract(self):
        """SeparationModel cannot be instantiated directly."""
        with pytest.raises(TypeError):
            SeparationModel()  # type: ignore[abstract]

    def test_instantaneous_returns_states_unchanged(self):
        """InstantaneousSeparation.apply returns (parent_state, child_state) unmodified."""
        model = InstantaneousSeparation()
        parent = {"v": 300}
        child = {"v": 300}
        p_out, c_out = model.apply(parent, child, None)
        assert p_out is parent
        assert c_out is child


# ---------------------------------------------------------------------------
# ParentUpdate
# ---------------------------------------------------------------------------


class TestParentUpdate:
    """ParentUpdate ABC and NoOpParentUpdate."""

    def test_parent_update_is_abstract(self):
        """ParentUpdate cannot be instantiated directly."""
        with pytest.raises(TypeError):
            ParentUpdate()  # type: ignore[abstract]

    def test_no_op_does_not_raise(self):
        """NoOpParentUpdate.apply runs without raising."""
        update = NoOpParentUpdate()
        update.apply(None)  # must not raise


# ---------------------------------------------------------------------------
# Deployable
# ---------------------------------------------------------------------------


class TestDeployable:
    """Deployable attaches a body with a deployment event."""

    def test_basic_creation(self):
        """Deployable can be created with minimal arguments."""
        d = _make_deployable()
        assert d.name == "payload"

    def test_deployment_event_in_events_list(self):
        """deployment_event is included in the events list."""
        ev = _make_deployment_event()
        d = _make_deployable(deployment_event=ev)
        assert ev in d.events

    def test_default_separation_model(self):
        """Default separation model is InstantaneousSeparation."""
        d = _make_deployable()
        assert isinstance(d.separation, InstantaneousSeparation)

    def test_default_parent_update(self):
        """Default parent update is NoOpParentUpdate."""
        d = _make_deployable()
        assert isinstance(d.parent_update, NoOpParentUpdate)

    def test_validate_passes_with_valid_config(self):
        """validate() does not raise for a properly configured deployable."""
        d = _make_deployable()
        d.validate()  # must not raise

    def test_validate_raises_on_missing_body(self):
        """validate() raises ValueError when body is None."""
        d = _make_deployable(body=None)
        with pytest.raises(ValueError, match="body"):
            d.validate()

    def test_validate_raises_on_missing_attachment(self):
        """validate() raises ValueError when attachment is None."""
        d = _make_deployable(attachment=None)
        with pytest.raises(ValueError, match="attachment"):
            d.validate()


# ---------------------------------------------------------------------------
# Stage
# ---------------------------------------------------------------------------


class TestStage:
    """Stage tracks lifecycle and holds separation/ignition events."""

    def test_initial_state_is_attached(self):
        """Stage starts in ATTACHED state."""
        stage = _make_stage()
        assert stage.state == StageState.ATTACHED

    def test_validate_passes_with_valid_config(self):
        """validate() does not raise for a well-configured stage."""
        stage = _make_stage()
        stage.validate()

    def test_validate_raises_on_missing_body(self):
        """validate() raises ValueError when body is None."""
        stage = _make_stage(body=None)
        with pytest.raises(ValueError, match="body"):
            stage.validate()

    def test_validate_raises_on_missing_attachment(self):
        """validate() raises ValueError when attachment is None."""
        stage = _make_stage(attachment=None)
        with pytest.raises(ValueError, match="attachment"):
            stage.validate()

    def test_separation_event_in_events(self):
        """separation_event is included in the events list."""
        sep_ev = StageSeparationEvent("sep", _always_trigger)
        stage = _make_stage(separation_event=sep_ev)
        assert sep_ev in stage.events

    def test_ignition_event_in_events(self):
        """ignition_event is included in the events list."""
        ign_ev = IgnitionEvent("ign", _always_trigger)
        stage = _make_stage(ignition_event=ign_ev)
        assert ign_ev in stage.events

    def test_default_separation_model(self):
        """Default separation model is InstantaneousSeparation."""
        stage = _make_stage()
        assert isinstance(stage.separation, InstantaneousSeparation)

    def test_default_parent_update(self):
        """Default parent update is NoOpParentUpdate."""
        stage = _make_stage()
        assert isinstance(stage.parent_update, NoOpParentUpdate)


# ---------------------------------------------------------------------------
# Mission
# ---------------------------------------------------------------------------


class TestMissionInit:
    """Mission stores name and starts with empty lists."""

    def test_default_name(self):
        """Default mission name is 'Mission'."""
        m = Mission()
        assert m.name == "Mission"

    def test_custom_name(self):
        """Custom name is stored correctly."""
        m = Mission("ASTER_X")
        assert m.name == "ASTER_X"

    def test_stages_starts_empty(self):
        """stages list starts empty."""
        m = Mission()
        assert m.stages == []

    def test_deployables_starts_empty(self):
        """deployables list starts empty."""
        m = Mission()
        assert m.deployables == []


class TestMissionAddStage:
    """Mission.add_stage validates and appends stages."""

    def test_add_valid_stage(self):
        """add_stage appends a valid Stage."""
        m = Mission()
        s = _make_stage()
        m.add_stage(s)
        assert s in m.stages

    def test_add_multiple_stages(self):
        """add_stage appends multiple stages in order."""
        m = Mission()
        s1 = _make_stage(name="stage_1")
        s2 = _make_stage(name="stage_2")
        m.add_stage(s1)
        m.add_stage(s2)
        assert m.stages == [s1, s2]

    def test_add_stage_raises_for_non_stage(self):
        """add_stage raises TypeError when given a non-Stage object."""
        m = Mission()
        with pytest.raises(TypeError):
            m.add_stage("not_a_stage")

    def test_add_stage_raises_for_invalid_stage(self):
        """add_stage raises ValueError when stage.validate() fails."""
        m = Mission()
        bad_stage = _make_stage(body=None)  # body=None will fail validate()
        with pytest.raises(ValueError):
            m.add_stage(bad_stage)


class TestMissionAddDeployable:
    """Mission.add_deployable validates and appends deployables."""

    def test_add_valid_deployable(self):
        """add_deployable appends a valid Deployable."""
        m = Mission()
        d = _make_deployable()
        m.add_deployable(d)
        assert d in m.deployables

    def test_add_deployable_raises_for_non_deployable(self):
        """add_deployable raises TypeError when given a non-Deployable."""
        m = Mission()
        with pytest.raises(TypeError):
            m.add_deployable(42)

    def test_add_deployable_raises_for_invalid_deployable(self):
        """add_deployable raises ValueError when deployable.validate() fails."""
        m = Mission()
        bad = _make_deployable(body=None)
        with pytest.raises(ValueError):
            m.add_deployable(bad)


class TestMissionAttachedItems:
    """Mission.attached_items returns all items in stages-first order."""

    def test_attached_items_combines_stages_and_deployables(self):
        """attached_items returns stages then deployables."""
        m = Mission()
        s = _make_stage()
        d = _make_deployable()
        m.add_stage(s)
        m.add_deployable(d)
        items = m.attached_items()
        assert items == [s, d]

    def test_attached_items_empty_when_nothing_added(self):
        """attached_items returns empty list when no items added."""
        m = Mission()
        assert m.attached_items() == []

    def test_len_counts_all_items(self):
        """len(mission) counts stages + deployables."""
        m = Mission()
        m.add_stage(_make_stage())
        m.add_deployable(_make_deployable())
        assert len(m) == 2


class TestMissionMissionMetadata:
    """Mission exposes mission-wide stage and connection metadata."""

    def test_number_of_stages_matches_added_stages(self):
        """number_of_stages returns the stage count."""
        mission = Mission()
        mission.add_stage(_make_stage(name="stage_1"))
        mission.add_stage(_make_stage(name="stage_2"))
        assert mission.number_of_stages == 2

    def test_connection_map_contains_attachment_data(self):
        """connection_map returns attachment metadata for mission items."""
        mission = Mission()
        stage = _make_stage(name="stage_1")
        mission.add_stage(stage)
        connection = mission.connection_map()["stage_1"]
        assert connection["parent_frame_position"] == [0.0, 0.0, 1.0]
        assert connection["child_frame_position"] == [0.0, 0.0, 0.0]
        assert connection["constraints"] == "rigid"

    def test_set_and_get_flight_inputs_by_name(self):
        """set_flight_inputs/get_flight_inputs store and return per-item inputs."""
        mission = Mission()
        stage = _make_stage(name="stage_1")
        mission.add_stage(stage)
        mission.set_flight_inputs("stage_1", inclination=85, heading=10)
        configured = mission.get_flight_inputs(stage)
        assert configured["inclination"] == 85
        assert configured["heading"] == 10

    def test_set_flight_inputs_raises_for_unknown_item(self):
        """set_flight_inputs raises KeyError when item is unknown."""
        mission = Mission()
        with pytest.raises(KeyError):
            mission.set_flight_inputs("missing_stage", inclination=85)


class TestMissionRootVehicle:
    """Mission.root_vehicle is a distinguished, non-attached-item vehicle."""

    def test_default_root_vehicle_is_none(self):
        """root_vehicle defaults to None."""
        assert Mission().root_vehicle is None

    def test_root_vehicle_via_constructor(self):
        """root_vehicle can be set via the constructor."""
        vehicle = _make_rocket_adapter("root")
        mission = Mission(root_vehicle=vehicle)
        assert mission.root_vehicle is vehicle

    def test_set_root_vehicle(self):
        """set_root_vehicle updates root_vehicle."""
        mission = Mission()
        vehicle = _make_rocket_adapter("root")
        mission.set_root_vehicle(vehicle)
        assert mission.root_vehicle is vehicle

    def test_root_vehicle_excluded_from_attached_items(self):
        """root_vehicle is not part of attached_items()."""
        mission = Mission(root_vehicle=_make_rocket_adapter("root"))
        mission.add_stage(_make_stage(name="stage_1"))
        assert len(mission.attached_items()) == 1

    def test_root_flight_inputs_round_trip(self):
        """set_root_flight_inputs/get_root_flight_inputs store and return inputs."""
        mission = Mission()
        mission.set_root_flight_inputs(inclination=85, heading=10)
        inputs = mission.get_root_flight_inputs()
        assert inputs == {"inclination": 85, "heading": 10}

    def test_get_root_flight_inputs_empty_by_default(self):
        """get_root_flight_inputs returns an empty dict when unconfigured."""
        assert Mission().get_root_flight_inputs() == {}


class TestMissionDescribe:
    """Mission.describe() returns a human-readable summary."""

    def test_describe_without_root_vehicle(self):
        """describe() reports root_vehicle as not set."""
        mission = Mission(name="Demo")
        assert "root_vehicle: not set" in mission.describe()
        assert "Demo" in mission.describe()

    def test_describe_with_root_vehicle(self):
        """describe() reports the root vehicle's type."""
        mission = Mission(root_vehicle=_make_rocket_adapter("root"))
        assert "RocketAdapter" in mission.describe()

    def test_describe_lists_stages_and_deployables(self):
        """describe() lists each stage's name/state and each deployable's name."""
        mission = Mission()
        mission.add_stage(_make_stage(name="stage_1"))
        mission.add_deployable(_make_deployable(name="payload"))
        description = mission.describe()
        assert "stage_1" in description
        assert "payload" in description
        assert "ATTACHED" in description


class TestMissionValidate:
    """Mission.validate() aggregates per-item validation plus mission invariants."""

    def test_validate_passes_for_well_formed_mission(self):
        """validate() does not raise for a valid mission."""
        mission = Mission(root_vehicle=_make_rocket_adapter("root"))
        mission.add_stage(_make_stage(name="stage_1"))
        mission.validate()  # must not raise

    def test_validate_raises_on_duplicate_names(self):
        """validate() raises ValueError when two items share a name."""
        mission = Mission()
        mission.add_stage(_make_stage(name="dup"))
        mission.add_deployable(_make_deployable(name="dup"))
        with pytest.raises(ValueError, match="Duplicate"):
            mission.validate()

    def test_validate_aggregates_item_errors(self):
        """validate() collects every failing item's error into one ValueError."""
        mission = Mission()
        stage = _make_stage(name="stage_1")
        deployable = _make_deployable(name="payload")
        mission.add_stage(stage)
        mission.add_deployable(deployable)
        # Mutate after adding to bypass add_stage/add_deployable's own checks.
        stage.body = None
        deployable.body = None

        with pytest.raises(ValueError) as exc_info:
            mission.validate()
        assert "stage_1" in str(exc_info.value)
        assert "payload" in str(exc_info.value)

    def test_validate_warns_when_root_vehicle_unset(self):
        """validate() warns (does not raise) when root_vehicle is unset."""
        mission = Mission()
        mission.add_stage(_make_stage(name="stage_1"))
        with pytest.warns(UserWarning, match="root_vehicle"):
            mission.validate()

    def test_validate_raises_when_root_vehicle_required(self):
        """validate(require_root_vehicle=True) raises when root_vehicle is unset."""
        mission = Mission()
        mission.add_stage(_make_stage(name="stage_1"))
        with pytest.raises(ValueError, match="root_vehicle"):
            mission.validate(require_root_vehicle=True)


class TestMissionExecutor:
    """MissionExecutor runs mission items without requiring manual Flight setup."""

    class FakeFlight:
        """Simple stand-in for rocketpy.simulation.Flight.

        Mimics just enough of Flight's initial_solution-chaining contract
        (see Flight.__init_flight_state) for MissionExecutor's sequential
        chaining logic to be exercised: passing a previous FakeFlight as
        initial_solution resolves to that flight's own final state.
        """

        def __init__(self, rocket, environment, rail_length, **kwargs):
            self.rocket = rocket
            self.environment = environment
            self.rail_length = rail_length
            self.kwargs = kwargs

            initial_solution = kwargs.get("initial_solution")
            if hasattr(initial_solution, "initial_solution"):
                initial_solution = initial_solution.initial_solution
            self.initial_solution = list(initial_solution) if initial_solution else [0.0]
            self.t_initial = self.initial_solution[0]
            self.apogee = 100.0
            self.impact_velocity = -5.0

    def test_execute_runs_stage_and_deployable(self):
        """execute runs all mission attached items in mission order."""
        mission = Mission()
        stage = _make_stage(name="stage_1", body=_make_rocket_adapter("stage_rocket"))
        deployable = _make_deployable(
            name="payload", body=_make_rocket_adapter("payload_rocket")
        )
        mission.add_stage(stage)
        mission.add_deployable(deployable)
        mission.set_flight_inputs("stage_1", heading=15)
        mission.set_flight_inputs("payload", heading=45)

        executor = MissionExecutor(
            mission=mission,
            environment=object(),
            rail_length=5.0,
            default_flight_inputs={"inclination": 80},
            flight_class=self.FakeFlight,
        )

        results = executor.execute()

        assert [result.item_name for result in results] == ["stage_1", "payload"]
        assert results[0].flight.kwargs["inclination"] == 80
        assert results[0].flight.kwargs["heading"] == 15
        assert results[1].flight.kwargs["heading"] == 45
        assert results[1].flight.kwargs["initial_solution"] is results[0].flight
        assert stage.state == StageState.SPENT

    def test_execute_raises_for_non_rocket_body(self):
        """execute raises TypeError when body is not RocketAdapter-backed."""
        mission = Mission()
        mission.add_stage(_make_stage(name="stage_1", body=_UnsupportedBody()))

        executor = MissionExecutor(
            mission=mission,
            environment=object(),
            rail_length=5.0,
            flight_class=self.FakeFlight,
        )

        with pytest.raises(TypeError, match="FlightBody"):
            executor.execute()

    def test_execute_accepts_protocol_compatible_rocket_body(self):
        """execute accepts bodies satisfying FlightCompatibleRocket protocol."""
        mission = Mission()
        mission.add_stage(_make_stage(name="stage_1", body=FakeRocket("raw_stage")))
        executor = MissionExecutor(
            mission=mission,
            environment=object(),
            rail_length=5.0,
            flight_class=self.FakeFlight,
        )
        results = executor.execute()
        assert results[0].flight.rocket.name == "raw_stage"

    def test_execute_raises_for_flight_body(self):
        """execute raises a clear TypeError for a bare FlightBody, since it
        cannot drive a real Flight (no total_mass()/add_motor())."""
        mission = Mission()
        body = _make_body("flight_body")
        mission.add_stage(_make_stage(name="stage_1", body=body))
        executor = MissionExecutor(
            mission=mission,
            environment=object(),
            rail_length=5.0,
            flight_class=self.FakeFlight,
        )
        with pytest.raises(TypeError, match="FlightBody"):
            executor.execute()


class TestMissionExecutorRun:
    """MissionExecutor.run()/dry_run() build on top of execute()'s logic."""

    FakeFlight = TestMissionExecutor.FakeFlight

    def test_run_without_root_vehicle(self):
        """run() returns a MissionResult with root_flight None when
        mission.root_vehicle is unset."""
        mission = Mission()
        mission.add_stage(
            _make_stage(name="stage_1", body=_make_rocket_adapter("stage_rocket"))
        )
        mission.add_deployable(
            _make_deployable(name="payload", body=_make_rocket_adapter("payload_rocket"))
        )
        executor = MissionExecutor(
            mission=mission,
            environment=object(),
            rail_length=5.0,
            flight_class=self.FakeFlight,
        )

        result = executor.run()

        assert result.root_flight is None
        assert list(result.branch_flights) == ["stage_1", "payload"]
        assert [branch.name for branch in result.branch_results] == [
            "stage_1",
            "payload",
        ]

    def test_run_with_root_vehicle_chains_from_root(self):
        """run() builds a root flight first and chains the first item from it."""
        mission = Mission(root_vehicle=_make_rocket_adapter("root_rocket"))
        mission.add_stage(
            _make_stage(name="stage_1", body=_make_rocket_adapter("stage_rocket"))
        )
        executor = MissionExecutor(
            mission=mission,
            environment=object(),
            rail_length=5.0,
            flight_class=self.FakeFlight,
        )

        result = executor.run()

        assert result.root_flight is not None
        assert result.branch_results[0].flight.kwargs["initial_solution"] is (
            result.root_flight
        )

    def test_run_raises_for_flight_body_item(self):
        """run() raises the BodyResolver error at the executor boundary for a
        bare FlightBody attached item."""
        mission = Mission()
        mission.add_stage(_make_stage(name="stage_1", body=_make_body("flight_body")))
        executor = MissionExecutor(
            mission=mission,
            environment=object(),
            rail_length=5.0,
            flight_class=self.FakeFlight,
        )
        with pytest.raises(TypeError, match="FlightBody"):
            executor.run()

    def test_run_raises_for_flight_body_root_vehicle(self):
        """run() raises the same clear error for a FlightBody root_vehicle."""
        mission = Mission(root_vehicle=_make_body("flight_body_root"))
        executor = MissionExecutor(
            mission=mission,
            environment=object(),
            rail_length=5.0,
            flight_class=self.FakeFlight,
        )
        with pytest.raises(TypeError, match="FlightBody"):
            executor.run()

    def test_run_marks_stage_spent(self):
        """run() transitions Stage.state to SPENT once its branch is built."""
        mission = Mission()
        stage = _make_stage(name="stage_1", body=_make_rocket_adapter("stage_rocket"))
        mission.add_stage(stage)
        executor = MissionExecutor(
            mission=mission,
            environment=object(),
            rail_length=5.0,
            flight_class=self.FakeFlight,
        )

        executor.run()

        assert stage.state == StageState.SPENT

    def test_dry_run_never_constructs_a_flight(self):
        """dry_run() resolves bodies/configs without invoking flight_class."""

        def _failing_flight_class(*args, **kwargs):
            raise AssertionError("dry_run() must not construct a Flight.")

        mission = Mission(root_vehicle=_make_rocket_adapter("root_rocket"))
        mission.add_stage(
            _make_stage(name="stage_1", body=_make_rocket_adapter("stage_rocket"))
        )
        executor = MissionExecutor(
            mission=mission,
            environment=object(),
            rail_length=5.0,
            default_flight_inputs={"inclination": 80},
            flight_class=_failing_flight_class,
        )

        configs = executor.dry_run()

        assert [config.rail_length for config in configs] == [5.0, 5.0]
        assert all(isinstance(config, FlightConfig) for config in configs)
        assert all(config.inclination == 80 for config in configs)

    def test_dry_run_raises_for_flight_body(self):
        """dry_run() still surfaces the FlightBody guard, cheaply."""
        mission = Mission()
        mission.add_stage(_make_stage(name="stage_1", body=_make_body("flight_body")))
        executor = MissionExecutor(
            mission=mission,
            environment=object(),
            rail_length=5.0,
            flight_class=self.FakeFlight,
        )
        with pytest.raises(TypeError, match="FlightBody"):
            executor.dry_run()
