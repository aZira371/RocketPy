"""Unit tests for rocketpy.body (BodyLike, FlightBody, RocketAdapter)."""

import pytest

from rocketpy.body import BodyLike, FlightBody, RocketAdapter


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------


def _const_mass_model(value=10.0):
    """Return a constant mass callable."""
    return lambda t: value


def _const_inertia_model(diag=1.0):
    """Return a constant inertia callable that returns a diagonal tuple."""
    return lambda t: (diag, diag, diag, 0.0, 0.0, 0.0)


def _const_com_model(pos=0.5):
    """Return a constant center-of-mass position callable."""
    return lambda t: pos


def _make_flight_body(**kwargs):
    """Construct a minimal FlightBody for testing."""
    defaults = {
        "name": "test_body",
        "geometry": 0.05,
        "mass_model": _const_mass_model(),
        "inertia_model": _const_inertia_model(),
        "center_of_mass_model": _const_com_model(),
    }
    defaults.update(kwargs)
    return FlightBody(**defaults)


# ---------------------------------------------------------------------------
# BodyLike Protocol
# ---------------------------------------------------------------------------


class TestBodyLikeProtocol:
    """BodyLike is a structural protocol."""

    def test_cannot_instantiate_body_like(self):
        """BodyLike must raise TypeError when instantiated directly."""
        # Arrange / Act / Assert
        with pytest.raises(TypeError):
            BodyLike()  # type: ignore[abstract]

    def test_structural_conformance_without_inheritance(self):
        """Objects can satisfy BodyLike without inheriting from it."""
        # Arrange
        class StructuralBody:
            name = "structural"

            def mass(self, t):
                return 1.0

            def inertia_tensor(self, t):
                return (1.0, 1.0, 1.0, 0.0, 0.0, 0.0)

            def center_of_mass(self, t):
                return 0.0

            def aerodynamic_model(self):
                return None

            def propulsion_model(self):
                return None

            def recovery_systems(self):
                return []

            def sensors(self):
                return []

            def controllers(self):
                return []

            def coordinate_system_orientation(self):
                return "tail_to_nose"

            def to_branch_ready_copy(self):
                return self

        # Act
        instance = StructuralBody()

        # Assert
        assert isinstance(instance, BodyLike)


# ---------------------------------------------------------------------------
# FlightBody
# ---------------------------------------------------------------------------


class TestFlightBodyInit:
    """FlightBody initializes attributes correctly."""

    def test_name_stored(self):
        """name attribute is stored and returned via .name property."""
        # Arrange & Act
        body = _make_flight_body(name="rocket_stage_1")
        # Assert
        assert body.name == "rocket_stage_1"

    def test_default_coordinate_system_orientation(self):
        """Default orientation is tail_to_nose."""
        body = _make_flight_body()
        assert body.coordinate_system_orientation() == "tail_to_nose"

    def test_custom_coordinate_system_orientation(self):
        """Custom orientation is stored correctly."""
        body = _make_flight_body(coordinate_system_orientation="nose_to_tail")
        assert body.coordinate_system_orientation() == "nose_to_tail"

    def test_recovery_systems_defaults_to_empty(self):
        """recovery_systems defaults to an empty list."""
        body = _make_flight_body()
        assert body.recovery_systems() == []

    def test_sensors_defaults_to_empty(self):
        """sensors defaults to an empty list."""
        body = _make_flight_body()
        assert body.sensors() == []

    def test_controllers_defaults_to_empty(self):
        """controllers defaults to an empty list."""
        body = _make_flight_body()
        assert body.controllers() == []


class TestFlightBodyInterface:
    """FlightBody satisfies the BodyLike interface contracts."""

    def test_mass_returns_float(self):
        """mass(t) delegates to mass_model and returns a float."""
        body = _make_flight_body(mass_model=_const_mass_model(15.5))
        assert body.mass(0.0) == pytest.approx(15.5)

    def test_inertia_tensor_delegates_to_model(self):
        """inertia_tensor(t) returns the value from inertia_model."""
        body = _make_flight_body(inertia_model=_const_inertia_model(2.0))
        result = body.inertia_tensor(0.0)
        assert result[0] == pytest.approx(2.0)

    def test_center_of_mass_delegates_to_model(self):
        """center_of_mass(t) returns value from center_of_mass_model."""
        body = _make_flight_body(center_of_mass_model=_const_com_model(1.2))
        assert body.center_of_mass(0.0) == pytest.approx(1.2)

    def test_aerodynamic_model_returns_stored_model(self):
        """aerodynamic_model() returns the aero_model passed at construction."""
        aero = object()
        body = _make_flight_body(aero_model=aero)
        assert body.aerodynamic_model() is aero

    def test_propulsion_model_returns_stored_model(self):
        """propulsion_model() returns the propulsion passed at construction."""
        prop = object()
        body = _make_flight_body(propulsion=prop)
        assert body.propulsion_model() is prop


