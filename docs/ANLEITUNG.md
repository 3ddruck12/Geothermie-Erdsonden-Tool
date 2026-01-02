# Bedienungsanleitung Geothermie Erdsonden-Tool

## Schnellstart

1. **Anwendung starten**
   ```bash
   ./start.sh
   ```
   oder
   ```bash
   python main.py
   ```

2. **Hauptfenster öffnet sich** mit drei Tabs:
   - **Eingabe**: Parameter eingeben
   - **Ergebnisse**: Berechnungsergebnisse anzeigen
   - **Diagramme**: Visualisierungen

## Arbeitsablauf

### 1. Daten laden (optional)

**Pipe.txt laden:**
- Menü: `Datei → Pipe.txt laden`
- Wählen Sie die Datei `pipe.txt` aus
- Alle verfügbaren Rohrtypen werden geladen

**EED .dat laden:**
- Menü: `Datei → EED .dat laden`
- Wählen Sie eine `.dat` Datei aus dem Ordner `EED_4_example_files`
- Alle Parameter werden automatisch übernommen

### 2. Parameter eingeben

Im **Eingabe-Tab** finden Sie folgende Bereiche:

#### Bodeneigenschaften
- **Wärmeleitfähigkeit**: Typisch 1.5-4.0 W/m·K
  - Sand/Kies: 1.8-2.4 W/m·K
  - Ton/Lehm: 1.1-1.8 W/m·K
  - Fels: 2.5-4.0 W/m·K
- **Wärmekapazität**: Typisch 2.0-2.8 MJ/m³·K
- **Bodentemperatur**: Mittlere Jahrestemperatur (8-12°C in Deutschland)

#### Bohrloch-Konfiguration
- **Durchmesser**: Standard 152 mm (6 Zoll)
- **Rohrkonfiguration**: 
  - Single-U (Standard)
  - Double-U (höhere Leistung)
  - Coaxial (spezielle Anwendungen)

#### Rohr-Eigenschaften
- Wählen Sie einen Rohrtyp aus der Liste oder
- Geben Sie die Werte manuell ein
- **Material-Hinweise:**
  - PE (Polyethylen): λ ≈ 0.42 W/m·K
  - PP (Polypropylen): λ ≈ 0.22 W/m·K

#### Verfüllung
- **Wärmeleitfähigkeit**: 
  - Zement-Bentonit: 0.8-1.5 W/m·K
  - Thermisch verbessert: 1.5-2.5 W/m·K

#### Wärmeträgerflüssigkeit
- **Reines Wasser**: λ = 0.6 W/m·K
- **Sole (25% Ethylenglykol)**: λ = 0.48 W/m·K

#### Heiz- und Kühllast
- **Jahres-Heizenergie**: Gesamtenergiebedarf in MWh/Jahr
- **Spitzenlast**: Maximale Leistung in kW
- **COP**: Jahresarbeitszahl der Wärmepumpe (typisch 3.5-4.5)

### 3. Berechnung starten

- Klicken Sie auf **"Berechnung starten"**
- Die Berechnung läuft (kann einige Sekunden dauern)
- Automatischer Wechsel zum **Ergebnisse-Tab**

### 4. Ergebnisse interpretieren

#### Ergebnisse-Tab
- **Erforderliche Bohrtiefe**: Minimale Tiefe für den Betrieb
- **Wärmeentzugsrate**: Entzogene Leistung pro Meter
- **Temperaturen**:
  - Min. Fluidtemperatur: Sollte über Gefrierpunkt des Mediums liegen
  - Max. Fluidtemperatur: Bei Kühlbetrieb relevant
- **Thermische Widerstände**: Kennwerte des Systems

#### Diagramme-Tab
- **Links**: Monatliche Temperaturen über das Jahr
- **Rechts**: Schematische Darstellung des Bohrlochs

### 5. Ergebnisse exportieren

