# Changelog V3.2.0

## 🚀 Version 3.2.0 - "Project Manager" (Januar 2026)

### 🆕 Neue Features

#### `.get` Dateiformat
- **Natives Projektformat**: JSON-basiertes, versioniertes Austauschformat
- **Komplett-Export**: Speichert alle Parameter, Berechnungen und Ergebnisse
- **Import/Export**: Strg+S zum Speichern, Strg+O zum Laden
- **Menschenlesbar**: JSON mit Formatierung und Kommentaren

#### Versionierung & Migration
- **Abwärtskompatibilität**: Automatische Migration von V3.0 und V3.1 Dateien
- **Versions-Tracking**: Jede Datei enthält Format-Version und Erstellungs-Info
- **Validierung**: Eingebaute Datei-Validierung mit Fehlerprüfung

#### pygfunction Integration
- **Bohrfeld-Simulationen**: g-Funktionen für Mehrfach-Bohrungen
- **Thermische Interaktion**: Berücksichtigung der gegenseitigen Beeinflussung
- **Langzeit-Prognose**: Temperaturentwicklung über 25+ Jahre
- **Flexible Layouts**: Rechteck, L-Form, U-Form, Linien-Anordnung

### 🔧 Verbesserungen

#### GUI
- **Neue Menüpunkte**: "Als .get speichern" und ".get Projekt laden"
- **Keyboard-Shortcuts**: Strg+S, Strg+O, Strg+P
- **V3.2 Info-Dialog**: Hilfe → V3.2 Features

#### Backend
- **Neue Module**:
  - `utils/get_file_handler.py`: Import/Export-Funktionalität
  - `calculations/borefield_gfunction.py`: pygfunction-Integration
- **Erweiterte Datenstrukturen**: Unterstützung für Bohrfeld-Konfigurationen

#### Dependencies
- **pygfunction[plot] >= 2.3.0**: Hinzugefügt für Bohrfeld-Berechnungen
- **SecondaryCoolantProps >= 1.3**: Automatisch mit pygfunction installiert
- **typing_extensions >= 4.11.0**: Für erweiterte Type Hints

### 📝 Dateiformat-Spezifikation

#### `.get` Struktur
```json
{
  "file_format": "GET",
  "format_version": "3.2",
  "metadata": { ... },
  "ground_properties": { ... },
  "borehole_config": { ... },
  "pipe_properties": { ... },
  "grout_material": { ... },
  "heat_carrier_fluid": { ... },
  "loads": { ... },
  "temperature_limits": { ... },
  "simulation_settings": { ... },
  "climate_data": { ... },
  "borefield_v32": {
    "enabled": true,
    "layout": "rectangle",
    "num_boreholes_x": 3,
    "num_boreholes_y": 2,
    ...
  },
  "results": { ... }
}
```

### 🧪 Tests

- **Vollständige Test-Suite**: `test_v32.py`
- **GET File Handler Tests**: Export, Import, Validierung, Migration
- **Bohrfeld-Tests**: Verschiedene Layouts und Konfigurationen
- **Migrations-Tests**: V3.0 → V3.2, V3.1 → V3.2

### 🐛 Bug Fixes

- Import von `Any` in `main_window_v3_professional.py` fehlte
- Titel auf "V3.2" aktualisiert

### 📚 Dokumentation

- **README aktualisiert**: V3.2 Features hinzugefügt
- **Schnellstart erweitert**: Projekt speichern/laden
- **Version-Badges**: 3.2.0 Badge hinzugefügt

### ⚠️ Breaking Changes

Keine! V3.2 ist vollständig abwärtskompatibel zu V3.0 und V3.1.

### 🔮 Ausblick V3.3

- **Bohrfeld-Tab**: Dedizierter Tab für Bohrfeld-Visualisierungen
- **g-Funktionen-Plots**: Interaktive Darstellung in GUI
- **Erweiterte Layouts**: Benutzerdefinierte Bohrfeld-Anordnungen
- **PDF-Integration**: Bohrfeld-Grafiken im Bericht

---

## Installation

```bash
# Python
pip install -r requirements.txt

# Neue Dependencies werden automatisch installiert:
# - pygfunction[plot]>=2.3.0
# - typing_extensions>=4.11.0
```

## Migration von V3.0/3.1

Einfach `.get` Datei öffnen - Migration erfolgt automatisch!

```python
from utils.get_file_handler import GETFileHandler

handler = GETFileHandler()
data = handler.import_from_get("old_v30_project.get")
# → Automatisch auf V3.2 migriert
```

---

**Vollständige Changelog**: [v3.1.0...v3.2.0](https://github.com/3ddruck12/GeothermieErdsondentool/compare/v3.1.0...v3.2.0)
