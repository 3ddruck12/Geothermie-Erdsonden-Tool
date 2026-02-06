# 📈 GET Roadmap

Entwicklungsplan für zukünftige Versionen des Geothermie Erdsondentool (GET).

---

## 🎯 Vision

GET soll das führende Open-Source-Tool für Erdwärmesonden-Berechnung werden mit:
- Professioneller Funktionalität
- Einfacher Bedienbarkeit
- Plattformübergreifender Verfügbarkeit
- Aktiver Community

---

## ✅ Abgeschlossene Versionen

### Version 3.1 ✓

#### ✨ Hauptfeatures
- ✅ `.get` Dateiformat mit Versionierung
- ✅ Import/Export-Funktionalität (Strg+S / Strg+O)
- ✅ Abwärtskompatibilität (automatische Migration)
- ✅ Verbesserte GUI mit statischer Bohrlochs-Grafik
- ✅ PDF-Export mit Grout-Material und Hydraulik-Berechnungen
- ✅ Professionelle Visualisierungen

### Version 3.2 ✓

#### ✨ Hauptfeatures
- ✅ **VDI 4640 Berechnungsmethode** (nach Koenigsdorff)
- ✅ **pygfunction Integration** (Bohrfeld-Simulationen)
- ✅ **Dominante Kühllast-Erkennung**
- ✅ **Wärmepumpenaustrittstemperatur-Berechnung**
- ✅ **Drei Zeitskalen** (Grundlast 10 Jahre, Periodisch 1 Monat, Peak 6 Stunden)
- ✅ **Separate COP/EER** für Heizen/Kühlen
- ✅ **Langzeit-Simulation** (bis 25+ Jahre)
- ✅ **Bohrfeld-Designer** mit verschiedenen Layouts (Rechteck, L, U, Linie)
- ✅ **Fluid-Datenbank** (3.2)
  - ✅ Wärmeträgerfluid-Datenbank (Text/XML)
  - ✅ Wasser/Glykol-Gemische (verschiedene Konzentrationen)
  - ✅ Thermische Eigenschaften (Dichte, Viskosität, spez. Wärmekapazität)
  - ✅ Temperaturbereiche und Frostschutz
  - ✅ Druckverlust-Eigenschaften
  - ✅ Auswahl und Vergleich verschiedener Fluide
  - ✅ Automatische Eigenschaften basierend auf Temperatur

---

## 📅 Geplante Releases

### Version 3.3

#### 🔧 Erweiterte Rohr-Konfigurationen
- ✅ Zusätzliche Rohrtypen (DN40, DN50) - beta3
- ✅ Coaxial-Rohr-Konfigurationen - beta3
- ✅ Erweiterte Datenbank für Rohrmaterialien - beta3

#### 💧 Fluid-Datenbank (bereits in 3.2 implementiert)
- ✅ **Wärmeträgerfluid-Datenbank** (Text/XML) - 3.2
  - ✅ Wasser/Glykol-Gemische (verschiedene Konzentrationen) - 3.2
  - ✅ Thermische Eigenschaften (Dichte, Viskosität, spez. Wärmekapazität) - 3.2
  - ✅ Temperaturbereiche und Frostschutz - 3.2
  - ✅ Druckverlust-Eigenschaften - 3.2
- ✅ Auswahl und Vergleich verschiedener Fluide - 3.2
- ✅ Automatische Eigenschaften basierend auf Temperatur - 3.2

#### 🌊 Erweiterte Hydraulik-Berechnungen (beta1: ✅ | beta2: ✅ | beta3: ✅)
- ✅ **Viskositätswerte korrigiert** (VDI-Wärmeatlas 0°C) - beta1
- ✅ **Reynolds-Schwelle angepasst** (2.5 m³/h) - beta1
- ✅ **Detaillierte Druckverlust-Analyse** - beta1
  - Aufschlüsselung: Bohrungen, Horizontal, Formstücke, Wärmetauscher
  - Prozentuale Anteile
  - Optimierungsvorschläge
- ✅ **Validierungs-Tool** (v3.2.1 vs v3.3.0) - beta1
- ✅ Pumpenauswahl-Assistent - beta2
- ✅ Energieverbrauch-Prognose für Pumpen - beta2
- ✅ Durchfluss-Optimierung - beta2

