"""Datenbank für Bodentypen mit typischen Werten."""

import os
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class SoilType:
    """Bodentyp mit thermischen Eigenschaften."""
    name: str
    thermal_conductivity_min: float  # W/m·K
    thermal_conductivity_max: float  # W/m·K
    thermal_conductivity_typical: float  # W/m·K
    heat_capacity_min: float  # MJ/m³·K
    heat_capacity_max: float  # MJ/m³·K
    heat_capacity_typical: float  # MJ/m³·K
    heat_extraction_rate_min: float  # W/m
    heat_extraction_rate_max: float  # W/m
    description: str
    moisture_dependency: str
    
    # Zusatzinformationen
    type: Optional[str] = None  # "sediment", "sedimentary_rock", "igneous_rock"
    subtype: Optional[str] = None  # "sand", "clay", "granite_gneiss", etc.
    permeability: Optional[str] = None  # "sehr gering", "gering", "mittel", "hoch", "sehr hoch"
    notes: List[str] = field(default_factory=list)  # Geologische Hinweise


class SoilTypeDB:
    """Datenbank für Bodentypen nach VDI 4640."""
    
    def __init__(self, xml_file: Optional[str] = None):
        """
        Initialisiert die Bodentypn-Datenbank.
        
        Args:
            xml_file: Pfad zur XML-Datei (Standard: soil_types.xml)
        """
        if xml_file is None:
            # Standard: XML-Datei im gleichen Verzeichnis
            current_dir = os.path.dirname(__file__)
            xml_file = os.path.join(current_dir, 'soil_types.xml')
        
        self.xml_file = xml_file
        self.soil_types: Dict[str, SoilType] = {}
        self.categories: Dict[str, List[SoilType]] = {}
        
        # Lade Bodentypen aus XML
        self._load_from_xml()
    
    def _load_from_xml(self):
        """Lädt Bodentypen aus XML-Datei."""
        try:
            tree = ET.parse(self.xml_file)
            root = tree.getroot()
            
            for category in root.findall('soil_category'):
                category_name = category.get('name')
                category_type = category.get('type')
                self.categories[category_name] = []
                
                for soil_elem in category.findall('soil_type'):
                    soil = self._parse_soil_type(soil_elem, category_type)
                    self.soil_types[soil.name] = soil
                    self.categories[category_name].append(soil)
        
        except FileNotFoundError:
            print(f"⚠️ Bodentyp-Datenbank nicht gefunden: {self.xml_file}")
            print(f"⚠️ Verwende Fallback-Bodentypen")
            self._load_fallback_soil_types()
        except Exception as e:
            print(f"⚠️ Fehler beim Laden der Bodentyp-Datenbank: {e}")
            self._load_fallback_soil_types()
    
    def _parse_soil_type(self, elem: ET.Element, category_type: str) -> SoilType:
        """Parst einen Bodentyp aus XML-Element."""
        # Basis-Infos
        name = elem.find('name').text
        soil_type = elem.find('type').text
        
        # Optional: Subtyp
        subtype_elem = elem.find('subtype')
        subtype = subtype_elem.text if subtype_elem is not None else None
        
        # Thermische Eigenschaften
        thermal_elem = elem.find('thermal_properties')
        cond_min = float(thermal_elem.find('conductivity_min').text)
        cond_max = float(thermal_elem.find('conductivity_max').text)
        cond_typ = float(thermal_elem.find('conductivity_typical').text)
        
        # Wärmekapazität
        capacity_elem = elem.find('heat_capacity')
        cap_min = float(capacity_elem.find('min').text)
        cap_max = float(capacity_elem.find('max').text)
        cap_typ = float(capacity_elem.find('typical').text)
        
        # Entzugsrate
        extraction_elem = elem.find('heat_extraction_rate')
        extr_min = float(extraction_elem.find('min').text)
        extr_max = float(extraction_elem.find('max').text)
        
        # Eigenschaften
        props_elem = elem.find('properties')
        description = props_elem.find('description').text
        moisture_dep = props_elem.find('moisture_dependency').text
        
        # Optional: Durchlässigkeit
        permeability_elem = props_elem.find('permeability')
        permeability = permeability_elem.text if permeability_elem is not None else None
        
        # Optional: Hinweise
        notes_elem = elem.find('notes')
        notes = []
        if notes_elem is not None:
            notes = [note.text for note in notes_elem.findall('note')]
        
        return SoilType(
            name=name,
            thermal_conductivity_min=cond_min,
            thermal_conductivity_max=cond_max,
            thermal_conductivity_typical=cond_typ,
            heat_capacity_min=cap_min,
            heat_capacity_max=cap_max,
            heat_capacity_typical=cap_typ,
            heat_extraction_rate_min=extr_min,
            heat_extraction_rate_max=extr_max,
            description=description,
            moisture_dependency=moisture_dep,
            type=soil_type,
            subtype=subtype,
            permeability=permeability,
            notes=notes
        )
    
    def _load_fallback_soil_types(self):
        """Lädt minimale Fallback-Bodentypen falls XML nicht geladen werden kann."""
        fallback_types = [
            SoilType(
                name="Sand",
                thermal_conductivity_min=0.3,
                thermal_conductivity_max=2.4,
                thermal_conductivity_typical=1.8,
                heat_capacity_min=2.0,
                heat_capacity_max=2.8,
                heat_capacity_typical=2.4,
                heat_extraction_rate_min=40,
                heat_extraction_rate_max=80,
                description="Sand, trocken bis wassergesättigt",
                moisture_dependency="Stark abhängig von Wassergehalt",
                notes=["Fallback: XML nicht geladen"]
            ),
            SoilType(
                name="Granit/Gneis",
                thermal_conductivity_min=2.9,
                thermal_conductivity_max=4.1,
                thermal_conductivity_typical=3.5,
                heat_capacity_min=2.2,
                heat_capacity_max=2.7,
                heat_capacity_typical=2.4,
                heat_extraction_rate_min=65,
                heat_extraction_rate_max=85,
                description="Kristallines Festgestein",
                moisture_dependency="Keine Abhängigkeit",
                notes=["Fallback: XML nicht geladen"]
            ),
        ]
        
        self.categories["Fallback"] = fallback_types
        for soil in fallback_types:
            self.soil_types[soil.name] = soil
    
    def get_soil_type(self, name: str) -> Optional[SoilType]:
        """Holt einen Bodentyp nach Namen."""
        return self.soil_types.get(name)
    
    def get_all_names(self) -> List[str]:
        """Gibt alle Bodentypnamen zurück."""
        return sorted(self.soil_types.keys())
    
    def get_all_soil_types(self) -> Dict[str, SoilType]:
        """Gibt alle Bodentypen zurück."""
        return self.soil_types
    
    def get_soil_types_by_category(self, category: str) -> List[SoilType]:
        """Gibt alle Bodentypen einer Kategorie zurück."""
        return self.categories.get(category, [])
    
    def get_all_categories(self) -> List[str]:
        """Gibt alle Kategorien zurück."""
        return list(self.categories.keys())
    
    def get_soil_types_by_type(self, soil_type: str) -> List[SoilType]:
        """Gibt alle Bodentypen eines bestimmten Typs zurück."""
        return [s for s in self.soil_types.values() if s.type == soil_type]
    
    @staticmethod
    def estimate_ground_temperature(
        avg_air_temp: float,
        coldest_month_temp: float
    ) -> float:
        """
        Schätzt die ungestörte Bodentemperatur basierend auf Lufttemperaturen.
        
        Args:
            avg_air_temp: Durchschnittliche Jahreslufttemperatur in °C
            coldest_month_temp: Durchschnittstemperatur des kältesten Monats in °C
            
        Returns:
            Geschätzte Bodentemperatur in 10-15m Tiefe in °C
        """
        # Faustformel: Bodentemperatur ≈ Jahresmitteltemperatur + 1-2°C
        ground_temp = avg_air_temp + 1.5
        
        return ground_temp


