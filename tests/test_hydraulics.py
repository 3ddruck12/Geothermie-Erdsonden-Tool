"""Tests für calculations/hydraulics.py – Hydraulische Berechnungen."""

import math
import pytest
from calculations.hydraulics import HydraulicsCalculator


class TestFlowRate:
    """Tests für Volumenstrom-Berechnung."""

    def test_standard_6kw_system(self):
        """6 kW Entzugsleistung, ΔT=3K, 25% Glykol → ~1.4 m³/h."""
        result = HydraulicsCalculator.calculate_required_flow_rate(
            heat_capacity_kw=6.0,
            temperature_difference=3.0,
            antifreeze_concentration=25
        )
        assert 'volume_flow_m3_h' in result
        assert 'volume_flow_l_min' in result
        assert 'mass_flow_kg_s' in result
        assert result['volume_flow_m3_h'] > 0
        # 6 kW / (4000 J/kg·K × 3 K) ≈ 0.5 kg/s ≈ 1.7 m³/h
        assert 0.5 < result['volume_flow_m3_h'] < 3.0

    def test_higher_power_needs_more_flow(self):
        """Höhere Leistung → höherer Volumenstrom."""
        flow_6kw = HydraulicsCalculator.calculate_required_flow_rate(6.0, 3.0, 25)
        flow_12kw = HydraulicsCalculator.calculate_required_flow_rate(12.0, 3.0, 25)
        assert flow_12kw['volume_flow_m3_h'] > flow_6kw['volume_flow_m3_h']

    def test_higher_delta_t_reduces_flow(self):
        """Höhere Temperaturdifferenz → niedrigerer Volumenstrom."""
        flow_3k = HydraulicsCalculator.calculate_required_flow_rate(6.0, 3.0, 25)
        flow_5k = HydraulicsCalculator.calculate_required_flow_rate(6.0, 5.0, 25)
        assert flow_5k['volume_flow_m3_h'] < flow_3k['volume_flow_m3_h']

    def test_unit_conversions_consistent(self):
        """Einheiten-Konversionen müssen konsistent sein."""
        result = HydraulicsCalculator.calculate_required_flow_rate(6.0, 3.0, 25)
        # m³/h zu l/min: × 1000 / 60
        expected_lmin = result['volume_flow_m3_h'] * 1000 / 60
        assert abs(result['volume_flow_l_min'] - expected_lmin) < 0.01

    def test_pure_water(self):
        """Reines Wasser (0% Glykol) hat höhere Wärmekapazität → weniger Durchfluss."""
        flow_0 = HydraulicsCalculator.calculate_required_flow_rate(6.0, 3.0, 0)
        flow_25 = HydraulicsCalculator.calculate_required_flow_rate(6.0, 3.0, 25)
        assert flow_0['volume_flow_m3_h'] < flow_25['volume_flow_m3_h']


