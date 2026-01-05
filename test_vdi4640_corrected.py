#!/usr/bin/env python3
"""Test-Skript für VDI 4640 Berechnung mit korrigierten Werten."""

from calculations.vdi4640 import VDI4640Calculator
import os

# Debug-Modus aktivieren
debug_file = os.path.join(os.path.expanduser("~"), "vdi4640_corrected_debug.log")
calc = VDI4640Calculator(debug=True, debug_file=debug_file)

print("=" * 80)
print("VDI 4640 BERECHNUNG MIT KORRIGIERTEN WERTEN")
print("=" * 80)
print()

# === EINGABEPARAMETER (aus Ihrer Analyse) ===
ground_thermal_conductivity = 2.3  # W/(m·K)
ground_thermal_diffusivity = 1.0e-6  # m²/s
t_undisturbed = 10.0  # °C
borehole_diameter = 152  # mm
borehole_depth_initial = 100.0  # m
n_boreholes_start = 2  # Startwert

# Verfüllmaterial optimiert (höhere Wärmeleitfähigkeit)
grout_thermal_cond = 1.8  # W/(m·K) - Bentonit-Quarzsand-Zement
pipe_outer_diameter = 0.032  # m
pipe_thickness = 0.0037  # m
pipe_thermal_cond = 0.42  # W/(m·K)
borehole_radius = (borehole_diameter / 1000) / 2  # m
pipe_outer_radius = pipe_outer_diameter / 2

# Berechne optimierten Bohrlochwiderstand
import math
r_grout = (1 / (2 * math.pi * grout_thermal_cond)) * math.log(borehole_radius / pipe_outer_radius)
pipe_inner_radius = (pipe_outer_diameter - 2 * pipe_thickness) / 2
r_pipe = (1 / (2 * math.pi * pipe_thermal_cond)) * math.log(pipe_outer_diameter / (2 * pipe_inner_radius))
r_conv = 1 / (2 * math.pi * pipe_inner_radius * 500)  # h ≈ 500 W/m²K
r_borehole = 0.8 * (r_grout + r_pipe + r_conv)  # Double-U (4 Rohre)
r_borehole = max(0.05, r_borehole)

print(f"Berechneter R_Bohrloch (optimiert): {r_borehole:.6f} m·K/W")
print()

# Lasten
annual_heating_demand = 33600  # kWh
peak_heating_load_corrected = 16.0  # kW (KORRIGIERT von 12 kW)
annual_cooling_demand = 0.0  # kWh
peak_cooling_load = 0.0  # kW

# Wärmepumpe
heat_pump_cop_heating = 4.0
heat_pump_cop_cooling = 4.0

# Temperaturgrenzen - verschiedene Varianten testen
temperature_variants = [
    {"name": "Aktuell (2°C)", "t_fluid_min": 2.0},
    {"name": "Variante 1 (0°C)", "t_fluid_min": 0.0},
    {"name": "Variante 2 (-2°C)", "t_fluid_min": -2.0},
]

delta_t_fluid = 3.0
t_fluid_max = 15.0

print("TESTE VERSCHIEDENE TEMPERATURGRENZEN UND BOHRLOCHANZAHLEN")
print("=" * 80)
print()

for temp_variant in temperature_variants:
    print(f"\n{'='*80}")
    print(f"TEMPERATURVARIANTE: {temp_variant['name']}")
    print(f"{'='*80}")
    
    for n_boreholes in [2, 3, 4, 5]:
        result = calc.calculate_complete(
            ground_thermal_conductivity=ground_thermal_conductivity,
            ground_thermal_diffusivity=ground_thermal_diffusivity,
            t_undisturbed=t_undisturbed,
            borehole_diameter=borehole_diameter,
            borehole_depth_initial=borehole_depth_initial,
            n_boreholes=n_boreholes,
            r_borehole=r_borehole,
            annual_heating_demand=annual_heating_demand,
            peak_heating_load=peak_heating_load_corrected,  # KORRIGIERT: 16 kW
            annual_cooling_demand=annual_cooling_demand,
            peak_cooling_load=peak_cooling_load,
            heat_pump_cop_heating=heat_pump_cop_heating,
            heat_pump_cop_cooling=heat_pump_cop_cooling,
            t_fluid_min_required=temp_variant['t_fluid_min'],
            t_fluid_max_required=t_fluid_max,
            delta_t_fluid=delta_t_fluid
        )
        
        print(f"\n  {n_boreholes} Bohrungen:")
        print(f"    Erforderliche Sondenlänge: {result.required_depth_final:.2f} m")
        print(f"    Gesamtlänge: {result.required_depth_final * n_boreholes:.2f} m")
        print(f"    WP-Austrittstemp. (min): {result.t_wp_aus_heating_min:.2f} °C")
        
        if result.required_depth_final <= 100:
            print(f"    ✅ UNTER 100m - GEEIGNET!")
        else:
            print(f"    ❌ ÜBER 100m - ZU TIEF")

print("\n" + "=" * 80)
print("ZUSAMMENFASSUNG")
print("=" * 80)
print("\nBitte prüfen Sie die Debug-Datei für detaillierte Berechnungsschritte:")
print(f"  {debug_file}")
print("\nEmpfehlung: Verwenden Sie die Variante mit 2-3 Bohrungen unter 100m!")




