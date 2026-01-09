"""
Lädt Beispielanlagen aus XML-Datei für Tests und Validierungen.
"""
import os
import sys
from typing import Dict, Any, Optional, List

# Import example_installations_db - funktioniert sowohl als Modul als auch direkt
try:
    from .example_installations_db import ExampleInstallationsDatabase, ExampleInstallation
except ImportError:
    # Fallback für direkten Aufruf
    script_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, script_dir)
    from example_installations_db import ExampleInstallationsDatabase, ExampleInstallation


class BeispielanlagenLoader:
    """Lädt und verwaltet Beispielanlagen aus XML."""
    
    def __init__(self, xml_path: Optional[str] = None):
        """
        Initialisiert den Loader.
        
        Args:
            xml_path: Pfad zur XML-Datei. Wenn None, wird der Standardpfad verwendet.
        """
        if xml_path is None:
            # Standardpfad: relativ zum Skript
            script_dir = os.path.dirname(os.path.abspath(__file__))
            xml_path = os.path.join(script_dir, "beispielanlagen.xml")
        
        self.xml_path = xml_path
        self.db = ExampleInstallationsDatabase(xml_path)
        self._mapping_cache = {}  # Cache für CSV-kompatible Dictionaries
    
    def _installation_to_dict(self, inst: ExampleInstallation) -> Dict[str, Any]:
        """
        Konvertiert eine Installation in ein CSV-kompatibles Dictionary.
        Dies ermöglicht Rückwärtskompatibilität mit dem alten CSV-Format.
        """
        if inst.id in self._mapping_cache:
            return self._mapping_cache[inst.id]
        
        # Mapping von XML-Feldern zu CSV-Spaltennamen
        d = {
            'Beispielanlage': inst.id,
            'Gebaeudetyp': inst.building_type,
            'Heizsystem': inst.heating_system,
            'Anzahl_Sonden': inst.num_boreholes,
            'Sondentiefe_m': inst.depth_m,
            'Bohrdurchmesser_mm': inst.diameter_mm,
            'Sondenabstand_m': inst.spacing_m if inst.spacing_m is not None else '-',
            'Gesamtsondenlaenge_m': inst.total_length_m,
            'Rohrtyp': inst.pipe_type,
            'Rohr_aussen_mm': inst.pipe_outer_diameter_mm,
            'Rohr_wand_mm': inst.pipe_wall_thickness_mm if inst.pipe_wall_thickness_mm > 0 else '-',
            'Verpressmaterial_lambda_W_mK': inst.grout_thermal_conductivity,
            'Entzugsleistung_spezifisch_W_m': inst.specific_extraction_power,
            'Maximale_Entzugsleistung_kW': inst.max_extraction_power,
            'Jahresenergie_Erdreich_kWh_a': inst.annual_energy,
            'Betriebsstunden_WP_h_a': inst.operating_hours if inst.operating_hours > 0 else '-',
            'Heizlast_Gebaeude_kW': inst.building_heat_load if inst.building_heat_load > 0 else '-',
            'Solemedium': inst.fluid_type if inst.fluid_type else '-',
            'Glykol_Prozent': inst.fluid_concentration_percent if inst.fluid_concentration_percent > 0 else '-',
            'Volumenstrom_m3_h': inst.flow_rate_m3h,
            'Eintritt_Sole_WP_min_C': inst.inlet_min_temp,
            'Austritt_Sole_WP_max_C': inst.outlet_max_temp if inst.outlet_max_temp != 0 else '-',
            'DeltaT_Sole_K': inst.delta_t,
            'Heizleistung_B0_W35_kW': inst.heating_power_b0_w35 if inst.heating_power_b0_w35 > 0 else '-',
            'COP_B0_W35': inst.cop_b0_w35 if inst.cop_b0_w35 > 0 else '-',
            'JAZ': inst.annual_cop if inst.annual_cop > 0 else '-',
            'Kuehl_Eintragsleistung_W_m': inst.specific_injection_power if inst.specific_injection_power > 0 else '-',
            'Jahreskuehlarbeit_kWh_a': inst.annual_cooling_energy if inst.annual_cooling_energy > 0 else '-',
            'Betriebsstunden_Heizen_h': inst.operating_hours if inst.operating_hours > 0 else '-',
            'Betriebsstunden_Kuehlen_h': inst.operating_hours_cooling if inst.operating_hours_cooling > 0 else '-',
            'Soletemperatur_Winter_min_C': inst.winter_min_temp if inst.winter_min_temp is not None else '-',
            'Soletemperatur_Sommer_max_C': inst.summer_max_temp if inst.summer_max_temp is not None else '-',
            'DeltaT_Kuehlen_K': inst.delta_t_cooling if inst.delta_t_cooling > 0 else '-',
            'Heizleistung_B0_W45_kW': inst.heating_power_b0_w45 if inst.heating_power_b0_w45 is not None else '-',
            'COP_B0_W45': inst.cop_b0_w45 if inst.cop_b0_w45 is not None else '-',
            'EER_passive_Kuehlung': inst.eer_passive if inst.eer_passive else '-'
        }
        
        self._mapping_cache[inst.id] = d
        return d
    
    def get_anlage(self, nummer: int) -> Dict[str, Any]:
        """
        Holt eine Beispielanlage nach Nummer.
        
        Args:
            nummer: Nummer der Beispielanlage (1, 2 oder 3)
        
        Returns:
            Dictionary mit allen Parametern der Anlage (CSV-kompatibles Format)
        """
        installation = self.db.get_installation(nummer)
        if installation is None:
            raise ValueError(f"Anlage {nummer} nicht gefunden.")
        
        return self._installation_to_dict(installation)
    
    def get_all_anlagen(self) -> List[Dict[str, Any]]:
        """
        Gibt alle Beispielanlagen zurück.
        
        Returns:
            Liste von Dictionaries (CSV-kompatibles Format)
        """
        installations = self.db.get_all_installations()
        return [self._installation_to_dict(inst) for inst in installations]
    
    def get_parameter(self, anlage_nummer: int, parameter: str) -> Any:
        """
        Holt einen spezifischen Parameter einer Anlage.
        
        Args:
            anlage_nummer: Nummer der Anlage (1, 2 oder 3)
            parameter: Name des Parameters (CSV-Spaltenname)
        
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