#### 🎨 GUI-Verbesserungen
- ✅ Erweiterte Diagramm-Optionen - beta3
  - ✅ 12 Diagramme (Hydraulik, Wärmepumpe, Energie)
  - ✅ Scrollbarer Diagramm-Tab
  - ✅ Automatische PDF-Integration
  - ✅ GET-Format-Erweiterung (Version 3.3)

---

### Version 3.4

> **Schwerpunkt: Monatliche Lastprofile, Code-Qualität & GUI-Modernisierung**
> **Geplant: Q2 2026 | GUI: tkinter (beibehalten)**

#### 🏗️ Phase 1 – Architektur-Refactoring (Grundlage für alle Features)

- [ ] **God-Class auflösen** – `main_window_v3_professional.py` (4.360 Zeilen) aufteilen:
  - [ ] `gui/tabs/input_tab.py` – Eingabefelder, Dropdowns, Validierung
  - [ ] `gui/tabs/results_tab.py` – Ergebnis-Anzeige, Text-Ausgabe
  - [ ] `gui/tabs/diagrams_tab.py` – Alle 14 Matplotlib-Diagramme
  - [ ] `gui/tabs/materials_tab.py` – Verfüllmaterial, Rohre, Fluide
  - [ ] `gui/controllers/calculation_controller.py` – Berechnungssteuerung
  - [ ] `gui/controllers/file_controller.py` – Import/Export (.get-Dateien)
- [ ] **Input-Validierung integrieren** – `utils/validators.py` in GUI einbinden
  - [ ] Wertebereiche bei Eingabe prüfen (rot markieren bei Fehler)
  - [ ] Plausibilitäts-Checks vor Berechnung (z.B. T_min < T_boden)
  - [ ] Komma-als-Dezimaltrennzeichen akzeptieren
- [ ] **Unit-Tests für Berechnungskern** (pytest)
  - [ ] `tests/test_thermal.py` – Thermische Widerstände
  - [ ] `tests/test_hydraulics.py` – Druckverlust, Reynolds
  - [ ] `tests/test_borehole.py` – Iterative Berechnung
  - [ ] `tests/test_g_functions.py` – g-Funktionen
  - [ ] `tests/test_validators.py` – Input-Validierung
  - [ ] CI/CD-Pipeline (GitHub Actions)

#### 📊 Phase 2 – Monatliche Lastprofile (Hauptfeature)

- [ ] **Monatliche Wärmebedarfs-Eingabe** (neuer Tab)
  - [ ] 12×3 Eingabetabelle (Monat | Heizlast [kWh] | Kühllast [kWh])
  - [ ] Schnelleingabe: Jahreswert automatisch auf Monate verteilen
  - [ ] Profile aus Vorlagen laden (EFH, MFH, Büro, Gewerbe)
  - [ ] Summenzeile mit Plausibilitäts-Check (Summe = Jahresbedarf)
  - [ ] Anbindung an `monthly_heating_factors` / `monthly_cooling_factors` (bereits im Backend vorhanden)
- [ ] **Warmwasser-Lastprofil**
  - [ ] Checkbox Warmwasser je Monat (Sommer/Winter-Unterscheidung)
  - [ ] Warmwasser-Bedarf aus Personenzahl berechnen (VDI 2067)
  - [ ] Separate Warmwasser-Last auf monatliche Faktoren aufteilen
  - [ ] Saisonale Warmwasser-Faktoren (Sommer weniger als Winter)
- [ ] **Lastprofil-Diagramme**
  - [ ] Gestapeltes Balkendiagramm: Heizen + Kühlen + Warmwasser pro Monat
  - [ ] Liniendiagramm: Jahresverlauf mit Spitzenlasten
  - [ ] Monatliche Entzugsleistung (W/m) als Zeitreihe
  - [ ] Export als PNG/PDF

#### 📊 Phase 3 – Langzeit-Simulation

- [ ] **Erweiterte Temperatur-Simulation**
  - [ ] Langzeit-Temperaturentwicklung bis 50 Jahre (statt 25)
  - [ ] Jahresgang der Fluid-Temperaturen mit monatlichen Profilen
  - [ ] Bodentemperatur-Regeneration zwischen Heiz-/Kühlperioden
