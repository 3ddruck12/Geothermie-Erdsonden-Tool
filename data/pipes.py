"""Datenbank für Erdwärmesonden-Rohre."""

import os
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class PipeDimensions:
    """Rohr-Abmessungen."""
    outer_diameter: float  # m
    wall_thickness: float  # m
    inner_diameter: float  # m


@dataclass
class Pipe:
    """Erdwärmesonden-Rohr mit allen Eigenschaften."""
    name: str
    material: str
    standard: str
    dimensions: PipeDimensions
    thermal_conductivity: float  # W/m·K
    
    # Anwendungsinformationen
    typical_use: Optional[str] = None
    flow_range_m3h: Optional[str] = None
    configuration: Optional[str] = None  # "single_u", "double_u", "coaxial"
    pressure_rating: Optional[str] = None
    recommended: bool = False
    notes: List[str] = field(default_factory=list)
    
    def get_inner_diameter_mm(self) -> float:
        """Gibt Innendurchmesser in mm zurück."""
        return self.dimensions.inner_diameter * 1000
    
    def get_outer_diameter_mm(self) -> float:
        """Gibt Außendurchmesser in mm zurück."""
        return self.dimensions.outer_diameter * 1000
    
    def get_cross_section_area_m2(self) -> float:
        """Berechnet Querschnittsfläche in m²."""
        import math
        return math.pi * (self.dimensions.inner_diameter / 2) ** 2
    
    def is_suitable_for_flow(self, flow_m3h: float, velocity_max: float = 1.5) -> bool:
        """
        Prüft ob Rohr für gegebenen Volumenstrom geeignet ist.
        
        Args:
            flow_m3h: Volumenstrom in m³/h
            velocity_max: Max. zulässige Geschwindigkeit in m/s (Standard: 1.5)
        
        Returns:
            True wenn Rohr geeignet ist
        """
        area = self.get_cross_section_area_m2()
        flow_m3s = flow_m3h / 3600
        velocity = flow_m3s / area if area > 0 else 999
        return velocity <= velocity_max


