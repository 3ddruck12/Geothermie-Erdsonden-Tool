import pytest
import math
from calculations.longterm_simulation import LongtermSimulator, LongtermSimulationResult

def test_longterm_simulator_runs_25_years():
    sim = LongtermSimulator()
    
    monthly_heating = [1000.0] * 12  # kWh
    monthly_cooling = [200.0] * 12   # kWh
    
    result = sim.simulate(
        ground_thermal_conductivity=2.0,
        ground_heat_capacity=2.4e6,
        undisturbed_ground_temp=10.0,
        geothermal_gradient=0.03,
        borehole_depth=100.0,
        borehole_diameter=0.152,
        borehole_resistance=0.1,
        monthly_heating_kwh=monthly_heating,
        monthly_cooling_kwh=monthly_cooling,
        cop_heating=4.0,
        eer_cooling=4.0,
        delta_t_fluid=3.0,
        simulation_years=25,
        max_years=25,
        n_boreholes=1
    )
    
    assert isinstance(result, LongtermSimulationResult)
    assert result.years == 25
    assert len(result.monthly_fluid_temps) == 25
    assert len(result.monthly_fluid_temps[0]) == 12
    assert len(result.annual_fluid_temp_min) == 25
    assert len(result.annual_energy_extraction) == 25
    
    # Fluid temperatures should decrease over time if heating dominated
    total_heating = sum(monthly_heating) * (1 - 1/4.0)
    total_cooling = sum(monthly_cooling) * (1 + 1/4.0)
    if total_heating > total_cooling:
        assert result.annual_fluid_temp_min[-1] < result.annual_fluid_temp_min[0]

def test_simulation_cap_at_max_years():
    sim = LongtermSimulator()
    result = sim.simulate(
        ground_thermal_conductivity=2.0,
        ground_heat_capacity=2.4e6,
        undisturbed_ground_temp=10.0,
        borehole_depth=100.0,
        simulation_years=60, # Requesting 60
        max_years=25       # Capped at 25
    )
    assert result.years == 25

def test_pure_cooling_increases_temperature():
    sim = LongtermSimulator()
    monthly_heating = [0.0] * 12
    monthly_cooling = [1000.0] * 12 # pure cooling
    
    result = sim.simulate(
        ground_thermal_conductivity=2.0,
        ground_heat_capacity=2.4e6,
        undisturbed_ground_temp=10.0,
        borehole_depth=100.0,
        monthly_heating_kwh=monthly_heating,
        monthly_cooling_kwh=monthly_cooling,
        simulation_years=5
    )
    
    assert result.annual_fluid_temp_max[-1] > result.annual_fluid_temp_max[0]
