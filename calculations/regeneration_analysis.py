"""Regenerations-Analyse für Erdwärmesonden.

Analysiert die thermische Balance zwischen Wärmeentzug (Heizen)
und Wärmeeintrag (Kühlen) und warnt bei langfristiger Auskühlung.
"""

import math
import logging
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class ThermalBalanceResult:
    """Ergebnis der thermischen Bilanzierung."""
    # Pro Jahr: Wärmeentzug und Wärmeeintrag [kWh]
    annual_extraction: List[float] = field(default_factory=list)
    annual_injection: List[float] = field(default_factory=list)
    # Netto-Bilanz pro Jahr [kWh] (positiv = Netto-Entzug)
    annual_net_balance: List[float] = field(default_factory=list)
    # Kumulierte Bilanz [kWh]
    cumulative_balance: List[float] = field(default_factory=list)
    # Verhältnis Entzug / Eintrag (>1 = Überwiegt Heizen)
    imbalance_ratio: float = 0.0
    # Gesamter Entzug / Eintrag über alle Jahre
    total_extraction: float = 0.0
    total_injection: float = 0.0


@dataclass
class DepletionWarning:
    """Warnung bei Auskühlung des Erdreichs."""
    is_warning: bool = False
    warning_level: str = ""   # "info", "warning", "critical"
    message: str = ""
    # Temperatur-Trend [K/Dekade]
    temperature_trend: float = 0.0
    # Min. Fluid-Temperatur im letzten Simulationsjahr
    final_year_min_temp: float = 0.0
    # Min. Fluid-Temperatur im ersten Simulationsjahr
    first_year_min_temp: float = 0.0


def calculate_thermal_balance(
    annual_extraction: List[float],
    annual_injection: List[float],
) -> ThermalBalanceResult:
    """Berechnet die thermische Bilanz über die Simulationsdauer.

    Args:
        annual_extraction: Jährlicher Wärmeentzug [kWh] pro Jahr
        annual_injection: Jährlicher Wärmeeintrag [kWh] pro Jahr

    Returns:
        ThermalBalanceResult
    """
    n_years = min(len(annual_extraction), len(annual_injection))

    result = ThermalBalanceResult(
        annual_extraction=annual_extraction[:n_years],
        annual_injection=annual_injection[:n_years],
    )

    cumulative = 0.0
    for i in range(n_years):
        net = annual_extraction[i] - annual_injection[i]
        result.annual_net_balance.append(round(net, 1))
        cumulative += net
        result.cumulative_balance.append(round(cumulative, 1))

    result.total_extraction = sum(annual_extraction[:n_years])
    result.total_injection = sum(annual_injection[:n_years])

    if result.total_injection > 0:
        result.imbalance_ratio = round(
            result.total_extraction / result.total_injection, 2
        )
    else:
        result.imbalance_ratio = float('inf') if result.total_extraction > 0 else 1.0

    return result


