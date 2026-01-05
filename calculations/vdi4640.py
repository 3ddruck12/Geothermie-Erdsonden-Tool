"""VDI 4640 / Koenigsdorff-Methode für Erdwärmesonden-Auslegung.

Diese Implementierung berücksichtigt:
- Drei Lasttypen (Grundlast, periodisch, Spitzenlast)
- Separate Auslegung für Heizen und Kühlen
- Dominante Last wird automatisch erkannt
- Berechnung der Wärmepumpenaustrittstemperatur
"""

import math
import os
from datetime import datetime
from typing import Dict, Tuple, List, Optional
from dataclasses import dataclass


@dataclass
class VDI4640Result:
    """Ergebnis einer VDI 4640 Berechnung."""
    # Sondenlänge
    required_depth_heating: float      # m - Auslegung nach Heizlast
    required_depth_cooling: float      # m - Auslegung nach Kühllast
    required_depth_final: float        # m - Größerer Wert (auslegungsrelevant)
    design_case: str                   # "heating" oder "cooling"
    
    # Austrittstemperaturen
    t_wp_aus_heating_min: float        # °C - Minimale WP-Austrittstemperatur (Heizen)
    t_wp_aus_cooling_max: float        # °C - Maximale WP-Austrittstemperatur (Kühlen)
    
    # Temperaturkomponenten (Heizen)
    delta_t_grundlast_heating: float   # K
    delta_t_per_heating: float         # K
    delta_t_peak_heating: float        # K
    delta_t_fluid_heating: float       # K
    
    # Temperaturkomponenten (Kühlen)
    delta_t_grundlast_cooling: float   # K
    delta_t_per_cooling: float         # K
    delta_t_peak_cooling: float        # K
    delta_t_fluid_cooling: float       # K
    
    # Thermische Widerstände
    r_grundlast: float                 # m·K/W
    r_per: float                       # m·K/W
    r_peak: float                      # m·K/W
    r_borehole: float                  # m·K/W
    
    # Lasten
    q_nettogrundlast_heating: float    # W
    q_per_heating: float               # W
    q_peak_heating: float              # W
    q_nettogrundlast_cooling: float    # W
    q_per_cooling: float               # W
    q_peak_cooling: float              # W
    
    # g-Funktionen
    g_grundlast: float
    g_per: float
    g_peak: float