class TestFlightBodyMutators:
    """FlightBody mutating helpers work correctly."""

    def test_add_recovery_system_appends(self):
        """add_recovery_system appends to internal list."""
        body = _make_flight_body()
        chute = object()
        body.add_recovery_system(chute)
        assert chute in body.recovery_systems()

    def test_add_sensor_appends(self):
        """add_sensor appends to internal list."""
        body = _make_flight_body()
        sensor = object()
        body.add_sensor(sensor)
        assert sensor in body.sensors()

    def test_add_controller_appends(self):
        """add_controller appends to internal list."""
        body = _make_flight_body()
        ctrl = object()
        body.add_controller(ctrl)
        assert ctrl in body.controllers()


class TestFlightBodyCopy:
    """to_branch_ready_copy produces an independent deep copy."""

    def test_copy_is_different_object(self):
        """The copy is not the same object."""
        body = _make_flight_body()
        copy = body.to_branch_ready_copy()
        assert copy is not body

    def test_copy_has_same_name(self):
        """The copy preserves the name."""
        body = _make_flight_body(name="original")
        copy = body.to_branch_ready_copy()
        assert copy.name == "original"

    def test_copy_is_independent(self):
        """Mutating the copy does not affect the original."""
        body = _make_flight_body()
        copy = body.to_branch_ready_copy()
        copy.add_sensor(object())
        assert len(body.sensors()) == 0


# ---------------------------------------------------------------------------
# RocketAdapter
# ---------------------------------------------------------------------------


class _FakeRocket:
    """Minimal fake rocket for testing RocketAdapter."""

    coordinate_system_orientation = "tail_to_nose"
    parachutes = ["parachute_a"]
    _controllers = []

    def total_mass(self, t):
        return 20.0

    def I_11(self, t):
        return 1.0

    def I_22(self, t):
        return 1.0

    def I_33(self, t):
        return 0.05

    def I_12(self, t):
        return 0.0

    def I_13(self, t):
        return 0.0

    def I_23(self, t):
        return 0.0

    def center_of_mass(self, t):
        return 0.8

    @property
    def aerodynamic_surfaces(self):
        return ["fin_set"]

    @property
    def motor(self):
        return "solid_motor"

    @property
    def sensors(self):
        return []


class TestRocketAdapter:
    """RocketAdapter wraps a rocket and implements BodyLike."""

    def test_is_body_like(self):
        """RocketAdapter is an instance of BodyLike."""
        adapter = RocketAdapter(_FakeRocket())
        assert isinstance(adapter, BodyLike)

    def test_name_unnamed(self):
        """name returns '<unnamed>' when the rocket has no name attribute."""
        adapter = RocketAdapter(_FakeRocket())
        assert adapter.name == "<unnamed>"

    def test_mass_delegates(self):
        """mass(t) delegates to rocket.total_mass(t)."""
        adapter = RocketAdapter(_FakeRocket())
        assert adapter.mass(0.0) == pytest.approx(20.0)

    def test_center_of_mass_delegates(self):
        """center_of_mass(t) delegates to rocket.center_of_mass(t)."""
        adapter = RocketAdapter(_FakeRocket())
        assert adapter.center_of_mass(0.0) == pytest.approx(0.8)

    def test_aerodynamic_model_returns_surfaces(self):
        """aerodynamic_model() returns rocket.aerodynamic_surfaces."""
        adapter = RocketAdapter(_FakeRocket())
        assert adapter.aerodynamic_model() == ["fin_set"]

    def test_propulsion_model_returns_motor(self):
        """propulsion_model() returns rocket.motor."""
        adapter = RocketAdapter(_FakeRocket())
        assert adapter.propulsion_model() == "solid_motor"

    def test_recovery_systems_returns_parachutes(self):
        """recovery_systems() returns rocket.parachutes."""
        adapter = RocketAdapter(_FakeRocket())
        assert adapter.recovery_systems() == ["parachute_a"]

    def test_coordinate_system_orientation_delegates(self):
        """coordinate_system_orientation() delegates to the rocket."""
        adapter = RocketAdapter(_FakeRocket())
        assert adapter.coordinate_system_orientation() == "tail_to_nose"

    def test_to_branch_ready_copy_is_deep(self):
        """to_branch_ready_copy produces a deep copy."""
        adapter = RocketAdapter(_FakeRocket())
        copy = adapter.to_branch_ready_copy()
        assert copy is not adapter
        assert copy.rocket is not adapter.rocket
