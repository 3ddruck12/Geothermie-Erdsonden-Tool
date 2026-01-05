"""Datenbank für Verfüllmaterialien."""

import os
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class GroutMaterial:
    """Verfüllmaterial mit Eigenschaften."""
    name: str
    thermal_conductivity: float  # W/m·K
    density: float  # kg/m³
    price_per_kg: float  # EUR/kg
    description: str
    typical_application: str
    
    # Zusatzinformationen
    type: Optional[str] = None  # "cement_bentonite", "thermal_sand", etc.
    quality_class: Optional[str] = None  # "standard", "enhanced", "high_performance"
    price_range: Optional[str] = None  # "budget", "standard", "premium"
    advantages: List[str] = field(default_factory=list)
    disadvantages: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)


class GroutMaterialDB:
    """Datenbank für Verfüllmaterialien."""
    
    def __init__(self, xml_file: Optional[str] = None):
        """
        Initialisiert die Verfüllmaterial-Datenbank.
        
        Args:
            xml_file: Pfad zur XML-Datei (Standard: grout_materials.xml)
        """
        if xml_file is None:
            # Standard: XML-Datei im gleichen Verzeichnis
            current_dir = os.path.dirname(__file__)
            xml_file = os.path.join(current_dir, 'grout_materials.xml')
        
        self.xml_file = xml_file
        self.materials: Dict[str, GroutMaterial] = {}
        self.categories: Dict[str, List[GroutMaterial]] = {}
        
        # Lade Materialien aus XML
        self._load_from_xml()
    
    def _load_from_xml(self):
        """Lädt Verfüllmaterialien aus XML-Datei."""
        try:
            tree = ET.parse(self.xml_file)
            root = tree.getroot()
            
            for category in root.findall('grout_category'):
                category_name = category.get('name')
                category_type = category.get('type')
                self.categories[category_name] = []
                
                for material_elem in category.findall('grout_material'):
                    material = self._parse_material(material_elem, category_type)
                    self.materials[material.name] = material
                    self.categories[category_name].append(material)
        
        except FileNotFoundError:
            print(f"⚠️ Verfüllmaterial-Datenbank nicht gefunden: {self.xml_file}")
            print(f"⚠️ Verwende Fallback-Materialien")
            self._load_fallback_materials()
        except Exception as e:
            print(f"⚠️ Fehler beim Laden der Verfüllmaterial-Datenbank: {e}")
            self._load_fallback_materials()
    
    def _parse_material(self, elem: ET.Element, category_type: str) -> GroutMaterial:
        """Parst ein Verfüllmaterial aus XML-Element."""
        # Basis-Infos
        name = elem.find('name').text
        material_type = elem.find('type').text
        
        # Quality class
        quality_elem = elem.find('quality_class')
        quality_class = quality_elem.text if quality_elem is not None else None
        
        # Thermische Eigenschaften
        thermal_elem = elem.find('thermal_properties')
        conductivity = float(thermal_elem.find('conductivity').text)
        
        # Physikalische Eigenschaften
        physical_elem = elem.find('physical_properties')
        density = float(physical_elem.find('density').text)
        
        # Preis
        pricing_elem = elem.find('pricing')
        price_per_kg = float(pricing_elem.find('price_per_kg').text)
        price_range_elem = pricing_elem.find('price_range')
        price_range = price_range_elem.text if price_range_elem is not None else None
        
        # Anwendung
        app_elem = elem.find('application')
        description = app_elem.find('description').text
        typical_use = app_elem.find('typical_use').text
        
        # Optional: Vor-/Nachteile
        advantages = []
        adv_elem = app_elem.find('advantages')
        if adv_elem is not None:
            advantages = [adv.text for adv in adv_elem.findall('advantage')]
        
        disadvantages = []
        disadv_elem = app_elem.find('disadvantages')
        if disadv_elem is not None:
            disadvantages = [dis.text for dis in disadv_elem.findall('disadvantage')]
        
        # Optional: Hinweise
        notes = []
        notes_elem = elem.find('notes')
        if notes_elem is not None:
            notes = [note.text for note in notes_elem.findall('note')]
        
        return GroutMaterial(
            name=name,
            thermal_conductivity=conductivity,
            density=density,
            price_per_kg=price_per_kg,
            description=description,
            typical_application=typical_use,
            type=material_type,
            quality_class=quality_class,
            price_range=price_range,
            advantages=advantages,
            disadvantages=disadvantages,
            notes=notes
        )
    
    def _load_fallback_materials(self):
        """Lädt minimale Fallback-Materialien falls XML nicht geladen werden kann."""
        fallback_materials = [
            GroutMaterial(
                name="Zement-Bentonit Standard",
                thermal_conductivity=0.8,
                density=1800,
                price_per_kg=0.15,
                description="Standardmischung, kostengünstig",
                typical_application="Normale Böden, geringe Anforderungen",
                notes=["Fallback: XML nicht geladen"]
            ),
            GroutMaterial(
                name="Zement-Bentonit verbessert",
                thermal_conductivity=1.3,
                density=1900,
                price_per_kg=0.25,
                description="Verbesserte Wärmeleitfähigkeit",
                typical_application="Standardanwendung, gutes Preis-Leistungs-Verhältnis",
                notes=["Fallback: XML nicht geladen"]
            ),
        ]
        
        self.categories["Fallback"] = fallback_materials
        for material in fallback_materials:
            self.materials[material.name] = material
    
    def get_material(self, name: str) -> Optional[GroutMaterial]:
        """Holt ein Material nach Namen."""
        return self.materials.get(name)
    
    def get_all_names(self) -> List[str]:
        """Gibt alle Materialnamen zurück."""
        return sorted(self.materials.keys())
    
    def get_all_materials(self) -> Dict[str, GroutMaterial]:
        """Gibt alle Materialien zurück."""
        return self.materials
    
    def get_materials_by_category(self, category: str) -> List[GroutMaterial]:
        """Gibt alle Materialien einer Kategorie zurück."""
        return self.categories.get(category, [])
    
    def get_all_categories(self) -> List[str]:
        """Gibt alle Kategorien zurück."""
        return list(self.categories.keys())
    
    def get_materials_by_quality(self, quality_class: str) -> List[GroutMaterial]:
        """Gibt alle Materialien einer Qualitätsklasse zurück."""
        return [m for m in self.materials.values() if m.quality_class == quality_class]
    
    @staticmethod
    def calculate_volume(
        borehole_depth: float,
        borehole_diameter: float,
        pipe_outer_diameter: float,
        num_pipes: int = 4
    ) -> float:
        """
        Berechnet das benötigte Verfüllvolumen.
        
        Args:
            borehole_depth: Bohrtiefe in m
            borehole_diameter: Bohrloch-Durchmesser in m
            pipe_outer_diameter: Rohr-Außendurchmesser in m
            num_pipes: Anzahl Rohre (Standard: 4 für 4-Rohr-System)
            
        Returns:
            Volumen in m³
        """
        # Bohrloch-Volumen
        borehole_radius = borehole_diameter / 2
        borehole_volume = 3.14159 * (borehole_radius ** 2) * borehole_depth
        
        # Rohr-Volumen (Außenvolumen)
        pipe_radius = pipe_outer_diameter / 2
        pipe_volume = 3.14159 * (pipe_radius ** 2) * borehole_depth * num_pipes
        
        # Verfüllvolumen
        grout_volume = borehole_volume - pipe_volume
        
        # Sicherheitszuschlag 10%
        grout_volume_with_safety = grout_volume * 1.10
        
        return grout_volume_with_safety
    
    @staticmethod
    def calculate_material_amount(volume_m3: float, material: GroutMaterial) -> Dict[str, float]:
        """
        Berechnet die benötigte Materialmenge und Kosten.
        
        Args:
            volume_m3: Volumen in m³
            material: Verfüllmaterial
            
        Returns:
            Dictionary mit Mengen und Kosten
        """
        # Masse berechnen
        mass_kg = volume_m3 * material.density
        
        # Kosten berechnen
        total_cost = mass_kg * material.price_per_kg
        
        # Säcke (typisch 25 kg pro Sack)
        bags_25kg = mass_kg / 25
        
        return {
            'volume_m3': volume_m3,
            'mass_kg': mass_kg,
            'bags_25kg': bags_25kg,
            'total_cost_eur': total_cost,
            'cost_per_m': total_cost / (volume_m3 * 100) if volume_m3 > 0 else 0  # EUR/m Bohrtiefe
        }


