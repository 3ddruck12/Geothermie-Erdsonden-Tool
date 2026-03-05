
import sys
import os
import math

# Add project root to path
# Assuming this script is run from project root, or we add relative
sys.path.append(os.path.abspath("."))

from calculations.borehole import BoreholeCalculator
from calculations.borefield_gfunction import BorefieldCalculator, PYGFUNCTION_AVAILABLE

def test_single_family_home_fix_direct():
    print("\n=== TEST 1A: Einfamilienhaus (Last-Splitting Fix, Direct) ===")
    calc = BoreholeCalculator()
    
    # Szenario: 12 MWh, 2 Sonden.
    # Ohne Fix: 12 MWh auf EINER Sonde -> Tiefe X (z.B. 200m). Total = 2*200 = 400m.
    # Mit Fix: 6 MWh pro Sonde -> Tiefe Y (z.B. 100m). Total = 2*100 = 200m.
    
    # 1. Berechnung OHNE Custom G-Function (nur Split)
    # Wir rufen direkt calculate_required_depth auf
    try:
        result = calc.calculate_required_depth(
            ground_thermal_conductivity=2.0,
            ground_heat_capacity=2.4e6,
            undisturbed_ground_temp=10.0,
            annual_heating_demand=12.0, # MWh Total
            peak_heating_load=6.0, # kW Total
            # NEU: n_boreholes=2. Das sollte die Last halbieren.
            n_boreholes=2,
            initial_depth=100.0,
            simulation_years=25
        )
        
        print(f"Eingabe: 2 Sonden, 12 MWh Total.")
        print(f"Ergebnis Tiefe pro Sonde: {result.required_depth} m")
        total_depth = result.required_depth * 2
        print(f"Gesamtlänge: {total_depth} m")
        
        # Erwartung: ca. 90-110m pro Sonde bei diesen Parametern.
        if 80 < result.required_depth < 130:
            print("✅ PASS: Tiefe liegt im erwarteten Bereich (Last wurde geteilt).")
        else:
            print(f"❌ FAIL: Tiefe {result.required_depth}m unplausibel (Bug noch vorhanden?).")
            
    except Exception as e:
        print(f"❌ FAIL: Exception: {e}")

def test_field_interference():
    print("\n=== TEST 2: Feld-Interferenz (25 Sonden) ===")
    
    # Wir vergleichen:
    # A) 25 Sonden, Last gesplittet, OHNE Interferenz (optimistisch)
    # B) 25 Sonden, Last gesplittet, MIT Interferenz (pygfunction)
    
    if not PYGFUNCTION_AVAILABLE:
        print("⚠️ pygfunction nicht da, Test übersprungen")
        return

    # Gemeinsame Parameter
    params = {
        "ground_thermal_conductivity": 2.0,
        "ground_heat_capacity": 2.4e6,
        "undisturbed_ground_temp": 10.0,
        "n_boreholes": 25,
        "annual_heating_demand": 100.0, # MWh Total (Klein für 25, aber testweise)
        "peak_heating_load": 30.0, # kW Total
        "initial_depth": 100.0,
        "simulation_years": 25
    }
    
    calc = BoreholeCalculator()
    
    # A) Ohne Interferenz (custom_gfunction=None)
    res_no_interf = calc.calculate_required_depth(**params)
    print(f"A) Ohne Interferenz: {res_no_interf.required_depth} m pro Sonde")
    
    # B) Mit Interferenz (simuliere Controller-Logic)
    bf_calc = BorefieldCalculator()

    # 5x5 Feld, 6m Abstand
    print("   Berechne g-Funktion für 5x5 Feld...")
    g_res = bf_calc.calculate_gfunction(
        "rectangle", 5, 5, 6.0, 6.0, 
        borehole_depth=100.0, 
        borehole_radius=0.075,
        soil_thermal_diffusivity=2.0/2.4e6,
        simulation_years=25
    )
    custom_g = bf_calc.get_gfunction_interpolator(g_res)
    
    # Aufruf mit custom_gfunction
    res_interf = calc.calculate_required_depth(
        **params,
        custom_gfunction=custom_g
    )
    print(f"B) Mit Interferenz:  {res_interf.required_depth} m pro Sonde")
    
    diff = res_interf.required_depth - res_no_interf.required_depth
    print(f"Differenz durch Interferenz: +{diff:.1f} m")
    
    if diff > 1.0:
        print("✅ PASS: Interferenz führt zu tieferen Bohrungen.")
    else:
        print("❌ FAIL: Keine signifikante Änderung durch Interferenz.")

if __name__ == "__main__":
    test_single_family_home_fix_direct()
    test_field_interference()
