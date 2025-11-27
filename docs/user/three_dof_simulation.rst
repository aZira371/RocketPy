.. _threedofsimulation:

3-DOF Rocket Simulations
=========================

RocketPy supports simplified 3-DOF (3 Degrees of Freedom) trajectory simulations,
where the rocket is modeled as a point mass. This mode is useful for quick
analyses, educational purposes, or when rotational dynamics are negligible.

.. contents:: Table of Contents
   :local:
   :depth: 2

Overview
--------

In a 3-DOF simulation, the rocket's motion is described by three translational
degrees of freedom (x, y, z positions), ignoring all rotational dynamics. This
simplification:

- **Reduces computational complexity** - Faster simulations for initial design studies
- **Focuses on trajectory** - Ideal for apogee predictions and flight path analysis
- **Simplifies model setup** - Requires fewer input parameters than full 6-DOF

When to Use 3-DOF Simulations
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

3-DOF simulations are appropriate when:

- You need quick trajectory estimates during preliminary design
- Rotational stability is not a concern (e.g., highly stable rockets)
- You're performing educational demonstrations
- You want to validate basic flight performance before detailed analysis

.. warning::

    3-DOF simulations **do not** account for:

    - Rocket rotation and attitude dynamics
    - Stability margin and center of pressure effects
    - Aerodynamic moments and angular motion
    - Fin effectiveness and control surfaces

    For complete flight analysis including stability, use standard 6-DOF simulations.

Setting Up a 3-DOF Simulation
------------------------------

A 3-DOF simulation requires three main components:

1. :class:`rocketpy.PointMassMotor` - Motor without rotational inertia
2. :class:`rocketpy.PointMassRocket` - Rocket without rotational properties
3. :class:`rocketpy.Flight` with ``simulation_mode="3 DOF"``

Step 1: Define the Environment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The environment setup is identical to standard simulations:

.. jupyter-execute::

    from rocketpy import Environment

    env = Environment(
        latitude=32.990254,
        longitude=-106.974998,
        elevation=1400
    )

    env.set_atmospheric_model(type="StandardAtmosphere")

Step 2: Create a PointMassMotor
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The :class:`rocketpy.PointMassMotor` class represents a motor as a point mass,
without rotational inertia or grain geometry:

.. jupyter-execute::

    from rocketpy import PointMassMotor

    # Using a thrust curve file
    motor = PointMassMotor(
        thrust_source="../data/motors/cesaroni/Cesaroni_M1670.eng",
        dry_mass=1.815,
        propellant_initial_mass=2.5,
    )

You can also define a constant thrust profile:

.. jupyter-execute::

    # Constant thrust of 250 N for 3 seconds
    motor_constant = PointMassMotor(
        thrust_source=250,
        dry_mass=1.0,
        propellant_initial_mass=0.5,
        burn_time=3.0,
    )

Or use a custom thrust function:

.. jupyter-execute::

    def custom_thrust(t):
        """Custom thrust profile: ramps up, plateaus, then ramps down"""
        if t < 0.5:
            return 500 * t / 0.5  # Ramp up
        elif t < 2.5:
            return 500  # Plateau
        elif t < 3.0:
            return 500 * (3.0 - t) / 0.5  # Ramp down
        else:
            return 0

    motor_custom = PointMassMotor(
        thrust_source=custom_thrust,
        dry_mass=1.2,
        propellant_initial_mass=0.6,
        burn_time=3.0,
    )

.. seealso::

    For detailed information about :class:`rocketpy.PointMassMotor` parameters,
    see the :ref:`API reference <api_reference>`.

Step 3: Create a PointMassRocket
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The :class:`rocketpy.PointMassRocket` class represents a rocket as a point mass:

.. jupyter-execute::

    from rocketpy import PointMassRocket

    rocket = PointMassRocket(
        radius=0.0635,  # meters
        mass=5.0,  # kg (dry mass without motor)
        center_of_mass_without_motor=0.0,
        power_off_drag=0.5,  # Constant drag coefficient
        power_on_drag=0.5,
    )

    # Add the motor
    rocket.add_motor(motor, position=0)

You can also specify drag as a function of Mach number:

.. jupyter-execute::

    # Drag coefficient vs Mach number
    drag_curve = [
        [0.0, 0.50],
        [0.5, 0.48],
        [0.9, 0.52],
        [1.1, 0.65],
        [2.0, 0.55],
        [3.0, 0.50],
    ]

    rocket_with_drag_curve = PointMassRocket(
        radius=0.0635,
        mass=5.0,
        center_of_mass_without_motor=0.0,
        power_off_drag=drag_curve,
        power_on_drag=drag_curve,
    )

.. note::

    Unlike the standard :class:`rocketpy.Rocket` class, :class:`rocketpy.PointMassRocket`
    does **not** support:

    - Aerodynamic surfaces (fins, nose cones)
    - Inertia tensors
    - Center of pressure calculations
    - Stability margin analysis

