"""Thermische Widerstands-Berechnungen für Erdwärmesonden."""

import numpy as np
import math
from typing import Tuple


class ThermalResistanceCalculator:
    """
    Berechnet thermische Widerstände für verschiedene Bohrlochkonfigurationen.
    Basiert auf der Multipol-Methode nach Bennet et al. (1987) und Hellström (1991).
    """
    
    @staticmethod
    def calculate_pipe_resistance(
        inner_diameter: float,
        outer_diameter: float,
        thermal_conductivity: float
    ) -> float:
        """
        Berechnet den thermischen Widerstand eines Rohres.
        
        Args:
            inner_diameter: Innendurchmesser in m
            outer_diameter: Außendurchmesser in m
            thermal_conductivity: Wärmeleitfähigkeit in W/m·K
            
        Returns:
            Thermischer Widerstand in m·K/W
        """
        if thermal_conductivity <= 0 or inner_diameter <= 0 or outer_diameter <= inner_diameter:
            return 0.0
        
        r_pipe = (1 / (2 * math.pi * thermal_conductivity)) * \
                 math.log(outer_diameter / inner_diameter)
        
        return r_pipe
    
    @staticmethod
    def calculate_convection_resistance(
        inner_diameter: float,
        flow_rate: float,
        fluid_thermal_conductivity: float,
        fluid_viscosity: float,
        fluid_density: float,
        fluid_heat_capacity: float
    ) -> float:
        """
        Berechnet den konvektiven Wärmeübergang im Rohr.
        
        Args:
            inner_diameter: Innendurchmesser in m
            flow_rate: Volumenstrom in m³/s
            fluid_thermal_conductivity: Wärmeleitfähigkeit der Flüssigkeit in W/m·K
            fluid_viscosity: Dynamische Viskosität in Pa·s
            fluid_density: Dichte in kg/m³
            fluid_heat_capacity: Spezifische Wärmekapazität in J/kg·K
            
        Returns:
            Konvektiver Widerstand in m·K/W
        """
        if inner_diameter <= 0 or flow_rate <= 0:
            return 0.0
        
        # Strömungsgeschwindigkeit
        area = math.pi * (inner_diameter / 2) ** 2
        velocity = flow_rate / area
        
        # Reynolds-Zahl
        reynolds = (fluid_density * velocity * inner_diameter) / fluid_viscosity
        
        # Prandtl-Zahl
        prandtl = (fluid_viscosity * fluid_heat_capacity) / fluid_thermal_conductivity
        
        # Nusselt-Zahl (Dittus-Boelter für turbulente Strömung)
        if reynolds > 2300:  # Turbulent
            nusselt = 0.023 * (reynolds ** 0.8) * (prandtl ** 0.4)
        else:  # Laminar
            nusselt = 3.66
        
        # Wärmeübergangskoeffizient
        h = (nusselt * fluid_thermal_conductivity) / inner_diameter
        
        # Konvektiver Widerstand
        r_conv = 1 / (h * math.pi * inner_diameter)
        
        return r_conv
    
    @staticmethod
    def calculate_single_u_tube_resistance(
        borehole_radius: float,
        pipe_outer_radius: float,
        shank_spacing: float,
        pipe_thermal_conductivity: float,
        grout_thermal_conductivity: float,
        n_multipoles: int = 10
    ) -> Tuple[float, float]:
        """
        Berechnet die thermischen Widerstände für ein Single-U-Rohr.
        
        Args:
            borehole_radius: Bohrlochradius in m
            pipe_outer_radius: Außenradius des Rohres in m
            shank_spacing: Abstand zwischen den Rohrschenkeln in m
            pipe_thermal_conductivity: Wärmeleitfähigkeit des Rohres in W/m·K
            grout_thermal_conductivity: Wärmeleitfähigkeit der Verfüllung in W/m·K
            n_multipoles: Anzahl der Multipole für die Berechnung
            
        Returns:
            Tuple (R_b, R_a): Bohrloch-Widerstand und interner Widerstand in m·K/W
        """
        # Vereinfachte Berechnung nach Hellström (1991)
        # Position der Rohre im Bohrloch (symmetrisch)
        x1 = shank_spacing / 2
        y1 = 0
        x2 = -shank_spacing / 2
        y2 = 0
        
        # Beta-Faktor (Verhältnis der Wärmeleitfähigkeiten)
        beta = (grout_thermal_conductivity - pipe_thermal_conductivity) / \
               (grout_thermal_conductivity + pipe_thermal_conductivity)
        
        # Abstand zwischen den Rohren
        d_12 = math.sqrt((x1 - x2)**2 + (y1 - y2)**2)
        
        # R_12: Thermischer Widerstand zwischen den Rohren
        r_12_term1 = math.log(d_12 / (2 * pipe_outer_radius))
        r_12_term2 = beta * math.log((borehole_radius**2 - (x1*x2 + y1*y2)) / 
                                     (borehole_radius * d_12))
        r_12 = (r_12_term1 + r_12_term2) / (2 * math.pi * grout_thermal_conductivity)
        
        # R_b: Bohrloch-Widerstand (von Rohr zur Bohrlochwand)
        sigma = (borehole_radius / pipe_outer_radius) * \
                math.sqrt(shank_spacing / (2 * borehole_radius))
        
        if sigma > 1:
            r_b = (1 / (2 * math.pi * grout_thermal_conductivity)) * \
                  (math.log(borehole_radius / pipe_outer_radius) + 
                   beta * math.log(borehole_radius / shank_spacing))
        else:
            r_b = (1 / (2 * math.pi * grout_thermal_conductivity)) * \
                  math.log(borehole_radius / pipe_outer_radius)
        
        # R_a: Interner Widerstand (zwischen Vor- und Rücklauf)
        r_a = 2 * r_12
        
        return r_b, r_a
    
    @staticmethod
    def calculate_double_u_tube_resistance(
        borehole_radius: float,
        pipe_outer_radius: float,
        shank_spacing: float,
        pipe_thermal_conductivity: float,
        grout_thermal_conductivity: float
    ) -> Tuple[float, float]:
        """
        Berechnet die thermischen Widerstände für ein Double-U-Rohr.
        
        Vereinfachte Annahme: 4 Rohre symmetrisch im Bohrloch angeordnet.
        """
        # Für Double-U: Abstand zum Zentrum
        r_pipes = shank_spacing / math.sqrt(2)
        
        # Äquivalenter Radius für 4 Rohre
        equiv_radius = 2 * pipe_outer_radius
        
        # Nutze Single-U Berechnung mit angepassten Parametern
        r_b, r_a = ThermalResistanceCalculator.calculate_single_u_tube_resistance(
            borehole_radius,
            equiv_radius,
            2 * r_pipes,
            pipe_thermal_conductivity,
            grout_thermal_conductivity
        )
        
        # Korrektur für Double-U (mehr Rohre = besserer Wärmeübergang)
        r_b = r_b * 0.7
        r_a = r_a * 0.5
        
        return r_b, r_a
    
    @staticmethod
    def calculate_coaxial_resistance(
        borehole_radius: float,
        outer_pipe_inner_radius: float,
        outer_pipe_outer_radius: float,
        inner_pipe_inner_radius: float,
        inner_pipe_outer_radius: float,
        outer_pipe_thermal_conductivity: float,
        inner_pipe_thermal_conductivity: float,
        annulus_thermal_conductivity: float
    ) -> Tuple[float, float]:
        """
        Berechnet die thermischen Widerstände für ein Koaxialrohr.
        
        Returns:
            Tuple (R_b, R_a): Bohrloch-Widerstand und interner Widerstand
        """
        # Widerstand des Ringquerschnitts (Außenrohr)
        r_outer = ThermalResistanceCalculator.calculate_pipe_resistance(
            2 * outer_pipe_inner_radius,
            2 * outer_pipe_outer_radius,
            outer_pipe_thermal_conductivity
        )
        
        # Widerstand des Innenrohrs
        r_inner = ThermalResistanceCalculator.calculate_pipe_resistance(
            2 * inner_pipe_inner_radius,
            2 * inner_pipe_outer_radius,
            inner_pipe_thermal_conductivity
        )
        
        # Widerstand des Ringquerschnitts zwischen den Rohren
        r_annulus = (1 / (2 * math.pi * annulus_thermal_conductivity)) * \
                    math.log(outer_pipe_inner_radius / inner_pipe_outer_radius)
        
        # Widerstand von Außenrohr zur Bohrlochwand
        r_grout = (1 / (2 * math.pi * annulus_thermal_conductivity)) * \
                  math.log(borehole_radius / outer_pipe_outer_radius)
        
        # Gesamt-Bohrloch-Widerstand
        r_b = r_outer + r_grout
        
        # Interner Widerstand (zwischen Vor- und Rücklauf)
        r_a = r_inner + r_annulus
        
        return r_b, r_a
    
    @staticmethod
    def calculate_total_resistance(
        r_b: float,
        r_a: float,
        r_pipe: float,
        r_conv: float
    ) -> float:
        """
        Berechnet den gesamten thermischen Widerstand.
        
        Args:
            r_b: Bohrloch-Widerstand (Rohr zu Bohrlochwand)
            r_a: Interner Widerstand (zwischen Vor- und Rücklauf)
            r_pipe: Rohr-Widerstand
            r_conv: Konvektiver Widerstand
            
        Returns:
            Gesamter thermischer Widerstand in m·K/W
        """
        r_total = r_b + r_pipe + r_conv
        return r_total


if __name__ == "__main__":
    # Test
    calc = ThermalResistanceCalculator()
    
    # Beispiel: Single-U-Rohr
    r_b, r_a = calc.calculate_single_u_tube_resistance(
        borehole_radius=0.115 / 2,  # 115 mm Durchmesser
        pipe_outer_radius=0.040 / 2,  # 40 mm Außendurchmesser
        shank_spacing=0.052,  # 52 mm Schenkelabstand
        pipe_thermal_conductivity=0.42,  # PE
        grout_thermal_conductivity=1.3  # Zement-Bentonit
    )
    
    print(f"Single-U Bohrloch-Widerstand R_b: {r_b:.4f} m·K/W")
    print(f"Single-U Interner Widerstand R_a: {r_a:.4f} m·K/W")









