# Changelog V3.4.0-beta1

> **Release: Februar 2026**
> **Schwerpunkt: Architektur-Refactoring, Monatliche Lastprofile & Code-Qualität**

## 🏗️ Phase 1 – Architektur-Refactoring

Die God-Class `main_window_v3_professional.py` wurde von **4.648 auf 3.353 Zeilen** reduziert (−28%).

### Neue Module

| Modul | Beschreibung |
|-------|-------------|
| `gui/tabs/input_tab.py` | 12 Eingabesektionen + Event-Handler |
| `gui/tabs/results_tab.py` | Ergebnis-Anzeige |
| `gui/tabs/materials_tab.py` | Material, Hydraulik, 3 Analyse-Tabs |
| `gui/tabs/diagrams_tab.py` | 12 Plot-Funktionen |
| `gui/tabs/borefield_tab.py` | g-Funktionen + Bohrfeld-Visualisierung |
| `gui/tabs/load_profiles_tab.py` | Monatliche Lastprofile, Warmwasser, Vorlagen |
| `gui/controllers/calculation_controller.py` | Berechnung, Ergebnis, PDF/Text-Export |
| `gui/controllers/file_controller.py` | .get Import/Export, Bohranzeige-PDF |

### Entfernte Dateien

- `gui/main_window.py` (V1 GUI)
- `gui/main_window_extended.py` (V2 GUI)

## 📊 Phase 2 – Monatliche Lastprofile

- **Neuer Tab „Lastprofile“**: 12×3 Tabelle (Monat | Heizlast | Kühllast)
- **Schnelleingabe**: Jahres-Heizen/Kühlen automatisch auf Monate verteilen
- **Vorlagen**: EFH, MFH, Büro, Gewerbe (aus `data/lastprofile_vorlagen.xml`)
- **Warmwasser (VDI 2067)**: 800 kWh/Person/Jahr, monatliche Faktoren
- **Lastprofil-Diagramme**: Gestapeltes Balkendiagramm, Liniendiagramm, Export PNG/PDF
- **Speichern/Laden**: Lastprofile in `.get`-Dateien integriert

## ✅ Unit-Tests

91 Tests mit pytest:

- `tests/test_thermal.py` – 16 Tests (thermische Widerstände)
- `tests/test_hydraulics.py` – 24 Tests (Druckverlust, Reynolds-Zahl)
- `tests/test_borehole.py` – 10 Tests (iterative Berechnung)
- `tests/test_validators.py` – 21 Tests (Input-Validierung)
- `tests/test_load_profiles.py` – 20 Tests (Lastprofile, VDI 2067, Vorlagen)

## 🔄 CI/CD

- GitHub Actions `test.yml` auf pytest umgestellt
- Build-Pipeline: Windows EXE + Linux DEB + AppImage

## ⚙️ Sonstige Änderungen

- `main.py`: Fallback-Import-Kette entfernt (nur noch V3 Professional)
- `utils/version.py`: Zentrale Versionsverwaltung aus VERSION-Datei
- Versionsnummer in GUI-Header, Statusleiste und Über-Dialog aus VERSION
