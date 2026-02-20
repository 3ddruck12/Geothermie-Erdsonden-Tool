# 📈 GET Roadmap

Entwicklungsplan für zukünftige Versionen des Geothermie Erdsondentool (GET).

> **Hinweis:** Diese Roadmap beschreibt die öffentliche Produktvision. Detaillierte Cloud-Planung und Preise siehe GET Cloud (separates Projekt).

---

## 🎯 Vision

GET soll das führende Open-Source-Tool für Erdwärmesonden-Berechnung werden mit:
- Professioneller Funktionalität
- Einfacher Bedienbarkeit
- Plattformübergreifender Verfügbarkeit (Desktop & Web)
- Aktiver Community
- Nachhaltigem Open-Core-Geschäftsmodell

---

## 📐 Abgrenzung & Scope

GET berechnet **vertikale Erdwärmesonden** (Bohrungen). Folgende Systeme werden aktuell *nicht* berechnet; eine Integration wäre langfristig denkbar:

| System | Typ | Status |
|:---|:---|:---|
| **Erdwärmesonden** | Vertikal, Bohrungen | ✅ Kern von GET |
| **Solarkollektoren** | Thermische Wärmequelle | ❌ Nicht in Scope (Eingabe extern) |
| **Ringgrabenkollektor** | Horizontal, Rohr in Graben | 🔮 Mögliche Zukunft |
| **GeoCollect** | Horizontal, Absorberplatten | 🔮 Mögliche Zukunft |
| **Eisspeicher** | Unterirdischer Wassertank | 🔮 Mögliche Zukunft |

*Solare Sondenregeneration*: Wärmeeinspeisung als Eingabe (CSV/Import); Kollektorauslegung erfolgt extern.

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
- ✅ **Fluid-Datenbank**
  - ✅ Wärmeträgerfluid-Datenbank (Text/XML)
  - ✅ Wasser/Glykol-Gemische (verschiedene Konzentrationen)
  - ✅ Thermische Eigenschaften (Dichte, Viskosität, spez. Wärmekapazität)
  - ✅ Temperaturbereiche und Frostschutz
  - ✅ Druckverlust-Eigenschaften
  - ✅ Auswahl und Vergleich verschiedener Fluide
  - ✅ Automatische Eigenschaften basierend auf Temperatur

### Version 3.3 ✓

> **Fertiggestellt: Januar 2026**

#### 🔧 Erweiterte Rohr-Konfigurationen
- ✅ Zusätzliche Rohrtypen (DN40, DN50)
- ✅ Coaxial-Rohr-Konfigurationen
- ✅ Erweiterte Datenbank für Rohrmaterialien

#### 🌊 Erweiterte Hydraulik-Berechnungen
- ✅ **Viskositätswerte korrigiert** (VDI-Wärmeatlas 0°C)
- ✅ **Reynolds-Schwelle angepasst** (2.5 m³/h)
- ✅ **Detaillierte Druckverlust-Analyse**
  - Aufschlüsselung: Bohrungen, Horizontal, Formstücke, Wärmetauscher
  - Prozentuale Anteile, Optimierungsvorschläge
- ✅ **Validierungs-Tool** (v3.2.1 vs v3.3.0)
- ✅ Pumpenauswahl-Assistent
- ✅ Energieverbrauch-Prognose für Pumpen
- ✅ Durchfluss-Optimierung

#### 🎨 GUI-Verbesserungen
- ✅ Erweiterte Diagramm-Optionen
  - ✅ 12 Diagramme (Hydraulik, Wärmepumpe, Energie)
  - ✅ Scrollbarer Diagramm-Tab
  - ✅ Automatische PDF-Integration
  - ✅ GET-Format-Erweiterung (Version 3.3)

### Version 3.3.5 ✓

> **Fertiggestellt: Februar 2026**

- ✅ **Input-Validierung**: Zentrales Validierungsmodul mit Wertebereichen für ~30 physikalische Parameter
- ✅ **Erweiterte Pumpen-Datenbank**: Grundfos Alpha3, Wilo Stratos PICO, KSB EtaLine, Lowara ECOCIRC
- ✅ **Bugfixes**: Division-durch-Null in Hydraulik, robustere Fehlerbehandlung
- ✅ **Code-Qualität**: Logging-Framework, benannte Konstanten, erweiterte Modul-Exports

### Version 3.3.6 ✓

> **Schwerpunkt: Wasserrechtliche Bohranzeige als PDF für die Untere Wasserbehörde**
> **Fertiggestellt: Februar 2026**

#### 📄 Bohranzeige für Erdwärmesonden ≤ 100m (PDF-Export)

