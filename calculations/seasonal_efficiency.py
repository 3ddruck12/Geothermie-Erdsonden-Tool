"""Saisonale Effizienz-Berechnung (SCOP/SEER/JAZ).

Berechnet temperatur- und teillastabhängige COP-Werte sowie
Jahresarbeitszahlen aus monatlichen Lastprofilen.

Desktop: Carnot-Modell nur in Langzeit-Simulation.
Cloud: Wird als vollständiger Effizienz-Rechner verwendet.
"""

import math
import logging
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple

logger = logging.getLogger(__name__)


@dataclass
class MonthlyEfficiency:
    """Monatliche Effizienzwerte."""
    month_names: List[str] = field(default_factory=lambda: [
        "Jan", "Feb", "Mär", "Apr", "Mai", "Jun",
        "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"
    ])
    cop_values: List[float] = field(default_factory=list)     # COP pro Monat
    loads_kwh: List[float] = field(default_factory=list)      # Last pro Monat [kWh]
    electricity_kwh: List[float] = field(default_factory=list) # Strom pro Monat [kWh]
    jaz: float = 0.0  # Jahresarbeitszahl


@dataclass
class JAZComparisonResult:
    """Vergleich der JAZ bei verschiedenen Sondentiefen."""
    depths: List[float] = field(default_factory=list)
    jaz_values: List[float] = field(default_factory=list)
    monthly_cop_per_depth: Dict[float, List[float]] = field(default_factory=dict)


class SeasonalEfficiencyCalculator:
    """Berechnet saisonale Effizienz (COP, JAZ) für Erdwärmesonden.

    Modelle:
    - 'linear': Einfache lineare Näherung (bestehendes Modell)
    - 'carnot': Physikalisch basiert auf Carnot-Wirkungsgrad
    - 'partload': Carnot + Teillastkorrekturen
    """

    # Typische Heizungs-Vorlauftemperatur [°C]
    DEFAULT_T_SINK = 35.0  # Fußbodenheizung

    @staticmethod
    def calculate_cop_linear(
        t_source: float,
        cop_nominal: float,
        t_source_nominal: float = 0.0,
    ) -> float:
        """Lineares COP-Modell (bestehendes Modell in diagrams_tab.py).

        COP = COP_nenn * (1 + 0.04 * (T_source - T_source_nenn))

        Args:
            t_source: Quellentemperatur (Fluid-Eintritt) [°C]
            cop_nominal: Nenn-COP bei Nennbedingungen
            t_source_nominal: Nenn-Quellentemperatur [°C]

        Returns:
            COP (begrenzt auf 2.0..8.0)
        """
        cop = cop_nominal * (1 + 0.04 * (t_source - t_source_nominal))
        return max(2.0, min(8.0, cop))

    @staticmethod
    def calculate_cop_carnot(
        t_source: float,
        t_sink: float = 35.0,
        eta_carnot: Optional[float] = None,
        cop_nominal: float = 4.0,
        t_source_nominal: float = 0.0,
    ) -> float:
        """Carnot-basiertes COP-Modell.

        COP_ideal = T_sink / (T_sink - T_source)  [in Kelvin]
        COP_real = eta_carnot * COP_ideal

        eta_carnot wird aus dem Nenn-COP abgeleitet, falls nicht angegeben.

        Args:
            t_source: Quellentemperatur [°C]
            t_sink: Senkentemperatur (Heizungsvorlauf) [°C]
            eta_carnot: Carnot-Gütegrad (typ. 0.40–0.55)
            cop_nominal: Nenn-COP (für eta_carnot-Berechnung)
            t_source_nominal: Nenn-Quellentemperatur [°C]

        Returns:
            COP (begrenzt auf 1.5..10.0)
        """
        T_source_K = t_source + 273.15
        T_sink_K = t_sink + 273.15
        T_source_nom_K = t_source_nominal + 273.15

        # Temperaturdifferenz muss positiv sein
        delta_T = T_sink_K - T_source_K
        if delta_T <= 0:
            return 10.0  # Theoretisch unendlich

        # COP_carnot = T_sink / (T_sink - T_source)
        cop_carnot = T_sink_K / delta_T

        # eta_carnot aus Nenn-COP ableiten
        if eta_carnot is None:
            delta_T_nom = T_sink_K - T_source_nom_K
            if delta_T_nom > 0:
                cop_carnot_nom = T_sink_K / delta_T_nom
                eta_carnot = cop_nominal / cop_carnot_nom
                eta_carnot = max(0.30, min(0.65, eta_carnot))
            else:
                eta_carnot = 0.45

        cop = eta_carnot * cop_carnot
        return max(1.5, min(10.0, cop))

    @staticmethod
    def calculate_cop_partload(
        t_source: float,
        t_sink: float = 35.0,
        part_load_ratio: float = 1.0,
        cop_nominal: float = 4.0,
        t_source_nominal: float = 0.0,
        eta_carnot: Optional[float] = None,
    ) -> float:
        """Carnot-Modell mit Teillast-Korrektur.

        Bei Teillast (PLR < 1) arbeitet die Wärmepumpe ineffizienter
        durch häufiges Takten. Bei Inverter-WP ist der Effekt geringer.

        Teillast-Faktor nach VDI 4650 (vereinfacht):
            f(PLR) = 1 - 0.1 * (1 - PLR)^2  (für PLR >= 0.3)
            f(PLR) = 0.85 * PLR / 0.3        (für PLR < 0.3)

        Args:
            t_source: Quellentemperatur [°C]
            t_sink: Senkentemperatur [°C]
            part_load_ratio: Teillast-Verhältnis [0..1]
            cop_nominal: Nenn-COP
            t_source_nominal: Nenn-Quellentemperatur [°C]
            eta_carnot: Carnot-Gütegrad

        Returns:
            COP mit Teillast-Korrektur
        """
        # Volllast-COP nach Carnot
        cop_fullload = SeasonalEfficiencyCalculator.calculate_cop_carnot(
            t_source, t_sink, eta_carnot, cop_nominal, t_source_nominal
        )

        # Teillast-Faktor
        plr = max(0.0, min(1.0, part_load_ratio))

        if plr >= 0.3:
            f_plr = 1.0 - 0.1 * (1.0 - plr) ** 2
        elif plr > 0:
            f_plr = 0.85 * plr / 0.3
        else:
            f_plr = 0.0

        cop = cop_fullload * f_plr
        return max(1.0, cop)


