import datetime as dt
from pathlib import Path

import rocketpy as rp
from rocketpy import (
    Attachment,
    Deployable,
    DeploymentEvent,
    Environment,
    FlightBody,
    IgnitionEvent,
    Mission,
    MissionExecutor,
    Parachute,
    Rocket,
    RocketAdapter,
    SolidMotor,
    Stage,
    StageSeparationEvent,
)
from rocketpy.plots.compare import CompareFlights
env = Environment(
    latitude=32.990254,
    longitude=-106.974998,
    elevation=1400,
    datum="WGS84",
)

tomorrow = dt.date.today() + dt.timedelta(days=1)
env.set_date((tomorrow.year, tomorrow.month, tomorrow.day, 12), timezone="UTC")
env.set_atmospheric_model(
    type="custom_atmosphere",
    pressure=101325,
    temperature=298.15,
    wind_u=[(0, 3.0), (2000, 5.0), (5000, 8.0)],
    wind_v=[(0, -1.0), (2000, -2.0), (5000, -3.5)],
)
env.max_expected_height = 10000
data_directory = Path(rp.__file__).resolve().parent.parent / "data"
motor_file = data_directory / "motors" / "cesaroni" / "Cesaroni_M1670.eng"
power_off_drag_file = data_directory / "rockets" / "calisto" / "powerOffDragCurve.csv"
power_on_drag_file = data_directory / "rockets" / "calisto" / "powerOnDragCurve.csv"

first_stage_motor = SolidMotor(
    thrust_source=str(motor_file),
    burn_time=3.9,
    dry_mass=1.815,
    dry_inertia=(0.125, 0.125, 0.002),
    center_of_dry_mass_position=0.317,
    nozzle_position=0,
    grain_number=5,
    grain_density=1815,
    nozzle_radius=33 / 1000,
    throat_radius=11 / 1000,
    grain_separation=5 / 1000,
    grain_outer_radius=33 / 1000,
    grain_initial_height=120 / 1000,
    grains_center_of_mass_position=0.397,
    grain_initial_inner_radius=15 / 1000,
    interpolation_method="linear",
    coordinate_system_orientation="nozzle_to_combustion_chamber",
)

second_stage_motor = SolidMotor(
    thrust_source=str(motor_file),
    burn_time=3.9,
    dry_mass=1.815,
    dry_inertia=(0.125, 0.125, 0.002),
    center_of_dry_mass_position=0.317,
    nozzle_position=0,
    grain_number=5,
    grain_density=1815,
    nozzle_radius=33 / 1000,
    throat_radius=11 / 1000,
    grain_separation=5 / 1000,
    grain_outer_radius=33 / 1000,
    grain_initial_height=120 / 1000,
    grains_center_of_mass_position=0.397,
    grain_initial_inner_radius=15 / 1000,
    interpolation_method="linear",
    coordinate_system_orientation="nozzle_to_combustion_chamber",
)

first_stage_rocket = Rocket(
    radius=0.0635,
    mass=14.426,
    inertia=(6.321, 6.321, 0.034),
    power_off_drag=str(power_off_drag_file),
    power_on_drag=str(power_on_drag_file),
    center_of_mass_without_motor=0,
    coordinate_system_orientation="tail_to_nose",
)
first_stage_rocket.name = "First Stage"
first_stage_rocket.add_motor(first_stage_motor, position=-1.255)
first_stage_rocket.set_rail_buttons(
    upper_button_position=0.0818,
    lower_button_position=-0.618,
    angular_position=45,
)
first_stage_rocket.add_nose(length=0.55829, kind="von karman", position=1.278)
first_stage_rocket.add_trapezoidal_fins(
    n=4,
    root_chord=0.120,
    tip_chord=0.060,
    span=0.110,
    position=-1.04956,
    cant_angle=0.5,
)
first_stage_rocket.add_tail(
    top_radius=0.0635,
    bottom_radius=0.0435,
    length=0.060,
    position=-1.194656,
)

second_stage_rocket = Rocket(
    radius=0.0635,
    mass=9.500,
    inertia=(6.321, 6.321, 0.034),
    power_off_drag=str(power_off_drag_file),
    power_on_drag=str(power_on_drag_file),
    center_of_mass_without_motor=0,
    coordinate_system_orientation="tail_to_nose",
)
second_stage_rocket.name = "Second Stage"
second_stage_rocket.add_motor(second_stage_motor, position=-1.000)
second_stage_rocket.add_nose(length=0.55829, kind="von karman", position=1.050)
second_stage_rocket.add_trapezoidal_fins(
    n=4,
    root_chord=0.120,
    tip_chord=0.060,
    span=0.110,
    position=-0.920,
    cant_angle=0.5,
)
second_stage_rocket.add_tail(
    top_radius=0.0635,
    bottom_radius=0.0435,
    length=0.060,
    position=-1.194656,
)