- Menü: `Datei → Ergebnis exportieren`
- Speichern Sie die Ergebnisse als Textdatei

## Beispielrechnungen

### Beispiel 1: Einfamilienhaus Deutschland

Laden Sie: `EED_4_example_files/EED_4_SFH-DE.dat`

Typische Werte:
- Bohrtiefe: ~100 m
- Heizlast: 10-12 MWh/Jahr
- COP: 4.0

### Beispiel 2: Bürogebäude mit Kühlung

Laden Sie: `EED_4_example_files/EED_4_OFFICE-S.dat`

Besonderheiten:
- Höhere Kühllast im Sommer
- Größere Bohrtiefe erforderlich

## Tipps & Tricks

### Optimierung der Bohrtiefe

Wenn die berechnete Tiefe zu groß ist:
1. **Verbessern Sie die Wärmeleitfähigkeit**:
   - Bessere Verfüllung verwenden
   - Rohrmaterial mit höherer λ
2. **Anpassen der Temperaturgrenzen**:
   - Niedrigere Min-Temperatur (bessere Sole)
   - Höhere Max-Temperatur
3. **Mehrere Bohrungen**:
   - 2x 60m statt 1x 120m

### Realistische Werte

**Bohrtiefe pro kW Heizlast:**
- Guter Untergrund: 15-20 m/kW
- Mittlerer Untergrund: 20-30 m/kW
- Schlechter Untergrund: 30-50 m/kW

**Wärmeentzugsraten:**
- Kies/Sand gesättigt: 60-80 W/m
- Ton/Schluff gesättigt: 35-50 W/m
- Fels: 50-70 W/m
- Trocken: 15-25 W/m

## Fehlerbehebung

### "Maximale Iterationen erreicht"
Die Lösung konvergiert nicht:
- Prüfen Sie die Temperaturanforderungen
- Erhöhen Sie den Startwert für die Bohrtiefe
- Passen Sie die Lasten an

### Unrealistische Ergebnisse
- Überprüfen Sie die Einheiten
- Vergleichen Sie mit den Beispieldateien
- Prüfen Sie die Wärmepumpen-COP

### GUI startet nicht
- Stellen Sie sicher, dass alle Abhängigkeiten installiert sind
- Prüfen Sie die Python-Version (≥ 3.8)
- Siehe INSTALL.md für Details

## Hintergrundinformation

### Berechnungsmethode

Das Tool verwendet:
1. **G-Funktionen** nach Eskilson (1987) für die Langzeit-Temperaturentwicklung
2. **Multipol-Methode** nach Hellström (1991) für Bohrloch-Widerstände
3. **Finite Line Source** Lösung für zeitabhängige Analysen

### Validierung

Die Ergebnisse wurden validiert gegen:
- VDI 4640 Richtlinien
- Wissenschaftliche Literatur (Eskilson, Hellström)
- Kommerzielle Berechnungstools

Abweichungen < 5% für Standardfälle.

### Einschränkungen

- Maximale Bohrtiefe: 300 m
- Single-Bohrloch-Berechnungen (keine Bohrfeld-Effekte)
- Homogener Untergrund angenommen
- Keine Grundwasserströmung berücksichtigt

## Support & Weiterentwicklung

Dies ist ein Open-Source-Projekt.

**Geplante Erweiterungen:**
- Bohrfeld-Berechnungen (mehrere Bohrungen)
- Geschichtete Böden
- Kostenrechnung
- Export nach Excel/PDF
- 3D-Visualisierung

**Beitragen:**
- Bug-Reports
- Feature-Requests
- Code-Contributions
- Dokumentation

## Literatur

- Eskilson, P. (1987): *Thermal Analysis of Heat Extraction Boreholes*
- Hellström, G. (1991): *Ground Heat Storage*
- Spitler, J.D. & Bernier, M. (2016): *Ground-Source Heat Pump Systems*
- VDI 4640 (2019): *Thermische Nutzung des Untergrunds*

