# Changelog V3.4.0 – Stable Release

> **Release: März 2026**
> **Status: Stable** ✅

---

## 🎯 Highlights dieser Version

V3.4.0 ist das erste stabile Release nach einer langen Beta-Phase und bringt bedeutende Verbesserungen in allen Bereichen: neue Berechnungsmodule, eine modernisierte Benutzeroberfläche, interaktive OSM-Karte sowie ein überarbeitetes Dateiformat.

---

## 🆕 Neue Features

### Phase 3 – Langzeit-Simulation

- **Langzeit-Temperaturentwicklung** (`LongtermSimulator`): Monatliche Fluid- und Erdreich-Temperaturen über konfigurierbare Zeiträume (bis 50 Jahre), nach Eskilson (1987)
- **Regenerations-Analyse** (`RegenerationAnalyzer`): Erkennt langfristige Abkühltrends, gibt Handlungsempfehlungen und berechnet optimalen Kühlanteil
- **Saisonale Effizienz** (`SeasonalEfficiencyCalculator`): Physikalisch basiertes Carnot-COP-Modell, monatliche COP-Werte, JAZ-Berechnung und Tiefenvergleich
- **4 neue Diagramme** (Langzeit-Temperatur, Thermische Balance, COP-Entwicklung, JAZ-Vergleich) – Diagramme-Tab enthält jetzt 17 Diagramme

### Phase 4 – GUI-Modernisierung

- **ttkbootstrap-Integration**: 18 moderne Themes (13 hell, 5 dunkel), wählbar unter `⚙️ Einstellungen → 🎨 Theme`, persistent gespeichert in `~/.config/geothermietool/settings.json`
- **Adresse → Karte**: Projektfelder (Straße, PLZ, Ort) geocodieren die Karte direkt; Button „📍 Adresse auf Karte zeigen" und Enter-Taste aus PLZ/Ort-Feldern
- **Interaktive OSM-Karte** (`tkintermapview`): Rechtsklick zum Standort setzen, Geocoding, Marker mit Koordinaten
- **Scrolling-Fix**: Mausrad scrollt nun zuverlässig den Bereich unter dem Mauszeiger – kein globales `bind_all` mehr, Geometrie-basierte Prüfung

### Dateiformat V3.4

- **`.get`-Format auf Version 3.4** angehoben: `address`, `postal_code`, `city`, `customer_name` als separate Felder (statt zusammengeführtem `location`/`notes`)
- **Kartenkoordinaten** (`latitude`/`longitude`) werden gespeichert und beim Laden wiederhergestellt
- **Abwärtskompatible Migration** älterer Dateiformate (3.0 → 3.1 → 3.2 → 3.3 → 3.4) automatisch beim Öffnen
- **Projektfelder** werden beim Laden einer `.get`-Datei wieder vollständig in die GUI eingetragen
- **Karte** springt beim Laden auf gespeicherte Koordinaten oder geocodiert Stadtname

### PDF-Bericht

- Kartenkoordinaten (Breitengrad / Längengrad) in der Projektinfo-Sektion

---

## 🔧 Fixes & Verbesserungen

- **Build**: SSL-Zertifikate (`certifi`) für PyInstaller/AppImage/DEB korrekt eingebunden
- **Build**: `collect_all('PIL')` und vollständige `geocoder`-Dependencies für frozen Builds
- **Build**: `ttkbootstrap` in PyInstaller-Spec aufgenommen
- **Pillow-Kompatibilität**: `Image.ANTIALIAS` für Pillow ≥ 10 automatisch gemappt
- **Scrolling**: Mausrad-Events gehen nicht mehr an falsche Bereiche (Enter/Leave-Ansatz durch Geometrie-Check ersetzt)

---

## 📦 Technische Details

| Komponente | Details |
|---|---|
| Python | 3.12+ |
| Neue Abhängigkeiten | `ttkbootstrap>=1.10.0` |
| `.get`-Formatversion | 3.4 (abwärtskompatibel zu 3.0–3.3) |
| Tests | 129 Unit-Tests, alle grün |
| Plattformen | Linux (DEB, AppImage), Windows (EXE) |

---

## 📜 Vollständige Beta-Historie

- [CHANGELOG_V3.4.0-beta1.md](CHANGELOG_V3.4.0-beta1.md) – Architektur-Refactoring, modulare Tabs, Unit-Tests
- [CHANGELOG_V3.4.0-beta2.md](CHANGELOG_V3.4.0-beta2.md) – Monatliche Lastprofile, Warmwasser-Integration
- [CHANGELOG_V3.4.0-beta2.2.md](CHANGELOG_V3.4.0-beta2.2.md) – W/m-Zeitreihe, weitere Build-Fixes
- [CHANGELOG_V3.4.0-beta3.md](CHANGELOG_V3.4.0-beta3.md) – OSM-Karte, Langzeit-Simulation, Diagramme