if __name__ == "__main__":
    # Test der Verfüllmaterial-Datenbank
    import sys
    # Erzwinge UTF-8 Encoding für Ausgabe (Windows-Kompatibilität)
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')
    
    db = GroutMaterialDB()
    
    print("="*80)
    print("VERFÜLLMATERIAL-DATENBANK TEST")
    print("="*80)
    print(f"Materialien geladen: {len(db.materials)}")
    print(f"Kategorien: {', '.join(db.get_all_categories())}")
    print()
    
    # Kategorien anzeigen
    for category in db.get_all_categories():
        materials = db.get_materials_by_category(category)
        print(f"\n{category}: {len(materials)} Materialien")
        for mat in materials:
            print(f"  - {mat.name}")
            print(f"    λ = {mat.thermal_conductivity} W/m·K | ρ = {mat.density} kg/m³")
            print(f"    Preis: {mat.price_per_kg:.2f} EUR/kg ({mat.price_range})")
            if mat.advantages:
                print(f"    ✓ {mat.advantages[0]}")
    
    # Beispielberechnung
    print("\n" + "="*80)
    print("BEISPIELBERECHNUNG")
    print("="*80)
    print("100m Bohrung, Ø 152mm, 4 Rohre Ø 32mm")
    volume = GroutMaterialDB.calculate_volume(100, 0.152, 0.032, 4)
    print(f"Benötigtes Volumen: {volume:.3f} m³")
    
    material = db.get_material("Zement-Bentonit verbessert")
    if material:
        amounts = GroutMaterialDB.calculate_material_amount(volume, material)
        
        print(f"\nMaterial: {material.name}")
        print(f"  Masse: {amounts['mass_kg']:.1f} kg")
        print(f"  Säcke (25kg): {amounts['bags_25kg']:.1f}")
        print(f"  Kosten gesamt: {amounts['total_cost_eur']:.2f} EUR")
        print(f"  Kosten pro Meter: {amounts['cost_per_m']:.2f} EUR/m")
    
    # Vergleich: Standard vs. Hochleistung
    print("\n" + "="*80)
    print("VERGLEICH: Standard vs. Hochleistung")
    print("="*80)
    standard = db.get_material("Zement-Bentonit Standard")
    premium = db.get_material("Hochleistung (Spezial)")
    
    if standard and premium:
        print(f"\n{standard.name}:")
        print(f"  λ = {standard.thermal_conductivity} W/m·K")
        print(f"  Preis: {standard.price_per_kg:.2f} EUR/kg")
        
        print(f"\n{premium.name}:")
        print(f"  λ = {premium.thermal_conductivity} W/m·K")
        print(f"  Preis: {premium.price_per_kg:.2f} EUR/kg")
        
        factor = premium.thermal_conductivity / standard.thermal_conductivity
        price_factor = premium.price_per_kg / standard.price_per_kg
        print(f"\n⚡ Wärmeleitfähigkeit: {factor:.1f}x besser")
        print(f"💰 Preis: {price_factor:.1f}x teurer")
    
    print("\n" + "="*80)