Erdwärmesonden bis 100m Tiefe erfordern i.d.R. eine **wasserrechtliche Anzeige bei der Unteren Wasserbehörde** (§ 49 WHG / Landeswassergesetze). Das Bergamt (§127 BBergG) ist erst ab >100m zuständig und daher hier nicht relevant. GET generiert ein einreichfähiges PDF mit allen nötigen technischen Angaben.

- [x] **Neuer Tab „Bohranzeige"** in der GUI
  - [x] Antragsteller (Name, Anschrift, Telefon, E-Mail)
  - [x] Grundstück (Flurstück-Nr., Gemarkung, Gemeinde, Landkreis)
  - [x] Standort-Koordinaten (automatisch aus PVGIS-Tab, falls vorhanden)
  - [x] Bohrunternehmen (Firma, Ansprechpartner, optional: DVGW W 120-1 Zertifizierung)
  - [x] Geplanter Ausführungszeitraum (Start-/Enddatum)
- [x] **Technische Angaben** (automatisch aus Berechnung befüllt)
  - [x] Anzahl der Bohrungen, Bohrtiefe, Gesamtbohrmeter, Bohrdurchmesser
  - [x] Sondentyp, Rohrmaterial, Verfüllmaterial, Wärmeträgerfluid
  - [x] Heizleistung / Kühlleistung (kW), Jahresarbeitszahl (COP)
- [x] **Standort- und Gewässerschutz**
  - [x] Wasserschutzgebiet, Grundwasserflurabstand, Bodenschichten, Altlastenkataster
- [x] **PDF-Generierung** (reportlab, behördengerechtes A4-Layout)
- [x] **Daten aus Projekt übernehmen** (Ein-Klick-Übernahme)

### Version 3.3.6.1 ✓

> **Schwerpunkt: Interaktive OSM-Karte & Lageplan in Bohranzeige-PDF**
> **Fertiggestellt: Februar 2026**

#### 🗺️ OSM-Kartenintegration

- [x] **Interaktive OSM-Karte** im Eingabe-Tab (tkintermapview)
  - [x] Marker per Rechtsklick, Zoom +/−, PVGIS-Geocoding-Sync
  - [x] Fallback auf statisches Kartenbild wenn tkintermapview fehlt
- [x] **Statische Karte für PDF-Lageplan** (`utils/osm_map.py`)
- [x] **Lageplan in Bohranzeige-PDF** eingebettet
- [x] **Automatische Datenübernahme** Eingabe-Tab → Bohranzeige

---

## 📅 Geplante Releases

### Version 3.4 (in Entwicklung)

> **Schwerpunkt: Code-Qualität, Monatliche Lastprofile & GUI-Modernisierung**
> **Geplant: Q2 2026 | GUI: tkinter (beibehalten)**

#### 🏗️ Phase 1 – Architektur-Refactoring ✓

> **Fertiggestellt: Februar 2026 (V3.4.0-beta2)**

- [x] **God-Class aufgelöst** – `main_window_v3_professional.py` (4.648 → 3.353 Zeilen) aufgeteilt:
  - [x] `gui/tabs/input_tab.py` – Eingabefelder, Dropdowns, Validierung
  - [x] `gui/tabs/results_tab.py` – Ergebnis-Anzeige, Text-Ausgabe
  - [x] `gui/tabs/diagrams_tab.py` – Alle 12 Matplotlib-Diagramme
  - [x] `gui/tabs/materials_tab.py` – Verfüllmaterial, Rohre, Fluide
  - [x] `gui/tabs/borefield_tab.py` – Bohrfeld-Simulation (g-Funktionen)
  - [x] `gui/controllers/calculation_controller.py` – Berechnungssteuerung
  - [x] `gui/controllers/file_controller.py` – Import/Export (.get-Dateien)
- [x] **Legacy-GUIs entfernt** – `main_window.py` (V1) und `main_window_extended.py` (V2) gelöscht
- [x] **Unit-Tests mit pytest** (71 Tests)
  - [x] `tests/test_thermal.py` – 16 Tests (thermische Widerstände)
  - [x] `tests/test_hydraulics.py` – 24 Tests (Druckverlust, Reynolds)
  - [x] `tests/test_borehole.py` – 10 Tests (iterative Berechnung)
  - [x] `tests/test_validators.py` – 21 Tests (Input-Validierung)
  - [x] CI/CD-Pipeline (GitHub Actions) auf pytest umgestellt
