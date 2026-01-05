"""Datenbank für Umwälzpumpen."""

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import List, Dict, Optional
import os


@dataclass
class PumpSpecifications:
    """Technische Spezifikationen einer Pumpe."""
    max_flow_m3h: float
    max_head_m: float
    power_min_w: float
    power_max_w: float
    power_avg_w: float
    connection_size: str
    voltage: str


@dataclass
class Pump:
    """Umwälzpumpe mit allen Eigenschaften."""
    manufacturer: str
    model: str
    series: str
    efficiency_class: str
    pump_type: str  # 'regulated' oder 'constant'
    specs: PumpSpecifications
    price_eur: float
    price_range: str
    features: List[str]
    suitable_for: Dict[str, any]
    note: Optional[str] = None
    
    def get_full_name(self) -> str:
        """Gibt den vollständigen Namen zurück."""
        return f"{self.manufacturer} {self.model}"
    
    def is_suitable_for_power(self, power_kw: float) -> bool:
        """Prüft ob Pumpe für gegebene Leistung geeignet ist."""
        min_kw = self.suitable_for.get('min_power_kw', 0)
        max_kw = self.suitable_for.get('max_power_kw', 999)
        return min_kw <= power_kw <= max_kw
    
    def is_suitable_for_flow_and_head(self, flow_m3h: float, head_m: float, 
                                      safety_factor: float = 1.1) -> bool:
        """Prüft ob Pumpe für gegebenen Volumenstrom und Förderhöhe geeignet ist."""
        return (flow_m3h * safety_factor <= self.specs.max_flow_m3h and 
                head_m * safety_factor <= self.specs.max_head_m)
    
    def calculate_suitability_score(self, flow_m3h: float, head_m: float,
                                    power_kw: float) -> float:
        """
        Berechnet Eignung-Score (0-100).
        
        100 = Perfekt dimensioniert
        > 80 = Gut geeignet
        > 60 = Akzeptabel
        < 60 = Über-/Unterdimensioniert
        """
        # Hydraulische Eignung
        flow_utilization = flow_m3h / self.specs.max_flow_m3h if self.specs.max_flow_m3h > 0 else 0
        head_utilization = head_m / self.specs.max_head_m if self.specs.max_head_m > 0 else 0
        
        # Ideal: 60-80% Auslastung
        flow_score = 100 if 0.6 <= flow_utilization <= 0.8 else \
                     max(0, 100 - abs(flow_utilization - 0.7) * 200)
        head_score = 100 if 0.6 <= head_utilization <= 0.8 else \
                     max(0, 100 - abs(head_utilization - 0.7) * 200)
        
        # Leistungsbereich
        power_suitable = self.is_suitable_for_power(power_kw)
        power_score = 100 if power_suitable else 50
        
        # Effizienz-Bonus
        efficiency_bonus = 10 if self.efficiency_class == 'A' else 0
        
        # Gesamt-Score
        total_score = (flow_score * 0.4 + head_score * 0.4 + power_score * 0.2 + 
                      efficiency_bonus)
        
        return min(100, total_score)


