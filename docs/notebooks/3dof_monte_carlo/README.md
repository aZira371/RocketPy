# 3-DOF Monte Carlo Simulations with RocketPy

This directory contains example Jupyter notebooks demonstrating the use of 3-DOF (3 Degrees of Freedom) rocket trajectory simulations with Monte Carlo analysis in RocketPy.

## Overview

3-DOF simulations provide a simplified, faster alternative to 6-DOF simulations by modeling the rocket as a point mass without rotational dynamics. This makes them ideal for:
- Quick trajectory analysis
- Monte Carlo uncertainty studies (100s-1000s of simulations)
- Preliminary design and optimization
- Landing zone prediction
- Educational purposes

## Notebooks

### 01_introduction_to_3dof.ipynb
**Introduction to 3-DOF Rocket Simulations**

This notebook provides a comprehensive introduction to 3-DOF simulations using RocketPy's `PointMassRocket` and `PointMassMotor` classes.

**Topics covered:**
- What is 3-DOF simulation and when to use it
- Creating point mass motors and rockets
- Running basic 3-DOF flight simulations
- Analyzing and visualizing results
- Parameter sensitivity studies
- Performance advantages

**Learning objectives:**
- Understand the difference between 3-DOF and 6-DOF
- Learn to set up and run 3-DOF simulations
- Interpret 3-DOF simulation results
- Perform quick parametric studies

### 02_monte_carlo_with_3dof.ipynb
**Monte Carlo Analysis with 3-DOF Simulations**

This notebook demonstrates Monte Carlo uncertainty analysis using 3-DOF simulations and **documents current limitations**.

**Topics covered:**
- Monte Carlo basics with 3-DOF
- Working approach: Flight parameter variations
- Statistical analysis and visualization
- Landing dispersion ellipses
- **Current limitations and issues**

**Important findings:**
- ✅ **What works**: Varying flight parameters (inclination, heading, rail length)
- ✅ **What works**: Environmental variations with `StochasticEnvironment`
- ⚠️ **Current limitation**: Cannot vary rocket/motor parameters with `PointMassRocket`
- ⚠️ **Issue**: No `StochasticPointMassRocket` class exists
- ⚠️ **Issue**: Using `StochasticRocket` with `PointMassRocket` raises `AttributeError`

**Recommended use cases:**
- Launch angle/heading uncertainty studies
- Wind sensitivity analysis
- Landing zone prediction
- Quick trajectory dispersion studies

### 03_advanced_3dof_use_cases.ipynb
**Advanced 3-DOF Features and Use Cases**

This notebook explores advanced features unique to 3-DOF simulations and demonstrates practical applications.

**Topics covered:**
- Weathercock coefficient for quasi-static attitude dynamics
- Wind effects on simplified trajectories
- Monte Carlo with environmental uncertainties
- Performance comparison: 3-DOF vs 6-DOF
- Design optimization using 3-DOF speed advantage

**Features demonstrated:**
- `weathercock_coeff` parameter for attitude alignment
- Landing ellipse generation
- Computational speedup quantification (5-10x faster)
- Constraint-based optimization examples

## Current Limitations with 3-DOF Monte Carlo

### Issues Identified

1. **No StochasticPointMassRocket class**
   - The stochastic module does not include a wrapper for `PointMassRocket`
   - Attempting to use `StochasticRocket` with `PointMassRocket` fails
   - Error: `AttributeError: 'PointMassRocket' object has no attribute 'create_object'`

2. **Limited parameter randomization**
   - Cannot vary rocket mass, drag, or inertia in Monte Carlo
   - Cannot vary motor thrust, burn time, or impulse in Monte Carlo
   - Only flight parameters (launch conditions) can be randomized

3. **Workarounds are not ideal**
   - Could use regular `Rocket` with `StochasticRocket` and force 3-DOF mode
   - This defeats the purpose of using simplified point mass models
   - Adds complexity and removes the advantage of 3-DOF

### What Works Well

Despite these limitations, 3-DOF Monte Carlo is highly effective for:

✅ **Launch parameter uncertainty**
- Inclination angle variations
- Heading/azimuth variations
- Rail length uncertainties

✅ **Environmental studies**
- Wind uncertainty (with `StochasticEnvironment`)
- Atmospheric condition variations
- Landing dispersion analysis

✅ **Fast computation**
- 5-10x faster than 6-DOF
- Enables 100s to 1000s of simulations
- Perfect for statistical studies

## Recommendations

### For Users

1. **Use 3-DOF Monte Carlo for:**
   - Launch site uncertainty analysis
   - Wind drift studies
   - Landing zone predictions
   - Quick dispersion estimates
   - Educational demonstrations

