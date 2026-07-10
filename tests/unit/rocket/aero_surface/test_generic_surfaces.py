import pytest

from rocketpy import Function, GenericSurface
from rocketpy.mathutils import Vector

REFERENCE_AREA = 1
REFERENCE_LENGTH = 1


@pytest.mark.parametrize(
    "coefficients",
    [
        "cN",
        {"invalid_name": 0},
        {"cN": "inexistent_file.csv"},
        {"cN": Function(lambda x1, x2, x3, x4, x5, x6: 0)},
        {"cN": lambda x1: 0},
        {"cN": {}},
    ],
)
def test_invalid_initialization(coefficients):
    """Checks if generic surface raises errors in initialization
    when coefficient argument is invalid"""

    with pytest.raises((ValueError, TypeError)):
        GenericSurface(
            reference_area=REFERENCE_AREA,
            reference_length=REFERENCE_LENGTH,
            coefficients=coefficients,
        )


def test_invalid_initialization_from_csv(filename_invalid_coeff):
    """Checks if generic surfaces raises errors when initialized incorrectly
    from a csv file"""
    with pytest.raises(ValueError):
        GenericSurface(
            reference_area=REFERENCE_AREA,
            reference_length=REFERENCE_LENGTH,
            coefficients={"cN": str(filename_invalid_coeff)},
        )


@pytest.mark.parametrize(
    "coefficients",
    [
        {},
        {"cN": 0},
        {
            "cN": 0,
            "cY": Function(lambda x1, x2, x3, x4, x5, x6, x7: 0),
            "cA": lambda x1, x2, x3, x4, x5, x6, x7: 0,
        },
    ],
)
def test_valid_initialization(coefficients):
    """Checks if generic surface initializes correctly when coefficient
    argument is valid"""

    GenericSurface(
        reference_area=REFERENCE_AREA,
        reference_length=REFERENCE_LENGTH,
        coefficients=coefficients,
    )


def test_valid_initialization_from_csv(filename_valid_coeff):
    """Checks if generic surfaces initializes correctly when
    coefficients is set from a csv file"""
    GenericSurface(
        reference_area=REFERENCE_AREA,
        reference_length=REFERENCE_LENGTH,
        coefficients={"cN": str(filename_valid_coeff)},
    )


def test_csv_independent_variables_accept_any_order(tmp_path):
    """Checks if GenericSurface correctly maps CSV columns by header names,
    regardless of independent variable column order."""
    filename = tmp_path / "valid_coefficients_shuffled_order.csv"
    filename.write_text(
        "mach,alpha,cN\n0,0,0\n0,1,10\n2,0,2\n2,1,12\n",
        encoding="utf-8",
    )

    generic_surface = GenericSurface(
        reference_area=REFERENCE_AREA,
        reference_length=REFERENCE_LENGTH,
        coefficients={"cN": str(filename)},
    )

    # The coefficient is stored at minimal dimension over its CSV columns, in
    # header order; AeroCoefficient maps the full argument tuple onto them.
    assert generic_surface.cN.depends_on == ("mach", "alpha")
    csv_function = generic_surface.cN.function

    assert generic_surface.cN(1, 0, 2, 0, 0, 0, 0) == pytest.approx(12)
    assert csv_function.get_interpolation_method() == "regular_grid"


POINTS = [[0, 0], [1, 1], [2, 4], [3, 9]]


def test_interpolation_extrapolation_scalar_applies_to_all():
    """A single interpolation/extrapolation string is applied to every
    tabulated coefficient."""
    gs = GenericSurface(
        reference_area=REFERENCE_AREA,
        reference_length=REFERENCE_LENGTH,
        coefficients={"cN": POINTS, "cA": POINTS},
        extrapolation="constant",
        interpolation="akima",
    )
    for coeff in (gs.cN, gs.cA):
        assert coeff.function.get_interpolation_method() == "akima"
        assert coeff.function.get_extrapolation_method() == "constant"


def test_interpolation_extrapolation_per_coefficient_dict():
    """A dict configures interpolation/extrapolation per coefficient; omitted
    coefficients keep the default."""
    gs = GenericSurface(
        reference_area=REFERENCE_AREA,
        reference_length=REFERENCE_LENGTH,
        coefficients={"cN": POINTS, "cA": POINTS},
        extrapolation={"cA": "constant"},
        interpolation={"cN": "akima"},
    )
    assert gs.cN.function.get_interpolation_method() == "akima"
    assert gs.cA.function.get_extrapolation_method() == "constant"
    # cN was not in the extrapolation dict, so it keeps the tabulated default.
    assert gs.cN.function.get_interpolation_method() == "akima"
    assert gs.cA.function.get_interpolation_method() == "linear"


def test_prebuilt_function_interpolation_left_unchanged():
    """A pre-built Function keeps its own interpolation/extrapolation when none
    is requested, and is copied (not mutated) when they are overridden."""
    source = Function(POINTS, interpolation="spline", extrapolation="zero")

    unchanged = GenericSurface(REFERENCE_AREA, REFERENCE_LENGTH, {"cN": source})
    assert unchanged.cN.function.get_interpolation_method() == "spline"
    assert unchanged.cN.function.get_extrapolation_method() == "zero"

    overridden = GenericSurface(
        REFERENCE_AREA,
        REFERENCE_LENGTH,
        {"cN": source},
        interpolation="linear",
        extrapolation="constant",
    )
    assert overridden.cN.function.get_interpolation_method() == "linear"
    # The original Function must not have been mutated in place.
    assert source.get_interpolation_method() == "spline"