if __name__ == "__main__":
    # Test der Bodentyp-Datenbank
    import sys
    # Erzwinge UTF-8 Encoding für Ausgabe (Windows-Kompatibilität)
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')
    
    db = SoilTypeDB()
    
    print("="*80)
    print("BODENTYP-DATENBANK TEST")
    print("="*80)
    print(f"Bodentypen geladen: {len(db.soil_types)}")
    print(f"Kategorien: {', '.join(db.get_all_categories())}")
    print()
    
    # Kategorien anzeigen
    for category in db.get_all_categories():
        soils = db.get_soil_types_by_category(category)
        print(f"\n{category}: {len(soils)} Typen")
        for soil in soils:
            print(f"  - {soil.name}")
            print(f"    λ: {soil.thermal_conductivity_typical} W/m·K "
                  f"({soil.thermal_conductivity_min}-{soil.thermal_conductivity_max})")
            print(f"    Entzug: {soil.heat_extraction_rate_min}-{soil.heat_extraction_rate_max} W/m")
            if soil.permeability:
                print(f"    Durchlässigkeit: {soil.permeability}")
            if soil.notes:
                print(f"    💡 {soil.notes[0]}")
    
    # Beispiel Temperaturschätzung
    print("\n" + "="*80)
    print("TEMPERATURSCHÄTZUNG")
    print("="*80)
    ground_temp = SoilTypeDB.estimate_ground_temperature(10.0, 2.0)
    print(f"Bei 10°C Jahresmittel und 2°C im kältesten Monat:")
    print(f"Geschätzte Bodentemperatur: {ground_temp:.1f}°C")
    print()
    
    # Vergleich bester vs. schlechtester Boden
    print("="*80)
    print("VERGLEICH: Bester vs. Schlechtester Boden")
    print("="*80)
    kies = db.get_soil_type("Kies (wasserführend)")
    ton_dry = db.get_soil_type("Ton (trocken)")
    
    if kies and ton_dry:
        print(f"\n{kies.name} (OPTIMAL):")
        print(f"  λ = {kies.thermal_conductivity_typical} W/m·K")
        print(f"  Entzug: {kies.heat_extraction_rate_min}-{kies.heat_extraction_rate_max} W/m")
        print(f"  → {kies.description}")
        
        print(f"\n{ton_dry.name} (UNGÜNSTIG):")
        print(f"  λ = {ton_dry.thermal_conductivity_typical} W/m·K")
        print(f"  Entzug: {ton_dry.heat_extraction_rate_min}-{ton_dry.heat_extraction_rate_max} W/m")
        print(f"  → {ton_dry.description}")
        
        factor = (kies.heat_extraction_rate_max / ton_dry.heat_extraction_rate_max)
        print(f"\n⚡ Faktor: Kies ist {factor:.1f}x besser als trockener Ton!")
    
    print("\n" + "="*80)

