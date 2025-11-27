"""
Bella Lui 3-DOF vs 6-DOF Flight Simulation Comparison

This example demonstrates the differences between the 3-DOF and 6-DOF simulation
modes using the Bella Lui rocket from EPFL Rocket Team. It compares the trajectory,
apogee, and other flight parameters between both simulation modes, including the
effect of the weathercocking model on 3-DOF simulations.

Permission to use flight data given by Antoine Scardigli, 2020
"""

import os

import matplotlib.pyplot as plt
import numpy as np

from rocketpy import Environment, Flight, Function, Rocket, SolidMotor

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, "..", "..", "data")

# Define Bella Lui parameters
parameters = {
    # Mass Details
    "rocket_mass": (18.227 - 1, 0.010),  # 1.373 = propellant mass
    # propulsion details
    "impulse": (2157, 0.03 * 2157),
    "burn_time": (2.43, 0.1),
    "nozzle_radius": (44.45 / 1000, 0.001),
    "throat_radius": (21.4376 / 1000, 0.001),
    "grain_separation": (3 / 1000, 1 / 1000),
    "grain_density": (782.4, 30),
    "grain_outer_radius": (85.598 / 2000, 0.001),
    "grain_initial_inner_radius": (33.147 / 1000, 0.002),
    "grain_initial_height": (152.4 / 1000, 0.001),
    # Aerodynamic Details
    "inertia_i": (0.78267, 0.03 * 0.78267),
    "inertia_z": (0.064244, 0.03 * 0.064244),
    "radius": (156 / 2000, 0.001),
    "distance_rocket_nozzle": (-1.1356, 0.100),
    "distance_rocket_propellant": (-1, 0.100),
    "power_off_drag": (1, 0.05),
    "power_on_drag": (1, 0.05),
    "nose_length": (0.242, 0.001),
    "nose_distance_to_cm": (1.3, 0.100),
    "fin_span": (0.200, 0.001),
    "fin_root_chord": (0.280, 0.001),
    "fin_tip_chord": (0.125, 0.001),
    "fin_distance_to_cm": (-0.75, 0.100),
    "tail_top_radius": (156 / 2000, 0.001),
    "tail_bottom_radius": (135 / 2000, 0.001),
    "tail_length": (0.050, 0.001),
    "tail_distance_to_cm": (-1.0856, 0.001),
    # Launch and Environment Details
    "wind_direction": (0, 5),
    "wind_speed": (1, 0.05),
    "inclination": (89, 1),
    "heading": (45, 5),
    "rail_length": (4.2, 0.001),
    # Parachute Details
    "CdS_drogue": (np.pi / 4, 0.20 * np.pi / 4),
    "lag_rec": (1, 0.020),
}


def create_environment():
    """Create the Environment object for the Bella Lui mission."""
    env = Environment(
        gravity=9.81,
        latitude=47.213476,
        longitude=9.003336,
        date=(2020, 2, 22, 13),
        elevation=407,
    )
    env.set_atmospheric_model(
        type="Reanalysis",
        file=os.path.join(DATA_DIR, "weather", "bella_lui_weather_data_ERA5.nc"),
        dictionary="ECMWF",
    )
    env.max_expected_height = 2000
    return env


def create_motor():
    """Create the K828FJ SolidMotor object."""
    return SolidMotor(
        thrust_source=os.path.join(
            DATA_DIR, "motors", "aerotech", "AeroTech_K828FJ.eng"
        ),
        burn_time=parameters.get("burn_time")[0],
        dry_mass=1,
        dry_inertia=(0, 0, 0),
        center_of_dry_mass_position=0,
        grains_center_of_mass_position=parameters.get("distance_rocket_propellant")[0],
        grain_number=3,
        grain_separation=parameters.get("grain_separation")[0],
        grain_density=parameters.get("grain_density")[0],
        grain_outer_radius=parameters.get("grain_outer_radius")[0],
        grain_initial_inner_radius=parameters.get("grain_initial_inner_radius")[0],
        grain_initial_height=parameters.get("grain_initial_height")[0],
        nozzle_radius=parameters.get("nozzle_radius")[0],
        throat_radius=parameters.get("throat_radius")[0],
        interpolation_method="linear",
        nozzle_position=parameters.get("distance_rocket_nozzle")[0],
    )


