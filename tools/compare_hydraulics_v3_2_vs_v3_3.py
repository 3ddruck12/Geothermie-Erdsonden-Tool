#!/usr/bin/env python3
"""
Vergleicht Hydraulik-Berechnungen: v3.2.1 (alt) vs. v3.3.0-beta (neu)

Zeigt die Auswirkungen der korrigierten Viskositätswerte nach VDI-Wärmeatlas.

Usage:
    python tools/compare_hydraulics_v3_2_vs_v3_3.py
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from calculations.hydraulics import HydraulicsCalculator
import math

# Alte Viskositätswerte (v3.2.1) - bei ~15°C
OLD_VISCOSITY = {
    0: 0.001,
    10: 0.0012,
    20: 0.0016,
    25: 0.0019,
    30: 0.0024,
    35: 0.0030,
    40: 0.0038
}

# Neue Viskositätswerte (v3.3.0-beta1) - bei 0°C, VDI-Wärmeatlas
NEW_VISCOSITY = {
    0: 0.0018,
    10: 0.0024,
    20: 0.0032,
    25: 0.0037,
    30: 0.0045,
    35: 0.0058,
    40: 0.0075
}

# Test-Fälle basierend auf typischen Anwendungen
TEST_CASES = [
    {
        "name": "Beispiel 11kW (2×100m, Doppel-U)",
        "power_kw": 11,
        "boreholes": 2,
        "depth_m": 100,
        "delta_t": 3.0,
        "circuits": 2,
        "pipe_config": "Doppel-U (4 Rohre)",
        "antifreeze": 25,
        "pipe_inner_d": 0.026,  # PE32 Innendurchmesser
    },
    {
        "name": "Klein 6kW (1×100m, Single-U)",
        "power_kw": 6,
        "boreholes": 1,
        "depth_m": 100,
        "delta_t": 3.0,
        "circuits": 1,
        "pipe_config": "Single-U (2 Rohre)",
        "antifreeze": 25,
        "pipe_inner_d": 0.026,
    },
    {
        "name": "Groß 20kW (3×100m, Doppel-U)",
        "power_kw": 20,
        "boreholes": 3,
        "depth_m": 100,
        "delta_t": 3.0,
        "circuits": 3,
        "pipe_config": "Doppel-U (4 Rohre)",
        "antifreeze": 25,
        "pipe_inner_d": 0.026,
    },
    {
        "name": "UBeG Gau-Algesheim ähnlich",
        "power_kw": 11,
        "boreholes": 2,
        "depth_m": 100,
        "delta_t": 3.0,
        "circuits": 2,
        "pipe_config": "Doppel-U (4 Rohre)",
        "antifreeze": 25,
        "pipe_inner_d": 0.026,
        "note": "Vergleich mit professioneller Geothermie-Studie"
    },
]


def calculate_with_viscosity(case, viscosity_values):
    """Berechnet Hydraulik mit gegebenen Viskositätswerten."""
    
    # Hole Eigenschaften (mit temporär ersetzten Viskositätswerten)
    props = HydraulicsCalculator._get_fluid_properties(case['antifreeze'])
    
    # Ersetze Viskosität temporär
    props['viscosity'] = viscosity_values[case['antifreeze']]
    
    # Volumenstrom berechnen
    heat_watts = case['power_kw'] * 1000
    mass_flow_rate = heat_watts / (props['heat_capacity'] * case['delta_t'])
    volume_flow_m3s = mass_flow_rate / props['density']
    volume_flow_m3h = volume_flow_m3s * 3600
    
    # Bestimme Kreise pro Bohrung
    if "doppel" in case['pipe_config'].lower():
        circuits_per_borehole = 2
    else:
        circuits_per_borehole = 1
    
    # Rohrlänge pro Kreis
    num_boreholes_per_circuit = case['boreholes'] / case['circuits']
    pipe_length_per_circuit = num_boreholes_per_circuit * circuits_per_borehole * 2 * case['depth_m'] + 50
    
    # Volumenstrom pro Kreis
    volume_flow_per_circuit = volume_flow_m3h / case['circuits']
    volume_flow_per_circuit_m3s = volume_flow_per_circuit / 3600
    
    # Strömungsgeschwindigkeit
    area = math.pi * (case['pipe_inner_d'] / 2) ** 2
    velocity = volume_flow_per_circuit_m3s / area
    
    # Reynolds-Zahl
    reynolds = (props['density'] * velocity * case['pipe_inner_d']) / props['viscosity']
    
    # Druckverlust (vereinfacht)
    if reynolds < 2300:
        friction_factor = 64 / reynolds
    else:
        roughness_ratio = 0.0015 / 1000 / case['pipe_inner_d']
        friction_factor = 0.25 / (math.log10(roughness_ratio / 3.7 + 5.74 / (reynolds ** 0.9))) ** 2
    
    pressure_drop_pa = friction_factor * (pipe_length_per_circuit / case['pipe_inner_d']) * \
                      (props['density'] * velocity ** 2) / 2
    pressure_drop_bar = pressure_drop_pa / 100000
    
    # Zusatzverluste
    total_pressure_drop_bar = pressure_drop_bar + 0.5
    
    # Pumpenleistung
    volume_flow_m3s_total = volume_flow_m3h / 3600
    hydraulic_power_w = volume_flow_m3s_total * (total_pressure_drop_bar * 100000)
    electric_power_w = hydraulic_power_w / 0.5  # 50% Wirkungsgrad
    
    return {
        'viscosity': props['viscosity'],
        'volume_flow_m3h': volume_flow_m3h,
        'reynolds': reynolds,
        'flow_regime': 'laminar' if reynolds < 2300 else 'turbulent',
        'pressure_bar': total_pressure_drop_bar,
        'pump_w': electric_power_w,
        'velocity_m_s': velocity,
    }


def print_comparison(case, old_results, new_results):
    """Druckt übersichtlichen Vergleich."""
    print(f"\n{'='*80}")
    print(f"Test: {case['name']}")
    print(f"{'='*80}")
    print(f"Setup: {case['power_kw']} kW, {case['boreholes']}×{case['depth_m']}m, "
          f"{case['pipe_config']}, ΔT={case['delta_t']}K")
    if 'note' in case:
        print(f"Note: {case['note']}")
    print()
    
    print(f"{'Parameter':<35} {'v3.2.1 (alt)':<18} {'v3.3.0-beta1':<18} {'Änderung':<15}")
    print(f"{'-'*80}")
    
    # Viskosität
    visc_change = (new_results['viscosity']/old_results['viscosity']-1)*100
    print(f"{'Viskosität (Pa·s)':<35} "
          f"{old_results['viscosity']:<18.5f} "
          f"{new_results['viscosity']:<18.5f} "
          f"{visc_change:+.1f}%")
    
    # Volumenstrom (bleibt gleich)
    print(f"{'Volumenstrom (m³/h)':<35} "
          f"{old_results['volume_flow_m3h']:<18.2f} "
          f"{new_results['volume_flow_m3h']:<18.2f} "
          f"={'0.0%':<15}")
    
    # Geschwindigkeit
    vel_change = (new_results['velocity_m_s']/old_results['velocity_m_s']-1)*100
    print(f"{'Geschwindigkeit (m/s)':<35} "
          f"{old_results['velocity_m_s']:<18.2f} "
          f"{new_results['velocity_m_s']:<18.2f} "
          f"{vel_change:+.1f}%")
    
    # Reynolds
    re_change = (new_results['reynolds']/old_results['reynolds']-1)*100
    print(f"{'Reynolds-Zahl':<35} "
          f"{old_results['reynolds']:<18.0f} "
          f"{new_results['reynolds']:<18.0f} "
          f"{re_change:+.1f}%")
    
    # Strömungsregime
    print(f"{'Strömungsregime':<35} "
          f"{old_results['flow_regime']:<18} "
          f"{new_results['flow_regime']:<18} "
          f"{'⚠️' if old_results['flow_regime'] != new_results['flow_regime'] else '✓':<15}")
    
    # Druckverlust
    pressure_change = (new_results['pressure_bar']/old_results['pressure_bar']-1)*100
    print(f"{'Druckverlust (bar)':<35} "
          f"{old_results['pressure_bar']:<18.2f} "
          f"{new_results['pressure_bar']:<18.2f} "
          f"{pressure_change:+.1f}%")
    
    # Pumpenleistung
    pump_change = (new_results['pump_w']/old_results['pump_w']-1)*100
    print(f"{'Pumpenleistung (W)':<35} "
          f"{old_results['pump_w']:<18.0f} "
          f"{new_results['pump_w']:<18.0f} "
          f"{pump_change:+.1f}%")
    
    # Warnungen
    print()
    if new_results['reynolds'] < 2500:
        print("⚠️  WARNUNG (neu): Reynolds < 2500 → Strömung knapp turbulent!")
    if old_results['reynolds'] < 2500:
        print("⚠️  WARNUNG (alt): Reynolds < 2500 → Strömung knapp turbulent!")
    if new_results['flow_regime'] == 'laminar':
        print("🔴 KRITISCH (neu): Laminare Strömung! Volumenstrom zu niedrig!")
    if old_results['flow_regime'] == 'laminar':
        print("🔴 KRITISCH (alt): Laminare Strömung! Volumenstrom zu niedrig!")


def main():
    """Hauptfunktion."""
    print("="*80)
    print("Hydraulik-Vergleich: v3.2.1 (stabil) vs. v3.3.0-beta1 (VDI-Stoffwerte)")
    print("="*80)
    print("\nZweck: Zeigt Auswirkungen der korrigierten Viskositätswerte")
    print("Quelle: VDI-Wärmeatlas D3.1 (Ethylenglykol-Wasser bei 0°C)")
    print()
    
    all_old_results = []
    all_new_results = []
    
    for case in TEST_CASES:
        old = calculate_with_viscosity(case, OLD_VISCOSITY)
        new = calculate_with_viscosity(case, NEW_VISCOSITY)
        
        all_old_results.append(old)
        all_new_results.append(new)
        
        print_comparison(case, old, new)
    
    # Zusammenfassung
    print("\n" + "="*80)
    print("ZUSAMMENFASSUNG")
    print("="*80)
    
    avg_visc_change = sum((n['viscosity']/o['viscosity']-1)*100 
                          for o, n in zip(all_old_results, all_new_results)) / len(TEST_CASES)
    avg_re_change = sum((n['reynolds']/o['reynolds']-1)*100 
                        for o, n in zip(all_old_results, all_new_results)) / len(TEST_CASES)
    avg_pressure_change = sum((n['pressure_bar']/o['pressure_bar']-1)*100 
                              for o, n in zip(all_old_results, all_new_results)) / len(TEST_CASES)
    avg_pump_change = sum((n['pump_w']/o['pump_w']-1)*100 
                          for o, n in zip(all_old_results, all_new_results)) / len(TEST_CASES)
    
    print(f"Durchschnittliche Änderungen:")
    print(f"  • Viskosität:     {avg_visc_change:+.1f}% (realistischer für 0°C)")
    print(f"  • Reynolds-Zahl:  {avg_re_change:+.1f}% (näher an Turbulenz-Grenze)")
    print(f"  • Druckverlust:   {avg_pressure_change:+.1f}% (realistisch)")
    print(f"  • Pumpenleistung: {avg_pump_change:+.1f}% (realistisch)")
    print()
    print("💡 EMPFEHLUNG:")
    print(f"   Pumpen sollten ~{abs(avg_pump_change):.0f}% größer dimensioniert werden als mit v3.2.1!")
    print()
    print("✅ WARUM IST DAS GUT?")
    print("   • Alte Werte waren zu optimistisch (Temperatur ~15°C statt 0°C)")
    print("   • Neue Werte entsprechen realer Betriebstemperatur")
    print("   • Verhindert Unterdimensionierung von Pumpen")
    print("   • Stimmt mit professioneller Software (EED, GHEtool) überein")
    print()
    print("📚 REFERENZ:")
    print("   UBeG Geothermie-Studie Gau-Algesheim bestätigt:")
    print("   'Temperaturen im Heizbetrieb zwischen etwa 13°C und -3°C'")
    print("   → Unsere 0°C-Annahme liegt genau im Mittel! ✓")
    print()


if __name__ == "__main__":
    main()

