"""
Erstellt .get Dateien aus den Beispielanlagen XML-Datei.
"""
import os
import sys
import importlib.util
from datetime import datetime

# Füge den Parent-Ordner zum Pfad hinzu, um utils zu importieren
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.get_file_handler import GETFileHandler

# Import load_examples - relativ zum aktuellen Skript
load_examples_path = os.path.join(os.path.dirname(__file__), 'load_examples.py')
spec = importlib.util.spec_from_file_location("load_examples", load_examples_path)
load_examples = importlib.util.module_from_spec(spec)
spec.loader.exec_module(load_examples)
BeispielanlagenLoader = load_examples.BeispielanlagenLoader


def create_get_file(loader: BeispielanlagenLoader, anlage_nummer: int, output_dir: str):
    """
    Erstellt eine .get Datei aus einer Beispielanlage.
    
    Args:
        loader: BeispielanlagenLoader Instanz
        anlage_nummer: Nummer der Anlage (1, 2 oder 3)
        output_dir: Ausgabeordner
    """
    anlage = loader.get_anlage(nummer=anlage_nummer)
    
    # Hole Parameter mit Fallback-Werten
    def get_param(key, default=None):
        value = loader.get_parameter(anlage_nummer, key)
        return value if value is not None and value != '' and value != '-' else default
    
    # Metadaten
    gebaeudetyp = anlage.get('Gebaeudetyp', f'Beispielanlage {anlage_nummer}')
    metadata = {
        "project_name": f"{gebaeudetyp} - Beispielanlage {anlage_nummer}",
        "location": "Deutschland",
        "designer": "GET Beispiel-Anlagen",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "notes": f"Beispielanlage {anlage_nummer}: {gebaeudetyp}\nHeizsystem: {anlage.get('Heizsystem', 'N/A')}"
    }
    
    # Bodeneigenschaften (Standardwerte, da nicht in CSV)
    ground_props = {
        "thermal_conductivity": 2.0,  # Standard für Sand
        "heat_capacity": 2400000.0,
        "undisturbed_temp": 10.0,
        "geothermal_gradient": 0.03,
        "soil_type": "Sand - feucht"
    }
    
    # Bohrlochkonfiguration
    bohrdurchmesser = get_param('Bohrdurchmesser_mm', 152.0)
    sondentiefe = get_param('Sondentiefe_m', 100.0)
    anzahl_sonden = int(get_param('Anzahl_Sonden', 1))
    
    # Bestimme Rohrkonfiguration basierend auf Rohrtyp
    rohrtyp = anlage.get('Rohrtyp', 'Doppel-U')
    if 'Doppel-U' in rohrtyp or 'Double-U' in rohrtyp:
        pipe_config = "2-rohr-u (Serie)"
    elif 'Single-U' in rohrtyp or 'Einfach-U' in rohrtyp:
        pipe_config = "1-rohr-u"
    elif '4-rohr' in rohrtyp.lower() or '4-verbinder' in rohrtyp.lower():
        pipe_config = "4-rohr-dual"
    else:
        pipe_config = "2-rohr-u (Serie)"  # Default
    
    borehole_config = {
        "diameter_mm": float(bohrdurchmesser),
        "depth_m": float(sondentiefe),
        "pipe_configuration": pipe_config,
        "shank_spacing_mm": 80.0,  # Standard
        "num_boreholes": anzahl_sonden
    }
    
    # Rohreigenschaften
    rohr_aussen = get_param('Rohr_aussen_mm', 32.0)
    rohr_wand = get_param('Rohr_wand_mm', 2.9)
    rohr_innen = float(rohr_aussen) - 2 * float(rohr_wand) if rohr_wand else 26.2
    
    pipe_props = {
        "material": rohrtyp,
        "outer_diameter_mm": float(rohr_aussen),
        "wall_thickness_mm": float(rohr_wand) if rohr_wand else 2.9,
        "thermal_conductivity": 0.42,  # PE Standard
        "inner_diameter_mm": rohr_innen
    }
    
    # Verfüllmaterial
    verpress_lambda = get_param('Verpressmaterial_lambda_W_mK', 2.0)
    grout_material = {
        "name": f"Verfüllmaterial λ={verpress_lambda} W/mK",
        "thermal_conductivity": float(verpress_lambda),
        "density": 1800.0,  # Standard
        "volume_per_borehole_liters": 2750.0  # Geschätzt
    }
    
    # Wärmeträgerflüssigkeit
    solemedium = anlage.get('Solemedium', 'Ethylenglykol')
    glykol_prozent = get_param('Glykol_Prozent', 25)
    volumenstrom = get_param('Volumenstrom_m3_h', 0.9)
    
    # Bestimme Gefriertemperatur basierend auf Glykol-Prozent
    if glykol_prozent == 25:
        freeze_temp = -12.0
        fluid_type = "Wasser/Glykol 25%"
    elif glykol_prozent == 30:
        freeze_temp = -15.0
        fluid_type = "Wasser/Glykol 30%"
    else:
        freeze_temp = -10.0
        fluid_type = f"Wasser/Glykol {glykol_prozent}%"
    
    # Fluid-Eigenschaften (Standardwerte für Glykol)
    heat_carrier_fluid = {
        "type": fluid_type,
        "thermal_conductivity": 0.48,
        "heat_capacity": 3795.0,
        "density": 1042.0,
        "viscosity": 0.00345,
        "flow_rate_m3h": float(volumenstrom),
        "freeze_temperature": freeze_temp
    }
    
    # Lastdaten
    jahresenergie = get_param('Jahresenergie_Erdreich_kWh_a', 0)
    maximale_entzugsleistung = get_param('Maximale_Entzugsleistung_kW', 0)
    heizlast = get_param('Heizlast_Gebaeude_kW', 0)
    jahreskuehlarbeit = get_param('Jahreskuehlarbeit_kWh_a', 0)
    betriebsstunden_wp = get_param('Betriebsstunden_WP_h_a', 0)
    betriebsstunden_heizen = get_param('Betriebsstunden_Heizen_h', 0)
    betriebsstunden_kuehlen = get_param('Betriebsstunden_Kuehlen_h', 0)
    
    # Bestimme Heizlast (falls nicht vorhanden, verwende maximale Entzugsleistung)
    peak_heating = float(heizlast) if heizlast else float(maximale_entzugsleistung)
    
    loads = {
        "annual_heating_kwh": float(jahresenergie) if jahresenergie else 0,
        "peak_heating_kw": peak_heating,
        "annual_cooling_kwh": float(jahreskuehlarbeit) if jahreskuehlarbeit else 0,
        "peak_cooling_kw": 0,  # Nicht in CSV
        "cop": get_param('COP_B0_W35', 4.0),
        "annual_operating_hours": int(betriebsstunden_wp) if betriebsstunden_wp else int(betriebsstunden_heizen) if betriebsstunden_heizen else 2000
    }
    
    # Temperaturgrenzen
    eintritt_min = get_param('Eintritt_Sole_WP_min_C', -2.0)
    austritt_max = get_param('Austritt_Sole_WP_max_C', -5.0)
    soletemp_winter = get_param('Soletemperatur_Winter_min_C', eintritt_min)
    soletemp_sommer = get_param('Soletemperatur_Sommer_max_C', 18.0)
    
    temp_limits = {
        "min_fluid_temp": float(soletemp_winter) if soletemp_winter else float(eintritt_min),
        "max_fluid_temp": float(soletemp_sommer) if soletemp_sommer else 18.0
    }
    
    # Simulationseinstellungen
    simulation = {
        "years": 25,
        "initial_depth": float(sondentiefe)
    }
    
    # Erstelle GET File Handler
    handler = GETFileHandler()
    
    # Dateiname
    filename = f"beispielanlage_{anlage_nummer}_{gebaeudetyp.lower().replace(' ', '_').replace('/', '_')}.get"
    filepath = os.path.join(output_dir, filename)
    
    # Exportiere
    success = handler.export_to_get(
        filepath=filepath,
        metadata=metadata,
        ground_props=ground_props,
        borehole_config=borehole_config,
        pipe_props=pipe_props,
        grout_material=grout_material,
        fluid_props=heat_carrier_fluid,
        loads=loads,
        temp_limits=temp_limits,
        simulation=simulation
    )
    
    if success:
        print(f"✅ Erstellt: {filename}")
        return filepath
    else:
        print(f"❌ Fehler beim Erstellen von {filename}")
        return None


def main():
    """Hauptfunktion: Erstellt alle 3 .get Dateien."""
    # Pfade
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = script_dir  # Speichere im gleichen Ordner
    
    print("=" * 60)
    print("Erstelle .get Dateien aus Beispielanlagen")
    print("=" * 60)
    print()
    
    # Lade Beispielanlagen
    loader = BeispielanlagenLoader()
    
    # Erstelle alle 3 Dateien
    created_files = []
    for anlage_nummer in [1, 2, 3]:
        print(f"\n📝 Erstelle Beispielanlage {anlage_nummer}...")
        filepath = create_get_file(loader, anlage_nummer, output_dir)
        if filepath:
            created_files.append(filepath)
    
    print("\n" + "=" * 60)
    print(f"✅ Fertig! {len(created_files)} Dateien erstellt:")
    for filepath in created_files:
        print(f"   - {os.path.basename(filepath)}")
    print("=" * 60)


if __name__ == "__main__":
    main()

