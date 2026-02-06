"""Zentrale Input-Validierung für Geothermie-Berechnungen.

Definiert erlaubte Wertebereiche für alle physikalischen Parameter
und bietet Validierungsfunktionen für GUI-Eingaben.
"""

import logging
from dataclasses import dataclass
from typing import Optional, Dict, List, Tuple

logger = logging.getLogger(__name__)


@dataclass
class ParameterRange:
    """Definiert den erlaubten Wertebereich eines Parameters."""
    name: str           # Anzeigename (deutsch)
    unit: str           # Einheit
    min_value: float    # Minimalwert (inklusive)
    max_value: float    # Maximalwert (inklusive)
    default: float      # Standardwert
    description: str = ""  # Optionale Beschreibung


class ValidationError(Exception):
    """Fehler bei der Parametervalidierung."""
    
    def __init__(self, message: str, parameter: str = "", value=None):
        self.parameter = parameter
        self.value = value
        super().__init__(message)


# ============================================================
# Erlaubte Wertebereiche für alle physikalischen Parameter
# ============================================================

PARAMETER_RANGES: Dict[str, ParameterRange] = {
    # Bohrloch-Geometrie
    "borehole_depth": ParameterRange(
        "Bohrtiefe", "m", 10, 400, 100,
        "Typisch 50-250m, max. 400m für tiefe Geothermie"
    ),
    "borehole_diameter": ParameterRange(
        "Bohrdurchmesser", "mm", 100, 300, 152,
        "Standard 152mm (6 Zoll)"
    ),
    "num_boreholes": ParameterRange(
        "Anzahl Bohrungen", "Stk", 1, 50, 1
    ),
    "borehole_spacing": ParameterRange(
        "Bohrabstand", "m", 3, 30, 6,
        "VDI 4640 empfiehlt min. 6m"
    ),
    
    # Rohre
    "pipe_outer_diameter": ParameterRange(
        "Rohr-Außendurchmesser", "mm", 20, 63, 32
    ),
    "pipe_thickness": ParameterRange(
        "Wandstärke", "mm", 1.5, 6.0, 2.9
    ),
    "shank_spacing": ParameterRange(
        "Schenkelabstand", "mm", 20, 120, 52
    ),
    "pipe_thermal_conductivity": ParameterRange(
        "Wärmeleitfähigkeit Rohr", "W/m·K", 0.1, 2.0, 0.42,
        "PE-HD: 0.42, PE-Xa: 0.38, PP: 0.22"
    ),
    
    # Boden
    "ground_thermal_conductivity": ParameterRange(
        "Wärmeleitfähigkeit Boden", "W/m·K", 0.5, 6.0, 2.0,
        "Sand 1.5-2.5, Granit 2.5-4.0"
    ),
    "ground_heat_capacity": ParameterRange(
        "Volumetrische Wärmekapazität", "MJ/m³·K", 1.0, 4.5, 2.4
    ),
    "undisturbed_ground_temp": ParameterRange(
        "Ungestörte Bodentemperatur", "°C", 4, 25, 10,
        "In Deutschland typisch 8-12°C"
    ),
    "geothermal_gradient": ParameterRange(
        "Geothermischer Gradient", "K/m", 0.01, 0.06, 0.03,
        "Typisch 0.03 K/m (3°C pro 100m)"
    ),
    
    # Verfüllung
    "grout_thermal_conductivity": ParameterRange(
        "Wärmeleitfähigkeit Verfüllung", "W/m·K", 0.4, 3.0, 1.3,
        "Standard-Bentonit ~0.8, Thermozement ~2.0"
    ),
    
    # Wärmepumpe
    "heat_pump_cop": ParameterRange(
        "COP / Leistungszahl", "-", 2.0, 8.0, 4.0,
        "Sole-WP Heizen typisch 3.5-5.0"
    ),
    "heat_pump_power": ParameterRange(
        "Wärmepumpenleistung", "kW", 1.0, 500.0, 8.0
    ),
    
    # Lasten
    "annual_heating_demand": ParameterRange(
        "Jahresheizwärmebedarf", "MWh/a", 0, 2000, 12.0
    ),
    "annual_cooling_demand": ParameterRange(
        "Jahreskältebedarf", "MWh/a", 0, 2000, 0.0
    ),
    "peak_heating_load": ParameterRange(
        "Heizlast (Peak)", "kW", 0, 500, 6.0
    ),
    "peak_cooling_load": ParameterRange(
        "Kühllast (Peak)", "kW", 0, 500, 0.0
    ),
    
    # Betriebsbedingungen
    "min_fluid_temperature": ParameterRange(
        "Min. Fluidtemperatur", "°C", -10, 10, -2.0,
        "Frostgrenze beachten!"
    ),
    "max_fluid_temperature": ParameterRange(
        "Max. Fluidtemperatur", "°C", 10, 40, 30.0
    ),
    "simulation_years": ParameterRange(
        "Simulationszeitraum", "Jahre", 1, 100, 25
    ),
    
    # Hydraulik
    "delta_t_fluid": ParameterRange(
        "Temperaturspreizung", "K", 1.0, 10.0, 3.0,
        "Typisch 3-5K"
    ),
    "antifreeze_concentration": ParameterRange(
        "Frostschutzkonzentration", "Vol%", 0, 40, 25
    ),
    "num_circuits": ParameterRange(
        "Anzahl Kreise", "Stk", 1, 50, 1
    ),
    
    # Fluid
    "fluid_flow_rate": ParameterRange(
        "Volumenstrom", "m³/h", 0.01, 50.0, 1.0
    ),
}


