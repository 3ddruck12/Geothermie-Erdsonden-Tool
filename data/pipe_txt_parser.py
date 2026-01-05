"""Parser für legacy pipe.txt Format."""

from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class PipeTxtEntry:
    """Ein Eintrag aus pipe.txt."""
    name: str
    outer_diameter: float  # m
    wall_thickness: float  # m
    thermal_conductivity: float  # W/m·K
    
    def get_inner_diameter(self) -> float:
        """Berechnet Innendurchmesser."""
        return self.outer_diameter - 2 * self.wall_thickness


class PipeTxtParser:
    """Parser für pipe.txt Dateien."""
    
    @staticmethod
    def parse_file(filepath: str) -> List[PipeTxtEntry]:
        """
        Parst eine pipe.txt Datei.
        
        Format:
        Name
            d=XX mm t=YY mm l=ZZ       0.XXXX 0.YYYY   ZZ.ZZ
        
        Args:
            filepath: Pfad zur pipe.txt Datei
        
        Returns:
            Liste von PipeTxtEntry
        """
        pipes = []
        current_name = None
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    
                    # Überspringe leere Zeilen und "ss"
                    if not line or line == 'ss':
                        continue
                    
                    # Prüfe ob Zeile mit Einrückung beginnt (= Daten)
                    # Datenzeilen beginnen mit "d=" nach Whitespace
                    if 'd=' in line and current_name:
                        # Parse Datenzeile
                        # Extrahiere die drei Zahlenwerte am Ende der Zeile
                        parts = line.split()
                        if len(parts) >= 3:
                            try:
                                # Die letzten 3 Werte sind: outer_d, wall_t, lambda
                                # Suche von hinten
                                lambda_val = float(parts[-1])  # W/m·K
                                wall_t = float(parts[-2])      # m
                                outer_d = float(parts[-3])     # m
                                
                                pipe = PipeTxtEntry(
                                    name=current_name,
                                    outer_diameter=outer_d,
                                    wall_thickness=wall_t,
                                    thermal_conductivity=lambda_val
                                )
                                pipes.append(pipe)
                            except (ValueError, IndexError):
                                pass  # Überspringe fehlerhafte Zeilen
                    elif not line.startswith(' ') and not line.startswith('\t'):
                        # Neue Rohrbeschreibung (keine Einrückung)
                        current_name = line
        
        except FileNotFoundError:
            pass  # Datei nicht gefunden
        except Exception as e:
            print(f"⚠️ Fehler beim Parsen von {filepath}: {e}")
        
        return pipes
    
    @staticmethod
    def export_to_txt(pipes: List[PipeTxtEntry], filepath: str):
        """
        Exportiert Rohre ins pipe.txt Format.
        
        Args:
            pipes: Liste von PipeTxtEntry
            filepath: Ziel-Dateipfad
        """
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                for pipe in pipes:
                    # Name
                    f.write(f"{pipe.name}\n")
                    
                    # Daten (mit Formatierung wie im Original)
                    f.write(f"    d={pipe.outer_diameter*1000:.1f} mm "
                           f"t={pipe.wall_thickness*1000:.1f} mm "
                           f"l={pipe.thermal_conductivity:.2f}       "
                           f"{pipe.outer_diameter:.4f} {pipe.wall_thickness:.4f}   "
                           f"{pipe.thermal_conductivity:.2f}\n")
                
                # Abschluss
                f.write("ss    \n")
        
        except Exception as e:
            print(f"⚠️ Fehler beim Exportieren nach {filepath}: {e}")


if __name__ == "__main__":
    # Test
    import sys
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')
    
    # Parse Material/pipe.txt
    parser = PipeTxtParser()
    pipes = parser.parse_file("Material/pipe.txt")
    
    print("="*80)
    print("PIPE.TXT PARSER TEST")
    print("="*80)
    print(f"Rohre geladen: {len(pipes)}")
    print()
    
    # Zeige erste 10
    print("ERSTE 10 ROHRE:")
    print("="*80)
    for i, pipe in enumerate(pipes[:10], 1):
        inner_d = pipe.get_inner_diameter()
        print(f"{i}. {pipe.name}")
        print(f"   Ø außen/innen: {pipe.outer_diameter*1000:.1f}/{inner_d*1000:.1f} mm")
        print(f"   Wandstärke: {pipe.wall_thickness*1000:.1f} mm")
        print(f"   λ = {pipe.thermal_conductivity} W/m·K")
        print()
    
    # Test Export
    print("="*80)
    print("EXPORT TEST")
    print("="*80)
    test_pipes = pipes[:3]
    parser.export_to_txt(test_pipes, "/tmp/test_pipe.txt")
    print("✓ Export nach /tmp/test_pipe.txt erfolgreich")
    
    # Re-import Test
    reimported = parser.parse_file("/tmp/test_pipe.txt")
    print(f"✓ Re-Import erfolgreich: {len(reimported)} Rohre")
    
    print("\n" + "="*80)