class PipeDatabase:
    """Datenbank für Erdwärmesonden-Rohre."""
    
    def __init__(self, xml_file: Optional[str] = None):
        """
        Initialisiert die Rohr-Datenbank.
        
        Args:
            xml_file: Pfad zur XML-Datei (Standard: pipes.xml)
        """
        if xml_file is None:
            # Standard: XML-Datei im gleichen Verzeichnis
            current_dir = os.path.dirname(__file__)
            xml_file = os.path.join(current_dir, 'pipes.xml')
        
        self.xml_file = xml_file
        self.pipes: Dict[str, Pipe] = {}
        self.categories: Dict[str, List[Pipe]] = {}
        
        # Lade Rohre aus XML
        self._load_from_xml()
    
    def _load_from_xml(self):
        """Lädt Rohre aus XML-Datei."""
        try:
            tree = ET.parse(self.xml_file)
            root = tree.getroot()
            
            for category in root.findall('pipe_category'):
                category_name = category.get('name')
                category_material = category.get('material')
                self.categories[category_name] = []
                
                for pipe_elem in category.findall('pipe'):
                    pipe = self._parse_pipe(pipe_elem, category_material)
                    self.pipes[pipe.name] = pipe
                    self.categories[category_name].append(pipe)
        
        except FileNotFoundError:
            print(f"⚠️ Rohr-Datenbank nicht gefunden: {self.xml_file}")
            print(f"⚠️ Verwende Fallback-Rohre")
            self._load_fallback_pipes()
        except Exception as e:
            print(f"⚠️ Fehler beim Laden der Rohr-Datenbank: {e}")
            self._load_fallback_pipes()
    
    def _parse_pipe(self, elem: ET.Element, category_material: str) -> Pipe:
        """Parst ein Rohr aus XML-Element."""
        # Basis-Infos
        name = elem.find('name').text
        material = elem.find('material').text
        standard = elem.find('standard').text
        
        # Abmessungen
        dim_elem = elem.find('dimensions')
        dimensions = PipeDimensions(
            outer_diameter=float(dim_elem.find('outer_diameter').text),
            wall_thickness=float(dim_elem.find('wall_thickness').text),
            inner_diameter=float(dim_elem.find('inner_diameter').text)
        )
        
        # Thermische Eigenschaften
        thermal_elem = elem.find('thermal_properties')
        thermal_conductivity = float(thermal_elem.find('conductivity').text)
        
        # Anwendung
        app_elem = elem.find('application')
        typical_use = app_elem.find('typical_use').text if app_elem is not None else None
        
        flow_range_elem = app_elem.find('flow_range_m3h') if app_elem is not None else None
        flow_range = flow_range_elem.text if flow_range_elem is not None else None
        
        config_elem = app_elem.find('configuration') if app_elem is not None else None
        configuration = config_elem.text if config_elem is not None else None
        
        pressure_elem = app_elem.find('pressure_rating') if app_elem is not None else None
        pressure_rating = pressure_elem.text if pressure_elem is not None else None
        
        recommended_elem = app_elem.find('recommended') if app_elem is not None else None
        recommended = recommended_elem.text.lower() == 'true' if recommended_elem is not None else False
        
        # Optional: Hinweise
        notes = []
        notes_elem = elem.find('notes')
        if notes_elem is not None:
            notes = [note.text for note in notes_elem.findall('note')]
        
        return Pipe(
            name=name,
            material=material,
            standard=standard,
            dimensions=dimensions,
            thermal_conductivity=thermal_conductivity,
            typical_use=typical_use,
            flow_range_m3h=flow_range,
            configuration=configuration,
            pressure_rating=pressure_rating,
            recommended=recommended,
            notes=notes
        )
    
    def _load_fallback_pipes(self):
        """Lädt minimale Fallback-Rohre falls XML nicht geladen werden kann."""
        fallback_pipes = [
            Pipe(
                name="PE DN32 SDR-11",
                material="PE",
                standard="SDR-11",
                dimensions=PipeDimensions(0.032, 0.003, 0.026),
                thermal_conductivity=0.42,
                typical_use="Standard für mittlere Anlagen",
                recommended=True,
                notes=["Fallback: XML nicht geladen"]
            ),
        ]
        
        self.categories["Fallback"] = fallback_pipes
        for pipe in fallback_pipes:
            self.pipes[pipe.name] = pipe
    
    def get_pipe(self, name: str) -> Optional[Pipe]:
        """Gibt ein Rohr nach Namen zurück."""
        return self.pipes.get(name)
    
    def get_all_names(self) -> List[str]:
        """Gibt alle Rohrnamen zurück."""
        return sorted(self.pipes.keys())
    
    def get_pipes_by_category(self, category: str) -> List[Pipe]:
        """Gibt alle Rohre einer Kategorie zurück."""
        return self.categories.get(category, [])
    
    def get_all_categories(self) -> List[str]:
        """Gibt alle Kategorien zurück."""
        return list(self.categories.keys())
    
    def get_pipes_by_material(self, material: str) -> List[Pipe]:
        """Gibt alle Rohre eines Materials zurück."""
        return [p for p in self.pipes.values() if material.lower() in p.material.lower()]
    
    def get_recommended_pipes(self) -> List[Pipe]:
        """Gibt alle empfohlenen Rohre zurück."""
        return [p for p in self.pipes.values() if p.recommended]
    
    def find_suitable_pipes(self, 
                           flow_m3h: float,
                           max_velocity: float = 1.5,
                           material_filter: Optional[str] = None) -> List[Pipe]:
        """
        Findet passende Rohre für gegebenen Volumenstrom.
        
        Args:
            flow_m3h: Volumenstrom in m³/h
            max_velocity: Max. zulässige Geschwindigkeit in m/s
            material_filter: Optional: nur bestimmtes Material
        
        Returns:
            Liste passender Rohre
        """
        suitable = []
        for pipe in self.pipes.values():
            # Material-Filter
            if material_filter and material_filter.lower() not in pipe.material.lower():
                continue
            
            # Geschwindigkeit prüfen
            if pipe.is_suitable_for_flow(flow_m3h, max_velocity):
                suitable.append(pipe)
        
        return suitable


if __name__ == "__main__":
    # Test der Rohr-Datenbank
    import sys
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')
    
    db = PipeDatabase()
    
    print("="*80)
    print("ROHR-DATENBANK TEST")
    print("="*80)
    print(f"Rohre geladen: {len(db.pipes)}")
    print(f"Kategorien: {', '.join(db.get_all_categories())}")
    print()
    
    # Empfohlene Rohre
    print("EMPFOHLENE ROHRE:")
    print("="*80)
    for pipe in db.get_recommended_pipes():
        print(f"✓ {pipe.name}")
        print(f"  Material: {pipe.material} ({pipe.standard})")
        print(f"  Ø außen/innen: {pipe.get_outer_diameter_mm():.1f}/{pipe.get_inner_diameter_mm():.1f} mm")
        print(f"  λ = {pipe.thermal_conductivity} W/m·K")
        print(f"  Anwendung: {pipe.typical_use}")
        if pipe.flow_range_m3h:
            print(f"  Volumenstrom: {pipe.flow_range_m3h} m³/h")
        print()
    
    # Suche passende Rohre für 11 kW Anlage
    print("="*80)
    print("ROHRE FÜR 11 kW ANLAGE (ca. 2.5 m³/h)")
    print("="*80)
    suitable = db.find_suitable_pipes(flow_m3h=2.5, material_filter="PE")
    
    print(f"Gefunden: {len(suitable)} PE-Rohre")
    for pipe in suitable[:5]:  # Top 5
        print(f"  - {pipe.name}: di={pipe.get_inner_diameter_mm():.1f}mm")
    
    # Kategorie-Übersicht
    print("\n" + "="*80)
    print("KATEGORIEN")
    print("="*80)
    for category in db.get_all_categories():
        pipes = db.get_pipes_by_category(category)
        print(f"{category}: {len(pipes)} Rohre")
    
    print("\n" + "="*80)

