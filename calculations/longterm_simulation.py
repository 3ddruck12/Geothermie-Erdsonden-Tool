"""Langzeit-Simulation für Erdwärmesonden (Temporal Superposition).

Berechnet monatliche Fluid-Temperaturen über N Jahre mittels
Temporal Superposition nach Eskilson (1987).

Desktop: max 25 Jahre | Cloud-ready: bis 50 Jahre.
"""

import math
import logging
import numpy as np
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from .g_functions import GFunctionCalculator
from .thermal import ThermalResistanceCalculator

logger = logging.getLogger(__name__)

# Konstanten
SECONDS_PER_MONTH = 30.44 * 24 * 3600  # ~2.63e6 s
MONTHS_PER_YEAR = 12
DESKTOP_MAX_YEARS = 25
CLOUD_MAX_YEARS = 50


@dataclass
class LongtermSimulationResult:
    """Ergebnis einer Langzeit-Simulation."""
    years: int
    # Monatliche Fluid-Temperaturen [Jahr][Monat] (Mittelwert Ein/Aus)
    monthly_fluid_temps: List[List[float]] = field(default_factory=list)
    # Monatliche Fluid-Eintrittstemperaturen [Jahr][Monat]
    monthly_fluid_temps_inlet: List[List[float]] = field(default_factory=list)
    # Monatliche Fluid-Austrittstemperaturen [Jahr][Monat]
    monthly_fluid_temps_outlet: List[List[float]] = field(default_factory=list)
    # Monatliche Bodentemperatur am Bohrloch [Jahr][Monat]
    monthly_ground_temps: List[List[float]] = field(default_factory=list)
    # Jährlicher Wärmeentzug (kWh, Heizen)
    annual_energy_extraction: List[float] = field(default_factory=list)
    # Jährlicher Wärmeeintrag (kWh, Kühlen)
    annual_energy_injection: List[float] = field(default_factory=list)
    # Monatliche Lasten am Bohrloch [W/m] (alle Monate flach)
    monthly_loads_w_per_m: List[float] = field(default_factory=list)
    # Min/Max Fluid-Temperatur pro Jahr
    annual_fluid_temp_min: List[float] = field(default_factory=list)
    annual_fluid_temp_max: List[float] = field(default_factory=list)


