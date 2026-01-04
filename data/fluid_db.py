"""Fluid-Datenbank für Wärmeträgerflüssigkeiten."""

import os
import json
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class FluidProperties:
    """Eigenschaften einer Wärmeträgerflüssigkeit."""
    name: str
    type: str  # "water", "glycol_mix"
    concentration_percent: float  # Glykol-Konzentration in %
    
    # Basis-Eigenschaften bei 20°C
    density_20: float  # kg/m³
    viscosity_20: float  # Pa·s
    heat_capacity_20: float  # J/kg·K
    thermal_conductivity_20: float  # W/m·K
    
    # Temperaturbereich
    min_temp: float  # °C - Frostschutzgrenze
    max_temp: float  # °C - Max. Betriebstemperatur
    
    # Druckverlust-Eigenschaften
    friction_factor_base: float  # Basis-Reibungsfaktor
    
    def get_properties_at_temp(self, temperature: float) -> Dict[str, float]:
        """
        Gibt die Eigenschaften bei gegebener Temperatur zurück.
        
        Args:
            temperature: Temperatur in °C
        
        Returns:
            Dict mit Eigenschaften
        """
        # Vereinfachte Temperaturabhängigkeit
        # Dichte: linear abnehmend mit Temperatur
        temp_factor = 1.0 - 0.0002 * (temperature - 20.0)
        density = self.density_20 * temp_factor
        
        # Viskosität: exponentiell abnehmend (Arrhenius-ähnlich)
        if temperature > 0:
            visc_factor = 1.0 / (1.0 + 0.03 * (temperature - 20.0))
        else:
            visc_factor = 1.0 + 0.1 * abs(temperature - 20.0)
        viscosity = self.viscosity_20 * visc_factor
        
        # Wärmekapazität: leicht zunehmend
        heat_cap_factor = 1.0 + 0.0001 * (temperature - 20.0)
        heat_capacity = self.heat_capacity_20 * heat_cap_factor
        
        # Wärmeleitfähigkeit: leicht zunehmend
        thermal_cond_factor = 1.0 + 0.0005 * (temperature - 20.0)
        thermal_conductivity = self.thermal_conductivity_20 * thermal_cond_factor
        
        return {
            "density": density,
            "viscosity": viscosity,
            "heat_capacity": heat_capacity,
            "thermal_conductivity": thermal_conductivity,
            "temperature": temperature
        }


