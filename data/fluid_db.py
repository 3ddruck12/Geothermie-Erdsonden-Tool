"""Fluid-Datenbank für Wärmeträgerflüssigkeiten."""

import os
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class FluidProperties:
    """Eigenschaften einer Wärmeträgerflüssigkeit."""
    name: str
    type: str  # "water", "glycol_mix", "special"
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
    
    # Zusatzinformationen
    glycol_type: Optional[str] = None  # "ethylene_glycol", "propylene_glycol"
    notes: List[str] = field(default_factory=list)  # Anwendungshinweise
    
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
    
    def __init__(self, xml_file: Optional[str] = None):
        """
        Initialisiert die Fluid-Datenbank.
        
        Args:
            xml_file: Pfad zur XML-Datei (Standard: fluids.xml)
        """
        if xml_file is None:
            # Standard: XML-Datei im gleichen Verzeichnis
            current_dir = os.path.dirname(__file__)
            xml_file = os.path.join(current_dir, 'fluids.xml')
        
        self.xml_file = xml_file
        self.fluids: Dict[str, FluidProperties] = {}
        self.categories: Dict[str, List[FluidProperties]] = {}
        
        # Lade Fluide aus XML
        self._load_from_xml()
    
    def _load_from_xml(self):
        """Lädt Fluide aus XML-Datei."""
        try:
            tree = ET.parse(self.xml_file)
            root = tree.getroot()
            
            for category in root.findall('fluid_category'):
                category_name = category.get('name')
                category_type = category.get('type')
                self.categories[category_name] = []
                
                for fluid_elem in category.findall('fluid'):
                    fluid = self._parse_fluid(fluid_elem, category_type)
                    self.fluids[fluid.name] = fluid
                    self.categories[category_name].append(fluid)
        
        except FileNotFoundError:
            print(f"⚠️ Fluid-Datenbank nicht gefunden: {self.xml_file}")
            print(f"⚠️ Verwende Fallback-Fluide")
            self._load_fallback_fluids()
        except Exception as e:
            print(f"⚠️ Fehler beim Laden der Fluid-Datenbank: {e}")
            self._load_fallback_fluids()
    
    def _parse_fluid(self, elem: ET.Element, category_type: str) -> FluidProperties:
        """Parst ein Fluid aus XML-Element."""
        # Basis-Infos
        name = elem.find('name').text
        fluid_type = elem.find('type').text
        concentration = float(elem.find('concentration_percent').text)
        
        # Stoffwerte bei 20°C
        props_elem = elem.find('properties_at_20c')
        density = float(props_elem.find('density').text)
        viscosity = float(props_elem.find('viscosity').text)
        heat_capacity = float(props_elem.find('heat_capacity').text)
        thermal_conductivity = float(props_elem.find('thermal_conductivity').text)
        
        # Temperaturbereich
        temp_elem = elem.find('temperature_range')
        min_temp = float(temp_elem.find('min_temp').text)
        max_temp = float(temp_elem.find('max_temp').text)
        
        # Hydraulik
        hydraulics_elem = elem.find('hydraulics')
        friction_factor = float(hydraulics_elem.find('friction_factor_base').text)
        
        # Optional: Glykol-Typ
        glycol_type_elem = elem.find('glycol_type')
        glycol_type = glycol_type_elem.text if glycol_type_elem is not None else None
        
        # Optional: Anwendungshinweise
        notes_elem = elem.find('notes')
        notes = []
        if notes_elem is not None:
            notes = [note.text for note in notes_elem.findall('note')]
        
        return FluidProperties(
            name=name,
            type=fluid_type,
            concentration_percent=concentration,
            density_20=density,
            viscosity_20=viscosity,
            heat_capacity_20=heat_capacity,
            thermal_conductivity_20=thermal_conductivity,
            min_temp=min_temp,
            max_temp=max_temp,
            friction_factor_base=friction_factor,
            glycol_type=glycol_type,
            notes=notes
        )
    
    def _load_fallback_fluids(self):
        """Lädt minimale Fallback-Fluide falls XML nicht geladen werden kann."""
        fallback_fluids = [
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
                friction_factor_base=0.025,
                notes=["Fallback: XML nicht geladen"]
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
                friction_factor_base=0.030,
                glycol_type="ethylene_glycol",
                notes=["Fallback: XML nicht geladen"]
            ),
        ]
        
        self.categories["Fallback"] = fallback_fluids
        for fluid in fallback_fluids:
            self.fluids[fluid.name] = fluid
    
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
    
    def get_fluids_by_category(self, category: str) -> List[FluidProperties]:
        """Gibt alle Fluide einer Kategorie zurück."""
        return self.categories.get(category, [])
    
    def get_all_categories(self) -> List[str]:
        """Gibt alle Kategorien zurück."""
        return list(self.categories.keys())
    
    def get_fluids_by_type(self, fluid_type: str) -> List[FluidProperties]:
        """Gibt alle Fluide eines bestimmten Typs zurück."""
        return [f for f in self.fluids.values() if f.type == fluid_type]
    
    def get_fluids_by_concentration(self, concentration: float, 
                                    tolerance: float = 0.1) -> List[FluidProperties]:
        """
        Gibt alle Fluide mit bestimmter Konzentration zurück.
        
        Args:
            concentration: Gewünschte Konzentration in %
            tolerance: Toleranz in % (Standard: 0.1%)
        """
        return [f for f in self.fluids.values() 
                if abs(f.concentration_percent - concentration) <= tolerance]
    
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
                    "glycol_type": fluid.glycol_type,
                    **props
                })
        return comparison


if __name__ == "__main__":
    # Test der Fluid-Datenbank
    db = FluidDatabase()
    
    print("="*70)
    print("FLUID-DATENBANK TEST")
    print("="*70)
    print(f"Fluide geladen: {len(db.fluids)}")
    print(f"Kategorien: {', '.join(db.get_all_categories())}")
    print()
    
    # Kategorien anzeigen
    for category in db.get_all_categories():
        fluids = db.get_fluids_by_category(category)
        print(f"\n{category}: {len(fluids)} Fluide")
        for fluid in fluids:
            print(f"  - {fluid.name} ({fluid.concentration_percent}%)")
            print(f"    Frostschutz bis {fluid.min_temp}°C")
            if fluid.notes:
                print(f"    Hinweis: {fluid.notes[0]}")
    
    # Test: Vergleich von Ethylenglykol-Konzentrationen
    print("\n" + "="*70)
    print("VERGLEICH: Ethylenglykol 20% vs 25% vs 30% bei 0°C")
    print("="*70)
    
    comparison = db.compare_fluids(
        ["Ethylenglykol 20%", "Ethylenglykol 25%", "Ethylenglykol 30%"],
        temperature=0.0
    )
    
    for fluid_data in comparison:
        print(f"\n{fluid_data['name']}:")
        print(f"  Dichte: {fluid_data['density']:.1f} kg/m³")
        print(f"  Viskosität: {fluid_data['viscosity']:.5f} Pa·s")
        print(f"  Wärmekapazität: {fluid_data['heat_capacity']:.0f} J/kg·K")
        print(f"  Frostschutz bis: {fluid_data['min_temp']}°C")
    
    print("\n" + "="*70)