class TestPressureDrop:
    """Tests für Druckverlust-Berechnung."""

    def test_standard_conditions(self):
        """200m Rohr, DN32 → messbare Druckverluste."""
        result = HydraulicsCalculator.calculate_pressure_drop(
            pipe_length=200,
            pipe_diameter=0.026,
            volume_flow_m3h=1.5,
            antifreeze_concentration=25
        )
        assert result['pressure_drop_bar'] > 0
        assert result['velocity_m_s'] > 0
        assert result['reynolds'] > 0
        assert result['flow_regime'] in ('laminar', 'turbulent')

    def test_longer_pipe_more_pressure_drop(self):
        """Längere Leitung → höherer Druckverlust (linear)."""
        dp_100 = HydraulicsCalculator.calculate_pressure_drop(100, 0.026, 1.5, 25)
        dp_200 = HydraulicsCalculator.calculate_pressure_drop(200, 0.026, 1.5, 25)
        assert dp_200['pressure_drop_bar'] > dp_100['pressure_drop_bar']

    def test_larger_diameter_less_pressure_drop(self):
        """Größerer Rohrdurchmesser → niedrigerer Druckverlust."""
        dp_26 = HydraulicsCalculator.calculate_pressure_drop(200, 0.026, 1.5, 25)
        dp_40 = HydraulicsCalculator.calculate_pressure_drop(200, 0.040, 1.5, 25)
        assert dp_40['pressure_drop_bar'] < dp_26['pressure_drop_bar']

    def test_zero_flow_returns_zero(self):
        """Kein Durchfluss → kein Druckverlust."""
        result = HydraulicsCalculator.calculate_pressure_drop(200, 0.026, 0.0, 25)
        assert result['pressure_drop_bar'] == 0.0
        assert result['velocity_m_s'] == 0.0

    def test_reynolds_number_range(self):
        """Reynolds-Zahl muss im physikalisch sinnvollen Bereich liegen."""
        result = HydraulicsCalculator.calculate_pressure_drop(200, 0.026, 1.5, 25)
        assert result['reynolds'] > 100, "Reynolds zu niedrig"
        assert result['reynolds'] < 50000, "Reynolds unrealistisch hoch"

    def test_unit_conversions(self):
        """bar/mbar/Pa müssen konsistent sein."""
        result = HydraulicsCalculator.calculate_pressure_drop(200, 0.026, 1.5, 25)
        assert abs(result['pressure_drop_mbar'] - result['pressure_drop_bar'] * 1000) < 0.01
        assert abs(result['pressure_drop_pa'] - result['pressure_drop_bar'] * 100000) < 1.0


class TestPumpPower:
    """Tests für Pumpenleistung."""

    def test_standard_calculation(self):
        """Typische Werte: 1.5 m³/h, 0.8 bar → ~60 W."""
        result = HydraulicsCalculator.calculate_pump_power(
            volume_flow_m3h=1.5,
            pressure_drop_bar=0.8,
            pump_efficiency=0.5
        )
        assert result['electric_power_w'] > 0
        assert result['hydraulic_power_w'] > 0
        assert result['electric_power_w'] > result['hydraulic_power_w']
        assert abs(result['electric_power_kw'] - result['electric_power_w'] / 1000) < 0.001

    def test_higher_efficiency_less_electric_power(self):
        """Höherer Wirkungsgrad → weniger elektrische Leistung."""
        p_50 = HydraulicsCalculator.calculate_pump_power(1.5, 0.8, 0.5)
        p_80 = HydraulicsCalculator.calculate_pump_power(1.5, 0.8, 0.8)
        assert p_80['electric_power_w'] < p_50['electric_power_w']
        # Hydraulische Leistung bleibt gleich
        assert abs(p_80['hydraulic_power_w'] - p_50['hydraulic_power_w']) < 0.01

    def test_zero_flow_zero_power(self):
        """Kein Durchfluss → keine Pumpenleistung."""
        result = HydraulicsCalculator.calculate_pump_power(0.0, 0.8, 0.5)
        assert result['hydraulic_power_w'] == 0.0


class TestSystemPressureDrop:
    """Tests für Gesamt-Systemdruckverlust."""

    def test_single_borehole(self):
        """1 Bohrung, 100m, Single-U."""
        result = HydraulicsCalculator.calculate_total_system_pressure_drop(
            borehole_depth=100,
            num_boreholes=1,
            num_circuits=1,
            pipe_inner_diameter=0.026,
            volume_flow_total_m3h=1.5,
            antifreeze_concentration=25
        )
        assert result['total_pressure_drop_bar'] > 0
        assert result['total_pressure_drop_mbar'] > 0
        assert result['pipe_length_per_circuit_m'] > 200  # min 2×100m + horizontal

    def test_more_boreholes_increases_pipe_length(self):
        """Mehr Bohrungen → längere Rohrleitungen → höherer Druckverlust."""
        dp_1 = HydraulicsCalculator.calculate_total_system_pressure_drop(
            100, 1, 1, 0.026, 1.5, 25
        )
        dp_2 = HydraulicsCalculator.calculate_total_system_pressure_drop(
            100, 2, 1, 0.026, 1.5, 25
        )
        assert dp_2['pipe_length_per_circuit_m'] > dp_1['pipe_length_per_circuit_m']

    def test_parallel_circuits_reduce_flow_per_circuit(self):
        """Parallele Kreise verteilen den Volumenstrom."""
        dp_1 = HydraulicsCalculator.calculate_total_system_pressure_drop(
            100, 2, 1, 0.026, 1.5, 25
        )
        dp_2 = HydraulicsCalculator.calculate_total_system_pressure_drop(
            100, 2, 2, 0.026, 1.5, 25
        )
        assert dp_2['volume_flow_per_circuit_m3h'] < dp_1['volume_flow_per_circuit_m3h']