class FluidDatabase:
    """Datenbank für Wärmeträgerflüssigkeiten."""
    
    def __init__(self, data_dir: Optional[str] = None):
        """
        Initialisiert die Fluid-Datenbank.
        
        Args:
            data_dir: Verzeichnis mit Fluid-Daten (Text/XML)
        """
        if data_dir is None:
            # Standard-Verzeichnis
            data_dir = os.path.join(os.path.dirname(__file__), "fluids")
        
        self.data_dir = data_dir
        self.fluids: Dict[str, FluidProperties] = {}
        
        # Erstelle Standard-Verzeichnis falls nicht vorhanden
        os.makedirs(data_dir, exist_ok=True)
        
        # Lade Standard-Fluide
        self._load_default_fluids()
        
        # Lade externe Dateien
        self._load_from_files()
    
    def _load_default_fluids(self):
        """Lädt Standard-Fluide in die Datenbank."""
        default_fluids = [
            FluidProperties(
                name="Reines Wasser",
                type="water",
                concentration_percent=0.0,
                density_20=998.2,
                viscosity_20=0.001002,
                heat_capacity_20=4182.0,
                thermal_conductivity_20=0.598,
                min_temp=0.0,
                max_temp=95.0,
                friction_factor_base=0.025
            ),
            FluidProperties(
                name="Ethylenglykol 20%",
                type="glycol_mix",
                concentration_percent=20.0,
                density_20=1028.0,
                viscosity_20=0.0025,
                heat_capacity_20=3900.0,
                thermal_conductivity_20=0.52,
                min_temp=-8.0,
                max_temp=95.0,
                friction_factor_base=0.028
            ),
            FluidProperties(
                name="Ethylenglykol 25%",
                type="glycol_mix",
                concentration_percent=25.0,
                density_20=1035.0,
                viscosity_20=0.0030,
                heat_capacity_20=3850.0,
                thermal_conductivity_20=0.48,
                min_temp=-12.0,
                max_temp=95.0,
                friction_factor_base=0.030
            ),
            FluidProperties(
                name="Ethylenglykol 30%",
                type="glycol_mix",
                concentration_percent=30.0,
                density_20=1042.0,
                viscosity_20=0.0038,
                heat_capacity_20=3800.0,
                thermal_conductivity_20=0.45,
                min_temp=-18.0,
                max_temp=95.0,
                friction_factor_base=0.032
            ),
            FluidProperties(
                name="Propylenglykol 20%",
                type="glycol_mix",
                concentration_percent=20.0,
                density_20=1020.0,
                viscosity_20=0.0030,
                heat_capacity_20=3920.0,
                thermal_conductivity_20=0.50,
                min_temp=-8.0,
                max_temp=95.0,
                friction_factor_base=0.029
            ),
            FluidProperties(
                name="Propylenglykol 30%",
                type="glycol_mix",
                concentration_percent=30.0,
                density_20=1035.0,
                viscosity_20=0.0045,
                heat_capacity_20=3850.0,
                thermal_conductivity_20=0.46,
                min_temp=-18.0,
                max_temp=95.0,
                friction_factor_base=0.033
            ),
        ]
        
        for fluid in default_fluids:
            self.fluids[fluid.name] = fluid
    
    def _load_from_files(self):
        """Lädt Fluide aus Text- und XML-Dateien."""
        if not os.path.exists(self.data_dir):
            return
        
        # Lade JSON/Text-Dateien
        for filename in os.listdir(self.data_dir):
            if filename.endswith('.json') or filename.endswith('.txt'):
                try:
                    filepath = os.path.join(self.data_dir, filename)
                    with open(filepath, 'r', encoding='utf-8') as f:
                        if filename.endswith('.json'):
                            data = json.load(f)
                            self._load_from_json(data)
                        else:
                            # Text-Format (einfaches Format)
                            self._load_from_text(f)
                except Exception as e:
                    print(f"⚠️ Fehler beim Laden von {filename}: {e}")
            
            # Lade XML-Dateien
            elif filename.endswith('.xml'):
                try:
                    filepath = os.path.join(self.data_dir, filename)
                    self._load_from_xml(filepath)
                except Exception as e:
                    print(f"⚠️ Fehler beim Laden von {filename}: {e}")
    
    def _load_from_json(self, data: Dict):
        """Lädt Fluide aus JSON-Daten."""
        if isinstance(data, list):
            for item in data:
                self._create_fluid_from_dict(item)
        elif isinstance(data, dict):
            if "fluids" in data:
                for item in data["fluids"]:
                    self._create_fluid_from_dict(item)
            else:
                self._create_fluid_from_dict(data)
    
    def _load_from_text(self, file_handle):
        """Lädt Fluide aus Text-Datei (einfaches Format)."""
        current_fluid = {}
        for line in file_handle:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            if line.startswith('[') and line.endswith(']'):
                # Neues Fluid
                if current_fluid:
                    self._create_fluid_from_dict(current_fluid)
                current_fluid = {"name": line[1:-1]}
            else:
                # Eigenschaft
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    try:
                        # Versuche als Float zu parsen
                        current_fluid[key] = float(value)
                    except ValueError:
                        current_fluid[key] = value
        
        # Letztes Fluid
        if current_fluid:
            self._create_fluid_from_dict(current_fluid)
    
    def _load_from_xml(self, filepath: str):
        """Lädt Fluide aus XML-Datei."""
        tree = ET.parse(filepath)
        root = tree.getroot()
        
        for fluid_elem in root.findall('fluid'):
            fluid_dict = {}
            for child in fluid_elem:
                tag = child.tag
                text = child.text
                if text:
                    try:
                        fluid_dict[tag] = float(text)
                    except ValueError:
                        fluid_dict[tag] = text
            
            self._create_fluid_from_dict(fluid_dict)
    
    def _create_fluid_from_dict(self, data: Dict):
        """Erstellt ein FluidProperties-Objekt aus Dict."""
        try:
            fluid = FluidProperties(
                name=data.get("name", "Unbekannt"),
                type=data.get("type", "water"),
                concentration_percent=float(data.get("concentration_percent", 0.0)),
                density_20=float(data.get("density_20", 1000.0)),
                viscosity_20=float(data.get("viscosity_20", 0.001)),
                heat_capacity_20=float(data.get("heat_capacity_20", 4182.0)),
                thermal_conductivity_20=float(data.get("thermal_conductivity_20", 0.6)),
                min_temp=float(data.get("min_temp", 0.0)),
                max_temp=float(data.get("max_temp", 95.0)),
                friction_factor_base=float(data.get("friction_factor_base", 0.025))
            )
            self.fluids[fluid.name] = fluid
        except Exception as e:
            print(f"⚠️ Fehler beim Erstellen von Fluid: {e}")
    
    def get_all_names(self) -> List[str]:
        """Gibt alle Fluid-Namen zurück."""
        return sorted(self.fluids.keys())
    
    def get_fluid(self, name: str) -> Optional[FluidProperties]:
        """Gibt ein Fluid nach Namen zurück."""
        return self.fluids.get(name)
    
    def get_properties(self, name: str, temperature: float = 20.0) -> Optional[Dict[str, float]]:
        """
        Gibt die Eigenschaften eines Fluids bei gegebener Temperatur zurück.
        
        Args:
            name: Fluid-Name
            temperature: Temperatur in °C
        
        Returns:
            Dict mit Eigenschaften oder None
        """
        fluid = self.get_fluid(name)
        if fluid:
            return fluid.get_properties_at_temp(temperature)
        return None
    
    def compare_fluids(self, names: List[str], temperature: float = 20.0) -> List[Dict]:
        """
        Vergleicht mehrere Fluide bei gegebener Temperatur.
        
        Args:
            names: Liste von Fluid-Namen
            temperature: Temperatur in °C
        
        Returns:
            Liste von Vergleichs-Dicts
        """
        comparison = []
        for name in names:
            fluid = self.get_fluid(name)
            if fluid:
                props = fluid.get_properties_at_temp(temperature)
                comparison.append({
                    "name": name,
                    "type": fluid.type,
                    "concentration": fluid.concentration_percent,
                    "min_temp": fluid.min_temp,
                    "max_temp": fluid.max_temp,
                    **props
                })
        return comparison

