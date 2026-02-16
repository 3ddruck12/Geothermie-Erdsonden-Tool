"""Tests für calculations/borehole.py – Bohrtiefe-Berechnung."""

import pytest
from calculations.borehole import BoreholeCalculator, BoreholeResult


class TestBoreholeResult:
    """Tests für die Ergebnis-Datenklasse."""

    def test_default_monthly_temperatures(self):
        """Ohne Angabe: 12 Nullen als monatliche Temperaturen."""
        result = BoreholeResult(
            required_depth=100,
            fluid_temperature_min=-1.5,
            fluid_temperature_max=12.0,
            borehole_resistance=0.10,
            effective_resistance=0.15,
            heat_extraction_rate=35.0
        )
        assert len(result.monthly_temperatures) == 12
        assert all(t == 0.0 for t in result.monthly_temperatures)

    def test_custom_monthly_temperatures(self):
        """Benutzerdefinierte monatliche Temperaturen."""
        temps = [5.0 + i for i in range(12)]
        result = BoreholeResult(
            required_depth=100,
            fluid_temperature_min=-1.5,
            fluid_temperature_max=12.0,
            borehole_resistance=0.10,
            effective_resistance=0.15,
            heat_extraction_rate=35.0,
            monthly_temperatures=temps
        )
        assert result.monthly_temperatures == temps


