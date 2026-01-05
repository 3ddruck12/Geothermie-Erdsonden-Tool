#!/usr/bin/env python3
"""Test für VDI 4640 Integration."""

import sys
sys.path.insert(0, '/home/jens/Dokumente/Software Projekte/Geothermietool')

from calculations.vdi4640 import VDI4640Calculator


def test_vdi4640_heating_dominant():
    """Test: Heizen ist auslegungsrelevant."""
    print("\n" + "="*70)
    print("TEST 1: Heizen dominant (Winter-Klimazone)")
    print("="*70)
    
    calc = VDI4640Calculator()
    
    result = calc.calculate_complete(
        ground_thermal_conductivity=2.0,
        ground_thermal_diffusivity=1.0e-6,
        t_undisturbed=10.0,
        borehole_diameter=152,
        borehole_depth_initial=100.0,
        n_boreholes=1,
        r_borehole=0.1,
        annual_heating_demand=15000,   # kWh
        peak_heating_load=8.0,          # kW
        annual_cooling_demand=1000,     # kWh (minimal)
        peak_cooling_load=2.0,
        heat_pump_cop_heating=4.0,
        heat_pump_cop_cooling=4.0,
        t_fluid_min_required=-2.0,
        t_fluid_max_required=35.0
    )
    
    print(f"\n✓ Auslegungsfall: {result.design_case.upper()}")
    print(f"  Sondenlänge Heizen: {result.required_depth_heating:.1f} m")
    print(f"  Sondenlänge Kühlen: {result.required_depth_cooling:.1f} m")
    print(f"  → Ausgelegt: {result.required_depth_final:.1f} m")
    print(f"\n  T_WP_aus (Heizen min): {result.t_wp_aus_heating_min:.2f} °C")
    print(f"  T_WP_aus (Kühlen max): {result.t_wp_aus_cooling_max:.2f} °C")
    
    assert result.design_case == "heating", "Heizen sollte dominant sein!"
    assert result.required_depth_final == result.required_depth_heating
    print("\n✅ Test bestanden!")
    

def test_vdi4640_cooling_dominant():
    """Test: Kühlen ist auslegungsrelevant."""
    print("\n" + "="*70)
    print("TEST 2: Kühlen dominant (Bürogebäude mit hoher Kühllast)")
    print("="*70)
    
    calc = VDI4640Calculator()
    
    result = calc.calculate_complete(
        ground_thermal_conductivity=1.5,  # Schlechterer Boden
        ground_thermal_diffusivity=0.8e-6,
        t_undisturbed=12.0,
        borehole_diameter=152,
        borehole_depth_initial=100.0,
        n_boreholes=2,
        r_borehole=0.12,
        annual_heating_demand=8000,      # kWh (wenig Heizen)
        peak_heating_load=5.0,
        annual_cooling_demand=20000,     # kWh (viel Kühlen!)
        peak_cooling_load=15.0,
        heat_pump_cop_heating=4.0,
        heat_pump_cop_cooling=3.5,
        t_fluid_min_required=-1.0,
        t_fluid_max_required=30.0        # Niedriges Limit!
    )
    
    print(f"\n✓ Auslegungsfall: {result.design_case.upper()}")
    print(f"  Sondenlänge Heizen: {result.required_depth_heating:.1f} m")
    print(f"  Sondenlänge Kühlen: {result.required_depth_cooling:.1f} m")
    print(f"  → Ausgelegt: {result.required_depth_final:.1f} m")
    print(f"\n  T_WP_aus (Heizen min): {result.t_wp_aus_heating_min:.2f} °C")
    print(f"  T_WP_aus (Kühlen max): {result.t_wp_aus_cooling_max:.2f} °C")
    
    assert result.design_case == "cooling", "Kühlen sollte dominant sein!"
    assert result.required_depth_final == result.required_depth_cooling
    print("\n✅ Test bestanden!")


