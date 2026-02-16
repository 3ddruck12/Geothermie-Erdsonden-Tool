# Changelog V3.4.0-beta1

> **Release: Februar 2026**
> **Schwerpunkt: Architektur-Refactoring & Code-Qualität**

## 🏗️ Architektur-Refactoring

Die God-Class `main_window_v3_professional.py` wurde von **4.648 auf 3.353 Zeilen** reduziert (−28%).

### Neue Module

| Modul | Beschreibung |
|-------|-------------|
| `gui/tabs/input_tab.py` | 12 Eingabesektionen + Event-Handler |
| `gui/tabs/results_tab.py` | Ergebnis-Anzeige |
| `gui/tabs/materials_tab.py` | Material, Hydraulik, 3 Analyse-Tabs |
| `gui/tabs/diagrams_tab.py` | 12 Plot-Funktionen |
| `gui/tabs/borefield_tab.py` | g-Funktionen + Bohrfeld-Visualisierung |
| `gui/controllers/calculation_controller.py` | Berechnung, Ergebnis, PDF/Text-Export |
| `gui/controllers/file_controller.py` | .get Import/Export, Bohranzeige-PDF |

### Entfernte Dateien

- `gui/main_window.py` (V1 GUI)
- `gui/main_window_extended.py` (V2 GUI)

## ✅ Unit-Tests

71 Tests mit pytest:

- `tests/test_thermal.py` – 16 Tests (thermische Widerstände)
- `tests/test_hydraulics.py` – 24 Tests (Druckverlust, Reynolds-Zahl)
- `tests/test_borehole.py` – 10 Tests (iterative Berechnung)
- `tests/test_validators.py` – 21 Tests (Input-Validierung)

## 🔄 CI/CD

- GitHub Actions `test.yml` auf pytest umgestellt
- Build-Pipeline bleibt unverändert (Windows EXE + Linux DEB)

## ⚙️ Sonstige Änderungen

- `main.py`: Fallback-Import-Kette entfernt (nur noch V3 Professional)
- `gui/__init__.py`: Exportiert `GeothermieGUIProfessional`
- Versionsnummer in GUI-Header, Statusleiste und Über-Dialog aktualisiert
