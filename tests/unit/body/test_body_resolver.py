"""Unit tests for rocketpy.body.BodyResolver."""

import pytest

from rocketpy.body import BodyResolver, FlightBody, RocketAdapter


def _make_flight_body(name="flight_body"):
    return FlightBody(
        name=name,
        geometry=0.05,
        mass_model=lambda t: 10.0,
        inertia_model=lambda t: (1.0, 1.0, 0.05, 0.0, 0.0, 0.0),
        center_of_mass_model=lambda t: 0.5,
    )


class _FakeRocket:
    """Rocket-like object exposing as_body(), as real Rocket does."""

    def __init__(self, name="fake_rocket"):
        self.name = name

    def as_body(self):
        return RocketAdapter(self)

    def add_motor(self, motor, position):
        """No-op helper to satisfy FlightCompatibleRocket."""

    def total_mass(self, _t):
        return 1.0

    def center_of_mass(self, _t):
        return 0.0


class _ProtocolOnlyRocket:
    """Satisfies FlightCompatibleRocket but has no as_body()."""

    def add_motor(self, motor, position):
        """No-op helper to satisfy FlightCompatibleRocket."""

    def total_mass(self, _t):
        return 1.0

    def center_of_mass(self, _t):
        return 0.0


class _UnsupportedBody:
    """Satisfies neither BodyLike nor FlightCompatibleRocket."""


class TestBodyResolverToBody:
    """BodyResolver.to_body resolves supported sources to a BodyLike."""

    def test_resolves_rocket_via_as_body(self):
        """A Rocket-like object with as_body() is resolved via that method."""
        rocket = _FakeRocket()
        body = BodyResolver.to_body(rocket)
        assert isinstance(body, RocketAdapter)
        assert body.rocket is rocket

    def test_passes_through_rocket_adapter(self):
        """An existing RocketAdapter is returned unchanged."""
        adapter = RocketAdapter(_FakeRocket())
        assert BodyResolver.to_body(adapter) is adapter

    def test_passes_through_flight_body(self):
        """A bare FlightBody is a legitimate BodyLike and is returned unchanged."""
        flight_body = _make_flight_body()
        assert BodyResolver.to_body(flight_body) is flight_body

    def test_wraps_protocol_only_rocket(self):
        """An object satisfying FlightCompatibleRocket but lacking as_body()
        is wrapped in a RocketAdapter."""
        rocket = _ProtocolOnlyRocket()
        body = BodyResolver.to_body(rocket)
        assert isinstance(body, RocketAdapter)
        assert body.rocket is rocket

    def test_raises_for_unsupported_type(self):
        """An unsupported type raises TypeError."""
        with pytest.raises(TypeError, match="_UnsupportedBody"):
            BodyResolver.to_body(_UnsupportedBody())


class TestBodyResolverToFlightRocket:
    """BodyResolver.to_flight_rocket gates what can drive a real Flight."""

    def test_unwraps_rocket_adapter(self):
        """A RocketAdapter unwraps to its underlying rocket."""
        rocket = _FakeRocket()
        adapter = RocketAdapter(rocket)
        assert BodyResolver.to_flight_rocket(adapter) is rocket

    def test_passes_through_protocol_compatible_rocket(self):
        """A bare object satisfying FlightCompatibleRocket passes through."""
        rocket = _ProtocolOnlyRocket()
        assert BodyResolver.to_flight_rocket(rocket) is rocket

    def test_raises_clear_error_for_flight_body(self):
        """A bare FlightBody raises a clear, actionable TypeError."""
        flight_body = _make_flight_body("payload")
        with pytest.raises(TypeError, match="FlightBody"):
            BodyResolver.to_flight_rocket(flight_body)

    def test_raises_for_unsupported_type(self):
        """An unsupported type raises TypeError."""
        with pytest.raises(TypeError):
            BodyResolver.to_flight_rocket(_UnsupportedBody())