- [ ] **Regenerations-Analyse**
  - [ ] Thermische Balance: Wärmeentzug vs. Wärmeeintrag pro Jahr
  - [ ] Warnung bei langfristiger Auskühlung des Erdreichs
  - [ ] Optimaler Heiz/Kühl-Anteil für Langzeitstabilität
- [ ] **Saisonale Effizienz (SCOP/SEER)**
  - [ ] Monatliche COP-Berechnung basierend auf Fluidtemperatur
  - [ ] Jahresarbeitszahl (JAZ) aus monatlichen Profilen
  - [ ] Vergleich: JAZ bei verschiedenen Sondentiefen

#### 🎨 Phase 4 – GUI-Modernisierung

- [ ] **ttkbootstrap-Integration** – Modernes Dark/Light-Theme
  - [ ] Drop-in-Ersatz für ttk (minimaler Änderungsaufwand)
  - [ ] Theme-Auswahl im Einstellungs-Menü
  - [ ] Konsistentes Farbschema für Diagramme
- [ ] **Scrolling-Fix** – `bind_all("<MouseWheel>")` durch Widget-spezifisches Binding ersetzen
- [ ] **Szenario-Vergleich** (Vorbereitung für V3.5)
  - [ ] Mehrere Konfigurationen als Tabs nebeneinander
  - [ ] Schnellvergleich: Tiefe, Kosten, Temperaturen

#### 📈 Phase 5 – Erweiterte Auswertung

- [ ] **Monatliche Leistungsanalyse**
  - [ ] Tabelle: Monat | Entzugsleistung | Fluid-T | COP | Strom
  - [ ] Vergleich: Geplant vs. tatsächlich (für Monitoring)
- [ ] **Sensitivitäts-Analyse**
  - [ ] Einfluss von λ_Boden auf Bohrtiefe (±10%, ±20%)
  - [ ] Einfluss von Bohrabstand auf Langzeit-Temperatur
  - [ ] Tornado-Diagramm: Welcher Parameter hat den größten Einfluss?
- [ ] **CSV/Excel-Export** der Berechnungsergebnisse
  - [ ] Monatliche Temperaturen, Leistungen, COP
  - [ ] Hydraulik-Daten
  - [ ] Für weitere Auswertung in Excel/Python

---

### Version 3.5

#### 🗺️ Standort-Funktionen
- [ ] Interaktive Karte für Standortwahl
- [ ] Automatische Boden-Datenbank nach Region
- [ ] Geologische Karten-Integration
- [ ] GPS-Koordinaten-Integration

#### 💰 Wirtschaftlichkeitsberechnung
- [ ] Investitionskosten-Berechnung
- [ ] Amortisations-Analyse
- [ ] Betriebskosten über Lebensdauer
- [ ] CO₂-Einsparungen quantifizieren

#### 📄 Erweiterte Vergleichsberichte
- [ ] **Vergleichstabelle im PDF-Bericht**
  - Gegenüberstellung verschiedener Konfigurationen
  - Fluid-Vergleich (Wasser vs. Glykol-Gemische)
  - Rohr-Konfiguration Vergleich (Single-U vs. Double-U vs. 4-Rohr)
  - Kosten-Nutzen-Vergleich
  - Effizienz-Vergleich
- [ ] Mehrere Szenarien parallel berechnen
- [ ] Export als Vergleichstabelle (Excel, CSV)

---

### Version 3.6

#### 🎯 Erweiterte Bohrfeld-Auslegung
- [ ] **Erforderliche Tiefe** ausgehend von Bohrfeld-Konfiguration und Geologie
- [ ] **Interferenz zwischen Bohrlöchern**
  - Thermische Beeinflussung benachbarter Bohrungen
  - Optimaler Abstand basierend auf Geologie
  - Langzeit-Interaktions-Analyse

#### 🌊 Erweiterte Hydraulische Auslegung
- [ ] **Druckabfall der Verteiler** (detailliert)
  - ✓/✗ Druckabfall Bohrloch-Verbindungen
  - ✓/✗ Druckabfall vom Bohrloch zum Verteiler
  - ✓/✗ Druckabfall vom Verteiler bis zum Anlagenraum
