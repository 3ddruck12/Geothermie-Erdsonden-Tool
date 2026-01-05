# Changelog v3.3.0-beta1

**Release-Datum:** Januar 2026  
**Status:** 🧪 BETA  
**Branch:** beta-v3.3.0

---

## 🎯 Überblick

v3.3.0-beta1 bringt **wissenschaftlich validierte Hydraulik-Berechnungen** und **detaillierte Analyse-Tools**.

**Hauptziel:** Realistische Dimensionierung durch korrekte Stoffwerte nach VDI-Wärmeatlas.

---

## ✅ Neue Features

### 1. Korrigierte Viskositätswerte (VDI-Wärmeatlas)

**Problem:** Alte Werte entsprachen ~15°C, reale Betriebstemperatur ist 0°C  
**Lösung:** Werte aus VDI-Wärmeatlas D3.1 (11. Auflage) für 0°C

**Änderungen:**
- Wasser (0%): 0.001 → 0.0018 Pa·s (+80%)
- Glykol 25%: 0.0019 → 0.0037 Pa·s (+95%)
- Glykol 40%: 0.0038 → 0.0075 Pa·s (+97%)

**Auswirkung:**
- Reynolds-Zahlen: -49%
- Druckverluste: +16%
- Pumpenleistungen: +16%

**Referenz:**
- VDI-Wärmeatlas D3.1
- UBeG Geothermie-Studie Gau-Algesheim (Temperaturbereich -3°C bis 13°C bestätigt)

---

### 2. Detaillierte Druckverlust-Analyse

**Neuer Button:** 🔍 Detaillierte Druckverlust-Analyse

**Zeigt:**
- Bohrungen (vertikal): Länge, Geschwindigkeit, Reynolds, ΔP, Anteil
- Horizontale Anbindung: Länge, ΔP, Anteil
- Formstücke & Ventile: T-Stücke, Bögen, Schieber, ζ-Werte, ΔP, Anteil
- Wärmetauscher/Filter: ΔP, Anteil
- **Gesamt-ΔP mit prozentualer Aufschlüsselung**
- **Optimierungsvorschläge**

**Beispiel-Vorschlag:**
> "Reynolds in Sonden kritisch (2300) → ΔT reduzieren erhöht Durchfluss"

**Technisch:**
- Neue Funktion: `calculate_detailed_pressure_analysis()` in `calculations/hydraulics.py`
- GUI-Integration: Button im Hydraulik-Tab
- Dialog mit formatierter Ausgabe

---

### 3. Validierungs-Tool

**Neues Skript:** `tools/compare_hydraulics_v3_2_vs_v3_3.py`

**Funktionen:**
- Vergleicht alte vs. neue Berechnungen
- 4 vordefinierte Test-Cases (inkl. UBeG Gau-Algesheim Beispiel)
- Zeigt Änderungen in %
- Zusammenfassung mit Empfehlungen

**Ausgabe:**
```
Durchschnittliche Änderungen:
  • Viskosität:     +94.7% (realistischer für 0°C)
  • Reynolds-Zahl:  -48.6% (näher an Turbulenz-Grenze)
  • Druckverlust:   +15.8% (realistisch)
  • Pumpenleistung: +15.8% (realistisch)
```

---

### 4. Angepasste Reynolds-Schwelle

**Alt:** 2.1 m³/h pro Sonde  
**Neu:** 2.5 m³/h pro Sonde

**Grund:** Mit realistischen Viskositätswerten ist höherer Volumenstrom für Re > 2500 nötig.

---

## 📊 Technische Änderungen

### Geänderte Dateien

1. **`VERSION`**
   - `3.2.1` → `3.3.0-beta1`

2. **`calculations/hydraulics.py`**
   - `ANTIFREEZE_PROPERTIES`: Alle Viskositätswerte aktualisiert
   - Neue Funktion: `calculate_detailed_pressure_analysis()`
   - Dokumentation erweitert

3. **`gui/main_window_v3_professional.py`**
   - Reynolds-Schwelle: 2.1 → 2.5 m³/h
   - Neue Funktion: `_show_detailed_pressure_analysis()`
   - Neuer Button: "🔍 Detaillierte Druckverlust-Analyse"
   - Button-Status-Management

4. **`tools/compare_hydraulics_v3_2_vs_v3_3.py`** (NEU)
   - Standalone Validierungs-Tool
   - 230 Zeilen Python-Code
   - 4 Test-Cases

5. **`docs/BETA_v3.3.0_TESTING.md`** (NEU)
   - Beta-Testing-Anleitung
   - Feedback-Formular
   - FAQ

6. **`docs/ROADMAP.md`**
   - Status-Update für v3.3.0 Features
   - beta1/beta2/beta3 Aufteilung

---

## 🔄 Breaking Changes

### ⚠️ Hydraulik-Ergebnisse ändern sich

**Pumpenleistungen steigen um ~16%**

**Beispiel:**
- Projekt: 11 kW, 2×100m, ΔT=3K
- Alt: 418 W
- Neu: 485 W

**Was tun?**
- Neue Projekte: Neue Werte verwenden
- Bestehende Projekte: Prüfen, ob Pumpe ausreichend dimensioniert ist
- Bei Unterdimensionierung: Pumpe upgraden oder ΔT anpassen

---

## 🐛 Bug Fixes

Keine Bug-Fixes in diesem Release (nur Feature-Update).

---

## 📚 Dokumentation

- [Beta-Testing-Anleitung](docs/BETA_v3.3.0_TESTING.md)
- [Validierungs-Tool Anleitung](tools/compare_hydraulics_v3_2_vs_v3_3.py)
- [ROADMAP Update](docs/ROADMAP.md)

---

## 🧪 Testing

### Wie testen?

1. **Vergleich mit v3.2.1:**
   ```bash
   python3 tools/compare_hydraulics_v3_2_vs_v3_3.py
   ```

2. **Detaillierte Analyse:**
   - Projekt öffnen
   - "Hydraulik berechnen" klicken
   - "🔍 Detaillierte Druckverlust-Analyse" klicken

3. **Real-Vergleich:**
   - Bestehende Anlage vermessen
   - Mit Berechnung vergleichen
   - Feedback geben!

### Feedback

- GitHub Issues: [Link]
- E-Mail: [Kontakt]
- [Feedback-Formular](docs/BETA_v3.3.0_TESTING.md#feedback-formular)

---

## 🚀 Nächste Schritte

### beta2 (in 2 Wochen):
- Energieverbrauch-Prognose für Pumpen
- Durchfluss-Optimierung
- Feedback aus beta1 einarbeiten

### beta3 (in 4 Wochen):
- Pumpenauswahl-Assistent
- Erweiterte Diagramme
- Finale Tests

### v3.3.0 stable (in 6 Wochen):
- Release mit allen Features
- Migration-Guide von v3.2.1

---

## 👥 Credits

- VDI-Wärmeatlas D3.1 (Stoffwerte)
- UBeG Geothermie-Studie Gau-Algesheim (Validierung)
- GHEtool Community (Inspiration)

---

## ⚠️ Wichtig

**v3.2.1 bleibt als stable verfügbar während der Beta-Phase!**

Parallel-Installation möglich für Vergleiche.

---

**Vielen Dank fürs Testing! 🙏**