def create_rocket(motor):
    """Create the Bella Lui Rocket object."""
    bella_lui = Rocket(
        radius=parameters.get("radius")[0],
        mass=parameters.get("rocket_mass")[0],
        inertia=(
            parameters.get("inertia_i")[0],
            parameters.get("inertia_i")[0],
            parameters.get("inertia_z")[0],
        ),
        power_off_drag=0.43,
        power_on_drag=0.43,
        center_of_mass_without_motor=0,
    )
    bella_lui.set_rail_buttons(0.1, -0.5)
    bella_lui.add_motor(motor, parameters.get("distance_rocket_nozzle")[0])
    bella_lui.add_nose(
        length=parameters.get("nose_length")[0],
        kind="tangent",
        position=parameters.get("nose_distance_to_cm")[0]
        + parameters.get("nose_length")[0],
    )
    bella_lui.add_trapezoidal_fins(
        3,
        span=parameters.get("fin_span")[0],
        root_chord=parameters.get("fin_root_chord")[0],
        tip_chord=parameters.get("fin_tip_chord")[0],
        position=parameters.get("fin_distance_to_cm")[0],
    )
    bella_lui.add_tail(
        top_radius=parameters.get("tail_top_radius")[0],
        bottom_radius=parameters.get("tail_bottom_radius")[0],
        length=parameters.get("tail_length")[0],
        position=parameters.get("tail_distance_to_cm")[0],
    )

    # Define aerodynamic drag coefficients
    bella_lui.power_off_drag = Function(
        [
            (0.01, 0.51),
            (0.02, 0.46),
            (0.04, 0.43),
            (0.28, 0.43),
            (0.29, 0.44),
            (0.45, 0.44),
            (0.49, 0.46),
        ],
        "Mach Number",
        "Drag Coefficient with Power Off",
        "linear",
        "constant",
    )
    bella_lui.power_on_drag = Function(
        [
            (0.01, 0.51),
            (0.02, 0.46),
            (0.04, 0.43),
            (0.28, 0.43),
            (0.29, 0.44),
            (0.45, 0.44),
            (0.49, 0.46),
        ],
        "Mach Number",
        "Drag Coefficient with Power On",
        "linear",
        "constant",
    )
    bella_lui.power_off_drag *= parameters.get("power_off_drag")[0]
    bella_lui.power_on_drag *= parameters.get("power_on_drag")[0]

    return bella_lui


