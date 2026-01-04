"""Hauptberechnungsmodul für Erdwärmesonden-Dimensionierung."""

import math
from dataclasses import dataclass
from typing import List, Tuple, Optional
from .thermal import ThermalResistanceCalculator
from .g_functions import GFunctionCalculator


@dataclass
class BoreholeResult:
    """Ergebnis einer Erdwärmesonden-Berechnung."""
    required_depth: float  # m
    fluid_temperature_min: float  # °C
    fluid_temperature_max: float  # °C
    borehole_resistance: float  # m·K/W
    effective_resistance: float  # m·K/W
    heat_extraction_rate: float  # W/m
    monthly_temperatures: List[float] = None  # °C
    
    def __post_init__(self):
        if self.monthly_temperatures is None:
            self.monthly_temperatures = [0.0] * 12


class BoreholeCalculator:
    """
    Hauptrechner für Erdwärmesonden-Dimensionierung.
    
    Kombiniert thermische Widerstände und g-Funktionen, um die
    erforderliche Bohrtiefe und Betriebstemperaturen zu berechnen.
    """
    
    def __init__(self):
        """Initialisiert den Bohrloch-Rechner."""
        self.thermal_calc = ThermalResistanceCalculator()
        self.g_calc = GFunctionCalculator()
    
    def calculate_required_depth(
        self,
        # Bodeneigenschaften
        ground_thermal_conductivity: float,  # W/m·K
        ground_heat_capacity: float,  # J/m³·K
        undisturbed_ground_temp: float,  # °C
        geothermal_gradient: float = 0.03,  # K/m
        
        # Bohrloch-Geometrie
        borehole_diameter: float = 0.152,  # m (6 inch)
        pipe_configuration: str = "single-u",
        
        # Rohr-Eigenschaften
        pipe_outer_diameter: float = 0.040,  # m
        pipe_wall_thickness: float = 0.0037,  # m
        pipe_thermal_conductivity: float = 0.42,  # W/m·K (PE)
        shank_spacing: float = 0.052,  # m
        
        # Verfüllung
        grout_thermal_conductivity: float = 1.3,  # W/m·K
        
        # Wärmeträgerflüssigkeit
        fluid_thermal_conductivity: float = 0.48,  # W/m·K
        fluid_heat_capacity: float = 3800,  # J/kg·K
        fluid_density: float = 1030,  # kg/m³
        fluid_viscosity: float = 0.004,  # Pa·s
        fluid_flow_rate: float = 0.0005,  # m³/s
        
        # Lasten
        annual_heating_demand: float = 10.0,  # MWh/Jahr
        annual_cooling_demand: float = 0.0,  # MWh/Jahr
        peak_heating_load: float = 6.0,  # kW
        peak_cooling_load: float = 0.0,  # kW
        monthly_heating_factors: Optional[List[float]] = None,
        monthly_cooling_factors: Optional[List[float]] = None,
        
        # Betriebsbedingungen
        heat_pump_cop: float = 4.0,
        min_fluid_temperature: float = -2.0,  # °C
        max_fluid_temperature: float = 15.0,  # °C
        simulation_years: int = 25,
        
        # Startwert für Iteration
        initial_depth: float = 100.0  # m
    ) -> BoreholeResult:
        """
        Berechnet die erforderliche Bohrtiefe für gegebene Parameter.
        
        Verwendet eine iterative Methode, um die Tiefe zu finden, bei der
        die Fluidtemperaturen die Anforderungen erfüllen.
        """
        # Standardwerte für monatliche Faktoren
        if monthly_heating_factors is None:
            # Typische Heizlastverteilung für Mitteleuropa
            monthly_heating_factors = [
                0.155, 0.148, 0.125, 0.099, 0.064, 0.0,
                0.0, 0.0, 0.061, 0.087, 0.117, 0.144
            ]
        
        if monthly_cooling_factors is None:
            monthly_cooling_factors = [0.0] * 12
        
        # Umrechnung MWh/Jahr in W
        avg_heating_power = (annual_heating_demand * 1e6 * 3600) / (365.25 * 24 * 3600)  # W
        avg_cooling_power = (annual_cooling_demand * 1e6 * 3600) / (365.25 * 24 * 3600)  # W
        
        # Wärmepumpen-Anteil berücksichtigen
        # Bei Wärmeentzug: Q_borehole = Q_heating * (1 - 1/COP)
        heat_pump_efficiency_factor = (heat_pump_cop - 1) / heat_pump_cop
        
        avg_ground_heat_extraction = avg_heating_power * heat_pump_efficiency_factor  # W
        avg_ground_heat_injection = avg_cooling_power * (1 + 1/heat_pump_cop)  # W
        
        net_annual_load = avg_ground_heat_extraction - avg_ground_heat_injection  # W
        
        # Peak-Last für Bohrloch (berücksichtigt Wärmepumpe)
        peak_ground_extraction = peak_heating_load * 1000 * heat_pump_efficiency_factor  # W
        peak_ground_injection = peak_cooling_load * 1000 * (1 + 1/heat_pump_cop)  # W
        
        # Iteration zur Bestimmung der erforderlichen Tiefe
        depth = initial_depth
        max_iterations = 20
        tolerance = 0.5  # m
        
        for iteration in range(max_iterations):
            # Berechne thermische Widerstände
            r_b, r_a = self._calculate_borehole_resistance(
                pipe_configuration,
                borehole_diameter / 2,
                pipe_outer_diameter / 2,
                pipe_wall_thickness,
                shank_spacing,
                pipe_thermal_conductivity,
                grout_thermal_conductivity
            )
            
            # Berechne Rohrwiderstand
            r_pipe = self.thermal_calc.calculate_pipe_resistance(
                pipe_outer_diameter - 2 * pipe_wall_thickness,
                pipe_outer_diameter,
                pipe_thermal_conductivity
            )
            
            # Berechne konvektiven Widerstand
            r_conv = self.thermal_calc.calculate_convection_resistance(
                pipe_outer_diameter - 2 * pipe_wall_thickness,
                fluid_flow_rate,
                fluid_thermal_conductivity,
                fluid_viscosity,
                fluid_density,
                fluid_heat_capacity
            )
            
            # Gesamt effektiver Widerstand
            r_eff = r_b + r_pipe + r_conv
            
            # Berechne thermische Diffusivität
            thermal_diffusivity = ground_thermal_conductivity / ground_heat_capacity
            
            # Erzeuge g-Funktions-Tabelle
            self.g_calc.generate_g_function_table(
                depth,
                borehole_diameter / 2,
                thermal_diffusivity,
                simulation_years
            )
            
            # Berechne Fluidtemperaturen für verschiedene Zeitpunkte
            # Monat mit höchster Heizlast (typisch Januar)
            max_heating_month = monthly_heating_factors.index(max(monthly_heating_factors))
            
            # Zeit am Ende der Simulationsperiode (kritisch)
            critical_time = simulation_years * 365.25 * 24 * 3600  # Sekunden
            
            # g-Wert für kritischen Zeitpunkt
            g_value = self.g_calc.interpolate_g(critical_time, depth, thermal_diffusivity)
            
            # Temperaturänderung durch Langzeit-Last
            q_per_meter = net_annual_load / depth  # W/m
            delta_T_long = self.g_calc.calculate_temperature_penalty(
                net_annual_load, ground_thermal_conductivity, depth, g_value
            )
            
            # Temperaturänderung durch Peak-Last
            # Für kurze Zeit (z.B. 6 Stunden Peak)
            peak_time = 6 * 3600  # Sekunden
            g_peak = self.g_calc.calculate_finite_line_source(
                peak_time, depth, borehole_diameter / 2, thermal_diffusivity
            )
            
            # Mittlere Bodentemperatur in Bohrtiefe
            avg_ground_temp = undisturbed_ground_temp + geothermal_gradient * depth / 2
            
            # Berechne minimale Fluidtemperatur (bei maximaler Wärmeentnahme)
            q_peak_per_meter = peak_ground_extraction / depth
            delta_T_peak = (q_peak_per_meter / (2 * math.pi * ground_thermal_conductivity)) * g_peak
            delta_T_resistance = q_peak_per_meter * r_eff
            
            fluid_temp_min = avg_ground_temp + delta_T_long - delta_T_peak - delta_T_resistance
            
            # Berechne maximale Fluidtemperatur (bei maximaler Wärmeeinspeisung, falls Kühlung)
            if peak_ground_injection > 0:
                q_cool_per_meter = peak_ground_injection / depth
                delta_T_cool_peak = (q_cool_per_meter / (2 * math.pi * ground_thermal_conductivity)) * g_peak
                delta_T_cool_resistance = q_cool_per_meter * r_eff
                fluid_temp_max = avg_ground_temp + delta_T_long + delta_T_cool_peak + delta_T_cool_resistance
            else:
                fluid_temp_max = avg_ground_temp + delta_T_long
            
            # Prüfe Temperaturanforderungen
            if fluid_temp_min >= min_fluid_temperature and fluid_temp_max <= max_fluid_temperature:
                # Anforderungen erfüllt
                break
            
            # Passe Tiefe an
            if fluid_temp_min < min_fluid_temperature:
                # Zu kalt -> mehr Tiefe benötigt
                depth_correction = (min_fluid_temperature - fluid_temp_min) / 0.02  # ~2°C pro 100m
                depth += depth_correction
            elif fluid_temp_max > max_fluid_temperature:
                # Zu warm -> mehr Tiefe benötigt (bei Kühlung)
                depth_correction = (fluid_temp_max - max_fluid_temperature) / 0.02
                depth += depth_correction
            
            # Begrenze Tiefe auf sinnvolle Werte
            depth = max(20, min(300, depth))
            
            if iteration == max_iterations - 1:
                print(f"Warnung: Maximale Iterationen erreicht. Tiefe möglicherweise nicht optimal.")
        
        # Berechne monatliche Temperaturen
        monthly_temps = self._calculate_monthly_temperatures(
            depth, avg_ground_temp, net_annual_load,
            monthly_heating_factors, monthly_cooling_factors,
            ground_thermal_conductivity, thermal_diffusivity,
            borehole_diameter / 2
        )
        
        # Erstelle Ergebnis
        result = BoreholeResult(
            required_depth=round(depth, 1),
            fluid_temperature_min=round(fluid_temp_min, 2),
            fluid_temperature_max=round(fluid_temp_max, 2),
            borehole_resistance=round(r_b, 4),
            effective_resistance=round(r_eff, 4),
            heat_extraction_rate=round(q_per_meter, 2),
            monthly_temperatures=monthly_temps
        )
        
        return result
    
    def _calculate_borehole_resistance(
        self,
        configuration: str,
        borehole_radius: float,
        pipe_radius: float,
        pipe_thickness: float,
        shank_spacing: float,
        pipe_thermal_cond: float,
        grout_thermal_cond: float
    ) -> Tuple[float, float]:
        """Hilfsmethode zur Berechnung des Bohrloch-Widerstands."""
        config_lower = configuration.lower()
        
        if "single" in config_lower or "single-u" in config_lower:
            return self.thermal_calc.calculate_single_u_tube_resistance(
                borehole_radius, pipe_radius, shank_spacing,
                pipe_thermal_cond, grout_thermal_cond
            )
        elif "double" in config_lower or "double-u" in config_lower:
            return self.thermal_calc.calculate_double_u_tube_resistance(
                borehole_radius, pipe_radius, shank_spacing,
                pipe_thermal_cond, grout_thermal_cond
            )
        else:
            # Standard: Single-U
            return self.thermal_calc.calculate_single_u_tube_resistance(
                borehole_radius, pipe_radius, shank_spacing,
                pipe_thermal_cond, grout_thermal_cond
            )
    
    def _calculate_monthly_temperatures(
        self,
        depth: float,
        avg_ground_temp: float,
        annual_load: float,
        heating_factors: List[float],
        cooling_factors: List[float],
        thermal_conductivity: float,
        thermal_diffusivity: float,
        borehole_radius: float
    ) -> List[float]:
        """Berechnet monatliche durchschnittliche Fluidtemperaturen."""
        monthly_temps = []
        
        # Zeit pro Monat (vereinfacht)
        seconds_per_month = 30.44 * 24 * 3600
        
        for month in range(12):
            # Monatliche Last
            monthly_load = annual_load * (heating_factors[month] - cooling_factors[month])
            
            # Zeit (Mitte des Monats)
            time = (month + 0.5) * seconds_per_month
            
            # g-Wert
            g = self.g_calc.interpolate_g(time, depth, thermal_diffusivity)
            
            # Temperaturänderung
            delta_T = self.g_calc.calculate_temperature_penalty(
                monthly_load, thermal_conductivity, depth, g
            )
            
            # Monatliche Temperatur
            temp = avg_ground_temp + delta_T
            monthly_temps.append(round(temp, 2))
        
        return monthly_temps


if __name__ == "__main__":
    # Test
    calc = BoreholeCalculator()
    
    result = calc.calculate_required_depth(
        ground_thermal_conductivity=3.4,
        ground_heat_capacity=2.4e6,
        undisturbed_ground_temp=10.0,
        annual_heating_demand=12.0,
        peak_heating_load=6.0,
        heat_pump_cop=4.0
    )
    
    print("=== Berechnungsergebnis ===")
    print(f"Erforderliche Bohrtiefe: {result.required_depth} m")
    print(f"Min. Fluidtemperatur: {result.fluid_temperature_min} °C")
    print(f"Max. Fluidtemperatur: {result.fluid_temperature_max} °C")
    print(f"Bohrloch-Widerstand R_b: {result.borehole_resistance} m·K/W")
    print(f"Effektiver Widerstand: {result.effective_resistance} m·K/W")
    print(f"Wärmeentzugsrate: {result.heat_extraction_rate} W/m")