- [x] **Input-Validierung integrieren** – `utils/validators.py` in GUI einbinden
  - [x] Wertebereiche bei Eingabe prüfen (rot markieren bei Fehler)
  - [x] Plausibilitäts-Checks vor Berechnung (z.B. T_min < T_boden)
  - [x] Komma-als-Dezimaltrennzeichen akzeptieren
- [x] **Normen-Compliance-Check** (VDI 4640 Grenzen)
  - [x] Mindestabstand zwischen Bohrungen (≥ 6 m)
  - [x] Maximale spezifische Entzugsleistung (W/m) pro Bodentyp
  - [x] Frostschutzprüfung: Sole-Austrittstemperatur > -2°C
- [x] **Auto-Save** – Periodischer Auto-Save der `.get`-Datei (alle 5 Min.)
- [x] **i18n-Infrastruktur vorbereiten** – `gettext`-Wrapper für alle UI-Strings
- [x] **Windows-Installer** – Professioneller Setup-Wizard mit Inno Setup

#### 📊 Phase 2 – Monatliche Lastprofile (Hauptfeature)

- [x] **Monatliche Wärmebedarfs-Eingabe** (neuer Tab „Lastprofile“)
  - [x] 12×3 Eingabetabelle (Monat | Heizlast [kWh] | Kühllast [kWh])
  - [x] Schnelleingabe: Jahreswert automatisch auf Monate verteilen
  - [x] Profile aus Vorlagen laden (EFH, MFH, Büro, Gewerbe)
  - [x] Summenzeile mit Plausibilitäts-Check (Summe = Jahresbedarf)
  - [x] Anbindung an `monthly_heating_factors` / `monthly_cooling_factors` (bereits im Backend vorhanden)
- [x] **Warmwasser-Lastprofil**
  - [x] Checkbox Warmwasser je Monat (Sommer/Winter-Unterscheidung)
  - [x] Warmwasser-Bedarf aus Personenzahl berechnen (VDI 2067)
  - [x] Separate Warmwasser-Last auf monatliche Faktoren aufteilen
- [x] **Lastprofil-Diagramme**
  - [x] Gestapeltes Balkendiagramm: Heizen + Kühlen + Warmwasser pro Monat
  - [x] Liniendiagramm: Jahresverlauf mit Spitzenlasten
  - [ ] Monatliche Entzugsleistung (W/m) als Zeitreihe *(noch offen)*
  - [x] Export als PNG/PDF

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
  - [ ] **Temperatur- und teillastabhängiger COP** *(GHEtool-Inspiration)* – COP als Funktion von Ein-/Austrittstemperatur und Teillast

#### 🎨 Phase 4 – GUI-Modernisierung

- [ ] **ttkbootstrap-Integration** – Modernes Dark/Light-Theme
  - [ ] Drop-in-Ersatz für ttk (minimaler Änderungsaufwand)
  - [ ] Theme-Auswahl im Einstellungs-Menü
  - [ ] Konsistentes Farbschema für Diagramme
- [ ] **Scrolling-Fix** – `bind_all("<MouseWheel>")` durch Widget-spezifisches Binding ersetzen

---

### Version 3.5

> **Schwerpunkt: Vergleichsberichte & Standort-Verbesserungen**
> **Geplant: Q3–Q4 2026**

#### 📈 Auswertung

- [ ] **Monatliche Leistungsanalyse**
  - [ ] Tabelle: Monat | Entzugsleistung | Fluid-T | COP | Strom
  - [ ] Vergleich: Geplant vs. tatsächlich (für Monitoring)

#### 🗺️ Standort-Funktionen

- [x] ~~Interaktive Karte für Standortwahl~~ *(erledigt in V3.3.6.1: OSM-Karte)*
- [x] ~~GPS-Koordinaten-Integration~~ *(erledigt in V3.3.6.1: PVGIS-Geocoding)*
- [ ] **Open Data Geothermie (Bundesländer)** – Anbindung an OGC-APIs und WMS der Landesämter
  - Automatischer Abruf von Geothermie-Karten und Bodendaten nach Standort
  - NRW: ogc-api.nrw.de, WMS Geothermie; weitere Bundesländer (Bayern, BW, Hessen, …)
  - Lizenz: DL-DE/BY-2.0 (Datenlizenz Deutschland – Namensnennung)
- [ ] Automatische Boden-Datenbank nach Region (Basisdaten)

#### 📄 Vergleichsberichte

- [ ] **Vergleichstabelle im PDF-Bericht**
  - Gegenüberstellung verschiedener Konfigurationen
  - Fluid-Vergleich (Wasser vs. Glykol-Gemische)
  - Rohr-Konfiguration Vergleich (Single-U vs. Double-U vs. 4-Rohr)

