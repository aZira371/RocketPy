"""Unit tests for rocketpy.simulation.FlightBranch."""

import pytest

from rocketpy.simulation import FlightBranch

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class _FakeBody:
    name = "fake_body"


# ---------------------------------------------------------------------------
# FlightBranch initialization
# ---------------------------------------------------------------------------


class TestFlightBranchInit:
    """FlightBranch stores its constructor arguments correctly."""

    def test_body_stored(self):
        """body attribute is stored."""
        body = _FakeBody()
        branch = FlightBranch(body=body)
        assert branch.body is body

    def test_default_start_time_is_zero(self):
        """start_time defaults to 0.0 when not provided."""
        branch = FlightBranch(body=None)
        assert branch.start_time == pytest.approx(0.0)

    def test_custom_start_time(self):
        """start_time is stored from the constructor argument."""
        branch = FlightBranch(body=None, start_time=5.5)
        assert branch.start_time == pytest.approx(5.5)

    def test_parent_defaults_to_none(self):
        """parent is None when not provided."""
        branch = FlightBranch(body=None)
        assert branch.parent is None

    def test_children_starts_empty(self):
        """children list starts empty."""
        branch = FlightBranch(body=None)
        assert branch.children == []

    def test_events_starts_empty(self):
        """events list starts empty when not provided."""
        branch = FlightBranch(body=None)
        assert branch.events == []

    def test_events_stored(self):
        """events list is stored from constructor argument."""
        ev = object()
        branch = FlightBranch(body=None, events=[ev])
        assert ev in branch.events


# ---------------------------------------------------------------------------
# Tree structure
# ---------------------------------------------------------------------------


class TestFlightBranchTree:
    """FlightBranch tracks parent/child relationships."""

    def test_is_root_for_no_parent(self):
        """is_root() returns True when parent is None."""
        root = FlightBranch(body=None)
        assert root.is_root() is True

    def test_is_not_root_when_parent_set(self):
        """is_root() returns False when a parent is set."""
        root = FlightBranch(body=None)
        child = FlightBranch(body=None, parent=root)
        assert child.is_root() is False

    def test_parent_registers_child(self):
        """Creating a child with a parent registers it in parent.children."""
        root = FlightBranch(body=None)
        child = FlightBranch(body=None, parent=root)
        assert child in root.children

    def test_spawn_child_creates_child(self):
        """spawn_child() creates and registers a child branch."""
        root = FlightBranch(body=_FakeBody(), start_time=0.0)
        child = root.spawn_child(body=_FakeBody(), start_time=10.0)
        assert child.parent is root
        assert child in root.children

    def test_spawn_child_inherits_start_state_if_not_given(self):
        """spawn_child inherits parent start_state when not provided."""
        state = {"x": 0}
        root = FlightBranch(body=None, start_state=state)
        child = root.spawn_child(body=None)
        assert child.start_state is state

    def test_spawn_child_uses_provided_start_time(self):
        """spawn_child uses the provided start_time."""
        root = FlightBranch(body=None, start_time=0.0)
        child = root.spawn_child(body=None, start_time=42.0)
        assert child.start_time == pytest.approx(42.0)

    def test_multiple_children(self):
        """A single parent can have multiple child branches."""
        root = FlightBranch(body=None)
        c1 = root.spawn_child(body=_FakeBody())
        c2 = root.spawn_child(body=_FakeBody())
        assert len(root.children) == 2
        assert c1 in root.children
        assert c2 in root.children


# ---------------------------------------------------------------------------
# Repr
# ---------------------------------------------------------------------------


class TestFlightBranchRepr:
    """FlightBranch has a useful __repr__."""

    def test_repr_contains_body_name(self):
        """__repr__ includes the body name."""
        body = _FakeBody()
        branch = FlightBranch(body=body)
        assert "fake_body" in repr(branch)
