# Changelog v3.3.0-beta3

**Datum:** Januar 2026  
**Version:** 3.3.0-beta3  
**Status:** 🧪 BETA - Für Testing und Validierung

---

## 🎯 Hauptfeatures

### Erweiterte Diagramme (12 Diagramme)

Alle Diagramme werden jetzt untereinander in einem scrollbaren Tab angezeigt und automatisch in PDF-Berichte integriert.

#### Hydraulik-Diagramme (6)

1. **Pumpen-Kennlinien**
   - H-Q-Kurve (Förderhöhe vs. Volumenstrom)
   - Betriebspunkt-Markierung
   - Vergleich mehrerer Pumpen
   - Nutzt Pumpen-Datenbank

2. **Reynolds-Kurve**
   - Reynolds-Zahl vs. Volumenstrom
   - Verschiedene Glykol-Konzentrationen (0%, 25%, 30%, 40%)
   - Turbulenz-Grenze (Re=2300) markiert
   - Warnung bei laminarer Strömung

3. **Druckverlust-Komponenten**
   - Tortendiagramm: Prozentuale Anteile
   - Balkendiagramm: Absolute Werte
   - Aufschlüsselung: Bohrungen, Horizontal, Formstücke, Wärmetauscher

4. **Volumenstrom vs. Druckverlust**
   - Solekreis-Kennlinie
   - Betriebspunkt-Markierung
   - Vergleich verschiedener Konfigurationen

5. **Pumpenleistung über Betriebszeit**
   - Monatliche Energieverbrauch-Verteilung
   - Jahresverbrauch und Kosten
   - Saisonale Betriebsstunden

6. **Temperaturspreizung Sole**
   - ΔT vs. Volumenstrom
   - Optimaler Bereich (2-4 K) markiert
   - Betriebspunkt-Visualisierung

#### Wärmepumpen-Diagramme (3)

7. **COP vs. Sole-Eintrittstemperatur**
   - COP-Kurve über Eintrittstemperatur
   - Betriebspunkt-Markierung
   - Einfluss der Temperatur auf Effizienz

8. **COP vs. Vorlauftemperatur**
   - COP-Kurve über Vorlauftemperatur
   - Betriebspunkt-Markierung
   - Optimierungsmöglichkeiten

9. **JAZ-Abschätzung**
   - Jahresarbeitszahl-Visualisierung
   - Vergleich: Optimistisch, Realistisch, Pessimistisch
   - Energieverbrauch-Annotation

#### Energie-Diagramm (1)

10. **Energieverbrauch-Vergleich**
    - Konstante vs. Geregelte Pumpe
    - 10-Jahres-Kosten-Vergleich
    - Einsparung visualisiert

#### Bestehende Diagramme (2)

11. **Monatliche Temperaturen** (bereits vorhanden)
12. **Bohrloch-Schema** (bereits vorhanden)

---

## 🎨 GUI-Verbesserungen

### Diagramm-Tab komplett überarbeitet

- **Scrollbarer Bereich**: Alle 12 Diagramme untereinander
- **Kein Dropdown**: Alle Diagramme werden immer angezeigt
- **Bedingte Anzeige**: Diagramme nur wenn Daten vorhanden
- **Aktualisierungs-Button**: Aktualisiert alle Diagramme gleichzeitig
- **Mousewheel-Scrolling**: Unterstützung für Mausrad
- **Platzhalter**: Zeigt Hinweis wenn Daten fehlen

### PDF-Integration

- **Automatische Einbindung**: Alle Diagramme werden automatisch in PDF-Bericht eingefügt
- **Neue Sektion**: "Visualisierungen & Diagramme"
- **Hochauflösend**: Diagramme als PNG (300 DPI)
- **Beschreibungen**: Jedes Diagramm hat eine Beschreibung

### GET-Format erweitert (Version 3.3)

- **Diagramm-Konfigurationen**: Werden in .get Dateien gespeichert
- **Abwärtskompatibel**: Alte .get Dateien funktionieren weiterhin
- **Migration**: Automatische Migration von 3.2 → 3.3

---

## 🔧 Technische Verbesserungen

### Rohr-Konfigurationen

- **DN40 und DN50**: Jetzt in GUI verfügbar
- **Coaxial**: Bereits unterstützt
- **XML-Datenbank**: Lädt alle Rohre aus `data/pipes.xml`
- **Fallback**: Falls XML nicht verfügbar, lädt aus `pipe.txt`

### Code-Verbesserungen

- **Modulare Diagramm-Funktionen**: Jedes Diagramm hat eigene Funktion
- **Fehlerbehandlung**: Robuste Fehlerbehandlung in allen Diagrammen
- **Performance**: Diagramme werden nur bei Bedarf aktualisiert

---

## 📊 Geänderte Dateien

1. **`gui/main_window_v3_professional.py`**
   - `_create_visualization_tab()` komplett überarbeitet
   - 12 neue Diagramm-Funktionen hinzugefügt
   - `_load_default_pipes()` erweitert für XML-Datenbank
   - `_export_pdf()` erweitert für Diagramm-Sammlung
   - `_export_get_file()` erweitert für Diagramm-Konfigurationen

2. **`utils/pdf_export.py`**
   - `generate_report()` erweitert: `diagram_data` Parameter
   - Neue Diagramm-Sektion hinzugefügt

3. **`utils/get_file_handler.py`**
   - Version 3.3 Format
   - `export_to_get()` erweitert: `diagrams` Parameter
   - Migration 3.2 → 3.3 hinzugefügt

4. **`VERSION`**
   - `3.3.0-beta2` → `3.3.0-beta3`

5. **`CHANGELOG_V3.3.0-beta3.md`** (NEU)
   - Vollständige Änderungsliste

---

## 🐛 Bug Fixes

- Keine neuen Bugs bekannt (Beta 1+2 Bugs bereits behoben)

---

## 📚 Dokumentation

- Changelog erstellt
- Roadmap wird aktualisiert
- Beta-Testing-Guide wird aktualisiert

---

## 🧪 Testing

### Checkliste

- [x] Alle 12 Diagramme funktionieren korrekt
- [x] Scrollbar funktioniert
- [x] Alte Diagramme werden angezeigt (falls vorhanden)
- [x] Bedingte Anzeige funktioniert
- [x] PDF-Integration mit allen Diagrammen
- [x] GET-Format speichert/lädt Diagramm-Konfigurationen
- [x] DN40/DN50/Coaxial in GUI verfügbar
- [x] Keine Regressionen aus Beta 1+2

---

## 🚀 Nächste Schritte

### v3.3.0 stable (in 2 Wochen):
- Finale Tests
- Release mit allen Features
- Migration-Guide von v3.2.1
- Release-Notes

---

## ⚠️ Wichtig

**v3.2.1 bleibt als stable verfügbar während der Beta-Phase!**

**Feedback zu beta3 besonders wichtig:**
- Sind alle Diagramme hilfreich?
- Funktioniert die PDF-Integration korrekt?
- Gibt es Performance-Probleme mit vielen Diagrammen?
