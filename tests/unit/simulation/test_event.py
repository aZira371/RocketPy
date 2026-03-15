"""Unit tests for the Event class.

The Event class records discrete occurrences that happen during a flight
simulation (e.g. parachute deployments, stage separations, deployable
releases). These tests cover construction, attribute access, backward-
compatible index access, string representations, and equality checking.
"""

import pytest

from rocketpy import Event
from rocketpy.simulation.event import Event as EventDirect


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def dummy_parachute():
    """A lightweight stand-in for a Parachute instance."""

    class _FakeParachute:
        name = "drogue"
        lag = 1.5
        trigger = "apogee"

    return _FakeParachute()


@pytest.fixture
def parachute_event(dummy_parachute):
    """An Event that mimics a parachute deployment."""
    return Event(
        time=45.0,
        trigger=dummy_parachute.trigger,
        event_type="parachute",
        action=dummy_parachute,
    )


# ---------------------------------------------------------------------------
# Construction and attribute access
# ---------------------------------------------------------------------------


def test_event_init_stores_time():
    """Test that Event stores the time parameter correctly in the time attribute."""
    ev = Event(time=10.5, trigger="apogee")
    assert ev.time == 10.5


def test_event_init_stores_trigger():
    """Test that Event stores string trigger values correctly in the trigger attribute."""
    ev = Event(time=5.0, trigger="apogee")
    assert ev.trigger == "apogee"


def test_event_init_stores_trigger_callable():
    """Test that Event stores a callable trigger function correctly in the trigger attribute."""

    def func(p, h, y, s):
        return h < 500

    ev = Event(time=3.0, trigger=func)
    assert ev.trigger is func


def test_event_init_stores_float_trigger():
    """Test that Event stores float trigger values (altitude thresholds) correctly."""
    ev = Event(time=3.0, trigger=800.0)
    assert ev.trigger == 800.0


def test_event_default_event_type():
    """Test that event_type defaults to 'parachute' when not specified."""
    ev = Event(time=1.0, trigger="apogee")
    assert ev.event_type == "parachute"


def test_event_custom_event_type():
    """Test that a custom event_type is stored correctly when supplied."""
    ev = Event(time=1.0, trigger=None, event_type="stage_separation")
    assert ev.event_type == "stage_separation"


def test_event_deployable_event_type():
    """Test that event_type 'deployable' is accepted and stored correctly."""
    ev = Event(time=2.0, trigger=None, event_type="deployable")
    assert ev.event_type == "deployable"


def test_event_default_action_is_none():
    """action defaults to None when not provided."""
    ev = Event(time=1.0, trigger="apogee")
    assert ev.action is None


def test_event_action_stored(dummy_parachute, parachute_event):
    """action attribute holds the associated object."""
    assert parachute_event.action is dummy_parachute


# ---------------------------------------------------------------------------
# Backward-compatible index access
# ---------------------------------------------------------------------------


def test_event_index_zero_returns_time(parachute_event):
    """event[0] returns the time (backward-compatible with [time, parachute])."""
    assert parachute_event[0] == parachute_event.time


def test_event_index_one_returns_action(parachute_event, dummy_parachute):
    """event[1] returns the action (backward-compatible with [time, parachute])."""
    assert parachute_event[1] is dummy_parachute


def test_event_index_out_of_range_raises_index_error(parachute_event):
    """Accessing index >= 2 raises IndexError."""
    with pytest.raises(IndexError):
        _ = parachute_event[2]


def test_event_negative_index_raises_index_error(parachute_event):
    """Negative indices raise IndexError."""
    with pytest.raises(IndexError):
        _ = parachute_event[-1]


# ---------------------------------------------------------------------------
# String representations
# ---------------------------------------------------------------------------


def test_event_repr_is_string(parachute_event):
    """repr() returns a non-empty string."""
    r = repr(parachute_event)
    assert isinstance(r, str)
    assert len(r) > 0


def test_event_repr_contains_time(parachute_event):
    """repr() includes the event time."""
    assert "45.000" in repr(parachute_event)


def test_event_repr_contains_type(parachute_event):
    """Test that repr() includes the event_type."""
    assert "parachute" in repr(parachute_event)


def test_event_str_is_string(parachute_event):
    """str() returns a non-empty string."""
    s = str(parachute_event)
    assert isinstance(s, str)
    assert len(s) > 0


def test_event_str_contains_type(parachute_event):
    """str() mentions the event type."""
    assert "parachute" in str(parachute_event)


def test_event_str_contains_time(parachute_event):
    """str() mentions the trigger time."""
    assert "45.000" in str(parachute_event)


# ---------------------------------------------------------------------------
# Equality
# ---------------------------------------------------------------------------


def test_event_equality_same_attributes(dummy_parachute):
    """Two Event instances with the same attributes are equal."""
    ev1 = Event(time=5.0, trigger="apogee", event_type="parachute", action=dummy_parachute)
    ev2 = Event(time=5.0, trigger="apogee", event_type="parachute", action=dummy_parachute)
    assert ev1 == ev2


def test_event_inequality_different_time(dummy_parachute):
    """Events with different times are not equal."""
    ev1 = Event(time=5.0, trigger="apogee", action=dummy_parachute)
    ev2 = Event(time=6.0, trigger="apogee", action=dummy_parachute)
    assert ev1 != ev2


def test_event_inequality_different_type():
    """Test that events with different event_type values are not equal."""
    ev1 = Event(time=5.0, trigger=None, event_type="parachute")
    ev2 = Event(time=5.0, trigger=None, event_type="stage_separation")
    assert ev1 != ev2


def test_event_not_equal_to_non_event(parachute_event):
    """Comparing an Event with a non-Event returns NotImplemented / False."""
    assert parachute_event != [45.0, None]


# ---------------------------------------------------------------------------
# Module-level import
# ---------------------------------------------------------------------------


def test_event_importable_from_rocketpy():
    """Event can be imported directly from the top-level rocketpy package."""
    assert Event is EventDirect
