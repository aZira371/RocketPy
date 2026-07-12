"""Unit tests for the Rocket AttachmentHost interface methods."""

import pytest

from rocketpy import Rocket
from rocketpy.body import FlightBody, RocketAdapter
from rocketpy.mission import (
    Attachment,
    Deployable,
    DeploymentEvent,
    IgnitionEvent,
    Stage,
    StageSeparationEvent,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_rocket():
    """Return a minimal Rocket instance."""
    return Rocket(
        radius=0.0635,
        mass=16.235,
        inertia=(6.321, 6.321, 0.0346),
        power_off_drag=0.5,
        power_on_drag=0.5,
        center_of_mass_without_motor=0,
    )


def _make_body(name="test_body"):
    return FlightBody(
        name=name,
        geometry=0.05,
        mass_model=lambda t: 5.0,
        inertia_model=lambda t: (0.5, 0.5, 0.01, 0.0, 0.0, 0.0),
        center_of_mass_model=lambda t: 0.4,
    )


def _make_attachment():
    return Attachment([0.0, 0.0, 1.5], [0.0, 0.0, 0.0])


def _always(**kwargs):
    return True


def _make_stage(**kwargs):
    defaults = dict(
        name="upper_stage",
        body=_make_body("upper_body"),
        attachment=_make_attachment(),
        separation_event=StageSeparationEvent("sep", _always),
    )
    defaults.update(kwargs)
    return Stage(**defaults)


def _make_deployable(**kwargs):
    defaults = dict(
        name="payload",
        body=_make_body("payload"),
        attachment=_make_attachment(),
        deployment_event=DeploymentEvent("deploy", _always),
    )
    defaults.update(kwargs)
    return Deployable(**defaults)


# ---------------------------------------------------------------------------
# Tests – stages / deployables lists
# ---------------------------------------------------------------------------


class TestRocketMissionLists:
    """Rocket starts with empty mission lists."""

    def test_stages_empty_by_default(self):
        """stages is empty when no stages have been added."""
        r = _make_rocket()
        assert r.stages == []

    def test_deployables_empty_by_default(self):
        """deployables is empty when no deployables have been added."""
        r = _make_rocket()
        assert r.deployables == []


# ---------------------------------------------------------------------------
# Tests – add_stage / add_deployable
# ---------------------------------------------------------------------------


class TestRocketAddStage:
    """Rocket.add_stage validates and stores stages."""

    def test_add_valid_stage(self):
        """add_stage appends a Stage to the internal list."""
        r = _make_rocket()
        s = _make_stage()
        r.add_stage(s)
        assert s in r.stages

    def test_add_stage_raises_for_non_stage(self):
        """add_stage raises TypeError when given a non-Stage object."""
        r = _make_rocket()
        with pytest.raises(TypeError):
            r.add_stage("not a stage")

    def test_add_stage_raises_for_invalid_stage(self):
        """add_stage raises ValueError when stage.validate() fails."""
        r = _make_rocket()
        bad_stage = _make_stage(body=None)
        with pytest.raises(ValueError):
            r.add_stage(bad_stage)


class TestRocketAddDeployable:
    """Rocket.add_deployable validates and stores deployables."""

    def test_add_valid_deployable(self):
        """add_deployable appends a Deployable."""
        r = _make_rocket()
        d = _make_deployable()
        r.add_deployable(d)
        assert d in r.deployables

    def test_add_deployable_raises_for_non_deployable(self):
        """add_deployable raises TypeError for a non-Deployable object."""
        r = _make_rocket()
        with pytest.raises(TypeError):
            r.add_deployable({"not": "a deployable"})

    def test_add_deployable_raises_for_invalid_deployable(self):
        """add_deployable raises ValueError when deployable.validate() fails."""
        r = _make_rocket()
        bad = _make_deployable(body=None)
        with pytest.raises(ValueError):
            r.add_deployable(bad)


# ---------------------------------------------------------------------------
# Tests – select_stage
# ---------------------------------------------------------------------------


class TestRocketSelectStage:
    """Rocket.select_stage retrieves stages by index or name."""

    def test_select_by_index(self):
        """select_stage(0) returns the first stage."""
        r = _make_rocket()
        s = _make_stage(name="booster")
        r.add_stage(s)
        assert r.select_stage(0) is s

    def test_select_by_name(self):
        """select_stage('booster') returns the stage with that name."""
        r = _make_rocket()
        s = _make_stage(name="booster")
        r.add_stage(s)
        assert r.select_stage("booster") is s

    def test_select_by_index_out_of_range_raises(self):
        """select_stage raises IndexError for an out-of-range index."""
        r = _make_rocket()
        with pytest.raises(IndexError):
            r.select_stage(0)

    def test_select_by_name_not_found_raises(self):
        """select_stage raises KeyError for an unknown stage name."""
        r = _make_rocket()
        with pytest.raises(KeyError):
            r.select_stage("nonexistent")

    def test_select_with_invalid_type_raises(self):
        """select_stage raises TypeError for a non-int/str argument."""
        r = _make_rocket()
        with pytest.raises(TypeError):
            r.select_stage(3.14)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Tests – attached_items / as_body
# ---------------------------------------------------------------------------


class TestRocketAttachmentHostHelpers:
    """Rocket.attached_items and Rocket.as_body satisfy the interface."""

    def test_attached_items_combines_stages_and_deployables(self):
        """attached_items returns stages + deployables."""
        r = _make_rocket()
        s = _make_stage()
        d = _make_deployable()
        r.add_stage(s)
        r.add_deployable(d)
        items = r.attached_items()
        assert items == [s, d]

    def test_attached_items_empty_by_default(self):
        """attached_items is empty before adding anything."""
        r = _make_rocket()
        assert r.attached_items() == []

    def test_as_body_returns_rocket_adapter(self):
        """as_body() returns a RocketAdapter wrapping this rocket."""
        r = _make_rocket()
        adapter = r.as_body()
        assert isinstance(adapter, RocketAdapter)
        assert adapter.rocket is r
