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


# ============================================================
# GUI Entry-Key → Validator-Key Mapping
# ============================================================

GUI_KEY_TO_VALIDATOR: Dict[str, str] = {
    # Bohrloch-Geometrie
    "borehole_diameter": "borehole_diameter",
    "initial_depth": "borehole_depth",
    "num_boreholes": "num_boreholes",
    "spacing_between": "borehole_spacing",
    # Rohre
    "pipe_outer_diameter": "pipe_outer_diameter",
    "pipe_thickness": "pipe_thickness",
    "shank_spacing": "shank_spacing",
    "pipe_thermal_cond": "pipe_thermal_conductivity",
    # Boden
    "ground_thermal_cond": "ground_thermal_conductivity",
    "ground_heat_cap": "ground_heat_capacity",
    "ground_temp": "undisturbed_ground_temp",
    "geothermal_gradient": "geothermal_gradient",
    # Verfüllung
    "grout_thermal_cond": "grout_thermal_conductivity",
    # Wärmepumpe & Lasten
    "heat_pump_cop": "heat_pump_cop",
    "heat_pump_power": "heat_pump_power",
    "annual_heating": "annual_heating_demand",
    "annual_cooling": "annual_cooling_demand",
    "peak_heating": "peak_heating_load",
    "peak_cooling": "peak_cooling_load",
    # Betriebsbedingungen
    "min_fluid_temp": "min_fluid_temperature",
    "max_fluid_temp": "max_fluid_temperature",
    "simulation_years": "simulation_years",
    # Hydraulik
    "delta_t_fluid": "delta_t_fluid",
    "fluid_flow_rate": "fluid_flow_rate",
    "num_circuits": "num_circuits",
}


def validate_gui_entry(gui_key: str, value: float) -> Tuple[bool, str]:
    """Validiert einen GUI-Entry-Wert über das Key-Mapping.

    Args:
        gui_key: GUI Entry-Schlüssel (z.B. 'ground_thermal_cond')
        value: Zu prüfender Wert

    Returns:
        Tuple (is_valid, error_message)
    """
    validator_key = GUI_KEY_TO_VALIDATOR.get(gui_key)
    if validator_key is None:
        return True, ""  # Kein Mapping → nicht prüfbar
    return validate_parameter(validator_key, value)


# ============================================================
# VDI 4640 Normen-Compliance-Check
# ============================================================

# Max. spezifische Entzugsleistung nach VDI 4640 [W/m]
# (für 1800 Heizstunden/Jahr, Einzelsonde)
VDI4640_MAX_EXTRACTION_RATES: Dict[str, float] = {
    "Sand (trocken)": 20.0,
    "Sand (feucht)": 65.0,
    "Sand": 40.0,
    "Lehm": 35.0,
    "Schluff": 35.0,
    "Ton": 35.0,
    "Kies": 40.0,
    "Granit": 65.0,
    "Gneis": 70.0,
    "Basalt": 40.0,
    "Sandstein": 55.0,
    "Kalkstein": 55.0,
}


@dataclass
class ComplianceResult:
    """Ergebnis eines Compliance-Checks."""
    level: str       # "info", "warning", "error"
    message: str     # Beschreibung
    norm_ref: str    # Normen-Referenz (z.B. "VDI 4640-2")


def check_vdi4640_compliance(
    params: Dict[str, float],
    soil_type: str = "",
    extraction_rate_wm: Optional[float] = None,
) -> List[ComplianceResult]:
    """Prüft VDI 4640 Normen-Compliance.

    Args:
        params: Parameter-Dictionary (GUI-Keys oder Validator-Keys)
        soil_type: Bodentyp-Name (z.B. "Sand", "Granit")
        extraction_rate_wm: Berechnete spez. Entzugsleistung [W/m]

    Returns:
        Liste von ComplianceResult (leer wenn alles konform)
    """
    results: List[ComplianceResult] = []

    # --- 1. Mindestabstand zwischen Bohrungen ---
    spacing = params.get("spacing_between",
                         params.get("borehole_spacing", None))
    num_bh = params.get("num_boreholes",
                        params.get("num_boreholes", 1))

    if spacing is not None and num_bh is not None and num_bh > 1:
        if spacing < 3.0:
            results.append(ComplianceResult(
                level="error",
                message=(f"Bohrabstand {spacing:.1f} m ist zu gering! "
                         f"Minimaler Abstand: 3 m (kritisch)."),
                norm_ref="VDI 4640-2, Abschn. 5.2"
            ))
        elif spacing < 6.0:
            results.append(ComplianceResult(
                level="warning",
                message=(f"Bohrabstand {spacing:.1f} m unterschreitet die "
                         f"Empfehlung von ≥ 6 m. Thermische Beeinflussung "
                         f"der Bohrungen möglich."),
                norm_ref="VDI 4640-2, Abschn. 5.2"
            ))

    # --- 2. Max. spezifische Entzugsleistung ---
    if extraction_rate_wm is not None and soil_type:
        max_rate = VDI4640_MAX_EXTRACTION_RATES.get(soil_type)
        if max_rate and extraction_rate_wm > max_rate:
            results.append(ComplianceResult(
                level="warning",
                message=(f"Spez. Entzugsleistung {extraction_rate_wm:.1f} W/m "
                         f"überschreitet VDI 4640 Maximum für {soil_type} "
                         f"({max_rate:.0f} W/m)."),
                norm_ref="VDI 4640-2, Tabelle 1"
            ))

    # --- 3. Frostschutzprüfung ---
    t_min = params.get("min_fluid_temp",
                       params.get("min_fluid_temperature", None))
    if t_min is not None and t_min <= -2.0:
        results.append(ComplianceResult(
            level="warning",
            message=(f"Min. Fluidtemperatur {t_min:.1f}°C liegt bei oder "
                     f"unter -2°C. Frostgefahr im Bohrlochbereich! "
                     f"Frostschutz und Verfüllmaterial prüfen."),
            norm_ref="VDI 4640-2, Abschn. 6.3"
        ))

    return results


def format_compliance_results(results: List[ComplianceResult]) -> str:
    """Formatiert Compliance-Ergebnisse als lesbaren Text.

    Args:
        results: Liste von ComplianceResult

    Returns:
        Formatierter Warnungstext
    """
    if not results:
        return "✅ VDI 4640 Compliance: Alle Prüfungen bestanden"

    icons = {"info": "ℹ️", "warning": "⚠️", "error": "❌"}
    lines = ["VDI 4640 Compliance-Prüfung:", ""]

    for r in results:
        icon = icons.get(r.level, "❓")
        lines.append(f"  {icon} {r.message}")
        lines.append(f"     Referenz: {r.norm_ref}")
        lines.append("")

    return "\n".join(lines)
