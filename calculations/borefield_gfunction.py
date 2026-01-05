"""Bohrfeld g-Funktionen Berechnung mit pygfunction.

Dieses Modul ermöglicht die Berechnung thermischer g-Funktionen für
Bohrfelder mit mehreren Erdwärmesonden unter Verwendung von pygfunction.
"""

import numpy as np
from typing import Dict, Optional, List, Tuple
import warnings

# Versuche pygfunction zu importieren
try:
    import pygfunction as gt
    PYGFUNCTION_AVAILABLE = True
except ImportError:
    PYGFUNCTION_AVAILABLE = False
    warnings.warn(
        "pygfunction nicht installiert. Bohrfeld-Berechnungen nicht verfügbar. "
        "Installieren mit: pip install pygfunction[plot]"
    )


class BorefieldCalculator:
    """Berechnet g-Funktionen für Bohrfelder mit pygfunction."""
    
    def __init__(self):
        """Initialisiert den Bohrfeld-Rechner."""
        if not PYGFUNCTION_AVAILABLE:
            raise ImportError(
                "pygfunction muss installiert sein!\n"
                "Installation: pip install pygfunction[plot]>=2.3.0"
            )
    
    def calculate_gfunction(
        self,
        layout: str,
        num_boreholes_x: int,
        num_boreholes_y: int,
        spacing_x: float,
        spacing_y: float,
        borehole_depth: float,
        borehole_radius: float,
        soil_thermal_diffusivity: float,
        simulation_years: int = 25,
        time_resolution: str = "monthly"
    ) -> Dict:
        """
        Berechnet g-Funktion für ein Bohrfeld.
        
        Args:
            layout: Layout-Typ ("rectangle", "L", "U", "line")
            num_boreholes_x: Anzahl Bohrungen in X-Richtung
            num_boreholes_y: Anzahl Bohrungen in Y-Richtung
            spacing_x: Abstand in X-Richtung (m)
            spacing_y: Abstand in Y-Richtung (m)
            borehole_depth: Tiefe pro Bohrung (m)
            borehole_radius: Bohrungsradius (m)
            soil_thermal_diffusivity: Thermische Diffusivität Boden (m²/s)
            simulation_years: Simulationsdauer (Jahre)
            time_resolution: Zeitauflösung ("hourly", "daily", "monthly")
        
        Returns:
            Dict mit g-Funktions-Daten und Bohrfeld-Informationen
        """
        print(f"🔄 Berechne g-Funktion für {layout}-Bohrfeld...")
        print(f"   Bohrungen: {num_boreholes_x}×{num_boreholes_y}")
        print(f"   Tiefe: {borehole_depth} m")
        print(f"   Simulation: {simulation_years} Jahre")
        
        # Erstelle Bohrfeld basierend auf Layout
        boreField = self._create_borefield(
            layout=layout,
            num_x=num_boreholes_x,
            num_y=num_boreholes_y,
            spacing_x=spacing_x,
            spacing_y=spacing_y,
            depth=borehole_depth,
            radius=borehole_radius
        )
        
        # Zeitpunkte generieren
        time = self._generate_time_points(simulation_years, time_resolution)
        
        # g-Funktion berechnen
        print("   Berechne thermische Response...")
        gFunc = gt.gfunction.gFunction(
            boreField,
            alpha=soil_thermal_diffusivity,
            time=time
        )
        
        # Statistiken berechnen
        num_boreholes = len(boreField)
        total_depth = num_boreholes * borehole_depth
        field_area = self._calculate_field_area(boreField)
        
        print(f"✅ g-Funktion berechnet!")
        print(f"   Anzahl Bohrungen: {num_boreholes}")
        print(f"   Gesamttiefe: {total_depth} m")
        print(f"   Feldgröße: {field_area:.1f} m²")
        
        return {
            "boreField": boreField,
            "gFunction": gFunc,
            "time": time,
            "num_boreholes": num_boreholes,
            "total_depth": total_depth,
            "total_length": total_depth,
            "field_area": field_area,
            "layout": layout,
            "spacing_x": spacing_x,
            "spacing_y": spacing_y,
            "borehole_depth": borehole_depth,
            "borehole_radius": borehole_radius,
            "simulation_years": simulation_years
        }
    
    def _create_borefield(
        self,
        layout: str,
        num_x: int,
        num_y: int,
        spacing_x: float,
        spacing_y: float,
        depth: float,
        radius: float
    ):
        """Erstellt Bohrfeld basierend auf Layout-Typ."""
        header_depth = 4.0  # Tiefe der Verteilerrohre (m)
        
        if layout == "rectangle":
            return gt.boreholes.rectangle_field(
                N_1=num_x,
                N_2=num_y,
                B_1=spacing_x,
                B_2=spacing_y,
                H=depth,
                D=header_depth,
                r_b=radius
            )
        
        elif layout == "L":
            return gt.boreholes.L_shaped_field(
                N_1=num_x,
                N_2=num_y,
                B_1=spacing_x,
                B_2=spacing_y,
                H=depth,
                D=header_depth,
                r_b=radius
            )
        
        elif layout == "U":
            return gt.boreholes.U_shaped_field(
                N_1=num_x,
                N_2=num_y,
                B_1=spacing_x,
                B_2=spacing_y,
                H=depth,
                D=header_depth,
                r_b=radius
            )
        
        elif layout == "line":
            # Einzelne Reihe
            return gt.boreholes.rectangle_field(
                N_1=num_x,
                N_2=1,
                B_1=spacing_x,
                B_2=1.0,
                H=depth,
                D=header_depth,
                r_b=radius
            )
        
        else:
            raise ValueError(
                f"Nicht unterstütztes Layout: {layout}. "
                f"Verfügbar: rectangle, L, U, line"
            )
    
    def _generate_time_points(
        self,
        years: int,
        resolution: str
    ) -> np.ndarray:
        """
        Generiert Zeitpunkte für Simulation.
        
        Args:
            years: Simulationsjahre
            resolution: "hourly", "daily", "monthly"
        
        Returns:
            Array mit Zeitpunkten in Sekunden
        """
        seconds_per_hour = 3600
        seconds_per_day = 24 * seconds_per_hour
        seconds_per_month = 30 * seconds_per_day
        seconds_per_year = 365.25 * seconds_per_day
        
        if resolution == "hourly":
            # Stündlich für erstes Jahr, dann monatlich für Rest
            t1 = np.array([i * seconds_per_hour for i in range(1, 8760)])  # Jahr 1
            t2 = np.array([
                seconds_per_year + i * seconds_per_month 
                for i in range(1, (years - 1) * 12)
            ])
            time = np.concatenate([t1, t2]) if years > 1 else t1
        
        elif resolution == "daily":
            # Täglich
            time = np.array([i * seconds_per_day for i in range(1, int(years * 365))])
        
        else:  # monthly (Standard)
            # Monatlich
            time = np.array([i * seconds_per_month for i in range(1, years * 12)])
        
        return time
    
    def _calculate_field_area(self, boreField) -> float:
        """
        Berechnet Fläche des Bohrfelds (m²).
        
        Args:
            boreField: pygfunction Bohrfeld-Objekt
        
        Returns:
            Fläche in m²
        """
        x_coords = [b.x for b in boreField]
        y_coords = [b.y for b in boreField]
        
        width = max(x_coords) - min(x_coords)
        height = max(y_coords) - min(y_coords)
        
        # Füge etwas Rand hinzu für realistischere Fläche
        margin = 3.0  # 3m Rand
        width += 2 * margin
        height += 2 * margin
        
        return width * height if (width > 0 and height > 0) else 0.0
    
    def calculate_required_boreholes(
        self,
        annual_load: float,
        peak_load: float,
        ground_thermal_conductivity: float,
        borehole_depth: float,
        borehole_resistance: float,
        fluid_temp_min: float,
        ground_temp: float,
        simulation_years: int = 25
    ) -> Dict:
        """
        Berechnet die erforderliche Anzahl Bohrungen für eine gegebene Last.
        
        Args:
            annual_load: Jahreswärmelast (kWh)
            peak_load: Spitzenlast (kW)
            ground_thermal_conductivity: Bodenwärmeleitfähigkeit (W/m·K)
            borehole_depth: Bohrungstiefe (m)
            borehole_resistance: Thermischer Bohrlochwiderstand (m·K/W)
            fluid_temp_min: Minimale Fluidtemperatur (°C)
            ground_temp: Ungestörte Bodentemperatur (°C)
            simulation_years: Simulationsjahre
        
        Returns:
            Dict mit Ergebnissen
        """
        print("🔄 Berechne erforderliche Bohrungen...")
        
        # Umrechnung kWh → Wh
        annual_load_wh = annual_load * 1000
        
        # Einfache Schätzung basierend auf spezifischer Entzugsleistung
        # Typisch: 30-60 W/m je nach Bodenleitfähigkeit
        specific_extraction = 25 + ground_thermal_conductivity * 15  # W/m
        
        # Erforderliche Gesamtlänge
        required_length = annual_load_wh / (specific_extraction * 8760)
        
        # Anzahl Bohrungen
        num_boreholes = int(np.ceil(required_length / borehole_depth))
        
        print(f"✅ Erforderlich: {num_boreholes} Bohrungen à {borehole_depth} m")
        
        return {
            "num_boreholes": num_boreholes,
            "total_length": num_boreholes * borehole_depth,
            "specific_extraction": specific_extraction,
            "required_length": required_length
        }
    
    def get_borehole_coordinates(self, boreField) -> List[Tuple[float, float]]:
        """
        Extrahiert X,Y Koordinaten aller Bohrungen.
        
        Args:
            boreField: pygfunction Bohrfeld-Objekt
        
        Returns:
            Liste von (x, y) Tupeln
        """
        return [(b.x, b.y) for b in boreField]
    
    def is_available(self) -> bool:
        """Prüft ob pygfunction verfügbar ist."""
        return PYGFUNCTION_AVAILABLE


def check_pygfunction_installation() -> Tuple[bool, str]:
    """
    Prüft ob pygfunction korrekt installiert ist.
    
    Returns:
        (is_installed, version_or_error_message)
    """
    if not PYGFUNCTION_AVAILABLE:
        return False, "Nicht installiert"
    
    try:
        import pygfunction as gt
        version = getattr(gt, '__version__', 'unbekannt')
        return True, version
    except Exception as e:
        return False, f"Fehler: {e}"








