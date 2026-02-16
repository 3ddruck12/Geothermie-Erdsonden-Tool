# 📈 GET Roadmap

Entwicklungsplan für zukünftige Versionen des Geothermie Erdsondentool (GET).

---

## 🎯 Vision

GET soll das führende Open-Source-Tool für Erdwärmesonden-Berechnung werden mit:
- Professioneller Funktionalität
- Einfacher Bedienbarkeit
- Plattformübergreifender Verfügbarkeit (Desktop & Web)
- Aktiver Community
- Nachhaltigem Open-Core-Geschäftsmodell

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

> **Fertiggestellt: Februar 2026 (V3.4.0-beta1)**

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
- [ ] **Input-Validierung integrieren** – `utils/validators.py` in GUI einbinden
  - [ ] Wertebereiche bei Eingabe prüfen (rot markieren bei Fehler)
  - [ ] Plausibilitäts-Checks vor Berechnung (z.B. T_min < T_boden)
  - [ ] Komma-als-Dezimaltrennzeichen akzeptieren
- [ ] **Normen-Compliance-Check** (VDI 4640 Grenzen)
  - [ ] Mindestabstand zwischen Bohrungen (≥ 6 m)
  - [ ] Maximale spezifische Entzugsleistung (W/m) pro Bodentyp
  - [ ] Frostschutzprüfung: Sole-Austrittstemperatur > -2°C
- [ ] **Auto-Save** – Periodischer Auto-Save der `.get`-Datei (alle 5 Min.)
- [ ] **i18n-Infrastruktur vorbereiten** – `gettext`-Wrapper für alle UI-Strings

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
- [ ] Automatische Boden-Datenbank nach Region (Basisdaten)

#### 📄 Vergleichsberichte

- [ ] **Vergleichstabelle im PDF-Bericht**
  - Gegenüberstellung verschiedener Konfigurationen
  - Fluid-Vergleich (Wasser vs. Glykol-Gemische)
  - Rohr-Konfiguration Vergleich (Single-U vs. Double-U vs. 4-Rohr)

> [!NOTE]
> Folgende Features aus V3.5 wurden in **GET Cloud** (proprietär) verschoben:
> Sensitivitäts-Analyse, CSV/Excel-Export, Wirtschaftlichkeitsberechnung,
> GEG/BEG-Integration, Geologische Karten, Multi-Szenario-Vergleich

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

#### 🌊 Erweiterte Hydraulische Auslegung
- [ ] **Druckabfall der Verteiler** (detailliert)
  - Druckabfall Bohrloch-Verbindungen
  - Druckabfall vom Bohrloch zum Verteiler
  - Druckabfall vom Verteiler bis zum Anlagenraum
- [ ] Rohrleitungs-Netzwerk Dimensionierung
- [ ] Ventil- und Fitting-Verluste
- [ ] Gesamtsystem-Druckabfall

#### 📐 CAD-Export
- [ ] DXF-Export des Bohrfeld-Layouts (Grundriss mit Koordinaten und Abständen)

> [!NOTE]
> Folgende Features aus V3.6 wurden in **GET Cloud** (proprietär) verschoben:
> Optimierungs-Tools (Auto-Tiefe, Kosten-optimal), Wärmepumpen-Hersteller-DB

---

### Version 4.0

> **Schwerpunkt: Wartung & Stabilität**
> **Geplant: 2027–2028**

> [!NOTE]
> Folgende Features aus V4.0 wurden in **GET Cloud** (proprietär) verschoben:
> Plugin-System, Plugin-API, CAD-Integration, 3D-Visualisierung, REST-API, BIM-Export (IFC), Kostenberechnung, Angebots-PDF

---

## ☁️ GET Cloud – Open-Core SaaS

> **Separates Projekt** (privates Repository) – der Desktop-Berechnungskern bleibt MIT-lizenziert.

GET Cloud bietet eine Web-Version des Tools mit Premium-Features für professionelle Anwender. Der Berechnungskern ist identisch mit der Desktop-Version (MIT-Lizenz). Alle Cloud-Premium-Features sind **proprietär** und nur über das Web verfügbar.

### Feature-Matrix

| Feature | Desktop (MIT) | ☁️ Free | ☁️ Pro (29€/M) | ☁️ Business (79€/M) | ☁️ Enterprise (199€/M) |
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
| 🔒 Optimierungs-Tools | ❌ | ❌ | ❌ | ✅ | ✅ |
| 🔒 Team-Projekte & Collaboration | ❌ | ❌ | ❌ | ✅ (3 Nutzer) | ✅ (10 Nutzer) |
| 🔒 Cloud-Backup & Auto-Sync | ❌ | ❌ | ❌ | ✅ | ✅ |
| 🔒 3D-Visualisierung (Bohrfeld) | ❌ | ❌ | ❌ | ❌ | ✅ |
| 🔒 Kostenberechnung & Angebots-PDF | ❌ | ❌ | ❌ | ❌ | ✅ |
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
- 🔒 Cloud-Infrastruktur & Hosting (Hetzner, DSGVO-konform)
- 🔒 Plugin-System & Plugin-API
- 🔒 CAD-Integration & CAD-Import/Export
- 🔒 Wärmepumpen-Hersteller-Datenbank (reale Kennlinien)
- 🔒 GEG/BEG-Prüflogik & Förderrechner
- 🔒 Wirtschaftlichkeitsberechnung & Angebots-PDF
- 🔒 Team-Collaboration & Nutzerverwaltung
- 🔒 Whitelabel-PDF (Firmenlogo auf Berichten)
- 🔒 Szenario-Vergleich & Sensitivitäts-Analyse
- 🔒 Optimierungs-Tools (Auto-Tiefe, Kosten-optimal)
- 🔒 3D-Visualisierung (Bohrfeld, Temperaturen)
- 🔒 Geologische Karten-Integration
- 🔒 REST-API & BIM-Export (IFC)
- 🔒 CSV/Excel-Export

### Geplante Phasen

- [ ] **Q2 2026**: FastAPI-Backend (Berechnungskern als Web-Service)
- [ ] **Q3 2026**: Web-Frontend, Stripe-Integration, Beta-Launch
- [ ] **Q4 2026**: Öffentlicher Launch (Free + Professional)
- [ ] **Q2 2027**: Enterprise-Plan (3D-Vis, REST-API, BIM, Kosten, Angebots-PDF)
- [ ] **Vision 2028+**: **GET IoT & Community Data**
  - Vernetzung von Planung und Ausführung im Feld
  - Digitale Dokumentationsunterstützung für Fachbetriebe
  - Aufbau einer kollaborativen Geodatenbasis zur Präzisierung von Projektvorhersagen
  - Datenbasierte Optimierungsalgorithmen für die Anlagenauslegung

Details zur Umsetzung siehe privates Repository `GET-Cloud`.

---

## 🔮 Langfristige Vision

### 🛰️ GET IoT & Vernetzung
- [ ] **Digitale Felndatenerfassung**: Unterstützung bei der Erfassung von Bohr- und Standortparametern direkt vor Ort
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
- [ ] Grundwasser-Strömung berücksichtigen
- [ ] Saisonale Speicher (ATES)
- [ ] Hybride Systeme (Solar + Geothermie)
- [ ] Eiskeller-Integration

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

**Stand**: Februar 2026 (V3.4.0-beta1, Planung V3.4 Phase 2–4 & GET Cloud)
