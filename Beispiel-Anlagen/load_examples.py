"""
Lädt Beispielanlagen aus CSV-Datei für Tests und Validierungen.
"""
import os
import csv
from typing import Dict, Any, Optional, List

# Versuche pandas zu importieren (optional)
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False
    pd = None


class BeispielanlagenLoader:
    """Lädt und verwaltet Beispielanlagen aus CSV."""
    
    def __init__(self, csv_path: Optional[str] = None):
        """
        Initialisiert den Loader.
        
        Args:
            csv_path: Pfad zur CSV-Datei. Wenn None, wird der Standardpfad verwendet.
        """
        if csv_path is None:
            # Standardpfad: relativ zum Skript
            script_dir = os.path.dirname(os.path.abspath(__file__))
            csv_path = os.path.join(script_dir, "beispielanlagen.csv")
        
        self.csv_path = csv_path
        self.df = None
        self._load()
    
    def _load(self):
        """Lädt die CSV-Datei."""
        if not os.path.exists(self.csv_path):
            raise FileNotFoundError(f"CSV-Datei nicht gefunden: {self.csv_path}")
        
        if HAS_PANDAS:
            self.df = pd.read_csv(self.csv_path)
        else:
            # Fallback: CSV mit Standard-Modul laden
            with open(self.csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                self.df = list(reader)
    
    def get_anlage(self, nummer: int) -> Dict[str, Any]:
        """
        Holt eine Beispielanlage nach Nummer.
        
        Args:
            nummer: Nummer der Beispielanlage (1, 2 oder 3)
        
        Returns:
            Dictionary mit allen Parametern der Anlage
        """
        if nummer not in [1, 2, 3]:
            raise ValueError(f"Ungültige Anlagennummer: {nummer}. Muss 1, 2 oder 3 sein.")
        
        if HAS_PANDAS:
            row = self.df[self.df['Beispielanlage'] == nummer].iloc[0]
            return row.to_dict()
        else:
            # Fallback: Suche in Liste
            for row in self.df:
                if int(row['Beispielanlage']) == nummer:
                    return row
            raise ValueError(f"Anlage {nummer} nicht gefunden.")
    
    def get_all_anlagen(self):
        """
        Gibt alle Beispielanlagen zurück.
        
        Returns:
            DataFrame (mit pandas) oder Liste von Dictionaries (ohne pandas)
        """
        if HAS_PANDAS:
            return self.df.copy()
        else:
            return self.df.copy()
    
    def get_parameter(self, anlage_nummer: int, parameter: str) -> Any:
        """
        Holt einen spezifischen Parameter einer Anlage.
        
        Args:
            anlage_nummer: Nummer der Anlage (1, 2 oder 3)
            parameter: Name des Parameters (Spaltenname)
        
        Returns:
            Wert des Parameters
        """
        anlage = self.get_anlage(anlage_nummer)
        if parameter not in anlage:
            raise KeyError(f"Parameter '{parameter}' nicht gefunden. Verfügbare Parameter: {list(anlage.keys())}")
        
        value = anlage[parameter]
        
        # Konvertiere leere Strings zu None
        if value is None or (isinstance(value, str) and value.strip() == ''):
            return None
        
        # Konvertiere numerische Strings zu float/int
        if isinstance(value, str):
            # Entferne Leerzeichen
            value = value.strip()
            if value == '' or value == '-':
                return None
            
            # Prüfe ob numerisch
            cleaned = value.replace('.', '').replace('-', '').replace('+', '')
            if cleaned.isdigit() or (cleaned.replace('e', '').replace('E', '').isdigit()):
                try:
                    if '.' in value or 'e' in value.lower():
                        return float(value)
                    else:
                        return int(value)
                except ValueError:
                    pass
        
        return value
    
    def print_anlage(self, nummer: int):
        """
        Druckt eine Anlage formatiert aus.
        
        Args:
            nummer: Nummer der Anlage (1, 2 oder 3)
        """
        anlage = self.get_anlage(nummer)
        
        print(f"\n{'='*60}")
        print(f"Beispielanlage {nummer}: {anlage['Gebaeudetyp']}")
        print(f"{'='*60}\n")
        
        print(f"Gebäudetyp: {anlage['Gebaeudetyp']}")
        print(f"Heizsystem: {anlage['Heizsystem']}\n")
        
        print("Erdsondenfeld:")
        print(f"  Anzahl Sonden: {anlage['Anzahl_Sonden']}")
        print(f"  Sondentiefe: {anlage['Sondentiefe_m']} m")
        sondenabstand = anlage.get('Sondenabstand_m', '-')
        if sondenabstand and sondenabstand != '-' and sondenabstand != '':
            print(f"  Sondenabstand: {sondenabstand} m")
        print(f"  Gesamtsondenlänge: {anlage['Gesamtsondenlaenge_m']} m")
        print(f"  Rohr: {anlage['Rohrtyp']}")
        rohr_aussen = anlage.get('Rohr_aussen_mm', '')
        if rohr_aussen and rohr_aussen != '' and rohr_aussen != '-':
            print(f"    Außendurchmesser: {rohr_aussen} mm")
            rohr_wand = anlage.get('Rohr_wand_mm', '')
            if rohr_wand and rohr_wand != '' and rohr_wand != '-':
                print(f"    Wandstärke: {rohr_wand} mm")
        print(f"  Verpressmaterial: λ = {anlage['Verpressmaterial_lambda_W_mK']} W/mK\n")
        
        print("Thermische Kenndaten:")
        def print_if_exists(key, label, format_str="{}"):
            value = anlage.get(key, '')
            if value and value != '' and value != '-':
                try:
                    if format_str == "{:.0f}":
                        print(f"  {label}: {float(value):.0f}")
                    else:
                        print(f"  {label}: {value}")
                except (ValueError, TypeError):
                    print(f"  {label}: {value}")
        
        print_if_exists('Entzugsleistung_spezifisch_W_m', 'Entzugsleistung spezifisch', '{} W/m')
        print_if_exists('Maximale_Entzugsleistung_kW', 'Maximale Entzugsleistung', '{} kW')
        print_if_exists('Jahresenergie_Erdreich_kWh_a', 'Jahresenergie Erdreich', '{:.0f} kWh/a')
        print_if_exists('Betriebsstunden_WP_h_a', 'Betriebsstunden WP', '{:.0f} h/a')
        print_if_exists('Heizlast_Gebaeude_kW', 'Heizlast Gebäude', '{} kW')
        print_if_exists('Kuehl_Eintragsleistung_W_m', 'Kühl-Eintragsleistung', '{} W/m')
        print_if_exists('Jahreskuehlarbeit_kWh_a', 'Jahreskühlarbeit', '{:.0f} kWh/a')
        print()
        
        print("Solebetrieb:")
        print_if_exists('Solemedium', 'Solemedium')
        print_if_exists('Glykol_Prozent', 'Glykol', '{}%')
        print_if_exists('Volumenstrom_m3_h', 'Volumenstrom', '{} m³/h')
        print_if_exists('Eintritt_Sole_WP_min_C', 'Eintritt Sole WP (min)', '{} °C')
        print_if_exists('Austritt_Sole_WP_max_C', 'Austritt Sole WP (max)', '{} °C')
        print_if_exists('DeltaT_Sole_K', 'ΔT Sole', '{} K')
        print_if_exists('Soletemperatur_Winter_min_C', 'Soletemperatur Winter min', '{} °C')
        print_if_exists('Soletemperatur_Sommer_max_C', 'Soletemperatur Sommer max', '{} °C')
        print_if_exists('DeltaT_Kuehlen_K', 'ΔT Kühlen', '{} K')
        print()
        
        print("Wärmepumpe:")
        print_if_exists('Heizleistung_B0_W35_kW', 'Heizleistung B0/W35', '{} kW')
        print_if_exists('COP_B0_W35', 'COP (B0/W35)', '{}')
        print_if_exists('JAZ', 'Jahresarbeitszahl (JAZ)', '{}')
        print_if_exists('Heizleistung_B0_W45_kW', 'Heizleistung B0/W45', '{} kW')
        print_if_exists('COP_B0_W45', 'COP (B0/W45)', '{}')
        eer = anlage.get('EER_passive_Kuehlung', '')
        if eer and eer != '-' and eer != '':
            print(f"  EER passive Kühlung: {eer}")
        print()


def main():
    """Beispiel-Verwendung."""
    loader = BeispielanlagenLoader()
    
    # Zeige alle Anlagen
    print("Verfügbare Beispielanlagen:")
    all_anlagen = loader.get_all_anlagen()
    if HAS_PANDAS:
        print(all_anlagen[['Beispielanlage', 'Gebaeudetyp', 'Anzahl_Sonden', 'Sondentiefe_m']])
    else:
        for anlage in all_anlagen:
            print(f"  {anlage['Beispielanlage']}: {anlage['Gebaeudetyp']} - {anlage['Anzahl_Sonden']} Sonden, {anlage['Sondentiefe_m']} m")
    
    # Zeige Details für Anlage 1
    loader.print_anlage(1)
    
    # Beispiel: Parameter abrufen
    print("\nBeispiel: Parameter abrufen")
    print(f"Anzahl Sonden (Anlage 1): {loader.get_parameter(1, 'Anzahl_Sonden')}")
    print(f"Sondentiefe (Anlage 2): {loader.get_parameter(2, 'Sondentiefe_m')} m")
    print(f"Volumenstrom (Anlage 3): {loader.get_parameter(3, 'Volumenstrom_m3_h')} m³/h")


if __name__ == "__main__":
    main()

