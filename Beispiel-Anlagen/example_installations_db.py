"""Datenbank für Beispielanlagen von Erdwärmesonden-Systemen."""

import os
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


@dataclass
class ExampleInstallation:
    """Eine Beispielanlage für Erdwärmesonden."""
    id: int
    name: str
    building_type: str
    heating_system: str
    
    # Bohrlochfeld
    num_boreholes: int
    depth_m: float
    diameter_mm: float
    spacing_m: Optional[float]
    total_length_m: float
    
    # Rohre
    pipe_type: str
    pipe_outer_diameter_mm: float
    pipe_wall_thickness_mm: float
    
    # Verfüllmaterial
    grout_thermal_conductivity: float  # W/mK
    
    # Thermische Eigenschaften
    specific_extraction_power: float  # W/m
    max_extraction_power: float  # kW
    annual_energy: float  # kWh/a
    operating_hours: float  # h/a
    building_heat_load: float  # kW
    
    # Wärmeträgerflüssigkeit
    fluid_type: str
    fluid_concentration_percent: float
    flow_rate_m3h: float
    
    # Temperaturen
    inlet_min_temp: float  # °C
    outlet_max_temp: float  # °C
    delta_t: float  # K
    
    # Wärmepumpe
    heating_power_b0_w35: float  # kW
    cop_b0_w35: float
    annual_cop: float  # JAZ
    heating_power_b0_w45: Optional[float] = None  # kW
    cop_b0_w45: Optional[float] = None
    
    # Kühlung (optional)
    specific_injection_power: float = 0.0  # W/m
    annual_cooling_energy: float = 0.0  # kWh/a
    operating_hours_cooling: float = 0.0  # h
    winter_min_temp: Optional[float] = None  # °C
    summer_max_temp: Optional[float] = None  # °C
    delta_t_cooling: float = 0.0  # K
    eer_passive: Optional[str] = None
    
    # Zusatzinformationen
    notes: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert die Installation in ein Dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'building_type': self.building_type,
            'heating_system': self.heating_system,
            'num_boreholes': self.num_boreholes,
            'depth_m': self.depth_m,
            'diameter_mm': self.diameter_mm,
            'spacing_m': self.spacing_m,
            'total_length_m': self.total_length_m,
            'pipe_type': self.pipe_type,
            'pipe_outer_diameter_mm': self.pipe_outer_diameter_mm,
            'pipe_wall_thickness_mm': self.pipe_wall_thickness_mm,
            'grout_thermal_conductivity': self.grout_thermal_conductivity,
            'specific_extraction_power': self.specific_extraction_power,
            'max_extraction_power': self.max_extraction_power,
            'annual_energy': self.annual_energy,
            'operating_hours': self.operating_hours,
            'building_heat_load': self.building_heat_load,
            'fluid_type': self.fluid_type,
            'fluid_concentration_percent': self.fluid_concentration_percent,
            'flow_rate_m3h': self.flow_rate_m3h,
            'inlet_min_temp': self.inlet_min_temp,
            'outlet_max_temp': self.outlet_max_temp,
            'delta_t': self.delta_t,
            'heating_power_b0_w35': self.heating_power_b0_w35,
            'cop_b0_w35': self.cop_b0_w35,
            'annual_cop': self.annual_cop,
            'heating_power_b0_w45': self.heating_power_b0_w45,
            'cop_b0_w45': self.cop_b0_w45,
            'specific_injection_power': self.specific_injection_power,
            'annual_cooling_energy': self.annual_cooling_energy,
            'operating_hours_cooling': self.operating_hours_cooling,
            'winter_min_temp': self.winter_min_temp,
            'summer_max_temp': self.summer_max_temp,
            'delta_t_cooling': self.delta_t_cooling,
            'eer_passive': self.eer_passive,
            'notes': self.notes
        }


