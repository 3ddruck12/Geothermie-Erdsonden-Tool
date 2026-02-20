"""Lastprofil-Vorlagen und VDI 2067 Warmwasser-Berechnung.

Lädt Vorlagen aus data/lastprofile_vorlagen.xml (wie soil_types, fluids, etc.).
Fallback auf eingebaute Werte, falls XML nicht gefunden wird.
"""

import os
import xml.etree.ElementTree as ET
from typing import List, Dict, Tuple, Optional

# Monatsnamen
MONTH_NAMES = [
    "Jan", "Feb", "Mär", "Apr", "Mai", "Jun",
    "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"
]

# Fallback-Werte (wenn XML nicht geladen werden kann)
_FALLBACK_EFH_HEATING = [
    0.155, 0.148, 0.125, 0.099, 0.064, 0.0,
    0.0, 0.0, 0.061, 0.087, 0.117, 0.144
]
_FALLBACK_EFH_COOLING = [
    0.0, 0.0, 0.0, 0.05, 0.15, 0.25,
    0.30, 0.25, 0.0, 0.0, 0.0, 0.0
]
_FALLBACK_DHW_FACTORS = [
    0.075, 0.072, 0.078, 0.082, 0.088, 0.092,
    0.084, 0.094, 0.090, 0.085, 0.080, 0.080
]
_FALLBACK_VDI2067_KWH = 800.0


class LoadProfilesDB:
    """Datenbank für Lastprofil-Vorlagen aus XML."""

    def __init__(self, xml_file: Optional[str] = None):
        if xml_file is None:
            current_dir = os.path.dirname(__file__)
            xml_file = os.path.join(current_dir, 'lastprofile_vorlagen.xml')
        self.xml_file = xml_file
        self.templates: Dict[str, Tuple[List[float], List[float]]] = {}
        self.dhw_factors: List[float] = _FALLBACK_DHW_FACTORS.copy()
        self.vdi2067_kwh_per_person: float = _FALLBACK_VDI2067_KWH
        self._load_from_xml()

    def _load_from_xml(self):
        """Lädt Lastprofile aus XML-Datei."""
        try:
            tree = ET.parse(self.xml_file)
            root = tree.getroot()

            for profile_elem in root.findall('load_profile'):
                name_elem = profile_elem.find('name')
                if name_elem is None:
                    continue
                name = name_elem.text.strip()

                h_factors = self._parse_month_list(profile_elem.find('heating_factors'))
                c_factors = self._parse_month_list(profile_elem.find('cooling_factors'))
                if h_factors and c_factors and len(h_factors) == 12 and len(c_factors) == 12:
                    self.templates[name] = (h_factors, c_factors)

            # Warmwasser-Faktoren
            dhw_elem = root.find('dhw_monthly_factors')
            if dhw_elem is not None:
                factors = self._parse_month_list(dhw_elem)
                if factors and len(factors) == 12:
                    self.dhw_factors = factors

            # VDI 2067
            vdi_elem = root.find('vdi2067')
            if vdi_elem is not None:
                kwh_elem = vdi_elem.find('kwh_per_person_year')
                if kwh_elem is not None:
                    self.vdi2067_kwh_per_person = float(kwh_elem.text)

        except FileNotFoundError:
            self._load_fallback()
        except Exception as e:
            print(f"⚠️ Lastprofil-Datenbank nicht geladen: {e}")
            self._load_fallback()

    def _parse_month_list(self, parent: Optional[ET.Element]) -> List[float]:
        """Parst 12 Monatswerte aus <month>-Elementen."""
        if parent is None:
            return []
        values = []
        for m in parent.findall('month'):
            try:
                values.append(float(m.text))
            except (ValueError, TypeError):
                values.append(0.0)
        return values if len(values) == 12 else []

    def _load_fallback(self):
        """Lädt Fallback-Vorlagen (eingebaut)."""
        self.templates = {
            "EFH (Einfamilienhaus)": (_FALLBACK_EFH_HEATING.copy(), _FALLBACK_EFH_COOLING.copy()),
            "MFH (Mehrfamilienhaus)": (
                [0.14, 0.135, 0.12, 0.10, 0.07, 0.02, 0.01, 0.01, 0.06, 0.09, 0.12, 0.125],
                [0.0, 0.0, 0.02, 0.08, 0.15, 0.22, 0.25, 0.23, 0.05, 0.0, 0.0, 0.0]
            ),
            "Büro": (
                [0.12, 0.12, 0.11, 0.09, 0.06, 0.02, 0.01, 0.01, 0.05, 0.10, 0.12, 0.19],
                [0.0, 0.0, 0.03, 0.08, 0.14, 0.18, 0.25, 0.23, 0.09, 0.0, 0.0, 0.0]
            ),
            "Gewerbe": (
                [0.11, 0.11, 0.10, 0.09, 0.06, 0.03, 0.02, 0.02, 0.06, 0.10, 0.12, 0.18],
                [0.0, 0.0, 0.04, 0.10, 0.15, 0.18, 0.25, 0.23, 0.05, 0.0, 0.0, 0.0]
            ),
        }
        self.dhw_factors = _FALLBACK_DHW_FACTORS.copy()
        self.vdi2067_kwh_per_person = _FALLBACK_VDI2067_KWH

    def get_template_names(self) -> List[str]:
        """Gibt alle Vorlagen-Namen zurück."""
        return list(self.templates.keys())

    def get_template(self, name: str) -> Tuple[List[float], List[float]]:
        """Gibt Heiz- und Kühlfaktoren für eine Vorlage zurück."""
        if name in self.templates:
            h, c = self.templates[name]
            return (h.copy(), c.copy())
        # Fallback auf EFH
        return (_FALLBACK_EFH_HEATING.copy(), _FALLBACK_EFH_COOLING.copy())


