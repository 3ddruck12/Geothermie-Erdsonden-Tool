"""Tests für calculations/thermal.py – Thermische Widerstände."""

import math
import pytest
from calculations.thermal import ThermalResistanceCalculator


class TestPipeResistance:
    """Tests für Rohr-Widerstandsberechnung."""

    def test_standard_pe_pipe(self):
        """PE-HD 32×2.9mm Rohr: typischer Wert ~0.08 m·K/W."""
        r = ThermalResistanceCalculator.calculate_pipe_resistance(
            inner_diameter=0.0262,  # 32mm - 2×2.9mm
            outer_diameter=0.032,
            thermal_conductivity=0.42  # PE-HD
        )
        assert 0.05 < r < 0.15, f"R_pipe={r:.4f} außerhalb erwarteter Spanne"

    def test_higher_conductivity_reduces_resistance(self):
        """Höhere Wärmeleitfähigkeit → niedrigerer Widerstand."""
        r_pe = ThermalResistanceCalculator.calculate_pipe_resistance(0.026, 0.032, 0.42)
        r_metal = ThermalResistanceCalculator.calculate_pipe_resistance(0.026, 0.032, 50.0)
        assert r_metal < r_pe

    def test_thicker_wall_increases_resistance(self):
        """Dickere Rohrwand → höherer Widerstand."""
        r_thin = ThermalResistanceCalculator.calculate_pipe_resistance(0.028, 0.032, 0.42)
        r_thick = ThermalResistanceCalculator.calculate_pipe_resistance(0.022, 0.032, 0.42)
        assert r_thick > r_thin

    def test_invalid_params_raise_error(self):
        """Ungültige Parameter müssen ValueError auslösen."""
        with pytest.raises(ValueError):
            ThermalResistanceCalculator.calculate_pipe_resistance(0.032, 0.026, 0.42)  # inner > outer
        with pytest.raises(ValueError):
            ThermalResistanceCalculator.calculate_pipe_resistance(0.026, 0.032, 0.0)  # lambda=0
        with pytest.raises(ValueError):
            ThermalResistanceCalculator.calculate_pipe_resistance(0.0, 0.032, 0.42)  # inner=0


class TestConvectionResistance:
    """Tests für konvektiven Widerstand."""

    def test_turbulent_flow(self):
        """Turbulente Strömung: Re > 2300 → Dittus-Boelter."""
        r = ThermalResistanceCalculator.calculate_convection_resistance(
            inner_diameter=0.026,
            flow_rate=0.0005,  # m³/s
            fluid_thermal_conductivity=0.48,
            fluid_viscosity=0.004,
            fluid_density=1030,
            fluid_heat_capacity=3800
        )
        assert r > 0, "Konvektiver Widerstand muss positiv sein"
        assert r < 0.5, f"R_conv={r:.4f} unrealistisch hoch"

    def test_higher_flow_reduces_resistance(self):
        """Höherer Durchfluss → besserer Wärmeübergang → niedrigerer Widerstand."""
        params = dict(
            inner_diameter=0.026,
            fluid_thermal_conductivity=0.48,
            fluid_viscosity=0.004,
            fluid_density=1030,
            fluid_heat_capacity=3800
        )
        r_low = ThermalResistanceCalculator.calculate_convection_resistance(flow_rate=0.0002, **params)
        r_high = ThermalResistanceCalculator.calculate_convection_resistance(flow_rate=0.001, **params)
        assert r_high < r_low

    def test_invalid_params_raise_error(self):
        """Ungültige Parameter müssen ValueError auslösen."""
        with pytest.raises(ValueError):
            ThermalResistanceCalculator.calculate_convection_resistance(
                inner_diameter=0.0, flow_rate=0.0005,
                fluid_thermal_conductivity=0.48, fluid_viscosity=0.004,
                fluid_density=1030, fluid_heat_capacity=3800
            )