def calculate_monthly_cop(
    monthly_fluid_temps: List[float],
    cop_nominal: float = 4.0,
    t_sink: float = 35.0,
    method: str = 'carnot',
    part_load_ratios: Optional[List[float]] = None,
) -> List[float]:
    """Berechnet monatliche COP-Werte.

    Args:
        monthly_fluid_temps: 12 monatliche Fluid-Temperaturen [°C]
        cop_nominal: Nenn-COP
        t_sink: Heizungs-Vorlauftemperatur [°C]
        method: 'linear', 'carnot', oder 'partload'
        part_load_ratios: 12 Teillast-Verhältnisse [0..1] (nur für 'partload')

    Returns:
        Liste mit 12 COP-Werten
    """
    calc = SeasonalEfficiencyCalculator
    cops = []

    for m in range(min(12, len(monthly_fluid_temps))):
        t_source = monthly_fluid_temps[m]

        if method == 'linear':
            cop = calc.calculate_cop_linear(t_source, cop_nominal)
        elif method == 'partload' and part_load_ratios:
            plr = part_load_ratios[m] if m < len(part_load_ratios) else 1.0
            cop = calc.calculate_cop_partload(
                t_source, t_sink, plr, cop_nominal
            )
        else:  # 'carnot'
            cop = calc.calculate_cop_carnot(
                t_source, t_sink, cop_nominal=cop_nominal
            )

        cops.append(round(cop, 2))

    return cops