class PumpDatabase:
    """Datenbank für Umwälzpumpen."""
    
    def __init__(self, xml_file: str = None):
        """Initialisiert Datenbank aus XML-Datei."""
        if xml_file is None:
            # Standard: XML-Datei im gleichen Verzeichnis
            current_dir = os.path.dirname(__file__)
            xml_file = os.path.join(current_dir, 'pump_database.xml')
        
        self.xml_file = xml_file
        self.pumps: List[Pump] = []
        self.categories: Dict[str, List[Pump]] = {}
        self._load_from_xml()
    
    def _load_from_xml(self):
        """Lädt Pumpen aus XML-Datei."""
        try:
            tree = ET.parse(self.xml_file)
            root = tree.getroot()
            
            for category in root.findall('pump_category'):
                category_name = category.get('name')
                self.categories[category_name] = []
                
                for pump_elem in category.findall('pump'):
                    pump = self._parse_pump(pump_elem)
                    self.pumps.append(pump)
                    self.categories[category_name].append(pump)
        
        except Exception as e:
            print(f"Fehler beim Laden der Pumpen-Datenbank: {e}")
            # Fallback: Leere Datenbank
            self.pumps = []
            self.categories = {}
    
    def _parse_pump(self, elem: ET.Element) -> Pump:
        """Parst eine Pumpe aus XML-Element."""
        # Basis-Infos
        manufacturer = elem.find('manufacturer').text
        model = elem.find('model').text
        series = elem.find('series').text
        efficiency_class = elem.find('efficiency_class').text
        pump_type = elem.find('type').text
        
        # Spezifikationen
        specs_elem = elem.find('specifications')
        specs = PumpSpecifications(
            max_flow_m3h=float(specs_elem.find('max_flow_m3h').text),
            max_head_m=float(specs_elem.find('max_head_m').text),
            power_min_w=float(specs_elem.find('power_min_w').text),
            power_max_w=float(specs_elem.find('power_max_w').text),
            power_avg_w=float(specs_elem.find('power_avg_w').text),
            connection_size=specs_elem.find('connection_size').text,
            voltage=specs_elem.find('voltage').text
        )
        
        # Preis
        pricing_elem = elem.find('pricing')
        price_eur = float(pricing_elem.find('price_eur').text)
        price_range = pricing_elem.find('price_range').text
        
        # Features
        features = [f.text for f in elem.find('features').findall('feature')]
        
        # Geeignet für
        suitable_elem = elem.find('suitable_for')
        suitable_for = {
            'application': suitable_elem.find('application').text,
            'min_power_kw': float(suitable_elem.find('min_power_kw').text),
            'max_power_kw': float(suitable_elem.find('max_power_kw').text)
        }
        
        # Note (optional)
        note_elem = elem.find('note')
        note = note_elem.text if note_elem is not None else None
        
        return Pump(
            manufacturer=manufacturer,
            model=model,
            series=series,
            efficiency_class=efficiency_class,
            pump_type=pump_type,
            specs=specs,
            price_eur=price_eur,
            price_range=price_range,
            features=features,
            suitable_for=suitable_for,
            note=note
        )
    
    def find_suitable_pumps(self, 
                           flow_m3h: float, 
                           head_m: float,
                           power_kw: float = None,
                           pump_type: str = None,
                           max_results: int = 5) -> List[tuple]:
        """
        Findet passende Pumpen mit Ranking.
        
        Args:
            flow_m3h: Benötigter Volumenstrom in m³/h
            head_m: Benötigte Förderhöhe in m
            power_kw: Wärmepumpen-Leistung in kW (optional)
            pump_type: 'regulated' oder 'constant' (optional)
            max_results: Maximale Anzahl Ergebnisse
            
        Returns:
            Liste von Tupeln: (score, pump)
        """
        suitable = []
        
        for pump in self.pumps:
            # Filter nach Typ
            if pump_type and pump.pump_type != pump_type:
                continue
            
            # Muss grundsätzlich Volumenstrom und Förderhöhe schaffen
            if not pump.is_suitable_for_flow_and_head(flow_m3h, head_m):
                continue
            
            # Berechne Score
            score = pump.calculate_suitability_score(
                flow_m3h, head_m, power_kw if power_kw else 10
            )
            
            suitable.append((score, pump))
        
        # Sortiere nach Score (höchster zuerst)
        suitable.sort(reverse=True, key=lambda x: x[0])
        
        return suitable[:max_results]
    
    def get_pumps_by_manufacturer(self, manufacturer: str) -> List[Pump]:
        """Gibt alle Pumpen eines Herstellers zurück."""
        return [p for p in self.pumps if p.manufacturer.lower() == manufacturer.lower()]
    
    def get_pumps_by_category(self, category: str) -> List[Pump]:
        """Gibt alle Pumpen einer Kategorie zurück."""
        return self.categories.get(category, [])
    
    def get_all_manufacturers(self) -> List[str]:
        """Gibt alle Hersteller zurück."""
        return sorted(set(p.manufacturer for p in self.pumps))
    
    def get_all_categories(self) -> List[str]:
        """Gibt alle Kategorien zurück."""
        return list(self.categories.keys())


if __name__ == "__main__":
    # Test
    db = PumpDatabase()
    
    print(f"Pumpen-Datenbank geladen: {len(db.pumps)} Pumpen")
    print(f"Kategorien: {', '.join(db.get_all_categories())}")
    print(f"Hersteller: {', '.join(db.get_all_manufacturers())}")
    print()
    
    # Test: Suche passende Pumpe für 11 kW Anlage
    print("="*70)
    print("Test: Pumpensuche für 11 kW Anlage")
    print("Volumenstrom: 3.2 m³/h, Förderhöhe: 5.5 m")
    print("="*70)
    
    results = db.find_suitable_pumps(flow_m3h=3.2, head_m=5.5, power_kw=11)
    
    for i, (score, pump) in enumerate(results, 1):
        print(f"\n{i}. {pump.get_full_name()} (Score: {score:.1f}/100)")
        print(f"   Typ: {pump.pump_type} | Effizienz: {pump.efficiency_class}")
        print(f"   Max. Flow: {pump.specs.max_flow_m3h} m³/h | Max. Head: {pump.specs.max_head_m} m")
        print(f"   Leistung: {pump.specs.power_avg_w} W (avg)")
        print(f"   Preis: {pump.price_eur} EUR")
        if score > 80:
            print(f"   ✅ Sehr gut geeignet")
        elif score > 60:
            print(f"   ✓ Gut geeignet")
        else:
            print(f"   ⚠️ Akzeptabel")