def test_tabulated_coefficient_defaults_to_constant_extrapolation():
    """Tabulated coefficients default to constant extrapolation, so they do not
    run to non-physical values past their data."""
    gs = GenericSurface(
        reference_area=REFERENCE_AREA,
        reference_length=REFERENCE_LENGTH,
        coefficients={"cN": POINTS},
    )
    assert gs.cN.function.get_extrapolation_method() == "constant"


def _write_grid_csv(path):
    """A 4x4 (mach, alpha) Cartesian grid, nonlinear in alpha so interpolation
    methods produce distinguishable values. 4 points per axis lets "cubic" fit.
    """
    rows = ["mach,alpha,cN"]
    for mach in (0, 1, 2, 3):
        for alpha in (0.0, 0.1, 0.2, 0.3):
            rows.append(f"{mach},{alpha},{mach + 10 * alpha**2}")
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    return str(path)


@pytest.mark.parametrize(
    "interpolation, expected_grid_method",
    [("linear", "linear"), ("spline", "cubic"), ("akima", "pchip")],
)
def test_grid_csv_interpolation_maps_to_scipy_method(
    tmp_path, interpolation, expected_grid_method
):
    """A gridded CSV honors the interpolation argument by mapping it onto the
    RegularGridInterpolator method (no silent fallback to shepard)."""
    filename = _write_grid_csv(tmp_path / "grid.csv")

    gs = GenericSurface(
        reference_area=REFERENCE_AREA,
        reference_length=REFERENCE_LENGTH,
        coefficients={"cN": filename},
        interpolation=interpolation,
    )
    function = gs.cN.function
    # The Function stays a regular grid (not clobbered to shepard) ...
    assert function.get_interpolation_method() == "regular_grid"
    # ... with the mapped scipy method threaded through.
    assert getattr(function, "_grid_method", "linear") == expected_grid_method


def test_grid_csv_cubic_differs_from_linear(tmp_path):
    """The mapped grid method actually changes interpolation off the grid nodes,
    confirming it is not ignored."""
    filename = _write_grid_csv(tmp_path / "grid.csv")

    linear = GenericSurface(
        REFERENCE_AREA, REFERENCE_LENGTH, {"cN": filename}, interpolation="linear"
    )
    cubic = GenericSurface(
        REFERENCE_AREA, REFERENCE_LENGTH, {"cN": filename}, interpolation="spline"
    )
    # Interior off-node point at alpha=0.15, mach=0.5 (argument order is
    # alpha, beta, mach, ...): the nonlinear-in-alpha grid makes cubic and
    # linear disagree there.
    args = (0.15, 0.0, 0.5, 0, 0, 0, 0)
    assert linear.cN(*args) != pytest.approx(cubic.cN(*args))


def test_compute_forces_and_moments():
    """Checks if there are not logical errors in
    compute forces and moments"""

    gs_object = GenericSurface(REFERENCE_AREA, REFERENCE_LENGTH, {})
    forces_and_moments = gs_object.compute_forces_and_moments(
        stream_velocity=Vector((0, 0, 0)),
        stream_speed=0,
        stream_mach=0,
        rho=0,
        cp=Vector((0, 0, 0)),
        omega=(0, 0, 0),
        density=Function(1.0),
        dynamic_viscosity=Function(1.0),
        z=0,
    )
    assert forces_and_moments == (0, 0, 0, 0, 0, 0)


def test_angular_rates_are_non_dimensionalized():
    """Coefficients receive the conventional reduced rate q* = q L_ref / (2 V),
    not the raw body rate in rad/s."""
    ref_area, ref_length = 2.0, 0.5
    # Roll-moment coefficient that simply returns the roll rate it is given, so
    # the resulting roll moment exposes which rate value reached the coefficient.
    gs = GenericSurface(ref_area, ref_length, {"cl": lambda roll_rate: roll_rate})

    rho, speed, raw_roll = 1.2, 10.0, 4.0
    *_, roll_moment = gs.compute_forces_and_moments(
        stream_velocity=Vector((0, 0, -speed)),  # along centerline -> alpha=beta=0
        stream_speed=speed,
        stream_mach=0,
        rho=rho,
        cp=Vector((0, 0, 0)),
        omega=(0, 0, raw_roll),  # raw body roll rate p, rad/s
        density=Function(1.0),
        dynamic_viscosity=Function(1.0),
        z=0,
    )

    reduced_roll = raw_roll * ref_length / (2 * speed)
    dyn_pressure_area_length = 0.5 * rho * speed**2 * ref_area * ref_length
    # The coefficient saw the reduced rate, ...
    assert roll_moment == pytest.approx(dyn_pressure_area_length * reduced_roll)
    # ... not the raw rad/s rate.
    assert roll_moment != pytest.approx(dyn_pressure_area_length * raw_roll)
