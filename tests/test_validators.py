"""Tests für utils/validators.py – Input-Validierung."""

import pytest
from utils.validators import (
    validate_parameter,
    validate_parameters,
    safe_float,
    PARAMETER_RANGES,
    ValidationError
)


class TestValidateParameter:
    """Tests für Einzelparameter-Validierung."""

    def test_valid_borehole_depth(self):
        """Gültige Bohrtiefe (100m)."""
        is_valid, msg = validate_parameter("borehole_depth", 100.0)
        assert is_valid
        assert msg == ""

    def test_depth_too_small(self):
        """Bohrtiefe unter Minimum."""
        is_valid, msg = validate_parameter("borehole_depth", 5.0)
        assert not is_valid
        assert "zu klein" in msg

    def test_depth_too_large(self):
        """Bohrtiefe über Maximum."""
        is_valid, msg = validate_parameter("borehole_depth", 500.0)
        assert not is_valid
        assert "zu groß" in msg

    def test_boundary_values(self):
        """Grenzwerte (min/max) sind erlaubt."""
        param = PARAMETER_RANGES["borehole_depth"]
        is_valid_min, _ = validate_parameter("borehole_depth", param.min_value)
        is_valid_max, _ = validate_parameter("borehole_depth", param.max_value)
        assert is_valid_min
        assert is_valid_max

    def test_unknown_key_is_valid(self):
        """Unbekannte Parameter werden nicht geprüft → gültig."""
        is_valid, msg = validate_parameter("unknown_param", 999.0)
        assert is_valid

    def test_all_parameters_have_ranges(self):
        """Alle definierten Parameter haben sinnvolle Bereiche."""
        for key, param in PARAMETER_RANGES.items():
            assert param.min_value < param.max_value, \
                f"{key}: min ({param.min_value}) >= max ({param.max_value})"
            assert param.min_value <= param.default <= param.max_value, \
                f"{key}: default ({param.default}) außerhalb [{param.min_value}, {param.max_value}]"

    def test_cop_range(self):
        """COP muss zwischen 2 und 8 liegen."""
        assert validate_parameter("heat_pump_cop", 4.0)[0]
        assert not validate_parameter("heat_pump_cop", 1.0)[0]
        assert not validate_parameter("heat_pump_cop", 10.0)[0]

    def test_ground_conductivity(self):
        """Wärmeleitfähigkeit Boden: 0.5-6.0 W/m·K."""
        assert validate_parameter("ground_thermal_conductivity", 2.0)[0]
        assert not validate_parameter("ground_thermal_conductivity", 0.1)[0]
        assert not validate_parameter("ground_thermal_conductivity", 10.0)[0]


class TestValidateParameters:
    """Tests für Multi-Parameter-Validierung."""

    def test_all_valid(self):
        """Alle Parameter gültig → leere Fehlerliste."""
        errors = validate_parameters({
            "borehole_depth": 100.0,
            "heat_pump_cop": 4.0,
            "ground_thermal_conductivity": 2.0
        })
        assert errors == []

    def test_multiple_errors(self):
        """Mehrere ungültige Parameter → mehrere Fehler."""
        errors = validate_parameters({
            "borehole_depth": 1.0,  # zu klein
            "heat_pump_cop": 20.0   # zu groß
        })
        assert len(errors) == 2

    def test_plausibility_pipe_dimensions(self):
        """Rohr: Innendurchmesser darf nicht negativ werden."""
        errors = validate_parameters({
            "pipe_outer_diameter": 20.0,  # 20mm Außen
            "pipe_thickness": 15.0        # 15mm Wand → Innendurchmesser negativ!
        })
        assert any("negativ" in e for e in errors)

    def test_plausibility_temperature(self):
        """T_min muss kleiner als T_max sein."""
        errors = validate_parameters({
            "min_fluid_temperature": 10.0,
            "max_fluid_temperature": 5.0
        })
        assert any("kleiner" in e for e in errors)

    def test_plausibility_ground_vs_fluid(self):
        """T_min_fluid sollte unter Bodentemperatur liegen."""
        errors = validate_parameters({
            "undisturbed_ground_temp": 10.0,
            "min_fluid_temperature": 15.0  # wärmer als Boden → sinnlos
        })
        assert any("Bodentemperatur" in e for e in errors)


class TestSafeFloat:
    """Tests für sichere Float-Konvertierung."""

    def test_normal_value(self):
        """Normaler Float-String."""
        assert safe_float("3.14") == pytest.approx(3.14)

    def test_comma_decimal(self):
        """Komma als Dezimaltrennzeichen (deutsch)."""
        assert safe_float("3,14") == pytest.approx(3.14)

    def test_with_spaces(self):
        """Leerzeichen werden entfernt."""
        assert safe_float("  3.14  ") == pytest.approx(3.14)

    def test_invalid_returns_default(self):
        """Ungültiger String → Standardwert."""
        assert safe_float("abc") == 0.0
        assert safe_float("abc", default=42.0) == 42.0

    def test_empty_returns_default(self):
        """Leerer String → Standardwert."""
        assert safe_float("") == 0.0

    def test_none_returns_default(self):
        """None → Standardwert."""
        assert safe_float(None) == 0.0

    def test_integer_string(self):
        """Ganzzahl-String → Float."""
        assert safe_float("42") == 42.0