class LongtermSimulator:
    """Langzeit-Simulation mit Temporal Superposition.

    Berechnet die thermische Antwort des Erdreichs auf monatlich
    variable Lasten über mehrere Jahre.

    Die Methode nutzt das Superpositionsprinzip:
      ΔT(t_n) = Σ_{i=0}^{n-1} Δq_i / (2πλH) · g(t_n - t_i)

    wobei Δq_i die Laständerung im Monat i ist.
    """

    def __init__(self):
        self.g_calc = GFunctionCalculator()
        self.thermal_calc = ThermalResistanceCalculator()

    def simulate(
        self,
        # Bodeneigenschaften
        ground_thermal_conductivity: float,  # W/m·K
        ground_heat_capacity: float,         # J/m³·K
        undisturbed_ground_temp: float,      # °C
        geothermal_gradient: float = 0.03,   # K/m

        # Bohrloch
        borehole_depth: float = 100.0,       # m
        borehole_diameter: float = 0.152,    # m
        borehole_resistance: float = 0.10,   # m·K/W (R_b)

        # Lasten (monatlich, 12 Werte in kWh)
        monthly_heating_kwh: Optional[List[float]] = None,
        monthly_cooling_kwh: Optional[List[float]] = None,

        # Wärmepumpe
        cop_heating: float = 4.0,
        eer_cooling: float = 4.0,
        delta_t_fluid: float = 3.0,  # K Spreizung

        # Simulation
        simulation_years: int = 25,
        max_years: int = DESKTOP_MAX_YEARS,

        # Bohrfeld
        n_boreholes: int = 1,
        custom_gfunction: Optional[callable] = None,
    ) -> LongtermSimulationResult:
        """Führt Langzeit-Simulation durch.

        Args:
            ground_thermal_conductivity: Wärmeleitfähigkeit Boden [W/m·K]
            ground_heat_capacity: Wärmekapazität Boden [J/m³·K]
            undisturbed_ground_temp: Ungestörte Bodentemperatur [°C]
            geothermal_gradient: Geothermischer Gradient [K/m]
            borehole_depth: Bohrtiefe [m]
            borehole_diameter: Bohrdurchmesser [m]
            borehole_resistance: Bohrlochwiderstand R_b [m·K/W]
            monthly_heating_kwh: 12 monatliche Heizwerte [kWh]
            monthly_cooling_kwh: 12 monatliche Kühlwerte [kWh]
            cop_heating: COP Heizen
            eer_cooling: EER Kühlen
            delta_t_fluid: Fluidspreizung [K]
            simulation_years: Simulationsdauer [Jahre]
            max_years: Maximale erlaubte Jahre
            n_boreholes: Anzahl Bohrungen
            custom_gfunction: Optionale Bohrfeld-g-Funktion

        Returns:
            LongtermSimulationResult
        """
        # Begrenze Simulationsdauer
        simulation_years = min(simulation_years, max_years)
        n_months_total = simulation_years * MONTHS_PER_YEAR

        # Default-Lastprofile
        if monthly_heating_kwh is None:
            monthly_heating_kwh = [0.0] * 12
        if monthly_cooling_kwh is None:
            monthly_cooling_kwh = [0.0] * 12

        # Thermische Diffusivität
        thermal_diffusivity = ground_thermal_conductivity / ground_heat_capacity
        borehole_radius = borehole_diameter / 2

        # Mittlere Bodentemperatur in Bohrtiefe
        avg_ground_temp = (undisturbed_ground_temp
                           + geothermal_gradient * borehole_depth / 2)

        # Berechne monatliche Last am Bohrloch [W] pro Bohrung
        # Heizen: Entzug = Q_heiz * (COP-1)/COP
        # Kühlen: Eintrag = Q_kühl * (1 + 1/EER) (negativ = Eintrag)
        heat_factor = (cop_heating - 1) / cop_heating if cop_heating > 1 else 0.75
        cool_factor = (1 + 1 / eer_cooling) if eer_cooling > 0 else 1.25

        # Monatliche Last am Bohrloch [W] (pro Bohrung)
        # Positiv = Wärmeentzug (Heizen), Negativ = Wärmeeintrag (Kühlen)
        monthly_borehole_load_w = []
        for m in range(12):
            q_heat_w = (monthly_heating_kwh[m] * 1000 * heat_factor
                        / (SECONDS_PER_MONTH / 3600))  # kWh → W
            q_cool_w = (monthly_cooling_kwh[m] * 1000 * cool_factor
                        / (SECONDS_PER_MONTH / 3600))
            q_net = (q_heat_w - q_cool_w) / max(n_boreholes, 1)
            monthly_borehole_load_w.append(q_net)

        # Last pro Meter [W/m]
        monthly_load_w_per_m = [q / borehole_depth
                                for q in monthly_borehole_load_w]

        # --- Vorberechnung der g-Werte ---
        # Wir brauchen g(Δt) für Δt = 1 Monat, 2 Monate, ..., n_months_total
        g_values = self._precalculate_g_values(
            n_months_total, borehole_depth, borehole_radius,
            thermal_diffusivity, custom_gfunction
        )

        # --- Temporal Superposition ---
        # q_load[i] = Last im Monat i [W/m] (zyklisch über 12 Monate)
        q_load = [monthly_load_w_per_m[i % 12] for i in range(n_months_total)]

        # Δq[i] = Laständerung im Monat i
        delta_q = [0.0] * n_months_total
        delta_q[0] = q_load[0]
        for i in range(1, n_months_total):
            delta_q[i] = q_load[i] - q_load[i - 1]

        # Faktor: 1 / (2π λ)
        thermal_factor = 1.0 / (2 * math.pi * ground_thermal_conductivity)

        # Berechne Bodentemperaturänderung für jeden Monat
        ground_delta_t = [0.0] * n_months_total

        for n in range(n_months_total):
            dt = 0.0
            for i in range(n + 1):
                time_index = n - i  # Δt in Monaten (0-basiert)
                g = g_values[time_index]
                dt += delta_q[i] * g
            ground_delta_t[n] = dt * thermal_factor

        # --- Fluid-Temperaturen berechnen ---
        all_fluid_temps = []
        all_fluid_inlet = []
        all_fluid_outlet = []
        all_ground_temps = []
        all_loads_w_per_m = []

        for n in range(n_months_total):
            # q_load is positive for extraction -> ground cools down
            t_ground = avg_ground_temp - ground_delta_t[n]
            q = q_load[n]

            # Fluid-Mitteltemperatur = Bodentemp - q * R_b
            # (R_b positiv: Fluid wärmer als Bohrloch bei Kühlung,
            #  kälter bei Heizen)
            t_fluid = t_ground - q * borehole_resistance

            # Ein-/Austritt (symmetrisch um Mittelwert)
            t_inlet = t_fluid - delta_t_fluid / 2
            t_outlet = t_fluid + delta_t_fluid / 2

            all_fluid_temps.append(round(t_fluid, 2))
            all_fluid_inlet.append(round(t_inlet, 2))
            all_fluid_outlet.append(round(t_outlet, 2))
            all_ground_temps.append(round(t_ground, 2))
            all_loads_w_per_m.append(round(q_load[n], 2))

        # --- In Jahres-Arrays aufteilen ---
        result = LongtermSimulationResult(years=simulation_years)

        for year in range(simulation_years):
            start = year * 12
            end = start + 12

            year_fluid = all_fluid_temps[start:end]
            year_inlet = all_fluid_inlet[start:end]
            year_outlet = all_fluid_outlet[start:end]
            year_ground = all_ground_temps[start:end]

            result.monthly_fluid_temps.append(year_fluid)
            result.monthly_fluid_temps_inlet.append(year_inlet)
            result.monthly_fluid_temps_outlet.append(year_outlet)
            result.monthly_ground_temps.append(year_ground)
            result.annual_fluid_temp_min.append(min(year_fluid))
            result.annual_fluid_temp_max.append(max(year_fluid))

            # Jährliche Energie (kWh)
            year_extraction = sum(
                monthly_heating_kwh[m % 12] * heat_factor / max(n_boreholes, 1)
                for m in range(12)
            )
            year_injection = sum(
                monthly_cooling_kwh[m % 12] * cool_factor / max(n_boreholes, 1)
                for m in range(12)
            )
            result.annual_energy_extraction.append(round(year_extraction, 1))
            result.annual_energy_injection.append(round(year_injection, 1))

        result.monthly_loads_w_per_m = all_loads_w_per_m

        logger.info(
            "Langzeit-Simulation abgeschlossen: %d Jahre, T_min=%.1f°C, T_max=%.1f°C",
            simulation_years,
            min(result.annual_fluid_temp_min),
            max(result.annual_fluid_temp_max),
        )

        return result

    def _precalculate_g_values(
        self,
        n_months: int,
        borehole_depth: float,
        borehole_radius: float,
        thermal_diffusivity: float,
        custom_gfunction: Optional[callable] = None,
    ) -> List[float]:
        """Vorberechnung der g-Werte für Δt = 1..n_months Monate.

        Returns:
            Liste von g-Werten, Index 0 = g(1 Monat), Index n-1 = g(n Monate)
        """
        g_values = []

        for i in range(n_months):
            t = (i + 1) * SECONDS_PER_MONTH  # Zeit in Sekunden

            if custom_gfunction is not None:
                try:
                    g = float(custom_gfunction(t))
                except Exception:
                    g = GFunctionCalculator.calculate_finite_line_source(
                        t, borehole_depth, borehole_radius, thermal_diffusivity
                    )
            else:
                g = GFunctionCalculator.calculate_finite_line_source(
                    t, borehole_depth, borehole_radius, thermal_diffusivity
                )

            g_values.append(g)

        return g_values
