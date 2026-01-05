"""G-Funktionen Berechnungen für Erdwärmesonden nach Eskilson."""

import numpy as np
import math
from typing import List, Tuple
from scipy import interpolate


class GFunctionCalculator:
    """
    Berechnet g-Funktionen für Erdwärmesonden.
    
    Die g-Funktion beschreibt die thermische Antwort des Untergrunds
    auf eine konstante Wärmelast über die Zeit.
    
    Basiert auf der Arbeit von Eskilson (1987) und Zeng et al. (2002).
    """
    
    def __init__(self):
        """Initialisiert den G-Funktions-Rechner."""
        self.g_values = []
        self.ln_t_ts_values = []
    
    @staticmethod
    def calculate_finite_line_source(
        time: float,
        borehole_depth: float,
        borehole_radius: float,
        thermal_diffusivity: float
    ) -> float:
        """
        Berechnet die Finite Line Source (FLS) Lösung.
        
        Args:
            time: Zeit in Sekunden
            borehole_depth: Bohrtiefe in m
            borehole_radius: Bohrlochradius in m
            thermal_diffusivity: Temperaturleitfähigkeit in m²/s
            
        Returns:
            g-Wert (dimensionslos)
        """
        if time <= 0 or borehole_depth <= 0:
            return 0.0
        
        # Fourier-Zahl
        Fo = thermal_diffusivity * time / (borehole_depth ** 2)
        
        # Verhältnis Tiefe zu Radius
        H_rb = borehole_depth / borehole_radius
        
        # Vereinfachte FLS-Berechnung für Single-Bohrloch
        # Für kleine Zeiten (Fo < 0.01): Unendliche Zylinder-Quelle
        if Fo < 0.01:
            g = GFunctionCalculator._infinite_cylindrical_source(time, borehole_radius, thermal_diffusivity)
        # Für große Zeiten (Fo > 10): Infinite Line Source
        elif Fo > 10:
            g = GFunctionCalculator._infinite_line_source(time, borehole_depth, thermal_diffusivity)
        # Für mittlere Zeiten: Interpolation
        else:
            g_cyl = GFunctionCalculator._infinite_cylindrical_source(time, borehole_radius, thermal_diffusivity)
            g_ils = GFunctionCalculator._infinite_line_source(time, borehole_depth, thermal_diffusivity)
            # Gewichtete Interpolation
            weight = (math.log10(Fo) + 2) / 3  # 0 bei Fo=0.01, 1 bei Fo=10
            weight = max(0, min(1, weight))
            g = (1 - weight) * g_cyl + weight * g_ils
        
        return g
    
    @staticmethod
    def _infinite_line_source(time: float, depth: float, thermal_diffusivity: float) -> float:
        """
        Infinite Line Source (ILS) Lösung.
        Gilt für lange Zeiten und große Tiefen.
        """
        if time <= 0:
            return 0.0
        
        # Dimensionslose Zeit
        ts = depth ** 2 / (9 * thermal_diffusivity)
        
        if time < ts:
            return 0.0
        
        # g-Funktion für ILS (vereinfachte Näherung)
        ln_t_ts = math.log(time / ts)
        
        # Eskilson's Näherung für eine einzelne Sonde
        g = 0.5 * ln_t_ts
        
        return g
    
    @staticmethod
    def _infinite_cylindrical_source(time: float, radius: float, thermal_diffusivity: float) -> float:
        """
        Infinite Cylindrical Source (ICS) Lösung.
        Gilt für kurze Zeiten.
        """
        if time <= 0 or radius <= 0:
            return 0.0
        
        # Argument der Exponentialintegral-Funktion
        u = radius ** 2 / (4 * thermal_diffusivity * time)
        
        # Exponentialintegral Ei(-u) Näherung für kleine u
        if u < 0.01:
            # Euler-Mascheroni Konstante
            gamma = 0.5772156649
            g = -0.5 * (math.log(u) + gamma)
        else:
            # Näherung für größere u
            g = -0.5 * math.log(4 * u)
        
        return max(0, g)
    
    def generate_g_function_table(
        self,
        borehole_depth: float,
        borehole_radius: float,
        thermal_diffusivity: float,
        simulation_years: int = 25
    ) -> Tuple[List[float], List[float]]:
        """
        Erzeugt eine Tabelle von g-Funktionswerten über die Zeit.
        
        Args:
            borehole_depth: Bohrtiefe in m
            borehole_radius: Bohrlochradius in m
            thermal_diffusivity: Temperaturleitfähigkeit in m²/s
            simulation_years: Simulationszeitraum in Jahren
            
        Returns:
            Tuple (ln(t/ts) Werte, g-Werte)
        """
        # Charakteristische Zeit
        ts = borehole_depth ** 2 / (9 * thermal_diffusivity)
        
        # Zeitpunkte logarithmisch verteilt
        # Von 1 Stunde bis simulation_years Jahre
        t_start = 3600  # 1 Stunde in Sekunden
        t_end = simulation_years * 365.25 * 24 * 3600  # Jahre in Sekunden
        
        # Logarithmisch verteilte Zeitpunkte
        n_points = 50
        times = np.logspace(math.log10(t_start), math.log10(t_end), n_points)
        
        # Berechne g-Werte
        g_values = []
        ln_t_ts_values = []
        
        for t in times:
            g = self.calculate_finite_line_source(
                t, borehole_depth, borehole_radius, thermal_diffusivity
            )
            ln_t_ts = math.log(t / ts)
            
            g_values.append(g)
            ln_t_ts_values.append(ln_t_ts)
        
        self.g_values = g_values
        self.ln_t_ts_values = ln_t_ts_values
        
        return ln_t_ts_values, g_values
    
    def interpolate_g(self, time: float, borehole_depth: float, thermal_diffusivity: float) -> float:
        """
        Interpoliert den g-Wert für eine gegebene Zeit aus der g-Funktions-Tabelle.
        """
        if not self.g_values:
            return 0.0
        
        ts = borehole_depth ** 2 / (9 * thermal_diffusivity)
        ln_t_ts = math.log(time / ts)
        
        # Lineare Interpolation
        f = interpolate.interp1d(
            self.ln_t_ts_values,
            self.g_values,
            kind='linear',
            fill_value='extrapolate'
        )
        
        return float(f(ln_t_ts))
    
    @staticmethod
    def calculate_temperature_penalty(
        heat_load: float,
        thermal_conductivity: float,
        borehole_depth: float,
        g_value: float
    ) -> float:
        """
        Berechnet die Temperaturänderung aufgrund einer Wärmelast.
        
        Args:
            heat_load: Wärmelast in W
            thermal_conductivity: Wärmeleitfähigkeit des Bodens in W/m·K
            borehole_depth: Bohrtiefe in m
            g_value: g-Funktionswert (dimensionslos)
            
        Returns:
            Temperaturänderung in K
        """
        if borehole_depth <= 0 or thermal_conductivity <= 0:
            return 0.0
        
        q_per_meter = heat_load / borehole_depth  # W/m
        
        delta_T = (q_per_meter * g_value) / (2 * math.pi * thermal_conductivity)
        
        return delta_T


if __name__ == "__main__":
    # Test
    calc = GFunctionCalculator()
    
    # Beispielparameter
    depth = 100  # m
    radius = 0.115 / 2  # m
    thermal_cond = 3.4  # W/m·K
    heat_capacity = 2.4e6  # J/m³·K
    diffusivity = thermal_cond / heat_capacity  # m²/s
    
    # Erzeuge g-Funktions-Tabelle
    ln_t_ts, g_vals = calc.generate_g_function_table(
        depth, radius, diffusivity, simulation_years=25
    )
    
    print(f"G-Funktions-Tabelle generiert: {len(g_vals)} Punkte")
    print(f"Erster g-Wert: {g_vals[0]:.4f}")
    print(f"Letzter g-Wert: {g_vals[-1]:.4f}")
    
    # Berechne Temperaturänderung für 6 kW Wärmeentzug
    heat_load = -6000  # W (negativ = Wärmeentzug)
    delta_T = calc.calculate_temperature_penalty(
        heat_load, thermal_cond, depth, g_vals[-1]
    )
    print(f"\nTemperaturänderung nach 25 Jahren: {delta_T:.2f} K")









