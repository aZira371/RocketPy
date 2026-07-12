"""Unit tests for rocketpy.mission.MissionResult and BranchResult."""

import pytest

from rocketpy.mission import BranchResult, MissionResult


class _FakeFlight:
    def __init__(self, apogee=100.0, impact_velocity=-5.0):
        self.apogee = apogee
        self.impact_velocity = impact_velocity


def _make_branch_result(name, flight=None):
    flight = flight or _FakeFlight()
    return BranchResult(
        name=name, flight=flight, item=object(), event_time=0.0, initial_solution=[]
    )


class TestMissionResultAllFlights:
    """all_flights() orders root_flight (if any) before branch flights."""

    def test_includes_root_flight_first(self):
        """root_flight comes before branch flights when set."""
        root_flight = _FakeFlight()
        branch = _make_branch_result("stage_1")
        result = MissionResult(
            root_flight=root_flight,
            branch_flights={"stage_1": branch.flight},
            branch_results=[branch],
        )
        assert result.all_flights() == [root_flight, branch.flight]

    def test_excludes_root_flight_when_none(self):
        """all_flights() omits root_flight when it is None."""
        branch = _make_branch_result("stage_1")
        result = MissionResult(
            root_flight=None,
            branch_flights={"stage_1": branch.flight},
            branch_results=[branch],
        )
        assert result.all_flights() == [branch.flight]


class TestMissionResultGetFlight:
    """get_flight() looks up flights by name, including 'root'."""

    def test_get_flight_by_name(self):
        """get_flight(name) returns the matching branch flight."""
        branch = _make_branch_result("stage_1")
        result = MissionResult(
            root_flight=None,
            branch_flights={"stage_1": branch.flight},
            branch_results=[branch],
        )
        assert result.get_flight("stage_1") is branch.flight

    def test_get_flight_root(self):
        """get_flight('root') returns root_flight when set."""
        root_flight = _FakeFlight()
        result = MissionResult(
            root_flight=root_flight, branch_flights={}, branch_results=[]
        )
        assert result.get_flight("root") is root_flight

    def test_get_flight_root_raises_when_unset(self):
        """get_flight('root') raises KeyError when root_flight is None."""
        result = MissionResult(root_flight=None, branch_flights={}, branch_results=[])
        with pytest.raises(KeyError):
            result.get_flight("root")

    def test_get_flight_raises_for_unknown_name(self):
        """get_flight(name) raises KeyError for an unknown branch name."""
        result = MissionResult(root_flight=None, branch_flights={}, branch_results=[])
        with pytest.raises(KeyError):
            result.get_flight("unknown")


class TestMissionResultGetBranchResult:
    """get_branch_result() looks up BranchResult records by name."""

    def test_returns_matching_branch(self):
        """get_branch_result(name) returns the matching BranchResult."""
        branch = _make_branch_result("stage_1")
        result = MissionResult(
            root_flight=None,
            branch_flights={"stage_1": branch.flight},
            branch_results=[branch],
        )
        assert result.get_branch_result("stage_1") is branch

    def test_raises_for_unknown_name(self):
        """get_branch_result(name) raises KeyError for an unknown name."""
        result = MissionResult(root_flight=None, branch_flights={}, branch_results=[])
        with pytest.raises(KeyError):
            result.get_branch_result("unknown")


class TestMissionResultSummary:
    """summary() reports one line per flight."""

    def test_summary_contains_each_flight_name(self):
        """summary() mentions 'root' and each branch's name."""
        root_flight = _FakeFlight(apogee=500.0, impact_velocity=-2.0)
        branch = _make_branch_result("stage_1", _FakeFlight(apogee=400.0))
        result = MissionResult(
            root_flight=root_flight,
            branch_flights={"stage_1": branch.flight},
            branch_results=[branch],
        )
        summary = result.summary()
        assert "root" in summary
        assert "stage_1" in summary
        assert "500.00" in summary


class TestMissionResultPlotAll:
    """plot_all() delegates to rocketpy.plots.CompareFlights."""

    def test_plot_all_calls_compare_flights(self, monkeypatch):
        """plot_all() builds a CompareFlights over all_flights() and renders it."""
        calls = {}

        class _FakeCompareFlights:
            def __init__(self, flights):
                calls["flights"] = flights

            def trajectories_3d(self, legend=None):
                calls["legend"] = legend

        monkeypatch.setattr(
            "rocketpy.mission.mission_result.CompareFlights", _FakeCompareFlights
        )

        root_flight = _FakeFlight()
        branch = _make_branch_result("stage_1")
        result = MissionResult(
            root_flight=root_flight,
            branch_flights={"stage_1": branch.flight},
            branch_results=[branch],
        )

        comparison = result.plot_all()

        assert isinstance(comparison, _FakeCompareFlights)
        assert calls["flights"] == [root_flight, branch.flight]
        assert calls["legend"] is True
