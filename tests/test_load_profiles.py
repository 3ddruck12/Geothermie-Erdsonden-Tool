"""Tests für data/load_profiles.py – Phase 2 Lastprofile.

Validiert:
- Lastprofil-Vorlagen (12 Faktoren, Summe = 1.0)
- VDI 2067 Warmwasser-Berechnung
- monthly_values_to_factors
- Integration mit VDI 4640
"""

import pytest
from data.load_profiles import (
    LoadProfilesDB,
    get_load_profile_template,
    get_load_profile_template_names,
    calculate_dhw_demand_vdi2067,
    get_monthly_dhw_distribution,
    monthly_values_to_factors,
    calculate_monthly_extraction_rate_w_per_m,
    MONTH_NAMES,
)


class TestLoadProfileTemplates:
    """Vorlagen: 12 Faktoren pro Monat, Summe = 1.0."""

    def test_efh_heating_factors_sum_to_one(self):
        """EFH Heizfaktoren summieren sich zu 1.0."""
        h, c = get_load_profile_template("EFH (Einfamilienhaus)")
        assert len(h) == 12
        assert abs(sum(h) - 1.0) < 1e-6

    def test_efh_cooling_factors_sum_to_one(self):
        """EFH Kühlfaktoren summieren sich zu 1.0."""
        h, c = get_load_profile_template("EFH (Einfamilienhaus)")
        assert len(c) == 12
        assert abs(sum(c) - 1.0) < 1e-6

    def test_all_templates_valid(self):
        """Alle Vorlagen: Heiz- und Kühlfaktoren summieren zu 1.0."""
        for name in get_load_profile_template_names():
            h, c = get_load_profile_template(name)
            assert abs(sum(h) - 1.0) < 1e-6, f"{name}: Heiz-Summe != 1"
            assert abs(sum(c) - 1.0) < 1e-6, f"{name}: Kühl-Summe != 1"

    def test_factors_non_negative(self):
        """Alle Faktoren sind >= 0."""
        for name in get_load_profile_template_names():
            h, c = get_load_profile_template(name)
            assert all(f >= 0 for f in h + c), f"{name}: negative Faktoren"

    def test_efh_heating_peak_in_winter(self):
        """EFH: Heizlast im Winter (Jan–Mär) höher als im Sommer."""
        h, _ = get_load_profile_template("EFH (Einfamilienhaus)")
        winter = sum(h[0:3])
        summer = sum(h[5:8])
        assert winter > summer

    def test_efh_cooling_peak_in_summer(self):
        """EFH: Kühllast im Sommer höher als im Winter."""
        _, c = get_load_profile_template("EFH (Einfamilienhaus)")
        summer = sum(c[5:8])
        winter = sum(c[0:3])
        assert summer > winter

    def test_template_names_not_empty(self):
        """Mindestens 4 Vorlagen vorhanden."""
        names = get_load_profile_template_names()
        assert len(names) >= 4
        assert "EFH (Einfamilienhaus)" in names
        assert "MFH (Mehrfamilienhaus)" in names


class TestVDI2067Dhw:
    """VDI 2067 Warmwasser-Berechnung."""

    def test_zero_persons_returns_zero(self):
        """0 Personen → 0 kWh."""
        assert calculate_dhw_demand_vdi2067(0) == 0.0

    def test_negative_persons_returns_zero(self):
        """Negative Personenzahl → 0 kWh."""
        assert calculate_dhw_demand_vdi2067(-1) == 0.0

    def test_four_persons_returns_3200(self):
        """4 Personen → 3200 kWh (4 × 800)."""
        assert calculate_dhw_demand_vdi2067(4) == 3200.0

    def test_monthly_dhw_distribution_sums_to_annual(self):
        """Monatliche Verteilung summiert zum Jahresbedarf."""
        annual = calculate_dhw_demand_vdi2067(4)
        monthly = get_monthly_dhw_distribution(4)
        assert len(monthly) == 12
        assert abs(sum(monthly) - annual) < 1e-6

    def test_monthly_dhw_has_12_values(self):
        """Monatliche Warmwasser-Verteilung hat 12 Werte."""
        monthly = get_monthly_dhw_distribution(4)
        assert len(monthly) == 12
        assert all(v >= 0 for v in monthly)


class TestMonthlyValuesToFactors:
    """Konvertierung kWh → Faktoren (Anteile)."""

    def test_factors_sum_to_one(self):
        """Faktoren summieren sich zu 1.0."""
        vals = [100, 200, 0, 0, 0, 0, 0, 0, 0, 50, 100, 150]
        factors = monthly_values_to_factors(vals)
        assert len(factors) == 12
        assert abs(sum(factors) - 1.0) < 1e-6

    def test_zero_total_returns_uniform(self):
        """Summe = 0 → alle Faktoren 1/12."""
        factors = monthly_values_to_factors([0.0] * 12)
        assert all(abs(f - 1.0 / 12.0) < 1e-6 for f in factors)

    def test_single_month_nonzero(self):
        """Nur ein Monat mit Wert → ein Faktor = 1, Rest = 0."""
        vals = [0.0] * 12
        vals[3] = 1000.0
        factors = monthly_values_to_factors(vals)
        assert abs(factors[3] - 1.0) < 1e-6
        assert all(abs(f) < 1e-6 for i, f in enumerate(factors) if i != 3)


