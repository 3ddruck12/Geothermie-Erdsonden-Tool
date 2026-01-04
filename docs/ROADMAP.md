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

---

## 📅 Geplante Releases

### Version 3.3

#### 🔧 Erweiterte Rohr-Konfigurationen
- [ ] Zusätzliche Rohrtypen (DN40, DN50)
- [ ] Coaxial-Rohr-Konfigurationen
- [ ] Erweiterte Datenbank für Rohrmaterialien

#### 💧 Fluid-Datenbank
- [ ] **Wärmeträgerfluid-Datenbank** (Text/XML)
  - Wasser/Glykol-Gemische (verschiedene Konzentrationen)
  - Thermische Eigenschaften (Dichte, Viskosität, spez. Wärmekapazität)
  - Temperaturbereiche und Frostschutz
  - Druckverlust-Eigenschaften
- [ ] Auswahl und Vergleich verschiedener Fluide
- [ ] Automatische Eigenschaften basierend auf Temperatur

#### 🌊 Erweiterte Hydraulik-Berechnungen
- [ ] Pumpenauswahl-Assistent
- [ ] Detaillierte Druckverlust-Analyse
- [ ] Energieverbrauch-Prognose für Pumpen
- [ ] Durchfluss-Optimierung

#### 🎨 GUI-Verbesserungen
- [ ] Erweiterte Diagramm-Optionen

---

### Version 3.4

#### 📊 Monatliche Lastprofile
- [ ] **Monatliche Wärmebedarfs-Eingabe**
  - 12 Eingabefelder für jeden Monat
  - Heizlast pro Monat [kWh]
  - Kühllast pro Monat [kWh]
- [ ] **Warmwasser-Lastart**
  - ✓/✗ Warmwasser ja/nein für jeden Monat
  - Separate Warmwasser-Last
  - Saisonale Warmwasser-Faktoren
- [ ] **Diagramm Wärmebedarf**
  - Balkendiagramm: Monatliche Belastung
  - Liniendiagramm: Jahresverlauf
  - Separate Darstellung: Heizen/Kühlen/Warmwasser
  - Export der Diagramme (PNG, PDF)

#### 📊 Jahreszeiten & Langzeit-Simulation
- [ ] Detaillierte Jahreszeiten-Simulation
- [ ] Langzeit-Temperaturentwicklung (50+ Jahre)
- [ ] Regenerations-Strategien für Erdreich
- [ ] Saisonale Effizienz-Analyse
- [ ] Temperaturfeld-Animation über Zeit

#### 📈 Erweiterte Auswertung
- [ ] Monatliche Leistungsanalyse
- [ ] Lastgang-Profile
- [ ] Vergleich verschiedener Szenarien

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

**Stand**: Januar 2026 (nach Release V3.2.0)