payload_body = FlightBody(
    name="Payload",
    geometry=0.055,
    mass_model=lambda t: 4.5,
    inertia_model=lambda t: (0.25, 0.25, 0.03, 0.0, 0.0, 0.0),
    center_of_mass_model=lambda t: 0.0,
    recovery_systems=[
        Parachute(
            name="Payload Drogue",
            cd_s=0.35,
            trigger="apogee",
            sampling_rate=105,
            lag=1.0,
            noise=(0, 4.0, 0.2),
        ),
        Parachute(
            name="Payload Main",
            cd_s=3.5,
            trigger=700,
            sampling_rate=105,
            lag=1.0,
            noise=(0, 4.0, 0.2),
        ),
    ],
    coordinate_system_orientation="tail_to_nose",
)
# Deploy second-stage parachute right after stage-2 motor burnout.
# Parachute trigger callbacks use (pressure, height_agl, state, sensors).
second_stage_rocket.add_parachute(
    "Second Stage Main",
    cd_s=5.0,
    trigger=lambda pressure, height_agl, state, sensors: state[0]
    >= second_stage_motor.burn_out_time and state[5] <= 0,
    sampling_rate=105,
    lag=1.2,
    noise=(0, 6.0, 0.25),
)

print(f"Using motor file: {motor_file}")
print(f"Using drag curve files: {power_off_drag_file.name}, {power_on_drag_file.name}")
print(f"Payload body type: {type(payload_body).__name__}")
print(f"Payload dry mass at t=0 s: {payload_body.mass(0):.2f} kg")
print(f"Payload recovery systems: {len(payload_body.recovery_systems())}")
mission = Mission(name="Calisto Two-Stage + Deployable Mission")

first_stage_attachment = Attachment(
    parent_frame_position=[0.0, 0.0, 0.0],
    child_frame_position=[0.0, 0.0, 0.0],
    constraints="rigid",
)

second_stage_attachment = Attachment(
    parent_frame_position=[0.0, 0.0, 0.85],
    child_frame_position=[0.0, 0.0, -0.45],
    constraints="rigid",
)

# In this tail_to_nose frame, z=0.55 m places the payload approximately
# halfway inserted into the first-stage airframe.
payload_attachment = Attachment(
    parent_frame_position=[0.0, 0.0, 0.55],
    child_frame_position=[0.0, 0.0, -0.30],
    constraints="rigid",
)

# In RocketPy state vectors, state[5] is vz (vertical velocity in m/s);
# vz <= 0 is used here as a descent/apogee crossing condition.
second_stage_sep = StageSeparationEvent(
    name="Second Stage Separation",
    trigger=lambda state, context: state[5] <= 0,
)
second_stage_ignition = IgnitionEvent(
    name="Second Stage Ignition",
    trigger=lambda state, context: state[5] <= 0,
)
payload_deploy_event = DeploymentEvent(
    name="Payload Deployment",
    trigger=lambda state, context: state[5] <= 0,
)

first_stage = Stage(
    name="first_stage",
    body=RocketAdapter(first_stage_rocket),
    attachment=first_stage_attachment,
)

second_stage = Stage(
    name="second_stage",
    body=RocketAdapter(second_stage_rocket),
    attachment=second_stage_attachment,
    separation_event=second_stage_sep,
    ignition_event=second_stage_ignition,
)

payload = Deployable(
    name="payload",
    body=payload_body,
    attachment=payload_attachment,
    deployment_event=payload_deploy_event,
)

mission.add_stage(first_stage)
mission.add_stage(second_stage)
mission.add_deployable(payload)
mission.set_flight_inputs(
    "first_stage",
    inclination=85,
    heading=20,
    terminate_on_apogee=True,
    max_time=240,
)

mission.set_flight_inputs(
    "second_stage",
    terminate_on_apogee=False,
    max_time=240,
)

mission.set_flight_inputs(
    "payload",
    terminate_on_apogee=False,
    max_time=700,
)

print("Mission Name:", mission.name)
print("Number of stages:", mission.number_of_stages)
print("Connection map:")
for item_name, metadata in mission.connection_map().items():
    print(f"  - {item_name}: {metadata}")
executor = MissionExecutor(
    mission=mission,
    environment=env,
    rail_length=5.2,
    default_flight_inputs={"time_overshoot": True},
)

results = executor.execute()
flights_by_name = {result.item_name: result.flight for result in results}

for result in results:
    print(
        f"{result.item_name}: apogee = {result.flight.apogee:.2f} m, "
        f"impact velocity = {result.flight.impact_velocity:.2f} m/s"
    )
comparison = CompareFlights(
    [
        flights_by_name["first_stage"],
        flights_by_name["second_stage"],
        flights_by_name["payload"],
    ]
)

comparison.trajectories_3d(legend=True)
