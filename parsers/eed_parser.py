"""Parser für EED .dat Dateien."""

from dataclasses import dataclass
from typing import List, Dict, Any
import re


@dataclass
class EEDConfiguration:
    """Repräsentiert eine EED-Konfiguration."""
    version: str = ""
    si_units: bool = True
    
    # Bodeneigenschaften
    thermal_conductivity_ground: float = 0.0  # W/m·K
    heat_capacity: float = 0.0  # J/m³·K
    init_ground_surface_temp: float = 0.0  # °C
    geothermal_heat_flux: float = 0.0  # W/m²
    
    # Bohrloch-Konfiguration
    borehole_type: str = "single"
    borehole_depth: float = 0.0  # m
    borehole_spacing: float = 0.0  # m
    borehole_diameter: float = 0.0  # m
    
    # Rohr-Konfiguration
    pipe_configuration: str = ""  # z.B. "SINGLE-U"
    pipe_volume_flow: float = 0.0  # m³/s
    pipe_diameter: float = 0.0  # m
    pipe_thickness: float = 0.0  # m
    pipe_thermal_conductivity: float = 0.0  # W/m·K
    
    # U-Rohr spezifisch
    u_pipe_diameter: float = 0.0  # m
    u_pipe_thickness: float = 0.0  # m
    u_pipe_thermal_conductivity: float = 0.0  # W/m·K
    u_pipe_shank_space: float = 0.0  # m
    
    # Verfüllung
    thermal_conductivity_fill: float = 0.0  # W/m·K
    
    # Wärmeträgerflüssigkeit
    hc_thermal_conductivity: float = 0.0  # W/m·K
    hc_heat_capacity: float = 0.0  # J/kg·K
    hc_density: float = 0.0  # kg/m³
    hc_viscosity: float = 0.0  # Pa·s
    hc_freeze_temp: float = 0.0  # °C
    
    # Bohrloch-Widerstand
    calculate_borehole_resistance: bool = True
    multipoles: int = 10
    bore_rb: float = 0.0
    bore_ra: float = 0.0
    
    # Lasten
    annual_heat_load: float = 0.0  # MWh
    spf_heat: float = 0.0  # Seasonal Performance Factor
    annual_cool_load: float = 0.0  # MWh
    spf_cool: float = 0.0
    
    # Monatliche Wärmelasten
    monthly_heat_loads: List[float] = None
    monthly_heat_factors: List[float] = None
    monthly_heat_peak_loads: List[float] = None
    monthly_heat_durations: List[float] = None
    
    # Monatliche Kühlung
    monthly_cool_loads: List[float] = None
    monthly_cool_factors: List[float] = None
    monthly_cool_peak_loads: List[float] = None
    monthly_cool_durations: List[float] = None
    
    # Temperaturanforderungen
    tfluid_min_required: float = 0.0  # °C
    tfluid_max_required: float = 0.0  # °C
    
    # Warmwasser
    annual_dhw: float = 0.0  # MWh
    spf_dhw: float = 0.0
    
    # Optimierung
    spacing_min: float = 0.0  # m
    spacing_max: float = 0.0  # m
    depth_min: float = 0.0  # m
    depth_max: float = 0.0  # m
    
    def __post_init__(self):
        """Initialisiert Listen, falls sie None sind."""
        if self.monthly_heat_loads is None:
            self.monthly_heat_loads = [0.0] * 12
        if self.monthly_heat_factors is None:
            self.monthly_heat_factors = [0.0] * 12
        if self.monthly_heat_peak_loads is None:
            self.monthly_heat_peak_loads = [0.0] * 12
        if self.monthly_heat_durations is None:
            self.monthly_heat_durations = [0.0] * 12
        if self.monthly_cool_loads is None:
            self.monthly_cool_loads = [0.0] * 12
        if self.monthly_cool_factors is None:
            self.monthly_cool_factors = [0.0] * 12
        if self.monthly_cool_peak_loads is None:
            self.monthly_cool_peak_loads = [0.0] * 12
        if self.monthly_cool_durations is None:
            self.monthly_cool_durations = [0.0] * 12