def validate_parameter(key: str, value: float) -> Tuple[bool, str]:
    """
    Validiert einen einzelnen Parameter gegen seinen erlaubten Bereich.
    
    Args:
        key: Parameter-Schlüssel (z.B. 'borehole_depth')
        value: Zu prüfender Wert
        
    Returns:
        Tuple (is_valid, error_message)
    """
    if key not in PARAMETER_RANGES:
        return True, ""  # Unbekannte Parameter werden nicht geprüft
    
    param = PARAMETER_RANGES[key]
    
    if value < param.min_value:
        return False, (
            f"{param.name} = {value} {param.unit} ist zu klein "
            f"(erlaubt: {param.min_value}–{param.max_value} {param.unit})"
        )
    
    if value > param.max_value:
        return False, (
            f"{param.name} = {value} {param.unit} ist zu groß "
            f"(erlaubt: {param.min_value}–{param.max_value} {param.unit})"
        )
    
    return True, ""


def validate_parameters(params: Dict[str, float]) -> List[str]:
    """
    Validiert mehrere Parameter auf einmal.
    
    Args:
        params: Dictionary mit Schlüssel-Wert-Paaren
        
    Returns:
        Liste von Fehlermeldungen (leer wenn alles OK)
    """
    errors = []
    
    for key, value in params.items():
        is_valid, message = validate_parameter(key, value)
        if not is_valid:
            errors.append(message)
    
    # Plausibilitäts-Checks
    if "pipe_outer_diameter" in params and "pipe_thickness" in params:
        outer = params["pipe_outer_diameter"]
        thickness = params["pipe_thickness"]
        inner = outer - 2 * thickness
        if inner <= 0:
            errors.append(
                f"Rohr-Innendurchmesser wäre negativ: "
                f"{outer} - 2×{thickness} = {inner} mm"
            )
    
    if "min_fluid_temperature" in params and "max_fluid_temperature" in params:
        t_min = params["min_fluid_temperature"]
        t_max = params["max_fluid_temperature"]
        if t_min >= t_max:
            errors.append(
                f"Min. Fluidtemperatur ({t_min}°C) muss kleiner als "
                f"Max. Fluidtemperatur ({t_max}°C) sein"
            )
    
    if "undisturbed_ground_temp" in params and "min_fluid_temperature" in params:
        t_ground = params["undisturbed_ground_temp"]
        t_min = params["min_fluid_temperature"]
        if t_min >= t_ground:
            errors.append(
                f"Min. Fluidtemperatur ({t_min}°C) sollte unter der "
                f"Bodentemperatur ({t_ground}°C) liegen"
            )
    
    return errors


def safe_float(value_str: str, default: float = 0.0) -> float:
    """
    Konvertiert einen String sicher in float.
    
    Args:
        value_str: Eingabe-String
        default: Rückgabewert bei Fehler
        
    Returns:
        float-Wert oder default
    """
    try:
        return float(value_str.strip().replace(",", "."))
    except (ValueError, AttributeError):
        return default