def test_vdi4640_multiple_boreholes():
    """Test: Mehrere Bohrungen."""
    print("\n" + "="*70)
    print("TEST 3: Mehrere Bohrungen (3 Stück)")
    print("="*70)
    
    calc = VDI4640Calculator()
    
    result = calc.calculate_complete(
        ground_thermal_conductivity=2.5,
        ground_thermal_diffusivity=1.2e-6,
        t_undisturbed=11.0,
        borehole_diameter=152,
        borehole_depth_initial=100.0,
        n_boreholes=3,
        r_borehole=0.09,
        annual_heating_demand=30000,
        peak_heating_load=18.0,
        annual_cooling_demand=5000,
        peak_cooling_load=6.0,
        heat_pump_cop_heating=4.2,
        heat_pump_cop_cooling=4.0,
        t_fluid_min_required=-3.0,
        t_fluid_max_required=35.0
    )
    
    print(f"\n✓ Auslegungsfall: {result.design_case.upper()}")
    print(f"  Tiefe pro Bohrung: {result.required_depth_final:.1f} m")
    print(f"  Anzahl Bohrungen: 3")
    print(f"  Gesamtlänge: {result.required_depth_final * 3:.1f} m")
    print(f"\n  Lasten (Heizen):")
    print(f"    Q_Grundlast: {result.q_nettogrundlast_heating/1000:.2f} kW")
    print(f"    Q_Periodisch: {result.q_per_heating/1000:.2f} kW")
    print(f"    Q_Peak: {result.q_peak_heating/1000:.2f} kW")
    
    assert result.required_depth_final > 0
    print("\n✅ Test bestanden!")


def test_vdi4640_resistances():
    """Test: Thermische Widerstände."""
    print("\n" + "="*70)
    print("TEST 4: Thermische Widerstände (Zeitskalen)")
    print("="*70)
    
    calc = VDI4640Calculator()
    
    result = calc.calculate_complete(
        ground_thermal_conductivity=2.0,
        ground_thermal_diffusivity=1.0e-6,
        t_undisturbed=10.0,
        borehole_diameter=152,
        borehole_depth_initial=100.0,
        n_boreholes=1,
        r_borehole=0.1,
        annual_heating_demand=12000,
        peak_heating_load=7.0,
        annual_cooling_demand=0,
        peak_cooling_load=0,
        heat_pump_cop_heating=4.0,
        heat_pump_cop_cooling=4.0,
        t_fluid_min_required=-2.0,
        t_fluid_max_required=35.0
    )
    
    print(f"\n✓ Thermische Widerstände:")
    print(f"  R_Grundlast (10 Jahre):  {result.r_grundlast:.6f} m·K/W")
    print(f"  R_Periodisch (1 Monat):  {result.r_per:.6f} m·K/W")
    print(f"  R_Peak (6 Stunden):      {result.r_peak:.6f} m·K/W")
    print(f"  R_Bohrloch:              {result.r_borehole:.6f} m·K/W")
    
    print(f"\n✓ g-Funktionswerte:")
    print(f"  g_Grundlast: {result.g_grundlast:.4f}")
    print(f"  g_Periodisch: {result.g_per:.4f}")
    print(f"  g_Peak: {result.g_peak:.4f}")
    
    # Physikalische Plausibilität
    assert result.r_grundlast > result.r_per > result.r_peak, \
        "Widerstände sollten mit Zeitskala abnehmen!"
    assert result.g_grundlast > result.g_per > result.g_peak, \
        "g-Werte sollten mit Zeitskala abnehmen!"
    
    print("\n✅ Test bestanden!")


if __name__ == "__main__":
    print("\n" + "🧪 " * 30)
    print("VDI 4640 INTEGRATION TESTS")
    print("🧪 " * 30)
    
    try:
        test_vdi4640_heating_dominant()
        test_vdi4640_cooling_dominant()
        test_vdi4640_multiple_boreholes()
        test_vdi4640_resistances()
        
        print("\n" + "🎉 " * 30)
        print("ALLE TESTS BESTANDEN!")
        print("🎉 " * 30 + "\n")
        
    except AssertionError as e:
        print(f"\n❌ TEST FEHLGESCHLAGEN: {e}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ FEHLER: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)








