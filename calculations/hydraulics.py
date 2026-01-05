"""Hydraulische Berechnungen für Erdwärmesonden-Systeme."""

import math
from typing import Tuple, Dict


class HydraulicsCalculator:
    """Berechnet hydraulische Parameter für Erdwärmesonden."""
    
    # Frostschutzmittel-Eigenschaften (Ethylenglykol-Wasser-Gemisch)
    # WICHTIG: Werte gelten für Betriebstemperatur 0°C (typische Sole-Temperatur im Heizbetrieb)
    # Vol% -> Dichte (kg/m³), Dyn. Viskosität (Pa·s), Wärmekapazität (J/kg·K)
    # Quelle: VDI-Wärmeatlas D3.1, 11. Auflage (2024)
    # 
    # ÄNDERUNG v3.3.0-beta1: Viskositätswerte korrigiert für realistische 0°C-Bedingungen
    # Vorher: Werte entsprachen ~15°C → Reynolds zu hoch → Druckverlust unterschätzt
    # Jetzt: Werte entsprechen 0°C → Reynolds realistisch → Druckverlust korrekt
    # 
    # Validierung: UBeG Geothermie-Studie Gau-Algesheim bestätigt Temperaturbereich -3°C bis 13°C
    ANTIFREEZE_PROPERTIES = {
        0: {'density': 1000, 'viscosity': 0.0018, 'heat_capacity': 4190, 'freeze_temp': 0},
        10: {'density': 1013, 'viscosity': 0.0024, 'heat_capacity': 4140, 'freeze_temp': -4},
        20: {'density': 1026, 'viscosity': 0.0032, 'heat_capacity': 4050, 'freeze_temp': -8},
        25: {'density': 1033, 'viscosity': 0.0037, 'heat_capacity': 4000, 'freeze_temp': -11},
        30: {'density': 1039, 'viscosity': 0.0045, 'heat_capacity': 3950, 'freeze_temp': -15},
        35: {'density': 1045, 'viscosity': 0.0058, 'heat_capacity': 3900, 'freeze_temp': -19},
        40: {'density': 1052, 'viscosity': 0.0075, 'heat_capacity': 3850, 'freeze_temp': -24},
    }
    
    @staticmethod
    def calculate_required_flow_rate(
        heat_capacity_kw: float,
        temperature_difference: float = 3.0,
        antifreeze_concentration: float = 25
    ) -> Dict[str, float]:
        """
        Berechnet den erforderlichen Volumenstrom.
        
        Args:
            heat_capacity_kw: Wärmeleistung in kW
            temperature_difference: Temperaturdifferenz Vor-/Rücklauf in K (Standard: 3K)
            antifreeze_concentration: Frostschutzkonzentration in Vol% (Standard: 25%)
            
        Returns:
            Dictionary mit Volumenströmen in verschiedenen Einheiten
        """
        # Fluid-Eigenschaften interpolieren
        props = HydraulicsCalculator._get_fluid_properties(antifreeze_concentration)
        
        # Berechnung: Q = m_dot * c_p * dT
        # m_dot = Q / (c_p * dT)
        heat_watts = heat_capacity_kw * 1000
        mass_flow_rate = heat_watts / (props['heat_capacity'] * temperature_difference)  # kg/s
        
        # Volumenstrom
        volume_flow_rate_m3s = mass_flow_rate / props['density']  # m³/s
        volume_flow_rate_m3h = volume_flow_rate_m3s * 3600  # m³/h
        volume_flow_rate_lmin = volume_flow_rate_m3s * 1000 * 60  # l/min
        
        return {
            'mass_flow_kg_s': mass_flow_rate,
            'volume_flow_m3_s': volume_flow_rate_m3s,
            'volume_flow_m3_h': volume_flow_rate_m3h,
            'volume_flow_l_min': volume_flow_rate_lmin,
            'temperature_difference': temperature_difference,
            'antifreeze_concentration': antifreeze_concentration
        }
    
    @staticmethod
    def calculate_pressure_drop(
        pipe_length: float,
        pipe_diameter: float,
        volume_flow_m3h: float,
        antifreeze_concentration: float = 25,
        roughness: float = 0.0015
    ) -> Dict[str, float]:
        """
        Berechnet den Druckverlust in einem Rohr.
        
        Args:
            pipe_length: Rohrlänge in m
            pipe_diameter: Rohr-Innendurchmesser in m
            volume_flow_m3h: Volumenstrom in m³/h
            antifreeze_concentration: Frostschutzkonzentration in Vol%
            roughness: Rohrrauhigkeit in mm (Standard: 1.5mm für PE)
            
        Returns:
            Dictionary mit Druckverlusten
        """
        # Fluid-Eigenschaften
        props = HydraulicsCalculator._get_fluid_properties(antifreeze_concentration)
        
        # Umrechnung Volumenstrom
        volume_flow_m3s = volume_flow_m3h / 3600
        
        # Strömungsgeschwindigkeit
        area = math.pi * (pipe_diameter / 2) ** 2
        velocity = volume_flow_m3s / area  # m/s
        
        # Reynolds-Zahl
        reynolds = (props['density'] * velocity * pipe_diameter) / props['viscosity']
        
        # Reibungsbeiwert nach Colebrook-White
        roughness_ratio = roughness / 1000 / pipe_diameter
        
        if reynolds < 2300:
            # Laminare Strömung
            friction_factor = 64 / reynolds
        else:
            # Turbulente Strömung (Vereinfachte Colebrook-Gleichung)
            friction_factor = 0.25 / (math.log10(roughness_ratio / 3.7 + 5.74 / (reynolds ** 0.9))) ** 2
        
        # Druckverlust nach Darcy-Weisbach
        pressure_drop_pa = friction_factor * (pipe_length / pipe_diameter) * \
                          (props['density'] * velocity ** 2) / 2
        
        # Umrechnungen
        pressure_drop_bar = pressure_drop_pa / 100000
        pressure_drop_mbar = pressure_drop_pa / 100
        
        return {
            'pressure_drop_pa': pressure_drop_pa,
            'pressure_drop_bar': pressure_drop_bar,
            'pressure_drop_mbar': pressure_drop_mbar,
            'velocity_m_s': velocity,
            'reynolds': reynolds,
            'friction_factor': friction_factor,
            'flow_regime': 'laminar' if reynolds < 2300 else 'turbulent'
        }
    
    @staticmethod
    def calculate_pump_power(
        volume_flow_m3h: float,
        pressure_drop_bar: float,
        pump_efficiency: float = 0.5
    ) -> Dict[str, float]:
        """
        Berechnet die erforderliche Pumpenleistung.
        
        Args:
            volume_flow_m3h: Volumenstrom in m³/h
            pressure_drop_bar: Druckverlust in bar
            pump_efficiency: Pumpenwirkungsgrad (Standard: 0.5 = 50%)
            
        Returns:
            Dictionary mit Pumpenleistungen
        """
        # Umrechnung
        volume_flow_m3s = volume_flow_m3h / 3600
        pressure_drop_pa = pressure_drop_bar * 100000
        
        # Hydraulische Leistung
        hydraulic_power_w = volume_flow_m3s * pressure_drop_pa
        
        # Elektrische Leistung
        electric_power_w = hydraulic_power_w / pump_efficiency
        
        return {
            'hydraulic_power_w': hydraulic_power_w,
            'electric_power_w': electric_power_w,
            'electric_power_kw': electric_power_w / 1000,
            'pump_efficiency': pump_efficiency
        }
    
    @staticmethod
    def calculate_total_system_pressure_drop(
        borehole_depth: float,
        num_boreholes: int,
        num_circuits: int,
        pipe_inner_diameter: float,
        volume_flow_total_m3h: float,
        antifreeze_concentration: float = 25,
        additional_losses_bar: float = 0.5,
        circuits_per_borehole: int = 1
    ) -> Dict[str, float]:
        """
        Berechnet den Gesamt-Druckverlust des Systems.
        
        Args:
            borehole_depth: Bohrtiefe in m
            num_boreholes: Anzahl Bohrungen
            num_circuits: Anzahl parallele Kreise
            pipe_inner_diameter: Rohr-Innendurchmesser in m
            volume_flow_total_m3h: Gesamt-Volumenstrom in m³/h
            antifreeze_concentration: Frostschutzkonzentration in Vol%
            additional_losses_bar: Zusätzliche Verluste (Verteiler, Ventile) in bar
            
        Returns:
            Dictionary mit Druckverlusten
        """
        # Volumenstrom pro System-Kreis
        volume_flow_per_circuit = volume_flow_total_m3h / num_circuits
        
        # Anzahl Bohrungen pro System-Kreis
        num_boreholes_per_circuit = num_boreholes / num_circuits if num_circuits > 0 else num_boreholes
        
        # Rohrlänge pro System-Kreis:
        # - Pro Bohrung: circuits_per_borehole × 2 × Tiefe (jeder Kreis hat Vorlauf + Rücklauf)
        #   Bei 4-Rohr-Systemen: 2 Kreise pro Bohrung = 2 × 2 × Tiefe = 4 × Tiefe pro Bohrung
        # - Horizontale Leitung: geschätzt 50m pro System-Kreis
        pipe_length_per_circuit = num_boreholes_per_circuit * circuits_per_borehole * 2 * borehole_depth + 50
        
        # Druckverlust pro Kreis
        pressure_drop_circuit = HydraulicsCalculator.calculate_pressure_drop(
            pipe_length_per_circuit,
            pipe_inner_diameter,
            volume_flow_per_circuit,
            antifreeze_concentration
        )
        
        # Gesamt-Druckverlust (Kreise parallel)
        total_pressure_drop_bar = pressure_drop_circuit['pressure_drop_bar'] + additional_losses_bar
        
        return {
            'pressure_drop_borehole_bar': pressure_drop_circuit['pressure_drop_bar'],
            'additional_losses_bar': additional_losses_bar,
            'total_pressure_drop_bar': total_pressure_drop_bar,
            'total_pressure_drop_mbar': total_pressure_drop_bar * 1000,
            'volume_flow_per_circuit_m3h': volume_flow_per_circuit,
            'pipe_length_per_circuit_m': pipe_length_per_circuit,
            'velocity_m_s': pressure_drop_circuit['velocity_m_s'],
            'reynolds': pressure_drop_circuit['reynolds']
        }
    
    @staticmethod
    def calculate_detailed_pressure_analysis(
        borehole_depth: float,
        num_boreholes: int,
        num_circuits: int,
        pipe_inner_diameter: float,
        volume_flow_total_m3h: float,
        antifreeze_concentration: float = 25,
        horizontal_length_estimate: float = 50,
        circuits_per_borehole: int = 1,
        fittings: Dict[str, int] = None
    ) -> Dict[str, any]:
        """
        Detaillierte Druckverlust-Analyse mit Aufschlüsselung aller Komponenten.
        
        NEU in v3.3.0-beta1: Zeigt genau, wo Druckverluste auftreten.
        
        Args:
            borehole_depth: Bohrtiefe in m
            num_boreholes: Anzahl Bohrungen
            num_circuits: Anzahl parallele Kreise
            pipe_inner_diameter: Rohr-Innendurchmesser in m
            volume_flow_total_m3h: Gesamt-Volumenstrom in m³/h
            antifreeze_concentration: Frostschutzkonzentration in Vol%
            horizontal_length_estimate: Geschätzte horizontale Leitungslänge in m
            circuits_per_borehole: Kreise pro Bohrung (1=Single-U, 2=Doppel-U)
            fittings: Dictionary mit Formstücken, z.B. {"T-piece": 4, "elbow_90": 8}
            
        Returns:
            Dictionary mit detaillierter Aufschlüsselung
        """
        # Standard-Formstücke wenn nicht angegeben
        if fittings is None:
            # Schätzung basierend auf typischer Installation
            fittings = {
                "T-piece": num_circuits * 2,  # Verteiler
                "elbow_90": num_circuits * 4,  # Bögen
                "valve": num_circuits * 2,  # Absperrschieber
            }
        
        # Volumenstrom pro System-Kreis
        volume_flow_per_circuit = volume_flow_total_m3h / num_circuits
        num_boreholes_per_circuit = num_boreholes / num_circuits if num_circuits > 0 else num_boreholes
        
        # 1. BOHRUNGEN (vertikal)
        borehole_length_per_circuit = num_boreholes_per_circuit * circuits_per_borehole * 2 * borehole_depth
        borehole_dp = HydraulicsCalculator.calculate_pressure_drop(
            borehole_length_per_circuit,
            pipe_inner_diameter,
            volume_flow_per_circuit,
            antifreeze_concentration
        )
        
        # 2. HORIZONTALE ANBINDUNG
        horizontal_dp = HydraulicsCalculator.calculate_pressure_drop(
            horizontal_length_estimate,
            pipe_inner_diameter,
            volume_flow_per_circuit,
            antifreeze_concentration
        )
        
        # 3. FORMSTÜCKE & VENTILE (Druckverlustbeiwerte ζ)
        zeta_values = {
            "T-piece": 0.6,
            "elbow_90": 0.8,
            "elbow_45": 0.4,
            "valve": 0.2,
            "filter": 1.0,
        }
        
        # Dynamischer Druck
        props = HydraulicsCalculator._get_fluid_properties(antifreeze_concentration)
        area = math.pi * (pipe_inner_diameter / 2) ** 2
        velocity = (volume_flow_per_circuit / 3600) / area
        dynamic_pressure_pa = (props['density'] * velocity ** 2) / 2
        
        # Summe aller Formstück-Verluste
        total_zeta = sum(zeta_values.get(fitting_type, 0.5) * count 
                         for fitting_type, count in fittings.items())
        fittings_pressure_drop_pa = total_zeta * dynamic_pressure_pa
        fittings_pressure_drop_bar = fittings_pressure_drop_pa / 100000
        
        # 4. WÄRMETAUSCHER/FILTER (Annahme)
        heat_exchanger_dp_bar = 0.05
        
        # GESAMT
        total_dp_bar = (borehole_dp['pressure_drop_bar'] + 
                        horizontal_dp['pressure_drop_bar'] +
                        fittings_pressure_drop_bar +
                        heat_exchanger_dp_bar)
        
        # Prozentuale Anteile
        total_dp_pa = total_dp_bar * 100000
        borehole_percent = (borehole_dp['pressure_drop_pa'] / total_dp_pa * 100) if total_dp_pa > 0 else 0
        horizontal_percent = (horizontal_dp['pressure_drop_pa'] / total_dp_pa * 100) if total_dp_pa > 0 else 0
        fittings_percent = (fittings_pressure_drop_pa / total_dp_pa * 100) if total_dp_pa > 0 else 0
        heat_exchanger_percent = (heat_exchanger_dp_bar * 100000 / total_dp_pa * 100) if total_dp_pa > 0 else 0
        
        # Optimierungsvorschläge
        suggestions = []
        if borehole_dp['reynolds'] < 2500:
            suggestions.append(
                f"Reynolds in Sonden kritisch ({borehole_dp['reynolds']:.0f}) → "
                f"ΔT reduzieren erhöht Durchfluss"
            )
        if fittings_percent > 30:
            potential_saving = fittings_pressure_drop_bar * 0.3
            suggestions.append(
                f"Formstücke haben hohen Anteil ({fittings_percent:.0f}%) → "
                f"Optimierung spart bis zu {potential_saving:.2f} bar"
            )
        if borehole_percent > 60:
            suggestions.append(
                f"Bohrungen dominant ({borehole_percent:.0f}%) → "
                f"Größerer Rohrdurchmesser reduziert Druckverlust"
            )
        
        return {
            'components': {
                'boreholes': {
                    'length_m': borehole_length_per_circuit,
                    'velocity_m_s': borehole_dp['velocity_m_s'],
                    'reynolds': borehole_dp['reynolds'],
                    'flow_regime': borehole_dp['flow_regime'],
                    'pressure_drop_bar': borehole_dp['pressure_drop_bar'],
                    'percent': borehole_percent
                },
                'horizontal': {
                    'length_m': horizontal_length_estimate,
                    'velocity_m_s': horizontal_dp['velocity_m_s'],
                    'reynolds': horizontal_dp['reynolds'],
                    'pressure_drop_bar': horizontal_dp['pressure_drop_bar'],
                    'percent': horizontal_percent
                },
                'fittings': {
                    'items': fittings,
                    'total_zeta': total_zeta,
                    'pressure_drop_bar': fittings_pressure_drop_bar,
                    'percent': fittings_percent
                },
                'heat_exchanger': {
                    'pressure_drop_bar': heat_exchanger_dp_bar,
                    'percent': heat_exchanger_percent
                }
            },
            'total_pressure_drop_bar': total_dp_bar,
            'total_pressure_drop_mbar': total_dp_bar * 1000,
            'suggestions': suggestions
        }
    
    @staticmethod
    def _get_fluid_properties(concentration: float) -> Dict[str, float]:
        """
        Interpoliert Fluid-Eigenschaften für gegebene Konzentration.
        
        Args:
            concentration: Frostschutzkonzentration in Vol%
            
        Returns:
            Dictionary mit Fluid-Eigenschaften
        """
        # Finde nächste Werte in Tabelle
        concentrations = sorted(HydraulicsCalculator.ANTIFREEZE_PROPERTIES.keys())
        
        if concentration <= concentrations[0]:
            return HydraulicsCalculator.ANTIFREEZE_PROPERTIES[concentrations[0]]
        
        if concentration >= concentrations[-1]:
            return HydraulicsCalculator.ANTIFREEZE_PROPERTIES[concentrations[-1]]
        
        # Lineare Interpolation
        for i in range(len(concentrations) - 1):
            c1 = concentrations[i]
            c2 = concentrations[i + 1]
            
            if c1 <= concentration <= c2:
                props1 = HydraulicsCalculator.ANTIFREEZE_PROPERTIES[c1]
                props2 = HydraulicsCalculator.ANTIFREEZE_PROPERTIES[c2]
                
                factor = (concentration - c1) / (c2 - c1)
                
                return {
                    'density': props1['density'] + factor * (props2['density'] - props1['density']),
                    'viscosity': props1['viscosity'] + factor * (props2['viscosity'] - props1['viscosity']),
                    'heat_capacity': props1['heat_capacity'] + factor * (props2['heat_capacity'] - props1['heat_capacity']),
                    'freeze_temp': props1['freeze_temp'] + factor * (props2['freeze_temp'] - props1['freeze_temp'])
                }
        
        return HydraulicsCalculator.ANTIFREEZE_PROPERTIES[25]  # Fallback