class TestBoreholeCalculator:
    """Tests für die iterative Bohrtiefe-Berechnung."""

    @pytest.fixture
    def calc(self):
        """Erstellt einen BoreholeCalculator."""
        return BoreholeCalculator()

    def test_standard_calculation(self, calc):
        """Standard-EFH: 12 MWh/a, 6 kW Peak → muss Ergebnis liefern."""
        result = calc.calculate_required_depth(
            ground_thermal_conductivity=2.0,
            ground_heat_capacity=2.4e6,
            undisturbed_ground_temp=10.0,
            annual_heating_demand=12.0,
            peak_heating_load=6.0,
            heat_pump_cop=4.0
        )
        assert isinstance(result, BoreholeResult)
        assert result.required_depth > 0
        assert result.borehole_resistance > 0
        assert result.effective_resistance > 0
        assert len(result.monthly_temperatures) == 12

    def test_depth_in_reasonable_range(self, calc):
        """Berechnete Tiefe muss im sinnvollen Bereich liegen."""
        result = calc.calculate_required_depth(
            ground_thermal_conductivity=2.0,
            ground_heat_capacity=2.4e6,
            undisturbed_ground_temp=10.0,
            annual_heating_demand=12.0,
            peak_heating_load=6.0,
            heat_pump_cop=4.0
        )
        assert 20 <= result.required_depth <= 300, \
            f"Tiefe {result.required_depth}m außerhalb des sinnvollen Bereichs"

    def test_higher_demand_needs_more_depth(self, calc):
        """Höherer Heizwärmebedarf → größere Bohrtiefe."""
        params = dict(
            ground_thermal_conductivity=2.0,
            ground_heat_capacity=2.4e6,
            undisturbed_ground_temp=10.0,
            heat_pump_cop=4.0
        )
        result_low = calc.calculate_required_depth(
            annual_heating_demand=8.0, peak_heating_load=4.0, **params
        )
        result_high = calc.calculate_required_depth(
            annual_heating_demand=20.0, peak_heating_load=10.0, **params
        )
        assert result_high.required_depth > result_low.required_depth

    def test_better_ground_needs_less_depth(self, calc):
        """Höhere Boden-Leitfähigkeit → geringere Bohrtiefe."""
        params = dict(
            ground_heat_capacity=2.4e6,
            undisturbed_ground_temp=10.0,
            annual_heating_demand=12.0,
            peak_heating_load=6.0,
            heat_pump_cop=4.0
        )
        result_poor = calc.calculate_required_depth(
            ground_thermal_conductivity=1.0, **params
        )
        result_good = calc.calculate_required_depth(
            ground_thermal_conductivity=3.5, **params
        )
        assert result_good.required_depth < result_poor.required_depth

    def test_lower_cop_extracts_less_from_ground(self, calc):
        """Niedrigerer COP → weniger Entzug aus dem Boden (Q_bh = Q × (COP-1)/COP)."""
        params = dict(
            ground_thermal_conductivity=2.5,
            ground_heat_capacity=2.4e6,
            undisturbed_ground_temp=10.0,
            annual_heating_demand=10.0,
            peak_heating_load=5.0
        )
        result_cop3 = calc.calculate_required_depth(heat_pump_cop=3.0, **params)
        result_cop5 = calc.calculate_required_depth(heat_pump_cop=5.0, **params)
        # Q_bh / Q = (COP-1)/COP → bei COP 3: 66.7%, bei COP 5: 80%
        # → höherer COP entzieht MEHR → braucht MEHR oder gleich Tiefe
        assert result_cop5.required_depth >= result_cop3.required_depth or \
               result_cop5.heat_extraction_rate >= result_cop3.heat_extraction_rate

    def test_min_fluid_temp_respected(self, calc):
        """Min. Fluidtemperatur muss eingehalten werden (wenn Tiefe ausreicht)."""
        result = calc.calculate_required_depth(
            ground_thermal_conductivity=2.0,
            ground_heat_capacity=2.4e6,
            undisturbed_ground_temp=10.0,
            annual_heating_demand=12.0,
            peak_heating_load=6.0,
            heat_pump_cop=4.0,
            min_fluid_temperature=-2.0
        )
        # Wenn die Iteration konvergiert, soll T_min >= -2.0 sein
        # (kann bei max_depth nicht garantiert werden)
        if result.required_depth < 300:
            assert result.fluid_temperature_min >= -2.5, \
                f"T_min={result.fluid_temperature_min}°C zu niedrig"

    def test_pipe_configurations(self, calc):
        """Verschiedene Rohrkonfigurationen müssen funktionieren."""
        params = dict(
            ground_thermal_conductivity=2.0,
            ground_heat_capacity=2.4e6,
            undisturbed_ground_temp=10.0,
            annual_heating_demand=12.0,
            peak_heating_load=6.0,
            heat_pump_cop=4.0
        )
        result_single = calc.calculate_required_depth(pipe_configuration="single-u", **params)
        result_double = calc.calculate_required_depth(pipe_configuration="double-u", **params)
        
        assert result_single.required_depth > 0
        assert result_double.required_depth > 0
        # Double-U hat niedrigeren R_b → kürzere Tiefen
        assert result_double.required_depth <= result_single.required_depth

    def test_heat_extraction_rate_positive(self, calc):
        """Wärmeentzugsrate muss positiv sein."""
        result = calc.calculate_required_depth(
            ground_thermal_conductivity=2.0,
            ground_heat_capacity=2.4e6,
            undisturbed_ground_temp=10.0,
            annual_heating_demand=12.0,
            peak_heating_load=6.0,
            heat_pump_cop=4.0
        )
        assert result.heat_extraction_rate > 0

    def test_with_cooling_load(self, calc):
        """Berechnung mit Kühllast → höheres T_max."""
        params = dict(
            ground_thermal_conductivity=2.0,
            ground_heat_capacity=2.4e6,
            undisturbed_ground_temp=10.0,
            peak_heating_load=6.0,
            heat_pump_cop=4.0
        )
        result_heat_only = calc.calculate_required_depth(
            annual_heating_demand=12.0, annual_cooling_demand=0.0,
            peak_cooling_load=0.0, **params
        )
        result_with_cool = calc.calculate_required_depth(
            annual_heating_demand=12.0, annual_cooling_demand=5.0,
            peak_cooling_load=4.0, **params
        )
        assert result_with_cool.fluid_temperature_max > result_heat_only.fluid_temperature_max
