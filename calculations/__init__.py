"""Berechnungsmodule für Erdwärmesonden."""

from .borehole import BoreholeCalculator
from .thermal import ThermalResistanceCalculator
from .g_functions import GFunctionCalculator
from .hydraulics import HydraulicsCalculator
from .vdi4640 import VDI4640Calculator
from .longterm_simulation import LongtermSimulator, LongtermSimulationResult
from .regeneration_analysis import (
    calculate_thermal_balance, check_ground_depletion,
    calculate_optimal_balance, ThermalBalanceResult, DepletionWarning,
)
from .seasonal_efficiency import (
    SeasonalEfficiencyCalculator, calculate_monthly_cop,
    calculate_jaz, calculate_monthly_efficiency,
    compare_jaz_by_depth, MonthlyEfficiency, JAZComparisonResult,
)

try:
    from .borefield_gfunction import BorefieldGFunction
except ImportError:
    BorefieldGFunction = None  # pygfunction optional

__all__ = [
    'BoreholeCalculator',
    'ThermalResistanceCalculator', 
    'GFunctionCalculator',
    'HydraulicsCalculator',
    'VDI4640Calculator',
    'BorefieldGFunction',
    # Langzeit-Simulation (V3.4 Phase 3)
    'LongtermSimulator',
    'LongtermSimulationResult',
    'calculate_thermal_balance',
    'check_ground_depletion',
    'calculate_optimal_balance',
    'ThermalBalanceResult',
    'DepletionWarning',
    'SeasonalEfficiencyCalculator',
    'calculate_monthly_cop',
    'calculate_jaz',
    'calculate_monthly_efficiency',
    'compare_jaz_by_depth',
    'MonthlyEfficiency',
    'JAZComparisonResult',
]