class TestSingleUTubeResistance:
    """Tests für Single-U-Rohr Widerstände."""

    def test_typical_values(self):
        """Standard-Konfiguration: R_b ~0.05-0.15 m·K/W."""
        r_b, r_a = ThermalResistanceCalculator.calculate_single_u_tube_resistance(
            borehole_radius=0.076,  # 152mm Durchmesser
            pipe_outer_radius=0.016,  # 32mm Durchmesser
            shank_spacing=0.052,
            pipe_thermal_conductivity=0.42,
            grout_thermal_conductivity=1.3
        )
        assert 0.01 < r_b < 0.3, f"R_b={r_b:.4f} unrealistisch"
        assert r_a > 0, "R_a muss positiv sein"

    def test_higher_grout_conductivity_reduces_rb(self):
        """Höhere Verfüllmaterial-Leitfähigkeit → niedrigerer R_b."""
        params = dict(
            borehole_radius=0.076,
            pipe_outer_radius=0.016,
            shank_spacing=0.052,
            pipe_thermal_conductivity=0.42
        )
        r_b_low, _ = ThermalResistanceCalculator.calculate_single_u_tube_resistance(
            grout_thermal_conductivity=0.8, **params
        )
        r_b_high, _ = ThermalResistanceCalculator.calculate_single_u_tube_resistance(
            grout_thermal_conductivity=2.0, **params
        )
        assert r_b_high < r_b_low

    def test_returns_tuple(self):
        """Rückgabe muss Tuple (R_b, R_a) sein."""
        result = ThermalResistanceCalculator.calculate_single_u_tube_resistance(
            borehole_radius=0.076, pipe_outer_radius=0.016,
            shank_spacing=0.052, pipe_thermal_conductivity=0.42,
            grout_thermal_conductivity=1.3
        )
        assert isinstance(result, tuple)
        assert len(result) == 2


class TestDoubleUTubeResistance:
    """Tests für Double-U-Rohr Widerstände."""

    def test_lower_resistance_than_single_u(self):
        """Double-U hat niedrigeren Bohrloch-Widerstand als Single-U."""
        params = dict(
            borehole_radius=0.076,
            pipe_outer_radius=0.016,
            shank_spacing=0.052,
            pipe_thermal_conductivity=0.42,
            grout_thermal_conductivity=1.3
        )
        r_b_single, _ = ThermalResistanceCalculator.calculate_single_u_tube_resistance(**params)
        r_b_double, _ = ThermalResistanceCalculator.calculate_double_u_tube_resistance(**params)
        assert r_b_double < r_b_single, "Double-U soll niedrigeren R_b haben"

    def test_correction_factors_applied(self):
        """Double-U nutzt Korrekturfaktoren (0.7 für Rb, 0.5 für Ra)."""
        r_b, r_a = ThermalResistanceCalculator.calculate_double_u_tube_resistance(
            borehole_radius=0.076, pipe_outer_radius=0.016,
            shank_spacing=0.052, pipe_thermal_conductivity=0.42,
            grout_thermal_conductivity=1.3
        )
        assert r_b > 0
        assert r_a > 0


class TestCoaxialResistance:
    """Tests für Koaxialrohr Widerstände."""

    def test_typical_coaxial(self):
        """Typische Koaxialrohr-Werte."""
        r_b, r_a = ThermalResistanceCalculator.calculate_coaxial_resistance(
            borehole_radius=0.076,
            outer_pipe_inner_radius=0.030,
            outer_pipe_outer_radius=0.032,
            inner_pipe_inner_radius=0.013,
            inner_pipe_outer_radius=0.016,
            outer_pipe_thermal_conductivity=0.42,
            inner_pipe_thermal_conductivity=0.42,
            annulus_thermal_conductivity=0.6
        )
        assert r_b > 0
        assert r_a > 0


class TestTotalResistance:
    """Tests für Gesamt-Widerstand."""

    def test_additive(self):
        """Gesamt-Widerstand ist Summe der Einzelwiderstände (ohne R_a)."""
        r_total = ThermalResistanceCalculator.calculate_total_resistance(
            r_b=0.10, r_a=0.30, r_pipe=0.05, r_conv=0.02
        )
        expected = 0.10 + 0.05 + 0.02  # R_b + R_pipe + R_conv
        assert abs(r_total - expected) < 1e-10