Step 4: Run the Simulation
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Create a :class:`rocketpy.Flight` object with ``simulation_mode="3 DOF"``:

.. jupyter-execute::

    from rocketpy import Flight

    flight = Flight(
        rocket=rocket,
        environment=env,
        rail_length=5.2,
        inclination=85,  # degrees from horizontal
        heading=0,  # degrees (0 = North, 90 = East)
        simulation_mode="3 DOF",
        max_time=100,
        terminate_on_apogee=False,
    )

.. important::

    The ``simulation_mode="3 DOF"`` parameter is **required** to enable 3-DOF mode.
    Without it, RocketPy will attempt a full 6-DOF simulation and may fail with
    :class:`rocketpy.PointMassRocket`.

Analyzing Results
-----------------

Once the simulation is complete, you can access trajectory data and generate plots.

Trajectory Information
^^^^^^^^^^^^^^^^^^^^^^

View key flight metrics:

.. jupyter-execute::

    flight.info()

This will display:

- Apogee altitude and time
- Maximum velocity
- Flight time
- Landing position

Plotting Trajectory
^^^^^^^^^^^^^^^^^^^

Visualize the 3D flight path:

.. jupyter-execute::

    flight.plots.trajectory_3d()

.. note::

    In 3-DOF mode, the rocket maintains a fixed orientation (no pitch, yaw, or roll),
    so attitude plots are not meaningful.

Available Plots
^^^^^^^^^^^^^^^

The following plots are available for 3-DOF simulations:

.. jupyter-execute::

    # Altitude vs time
    flight.z.plot()

    # Velocity components
    flight.vx.plot()
    flight.vy.plot()
    flight.vz.plot()

    # Total velocity
    flight.speed.plot()

    # Acceleration
    flight.ax.plot()

Export Data
^^^^^^^^^^^

Export trajectory data to CSV:

.. jupyter-execute::

    from rocketpy.simulation import FlightDataExporter

    exporter = FlightDataExporter(flight)
    exporter.export_data(
        "trajectory_3dof.csv",
        "x",
        "y",
        "z",
        "vx",
        "vy",
        "vz",
    )

Complete Example
----------------

Here's a complete 3-DOF simulation from start to finish:

.. jupyter-execute::

    from rocketpy import Environment, PointMassMotor, PointMassRocket, Flight

    # 1. Environment
    env = Environment(
        latitude=39.3897,
        longitude=-8.2889,
        elevation=100
    )
    env.set_atmospheric_model(type="StandardAtmosphere")

    # 2. Motor
    motor = PointMassMotor(
        thrust_source=1500,  # Constant 1500 N thrust
        dry_mass=2.0,
        propellant_initial_mass=3.0,
        burn_time=4.0,
    )

    # 3. Rocket
    rocket = PointMassRocket(
        radius=0.0635,
        mass=8.0,
        center_of_mass_without_motor=0.0,
        power_off_drag=0.45,
        power_on_drag=0.45,
    )
    rocket.add_motor(motor, position=0)

    # 4. Simulate
    flight = Flight(
        rocket=rocket,
        environment=env,
        rail_length=5.2,
        inclination=85,
        heading=0,
        simulation_mode="3 DOF",
        max_time=120,
    )

    # 5. Results
    print(f"Apogee: {flight.apogee:.2f} m")
    print(f"Max velocity: {flight.max_speed:.2f} m/s")
    print(f"Flight time: {flight.t_final:.2f} s")

    flight.plots.trajectory_3d()

Weathercocking Model
--------------------

RocketPy's 3-DOF simulation mode includes a weathercocking model that allows
the rocket's attitude to evolve during flight. This feature simulates how a
statically stable rocket naturally aligns with the relative wind direction.

Understanding Weathercocking
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Weathercocking is the tendency of a rocket to align its body axis with the
direction of the relative wind. In reality, this occurs due to aerodynamic
restoring moments from fins and other stabilizing surfaces. The 3-DOF
weathercocking model provides a simplified representation of this behavior
without requiring full 6-DOF rotational dynamics.

The ``weathercock_coeff`` Parameter
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The weathercocking behavior is controlled by the ``weathercock_coeff`` parameter
in the :class:`rocketpy.Flight` class:

.. jupyter-execute::

    from rocketpy import Environment, PointMassMotor, PointMassRocket, Flight

    env = Environment(
        latitude=32.990254,
        longitude=-106.974998,
        elevation=1400
    )
    env.set_atmospheric_model(type="StandardAtmosphere")

    motor = PointMassMotor(
        thrust_source=1500,
        dry_mass=1.5,
        propellant_initial_mass=2.5,
        burn_time=3.5,
    )

    rocket = PointMassRocket(
        radius=0.078,
        mass=15.0,
        center_of_mass_without_motor=0.0,
        power_off_drag=0.43,
        power_on_drag=0.43,
    )
    rocket.add_motor(motor, position=0)

    # Flight with weathercocking enabled
    flight = Flight(
        rocket=rocket,
        environment=env,
        rail_length=4.2,
        inclination=85,
        heading=45,
        simulation_mode="3 DOF",
        weathercock_coeff=1.0,  # Default value
    )

    print(f"Apogee: {flight.apogee - env.elevation:.2f} m")

