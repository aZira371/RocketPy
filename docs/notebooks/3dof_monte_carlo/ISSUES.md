# Issues and Limitations: 3-DOF Monte Carlo Simulations

## Executive Summary

This document highlights the **current limitations** discovered when attempting to use Monte Carlo simulations with 3-DOF (point mass) rocket models in RocketPy.

**Key Finding**: While 3-DOF simulations work perfectly for deterministic flight analysis, **Monte Carlo simulations with 3-DOF have significant limitations** due to missing stochastic wrapper classes.

## Issues Identified

### 1. No StochasticPointMassRocket Class

**Problem**: There is no stochastic wrapper for the `PointMassRocket` class.

**Impact**:
- Cannot randomize rocket parameters (mass, drag, radius, etc.) in Monte Carlo
- Attempting to use `StochasticRocket` with `PointMassRocket` fails
- Users must pass the regular (non-stochastic) rocket to Monte Carlo

**Error Message**:
```python
AttributeError: 'PointMassRocket' object has no attribute 'create_object'
```

**Code that fails**:
```python
from rocketpy.stochastic import StochasticRocket

rocket = PointMassRocket(...)  # Create point mass rocket

# This will fail in Monte Carlo:
stochastic_rocket = StochasticRocket(
    rocket=rocket,
    mass=(5.0, 0.5, 'normal'),  # Try to randomize mass
)

mc = MonteCarlo(
    filename="test",
    environment=stochastic_env,
    rocket=stochastic_rocket,  # Will cause error
    flight=stochastic_flight,
)

mc.simulate(number_of_simulations=10)  # AttributeError
```

**Root Cause**:
- `MonteCarlo` expects stochastic objects with a `create_object()` method
- `StochasticRocket` wraps regular `Rocket` class, not `PointMassRocket`
- There is no `StochasticPointMassRocket` implementation

### 2. No StochasticPointMassMotor Class

**Problem**: There is no stochastic wrapper for the `PointMassMotor` class.

**Impact**:
- Cannot randomize motor parameters (thrust, burn time, impulse, mass) in Monte Carlo
- Must use deterministic motor in all 3-DOF Monte Carlo simulations
- Limits uncertainty quantification capabilities

**Missing functionality**:
```python
# This class does not exist:
from rocketpy.stochastic import StochasticPointMassMotor  # ImportError

motor = PointMassMotor(
    thrust_source=500,
    dry_mass=1.5,
    propellant_initial_mass=2.0,
    burn_time=3.5,
)

# Cannot create stochastic version:
stochastic_motor = StochasticPointMassMotor(  # Not implemented
    motor=motor,
    thrust_source=(500, 50, 'normal'),
    burn_time=(3.5, 0.2, 'normal'),
    # etc.
)
```

### 3. Limited Monte Carlo Capabilities for 3-DOF

**Problem**: Only flight parameters can be randomized in 3-DOF Monte Carlo.

**What works** ✅:
- Launch inclination angle
- Launch heading/azimuth
- Rail length
- Environmental conditions (with `StochasticEnvironment`)

**What doesn't work** ❌:
- Rocket mass variations
- Rocket drag coefficient variations
- Rocket geometry variations
- Motor thrust variations
- Motor burn time variations
- Motor total impulse variations
- Motor mass variations

**Impact**:
- 3-DOF Monte Carlo is limited to launch/environmental uncertainty
- Cannot perform comprehensive uncertainty quantification
- Must use 6-DOF for parameter uncertainty studies

## Working Approach

The **current recommended approach** for 3-DOF Monte Carlo:

```python
from rocketpy import Environment
from rocketpy.motors.point_mass_motor import PointMassMotor
from rocketpy.rocket.point_mass_rocket import PointMassRocket
from rocketpy.simulation.flight import Flight
from rocketpy.simulation import MonteCarlo
from rocketpy.stochastic import StochasticEnvironment, StochasticFlight

# Create deterministic components
env = Environment(...)
env.set_atmospheric_model(type='standard_atmosphere')

motor = PointMassMotor(
    thrust_source=500,
    dry_mass=1.5,
    propellant_initial_mass=2.0,
    burn_time=3.5,
)

rocket = PointMassRocket(
    radius=0.0635,
    mass=5.0,
    center_of_mass_without_motor=0.0,
    power_off_drag=0.5,
    power_on_drag=0.5,
)
rocket.add_motor(motor, position=0.0)

# Create nominal flight
flight = Flight(
    rocket=rocket,
    environment=env,
    rail_length=5.0,
    inclination=84,
    heading=90,
    simulation_mode='3 DOF',
)

# Create stochastic objects (only env and flight)
stochastic_env = StochasticEnvironment(environment=env)

stochastic_flight = StochasticFlight(
    flight=flight,
    rail_length=(5.0, 0.1, 'normal'),
    inclination=(84, 2.0, 'normal'),
    heading=(90, 3.0, 'normal'),
)

# Monte Carlo - pass regular rocket (not stochastic)
mc = MonteCarlo(
    filename="mc_3dof",
    environment=stochastic_env,
    rocket=rocket,  # Regular rocket, not stochastic
    flight=stochastic_flight,
)

# Run simulations
mc.simulate(number_of_simulations=100)
```

