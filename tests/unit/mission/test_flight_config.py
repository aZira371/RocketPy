"""Unit tests for rocketpy.mission.FlightConfig."""

from rocketpy.mission import FlightConfig


class TestFlightConfigDefaults:
    """FlightConfig field defaults match Flight's own constructor defaults."""

    def test_defaults(self):
        """Only rail_length is required; other fields carry Flight-matching
        defaults."""
        config = FlightConfig(rail_length=5.0)
        assert config.rail_length == 5.0
        assert config.inclination == 80.0
        assert config.heading == 90.0
        assert config.initial_solution is None
        assert config.max_time == 600
        assert config.terminate_on_apogee is False
        assert config.time_overshoot is True
        assert config.extra_kwargs == {}


class TestFlightConfigToFlightKwargs:
    """to_flight_kwargs() builds the keyword mapping passed to Flight."""

    def test_shape(self):
        """to_flight_kwargs() returns every field except rail_length."""
        config = FlightConfig(rail_length=5.0, inclination=85.0)
        kwargs = config.to_flight_kwargs()
        assert "rail_length" not in kwargs
        assert kwargs["inclination"] == 85.0
        assert kwargs["heading"] == 90.0
        assert kwargs["max_time"] == 600
        assert kwargs["terminate_on_apogee"] is False
        assert kwargs["time_overshoot"] is True

    def test_extra_kwargs_are_merged(self):
        """extra_kwargs entries are merged into the returned mapping."""
        config = FlightConfig(rail_length=5.0, extra_kwargs={"max_time_step": 0.01})
        kwargs = config.to_flight_kwargs()
        assert kwargs["max_time_step"] == 0.01


class TestFlightConfigForBranch:
    """for_branch() produces a new, independently overridden FlightConfig."""

    def test_returns_new_instance(self):
        """for_branch() does not mutate the original config."""
        base = FlightConfig(rail_length=5.0, inclination=80.0)
        branch = base.for_branch("stage_1", {"inclination": 85.0})
        assert base.inclination == 80.0
        assert branch.inclination == 85.0
        assert branch is not base

    def test_known_field_override_precedence(self):
        """Per-branch overrides win over the base config's values."""
        base = FlightConfig(rail_length=5.0, heading=90.0)
        branch = base.for_branch("stage_1", {"heading": 15.0})
        assert branch.heading == 15.0

    def test_unrecognized_keys_land_in_extra_kwargs(self):
        """Unknown override keys are routed into extra_kwargs."""
        base = FlightConfig(rail_length=5.0)
        branch = base.for_branch("stage_1", {"max_time_step": 0.01})
        assert branch.extra_kwargs["max_time_step"] == 0.01

    def test_no_overrides_inherits_base_values(self):
        """Calling for_branch() with no overrides copies the base config."""
        base = FlightConfig(rail_length=5.0, inclination=82.0)
        branch = base.for_branch("stage_1")
        assert branch.inclination == 82.0
        assert branch.rail_length == 5.0
