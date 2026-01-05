#!/usr/bin/env python3
"""Erweiterte Tests für VDI 4640 Berechnung."""

from calculations.vdi4640 import VDI4640Calculator
import os

debug_file = os.path.join(os.path.expanduser("~"), "vdi4640_extended_debug.log")
calc = VDI4640Calculator(debug=True, debug_file=debug_file)

print("=" * 80)
print("ERWEITERTE VDI 4640 BERECHNUNG")
print("=" * 80)
print()

# Parameter
ground_thermal_conductivity = 2.3
ground_thermal_diffusivity = 1.0e-6
t_undisturbed = 10.0
borehole_diameter = 152
borehole_depth_initial = 100.0

# Optimierter R_Bohrloch
r_borehole = 0.15  # Sehr optimiert (Thermobeton, optimale Geometrie)

annual_heating_demand = 33600
peak_heating_load = 16.0
heat_pump_cop_heating = 4.0
t_fluid_min = -2.0  # Konservativ
delta_t_fluid = 3.0

print(f"Parameter:")
print(f"  Spitzenlast: {peak_heating_load} kW")
print(f"  R_Bohrloch (optimiert): {r_borehole} m·K/W")
print(f"  T_Fluid_min: {t_fluid_min} °C")
print()

# Teste verschiedene Anzahlen
print("Berechnung mit verschiedenen Bohrlochanzahlen:")
print("-" * 80)

for n_boreholes in [2, 3, 4, 5, 6, 7, 8, 9, 10]:
    result = calc.calculate_complete(
        ground_thermal_conductivity=ground_thermal_conductivity,
        ground_thermal_diffusivity=ground_thermal_diffusivity,
        t_undisturbed=t_undisturbed,
        borehole_diameter=borehole_diameter,
        borehole_depth_initial=borehole_depth_initial,
        n_boreholes=n_boreholes,
        r_borehole=r_borehole,
        annual_heating_demand=annual_heating_demand,
        peak_heating_load=peak_heating_load,
        annual_cooling_demand=0.0,
        peak_cooling_load=0.0,
        heat_pump_cop_heating=heat_pump_cop_heating,
        heat_pump_cop_cooling=4.0,
        t_fluid_min_required=t_fluid_min,
        t_fluid_max_required=15.0,
        delta_t_fluid=delta_t_fluid
    )
    
    depth_per_borehole = result.required_depth_final
    total_length = depth_per_borehole * n_boreholes
    
    status = "✅" if depth_per_borehole <= 100 else "❌"
    
    print(f"{n_boreholes:2d} Bohrungen: {depth_per_borehole:6.2f} m/Bohrung, "
          f"Gesamt: {total_length:6.2f} m, "
          f"WP-Temp: {result.t_wp_aus_heating_min:5.2f} °C {status}")

print()
print("=" * 80)
print("VERGLEICH MIT VEREINFACHTER METHODE")
print("=" * 80)
print()
print("Vereinfachte Methode (55 W/m):")
print("  2× 99m = 198m Gesamtlänge")
print("  Entzugsleistung: 10,9 kW")
print()
print("VDI 4640 Methode (konservativ):")
print("  Erfordert deutlich mehr Sondenlänge aufgrund:")
print("  - Langzeit-Effekte (10 Jahre)")
print("  - Drei Lasttypen (Grundlast, periodisch, Spitzenlast)")
print("  - Höhere thermische Widerstände")