class VDI4640Calculator:
    """
    Berechnung nach VDI 4640 / Koenigsdorff-Methode.
    
    Berücksichtigt:
    - Drei Lasttypen (Grundlast, periodisch, Spitzenlast)
    - Separate Auslegung für Heizen und Kühlen
    - Dominante Last wird automatisch erkannt
    - Berechnung der Wärmepumpenaustrittstemperatur
    """
    
    def __init__(self, debug=False, debug_file=None):
        """
        Args:
            debug: Wenn True, werden alle Berechnungsschritte protokolliert
            debug_file: Pfad zur Debug-Datei (optional, Standard: vdi4640_debug.log)
        """
        self.debug = debug
        self.debug_file = debug_file or "vdi4640_debug.log"
        if self.debug:
            self._init_debug_file()
    
    def _init_debug_file(self):
        """Initialisiert die Debug-Datei."""
        with open(self.debug_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("VDI 4640 DEBUG-PROTOKOLL\n")
            f.write(f"Erstellt: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 80 + "\n\n")
    
    def _debug(self, message: str, values: Dict = None):
        """Schreibt Debug-Informationen in die Datei."""
        if not self.debug:
            return
        
        with open(self.debug_file, 'a', encoding='utf-8') as f:
            f.write(f"{message}\n")
            if values:
                for key, value in values.items():
                    if isinstance(value, float):
                        f.write(f"  {key}: {value:.6f}\n")
                    else:
                        f.write(f"  {key}: {value}\n")
            f.write("\n")
    
    def calculate_complete(
        self,
        # Bodeneigenschaften
        ground_thermal_conductivity: float,  # W/m·K
        ground_thermal_diffusivity: float,   # m²/s
        t_undisturbed: float,                # °C - Ungestörte Erdreichtemperatur
        
        # Bohrlochgeometrie
        borehole_diameter: float,            # mm
        borehole_depth_initial: float,       # m - Startwert für Iteration
        n_boreholes: int = 1,                # Anzahl Sonden
        
        # Bohrlochwiderstand
        r_borehole: float = 0.1,             # m·K/W
        
        # Heizlasten
        annual_heating_demand: float = 10.0,        # kWh/Jahr
        peak_heating_load: float = 6.0,            # kW
        monthly_heating_factors: Optional[List[float]] = None,       # 12 Werte
        
        # Kühllasten
        annual_cooling_demand: float = 0.0,        # kWh/Jahr
        peak_cooling_load: float = 0.0,            # kW
        monthly_cooling_factors: Optional[List[float]] = None,       # 12 Werte
        
        # Wärmepumpe
        heat_pump_cop_heating: float = 4.0,        # -
        heat_pump_cop_cooling: float = 4.0,        # - (EER)
        
        # Temperaturgrenzen
        t_fluid_min_required: float = -2.0,        # °C - Minimale Fluidtemperatur (Heizen)
        t_fluid_max_required: float = 35.0,        # °C - Maximale Fluidtemperatur (Kühlen)
        delta_t_fluid: float = 3.0,                # K - Temperaturdifferenz im Fluid
        
    ) -> VDI4640Result:
        """
        Führt komplette VDI 4640 Berechnung durch.
        
        Returns:
            VDI4640Result mit allen Berechnungsdetails
        """
        
        # === DEBUG: Eingabeparameter ===
        self._debug("=== EINGABEPARAMETER ===", {
            "Wärmeleitfähigkeit": ground_thermal_conductivity,
            "Wärmediffusivität": ground_thermal_diffusivity,
            "Ungestörte Bodentemperatur": t_undisturbed,
            "Bohrdurchmesser": borehole_diameter,
            "Startwert Tiefe": borehole_depth_initial,
            "Anzahl Bohrungen": n_boreholes,
            "R_Bohrloch": r_borehole,
            "Jahres-Heizenergie": annual_heating_demand,
            "Spitzenlast Heizen": peak_heating_load,
            "Jahres-Kühlenergie": annual_cooling_demand,
            "Spitzenlast Kühlen": peak_cooling_load,
            "COP Heizen": heat_pump_cop_heating,
            "COP Kühlen": heat_pump_cop_cooling,
            "T_Fluid_min": t_fluid_min_required,
            "T_Fluid_max": t_fluid_max_required,
            "Delta_T_Fluid": delta_t_fluid
        })
        
        # Standardwerte für monatliche Faktoren
        if monthly_heating_factors is None:
            monthly_heating_factors = [
                0.155, 0.148, 0.125, 0.099, 0.064, 0.0,
                0.0, 0.0, 0.061, 0.087, 0.117, 0.144
            ]
        
        if monthly_cooling_factors is None:
            monthly_cooling_factors = [
                0.0, 0.0, 0.0, 0.05, 0.15, 0.25,
                0.30, 0.25, 0.0, 0.0, 0.0, 0.0
            ]
        
        # === SCHRITT 1: Thermische Widerstände berechnen ===
        resistances = self._calculate_thermal_resistances(
            ground_thermal_conductivity,
            ground_thermal_diffusivity,
            borehole_depth_initial,
            borehole_diameter / 2000.0  # mm → m Radius
        )
        
        self._debug("=== SCHRITT 1: THERMISCHE WIDERSTÄNDE ===", {
            "R_Grundlast (10 Jahre)": resistances['r_grundlast'],
            "R_Periodisch (1 Monat)": resistances['r_per'],
            "R_Peak (6 Stunden)": resistances['r_peak'],
            "g_Grundlast": resistances['g_grundlast'],
            "g_Periodisch": resistances['g_per'],
            "g_Peak": resistances['g_peak']
        })
        
        # === SCHRITT 2: Lasten berechnen ===
        
        # HEIZLASTEN
        loads_heating = self._calculate_loads(
            annual_demand=annual_heating_demand,
            peak_load=peak_heating_load,
            monthly_factors=monthly_heating_factors,
            cop=heat_pump_cop_heating,
            is_heating=True
        )
        
        # KÜHLLASTEN
        loads_cooling = self._calculate_loads(
            annual_demand=annual_cooling_demand,
            peak_load=peak_cooling_load,
            monthly_factors=monthly_cooling_factors,
            cop=heat_pump_cop_cooling,
            is_heating=False
        )
        
        self._debug("=== SCHRITT 2: LASTEN ===", {
            "HEIZEN - Q_Nettogrundlast": loads_heating['q_nettogrundlast'],
            "HEIZEN - Q_Periodisch": loads_heating['q_per'],
            "HEIZEN - Q_Peak": loads_heating['q_peak'],
            "KÜHLEN - Q_Nettogrundlast": loads_cooling['q_nettogrundlast'],
            "KÜHLEN - Q_Periodisch": loads_cooling['q_per'],
            "KÜHLEN - Q_Peak": loads_cooling['q_peak']
        })
        
        # === SCHRITT 3: Sondenlänge für HEIZEN berechnen ===
        h_heating = self._calculate_borehole_length(
            q_grundlast=loads_heating['q_nettogrundlast'],
            q_per=loads_heating['q_per'],
            q_peak=loads_heating['q_peak'],
            r_grundlast=resistances['r_grundlast'],
            r_per=resistances['r_per'],
            r_peak=resistances['r_peak'],
            r_borehole=r_borehole,
            t_ground=t_undisturbed,
            t_fluid_limit=t_fluid_min_required,
            n_boreholes=n_boreholes,
            is_heating=True
        )
        
        # === SCHRITT 4: Sondenlänge für KÜHLEN berechnen ===
        h_cooling = self._calculate_borehole_length(
            q_grundlast=loads_cooling['q_nettogrundlast'],
            q_per=loads_cooling['q_per'],
            q_peak=loads_cooling['q_peak'],
            r_grundlast=resistances['r_grundlast'],
            r_per=resistances['r_per'],
            r_peak=resistances['r_peak'],
            r_borehole=r_borehole,
            t_ground=t_undisturbed,
            t_fluid_limit=t_fluid_max_required,
            n_boreholes=n_boreholes,
            is_heating=False
        )
        
        self._debug("=== SCHRITT 3 & 4: SONDENLÄNGE ===", {
            "H_Heizen": h_heating,
            "H_Kühlen": h_cooling
        })
        
        # === SCHRITT 5: Auslegungsrelevanten Fall bestimmen ===
        if h_heating > h_cooling:
            h_final = h_heating
            design_case = "heating"
        else:
            h_final = h_cooling
            design_case = "cooling"
        
        self._debug("=== SCHRITT 5: AUSLEGUNGSFALL ===", {
            "Auslegungsfall": design_case,
            "Erforderliche Sondenlänge": h_final
        })
        
        # === SCHRITT 6: Wärmepumpenaustrittstemperaturen berechnen ===
        
        # Für HEIZEN (mit finaler Sondenlänge)
        t_wp_aus_heating, deltas_heating = self._calculate_wp_exit_temperature(
            h_sonde=h_final,
            n_boreholes=n_boreholes,
            q_grundlast=loads_heating['q_nettogrundlast'],
            q_per=loads_heating['q_per'],
            q_peak=loads_heating['q_peak'],
            r_grundlast=resistances['r_grundlast'],
            r_per=resistances['r_per'],
            r_peak=resistances['r_peak'],
            r_borehole=r_borehole,
            lambda_ground=ground_thermal_conductivity,
            t_undisturbed=t_undisturbed,
            delta_t_fluid=delta_t_fluid,
            is_heating=True
        )
        
        # Für KÜHLEN (mit finaler Sondenlänge)
        t_wp_aus_cooling, deltas_cooling = self._calculate_wp_exit_temperature(
            h_sonde=h_final,
            n_boreholes=n_boreholes,
            q_grundlast=loads_cooling['q_nettogrundlast'],
            q_per=loads_cooling['q_per'],
            q_peak=loads_cooling['q_peak'],
            r_grundlast=resistances['r_grundlast'],
            r_per=resistances['r_per'],
            r_peak=resistances['r_peak'],
            r_borehole=r_borehole,
            lambda_ground=ground_thermal_conductivity,
            t_undisturbed=t_undisturbed,
            delta_t_fluid=delta_t_fluid,
            is_heating=False
        )
        
        # === DEBUG: Finale Ergebnisse ===
        self._debug("=== FINALE ERGEBNISSE ===", {
            "Erforderliche Sondenlänge": h_final,
            "Anzahl Bohrungen": n_boreholes,
            "Gesamtlänge": h_final * n_boreholes,
            "WP-Austrittstemp. Heizen": t_wp_aus_heating,
            "WP-Austrittstemp. Kühlen": t_wp_aus_cooling,
            "Delta_T_Grundlast (Heizen)": deltas_heating[0],
            "Delta_T_Periodisch (Heizen)": deltas_heating[1],
            "Delta_T_Peak (Heizen)": deltas_heating[2]
        })
        
        # === ERGEBNIS ===
        return VDI4640Result(
            required_depth_heating=h_heating,
            required_depth_cooling=h_cooling,
            required_depth_final=h_final,
            design_case=design_case,
            t_wp_aus_heating_min=t_wp_aus_heating,
            t_wp_aus_cooling_max=t_wp_aus_cooling,
            delta_t_grundlast_heating=deltas_heating[0],
            delta_t_per_heating=deltas_heating[1],
            delta_t_peak_heating=deltas_heating[2],
            delta_t_fluid_heating=delta_t_fluid,
            delta_t_grundlast_cooling=deltas_cooling[0],
            delta_t_per_cooling=deltas_cooling[1],
            delta_t_peak_cooling=deltas_cooling[2],
            delta_t_fluid_cooling=delta_t_fluid,
            r_grundlast=resistances['r_grundlast'],
            r_per=resistances['r_per'],
            r_peak=resistances['r_peak'],
            r_borehole=r_borehole,
            q_nettogrundlast_heating=loads_heating['q_nettogrundlast'],
            q_per_heating=loads_heating['q_per'],
            q_peak_heating=loads_heating['q_peak'],
            q_nettogrundlast_cooling=loads_cooling['q_nettogrundlast'],
            q_per_cooling=loads_cooling['q_per'],
            q_peak_cooling=loads_cooling['q_peak'],
            g_grundlast=resistances['g_grundlast'],
            g_per=resistances['g_per'],
            g_peak=resistances['g_peak']
        )
    
    def _calculate_borehole_length(
        self,
        q_grundlast: float,
        q_per: float,
        q_peak: float,
        r_grundlast: float,
        r_per: float,
        r_peak: float,
        r_borehole: float,
        t_ground: float,
        t_fluid_limit: float,
        n_boreholes: int,
        is_heating: bool
    ) -> float:
        """
        Berechnet erforderliche Sondenlänge nach VDI 4640.
        
        H_Sonde = [Q_netto·(R_grundlast + R_B) + Q_per·(R_per + R_B) + Q_peak·(R_peak + R_B)]
                  / (ΔT_Reaktion · N_Sonden)
        """
        # Temperaturdifferenz
        if is_heating:
            # Bei Heizen: Erdreich wärmer als Fluid → positive Differenz
            delta_t_reaction = t_ground - t_fluid_limit
        else:
            # Bei Kühlen: Erdreich kälter als Fluid → positive Differenz
            delta_t_reaction = t_fluid_limit - t_ground
        
        if delta_t_reaction <= 0:
            raise ValueError(
                f"Ungültige Temperaturdifferenz: {delta_t_reaction:.2f} K. "
                f"Prüfe Temperaturgrenzen!"
            )
        
        # VDI 4640 Formel - Schritt für Schritt
        term1 = abs(q_grundlast) * (r_grundlast + r_borehole)
        term2 = abs(q_per) * (r_per + r_borehole)
        term3 = abs(q_peak) * (r_peak + r_borehole)
        
        numerator = term1 + term2 + term3
        denominator = delta_t_reaction * n_boreholes
        
        h_sonde = numerator / denominator
        
        # Debug-Ausgabe
        if self.debug:
            mode = "HEIZEN" if is_heating else "KÜHLEN"
            self._debug(f"=== SONDENLÄNGE BERECHNUNG ({mode}) ===", {
                "Q_Grundlast": q_grundlast,
                "Q_Periodisch": q_per,
                "Q_Peak": q_peak,
                "R_Grundlast": r_grundlast,
                "R_Periodisch": r_per,
                "R_Peak": r_peak,
                "R_Bohrloch": r_borehole,
                "T_Erdreich": t_ground,
                "T_Fluid_Limit": t_fluid_limit,
                "Delta_T_Reaktion": delta_t_reaction,
                "Anzahl Bohrungen": n_boreholes,
                "Term 1 (Q_Grundlast)": term1,
                "Term 2 (Q_Periodisch)": term2,
                "Term 3 (Q_Peak)": term3,
                "Zähler (Summe)": numerator,
                "Nenner": denominator,
                "H_Sonde": h_sonde
            })
        
        return h_sonde
    
    def _calculate_wp_exit_temperature(
        self,
        h_sonde: float,
        n_boreholes: int,
        q_grundlast: float,
        q_per: float,
        q_peak: float,
        r_grundlast: float,
        r_per: float,
        r_peak: float,
        r_borehole: float,
        lambda_ground: float,
        t_undisturbed: float,
        delta_t_fluid: float,
        is_heating: bool
    ) -> Tuple[float, Tuple[float, float, float]]:
        """
        Berechnet die Wärmepumpenaustrittstemperatur.
        
        T_WP,aus = T_ungestört + ΔT_Grundlast + ΔT_per + ΔT_peak - 0.5·ΔT_Fluid
        
        Returns:
            (T_WP_aus, (ΔT_Grundlast, ΔT_per, ΔT_peak))
        """
        # Spezifische Last pro Meter
        q_grundlast_per_m = abs(q_grundlast) / (h_sonde * n_boreholes) if h_sonde > 0 else 0
        q_per_per_m = abs(q_per) / (h_sonde * n_boreholes) if h_sonde > 0 else 0
        q_peak_per_m = abs(q_peak) / (h_sonde * n_boreholes) if h_sonde > 0 else 0
        
        # Temperaturänderungen berechnen
        delta_t_grundlast = q_grundlast_per_m * (r_grundlast + r_borehole)
        delta_t_per = q_per_per_m * (r_per + r_borehole)
        delta_t_peak = q_peak_per_m * (r_peak + r_borehole)
        
        # Vorzeichen anpassen
        if is_heating:
            # Bei Heizen: Erdreich kühlt ab → negative ΔT
            sign = -1
        else:
            # Bei Kühlen: Erdreich erwärmt sich → positive ΔT
            sign = +1
        
        # Wärmepumpenaustrittstemperatur
        t_wp_aus = (
            t_undisturbed +
            sign * delta_t_grundlast +
            sign * delta_t_per +
            sign * delta_t_peak -
            0.5 * delta_t_fluid
        )
        
        return t_wp_aus, (delta_t_grundlast, delta_t_per, delta_t_peak)
    
    def _calculate_thermal_resistances(
        self,
        lambda_ground: float,
        alpha_ground: float,
        h_sonde: float,
        r_borehole: float
    ) -> Dict[str, float]:
        """Berechnet thermische Widerstände für drei Zeitskalen."""
        from calculations.g_functions import GFunctionCalculator
        
        g_calc = GFunctionCalculator()
        
        # Zeitskalen
        t_grundlast = 10 * 365.25 * 24 * 3600  # 10 Jahre in Sekunden
        t_per = 30 * 24 * 3600                  # 1 Monat
        t_peak = 6 * 3600                       # 6 Stunden
        
        # g-Funktionen berechnen
        g_grundlast = g_calc.calculate_finite_line_source(
            t_grundlast, h_sonde, r_borehole, alpha_ground
        )
        g_per = g_calc.calculate_finite_line_source(
            t_per, h_sonde, r_borehole, alpha_ground
        )
        g_peak = g_calc.calculate_finite_line_source(
            t_peak, h_sonde, r_borehole, alpha_ground
        )
        
        # Thermische Widerstände: R = g / (2π·λ)
        r_grundlast = g_grundlast / (2 * math.pi * lambda_ground)
        r_per = g_per / (2 * math.pi * lambda_ground)
        r_peak = g_peak / (2 * math.pi * lambda_ground)
        
        return {
            'r_grundlast': r_grundlast,
            'r_per': r_per,
            'r_peak': r_peak,
            'g_grundlast': g_grundlast,
            'g_per': g_per,
            'g_peak': g_peak
        }
    
    def _calculate_loads(
        self,
        annual_demand: float,
        peak_load: float,
        monthly_factors: list,
        cop: float,
        is_heating: bool
    ) -> Dict[str, float]:
        """Berechnet die drei Lasttypen."""
        
        if is_heating:
            # Heizen: Wärmepumpe entzieht Wärme
            efficiency_factor = (cop - 1) / cop
        else:
            # Kühlen: Wärmepumpe gibt Wärme ab (inkl. elektrische Leistung)
            efficiency_factor = (cop + 1) / cop
        
        # Nettogrundlast (Jahresmittel)
        annual_extraction_kwh = annual_demand * efficiency_factor
        q_nettogrundlast = (annual_extraction_kwh * 1000) / 8760  # W
        
        # Periodische Last (kritischster Monat)
        max_monthly_factor = max(monthly_factors) if monthly_factors else 0.155
        monthly_energy_kwh = annual_demand * max_monthly_factor
        monthly_extraction_kwh = monthly_energy_kwh * efficiency_factor
        q_per = (monthly_extraction_kwh * 1000) / 730  # W (730h/Monat)
        
        # Spitzenlast
        q_peak = peak_load * 1000 * efficiency_factor  # W
        
        # Debug-Ausgabe
        if self.debug:
            mode = "HEIZEN" if is_heating else "KÜHLEN"
            self._debug(f"=== LASTEN BERECHNUNG ({mode}) ===", {
                "Jahresenergie (Eingabe)": annual_demand,
                "Spitzenlast (Eingabe)": peak_load,
                "COP": cop,
                "Effizienzfaktor": efficiency_factor,
                "Jahresenergie (Erdreich)": annual_extraction_kwh,
                "Max. Monatsfaktor": max_monthly_factor,
                "Monatsenergie (Eingabe)": monthly_energy_kwh,
                "Monatsenergie (Erdreich)": monthly_extraction_kwh,
                "Q_Nettogrundlast": q_nettogrundlast,
                "Q_Periodisch": q_per,
                "Q_Peak": q_peak
            })
        
        return {
            'q_nettogrundlast': q_nettogrundlast,
            'q_per': q_per,
            'q_peak': q_peak
        }


if __name__ == "__main__":
    # Test
    calc = VDI4640Calculator()
    
    result = calc.calculate_complete(
        ground_thermal_conductivity=2.0,
        ground_thermal_diffusivity=1.0e-6,
        t_undisturbed=10.0,
        borehole_diameter=152,
        borehole_depth_initial=100.0,
        n_boreholes=1,
        r_borehole=0.1,
        annual_heating_demand=10000,
        peak_heating_load=6.0,
        annual_cooling_demand=3000,
        peak_cooling_load=4.0,
        heat_pump_cop_heating=4.0,
        heat_pump_cop_cooling=4.0,
        t_fluid_min_required=-2.0,
        t_fluid_max_required=35.0
    )
    
    print("=" * 70)
    print("VDI 4640 TEST-BERECHNUNG")
    print("=" * 70)
    print(f"\nAuslegungsfall: {result.design_case.upper()}")
    print(f"Erforderliche Sondenlänge: {result.required_depth_final:.1f} m")
    print(f"  - Heizen: {result.required_depth_heating:.1f} m")
    print(f"  - Kühlen: {result.required_depth_cooling:.1f} m")
    print(f"\nWärmepumpenaustrittstemperaturen:")
    print(f"  - Heizen (min): {result.t_wp_aus_heating_min:.2f} °C")
    print(f"  - Kühlen (max): {result.t_wp_aus_cooling_max:.2f} °C")