## Attempted Workarounds

### Workaround 1: Use StochasticRocket with PointMassRocket

**Attempt**: Try to use `StochasticRocket` directly with `PointMassRocket`.

**Result**: ❌ **Fails** with `AttributeError`

**Reason**: `StochasticRocket` expects a regular `Rocket` object, not `PointMassRocket`.

### Workaround 2: Use Regular Rocket and Force 3-DOF Mode

**Attempt**: Use a full `Rocket` with `StochasticRocket`, then force `simulation_mode='3 DOF'`.

**Result**: ⚠️ **Partially works** but defeats the purpose

**Issues**:
- Requires creating a full 6-DOF rocket model
- Adds unnecessary complexity
- Loses the simplicity of point mass models
- Still slower than true 3-DOF
- Defeats the purpose of using `PointMassRocket`

### Workaround 3: Manual Parameter Variation Loop

**Attempt**: Manually vary parameters in a loop instead of using Monte Carlo class.

**Result**: ✅ **Works** but loses Monte Carlo features

**Code**:
```python
import numpy as np

results = []
for i in range(num_simulations):
    # Manually sample parameters
    mass = np.random.normal(5.0, 0.5)
    thrust = np.random.normal(500, 50)
    
    # Create new objects each iteration
    motor_i = PointMassMotor(thrust_source=thrust, ...)
    rocket_i = PointMassRocket(mass=mass, ...)
    rocket_i.add_motor(motor_i, position=0.0)
    
    flight_i = Flight(rocket=rocket_i, ...)
    
    # Store results
    results.append({
        'apogee': flight_i.apogee,
        'x_impact': flight_i.x_impact,
        'y_impact': flight_i.y_impact,
        # etc.
    })
```

**Issues**:
- Verbose and error-prone
- Loses Monte Carlo class features (logging, plotting, analysis)
- No automatic parallelization
- Must manually implement statistical analysis
- Not integrated with existing tools

## Recommended Use Cases for 3-DOF Monte Carlo

Despite limitations, 3-DOF Monte Carlo is valuable for:

### ✅ Good Use Cases

1. **Launch Uncertainty Studies**
   - Inclination angle variations (rail misalignment)
   - Heading/azimuth variations
   - Rail length uncertainties

2. **Environmental Sensitivity**
   - Wind uncertainty analysis
   - Atmospheric condition variations
   - Landing zone prediction

3. **Quick Dispersion Estimates**
   - Fast computation (5-10x speedup)
   - Large sample sizes (100s-1000s of sims)
   - Preliminary risk assessment

4. **Educational Purposes**
   - Demonstrating Monte Carlo concepts
   - Simplified uncertainty analysis
   - Fast feedback for learning

### ❌ Not Suitable For

1. **Comprehensive Uncertainty Quantification**
   - Cannot vary rocket parameters
   - Cannot vary motor parameters
   - Limited to launch/environmental factors

2. **Parameter Sensitivity Studies**
   - Cannot assess impact of mass uncertainty
   - Cannot assess impact of thrust variations
   - Cannot assess impact of drag uncertainty

3. **Design Optimization Under Uncertainty**
   - Requires varying design parameters
   - Needs full parameter space exploration

For these cases, **use 6-DOF Monte Carlo** with full `Rocket` and `Motor` classes.

## Impact Assessment

### Current Impact on Users

**Low to Moderate**:
- 3-DOF simulations work fine for deterministic cases
- Monte Carlo with launch/environmental uncertainty works
- Clear workaround exists (use 6-DOF for parameter uncertainty)

### Potential Impact if Fixed

**High Value**:
- Enable fast Monte Carlo with full parameter uncertainty
- 5-10x speedup for large Monte Carlo studies
- Better integration with existing stochastic framework
- More consistent API across rocket types

## Proposed Solutions

### Solution 1: Implement StochasticPointMassRocket (Recommended)

Create a new class similar to `StochasticRocket`:

