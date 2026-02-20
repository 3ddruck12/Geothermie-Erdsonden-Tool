# Changelog V3.4.1-beta2

> **Release: Februar 2026**
> **Baut auf V3.4.0-beta2 auf**

## 🆕 Neue Features

### Monatliche Entzugsleistung (W/m) als Zeitreihe

- **Berechnung**: `calculate_monthly_extraction_rate_w_per_m()` in `data/load_profiles.py`
  - Heizen: Entzug aus Erdreich [W/m]
  - Kühlen: Eintrag ins Erdreich [W/m]
  - Berücksichtigt COP, EER und Gesamtsondenlänge
- **Lastprofile-Tab**: Live-Vorschau mit W/m-Zeitreihe (zweites Subplot)
- **Diagramme-Tab**: Neues Diagramm „Monatliche Entzugsleistung (W/m)“
- **Tests**: 4 neue Tests in `TestMonthlyExtractionRateWPerM`

## 🔧 Fixes

- **Build-Workflow**: Robuste Icon-Erstellung für DEB und AppImage (Fallback bei convert-Fehler)

## Vollständige Feature-Liste

Siehe [CHANGELOG_V3.4.0-beta1.md](CHANGELOG_V3.4.0-beta1.md) und [CHANGELOG_V3.4.0-beta2.md](CHANGELOG_V3.4.0-beta2.md).
