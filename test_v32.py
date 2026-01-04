#!/usr/bin/env python3
"""Test-Skript für V3.2 Features."""

import sys
import os

# Füge Projektverzeichnis zum Pfad hinzu
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.get_file_handler import GETFileHandler
from calculations.borefield_gfunction import BorefieldCalculator, check_pygfunction_installation

def test_get_file_handler():
    """Testet den GET File Handler."""
    print("=" * 60)
    print("TEST 1: GET File Handler")
    print("=" * 60)
    
    handler = GETFileHandler()
    print(f"✅ Handler erstellt (Version {handler.format_version})")
    
    # Test-Daten
    test_file = "/tmp/v32_test.get"
    
    metadata = {
        "project_name": "V3.2 Test Projekt",
        "location": "München, Deutschland",
        "designer": "Test User",
        "date": "2026-01-03",
        "notes": "Testprojekt für V3.2"
    }
    
    ground = {
        "thermal_conductivity": 2.8,
        "heat_capacity": 2.5e6,
        "undisturbed_temp": 11.5,
        "geothermal_gradient": 0.03,
        "soil_type": "Granit - feucht"
    }
    
    borehole = {
        "diameter_mm": 150.0,
        "depth_m": 140.0,
        "pipe_configuration": "2-rohr-u (Serie)",
        "shank_spacing_mm": 75.0,
        "num_boreholes": 2
    }
    
    pipe = {
        "material": "PE-100 RC",
        "outer_diameter_mm": 32.0,
        "wall_thickness_mm": 2.9,
        "thermal_conductivity": 0.42,
        "inner_diameter_mm": 26.2
    }
    
    grout = {
        "name": "Thermozement Plus",
        "thermal_conductivity": 2.2,
        "density": 1850.0,
        "volume_per_borehole_liters": 2650.0
    }
    
    fluid = {
        "type": "Wasser/Glykol 35%",
        "thermal_conductivity": 0.46,
        "heat_capacity": 3800.0,
        "density": 1045.0,
        "viscosity": 0.0038,
        "flow_rate_m3h": 2.8,
        "freeze_temperature": -18.0
    }
    
    loads = {
        "annual_heating_kwh": 52000.0,
        "annual_cooling_kwh": 0.0,
        "peak_heating_kw": 14.2,
        "peak_cooling_kw": 0.0,
        "heat_pump_cop": 4.6
    }
    
    temp_limits = {
        "min_fluid_temp": -2.5,
        "max_fluid_temp": 18.0
    }
    
    simulation = {
        "years": 50,
        "initial_depth": 120.0
    }
    
    # Bohrfeld-Daten V3.2
    borefield = {
        "enabled": True,
        "layout": "rectangle",
        "num_boreholes_x": 2,
        "num_boreholes_y": 1,
        "spacing_x_m": 7.0,
        "spacing_y_m": 7.0,
        "soil_thermal_diffusivity": 1.12e-6,
        "simulation_years": 25
    }
    
    # Export
    print("\n📤 Exportiere Test-Projekt...")
    success = handler.export_to_get(
        test_file, metadata, ground, borehole, pipe, grout, 
        fluid, loads, temp_limits, simulation, 
        borefield_data=borefield
    )
    
    if not success:
        print("❌ Export fehlgeschlagen!")
        return False
    
    print(f"✅ Export erfolgreich: {test_file}")
    
    # Datei-Info
    info = handler.get_file_info(test_file)
    if info:
        print(f"\n📋 Datei-Informationen:")
        print(f"   Format: {info['format']}")
        print(f"   Version: {info['version']}")
        print(f"   Projekt: {info['project_name']}")
        print(f"   Ort: {info['location']}")
        print(f"   Bohrfeld aktiv: {info['has_borefield']}")
    
    # Validierung
    valid, msg = handler.validate_get_file(test_file)
    print(f"\n✔️  Validierung: {msg}")
    
    # Import
    print("\n📥 Importiere Test-Projekt...")
    data = handler.import_from_get(test_file)
    
    if not data:
        print("❌ Import fehlgeschlagen!")
        return False
    
    print(f"✅ Import erfolgreich!")
    print(f"   Projekt: {data['metadata']['project_name']}")
    print(f"   Bohrungen: {data['borehole_config']['num_boreholes']}")
    print(f"   Tiefe: {data['borehole_config']['depth_m']} m")
    print(f"   Bohrfeld: {data['borefield_v32']['layout']} Layout")
    
    # Aufräumen
    os.remove(test_file)
    print(f"\n🗑️  Test-Datei gelöscht")
    
    return True