class ExampleInstallationsDatabase:
    """Datenbank für Beispielanlagen."""
    
    def __init__(self, xml_file: Optional[str] = None):
        """
        Initialisiert die Beispielanlagen-Datenbank.
        
        Args:
            xml_file: Pfad zur XML-Datei (Standard: beispielanlagen.xml)
        """
        if xml_file is None:
            # Standard: XML-Datei im gleichen Verzeichnis
            current_dir = os.path.dirname(__file__)
            xml_file = os.path.join(current_dir, 'beispielanlagen.xml')
        
        self.xml_file = xml_file
        self.installations: Dict[int, ExampleInstallation] = {}
        self.categories: Dict[str, List[ExampleInstallation]] = {}
        
        # Lade Installationen aus XML
        self._load_from_xml()
    
    def _load_from_xml(self):
        """Lädt Installationen aus XML-Datei."""
        try:
            tree = ET.parse(self.xml_file)
            root = tree.getroot()
            
            for category in root.findall('installation_category'):
                category_name = category.get('name')
                category_type = category.get('type')
                self.categories[category_name] = []
                
                for inst_elem in category.findall('example_installation'):
                    installation = self._parse_installation(inst_elem)
                    self.installations[installation.id] = installation
                    self.categories[category_name].append(installation)
        
        except FileNotFoundError:
            print(f"⚠️ Beispielanlagen-Datenbank nicht gefunden: {self.xml_file}")
            raise
        except Exception as e:
            print(f"⚠️ Fehler beim Laden der Beispielanlagen-Datenbank: {e}")
            raise
    
    def _parse_installation(self, elem: ET.Element) -> ExampleInstallation:
        """Parst eine Installation aus XML-Element."""
        # Basis-Infos
        id = int(elem.find('id').text)
        name = elem.find('name').text
        building_type = elem.find('building_type').text
        heating_system = elem.find('heating_system').text
        
        # Bohrlochfeld
        borefield = elem.find('borefield')
        num_boreholes = int(borefield.find('num_boreholes').text)
        depth_m = float(borefield.find('depth_m').text)
        diameter_mm = float(borefield.find('diameter_mm').text)
        spacing_elem = borefield.find('spacing_m')
        spacing_m = float(spacing_elem.text) if spacing_elem is not None and spacing_elem.text is not None and spacing_elem.text.strip() else None
        total_length_m = float(borefield.find('total_length_m').text)
        
        # Rohre
        pipes = elem.find('pipes')
        pipe_type = pipes.find('type').text
        pipe_outer_diameter_mm = float(pipes.find('outer_diameter_mm').text)
        pipe_wall_thickness_elem = pipes.find('wall_thickness_mm')
        pipe_wall_thickness_mm = float(pipe_wall_thickness_elem.text) if pipe_wall_thickness_elem is not None and pipe_wall_thickness_elem.text is not None and pipe_wall_thickness_elem.text.strip() else 0.0
        
        # Verfüllmaterial
        grout = elem.find('grout')
        grout_thermal_conductivity = float(grout.find('thermal_conductivity').text)
        
        # Thermische Eigenschaften
        thermal = elem.find('thermal_properties')
        specific_extraction_power = float(thermal.find('specific_extraction_power').text)
        max_extraction_power = float(thermal.find('max_extraction_power').text)
        annual_energy = float(thermal.find('annual_energy').text)
        operating_hours = float(thermal.find('operating_hours').text)
        building_heat_load = float(thermal.find('building_heat_load').text)
        
        # Wärmeträgerflüssigkeit
        fluid = elem.find('fluid')
        fluid_type_elem = fluid.find('type')
        fluid_type = fluid_type_elem.text if fluid_type_elem is not None and fluid_type_elem.text is not None and fluid_type_elem.text.strip() else ""
        fluid_concentration_percent = float(fluid.find('concentration_percent').text)
        flow_rate_m3h = float(fluid.find('flow_rate_m3h').text)
        
        # Temperaturen
        temps = elem.find('temperatures')
        inlet_min_temp = float(temps.find('inlet_min').text)
        outlet_max_elem = temps.find('outlet_max')
        outlet_max_temp = float(outlet_max_elem.text) if outlet_max_elem is not None and outlet_max_elem.text is not None and outlet_max_elem.text.strip() else 0.0
        delta_t = float(temps.find('delta_t').text)
        
        # Wärmepumpe
        hp = elem.find('heat_pump')
        heating_power_b0_w35 = float(hp.find('heating_power_b0_w35').text)
        cop_b0_w35 = float(hp.find('cop_b0_w35').text)
        annual_cop = float(hp.find('annual_cop').text)
        heating_power_b0_w45_elem = hp.find('heating_power_b0_w45')
        heating_power_b0_w45 = float(heating_power_b0_w45_elem.text) if heating_power_b0_w45_elem is not None and heating_power_b0_w45_elem.text is not None and heating_power_b0_w45_elem.text.strip() else None
        cop_b0_w45_elem = hp.find('cop_b0_w45')
        cop_b0_w45 = float(cop_b0_w45_elem.text) if cop_b0_w45_elem is not None and cop_b0_w45_elem.text is not None and cop_b0_w45_elem.text.strip() else None
        
        # Kühlung (optional)
        cooling = elem.find('cooling')
        specific_injection_power = float(cooling.find('specific_injection_power').text) if cooling is not None else 0.0
        annual_cooling_energy = float(cooling.find('annual_cooling_energy').text) if cooling is not None else 0.0
        operating_hours_cooling = float(cooling.find('operating_hours_cooling').text) if cooling is not None else 0.0
        winter_min_temp_elem = cooling.find('winter_min_temp') if cooling is not None else None
        winter_min_temp = float(winter_min_temp_elem.text) if winter_min_temp_elem is not None and winter_min_temp_elem.text is not None and winter_min_temp_elem.text.strip() else None
        summer_max_temp_elem = cooling.find('summer_max_temp') if cooling is not None else None
        summer_max_temp = float(summer_max_temp_elem.text) if summer_max_temp_elem is not None and summer_max_temp_elem.text is not None and summer_max_temp_elem.text.strip() else None
        delta_t_cooling = float(cooling.find('delta_t_cooling').text) if cooling is not None else 0.0
        eer_passive_elem = cooling.find('eer_passive') if cooling is not None else None
        eer_passive = eer_passive_elem.text if eer_passive_elem is not None and eer_passive_elem.text is not None and eer_passive_elem.text.strip() else None
        
        # Notizen
        notes_elem = elem.find('notes')
        notes = []
        if notes_elem is not None:
            notes = [note.text for note in notes_elem.findall('note')]
        
        return ExampleInstallation(
            id=id,
            name=name,
            building_type=building_type,
            heating_system=heating_system,
            num_boreholes=num_boreholes,
            depth_m=depth_m,
            diameter_mm=diameter_mm,
            spacing_m=spacing_m,
            total_length_m=total_length_m,
            pipe_type=pipe_type,
            pipe_outer_diameter_mm=pipe_outer_diameter_mm,
            pipe_wall_thickness_mm=pipe_wall_thickness_mm,
            grout_thermal_conductivity=grout_thermal_conductivity,
            specific_extraction_power=specific_extraction_power,
            max_extraction_power=max_extraction_power,
            annual_energy=annual_energy,
            operating_hours=operating_hours,
            building_heat_load=building_heat_load,
            fluid_type=fluid_type,
            fluid_concentration_percent=fluid_concentration_percent,
            flow_rate_m3h=flow_rate_m3h,
            inlet_min_temp=inlet_min_temp,
            outlet_max_temp=outlet_max_temp,
            delta_t=delta_t,
            heating_power_b0_w35=heating_power_b0_w35,
            cop_b0_w35=cop_b0_w35,
            annual_cop=annual_cop,
            heating_power_b0_w45=heating_power_b0_w45,
            cop_b0_w45=cop_b0_w45,
            specific_injection_power=specific_injection_power,
            annual_cooling_energy=annual_cooling_energy,
            operating_hours_cooling=operating_hours_cooling,
            winter_min_temp=winter_min_temp,
            summer_max_temp=summer_max_temp,
            delta_t_cooling=delta_t_cooling,
            eer_passive=eer_passive,
            notes=notes
        )
    
    def get_installation(self, id: int) -> Optional[ExampleInstallation]:
        """Gibt eine Installation nach ID zurück."""
        return self.installations.get(id)
    
    def get_all_installations(self) -> List[ExampleInstallation]:
        """Gibt alle Installationen zurück."""
        return list(self.installations.values())
    
    def get_installations_by_category(self, category: str) -> List[ExampleInstallation]:
        """Gibt alle Installationen einer Kategorie zurück."""
        return self.categories.get(category, [])
    
    def get_all_categories(self) -> List[str]:
        """Gibt alle Kategorien zurück."""
        return list(self.categories.keys())