# Singleton-Instanz (lazy)
_db: Optional[LoadProfilesDB] = None


def _get_db() -> LoadProfilesDB:
    global _db
    if _db is None:
        _db = LoadProfilesDB()
    return _db


def get_load_profile_template(name: str) -> Tuple[List[float], List[float]]:
    """Gibt Heiz- und Kühlfaktoren für eine Vorlage zurück (lädt aus XML)."""
    return _get_db().get_template(name)


def get_load_profile_template_names() -> List[str]:
    """Gibt alle verfügbaren Vorlagen-Namen zurück."""
    return _get_db().get_template_names()


def calculate_dhw_demand_vdi2067(num_persons: int) -> float:
    """
    Berechnet Warmwasser-Bedarf nach VDI 2067 aus Personenzahl.

    Args:
        num_persons: Anzahl Personen im Haushalt

    Returns:
        Jahres-Warmwasserbedarf in kWh
    """
    if num_persons <= 0:
        return 0.0
    return num_persons * _get_db().vdi2067_kwh_per_person


def get_monthly_dhw_distribution(num_persons: int) -> List[float]:
    """
    Verteilt den Warmwasser-Bedarf auf 12 Monate.

    Returns:
        Liste mit 12 kWh-Werten pro Monat
    """
    annual = calculate_dhw_demand_vdi2067(num_persons)
    factors = _get_db().dhw_factors
    return [annual * f for f in factors]


def monthly_values_to_factors(values: List[float]) -> List[float]:
    """
    Konvertiert monatliche kWh-Werte in Faktoren (Anteile, Summe=1).

    Returns:
        12 Faktoren, oder [1/12]*12 wenn Summe=0
    """
    total = sum(values)
    if total <= 0:
        return [1.0 / 12.0] * 12
    return [v / total for v in values]


# Stunden pro Monat (Durchschnitt)
_HOURS_PER_MONTH = 730.0


def calculate_monthly_extraction_rate_w_per_m(
    monthly_heating_kwh: List[float],
    monthly_cooling_kwh: List[float],
    cop_heating: float,
    eer_cooling: float,
    total_borehole_length_m: float,
) -> Tuple[List[float], List[float], List[float]]:
    """
    Berechnet monatliche Entzugsleistung (W/m) als Zeitreihe.

    Heizen: Wärmeentzug aus dem Erdreich (positiv).
    Kühlen: Wärmeeintrag ins Erdreich (negativ, aus Sicht des Bodens).

    Args:
        monthly_heating_kwh: 12 Heizlast-Werte [kWh]
        monthly_cooling_kwh: 12 Kühllast-Werte [kWh]
        cop_heating: COP der Wärmepumpe (Heizen)
        eer_cooling: EER der Wärmepumpe (Kühlen)
        total_borehole_length_m: Gesamtlänge der Sonden [m]

    Returns:
        (heating_w_per_m, cooling_w_per_m, net_w_per_m)
        - heating_w_per_m: 12 Werte, Entzug beim Heizen [W/m]
        - cooling_w_per_m: 12 Werte, Eintrag beim Kühlen [W/m] (positiv)
        - net_w_per_m: 12 Werte, Netto (Entzug - Eintrag) [W/m]
    """
    if total_borehole_length_m <= 0:
        return ([0.0] * 12, [0.0] * 12, [0.0] * 12)

    # Heizen: (COP-1)/COP = Anteil aus Erdreich
    eff_heating = (cop_heating - 1) / cop_heating if cop_heating > 0 else 0
    # Kühlen: (EER+1)/EER = Abwärme ins Erdreich
    eff_cooling = (eer_cooling + 1) / eer_cooling if eer_cooling > 0 else 0

    heating_w_per_m = []
    cooling_w_per_m = []
    net_w_per_m = []

    for h_kwh, c_kwh in zip(monthly_heating_kwh, monthly_cooling_kwh):
        # Monatliche Leistung [W] = kWh * 1000 / Stunden
        p_heating = h_kwh * 1000.0 / _HOURS_PER_MONTH * eff_heating
        p_cooling = c_kwh * 1000.0 / _HOURS_PER_MONTH * eff_cooling

        h_wm = p_heating / total_borehole_length_m
        c_wm = p_cooling / total_borehole_length_m
        n_wm = h_wm - c_wm  # Entzug - Eintrag

        heating_w_per_m.append(h_wm)
        cooling_w_per_m.append(c_wm)
        net_w_per_m.append(n_wm)

    return (heating_w_per_m, cooling_w_per_m, net_w_per_m)


# Kompatibilität: LOAD_PROFILE_TEMPLATES für direkten Zugriff (z.B. Combobox)
def get_load_profile_templates_dict() -> Dict[str, Tuple[List[float], List[float]]]:
    """Gibt Vorlagen als Dict zurück (für Combobox values)."""
    db = _get_db()
    return {name: db.get_template(name) for name in db.get_template_names()}