```python
# In rocketpy/stochastic/stochastic_point_mass_rocket.py

class StochasticPointMassRocket(StochasticModel):
    """Stochastic wrapper for PointMassRocket."""
    
    def __init__(
        self,
        rocket,  # PointMassRocket instance
        radius=None,
        mass=None,
        center_of_mass_without_motor=None,
        power_off_drag=None,
        power_on_drag=None,
    ):
        # Initialize with parameter distributions
        super().__init__(rocket, ...)
    
    def create_object(self):
        """Create randomized PointMassRocket instance."""
        generated_dict = next(self.dict_generator())
        
        return PointMassRocket(
            radius=generated_dict['radius'],
            mass=generated_dict['mass'],
            center_of_mass_without_motor=generated_dict['center_of_mass_without_motor'],
            power_off_drag=generated_dict['power_off_drag'],
            power_on_drag=generated_dict['power_on_drag'],
        )
```

**Benefits**:
- Consistent with existing stochastic classes
- Integrates seamlessly with Monte Carlo
- Enables full parameter uncertainty
- Maintains 3-DOF speed advantage

### Solution 2: Implement StochasticPointMassMotor

Create a new class for motor uncertainty:

```python
# In rocketpy/stochastic/stochastic_point_mass_motor.py

class StochasticPointMassMotor(StochasticModel):
    """Stochastic wrapper for PointMassMotor."""
    
    def __init__(
        self,
        motor,  # PointMassMotor instance
        thrust_source=None,
        dry_mass=None,
        propellant_initial_mass=None,
        burn_time=None,
    ):
        # Initialize with parameter distributions
        super().__init__(motor, ...)
    
    def create_object(self):
        """Create randomized PointMassMotor instance."""
        generated_dict = next(self.dict_generator())
        
        return PointMassMotor(
            thrust_source=generated_dict['thrust_source'],
            dry_mass=generated_dict['dry_mass'],
            propellant_initial_mass=generated_dict['propellant_initial_mass'],
            burn_time=generated_dict['burn_time'],
        )
```

### Solution 3: Update Monte Carlo to Handle Point Mass Models

Modify `MonteCarlo` class to detect and handle point mass rockets:

```python
# In rocketpy/simulation/monte_carlo.py

def __run_single_simulation(self):
    # Check if rocket is PointMassRocket
    if isinstance(self.rocket, PointMassRocket):
        # Handle point mass case
        rocket = self.rocket  # Use as-is, no create_object()
    else:
        # Handle regular rocket case
        rocket = self.rocket.create_object()
    
    # Continue with simulation...
```

**Note**: This is a temporary fix and less ideal than implementing proper stochastic classes.

## Testing Recommendations

If implementing the proposed solutions, test the following:

1. **Basic functionality**
   - Create stochastic point mass rocket/motor
   - Verify parameter randomization
   - Check `create_object()` method

2. **Monte Carlo integration**
   - Run small Monte Carlo (10 sims)
   - Run larger Monte Carlo (100 sims)
   - Verify results logging
   - Check parallel execution

3. **Statistical validity**
   - Verify distributions match input specifications
   - Check mean and std deviation of results
   - Compare with manual loop approach

4. **Performance**
   - Measure speedup vs 6-DOF
   - Verify no significant overhead
   - Test with various sample sizes

## Documentation Needs

If implementing these classes, update:

1. **API Documentation**
   - Add to stochastic module docs
   - Document all parameters
   - Provide usage examples

2. **User Guide**
   - Add section on 3-DOF Monte Carlo
   - Explain when to use vs 6-DOF
   - Show complete workflow

3. **Example Notebooks**
   - Update existing notebooks
   - Remove limitation warnings
   - Add full parameter uncertainty examples

4. **Migration Guide**
   - For users currently using workarounds
   - Show before/after code
   - Explain benefits

## Conclusion

**Current State**:
- 3-DOF deterministic simulations work perfectly ✅
- 3-DOF Monte Carlo with launch/environmental uncertainty works ✅
- 3-DOF Monte Carlo with rocket/motor parameter uncertainty does NOT work ❌

**Recommendation for Users**:
- Use 3-DOF Monte Carlo for launch/environmental studies
- Use 6-DOF Monte Carlo for comprehensive parameter uncertainty
- Wait for implementation of stochastic point mass classes for full capability

**Recommendation for Developers**:
- Implement `StochasticPointMassRocket` and `StochasticPointMassMotor`
- Follow existing stochastic class patterns
- Maintain backward compatibility
- Add comprehensive tests and documentation

## References

- See `docs/notebooks/3dof_monte_carlo/02_monte_carlo_with_3dof.ipynb` for detailed examples
- See `docs/notebooks/3dof_monte_carlo/README.md` for overview
- See `rocketpy/stochastic/` directory for existing stochastic class implementations
- See `tests/integration/simulation/test_flight_3dof.py` for 3-DOF test examples