2. **Use 6-DOF Monte Carlo when:**
   - Rocket/motor parameter uncertainties are important
   - Rotational dynamics affect the outcome
   - High-fidelity results are required
   - Comprehensive uncertainty quantification is needed

3. **Workflow suggestion:**
   - Start with 3-DOF for rapid initial studies
   - Use 6-DOF for detailed final analysis
   - Combine both for efficient design iteration

### For Developers

To fully enable 3-DOF Monte Carlo, the following enhancements could be implemented:

1. **Create `StochasticPointMassRocket` class**
   - Similar to `StochasticRocket` but for `PointMassRocket`
   - Allow randomization of: mass, radius, drag coefficients, center of mass
   - Integrate with existing stochastic framework

2. **Create `StochasticPointMassMotor` class**
   - Similar to `StochasticSolidMotor` but for `PointMassMotor`
   - Allow randomization of: thrust, burn time, masses, total impulse
   - Support both constant and curve-based thrust sources

3. **Update `MonteCarlo` class**
   - Detect point mass models automatically
   - Handle both regular and point mass stochastic objects
   - Maintain backward compatibility

4. **Add documentation**
   - Document 3-DOF Monte Carlo capabilities and limitations
   - Provide examples of valid use cases
   - Clarify when to use 3-DOF vs 6-DOF

## Installation

To run these notebooks, install RocketPy with Monte Carlo dependencies:

```bash
pip install rocketpy[monte-carlo]
```

Or install from the repository:

```bash
pip install -e .[monte-carlo,tests]
```

## Requirements

- Python >= 3.10
- RocketPy >= 1.11.0
- matplotlib
- numpy
- scipy
- multiprocess (for parallel Monte Carlo)
- statsmodels (for statistical analysis)

## Usage

1. Clone the repository
2. Install dependencies
3. Launch Jupyter:
   ```bash
   jupyter notebook
   ```
4. Navigate to `docs/notebooks/3dof_monte_carlo/`
5. Open and run the notebooks in order

## Key Concepts

### 3-DOF vs 6-DOF

| Feature | 3-DOF | 6-DOF |
|---------|-------|-------|
| **State variables** | Position (x, y, z) + Velocity (vx, vy, vz) | + Orientation + Angular velocity |
| **Rotational dynamics** | ❌ Not modeled | ✅ Full dynamics |
| **Attitude tracking** | ❌ No | ✅ Yes |
| **Computational speed** | ⚡ Fast (5-10x) | 🐢 Slower |
| **Use case** | Quick studies, Monte Carlo | Detailed analysis |
| **Rocket class** | `PointMassRocket` | `Rocket` |
| **Motor class** | `PointMassMotor` | `SolidMotor`, `HybridMotor`, etc. |

### Weathercock Coefficient

The `weathercock_coeff` parameter enables quasi-static weathercocking in 3-DOF:

- **Value**: Rate coefficient in rad/s
- **Effect**: Aligns rocket body axis with relative wind direction
- **Formula**: Angular velocity = `weathercock_coeff * sin(misalignment_angle)`
- **Default**: 0.0 (no weathercocking, fixed attitude)
- **Typical range**: 0.0 to 2.0 rad/s

Higher values cause faster alignment with the wind, affecting trajectory and drift.

## Performance Benchmarks

Based on testing in notebook 03:

- **3-DOF**: ~0.02-0.04 seconds per simulation
- **6-DOF**: ~0.10-0.20 seconds per simulation
- **Speedup**: 5-10x faster
- **Monte Carlo**: 100 simulations in ~3-5 seconds (3-DOF) vs ~15-25 seconds (6-DOF)

These numbers vary with simulation complexity, integration settings, and hardware.

## Contributing

If you encounter issues or have suggestions for improving 3-DOF Monte Carlo support:

1. Check existing issues on GitHub
2. Review the limitations documented in notebook 02
3. Consider contributing:
   - `StochasticPointMassRocket` implementation
   - `StochasticPointMassMotor` implementation
   - Additional examples or use cases
   - Documentation improvements

## License

These notebooks are part of the RocketPy project and are distributed under the MIT License.

## Authors

- Example notebooks created for RocketPy documentation
- Based on RocketPy framework by the RocketPy Team

## References

- [RocketPy Documentation](https://docs.rocketpy.org/)
- [RocketPy GitHub Repository](https://github.com/RocketPy-Team/RocketPy)
- [Monte Carlo Simulation Theory](https://en.wikipedia.org/wiki/Monte_Carlo_method)
- [Degrees of Freedom in Mechanics](https://en.wikipedia.org/wiki/Degrees_of_freedom_(mechanics))

## Version History

- **v1.0** (2024-12): Initial creation with three example notebooks
  - Basic 3-DOF introduction
  - Monte Carlo with limitations documentation
  - Advanced features and use cases