if __name__ == "__main__":
    # Test
    calc = HydraulicsCalculator()
    
    print("=== Hydraulik-Berechnungen ===\n")
    
    # 1. Volumenstrom berechnen
    print("1. Erforderlicher Volumenstrom:")
    flow = calc.calculate_required_flow_rate(
        heat_capacity_kw=6.0,
        temperature_difference=3.0,
        antifreeze_concentration=25
    )
    print(f"   Wärmeleistung: 6 kW, ΔT=3K, Sole 25%")
    print(f"   Volumenstrom: {flow['volume_flow_m3_h']:.3f} m³/h ({flow['volume_flow_l_min']:.1f} l/min)")
    
    # 2. Druckverlust
    print("\n2. Druckverlust:")
    pressure = calc.calculate_pressure_drop(
        pipe_length=200,
        pipe_diameter=0.026,  # 32mm Außen, ca. 26mm Innen
        volume_flow_m3h=flow['volume_flow_m3_h'],
        antifreeze_concentration=25
    )
    print(f"   200m Rohr, Ø 26mm innen")
    print(f"   Druckverlust: {pressure['pressure_drop_mbar']:.1f} mbar")
    print(f"   Geschwindigkeit: {pressure['velocity_m_s']:.2f} m/s")
    print(f"   Reynolds: {pressure['reynolds']:.0f} ({pressure['flow_regime']})")
    
    # 3. Gesamt-System
    print("\n3. Gesamt-System (2 Bohrungen, 100m tief):")
    system = calc.calculate_total_system_pressure_drop(
        borehole_depth=100,
        num_boreholes=2,
        num_circuits=1,
        pipe_inner_diameter=0.026,
        volume_flow_total_m3h=flow['volume_flow_m3_h'],
        antifreeze_concentration=25
    )
    print(f"   Druckverlust Sonden: {system['pressure_drop_borehole_bar']:.2f} bar")
    print(f"   Zusatzverluste: {system['additional_losses_bar']:.2f} bar")
    print(f"   GESAMT: {system['total_pressure_drop_bar']:.2f} bar ({system['total_pressure_drop_mbar']:.0f} mbar)")
    
    # 4. Pumpenleistung
    print("\n4. Erforderliche Pumpenleistung:")
    pump = calc.calculate_pump_power(
        volume_flow_m3h=flow['volume_flow_m3_h'],
        pressure_drop_bar=system['total_pressure_drop_bar'],
        pump_efficiency=0.5
    )
    print(f"   Hydraulische Leistung: {pump['hydraulic_power_w']:.0f} W")
    print(f"   Elektrische Leistung: {pump['electric_power_w']:.0f} W ({pump['electric_power_kw']:.2f} kW)")