class TestValidationError:
    """Tests für ValidationError."""

    def test_error_attributes(self):
        """Fehler hat Parameter und Wert."""
        err = ValidationError("Test-Fehler", parameter="depth", value=500)
        assert str(err) == "Test-Fehler"
        assert err.parameter == "depth"
        assert err.value == 500


class TestValidateGuiEntry:
    """Tests für GUI-Entry-Validierung mit Key-Mapping."""

    def test_valid_gui_entry(self):
        """Gültiger GUI-Entry-Wert."""
        from utils.validators import validate_gui_entry
        is_valid, msg = validate_gui_entry("ground_thermal_cond", 2.0)
        assert is_valid

    def test_invalid_gui_entry(self):
        """Ungültiger GUI-Entry-Wert."""
        from utils.validators import validate_gui_entry
        is_valid, msg = validate_gui_entry("ground_thermal_cond", 0.1)
        assert not is_valid
        assert "zu klein" in msg

    def test_unmapped_key_is_valid(self):
        """Nicht gemappter GUI-Key → gültig."""
        from utils.validators import validate_gui_entry
        is_valid, msg = validate_gui_entry("project_name", 999)
        assert is_valid

    def test_depth_mapping(self):
        """GUI-Key 'initial_depth' mappt auf 'borehole_depth'."""
        from utils.validators import validate_gui_entry
        is_valid, _ = validate_gui_entry("initial_depth", 100)
        assert is_valid
        is_valid, _ = validate_gui_entry("initial_depth", 5)
        assert not is_valid


class TestVDI4640Compliance:
    """Tests für VDI 4640 Normen-Compliance."""

    def test_valid_configuration(self):
        """Gültige Konfiguration → keine Warnungen."""
        from utils.validators import check_vdi4640_compliance
        results = check_vdi4640_compliance({
            "spacing_between": 6.0,
            "num_boreholes": 2,
            "min_fluid_temp": -1.0,
        })
        assert len(results) == 0

    def test_spacing_warning(self):
        """Bohrabstand < 6m → Warnung."""
        from utils.validators import check_vdi4640_compliance
        results = check_vdi4640_compliance({
            "spacing_between": 4.0,
            "num_boreholes": 2,
        })
        assert len(results) == 1
        assert results[0].level == "warning"
        assert "Bohrabstand" in results[0].message

    def test_spacing_error(self):
        """Bohrabstand < 3m → Fehler."""
        from utils.validators import check_vdi4640_compliance
        results = check_vdi4640_compliance({
            "spacing_between": 2.0,
            "num_boreholes": 2,
        })
        assert len(results) == 1
        assert results[0].level == "error"

    def test_single_borehole_no_spacing_check(self):
        """Einzelbohrung → kein Abstandscheck."""
        from utils.validators import check_vdi4640_compliance
        results = check_vdi4640_compliance({
            "spacing_between": 2.0,
            "num_boreholes": 1,
        })
        assert len(results) == 0

    def test_frost_protection_warning(self):
        """T_min ≤ -2°C → Warnung."""
        from utils.validators import check_vdi4640_compliance
        results = check_vdi4640_compliance({
            "min_fluid_temp": -2.0,
        })
        assert len(results) == 1
        assert results[0].level == "warning"
        assert "Frostgefahr" in results[0].message

    def test_frost_protection_ok(self):
        """T_min > -2°C → keine Warnung."""
        from utils.validators import check_vdi4640_compliance
        results = check_vdi4640_compliance({
            "min_fluid_temp": -1.0,
        })
        assert len(results) == 0

    def test_extraction_rate_warning(self):
        """Entzugsleistung > max → Warnung."""
        from utils.validators import check_vdi4640_compliance
        results = check_vdi4640_compliance(
            params={},
            soil_type="Sand",
            extraction_rate_wm=50.0  # > 40 W/m für Sand
        )
        assert len(results) == 1
        assert "Entzugsleistung" in results[0].message

    def test_extraction_rate_ok(self):
        """Entzugsleistung ≤ max → keine Warnung."""
        from utils.validators import check_vdi4640_compliance
        results = check_vdi4640_compliance(
            params={},
            soil_type="Granit",
            extraction_rate_wm=60.0  # ≤ 65 W/m für Granit
        )
        assert len(results) == 0

    def test_format_compliance_results_empty(self):
        """Leere Liste → Alle-OK-Meldung."""
        from utils.validators import format_compliance_results
        text = format_compliance_results([])
        assert "Alle Prüfungen bestanden" in text

    def test_format_compliance_results_with_warnings(self):
        """Warnungen werden formatiert."""
        from utils.validators import (
            check_vdi4640_compliance,
            format_compliance_results,
        )
        results = check_vdi4640_compliance({
            "spacing_between": 4.0,
            "num_boreholes": 2,
            "min_fluid_temp": -3.0,
        })
        text = format_compliance_results(results)
        assert "⚠️" in text
        assert "VDI 4640" in text

