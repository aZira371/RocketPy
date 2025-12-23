"""Unit tests for the Parachute class, specifically focusing on trigger mechanisms."""

import pytest

from rocketpy import Parachute


class TestParachuteTriggers:
    """Test class for parachute trigger functionality."""

    def test_apogee_trigger(self):
        """Test that the 'apogee' trigger is correctly parsed and works."""
        parachute = Parachute(
            name="test_apogee",
            cd_s=1.0,
            trigger="apogee",
            sampling_rate=100,
            lag=0,
        )
        
        # Test trigger function with descending velocity (should trigger)
        state_descending = [0, 0, 1000, 0, 0, -10, 1, 0, 0, 0, 0, 0, 0]
        assert parachute.triggerfunc(101325, 1000, state_descending, [], 5.0, None) is True
        
        # Test trigger function with ascending velocity (should not trigger)
        state_ascending = [0, 0, 1000, 0, 0, 10, 1, 0, 0, 0, 0, 0, 0]
        assert parachute.triggerfunc(101325, 1000, state_ascending, [], 3.0, None) is False

    def test_altitude_trigger(self):
        """Test that altitude-based trigger works correctly."""
        parachute = Parachute(
            name="test_altitude",
            cd_s=1.0,
            trigger=500.0,  # 500 meters
            sampling_rate=100,
            lag=0,
        )
        
        # Test at altitude above trigger point with descending velocity (should not trigger)
        state_above = [0, 0, 1000, 0, 0, -10, 1, 0, 0, 0, 0, 0, 0]
        assert parachute.triggerfunc(101325, 600, state_above, [], 10.0, None) is False
        
        # Test at altitude below trigger point with descending velocity (should trigger)
        state_below = [0, 0, 1000, 0, 0, -10, 1, 0, 0, 0, 0, 0, 0]
        assert parachute.triggerfunc(101325, 400, state_below, [], 15.0, None) is True
        
        # Test at altitude below trigger point with ascending velocity (should not trigger)
        state_ascending = [0, 0, 1000, 0, 0, 10, 1, 0, 0, 0, 0, 0, 0]
        assert parachute.triggerfunc(101325, 400, state_ascending, [], 2.0, None) is False

    def test_launch_plus_delay_trigger_parsing(self):
        """Test that 'launch + X' trigger string is correctly parsed."""
        parachute = Parachute(
            name="test_launch_delay",
            cd_s=1.0,
            trigger="launch + 5",
            sampling_rate=100,
            lag=0,
        )
        
        # Check that the parachute was created successfully
        assert parachute.name == "test_launch_delay"
        assert parachute.trigger == "launch + 5"

    def test_launch_plus_delay_trigger_functionality(self):
        """Test that 'launch + X' trigger works correctly."""
        delay = 5.0
        parachute = Parachute(
            name="test_launch_delay",
            cd_s=1.0,
            trigger=f"launch + {delay}",
            sampling_rate=100,
            lag=0,
        )
        
        state = [0, 0, 1000, 0, 0, -10, 1, 0, 0, 0, 0, 0, 0]
        
        # Before delay time - should not trigger
        assert parachute.triggerfunc(101325, 1000, state, [], 3.0, None) is False
        
        # Exactly at delay time - should trigger
        assert parachute.triggerfunc(101325, 1000, state, [], 5.0, None) is True
        
        # After delay time - should trigger
        assert parachute.triggerfunc(101325, 1000, state, [], 7.0, None) is True

    def test_burnout_plus_delay_trigger_parsing(self):
        """Test that 'burnout + X' trigger string is correctly parsed."""
        parachute = Parachute(
            name="test_burnout_delay",
            cd_s=1.0,
            trigger="burnout + 3.5",
            sampling_rate=100,
            lag=0,
        )
        
        # Check that the parachute was created successfully
        assert parachute.name == "test_burnout_delay"
        assert parachute.trigger == "burnout + 3.5"

    def test_burnout_plus_delay_trigger_functionality(self):
        """Test that 'burnout + X' trigger works correctly."""
        # Create a mock rocket with motor
        class MockMotor:
            def __init__(self, burn_out_time):
                self.burn_out_time = burn_out_time
        
        class MockRocket:
            def __init__(self, burn_out_time):
                self.motor = MockMotor(burn_out_time)
        
        delay = 3.5
        burnout_time = 2.0
        parachute = Parachute(
            name="test_burnout_delay",
            cd_s=1.0,
            trigger=f"burnout + {delay}",
            sampling_rate=100,
            lag=0,
        )
        
        rocket = MockRocket(burnout_time)
        state = [0, 0, 1000, 0, 0, -10, 1, 0, 0, 0, 0, 0, 0]
        
        # Before burnout + delay - should not trigger
        assert parachute.triggerfunc(101325, 1000, state, [], 4.0, rocket) is False
        
        # Exactly at burnout + delay - should trigger
        assert parachute.triggerfunc(101325, 1000, state, [], 5.5, rocket) is True
        
        # After burnout + delay - should trigger
        assert parachute.triggerfunc(101325, 1000, state, [], 10.0, rocket) is True

    def test_launch_trigger_with_whitespace(self):
        """Test that whitespace in trigger string is handled correctly."""
        parachute1 = Parachute(
            name="test1",
            cd_s=1.0,
            trigger="launch + 5",
            sampling_rate=100,
            lag=0,
        )
        
        parachute2 = Parachute(
            name="test2",
            cd_s=1.0,
            trigger="  launch  +  5  ",
            sampling_rate=100,
            lag=0,
        )
        
        parachute3 = Parachute(
            name="test3",
            cd_s=1.0,
            trigger="LAUNCH + 5",
            sampling_rate=100,
            lag=0,
        )
        
        state = [0, 0, 1000, 0, 0, -10, 1, 0, 0, 0, 0, 0, 0]
        
        # All should behave the same way
        assert parachute1.triggerfunc(101325, 1000, state, [], 6.0, None) is True
        assert parachute2.triggerfunc(101325, 1000, state, [], 6.0, None) is True
        assert parachute3.triggerfunc(101325, 1000, state, [], 6.0, None) is True

    def test_invalid_trigger_format(self):
        """Test that invalid trigger formats raise appropriate errors."""
        # Invalid string without '+'
        with pytest.raises(ValueError, match="Unable to set the trigger function"):
            Parachute(
                name="test",
                cd_s=1.0,
                trigger="invalid_trigger",
                sampling_rate=100,
                lag=0,
            )
        
        # Invalid event name
        with pytest.raises(ValueError, match="Invalid time-based trigger event"):
            Parachute(
                name="test",
                cd_s=1.0,
                trigger="invalid_event + 5",
                sampling_rate=100,
                lag=0,
            )
        
        # Invalid delay value (not a number)
        with pytest.raises(ValueError, match="Invalid delay value"):
            Parachute(
                name="test",
                cd_s=1.0,
                trigger="launch + not_a_number",
                sampling_rate=100,
                lag=0,
            )
        
        # Invalid format (multiple '+')
        with pytest.raises(ValueError, match="Invalid time-based trigger format"):
            Parachute(
                name="test",
                cd_s=1.0,
                trigger="launch + 5 + 3",
                sampling_rate=100,
                lag=0,
            )

    def test_decimal_delay_values(self):
        """Test that decimal delay values work correctly."""
        parachute = Parachute(
            name="test_decimal",
            cd_s=1.0,
            trigger="launch + 2.75",
            sampling_rate=100,
            lag=0,
        )
        
        state = [0, 0, 1000, 0, 0, -10, 1, 0, 0, 0, 0, 0, 0]
        
        # Just before delay - should not trigger
        assert parachute.triggerfunc(101325, 1000, state, [], 2.74, None) is False
        
        # At and after delay - should trigger
        assert parachute.triggerfunc(101325, 1000, state, [], 2.75, None) is True
        assert parachute.triggerfunc(101325, 1000, state, [], 3.0, None) is True

    def test_custom_callable_trigger_backward_compatibility(self):
        """Test that custom callable triggers still work with backward compatibility."""
        # 3-parameter trigger (old style)
        def old_trigger(p, h, y):
            return y[5] < 0 and h < 800
        
        parachute_old = Parachute(
            name="test_old",
            cd_s=1.0,
            trigger=old_trigger,
            sampling_rate=100,
            lag=0,
        )
        
        # 4-parameter trigger (with sensors)
        def new_trigger(p, h, y, sensors):
            return y[5] < 0 and h < 800
        
        parachute_new = Parachute(
            name="test_new",
            cd_s=1.0,
            trigger=new_trigger,
            sampling_rate=100,
            lag=0,
        )
        
        state = [0, 0, 1000, 0, 0, -10, 1, 0, 0, 0, 0, 0, 0]
        
        # Both should work with the new 6-parameter signature
        assert parachute_old.triggerfunc(101325, 700, state, [], 10.0, None) is True
        assert parachute_new.triggerfunc(101325, 700, state, [], 10.0, None) is True
        
        # Should not trigger above altitude
        assert parachute_old.triggerfunc(101325, 900, state, [], 10.0, None) is False
        assert parachute_new.triggerfunc(101325, 900, state, [], 10.0, None) is False

    def test_zero_delay_trigger(self):
        """Test that zero delay triggers work correctly."""
        parachute = Parachute(
            name="test_zero",
            cd_s=1.0,
            trigger="launch + 0",
            sampling_rate=100,
            lag=0,
        )
        
        state = [0, 0, 1000, 0, 0, -10, 1, 0, 0, 0, 0, 0, 0]
        
        # Should trigger immediately at t=0
        assert parachute.triggerfunc(101325, 1000, state, [], 0.0, None) is True
        
        # Should also trigger at any positive time
        assert parachute.triggerfunc(101325, 1000, state, [], 0.1, None) is True