The ``weathercock_coeff`` parameter controls the rate at which the rocket
aligns with the relative wind:

- ``weathercock_coeff=0``: No weathercocking (original fixed-attitude behavior)
- ``weathercock_coeff=1.0``: Default moderate alignment rate
- ``weathercock_coeff>1.0``: Faster alignment (more stable rocket)

Effect of Weathercocking Coefficient
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Higher values of ``weathercock_coeff`` result in faster alignment with the
relative wind. This affects the lateral motion and impact point:

.. list-table:: Weathercocking Coefficient Effects
   :header-rows: 1
   :widths: 25 25 50

   * - Coefficient
     - Alignment Speed
     - Typical Use Case
   * - 0
     - None (fixed attitude)
     - Original 3-DOF behavior
   * - 1.0
     - Moderate
     - Default, general purpose
   * - 2.0-5.0
     - Fast
     - Highly stable rockets
   * - >5.0
     - Very fast
     - Rockets with large fins

Example Comparison Notebook
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For a comprehensive comparison of 3-DOF vs 6-DOF simulations with different
weathercocking coefficients, see the example notebook:

:doc:`../examples/bella_lui_3dof_vs_6dof_comparison`

This notebook demonstrates:

- **Performance comparison**: 3-DOF is 5-7x faster than 6-DOF
- **Accuracy analysis**: Apogee predictions within 1.5% of 6-DOF
- **Weathercocking effects**: How different coefficients affect trajectory
- **Impact point predictions**: Comparison of landing locations

Comparison: 3-DOF vs 6-DOF
---------------------------

Understanding the differences between simulation modes:

.. list-table:: 3-DOF vs 6-DOF Comparison
   :header-rows: 1
   :widths: 30 35 35

   * - Feature
     - 3-DOF
     - 6-DOF
   * - Computational Speed
     - 5-7x faster
     - Slower (more accurate)
   * - Rocket Orientation
     - Weathercocking model
     - Full attitude dynamics
   * - Stability Analysis
     - ❌ Not available
     - ✅ Full stability margin
   * - Aerodynamic Surfaces
     - ❌ Not modeled
     - ✅ Fins, nose, tail
   * - Center of Pressure
     - ❌ Not computed
     - ✅ Computed
   * - Moments of Inertia
     - ❌ Not needed
     - ✅ Required
   * - Use Cases
     - Quick estimates, Monte Carlo
     - Detailed design, stability
   * - Trajectory Accuracy
     - Good (~1.5% error)
     - Highly accurate

Best Practices
--------------

1. **Validate with 6-DOF**: After getting initial results with 3-DOF, validate
   critical designs with full 6-DOF simulations.

2. **Check Drag Coefficient**: Ensure your drag coefficient is realistic for
   your rocket's geometry. Use wind tunnel data or CFD if available.

3. **Use Realistic Launch Conditions**: Even in 3-DOF mode, wind conditions
   and rail length affect trajectory.

4. **Document Assumptions**: Clearly document that your analysis uses 3-DOF
   and its limitations.

Limitations and Warnings
------------------------

.. danger::

    **Critical Limitations:**

    - **No stability checking** - The simulation cannot detect unstable rockets
    - **No attitude control** - Air brakes and thrust vectoring are not supported
    - **Simplified weathercocking** - Uses proportional alignment model, not full dynamics

.. warning::

    3-DOF simulations should **not** be used for:

    - Final design verification
    - Stability margin analysis
    - Control system design
    - Fin sizing and optimization
    - Safety-critical trajectory predictions

See Also
--------

- :ref:`First Simulation <firstsimulation>` - Standard 6-DOF simulation tutorial
- :ref:`Rocket Class Usage <rocketusage>` - Full rocket modeling capabilities
- :ref:`Flight Class Usage <flightusage>` - Complete flight simulation options
- :doc:`../examples/bella_lui_3dof_vs_6dof_comparison` - 3-DOF vs 6-DOF comparison with weathercocking

Further Reading
---------------

For more information about point mass trajectory simulations:

- `Trajectory Optimization <https://en.wikipedia.org/wiki/Trajectory_optimization>`_
- `Equations of Motion <https://en.wikipedia.org/wiki/Equations_of_motion>`_
- `Point Mass Model <https://www.grc.nasa.gov/www/k-12/airplane/flteqs.html>`_