def check_ground_depletion(
    annual_fluid_temp_min: List[float],
    warning_threshold: float = -3.0,
    trend_threshold: float = 0.5,
) -> DepletionWarning:
    """Prüft auf langfristige Auskühlung des Erdreichs.

    Args:
        annual_fluid_temp_min: Min. Fluid-Temperatur pro Jahr [°C]
        warning_threshold: Absolute Warngrenze [°C]
        trend_threshold: Max. erlaubter Abkühltrend [K/Dekade]

    Returns:
        DepletionWarning
    """
    if not annual_fluid_temp_min or len(annual_fluid_temp_min) < 2:
        return DepletionWarning()

    n_years = len(annual_fluid_temp_min)
    first_min = annual_fluid_temp_min[0]
    final_min = annual_fluid_temp_min[-1]

    # Temperatur-Trend (lineare Regression)
    x = list(range(n_years))
    x_mean = sum(x) / n_years
    y_mean = sum(annual_fluid_temp_min) / n_years

    numerator = sum((x[i] - x_mean) * (annual_fluid_temp_min[i] - y_mean)
                    for i in range(n_years))
    denominator = sum((x[i] - x_mean) ** 2 for i in range(n_years))

    if denominator > 0:
        slope = numerator / denominator  # K/Jahr
        trend_per_decade = slope * 10  # K/Dekade
    else:
        trend_per_decade = 0.0

    warning = DepletionWarning(
        temperature_trend=round(trend_per_decade, 3),
        final_year_min_temp=round(final_min, 2),
        first_year_min_temp=round(first_min, 2),
    )

    # Absolut-Grenze
    if final_min < warning_threshold:
        warning.is_warning = True
        warning.warning_level = "critical"
        warning.message = (
            f"⚠️ KRITISCH: Min. Fluid-Temperatur im letzten Jahr "
            f"({final_min:.1f}°C) unterschreitet Grenzwert "
            f"({warning_threshold:.1f}°C). "
            f"Risiko: Frostschäden, Effizienzverlust."
        )
    # Trend-Grenze (negativer Trend = Abkühlung)
    elif trend_per_decade < -trend_threshold:
        warning.is_warning = True
        warning.warning_level = "warning"
        warning.message = (
            f"⚠️ WARNUNG: Abkühltrend von {abs(trend_per_decade):.2f} K/Dekade "
            f"detektiert. Temperatur sinkt von {first_min:.1f}°C auf "
            f"{final_min:.1f}°C. "
            f"Empfehlung: Kühlanteil erhöhen oder Solarregeneration prüfen."
        )
    # Leichte Abkühlung
    elif trend_per_decade < -0.1:
        warning.is_warning = True
        warning.warning_level = "info"
        warning.message = (
            f"ℹ️ INFO: Leichter Abkühltrend von "
            f"{abs(trend_per_decade):.2f} K/Dekade. "
            f"Aktuell unkritisch, aber langfristig beobachten."
        )

    return warning


def calculate_optimal_balance(
    simulate_func: callable,
    base_params: dict,
    monthly_heating_kwh: List[float],
    max_cooling_fraction: float = 1.0,
    tolerance: float = 0.3,
    max_iterations: int = 20,
) -> Tuple[float, float]:
    """Berechnet den optimalen Kühlanteil für Langzeitstabilität.

    Verwendet Bisection, um den Kühlanteil zu finden, bei dem die
    Min-Temperatur im letzten Jahr ≈ Min-Temperatur im ersten Jahr ist.

    Args:
        simulate_func: Funktion die LongtermSimulationResult liefert
        base_params: Basisparameter für simulate_func
        monthly_heating_kwh: 12 monatliche Heizwerte [kWh]
        max_cooling_fraction: Maximaler Kühlanteil (1.0 = 100% des Heizbedarfs)
        tolerance: Toleranz [K]
        max_iterations: Max. Iterationen

    Returns:
        Tuple (optimaler Kühlanteil [0..1], resultierende Temperatur-Drift [K])
    """
    total_heating = sum(monthly_heating_kwh)
    if total_heating <= 0:
        return 0.0, 0.0

    # Standard-Kühlprofil (Sommer)
    cooling_profile = [
        0.0, 0.0, 0.0, 0.05, 0.15, 0.25,
        0.30, 0.25, 0.0, 0.0, 0.0, 0.0
    ]

    low, high = 0.0, max_cooling_fraction

    for _ in range(max_iterations):
        mid = (low + high) / 2

        # Kühlbedarf = Anteil × Heizbedarf
        cooling_kwh = [total_heating * mid * f for f in cooling_profile]

        params = dict(base_params)
        params['monthly_heating_kwh'] = monthly_heating_kwh
        params['monthly_cooling_kwh'] = cooling_kwh

        result = simulate_func(**params)

        if len(result.annual_fluid_temp_min) < 2:
            return mid, 0.0

        drift = (result.annual_fluid_temp_min[-1]
                 - result.annual_fluid_temp_min[0])

        if abs(drift) < tolerance:
            return round(mid, 3), round(drift, 3)

        if drift < 0:
            # Noch zu viel Auskühlung → mehr Kühlung/Eintrag nötig
            low = mid
        else:
            # Überschuss → weniger Kühlung
            high = mid

    return round((low + high) / 2, 3), round(drift, 3)