class TestLoadProfilesDB:
    """Datenbank lädt XML oder Fallback."""

    def test_loads_templates(self):
        """Datenbank lädt mindestens 4 Vorlagen."""
        db = LoadProfilesDB()
        assert len(db.get_template_names()) >= 4

    def test_unknown_template_returns_efh(self):
        """Unbekannte Vorlage → Fallback auf EFH."""
        h, c = get_load_profile_template("UnbekannteVorlage123")
        assert len(h) == 12 and len(c) == 12
        assert abs(sum(h) - 1.0) < 1e-6
        assert abs(sum(c) - 1.0) < 1e-6

    def test_dhw_factors_sum_to_one(self):
        """Warmwasser-Monatsfaktoren summieren zu 1.0."""
        db = LoadProfilesDB()
        assert len(db.dhw_factors) == 12
        assert abs(sum(db.dhw_factors) - 1.0) < 1e-6


class TestMonthNames:
    """MONTH_NAMES Konstante."""

    def test_twelve_months(self):
        """12 Monatsnamen definiert."""
        assert len(MONTH_NAMES) == 12


class TestMonthlyExtractionRateWPerM:
    """Monatliche Entzugsleistung (W/m) als Zeitreihe."""

    def test_zero_length_returns_zeros(self):
        """total_borehole_length_m=0 → alle W/m = 0."""
        h = [1000.0] * 12
        c = [0.0] * 12
        h_wm, c_wm, net = calculate_monthly_extraction_rate_w_per_m(
            h, c, cop_heating=4.0, eer_cooling=4.0, total_borehole_length_m=0
        )
        assert all(v == 0 for v in h_wm + c_wm + net)

    def test_heating_only_positive_w_per_m(self):
        """Nur Heizen → positive Entzugsleistung."""
        h = [1000.0] + [0.0] * 11
        c = [0.0] * 12
        h_wm, c_wm, net = calculate_monthly_extraction_rate_w_per_m(
            h, c, cop_heating=4.0, eer_cooling=4.0, total_borehole_length_m=100.0
        )
        assert h_wm[0] > 0
        assert c_wm[0] == 0
        assert net[0] > 0

    def test_returns_twelve_values_each(self):
        """Gibt 12 Werte pro Rückgabetyp zurück."""
        h = [100.0] * 12
        c = [50.0] * 12
        h_wm, c_wm, net = calculate_monthly_extraction_rate_w_per_m(
            h, c, cop_heating=4.0, eer_cooling=4.0, total_borehole_length_m=100.0
        )
        assert len(h_wm) == 12
        assert len(c_wm) == 12
        assert len(net) == 12

    def test_net_is_heating_minus_cooling(self):
        """Netto = Heiz-Entzug minus Kühl-Eintrag."""
        h = [1000.0] * 12
        c = [500.0] * 12
        h_wm, c_wm, net = calculate_monthly_extraction_rate_w_per_m(
            h, c, cop_heating=4.0, eer_cooling=4.0, total_borehole_length_m=100.0
        )
        for i in range(12):
            assert abs(net[i] - (h_wm[i] - c_wm[i])) < 1e-6


class TestLoadProfilesIntegration:
    """Integration mit VDI 4640."""

    def test_vdi4640_accepts_monthly_factors(self):
        """VDI 4640 akzeptiert monatliche Faktoren aus Lastprofil."""
        from calculations.vdi4640 import VDI4640Calculator

        h_factors, c_factors = get_load_profile_template("EFH (Einfamilienhaus)")
        calc = VDI4640Calculator(debug=False)

        result = calc.calculate_complete(
            ground_thermal_conductivity=2.0,
            ground_thermal_diffusivity=1.0e-6,
            t_undisturbed=10.0,
            borehole_diameter=152,
            borehole_depth_initial=100.0,
            n_boreholes=1,
            r_borehole=0.1,
            annual_heating_demand=12000,
            peak_heating_load=6.0,
            annual_cooling_demand=0,
            peak_cooling_load=0.0,
            monthly_heating_factors=h_factors,
            monthly_cooling_factors=c_factors,
            heat_pump_cop_heating=4.0,
            heat_pump_cop_cooling=4.0,
            t_fluid_min_required=-2.0,
            t_fluid_max_required=35.0,
        )

        assert result.required_depth_final > 0
        assert result.design_case == "heating"
