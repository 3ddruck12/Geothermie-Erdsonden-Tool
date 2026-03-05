import pytest
from calculations.seasonal_efficiency import (
    calculate_monthly_cop,
    calculate_jaz,
    SeasonalEfficiencyCalculator
)

def test_carnot_cop_is_valid():
    cop = SeasonalEfficiencyCalculator.calculate_cop_carnot(t_source=5.0, t_sink=35.0, cop_nominal=4.0)
    # The actual physical Carnot COP for 5->35 (absolute 278.15 to 308.15)
    # is 308.15 / 30.0 = 10.27
    # So the model should return something reasonable relative to cop_nominal
    assert cop > 0.0

def test_monthly_cop_calculation():
    monthly_fluid_temps = [2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 7.0, 6.0, 5.0, 4.0, 3.0]
    
    # Using linear model
    cops_linear = calculate_monthly_cop(
        monthly_fluid_temps, 
        cop_nominal=4.0, 
        method='linear'
    )
    assert len(cops_linear) == 12
    # Linear model is cop_nominal * (1 + 0.04 * t_fluid)
    assert cops_linear[0] == pytest.approx(4.0 * (1 + 0.04 * 2.0))
    
    # Using carnot model (for background)
    cops_carnot = calculate_monthly_cop(
        monthly_fluid_temps, 
        cop_nominal=4.0, 
        method='carnot'
    )
    assert len(cops_carnot) == 12

def test_jaz_calculation():
    monthly_cops = [4.0] * 12
    monthly_heating = [100.0] * 12
    
    # JAZ with constant COP 4.0 and equal heating should just be 4.0
    jaz = calculate_jaz(monthly_cops, monthly_heating)
    assert jaz == pytest.approx(4.0)
    
    # With 0 heating, jaz should return 0 or another fallback
    jaz_zero = calculate_jaz([4.0]*12, [0.0]*12)
    assert jaz_zero == 0.0

def test_monthly_efficiency():
    from calculations.seasonal_efficiency import calculate_monthly_efficiency
    
    monthly_temps = [2.0] * 12
    monthly_heating = [100.0] * 12
    
    # Just checking it doesn't crash and returns the correct class
    result = calculate_monthly_efficiency(monthly_temps, monthly_heating, cop_nominal=4.0)
    assert hasattr(result, "jaz")
    assert hasattr(result, "cop_values")
    assert len(result.cop_values) == 12