if __name__ == "__main__":
    # Test der Beispielanlagen-Datenbank
    db = ExampleInstallationsDatabase()
    
    print("="*70)
    print("BEISPIELANLAGEN-DATENBANK TEST")
    print("="*70)
    print(f"Installationen geladen: {len(db.installations)}")
    print(f"Kategorien: {', '.join(db.get_all_categories())}")
    print()
    
    # Alle Installationen anzeigen
    for category in db.get_all_categories():
        installations = db.get_installations_by_category(category)
        print(f"\n{category}: {len(installations)} Installationen")
        for inst in installations:
            print(f"  [{inst.id}] {inst.name} ({inst.building_type})")
            print(f"      {inst.num_boreholes} Sonden, {inst.depth_m}m tief")
            print(f"      {inst.specific_extraction_power} W/m, {inst.max_extraction_power} kW max")
    
    # Details für Installation 1
    print("\n" + "="*70)
    print("DETAILS: Installation 1")
    print("="*70)
    inst1 = db.get_installation(1)
    if inst1:
        print(f"Name: {inst1.name}")
        print(f"Gebäudetyp: {inst1.building_type}")
        print(f"Heizsystem: {inst1.heating_system}")
        print(f"Sonden: {inst1.num_boreholes} × {inst1.depth_m}m")
        print(f"Rohr: {inst1.pipe_type}, {inst1.pipe_outer_diameter_mm}mm")
        print(f"Entzugsleistung: {inst1.specific_extraction_power} W/m")
        print(f"Jahresenergie: {inst1.annual_energy} kWh/a")
        print(f"Wärmepumpe: {inst1.heating_power_b0_w35} kW, COP {inst1.cop_b0_w35}")
    
    print("\n" + "="*70)