> [!NOTE]
> Folgende Features aus V3.5 wurden in **GET Cloud** (proprietär) verschoben:
> Sensitivitäts-Analyse, CSV/Excel-Export, Wirtschaftlichkeitsberechnung,
> GEG/BEG-Integration, Geologische Karten, Multi-Szenario-Vergleich.

---

### Version 3.6

> **Schwerpunkt: Erweiterte Bohrfeld-Auslegung & Hydraulische Auslegung**
> **Geplant: 2027**

#### 🎯 Erweiterte Bohrfeld-Auslegung
- [ ] **Erforderliche Tiefe** ausgehend von Bohrfeld-Konfiguration und Geologie
- [ ] **Interferenz zwischen Bohrlöchern**
  - Thermische Beeinflussung benachbarter Bohrungen
  - Optimaler Abstand basierend auf Geologie
  - Langzeit-Interaktions-Analyse
- [ ] **Einfluss von Nachbarsonden** – Thermische Beeinflussung durch externe Sondenfelder auf angrenzenden Grundstücken (Quartiersplanung)
- [ ] **Bohrfeld-Konfigurations-Optimierung** *(GHEtool-Inspiration)*
  - Automatische Suche optimaler Anordnung (L, U, Rechteck, Box, Staggered)
  - Bei gegebener Fläche: minimale Bohrmeter finden
  - Optuna-basierte Optimierung (Abhängigkeit: `optuna`)

