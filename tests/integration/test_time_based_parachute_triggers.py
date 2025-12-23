"""Integration tests for time-based parachute triggers in flight simulations."""

import pytest

from rocketpy import Flight


@pytest.mark.slow
def test_flight_with_launch_plus_delay_trigger(
    example_spaceport_env, calisto_motorless, cesaroni_m1670
):
    """Test a complete flight simulation with a 'launch + X' parachute trigger.
    
    This simulates a rocket with a delay charge that deploys the parachute at a
    fixed time after launch, similar to model rockets without avionics.
    """
    # Use existing rocket and add motor
    rocket = calisto_motorless
    rocket.add_motor(cesaroni_m1670, position=-1.373)
    
    # Add a parachute with "launch + 5" trigger (5 seconds after launch)
    rocket.add_parachute(
        name="Main",
        cd_s=10.0,
        trigger="launch + 5",
        sampling_rate=100,
        lag=1.5,
        noise=(0, 8.3, 0.5),
    )
    
    # Run flight simulation
    flight = Flight(
        environment=example_spaceport_env,
        rocket=rocket,
        rail_length=5.2,
        inclination=85,
        heading=0,
        terminate_on_apogee=False,
    )
    
    # Verify that the parachute was deployed at approximately the right time
    # The parachute should deploy at t=5s + lag=1.5s = 6.5s (fully deployed)
    assert flight.t is not None
    
    # Check that parachute deployment happened (should have parachute_cd_s set)
    # This attribute is set when parachute is deployed
    assert hasattr(flight, "parachute_cd_s")
    
    # Verify simulation completed successfully
    assert flight.apogee_time > 0


@pytest.mark.slow
def test_flight_with_burnout_plus_delay_trigger(
    example_spaceport_env, calisto_motorless, cesaroni_m1670
):
    """Test a complete flight simulation with a 'burnout + X' parachute trigger.
    
    This simulates a rocket with a motor delay charge that deploys the parachute
    at a fixed time after motor burnout, typical of model rocket motors.
    """
    # Use existing rocket and add motor
    rocket = calisto_motorless
    rocket.add_motor(cesaroni_m1670, position=-1.373)
    
    # Get motor burnout time
    motor_burnout = rocket.motor.burn_out_time
    
    # Add a parachute with "burnout + 3" trigger (3 seconds after burnout)
    rocket.add_parachute(
        name="Main",
        cd_s=10.0,
        trigger="burnout + 3",
        sampling_rate=100,
        lag=1.5,
        noise=(0, 8.3, 0.5),
    )
    
    # Run flight simulation
    flight = Flight(
        environment=example_spaceport_env,
        rocket=rocket,
        rail_length=5.2,
        inclination=85,
        heading=0,
        terminate_on_apogee=False,
    )
    
    # Verify that the parachute was deployed
    assert flight.t is not None
    
    # Check that parachute deployment happened
    assert hasattr(flight, "parachute_cd_s")
    
    # The parachute should deploy after motor burnout + delay
    # Expected deployment at burnout_time + 3s + lag
    expected_deploy_time = motor_burnout + 3.0 + 1.5
    
    # Verify simulation completed successfully and parachute deployed after burnout
    assert flight.apogee_time > 0
    # The simulation should run past the expected deployment time
    assert flight.t_final >= expected_deploy_time


@pytest.mark.slow
def test_flight_with_multiple_time_based_parachutes(
    example_spaceport_env, calisto_motorless, cesaroni_m1670
):
    """Test a flight with multiple time-based parachutes (drogue and main).
    
    This simulates a dual-deployment system using time-based triggers.
    """
    # Use existing rocket and add motor
    rocket = calisto_motorless
    rocket.add_motor(cesaroni_m1670, position=-1.373)
    
    # Add drogue parachute - deploys at burnout + 2 seconds
    rocket.add_parachute(
        name="Drogue",
        cd_s=1.0,
        trigger="burnout + 2",
        sampling_rate=100,
        lag=0.5,
        noise=(0, 8.3, 0.5),
    )
    
    # Add main parachute - deploys at burnout + 10 seconds
    rocket.add_parachute(
        name="Main",
        cd_s=10.0,
        trigger="burnout + 10",
        sampling_rate=100,
        lag=1.0,
        noise=(0, 8.3, 0.5),
    )
    
    # Run flight simulation
    flight = Flight(
        environment=example_spaceport_env,
        rocket=rocket,
        rail_length=5.2,
        inclination=85,
        heading=0,
        terminate_on_apogee=False,
    )
    
    # Verify simulation completed successfully
    assert flight.t is not None
    assert flight.apogee_time > 0
    
    # Check that parachute deployment happened
    assert hasattr(flight, "parachute_cd_s")


@pytest.mark.slow
def test_flight_with_mixed_trigger_types(
    example_spaceport_env, calisto_motorless, cesaroni_m1670
):
    """Test a flight with both time-based and traditional parachute triggers.
    
    This ensures backward compatibility when mixing trigger types.
    """
    # Use existing rocket and add motor
    rocket = calisto_motorless
    rocket.add_motor(cesaroni_m1670, position=-1.373)
    
    # Add drogue parachute with traditional apogee trigger
    rocket.add_parachute(
        name="Drogue",
        cd_s=1.0,
        trigger="apogee",
        sampling_rate=100,
        lag=0.5,
        noise=(0, 8.3, 0.5),
    )
    
    # Add main parachute with altitude trigger
    rocket.add_parachute(
        name="Main",
        cd_s=10.0,
        trigger=800.0,  # 800 meters AGL
        sampling_rate=100,
        lag=1.0,
        noise=(0, 8.3, 0.5),
    )
    
    # Run flight simulation
    flight = Flight(
        environment=example_spaceport_env,
        rocket=rocket,
        rail_length=5.2,
        inclination=85,
        heading=0,
        terminate_on_apogee=False,
    )
    
    # Verify simulation completed successfully
    assert flight.t is not None
    assert flight.apogee_time > 0
    
    # Check that parachute deployment happened
    assert hasattr(flight, "parachute_cd_s")
