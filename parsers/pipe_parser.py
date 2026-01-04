"""Parser für pipe.txt Dateien mit Rohrdaten."""

import re
from dataclasses import dataclass
from typing import List


@dataclass
class PipeData:
    """Repräsentiert ein Rohr mit seinen Eigenschaften."""
    name: str
    diameter_mm: float  # Außendurchmesser in mm
    thickness_mm: float  # Wandstärke in mm
    thermal_conductivity: float  # Wärmeleitfähigkeit in W/m·K
    
    @property
    def inner_diameter_mm(self) -> float:
        """Berechnet den Innendurchmesser."""
        return self.diameter_mm - 2 * self.thickness_mm
    
    @property
    def diameter_m(self) -> float:
        """Außendurchmesser in Metern."""
        return self.diameter_mm / 1000.0
    
    @property
    def thickness_m(self) -> float:
        """Wandstärke in Metern."""
        return self.thickness_mm / 1000.0


class PipeParser:
    """Parser für pipe.txt Dateien."""
    
    @staticmethod
    def parse_file(filepath: str) -> List[PipeData]:
        """
        Liest eine pipe.txt Datei ein und gibt eine Liste von PipeData zurück.
        
        Format pro Zeile (alternierend):
        1. Zeile: Name des Rohrs
        2. Zeile: d=XX mm t=YY mm l=ZZ  XXXX YYYY ZZZZ
        
        wobei:
        - d = Außendurchmesser in mm
        - t = Wandstärke in mm
        - l = Wärmeleitfähigkeit in W/m·K
        """
        pipes = []
        
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Überspringe leere Zeilen
            if not line:
                i += 1
                continue
            
            # Erste Zeile ist der Name
            name = line
            i += 1
            
            # Zweite Zeile enthält die Daten
            if i < len(lines):
                data_line = lines[i].strip()
                
                # Parse mit Regex
                # Format: d=63 mm t=11.8 mm l=4.70
                match = re.search(r'd=([0-9.]+)\s+mm\s+t=([0-9.]+)\s+mm\s+l=([0-9.]+)', data_line)
                
                if match:
                    diameter = float(match.group(1))
                    thickness = float(match.group(2))
                    thermal_cond = float(match.group(3))
                    
                    pipe = PipeData(
                        name=name,
                        diameter_mm=diameter,
                        thickness_mm=thickness,
                        thermal_conductivity=thermal_cond
                    )
                    pipes.append(pipe)
                
                i += 1
            else:
                break
        
        return pipes
    
    @staticmethod
    def get_pipe_by_name(pipes: List[PipeData], name: str) -> PipeData:
        """Sucht ein Rohr nach Namen."""
        for pipe in pipes:
            if name in pipe.name or pipe.name in name:
                return pipe
        raise ValueError(f"Rohr '{name}' nicht gefunden")
    
    @staticmethod
    def get_pipes_by_material(pipes: List[PipeData], material: str) -> List[PipeData]:
        """Filtert Rohre nach Material (z.B. 'PE', 'PP', 'PVC')."""
        return [pipe for pipe in pipes if material.upper() in pipe.name.upper()]


if __name__ == "__main__":
    # Test
    parser = PipeParser()
    pipes = parser.parse_file("../pipe.txt")
    
    print(f"Anzahl geladener Rohre: {len(pipes)}")
    print("\nErste 5 Rohre:")
    for pipe in pipes[:5]:
        print(f"  {pipe.name}")
        print(f"    Durchmesser: {pipe.diameter_mm} mm (innen: {pipe.inner_diameter_mm:.2f} mm)")
        print(f"    Wandstärke: {pipe.thickness_mm} mm")
        print(f"    Wärmeleitfähigkeit: {pipe.thermal_conductivity} W/m·K")





