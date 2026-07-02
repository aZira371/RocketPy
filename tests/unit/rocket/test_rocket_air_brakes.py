"""Unit tests for wiring air brakes (and controllable surfaces) into the
Rocket: surface-loop membership, cp pinning, stability invariance, and the
add_air_brakes compatibility surface."""

import pytest

from rocketpy import (
    AirBrakesController,
    ControllableGenericSurface,
    SurfaceController,
)

DRAG_CURVE = "data/rockets/calisto/air_brakes_cd.csv"


def kwargs_controller(**kwargs):
    kwargs["air_brakes"].deployment_level = 0.5


def add_air_brakes(rocket, **kwargs):
    defaults = {
        "drag_coefficient_curve": DRAG_CURVE,
        "controller_function": kwargs_controller,
        "sampling_rate": 10,
        "return_controller": True,
    }
    defaults.update(kwargs)
    return rocket.add_air_brakes(**defaults)


class TestAirBrakesInSurfaceLoop:
    def test_air_brakes_join_aerodynamic_surfaces(self, calisto_motorless):
        air_brakes, controller = add_air_brakes(calisto_motorless)
        assert air_brakes in [s for s, _ in calisto_motorless.aerodynamic_surfaces]
        assert air_brakes in calisto_motorless.air_brakes
        assert controller in calisto_motorless._controllers

    def test_default_position_pins_cp_to_cdm(self, calisto_motorless):
        air_brakes, _ = add_air_brakes(calisto_motorless)
        assert air_brakes._pin_cp_to_cdm is True
        assert tuple(calisto_motorless.surfaces_cp_to_cdm[air_brakes]) == (0, 0, 0)

    def test_pin_survives_add_motor(self, calisto_motorless, cesaroni_m1670):
        air_brakes, _ = add_air_brakes(calisto_motorless)
        calisto_motorless.add_motor(cesaroni_m1670, position=-1.373)
        assert tuple(calisto_motorless.surfaces_cp_to_cdm[air_brakes]) == (0, 0, 0)

    def test_explicit_position_uses_standard_cp_path(self, calisto_motorless):
        air_brakes, _ = add_air_brakes(calisto_motorless, position=-0.5)
        assert air_brakes._pin_cp_to_cdm is False
        cp_to_cdm = calisto_motorless.surfaces_cp_to_cdm[air_brakes]
        assert tuple(cp_to_cdm) != (0, 0, 0)

    def test_static_margin_unchanged_by_air_brakes(self, calisto_robust):
        margin_before = [calisto_robust.static_margin(t) for t in (0, 1, 3)]
        add_air_brakes(calisto_robust)
        margin_after = [calisto_robust.static_margin(t) for t in (0, 1, 3)]
        assert margin_after == pytest.approx(margin_before)


class TestAddAirBrakesCompatibility:
    def test_return_controller_type(self, calisto_motorless):
        _, controller = add_air_brakes(calisto_motorless)
        assert isinstance(controller, AirBrakesController)

    def test_kwargs_controller_function_not_wrapped(self, calisto_motorless):
        _, controller = add_air_brakes(calisto_motorless)
        assert controller.controller_function is kwargs_controller

    def test_legacy_positional_function_warns_and_works(self, calisto_motorless):
        def legacy(time, sampling_rate, state, state_history, observed, air_brakes):
            air_brakes.deployment_level = 0.25

        with pytest.warns(DeprecationWarning, match="positional arguments"):
            air_brakes, controller = add_air_brakes(
                calisto_motorless, controller_function=legacy
            )
        controller(time=1.0, state=[0.0] * 13)
        assert air_brakes.deployment_level == 0.25
        assert controller.control_history["air_brakes"]["deployment_level"] == [
            (1.0, 0.25)
        ]

    def test_initial_observed_variables_deprecated(self, calisto_motorless):
        with pytest.warns(DeprecationWarning, match="initial_observed_variables"):
            add_air_brakes(
                calisto_motorless, initial_observed_variables=[(0, 0, 0)]
            )


class TestAddControllableSurface:
    def make_surface(self, name="Canards"):
        return ControllableGenericSurface(
            reference_area=0.005,
            reference_length=0.05,
            coefficients={
                "cl": lambda alpha, beta, mach, re, q, r, p, deflection: deflection
            },
            name=name,
        )

    def test_surface_and_controller_wired(self, calisto_motorless):
        surface = self.make_surface()

        def law(**kwargs):
            kwargs["controlled_objects"].set_control("deflection", 0.2)

        controller = calisto_motorless.add_controllable_surface(
            surface, -0.5, law, sampling_rate=20
        )
        assert isinstance(controller, SurfaceController)
        assert controller.name == "Canards Controller"
        assert controller in calisto_motorless._controllers
        assert surface in [s for s, _ in calisto_motorless.aerodynamic_surfaces]

        controller(time=1.0, state=[0.0] * 13)
        assert surface.get_control("deflection") == 0.2
        assert controller.control_history["Canards"]["deflection"] == [(1.0, 0.2)]

    def test_rejects_non_controllable_surface(self, calisto_motorless):
        with pytest.raises(TypeError, match="ControllableGenericSurface"):
            calisto_motorless.add_controllable_surface(
                object(), -0.5, lambda **kwargs: None, sampling_rate=20
            )
