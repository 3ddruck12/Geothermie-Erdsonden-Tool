"""Datenbank für Rohrkonfigurationen in Erdwärmesonden."""

import os
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple


@dataclass
class ConfigurationGeometry:
    """Geometrische Eigenschaften einer Rohrkonfiguration."""
    pipes_per_borehole: int
    circuits_per_borehole: int
    pipe_arrangement: str
    typical_shank_spacing: float  # m


@dataclass
class ConfigurationThermal:
    """Thermische Eigenschaften einer Rohrkonfiguration."""
    borehole_resistance_typical: float  # m·K/W
    borehole_resistance_min: float
    borehole_resistance_max: float


@dataclass
class ConfigurationHydraulics:
    """Hydraulische Eigenschaften einer Rohrkonfiguration."""
    flow_path_multiplier: float
    typical_pressure_drop_factor: float


@dataclass
class PowerRange:
    """Leistungsbereich."""
    min: float  # kW
    max: float  # kW


@dataclass
class PipeConfiguration:
    """Rohrkonfiguration für Erdwärmesonden."""
    id: str
    name: str
    display_name: str
    type: str
    description: str
    geometry: ConfigurationGeometry
    thermal: ConfigurationThermal
    hydraulics: ConfigurationHydraulics
    typical_use: str
    power_range: PowerRange
    advantages: List[str] = field(default_factory=list)
    disadvantages: List[str] = field(default_factory=list)
    recommended: bool = False
    notes: List[str] = field(default_factory=list)
    
    def is_suitable_for_power(self, power_kw: float) -> bool:
        """Prüft ob Konfiguration für gegebene Leistung geeignet ist."""
        return self.power_range.min <= power_kw <= self.power_range.max
    
    def get_circuits_per_borehole(self) -> int:
        """Gibt Anzahl Kreise pro Bohrung zurück."""
        return self.geometry.circuits_per_borehole
    
    def get_pipes_per_borehole(self) -> int:
        """Gibt Anzahl Rohre pro Bohrung zurück."""
        return self.geometry.pipes_per_borehole
    
    def calculate_total_circuits(self, num_boreholes: int) -> int:
        """Berechnet Gesamtzahl System-Kreise."""
        return num_boreholes * self.geometry.circuits_per_borehole
    
    def calculate_total_pipes(self, num_boreholes: int) -> int:
        """Berechnet Gesamtzahl Rohre."""
        return num_boreholes * self.geometry.pipes_per_borehole


