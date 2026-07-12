# These lines are here for debugging purposes only

from rocketpy import (
    CylindricalTank,
    Environment,
    Flight,
    Fluid,
    Function,
    LiquidMotor,
    MassBasedTank,
    Rocket,
    UllageBasedTank,
)
# Define and set up LOX volume
lox_volume_liters = Function(
    "../../data/rockets/berkeley/test124_Lox_Volume.csv",
    extrapolation="zero",
    inputs="Time (s)",
    outputs="Volume (L)",
)
lox_volume = lox_volume_liters * 0.001  # Convert to m^3
lox_volume.set_discrete(8.003, 19.984, 40, interpolation="linear")
lox_volume.set_outputs("Volume (m³)")
lox_volume.set_title("LOX Volume")

# Plot LOX volume
lox_volume.plot(force_data=True)

# Define and set up LOX tank ullage
lox_tank_ullage = 0.013167926436231077 - lox_volume
lox_tank_ullage.set_title("LOX Tank Ullage")
lox_tank_ullage.set_outputs("Ullage volume (m³)")

# Plot LOX tank ullage
lox_tank_ullage.plot(8, 20, force_data=True)
# Define and set up Propane volume
propane_volume_liters = Function(
    "../../data/rockets/berkeley/test124_Propane_Volume.csv",
    inputs="Time (s)",
    outputs="Volume (L)",
)
propane_volume = propane_volume_liters * 0.001  # Convert to m^3
propane_volume.set_discrete(8.003, 19.984, 40, interpolation="linear")
propane_volume.set_outputs("Volume (m³)")

# Plot Propane volume
propane_volume.plot(force_data=True)

# Define and set up Propane tank ullage
propane_tank_ullage = 0.013167926436231077 - propane_volume
propane_tank_ullage.set_title("Propane Tank Ullage")
propane_tank_ullage.set_outputs("Ullage volume (m³)")

# Plot Propane tank ullage
propane_tank_ullage.plot(force_data=True)
# Define fluids
lox = Fluid(name="LOX", density=1024)
propane = Fluid(name="Propane", density=566)

# Define pressurizing gases with their respective pressures
lox_tank_pressurizing_gas = Fluid(name="N2", density=31.3 / 28)  # 450 PSI
propane_tank_pressurizing_gas = Fluid(
    name="N2", density=313 * 300 / 4500 / 28
)  # 300 PSI
pressurizing_gas = Fluid(name="N2", density=300)  # 4500 PSI
lox_tank_geometry = CylindricalTank(0.0744, 0.8068, spherical_caps=True)
lox_tank = UllageBasedTank(
    name="LOX Tank",
    flux_time=(8, 20),
    geometry=lox_tank_geometry,
    gas=lox_tank_pressurizing_gas,
    liquid=lox,
    ullage=lox_tank_ullage,
)
lox_tank.fluid_mass()
lox_tank.net_mass_flow_rate()
lox_tank.liquid_height()
lox_tank.gas_height()
lox_tank.center_of_mass()
lox_tank.inertia()
propane_tank_geometry = CylindricalTank(0.0744, 0.8068, spherical_caps=True)
propane_tank = UllageBasedTank(
    name="Propane Tank",
    flux_time=(8, 20),
    geometry=propane_tank_geometry,
    gas=propane_tank_pressurizing_gas,
    liquid=propane,
    ullage=propane_tank_ullage,
)
propane_tank.fluid_mass()
propane_tank.net_mass_flow_rate()
propane_tank.liquid_height()
propane_tank.gas_height()
propane_tank.center_of_mass()
propane_tank.inertia()
pressure_tank_geometry = CylindricalTank(0.135 / 2, 0.981, spherical_caps=True)
pressure_tank = MassBasedTank(
    name="Pressure Tank",
    geometry=pressure_tank_geometry,
    liquid_mass=0,
    flux_time=(8, 20),
    gas_mass="../../data/rockets/berkeley/pressurantMassFiltered.csv",
    gas=pressurizing_gas,
    liquid=pressurizing_gas,
)
pressure_tank.fluid_mass()
pressure_tank.net_mass_flow_rate()
pressure_tank.liquid_height()
pressure_tank.gas_height()
pressure_tank.center_of_mass()
pressure_tank.inertia()
liquid_motor = LiquidMotor(
    thrust_source="../../data/rockets/berkeley/test124_Thrust_Curve.csv",
    center_of_dry_mass_position=0,
    dry_inertia=(0, 0, 0),
    dry_mass=0,
    burn_time=(8, 20),
    nozzle_radius=0.069 / 2,
    nozzle_position=-1.364,
    coordinate_system_orientation="nozzle_to_combustion_chamber",
)

liquid_motor.add_tank(propane_tank, position=-0.6446)
liquid_motor.add_tank(lox_tank, position=1.1144)
liquid_motor.add_tank(pressure_tank, position=2.4975)
liquid_motor.all_info()
berkeley_rocket = Rocket(
    radius=0.098,
    mass=63.4,
    inertia=(25, 25, 1),
    power_off_drag="../../data/rockets/berkeley/drag.csv",
    power_on_drag="../../data/rockets/berkeley/drag.csv",
    center_of_mass_without_motor=3.23,
    coordinate_system_orientation="nose_to_tail",
)
berkeley_rocket.add_motor(liquid_motor, position=4.2)
nose = berkeley_rocket.add_nose(length=0.7, kind="vonKarman", position=0)
tail = berkeley_rocket.add_tail(
    top_radius=0.098, bottom_radius=0.058, length=0.198, position=5.69 - 0.198
)

fins = berkeley_rocket.add_trapezoidal_fins(
    n=4,
    root_chord=0.355,
    tip_chord=0.0803,
    span=0.156,
    position=5.25,
    cant_angle=0,
)
berkeley_rocket.all_info()
env = Environment(latitude=35.347122986338356, longitude=-117.80893423073582)

env.set_date((2022, 12, 3, 14 + 7, 0, 0))  # UTC

env.set_atmospheric_model(
    type="custom_atmosphere",
    pressure=None,
    temperature=None,
    wind_u=[(0, 1), (500, 0), (1000, 5), (2500, 5.0), (5000, 10)],
    wind_v=[(0, 0), (500, 3), (1600, 2), (2500, -3), (5000, 10)],
)
env.info()
test_flight = Flight(
    rocket=berkeley_rocket,
    environment=env,
    rail_length=18.28,
    inclination=90,
    heading=23,
    max_time_step=0.1,
    terminate_on_apogee=True,
)
test_flight.angle_of_attack.plot(test_flight.out_of_rail_time, 15)
test_flight.all_info()