#### 🌡️ GHEtool-Integration – Erweiterte Berechnungsmodelle
> **Kontext**: [GHEtool](https://github.com/wouterpeere/GHEtool) (BSD-Lizenz) bietet erweiterte Methoden. GET und GHEtool nutzen beide pygfunction – gemeinsame Basis für Integration.
- [ ] **Geothermischer Temperaturgradient** – Bodentemperatur steigt mit Tiefe (relevant ab >100 m)
- [ ] **Mehrschichtiger Boden** – Verschiedene Bodeneigenschaften pro Tiefenschicht
- [ ] **Stündliche Lastprofile (L4-Sizing)** – 8760 Pulse/Jahr für präzisere Auslegung bei variablen Lasten
- [ ] **Building Load statt Geothermal Load** – Eingabe als Gebäudelast (kWh Heizen/Kühlen), interne Umrechnung via COP/EER

#### 🌊 Erweiterte Hydraulische Auslegung
- [ ] **Druckabfall der Verteiler** (detailliert)
  - Druckabfall Bohrloch-Verbindungen
  - Druckabfall vom Bohrloch zum Verteiler
  - Druckabfall vom Verteiler bis zum Anlagenraum
- [ ] Rohrleitungs-Netzwerk Dimensionierung
- [ ] Ventil- und Fitting-Verluste
- [ ] Gesamtsystem-Druckabfall

#### 📐 CAD-Export
- [ ] **DXF-Export des Bohrfeld-Layouts**
  - Bohransatzpunkte (Positionen der Bohrungen)
  - Anbindungsleitungen (Verbindungen zu Verteiler)
  - Verteiler (Positionen)
  - Koordinaten und Abstände
  - Georeferenzierter Lageplan (optional)
  - Farbcodierung (z.B. grün: Bohransatzpunkte, lila: Anbindungsleitungen)

#### 🔬 Erweiterte Simulationen
- [ ] **TRT-Simulation** – Auswertung von Thermal Response Tests (instationär, Minutenbereich)
- [ ] **TRT-Integration** *(Verfüllungsqualität)*
  - TRT-Datenimport (CSV/Excel: Temperatur- und Leistungsverlauf)
  - TRT-Auswertung – λ und R<sub>b</sub> aus Line-Source-Methode (VDI 4640 Blatt 5)
  - Option „R<sub>b</sub> aus TRT übernehmen“ statt Berechnung
- [ ] **Verfüllprotokoll-Import** – Dokumentation von HMG-/DPG-Messdaten (optional)
- [ ] **Magnetometrie-Datenimport** – CSV-Import (Tiefe, magnetische Feldstärke) bei magnetischem Verfüllmaterial (VDI 4640 Blatt 5)
- [ ] **Solare Sondenregeneration** – Stündliche Wärmeeinspeisung über thermische Solarkollektoren
- [ ] **Direktkühlung (Free Cooling)** – TABS, Kühldecken, Lüftung direkt an Sonden gekoppelt

> [!NOTE]
> Folgende Features aus V3.6 wurden in **GET Cloud** (proprietär) verschoben:
> Optimierungs-Tools (Auto-Tiefe, Kosten-optimal), Wärmepumpen-Hersteller-DB

---

### Version 4.0

> **Schwerpunkt: Wartung & Stabilität**
> **Geplant: 2027–2028**

> [!NOTE]
> Folgende Features aus V4.0 wurden in **GET Cloud** (proprietär) verschoben:
> Plugin-System, Plugin-API, CAD-Integration, 3D-Visualisierung (Plotly.js), REST-API, BIM-Export (IFC), Kostenberechnung, Angebots-PDF

---

## ☁️ GET Cloud – Open-Core SaaS

> **Separates Projekt** (privates Repository) – der Desktop-Berechnungskern bleibt MIT-lizenziert.

GET Cloud bietet eine Web-Version des Tools mit Premium-Features für professionelle Anwender. Der Berechnungskern ist identisch mit der Desktop-Version (MIT-Lizenz). Alle Cloud-Premium-Features sind **proprietär** und nur über das Web verfügbar.

### Feature-Matrix

| Feature | Desktop (MIT) | ☁️ Free | ☁️ Pro | ☁️ Business | ☁️ Enterprise |
|---|:---:|:---:|:---:|:---:|:---:|
| **Berechnung** | | | | | |
| VDI 4640 + Iterativ (Eskilson) | ✅ | ✅ | ✅ | ✅ | ✅ |
| Hydraulik-Berechnung | ✅ | ✅ | ✅ | ✅ | ✅ |
| 12 Diagramme | ✅ | ✅ | ✅ | ✅ | ✅ |
| Monatliche Leistungsanalyse | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Export** | | | | | |
| PDF-Bericht | ✅ | ✅ | ✅ | ✅ | ✅ |
| Bohranzeige (§ 49 WHG) | ✅ | ✅ | ✅ | ✅ | ✅ |
| OSM-Karte & Geocoding | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Projekte** | | | | | |
| Anzahl Projekte | ∞ (lokal) | 3 | ∞ | ∞ | ∞ |
| `.get`-Dateiformat | ✅ | ✅ | ✅ | ✅ | ✅ |
| | | | | | |
| **☁️ Cloud-Only (proprietär)** | | | | | |
| 🔒 Whitelabel-PDF (Firmenlogo) | ❌ | ❌ | ✅ | ✅ | ✅ |
| 🔒 Wärmepumpen-Hersteller-DB | ❌ | ❌ | ✅ | ✅ | ✅ |
| 🔒 Szenario-Vergleich | ❌ | ❌ | 2 Szenarien | 5 Szenarien | ∞ |
| 🔒 Wirtschaftlichkeitsberechnung | ❌ | ❌ | ✅ | ✅ | ✅ |
| 🔒 GEG/BEG-Compliance-Check | ❌ | ❌ | ❌ | ✅ | ✅ |
| 🔒 BEG-Förderrechner | ❌ | ❌ | ❌ | ✅ | ✅ |
| 🔒 Sensitivitäts-Analyse | ❌ | ❌ | ❌ | ✅ | ✅ |
| 🔒 Langzeit-Simulation (50 J.) | ❌ | ❌ | ❌ | ✅ | ✅ |
| 🔒 Geologische Karten-Integration | ❌ | ❌ | ❌ | ✅ | ✅ |
| 🔒 Open Data Geothermie (Bundesländer) | ❌ | ❌ | ❌ | ✅ | ✅ |
| 🔒 Grundwasser-Strömung (MODFLOW 6 GWE) | ❌ | ❌ | ❌ | ✅ | ✅ |
| 🔒 Einfluss Nachbarsonden (Quartiersplanung) | ❌ | ❌ | ❌ | ✅ | ✅ |
| 🔒 Solare Regeneration & Direktkühlung | ❌ | ❌ | ❌ | ✅ | ✅ |
| 🔒 TRT-Simulation (Thermal Response Test) | ❌ | ❌ | ❌ | ✅ | ✅ |
| 🔒 Optimierungs-Tools | ❌ | ❌ | ❌ | ✅ | ✅ |
| 🔒 Team-Projekte & Collaboration | ❌ | ❌ | ❌ | ✅ (3 Nutzer) | ✅ (10 Nutzer) |
| 🔒 Cloud-Backup & Auto-Sync | ❌ | ❌ | ❌ | ✅ | ✅ |
| 🔒 3D-Visualisierung (Bohrfeld, Plotly.js) | ❌ | ❌ | ❌ | ❌ | ✅ |
| 🔒 Kostenberechnung & Angebots-PDF | ❌ | ❌ | ❌ | ❌ | ✅ |
| 🔒 Beschaffungsliste (Projekt-Materialliste) | ❌ | ❌ | ❌ | ❌ | ✅ |
| 🔒 Bohrkern-Dokumentation (Bodenschichten-Log) | ❌ | ❌ | ❌ | ❌ | ✅ |
| 🔒 REST-API-Zugang | ❌ | ❌ | ❌ | ❌ | ✅ |
| 🔒 BIM-Export (IFC-Format) | ❌ | ❌ | ❌ | ❌ | ✅ |
| 🔒 CSV/Excel-Export | ❌ | ❌ | ❌ | ❌ | ✅ |
| 🔒 Priority Support | ❌ | ❌ | ❌ | ❌ | ✅ |

### Was bleibt Open Source (MIT)?

- ✅ Berechnungskern (`calculations/`) – VDI 4640, Iterativ, Hydraulik, g-Funktionen
- ✅ Desktop-GUI (tkinter)
- ✅ PDF-Export & Bohranzeige-Generator
- ✅ Vergleichsberichte (Basis)
- ✅ Alle Datenbanken (Boden, Rohre, Fluide, Pumpen)
- ✅ Interferenz-Berechnung, erweiterte Hydraulik (V3.6)
- ✅ Jeder Bugfix und jede neue Berechnungsnorm

### Was ist proprietär (nur GET Cloud)?

- 🔒 Web-Frontend (Vue.js / Next.js)
- 🔒 Cloud-Infrastruktur & Hosting (DSGVO-konform)
- 🔒 Plugin-System & Plugin-API
- 🔒 CAD-Integration & CAD-Import/Export
- 🔒 Wärmepumpen-Hersteller-Datenbank (reale Kennlinien)
- 🔒 GEG/BEG-Prüflogik & Förderrechner
- 🔒 Wirtschaftlichkeitsberechnung & Angebots-PDF
- 🔒 Beschaffungsliste (Projekt-Materialliste) – Rohr-Meter, Verfüllmaterial, Fluid, Pumpe, Verteiler; Export PDF/CSV
- 🔒 Bohrkern-Dokumentation – Schichten pro Bohrung (Gestein, Material, Tiefe von–bis), Proben-Dosen-Zuordnung, Schichtenlog-Bericht
- 🔒 Team-Collaboration & Nutzerverwaltung
- 🔒 Whitelabel-PDF (Firmenlogo auf Berichten)
- 🔒 Szenario-Vergleich & Sensitivitäts-Analyse
- 🔒 Optimierungs-Tools (Auto-Tiefe, Kosten-optimal)
- 🔒 3D-Visualisierung (Bohrfeld, Temperaturen) – Plotly.js
- 🔒 Geologische Karten-Integration
- 🔒 Open Data Geothermie (Bundesländer) – OGC-API, WMS, DL-DE/BY-2.0
- 🔒 Grundwasser-Strömung (MODFLOW 6 GWE, flopy) – Public Domain, subscription-tauglich
- 🔒 Einfluss von Nachbarsonden (Quartiersplanung)
- 🔒 Solare Sondenregeneration & Direktkühlung (TABS, Free Cooling)
- 🔒 TRT-Simulation & TRT-Integration (Datenimport, Auswertung, R<sub>b</sub>-Übernahme)
- 🔒 REST-API & BIM-Export (IFC)
- 🔒 CSV/Excel-Export

### Geplante Phasen

- [ ] **Backend & Infrastruktur**: FastAPI, REST-API (versioniert, modular, Auth, Logging)
- [ ] **Web-Frontend & Beta**: Vue.js/Next.js, Beta-Launch
- [ ] **Öffentlicher Launch**: Free- und Professional-Pläne
- [ ] **Enterprise-Plan**: 3D-Visualisierung, REST-API, BIM, Kostenberechnung, Beschaffungsliste, Bohrkern-Dokumentation
- [ ] **Erweiterte Simulationen**: Grundwasser-Strömung, Nachbarsonden, Solare Regeneration, TRT, Direktkühlung
- [ ] **Vision**: GET IoT & Community Data – Vernetzung Planung/Ausführung, kollaborative Geodatenbasis

---

## 🔗 GHEtool-Integration – Übersicht

[GHEtool](https://github.com/wouterpeere/GHEtool) (KU Leuven, FH Aachen, 3-Clause BSD) ergänzt klassische Methoden um erweiterte Berechnungsmodelle. GET und GHEtool nutzen beide **pygfunction** – eine Integration ist technisch gut möglich.

| Priorität | Feature | Zielversion | Abhängigkeiten |
|:---:|:---|:---:|:---|
| Hoch | Geothermischer Temperaturgradient | V3.6 | – |
| Hoch | Bohrfeld-Konfigurations-Optimierung | V3.6 | optuna |
| Mittel | Temperatur-/teillastabhängiger COP | V3.4 | – |
| Mittel | Stündliche Lastprofile (L4) | V3.6 | – |
| Mittel | Building Load statt Geothermal Load | V3.4/V3.5 | – |
| Mittel | Mehrschichtiger Boden | V3.6 | – |
| Niedrig | Variable Durchflussraten | V3.6 | – |
| Niedrig | Exotische Rohrtypen (Separatus, Conical) | optional | – |

---

## 🌊 MODFLOW 6 GWE – Grundwasser-Strömung (GET Cloud)

[MODFLOW 6 GWE](https://modflow6-examples.readthedocs.io/en/develop/_notebooks/ex-gwe-geotherm.html) (USGS) simuliert Erdwärmesonden in strömendem Grundwasser – advektiver Wärmetransport, Interferenz mehrerer BHEs. **Lizenz**: Public Domain (MODFLOW 6) + CC0 (flopy) → uneingeschränkt kommerziell nutzbar, subscription-tauglich.

| Aspekt | Details |
|:---|:---|
| **Ziel** | GET Cloud Business/Enterprise |
| **Technologie** | flopy + MODFLOW 6 GWE |
| **Lizenz** | Public Domain – keine Gebühren, keine Einschränkungen |
| **Referenz** | Al-Khoury et al. (2021), MODFLOW 6 Examples |

---

## 🗺️ Open Data Geothermie – Bundesländer

Die Bundesländer stellen Geothermie-Karten und Bodendaten als Open Data bereit. Anbindung ermöglicht automatischen Abruf nach Standort (Koordinaten).

| Aspekt | Details |
|:---|:---|
| **Desktop** | V3.5 – Standort-Funktionen |
| **GET Cloud** | Business/Enterprise |
| **Quellen** | NRW (ogc-api.nrw.de, WMS), Bayern, BW, Hessen, Niedersachsen, … |
| **Technologie** | OGC API, WMS, WFS |
| **Lizenz** | DL-DE/BY-2.0 (Datenlizenz Deutschland – Namensnennung) |

---

## 📊 Erweiterte Simulationen – Feature-Übersicht

Übersicht der geplanten erweiterten Berechnungsfunktionen:

| Feature | GET Status |
|:---|:---|
| Stündliche Simulation (L4) | ⏳ V3.6 |
| Bohrfeld-Optimierung | ⏳ V3.6 |
| Mehrschichtiger Boden | ⏳ V3.6 |
| Grundwasser-Strömung | ⏳ GET Cloud |
| Einfluss Nachbarsonden | ⏳ V3.6 + GET Cloud |
| Solare Regeneration | ⏳ V3.6 + GET Cloud |
| TRT-Simulation | ⏳ V3.6 + GET Cloud |
| TRT-Integration (Datenimport, Auswertung, R<sub>b</sub>-Übernahme) | ⏳ V3.6 + GET Cloud |
| Verfüllprotokoll-Import (HMG, DPG) | ⏳ V3.6 |
| Magnetometrie-Datenimport (magnetisches Verfüllmaterial) | ⏳ V3.6 |
| Direktkühlung (TABS, Free Cooling) | ⏳ V3.6 + GET Cloud |
| Open Data Geothermie (Bundesländer) | ⏳ V3.5 + GET Cloud |

---

## 🔬 Verfüllungsqualität & TRT-Integration

Methoden zur Messung der Verfüllqualität und Anbindung an GET:

| Methode | Liefert | Integration |
|:---|:---|:---|
| **Thermal Response Test (TRT)** | λ, R<sub>b</sub>, T<sub>0</sub> | V3.6 – Datenimport, Auswertung, R<sub>b</sub>-Übernahme |
| **Magnetometrie** (magnetisches Verfüllmaterial) | Verfüllkontinuität über Tiefe | V3.6 – Magnetometrie-Datenimport |
| **Verfüllungsüberwachung (HMG-S/K)** | Protokoll während Installation | V3.6 – Verfüllprotokoll-Import |
| **Durchfluss-/Dichtigkeitsprüfung (DPG-C3)** | Leckage-Prüfung | V3.6 – Protokoll-Dokumentation |

**Norm:** VDI 4640 Blatt 5 (TRT, Magnetometrie bei ferromagnetischem Verfüllmaterial)

**Hardware:** IoT- bzw. Mikrocontroller-basierte Magnetometrie-Sonden können Daten im CSV-Format liefern.

---

## 🔮 Langfristige Vision

### 🛰️ GET IoT & Vernetzung
- [ ] **Digitale Felndatenerfassung**: Unterstützung bei der Erfassung von Bohr- und Standortparametern direkt vor Ort
- [ ] **Bohrkern-Dokumentation** (GET Cloud Enterprise): Schichten pro Bohrung erfassen (Gestein, Material, Zusammensetzung, Tiefe von–bis), Proben-Dosen-Zuordnung, Schichtenlog-Bericht
- [ ] **Data Feedback Loop**: Validierung von Planungswerten durch reale Ausführungsdaten zur kontinuierlichen Verbesserung der Berechnungsmodelle
- [ ] **Echtzeit-Assistenz**: Intelligente Assistenzsysteme während des Erstellungsprozesses von Erdwärme-Anlagen

### 🧠 Community-Datenbank & KI
- [ ] **Kollaborative Datenbasis**: Aufbau eines anonymisierten Datenpools zur Verbesserung lokaler geologischer Prognosen
- [ ] **KI-gestützte Auslegung**: Intelligente Vorschlagssysteme basierend auf einer breiteren Datenbasis aus realen Projekten
- [ ] **Automatisierte Qualitätsprüfung**: Datenbasierte Unterstützung bei der Einhaltung von Normen und Standards


### Internationalisierung
- [ ] Englische Übersetzung (EN) – i18n-Infrastruktur wird in V3.4 vorbereitet
- [ ] Mehrsprachen-Unterstützung im GUI
- [ ] Lokalisierung von Einheiten und Standards

### Machine Learning & KI
- [ ] Vorhersage-Modelle basierend auf historischen Daten
- [ ] Automatische Boden-Klassifikation aus Bohrdaten
- [ ] Intelligente Empfehlungen für Systemauslegung
- [ ] Anomalie-Erkennung in Messdaten

### Erweiterte Physik
- [ ] **Grundwasser-Strömung** – geplant für GET Cloud (MODFLOW 6 GWE + flopy, Public Domain)
- [ ] **Solare Sondenregeneration** – Wärmeeinspeisung als Eingabe (CSV/Import); Kollektorauslegung extern
- [ ] **Direktkühlung (Free Cooling)** – TABS, Kühldecken, Lüftung direkt an Sonden
- [ ] Saisonale Speicher (ATES)
- [ ] Hybride Systeme (Solar + Geothermie)
- [ ] Eiskeller-Integration
- [ ] **Ringgrabenkollektor** – Auslegung horizontaler Grabenkollektoren (langfristig)
- [ ] **GeoCollect** – Auslegung horizontaler Absorberplatten-Kollektoren (langfristig)

---

## 🤝 Community-Wünsche

Haben Sie Feature-Wünsche? 

**Möglichkeiten:**
1. [GitHub Issues](https://github.com/3ddruck12/Geothermie-Erdsonden-Tool/issues) öffnen
2. [Discussions](https://github.com/3ddruck12/Geothermie-Erdsonden-Tool/discussions) starten
3. Pull Request mit Feature einreichen

---

## 📊 Priorisierung

Features werden priorisiert nach:

1. **Community-Bedarf** - Was wird am meisten gewünscht?
2. **Technische Machbarkeit** - Wie komplex ist die Umsetzung?
3. **Wartbarkeit** - Wie gut passt es zur Architektur?
4. **Nutzen** - Wie viele Benutzer profitieren?

---

## 🎯 Kurzfristige Ziele (Q1–Q2 2026)

- [x] V3.4 Phase 1: Architektur-Refactoring ✓ (God-Class aufgelöst, 71 Tests)
- [x] Unit-Tests aufbauen (pytest + CI/CD) ✓
- [ ] Community aufbauen & Feedback sammeln
- [ ] Dokumentation erweitern
- [ ] Video-Tutorials erstellen
- [ ] GET Cloud: Privates Repository aufsetzen

---

## 📝 Changelog

Aktuelle Änderungen siehe:
- [CHANGELOG_V3.4.0-beta1](../CHANGELOG_V3.4.0-beta1.md)
- [CHANGELOG_V3.4.0-beta2](../CHANGELOG_V3.4.0-beta2.md)
- [CHANGELOG_V3.3.0-beta1](../CHANGELOG_V3.3.0-beta1.md)
- [CHANGELOG_V3.3.0-beta2](../CHANGELOG_V3.3.0-beta2.md)
- [CHANGELOG_V3.3.0-beta3](../CHANGELOG_V3.3.0-beta3.md)
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

**Stand**: Februar 2026 (V3.4.0-beta2, Planung V3.4 Phase 2–4, V3.6 GHEtool-Integration & GET Cloud)
