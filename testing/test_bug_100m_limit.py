#!/usr/bin/env python3
"""Test um den Bug mit der 100m-Begrenzung zu finden."""

from calculations.vdi4640 import VDI4640Calculator
import os
import math

calc = VDI4640Calculator(debug=False)

# Parameter
params = {
    "ground_thermal_cond": 2.3,
    "ground_thermal_diffusivity": 1.0e-6,
    "ground_temp": 10.0,
    "borehole_diameter": 152,
    "initial_depth": 100.0,
    "annual_heating": 33600,
    "peak_heating": 12.0,
    "heat_pump_cop": 4.0,
    "min_fluid_temp": 2.0,
    "max_fluid_temp": 15.0,
    "delta_t_fluid": 3.0,
    "r_borehole": 0.235142
}

print("=" * 80)
print("TEST: Berechnung mit verschiedenen Bohrlochanzahlen")
print("=" * 80)
print()

# Test 1: Ohne 100m-Begrenzung (wie vorher)
print("OHNE 100m-BEGRENZUNG (wie vorher):")
print("-" * 80)
result_2 = calc.calculate_complete(
    ground_thermal_conductivity=params["ground_thermal_cond"],
    ground_thermal_diffusivity=params["ground_thermal_diffusivity"],
    t_undisturbed=params["ground_temp"],
    borehole_diameter=params["borehole_diameter"],
    borehole_depth_initial=params["initial_depth"],
    n_boreholes=2,
    r_borehole=params["r_borehole"],
    annual_heating_demand=params["annual_heating"],
    peak_heating_load=params["peak_heating"],
    annual_cooling_demand=0.0,
    peak_cooling_load=0.0,
    heat_pump_cop_heating=params["heat_pump_cop"],
    heat_pump_cop_cooling=4.0,
    t_fluid_min_required=params["min_fluid_temp"],
    t_fluid_max_required=params["max_fluid_temp"],
    delta_t_fluid=params["delta_t_fluid"]
)

print(f"2 Bohrungen: {result_2.required_depth_final:.2f} m pro Bohrung")
print(f"  Gesamtlänge: {result_2.required_depth_final * 2:.2f} m")
print()

# Test 2: Mit 100m-Begrenzung (aktuelle Logik)
print("MIT 100m-BEGRENZUNG (aktuelle Logik):")
print("-" * 80)
max_depth = 100.0
original_num = 2

# Berechne neue Anzahl
new_num = int(math.ceil(result_2.required_depth_final * original_num / max_depth))
print(f"Erforderliche Tiefe: {result_2.required_depth_final:.2f} m")
print(f"Berechnete neue Anzahl: {new_num} Bohrungen")
print()

# Neu berechnen mit neuer Anzahl
result_new = calc.calculate_complete(
    ground_thermal_conductivity=params["ground_thermal_cond"],
    ground_thermal_diffusivity=params["ground_thermal_diffusivity"],
    t_undisturbed=params["ground_temp"],
    borehole_diameter=params["borehole_diameter"],
    borehole_depth_initial=params["initial_depth"],  # PROBLEM: Immer noch 100m!
    n_boreholes=new_num,
    r_borehole=params["r_borehole"],
    annual_heating_demand=params["annual_heating"],
    peak_heating_load=params["peak_heating"],
    annual_cooling_demand=0.0,
    peak_cooling_load=0.0,
    heat_pump_cop_heating=params["heat_pump_cop"],
    heat_pump_cop_cooling=4.0,
    t_fluid_min_required=params["min_fluid_temp"],
    t_fluid_max_required=params["max_fluid_temp"],
    delta_t_fluid=params["delta_t_fluid"]
)

print(f"{new_num} Bohrungen: {result_new.required_depth_final:.2f} m pro Bohrung")
print(f"  Gesamtlänge: {result_new.required_depth_final * new_num:.2f} m")
print()

# Test 3: Mit korrigiertem Startwert
print("MIT KORRIGIERTEM STARTWERT (besser):")
print("-" * 80)
# Verwende die berechnete Tiefe als neuen Startwert
result_corrected = calc.calculate_complete(
    ground_thermal_conductivity=params["ground_thermal_cond"],
    ground_thermal_diffusivity=params["ground_thermal_diffusivity"],
    t_undisturbed=params["ground_temp"],
    borehole_diameter=params["borehole_diameter"],
    borehole_depth_initial=result_new.required_depth_final,  # KORRIGIERT: Verwende berechnete Tiefe
    n_boreholes=new_num,
    r_borehole=params["r_borehole"],
    annual_heating_demand=params["annual_heating"],
    peak_heating_load=params["peak_heating"],
    annual_cooling_demand=0.0,
    peak_cooling_load=0.0,
    heat_pump_cop_heating=params["heat_pump_cop"],
    heat_pump_cop_cooling=4.0,
    t_fluid_min_required=params["min_fluid_temp"],
    t_fluid_max_required=params["max_fluid_temp"],
    delta_t_fluid=params["delta_t_fluid"]
)

print(f"{new_num} Bohrungen (korrigiert): {result_corrected.required_depth_final:.2f} m pro Bohrung")
print(f"  Gesamtlänge: {result_corrected.required_depth_final * new_num:.2f} m")
print()

print("=" * 80)
print("PROBLEM IDENTIFIZIERT:")
print("=" * 80)
print("Die thermischen Widerstände werden mit dem Startwert (100m) berechnet,")
print("auch wenn die tatsächliche Tiefe viel niedriger ist (92.77m).")
print("Das führt zu falschen Ergebnissen bei der Neuberechnung!")