def calculate_jaz(
    monthly_cop: List[float],
    monthly_loads_kwh: List[float],
) -> float:
    """Berechnet die Jahresarbeitszahl (JAZ) aus monatlichen Profilen.

    JAZ = Σ(Q_i) / Σ(Q_i / COP_i)

    wobei Q_i die monatliche Last und COP_i der monatliche COP ist.

    Args:
        monthly_cop: 12 monatliche COP-Werte
        monthly_loads_kwh: 12 monatliche Heizlasten [kWh]

    Returns:
        JAZ (Jahresarbeitszahl)
    """
    total_heat = 0.0
    total_elec = 0.0

    for m in range(min(12, len(monthly_cop), len(monthly_loads_kwh))):
        q = monthly_loads_kwh[m]
        cop = monthly_cop[m]

        if q > 0 and cop > 0:
            total_heat += q
            total_elec += q / cop

    if total_elec > 0:
        return round(total_heat / total_elec, 2)
    return 0.0


def calculate_monthly_efficiency(
    monthly_fluid_temps: List[float],
    monthly_heating_kwh: List[float],
    cop_nominal: float = 4.0,
    t_sink: float = 35.0,
    method: str = 'carnot',
) -> MonthlyEfficiency:
    """Berechnet detaillierte monatliche Effizienz.

    Args:
        monthly_fluid_temps: 12 monatliche Fluid-Temperaturen [°C]
        monthly_heating_kwh: 12 monatliche Heizlasten [kWh]
        cop_nominal: Nenn-COP
        t_sink: Heizungs-Vorlauftemperatur [°C]
        method: COP-Berechnungsmethode

    Returns:
        MonthlyEfficiency mit COP, Lasten, Strom und JAZ
    """
    cops = calculate_monthly_cop(
        monthly_fluid_temps, cop_nominal, t_sink, method
    )

    electricity = []
    for m in range(12):
        q = monthly_heating_kwh[m] if m < len(monthly_heating_kwh) else 0.0
        cop = cops[m] if m < len(cops) else cop_nominal
        if q > 0 and cop > 0:
            electricity.append(round(q / cop, 1))
        else:
            electricity.append(0.0)

    jaz = calculate_jaz(cops, monthly_heating_kwh)

    return MonthlyEfficiency(
        cop_values=cops,
        loads_kwh=list(monthly_heating_kwh[:12]),
        electricity_kwh=electricity,
        jaz=jaz,
    )


def compare_jaz_by_depth(
    depths: List[float],
    simulate_func: callable,
    base_params: dict,
    cop_nominal: float = 4.0,
    t_sink: float = 35.0,
    method: str = 'carnot',
) -> JAZComparisonResult:
    """Vergleicht JAZ bei verschiedenen Sondentiefen.

    Args:
        depths: Liste von Sondentiefen [m]
        simulate_func: Funktion die LongtermSimulationResult liefert
        base_params: Basisparameter für simulate_func
        cop_nominal: Nenn-COP
        t_sink: Heizungs-Vorlauftemperatur [°C]
        method: COP-Berechnungsmethode

    Returns:
        JAZComparisonResult
    """
    result = JAZComparisonResult()

    monthly_heating = base_params.get('monthly_heating_kwh', [0.0] * 12)

    for depth in sorted(depths):
        params = dict(base_params)
        params['borehole_depth'] = depth
        params['simulation_years'] = min(
            params.get('simulation_years', 25), 25
        )

        try:
            sim_result = simulate_func(**params)

            # Verwende Temperaturen des letzten Jahres
            if sim_result.monthly_fluid_temps:
                last_year_temps = sim_result.monthly_fluid_temps[-1]
            else:
                continue

            cops = calculate_monthly_cop(
                last_year_temps, cop_nominal, t_sink, method
            )
            jaz = calculate_jaz(cops, monthly_heating)

            result.depths.append(depth)
            result.jaz_values.append(jaz)
            result.monthly_cop_per_depth[depth] = cops

        except Exception as e:
            logger.warning(
                "JAZ-Vergleich für Tiefe %.0fm fehlgeschlagen: %s",
                depth, e
            )

    return result