class PipeConfigurationDatabase:
    """Datenbank für Rohrkonfigurationen."""
    
    def __init__(self, xml_file: Optional[str] = None):
        """
        Initialisiert die Rohrkonfigurations-Datenbank.
        
        Args:
            xml_file: Pfad zur XML-Datei (Standard: pipe_configurations.xml)
        """
        if xml_file is None:
            # Standard: XML-Datei im gleichen Verzeichnis
            current_dir = os.path.dirname(__file__)
            xml_file = os.path.join(current_dir, 'pipe_configurations.xml')
        
        self.xml_file = xml_file
        self.configurations: Dict[str, PipeConfiguration] = {}
        
        # Lade Konfigurationen aus XML
        self._load_from_xml()
    
    def _load_from_xml(self):
        """Lädt Rohrkonfigurationen aus XML-Datei."""
        try:
            tree = ET.parse(self.xml_file)
            root = tree.getroot()
            
            for config_elem in root.findall('configuration'):
                config = self._parse_configuration(config_elem)
                self.configurations[config.id] = config
        
        except FileNotFoundError:
            print(f"⚠️ Rohrkonfigurations-Datenbank nicht gefunden: {self.xml_file}")
            print(f"⚠️ Verwende Fallback-Konfigurationen")
            self._load_fallback_configurations()
        except Exception as e:
            print(f"⚠️ Fehler beim Laden der Rohrkonfigurations-Datenbank: {e}")
            self._load_fallback_configurations()
    
    def _parse_configuration(self, elem: ET.Element) -> PipeConfiguration:
        """Parst eine Rohrkonfiguration aus XML-Element."""
        # Basis-Infos
        config_id = elem.find('id').text
        name = elem.find('name').text
        display_name = elem.find('display_name').text
        config_type = elem.find('type').text
        description = elem.find('description').text
        
        # Geometrie
        geom_elem = elem.find('geometry')
        geometry = ConfigurationGeometry(
            pipes_per_borehole=int(geom_elem.find('pipes_per_borehole').text),
            circuits_per_borehole=int(geom_elem.find('circuits_per_borehole').text),
            pipe_arrangement=geom_elem.find('pipe_arrangement').text,
            typical_shank_spacing=float(geom_elem.find('typical_shank_spacing').text)
        )
        
        # Thermische Eigenschaften
        thermal_elem = elem.find('thermal_properties')
        thermal = ConfigurationThermal(
            borehole_resistance_typical=float(thermal_elem.find('borehole_resistance_typical').text),
            borehole_resistance_min=float(thermal_elem.find('borehole_resistance_min').text),
            borehole_resistance_max=float(thermal_elem.find('borehole_resistance_max').text)
        )
        
        # Hydraulik
        hydraulics_elem = elem.find('hydraulics')
        hydraulics = ConfigurationHydraulics(
            flow_path_multiplier=float(hydraulics_elem.find('flow_path_multiplier').text),
            typical_pressure_drop_factor=float(hydraulics_elem.find('typical_pressure_drop_factor').text)
        )
        
        # Anwendung
        app_elem = elem.find('application')
        typical_use = app_elem.find('typical_use').text
        
        power_elem = app_elem.find('power_range_kw')
        power_range = PowerRange(
            min=float(power_elem.find('min').text),
            max=float(power_elem.find('max').text)
        )
        
        # Vor-/Nachteile
        advantages = []
        adv_elem = app_elem.find('advantages')
        if adv_elem is not None:
            advantages = [adv.text for adv in adv_elem.findall('advantage')]
        
        disadvantages = []
        disadv_elem = app_elem.find('disadvantages')
        if disadv_elem is not None:
            disadvantages = [dis.text for dis in disadv_elem.findall('disadvantage')]
        
        # Empfohlen?
        recommended_elem = elem.find('recommended')
        recommended = recommended_elem.text.lower() == 'true' if recommended_elem is not None else False
        
        # Optional: Hinweise
        notes = []
        notes_elem = elem.find('notes')
        if notes_elem is not None:
            notes = [note.text for note in notes_elem.findall('note')]
        
        return PipeConfiguration(
            id=config_id,
            name=name,
            display_name=display_name,
            type=config_type,
            description=description,
            geometry=geometry,
            thermal=thermal,
            hydraulics=hydraulics,
            typical_use=typical_use,
            power_range=power_range,
            advantages=advantages,
            disadvantages=disadvantages,
            recommended=recommended,
            notes=notes
        )
    
    def _load_fallback_configurations(self):
        """Lädt minimale Fallback-Konfigurationen falls XML nicht geladen werden kann."""
        fallback_configs = [
            PipeConfiguration(
                id="single-u",
                name="Single-U",
                display_name="Single-U (1x2 Rohre)",
                type="u_tube",
                description="Ein U-Rohr pro Bohrung",
                geometry=ConfigurationGeometry(2, 1, "U-shaped", 0.052),
                thermal=ConfigurationThermal(0.12, 0.08, 0.18),
                hydraulics=ConfigurationHydraulics(1.0, 1.0),
                typical_use="Standard",
                power_range=PowerRange(3, 15),
                recommended=True,
                notes=["Fallback: XML nicht geladen"]
            ),
        ]
        
        for config in fallback_configs:
            self.configurations[config.id] = config
    
    def get_configuration(self, config_id: str) -> Optional[PipeConfiguration]:
        """Gibt eine Konfiguration nach ID zurück."""
        return self.configurations.get(config_id)
    
    def get_all_ids(self) -> List[str]:
        """Gibt alle Konfigurations-IDs zurück."""
        return list(self.configurations.keys())
    
    def get_all_display_names(self) -> List[str]:
        """Gibt alle Display-Namen zurück."""
        return [c.display_name for c in self.configurations.values()]
    
    def get_recommended_configurations(self) -> List[PipeConfiguration]:
        """Gibt alle empfohlenen Konfigurationen zurück."""
        return [c for c in self.configurations.values() if c.recommended]
    
    def find_suitable_configurations(self, power_kw: float) -> List[Tuple[PipeConfiguration, float]]:
        """
        Findet passende Konfigurationen für gegebene Leistung mit Score.
        
        Args:
            power_kw: Wärmepumpen-Leistung in kW
        
        Returns:
            Liste von Tupeln (Konfiguration, Score)
        """
        suitable = []
        
        for config in self.configurations.values():
            if config.is_suitable_for_power(power_kw):
                # Score basierend auf optimaler Auslastung
                mid_power = (config.power_range.min + config.power_range.max) / 2
                deviation = abs(power_kw - mid_power) / mid_power
                score = max(0, 100 - deviation * 100)
                
                # Bonus für empfohlene Konfigurationen
                if config.recommended:
                    score += 10
                
                suitable.append((config, min(100, score)))
        
        # Sortiere nach Score (höchster zuerst)
        suitable.sort(reverse=True, key=lambda x: x[1])
        
        return suitable
    
    def get_configuration_by_name(self, name: str) -> Optional[PipeConfiguration]:
        """Gibt eine Konfiguration nach Name zurück."""
        for config in self.configurations.values():
            if config.name.lower() == name.lower() or config.display_name.lower() == name.lower():
                return config
        return None