class EEDParser:
    """Parser für EED .dat Dateien."""
    
    @staticmethod
    def parse_file(filepath: str) -> EEDConfiguration:
        """
        Liest eine EED .dat Datei ein und gibt eine EEDConfiguration zurück.
        """
        config = EEDConfiguration()
        
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        # Parse Zeile für Zeile
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Überspringe leere Zeilen
            if not line:
                i += 1
                continue
            
            # Version
            if 'Version=' in line:
                config.version = line.split('=')[1]
            
            # SI Units
            elif line == 'SI=yes':
                config.si_units = True
            elif line == 'SI=no':
                config.si_units = False
            
            # Numerische Werte mit Namen
            elif 'ThermCondGround' in line:
                config.thermal_conductivity_ground = EEDParser._extract_float(line)
            elif 'HeatCap' in line:
                config.heat_capacity = EEDParser._extract_float(line)
            elif 'InitGroundSurfTemp' in line:
                config.init_ground_surface_temp = EEDParser._extract_float(line)
            elif 'GeothermalHeatFlux' in line:
                config.geothermal_heat_flux = EEDParser._extract_float(line)
            
            # Bohrloch
            elif 'BHDepth' in line:
                config.borehole_depth = EEDParser._extract_float(line)
            elif line.strip() == '1 : single':
                config.borehole_type = 'single'
            elif 'BoreholeDiam' in line:
                config.borehole_diameter = EEDParser._extract_float(line)
            
            # Rohr-Konfiguration
            elif line == 'SINGLE-U' or line == 'DOUBLE-U' or line == 'COAXIAL':
                config.pipe_configuration = line
            elif 'BhVolFlow' in line:
                config.pipe_volume_flow = EEDParser._extract_float(line)
            elif 'PipeDiam' in line and 'UPipeDiam' not in line:
                config.pipe_diameter = EEDParser._extract_float(line)
            elif 'PipeThick' in line and 'UPipeThick' not in line:
                config.pipe_thickness = EEDParser._extract_float(line)
            elif 'PipeThCond' in line and 'UPipeThCond' not in line:
                config.pipe_thermal_conductivity = EEDParser._extract_float(line)
            
            # U-Rohr
            elif 'UPipeDiam' in line:
                config.u_pipe_diameter = EEDParser._extract_float(line)
            elif 'UPipeThick' in line:
                config.u_pipe_thickness = EEDParser._extract_float(line)
            elif 'UPipeThCond' in line:
                config.u_pipe_thermal_conductivity = EEDParser._extract_float(line)
            elif 'UPipeShankSpace' in line:
                config.u_pipe_shank_space = EEDParser._extract_float(line)
            
            # Verfüllung
            elif 'ThermCondFill' in line:
                config.thermal_conductivity_fill = EEDParser._extract_float(line)
            
            # Wärmeträger
            elif 'hc_thermcond' in line:
                config.hc_thermal_conductivity = EEDParser._extract_float(line)
            elif 'hc_heatcap' in line:
                config.hc_heat_capacity = EEDParser._extract_float(line)
            elif 'hc_dens' in line:
                config.hc_density = EEDParser._extract_float(line)
            elif 'hc_visc' in line:
                config.hc_viscosity = EEDParser._extract_float(line)
            elif 'hc_freeze' in line:
                config.hc_freeze_temp = EEDParser._extract_float(line)
            
            # Bohrloch-Widerstand
            elif 'multipoles' in line:
                val = EEDParser._extract_float(line)
                if val is not None:
                    config.multipoles = int(val)
            elif 'bore_rb' in line and 'bore_rb_const' not in line:
                config.bore_rb = EEDParser._extract_float(line)
            elif 'bore_ra' in line and 'bore_ra_const' not in line:
                config.bore_ra = EEDParser._extract_float(line)
            
            # Lasten
            elif 'annual_heat_load' in line:
                config.annual_heat_load = EEDParser._extract_float(line)
            elif 'SPF_Heat' in line:
                config.spf_heat = EEDParser._extract_float(line)
            elif 'annual_cool_load' in line:
                config.annual_cool_load = EEDParser._extract_float(line)
            elif 'SPF_Cool' in line:
                config.spf_cool = EEDParser._extract_float(line)
            
            # Monatliche Lasten (Heizen)
            elif 'monthly heat load' in line:
                month_match = re.search(r'monthly heat load\s+(\d+)', line)
                if month_match:
                    month = int(month_match.group(1)) - 1
                    value = EEDParser._extract_float(line)
                    if 0 <= month < 12:
                        config.monthly_heat_loads[month] = value
            
            elif 'monthly heat factor' in line:
                month_match = re.search(r'monthly heat factor\s+(\d+)', line)
                if month_match:
                    month = int(month_match.group(1)) - 1
                    value = EEDParser._extract_float(line)
                    if 0 <= month < 12:
                        config.monthly_heat_factors[month] = value
            
            elif 'monthly heat peak load' in line:
                month_match = re.search(r'monthly heat peak load\s+(\d+)', line)
                if month_match:
                    month = int(month_match.group(1)) - 1
                    value = EEDParser._extract_float(line)
                    if 0 <= month < 12:
                        config.monthly_heat_peak_loads[month] = value
            
            elif 'monthly heat duration' in line:
                month_match = re.search(r'monthly heat duration\s+(\d+)', line)
                if month_match:
                    month = int(month_match.group(1)) - 1
                    value = EEDParser._extract_float(line)
                    if 0 <= month < 12:
                        config.monthly_heat_durations[month] = value
            
            # Monatliche Lasten (Kühlung)
            elif 'monthly cool load' in line:
                month_match = re.search(r'monthly cool load\s+(\d+)', line)
                if month_match:
                    month = int(month_match.group(1)) - 1
                    value = EEDParser._extract_float(line)
                    if 0 <= month < 12:
                        config.monthly_cool_loads[month] = value
            
            elif 'monthly cool factor' in line:
                month_match = re.search(r'monthly cool factor\s+(\d+)', line)
                if month_match:
                    month = int(month_match.group(1)) - 1
                    value = EEDParser._extract_float(line)
                    if 0 <= month < 12:
                        config.monthly_cool_factors[month] = value
            
            # Temperaturanforderungen
            elif 'tfluid_min_required' in line:
                config.tfluid_min_required = EEDParser._extract_float(line)
            elif 'tfluid_max_required' in line:
                config.tfluid_max_required = EEDParser._extract_float(line)
            
            # Warmwasser
            elif 'annual DHW' in line:
                config.annual_dhw = EEDParser._extract_float(line)
            elif 'SPF DHW' in line:
                config.spf_dhw = EEDParser._extract_float(line)
            
            # Optimierungsparameter
            elif 'Spacing min' in line:
                config.spacing_min = EEDParser._extract_float(line)
            elif 'Spacing max' in line:
                config.spacing_max = EEDParser._extract_float(line)
            elif 'Depth min' in line:
                config.depth_min = EEDParser._extract_float(line)
            elif 'Depth max' in line:
                config.depth_max = EEDParser._extract_float(line)
            
            i += 1
        
        return config
    
    @staticmethod
    def _extract_float(line: str) -> float:
        """Extrahiert einen Float-Wert aus einer Zeile."""
        # Suche nach wissenschaftlicher Notation oder normalen Zahlen
        match = re.search(r'[-+]?[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?', line)
        if match:
            try:
                return float(match.group(0))
            except ValueError:
                return 0.0
        return 0.0


if __name__ == "__main__":
    # Test
    parser = EEDParser()
    config = parser.parse_file("../EED_4_example_files/EED_4_SFH-SE.dat")
    
    print(f"EED Version: {config.version}")
    print(f"Wärmeleitfähigkeit Boden: {config.thermal_conductivity_ground} W/m·K")
    print(f"Bohrtiefe: {config.borehole_depth} m")
    print(f"Rohrkonfiguration: {config.pipe_configuration}")
    print(f"Jährliche Wärmelast: {config.annual_heat_load} MWh")