def test_borefield_calculator():
    """Testet den BorefieldCalculator."""
    print("\n" + "=" * 60)
    print("TEST 2: Bohrfeld-Simulation (pygfunction)")
    print("=" * 60)
    
    # Prüfe Installation
    installed, version = check_pygfunction_installation()
    print(f"pygfunction: {'✅ ' + version if installed else '❌ nicht installiert'}")
    
    if not installed:
        print("⚠️  Überspringe Bohrfeld-Tests")
        return False
    
    # Erstelle Calculator
    calc = BorefieldCalculator()
    print("✅ BorefieldCalculator erstellt")
    
    # Test 1: Einfaches Rechteck-Feld
    print("\n🔄 Test 1: 3×2 Rechteck-Feld...")
    result = calc.calculate_gfunction(
        layout="rectangle",
        num_boreholes_x=3,
        num_boreholes_y=2,
        spacing_x=6.5,
        spacing_y=6.5,
        borehole_depth=120.0,
        borehole_radius=0.075,
        soil_thermal_diffusivity=1.1e-6,
        simulation_years=15,
        time_resolution="monthly"
    )
    
    print(f"✅ Berechnung erfolgreich:")
    print(f"   {result['num_boreholes']} Bohrungen")
    print(f"   {result['total_depth']} m Gesamttiefe")
    print(f"   {result['field_area']:.1f} m² Feldgröße")
    
    # Test 2: L-förmiges Feld
    print("\n🔄 Test 2: L-förmiges Feld...")
    result_l = calc.calculate_gfunction(
        layout="L",
        num_boreholes_x=4,
        num_boreholes_y=3,
        spacing_x=7.0,
        spacing_y=7.0,
        borehole_depth=100.0,
        borehole_radius=0.076,
        soil_thermal_diffusivity=1.0e-6,
        simulation_years=10,
        time_resolution="monthly"
    )
    
    print(f"✅ L-Feld: {result_l['num_boreholes']} Bohrungen")
    
    # Test 3: Einzelne Reihe
    print("\n🔄 Test 3: Einzelne Reihe (line)...")
    result_line = calc.calculate_gfunction(
        layout="line",
        num_boreholes_x=5,
        num_boreholes_y=1,
        spacing_x=6.0,
        spacing_y=6.0,
        borehole_depth=150.0,
        borehole_radius=0.076,
        soil_thermal_diffusivity=1.2e-6,
        simulation_years=20,
        time_resolution="monthly"
    )
    
    print(f"✅ Reihe: {result_line['num_boreholes']} Bohrungen")
    
    return True


def test_migration():
    """Testet Migrations-Funktionalität."""
    print("\n" + "=" * 60)
    print("TEST 3: Abwärtskompatibilität & Migration")
    print("=" * 60)
    
    handler = GETFileHandler()
    
    # Simuliere V3.0 Datei
    v30_file = "/tmp/v30_test.get"
    
    v30_data = {
        "file_format": "GET",
        "format_version": "3.0",
        "created_with": "Test v3.0",
        "created_date": "2025-12-01T12:00:00Z",
        "encoding": "UTF-8",
        "ground_properties": {
            "thermal_conductivity": 2.5,
            "heat_capacity": 2.4e6,
            "undisturbed_temp": 10.0,
            "geothermal_gradient": 0.03
        },
        "borehole_config": {
            "diameter_mm": 152.0,
            "depth_m": 100.0,
            "pipe_configuration": "2-rohr-u",
            "shank_spacing_mm": 80.0,
            "num_boreholes": 1
        },
        "loads": {
            "annual_heating_kwh": 40000.0,
            "peak_heating_kw": 10.0
        }
    }
    
    # Schreibe V3.0 Datei
    import json
    with open(v30_file, 'w', encoding='utf-8') as f:
        json.dump(v30_data, f, indent=2)
    
    print("📝 V3.0 Test-Datei erstellt")
    
    # Importiere und migriere
    print("🔄 Migriere V3.0 → V3.2...")
    migrated_data = handler.import_from_get(v30_file)
    
    if migrated_data:
        print(f"✅ Migration erfolgreich!")
        print(f"   Original: {v30_data['format_version']}")
        print(f"   Migriert: {migrated_data['format_version']}")
        print(f"   Bohrfeld hinzugefügt: {'borefield_v32' in migrated_data}")
        
        if 'borefield_v32' in migrated_data:
            print(f"   Bohrfeld aktiviert: {migrated_data['borefield_v32']['enabled']}")
    else:
        print("❌ Migration fehlgeschlagen!")
        return False
    
    # Aufräumen
    os.remove(v30_file)
    print("🗑️  Test-Datei gelöscht")
    
    return True


def main():
    """Hauptfunktion für alle Tests."""
    print("\n")
    print("🚀" * 30)
    print("   GEOTHERMIE ERDSONDEN-TOOL V3.2")
    print("   Test Suite")
    print("🚀" * 30)
    
    results = []
    
    # Test 1: GET File Handler
    try:
        success = test_get_file_handler()
        results.append(("GET File Handler", success))
    except Exception as e:
        print(f"❌ TEST 1 FEHLER: {e}")
        results.append(("GET File Handler", False))
    
    # Test 2: Bohrfeld-Simulation
    try:
        success = test_borefield_calculator()
        results.append(("Bohrfeld-Simulation", success))
    except Exception as e:
        print(f"❌ TEST 2 FEHLER: {e}")
        results.append(("Bohrfeld-Simulation", False))
    
    # Test 3: Migration
    try:
        success = test_migration()
        results.append(("Abwärtskompatibilität", success))
    except Exception as e:
        print(f"❌ TEST 3 FEHLER: {e}")
        results.append(("Abwärtskompatibilität", False))
    
    # Zusammenfassung
    print("\n" + "=" * 60)
    print("ZUSAMMENFASSUNG")
    print("=" * 60)
    
    for test_name, success in results:
        status = "✅ BESTANDEN" if success else "❌ FEHLGESCHLAGEN"
        print(f"{test_name:.<40} {status}")
    
    all_passed = all(result[1] for result in results)
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALLE TESTS BESTANDEN! V3.2 ist bereit!")
    else:
        print("⚠️  EINIGE TESTS FEHLGESCHLAGEN!")
    print("=" * 60 + "\n")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())