if __name__ == "__main__":
    # Test der Rohrkonfigurations-Datenbank
    import sys
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')
    
    db = PipeConfigurationDatabase()
    
    print("="*80)
    print("ROHRKONFIGURATIONS-DATENBANK TEST")
    print("="*80)
    print(f"Konfigurationen geladen: {len(db.configurations)}")
    print(f"IDs: {', '.join(db.get_all_ids())}")
    print()
    
    # Alle Konfigurationen anzeigen
    print("KONFIGURATIONEN:")
    print("="*80)
    for config in db.configurations.values():
        marker = "✓" if config.recommended else " "
        print(f"{marker} {config.display_name} ({config.id})")
        print(f"  {config.description}")
        print(f"  Geometrie: {config.geometry.pipes_per_borehole} Rohre, "
              f"{config.geometry.circuits_per_borehole} Kreis(e)")
        print(f"  Thermisch: R_b = {config.thermal.borehole_resistance_typical} m·K/W")
        print(f"  Leistung: {config.power_range.min}-{config.power_range.max} kW")
        print(f"  Vorteile: {config.advantages[0] if config.advantages else '-'}")
        print()
    
    # Suche für 11 kW Anlage
    print("="*80)
    print("PASSENDE KONFIGURATIONEN FÜR 11 kW ANLAGE")
    print("="*80)
    suitable = db.find_suitable_configurations(power_kw=11)
    
    for i, (config, score) in enumerate(suitable, 1):
        print(f"{i}. {config.display_name} (Score: {score:.1f}/100)")
        print(f"   {config.description}")
        print(f"   Leistungsbereich: {config.power_range.min}-{config.power_range.max} kW")
        if score > 80:
            print(f"   ✅ Sehr gut geeignet")
        elif score > 60:
            print(f"   ✓ Gut geeignet")
        print()
    
    # Vergleich: Single-U vs. Double-U
    print("="*80)
    print("VERGLEICH: Single-U vs. Double-U")
    print("="*80)
    single_u = db.get_configuration("single-u")
    double_u = db.get_configuration("double-u")
    
    if single_u and double_u:
        print(f"\n{single_u.display_name}:")
        print(f"  Rohre/Kreise: {single_u.geometry.pipes_per_borehole}/{single_u.geometry.circuits_per_borehole}")
        print(f"  R_b: {single_u.thermal.borehole_resistance_typical} m·K/W")
        print(f"  ✓ {single_u.advantages[0]}")
        
        print(f"\n{double_u.display_name}:")
        print(f"  Rohre/Kreise: {double_u.geometry.pipes_per_borehole}/{double_u.geometry.circuits_per_borehole}")
        print(f"  R_b: {double_u.thermal.borehole_resistance_typical} m·K/W")
        print(f"  ✓ {double_u.advantages[0]}")
        
        improvement = (single_u.thermal.borehole_resistance_typical / 
                      double_u.thermal.borehole_resistance_typical - 1) * 100
        print(f"\n⚡ Double-U hat {improvement:.0f}% niedrigeren Bohrlochwiderstand!")
    
    print("\n" + "="*80)