class TestPumpEnergy:
    """Tests für Energieverbrauch-Prognose."""

    def test_constant_pump(self):
        """Konstante Pumpe: volle Leistung × Stunden."""
        result = HydraulicsCalculator.calculate_pump_energy_consumption(
            pump_power_w=100,
            annual_heating_hours=1800,
            electricity_price_per_kwh=0.30
        )
        assert result['annual_kwh'] == pytest.approx(180.0)  # 100W × 1800h / 1000
        assert result['annual_cost_eur'] == pytest.approx(54.0)  # 180 kWh × 0.30

    def test_regulated_pump_saves_energy(self):
        """Geregelte Pumpe verbraucht weniger Energie."""
        result_const = HydraulicsCalculator.calculate_pump_energy_consumption(
            100, 1800, 0.30, regulation_factor=1.0, pump_efficiency_curve="constant"
        )
        result_reg = HydraulicsCalculator.calculate_pump_energy_consumption(
            100, 1800, 0.30, regulation_factor=0.55, pump_efficiency_curve="regulated"
        )
        assert result_reg['annual_kwh'] < result_const['annual_kwh']

    def test_10_year_projection(self):
        """10-Jahres-Werte = 10 × Jahreswerte."""
        result = HydraulicsCalculator.calculate_pump_energy_consumption(100, 1800, 0.30)
        assert result['lifetime_10y_kwh'] == pytest.approx(result['annual_kwh'] * 10)
        assert result['lifetime_10y_cost_eur'] == pytest.approx(result['annual_cost_eur'] * 10)

    def test_regulated_comparison_in_constant_mode(self):
        """Im Konstantmodus: Vergleich mit geregelter Pumpe enthalten."""
        result = HydraulicsCalculator.calculate_pump_energy_consumption(
            100, 1800, 0.30, regulation_factor=1.0, pump_efficiency_curve="constant"
        )
        assert result['regulated']['savings_annual_eur'] > 0
        assert result['regulated']['payback_years'] is not None


class TestFluidProperties:
    """Tests für Fluid-Eigenschafts-Interpolation."""

    def test_known_concentration_25(self):
        """25% Glykol: exakter Tabellenwert."""
        props = HydraulicsCalculator._get_fluid_properties(25)
        assert props['density'] == 1033
        assert props['viscosity'] == 0.0037
        assert props['heat_capacity'] == 4000

    def test_pure_water(self):
        """0% Glykol = reines Wasser."""
        props = HydraulicsCalculator._get_fluid_properties(0)
        assert props['density'] == 1000
        assert props['heat_capacity'] == 4190

    def test_interpolation(self):
        """15% Glykol: interpoliert zwischen 10% und 20%."""
        props = HydraulicsCalculator._get_fluid_properties(15)
        # Muss zwischen 10% und 20% liegen
        props_10 = HydraulicsCalculator._get_fluid_properties(10)
        props_20 = HydraulicsCalculator._get_fluid_properties(20)
        assert props_10['density'] < props['density'] < props_20['density']
        assert props_10['viscosity'] < props['viscosity'] < props_20['viscosity']

    def test_clamping_at_boundaries(self):
        """Werte außerhalb des Bereichs werden auf Grenzen begrenzt."""
        props_neg = HydraulicsCalculator._get_fluid_properties(-5)
        props_0 = HydraulicsCalculator._get_fluid_properties(0)
        assert props_neg['density'] == props_0['density']

        props_50 = HydraulicsCalculator._get_fluid_properties(50)
        props_40 = HydraulicsCalculator._get_fluid_properties(40)
        assert props_50['density'] == props_40['density']