- [ ] Rohrleitungs-Netzwerk Dimensionierung
- [ ] Ventil- und Fitting-Verluste
- [ ] Gesamtsystem-Druckabfall
- [ ] Pumpen-Kennlinie und Betriebspunkt

#### 🔧 Optimierungs-Tools
- [ ] Automatische Optimierung der Bohrloch-Anzahl
- [ ] Kosten-optimale Tiefe
- [ ] Balance zwischen Anzahl und Tiefe

---

### Version 4.0

#### 🎮 3D-Visualisierung
- [ ] 3D-Modell des Bohrfelds
- [ ] Temperaturverteilung visualisieren
- [ ] Interaktive Kamera-Steuerung
- [ ] Export als 3D-Modell (STL/OBJ)

#### 💰 Erweiterte Kostenberechnung
- [ ] Material-Kostendatenbank
- [ ] Arbeitszeitberechnung
- [ ] Regionale Preisanpassung
- [ ] Angebots-Generierung (PDF)

#### 🤖 Intelligente Optimierung
- [ ] Automatische Optimierung der Bohrfeld-Konfiguration
- [ ] Genetische Algorithmen für beste Lösung
- [ ] Multi-Parameter-Optimierung
- [ ] Kosten-Nutzen-Optimierung

#### 🌐 API & Integration
- [ ] REST API für externe Tools
- [ ] Plugin-System
- [ ] CAD-Integration
- [ ] BIM-Export (IFC-Format)

---

## 🔮 Langfristige Vision

### Internationalisierung
- [ ] Englische Übersetzung (EN)
- [ ] Mehrsprachen-Unterstützung im GUI
- [ ] Lokalisierung von Einheiten und Standards

### Machine Learning & KI
- [ ] Vorhersage-Modelle basierend auf historischen Daten
- [ ] Automatische Boden-Klassifikation aus Bohrdaten
- [ ] Intelligente Empfehlungen für Systemauslegung
- [ ] Anomalie-Erkennung in Messdaten

### Erweiterte Physik
- [ ] Grundwasser-Strömung berücksichtigen
- [ ] Saisonale Speicher (ATES)
- [ ] Hybride Systeme (Solar + Geothermie)
- [ ] Eiskeller-Integration

---

## 🤝 Community-Wünsche

Haben Sie Feature-Wünsche? 

**Möglichkeiten:**
1. [GitHub Issues](https://github.com/3ddruck12/GeothermieErdsondentool/issues) öffnen
2. [Discussions](https://github.com/3ddruck12/GeothermieErdsondentool/discussions) starten
3. Pull Request mit Feature einreichen

---

## 📊 Priorisierung

Features werden priorisiert nach:

1. **Community-Bedarf** - Was wird am meisten gewünscht?
2. **Technische Machbarkeit** - Wie komplex ist die Umsetzung?
3. **Wartbarkeit** - Wie gut passt es zur Architektur?
4. **Nutzen** - Wie viele Benutzer profitieren?

---

## 🎯 Kurzfristige Ziele

- [ ] Community aufbauen
- [ ] Feedback sammeln zu V3.2
- [ ] Bug-Fixes basierend auf User-Reports
- [ ] Dokumentation erweitern
- [ ] Video-Tutorials erstellen
- [ ] Start V3.3 Entwicklung (Erweiterte Rohr-Konfigurationen & Fluid-Datenbank)

---

## 📝 Changelog

Aktuelle Änderungen siehe:
- [CHANGELOG_V3.2_VDI4640.md](../CHANGELOG_V3.2_VDI4640.md)
- [CHANGELOG_V3.2.md](../CHANGELOG_V3.2.md)

---

## 🙋 Mitmachen

Möchten Sie bei der Entwicklung helfen?

- 👨‍💻 **Code**: Pull Requests willkommen!
- 📝 **Dokumentation**: Verbesserungen und Übersetzungen
- 🐛 **Testing**: Bug-Reports und Testing
- 💡 **Ideen**: Feature-Vorschläge

Siehe [CONTRIBUTING.md](CONTRIBUTING.md) für Details.

---

**Diese Roadmap ist ein lebendiges Dokument und wird regelmäßig aktualisiert basierend auf Community-Feedback und Entwicklungs-Fortschritt.**

**Stand**: Februar 2026 (V3.3.0-beta3, Planung V3.4)
