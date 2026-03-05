import pytest
from calculations.regeneration_analysis import (
    calculate_thermal_balance,
    check_ground_depletion,
    calculate_optimal_balance
)

def test_thermal_balance():
    extraction = [100.0, 100.0, 100.0]
    injection = [50.0, 50.0, 50.0]
    
    balance = calculate_thermal_balance(extraction, injection)
    
    assert balance.total_extraction == 300.0
    assert balance.total_injection == 150.0
    assert balance.imbalance_ratio == pytest.approx(2.0)
    assert balance.cumulative_balance[-1] == 150.0  # (300 - 150)

def test_ground_depletion_warning():
    # Depleting case but hasn't hit absolute threshold yet
    temps = [5.0, 4.0, 3.0, 2.0, 1.0, 0.0]
    warn = check_ground_depletion(temps, warning_threshold=-2.0, trend_threshold=0.5)
    # The trend is -10.0 K/decade, so it SHOULD be a warning!
    assert warn.is_warning == True 
    assert warn.warning_level == 'warning'
    assert warn.temperature_trend == -10.0

    temps_critical = [5.0, 2.0, -1.0, -3.0]
    warn2 = check_ground_depletion(temps_critical, warning_threshold=-2.0)
    assert warn2.is_warning == True
    assert warn2.warning_level == 'critical'

def test_optimal_balance():
    # Mock simulate function
    class MockResult:
        def __init__(self, temps):
            self.annual_fluid_temp_min = temps
            
    def mock_simulate(monthly_heating_kwh, monthly_cooling_kwh):
        # We need more cooling to stop drift. Drift is heating - cooling
        heating = sum(monthly_heating_kwh)
        cooling = sum(monthly_cooling_kwh)
        drift = -1.0 * (heating - cooling)
        # If drift is negative, it's cooling down (first > last)
        return MockResult([10.0, 10.0 + drift])
        
    optimal, drift = calculate_optimal_balance(
        mock_simulate,
        base_params={},
        monthly_heating_kwh=[100.0] * 12, # 1200 total
        max_cooling_fraction=1.0,
        tolerance=0.5
    )
    # Optimal cooling should be close to heating (1.0 fraction)
    assert optimal > 0.0
    assert abs(drift) < 0.5