def run_flight_comparison():
    """
    Run 6-DOF and 3-DOF flight simulations and compare results.

    This function creates the environment, motor, and rocket, then runs
    simulations in both 6-DOF and 3-DOF modes with different weathercocking
    coefficients to demonstrate the effect of the weathercocking model.
    """
    print("=" * 70)
    print("Bella Lui 3-DOF vs 6-DOF Flight Simulation Comparison")
    print("=" * 70)

    # Create environment and rocket components
    print("\nCreating environment...")
    env = create_environment()

    print("Creating motor...")
    motor = create_motor()

    print("Creating rocket...")
    rocket = create_rocket(motor)

    # Run 6-DOF simulation (reference)
    print("\n" + "-" * 50)
    print("Running 6-DOF simulation (reference)...")
    print("-" * 50)
    flight_6dof = Flight(
        rocket=rocket,
        environment=env,
        rail_length=parameters.get("rail_length")[0],
        inclination=parameters.get("inclination")[0],
        heading=parameters.get("heading")[0],
        terminate_on_apogee=True,
    )

    # Run 3-DOF simulation without weathercocking (fixed attitude)
    print("\n" + "-" * 50)
    print("Running 3-DOF simulation (no weathercocking, weathercock_coeff=0)...")
    print("-" * 50)
    flight_3dof_fixed = Flight(
        rocket=rocket,
        environment=env,
        rail_length=parameters.get("rail_length")[0],
        inclination=parameters.get("inclination")[0],
        heading=parameters.get("heading")[0],
        terminate_on_apogee=True,
        simulation_mode="3 DOF",
        weathercock_coeff=0.0,  # Fixed attitude
    )

    # Run 3-DOF simulation with default weathercocking
    print("\n" + "-" * 50)
    print("Running 3-DOF simulation (default weathercocking, weathercock_coeff=1.0)...")
    print("-" * 50)
    flight_3dof_wc1 = Flight(
        rocket=rocket,
        environment=env,
        rail_length=parameters.get("rail_length")[0],
        inclination=parameters.get("inclination")[0],
        heading=parameters.get("heading")[0],
        terminate_on_apogee=True,
        simulation_mode="3 DOF",
        weathercock_coeff=1.0,  # Default weathercocking
    )

    # Run 3-DOF simulation with high weathercocking
    print("\n" + "-" * 50)
    print("Running 3-DOF simulation (high weathercocking, weathercock_coeff=5.0)...")
    print("-" * 50)
    flight_3dof_wc5 = Flight(
        rocket=rocket,
        environment=env,
        rail_length=parameters.get("rail_length")[0],
        inclination=parameters.get("inclination")[0],
        heading=parameters.get("heading")[0],
        terminate_on_apogee=True,
        simulation_mode="3 DOF",
        weathercock_coeff=5.0,  # High weathercocking
    )

    # Print comparison results
    print("\n" + "=" * 70)
    print("SIMULATION RESULTS COMPARISON")
    print("=" * 70)

    print(
        "\n{:<40} {:>10} {:>10} {:>10} {:>10}".format(
            "Parameter", "6-DOF", "3DOF(wc=0)", "3DOF(wc=1)", "3DOF(wc=5)"
        )
    )
    print("-" * 80)

    print(
        "{:<40} {:>10.2f} {:>10.2f} {:>10.2f} {:>10.2f}".format(
            "Apogee (m AGL)",
            flight_6dof.apogee - env.elevation,
            flight_3dof_fixed.apogee - env.elevation,
            flight_3dof_wc1.apogee - env.elevation,
            flight_3dof_wc5.apogee - env.elevation,
        )
    )

    print(
        "{:<40} {:>10.2f} {:>10.2f} {:>10.2f} {:>10.2f}".format(
            "Apogee Time (s)",
            flight_6dof.apogee_time,
            flight_3dof_fixed.apogee_time,
            flight_3dof_wc1.apogee_time,
            flight_3dof_wc5.apogee_time,
        )
    )

    print(
        "{:<40} {:>10.2f} {:>10.2f} {:>10.2f} {:>10.2f}".format(
            "Apogee X (m)",
            flight_6dof.apogee_x,
            flight_3dof_fixed.apogee_x,
            flight_3dof_wc1.apogee_x,
            flight_3dof_wc5.apogee_x,
        )
    )

    print(
        "{:<40} {:>10.2f} {:>10.2f} {:>10.2f} {:>10.2f}".format(
            "Apogee Y (m)",
            flight_6dof.apogee_y,
            flight_3dof_fixed.apogee_y,
            flight_3dof_wc1.apogee_y,
            flight_3dof_wc5.apogee_y,
        )
    )

    print(
        "{:<40} {:>10.2f} {:>10.2f} {:>10.2f} {:>10.2f}".format(
            "Max Speed (m/s)",
            flight_6dof.max_speed,
            flight_3dof_fixed.max_speed,
            flight_3dof_wc1.max_speed,
            flight_3dof_wc5.max_speed,
        )
    )

    print(
        "{:<40} {:>10.2f} {:>10.2f} {:>10.2f} {:>10.2f}".format(
            "Max Acceleration (m/s²)",
            flight_6dof.max_acceleration,
            flight_3dof_fixed.max_acceleration,
            flight_3dof_wc1.max_acceleration,
            flight_3dof_wc5.max_acceleration,
        )
    )

    print(
        "{:<40} {:>10.2f} {:>10.2f} {:>10.2f} {:>10.2f}".format(
            "Out of Rail Velocity (m/s)",
            flight_6dof.out_of_rail_velocity,
            flight_3dof_fixed.out_of_rail_velocity,
            flight_3dof_wc1.out_of_rail_velocity,
            flight_3dof_wc5.out_of_rail_velocity,
        )
    )

    # Calculate percentage differences from 6-DOF
    print("\n" + "-" * 80)
    print("PERCENTAGE DIFFERENCE FROM 6-DOF REFERENCE:")
    print("-" * 80)

    apogee_diff_fixed = (
        (flight_3dof_fixed.apogee - flight_6dof.apogee) / flight_6dof.apogee * 100
    )
    apogee_diff_wc1 = (
        (flight_3dof_wc1.apogee - flight_6dof.apogee) / flight_6dof.apogee * 100
    )
    apogee_diff_wc5 = (
        (flight_3dof_wc5.apogee - flight_6dof.apogee) / flight_6dof.apogee * 100
    )

    print(
        "{:<40} {:>10} {:>10.2f}% {:>10.2f}% {:>10.2f}%".format(
            "Apogee Difference",
            "-",
            apogee_diff_fixed,
            apogee_diff_wc1,
            apogee_diff_wc5,
        )
    )

    # Create comparison plots
    print("\n" + "=" * 70)
    print("Creating comparison plots...")
    print("=" * 70)

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # Plot 1: Altitude vs Time
    ax1 = axes[0, 0]
    ax1.plot(
        flight_6dof.z[:, 0],
        flight_6dof.z[:, 1] - env.elevation,
        label="6-DOF",
        linewidth=2,
    )
    ax1.plot(
        flight_3dof_fixed.z[:, 0],
        flight_3dof_fixed.z[:, 1] - env.elevation,
        label="3-DOF (wc=0)",
        linestyle="--",
        linewidth=2,
    )
    ax1.plot(
        flight_3dof_wc1.z[:, 0],
        flight_3dof_wc1.z[:, 1] - env.elevation,
        label="3-DOF (wc=1)",
        linestyle="-.",
        linewidth=2,
    )
    ax1.plot(
        flight_3dof_wc5.z[:, 0],
        flight_3dof_wc5.z[:, 1] - env.elevation,
        label="3-DOF (wc=5)",
        linestyle=":",
        linewidth=2,
    )
    ax1.set_xlabel("Time (s)")
    ax1.set_ylabel("Altitude AGL (m)")
    ax1.set_title("Altitude vs Time Comparison")
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # Plot 2: Velocity vs Time
    ax2 = axes[0, 1]
    ax2.plot(
        flight_6dof.speed[:, 0], flight_6dof.speed[:, 1], label="6-DOF", linewidth=2
    )
    ax2.plot(
        flight_3dof_fixed.speed[:, 0],
        flight_3dof_fixed.speed[:, 1],
        label="3-DOF (wc=0)",
        linestyle="--",
        linewidth=2,
    )
    ax2.plot(
        flight_3dof_wc1.speed[:, 0],
        flight_3dof_wc1.speed[:, 1],
        label="3-DOF (wc=1)",
        linestyle="-.",
        linewidth=2,
    )
    ax2.plot(
        flight_3dof_wc5.speed[:, 0],
        flight_3dof_wc5.speed[:, 1],
        label="3-DOF (wc=5)",
        linestyle=":",
        linewidth=2,
    )
    ax2.set_xlabel("Time (s)")
    ax2.set_ylabel("Speed (m/s)")
    ax2.set_title("Speed vs Time Comparison")
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    # Plot 3: Trajectory (X-Y)
    ax3 = axes[1, 0]
    ax3.plot(flight_6dof.x[:, 1], flight_6dof.y[:, 1], label="6-DOF", linewidth=2)
    ax3.plot(
        flight_3dof_fixed.x[:, 1],
        flight_3dof_fixed.y[:, 1],
        label="3-DOF (wc=0)",
        linestyle="--",
        linewidth=2,
    )
    ax3.plot(
        flight_3dof_wc1.x[:, 1],
        flight_3dof_wc1.y[:, 1],
        label="3-DOF (wc=1)",
        linestyle="-.",
        linewidth=2,
    )
    ax3.plot(
        flight_3dof_wc5.x[:, 1],
        flight_3dof_wc5.y[:, 1],
        label="3-DOF (wc=5)",
        linestyle=":",
        linewidth=2,
    )
    ax3.set_xlabel("X Position (m)")
    ax3.set_ylabel("Y Position (m)")
    ax3.set_title("Horizontal Trajectory Comparison")
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    ax3.set_aspect("equal")

    # Plot 4: 3D Trajectory
    ax4 = axes[1, 1]
    ax4 = fig.add_subplot(2, 2, 4, projection="3d")
    ax4.plot(
        flight_6dof.x[:, 1],
        flight_6dof.y[:, 1],
        flight_6dof.z[:, 1] - env.elevation,
        label="6-DOF",
        linewidth=2,
    )
    ax4.plot(
        flight_3dof_fixed.x[:, 1],
        flight_3dof_fixed.y[:, 1],
        flight_3dof_fixed.z[:, 1] - env.elevation,
        label="3-DOF (wc=0)",
        linestyle="--",
        linewidth=2,
    )
    ax4.plot(
        flight_3dof_wc1.x[:, 1],
        flight_3dof_wc1.y[:, 1],
        flight_3dof_wc1.z[:, 1] - env.elevation,
        label="3-DOF (wc=1)",
        linestyle="-.",
        linewidth=2,
    )
    ax4.plot(
        flight_3dof_wc5.x[:, 1],
        flight_3dof_wc5.y[:, 1],
        flight_3dof_wc5.z[:, 1] - env.elevation,
        label="3-DOF (wc=5)",
        linestyle=":",
        linewidth=2,
    )
    ax4.set_xlabel("X (m)")
    ax4.set_ylabel("Y (m)")
    ax4.set_zlabel("Altitude AGL (m)")
    ax4.set_title("3D Trajectory Comparison")
    ax4.legend()

    plt.tight_layout()
    plt.savefig("bella_lui_3dof_vs_6dof_comparison.png", dpi=150, bbox_inches="tight")
    print("\nPlots saved to: bella_lui_3dof_vs_6dof_comparison.png")

    plt.show()

    # Return flights for further analysis
    return {
        "6dof": flight_6dof,
        "3dof_fixed": flight_3dof_fixed,
        "3dof_wc1": flight_3dof_wc1,
        "3dof_wc5": flight_3dof_wc5,
    }


if __name__ == "__main__":
    flights = run_flight_comparison()

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print("""
This example demonstrates the differences between 6-DOF and 3-DOF simulation modes:

1. 6-DOF (Full Dynamics):
   - Full rotational and translational dynamics
   - Quaternions evolve based on angular momentum conservation
   - Most accurate but computationally expensive

2. 3-DOF with weathercock_coeff=0 (Fixed Attitude):
   - Only translational dynamics
   - Attitude remains fixed (no quaternion evolution)
   - Fastest but may not capture lateral motion accurately

3. 3-DOF with weathercock_coeff=1 (Default Weathercocking):
   - Translational dynamics with quasi-static attitude evolution
   - Body axis aligns toward relative wind direction
   - Good balance between accuracy and speed

4. 3-DOF with weathercock_coeff=5 (High Weathercocking):
   - Faster alignment toward relative wind
   - Useful when rocket is expected to quickly align with velocity

Key Observations:
- The weathercocking model helps the 3-DOF simulation better approximate
  the 6-DOF behavior by allowing the attitude to evolve
- Higher weathercock_coeff values result in faster alignment with the wind
- The 3-DOF mode is significantly faster and suitable for Monte Carlo
  simulations where many runs are needed
""")
