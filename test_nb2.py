
import csv

import cadquery as cq
import numpy as np

from rocketpy import CylindricalTank, SphericalTank
# Create fixtures geometries
geometry_map = {}
geometry_map["sphere"] = {"spherical_oxidizer_tank": SphericalTank(0.05)}
geometry_map["cylinder"] = {
    "cylindrical_oxidizer_tank": CylindricalTank(0.0744, 0.8068, True),
    "cylindrical_pressurant_tank": CylindricalTank(0.135 / 2, 0.981, True),
}
def export_expected_parameters(name, datapoints):
    with open(f"{name}_expected.csv", mode="w") as output_file:
        writer = csv.writer(output_file)
        writer.writerow(["level_height", "volume", "center_of_mass", "inertia"])
        for data_row in datapoints:
            writer.writerow([*data_row])
def evaluate_sphere_parameters(radius, level_height):
    """Computes the volume, center of mass and inertia
    (with respect to the origin) of a sphere 'filled' up
    to a certain level height.

    Parameters
    ----------
    radius : float
        The radius of the sphere.
    level_height : float
        The height of the liquid inside the sphere.

    Returns
    -------
    volume : float
        The volume of the sphere.
    center_of_mass : float
        The center of mass of the sphere.
    inertia : float
        The inertia of the sphere with respect to the origin.
    """
    sphere = cq.Workplane("XY").sphere(radius)

    # Cut the sphere to the level height
    drill_height = 10 * radius
    sphere = sphere.cut(
        cq.Workplane("XY")
        .cylinder(drill_height, radius)
        .translate((0, 0, drill_height / 2 + level_height))
    )

    # Uncomment to display the CAD
    # display(sphere)

    primitive = sphere.val()

    volume = primitive.Volume()
    center_of_mass = primitive.centerOfMass(primitive)
    inertia_tensor = primitive.matrixOfInertia(primitive)

    return volume, center_of_mass.z, inertia_tensor[0][0] + volume * center_of_mass.z**2
for name, sphere_geometry in geometry_map["sphere"].items():
    radius = sphere_geometry.total_height / 2
    datapoints = []
    for h in np.linspace(-radius, radius, 25):
        datapoints.append([h, *evaluate_sphere_parameters(radius, h)])

    export_expected_parameters(name, datapoints)
def evaluate_cylinder_with_caps(total_length, radius, level_height):
    """Computes the volume, center of mass and inertia (with respect
    to the origin) of a cylinder with spherical caps 'filled' up to a
    certain level height.

    Parameters
    ----------
    total_length : float
        The total length of the cylinder (with caps).
    radius : float
        The radius of the cylinder.

    Returns
    -------
    volume : float
        The volume of the cylinder with caps.
    center_of_mass : float
        The z-coordinate of the center of mass.
    inertia : float
        The inertia of the cylinder with caps with respect to the origin.
    """
    cylinder_height = total_length - 2 * radius

    cylinder = cq.Workplane("XY").cylinder(cylinder_height, radius)
    top_cap = (
        cq.Workplane("XY").sphere(radius).translate((0, 0, total_length / 2 - radius))
    )
    bottom_cap = (
        cq.Workplane("XY").sphere(radius).translate((0, 0, -total_length / 2 + radius))
    )

    solid = cylinder.union(top_cap).union(bottom_cap)

    # Remove solid above the level_height
    drill_height = 10 * total_length
    solid = solid.cut(
        cq.Workplane("XY")
        .cylinder(drill_height, radius)
        .translate((0, 0, drill_height / 2 + level_height))
    )
    # Uncomment to display the CAD
    # display(solid)

    primitive = solid.val()

    volume = primitive.Volume()
    center_of_mass = primitive.centerOfMass(primitive)
    inertia_tensor = primitive.matrixOfInertia(primitive)

    return volume, center_of_mass.z, inertia_tensor[0][0] + volume * center_of_mass.z**2
for name, cylinder_geometry in geometry_map["cylinder"].items():
    radius = cylinder_geometry.radius(0)
    length = cylinder_geometry.total_height
    datapoints = []
    for h in np.linspace(-length / 2, length / 2, 25):
        datapoints.append([h, *evaluate_cylinder_with_caps(length, radius, h)])

    export_expected_parameters(name, datapoints)
