# Changelog v3.3.0-beta2

**Release-Datum:** Januar 2026  
**Status:** 🧪 BETA  
**Branch:** beta-v3.3.0

---

## 🎯 Überblick

v3.3.0-beta2 bringt **Energieverbrauch-Prognose** und **interaktive Durchfluss-Optimierung**.

**Basis:** Baut auf beta1 auf (VDI-Wärmeatlas Stoffwerte, Detaillierte Druckverlust-Analyse)

---

## ✅ Neue Features

### 1. Energieverbrauch-Prognose 💰

**Neuer Button:** 💰 Energieverbrauch-Prognose

**Funktionen:**
- Berechnet Jahres-Energieverbrauch der Pumpe
- Vergleicht konstante vs. geregelte Pumpen
- Zeigt 10-Jahres-Kosten
- Berechnet Amortisation für Hocheffizienz-Pumpen
- Vergleich mit kleinerer Pumpe

**Ausgabe:**
```
OPTION 1: KONSTANTE PUMPE
  • Energie: 475 kWh/Jahr
  • Kosten: 143 EUR/Jahr
  • 10 Jahre: 1.425 EUR

OPTION 2: GEREGELTE PUMPE
  • Energie: 262 kWh/Jahr (-45%)
  • Kosten: 79 EUR/Jahr
  • 10 Jahre: 786 EUR

VERGLEICH:
  • Ersparnis: 64 EUR/Jahr
  • Amortisation: 3.1 Jahre
  ✅ Geregelte Pumpe lohnt sich!
```

**Parameter anpassbar:**
- Betriebsstunden/Jahr
- Strompreis EUR/kWh

**Technisch:**
- Neue Funktion: `calculate_pump_energy_consumption()` in `hydraulics.py`
- Berücksichtigt Regelungs-Faktor (55% Durchschnitt bei geregelten Pumpen)
- Vergleich mit Standard-Pumpen vs. Hocheffizienz (A++)

---

### 2. Durchfluss-Optimierung 🎯

**Neuer Button:** 🎯 Durchfluss optimieren

**Funktionen:**
- Interaktiver ΔT-Schieberegler (2-5K)
- Echtzeit-Berechnung während Slider-Bewegung
- Drei Optimierungsziele:
  - Minimale Pumpenleistung
  - Optimale Reynolds-Zahl (Re > 3000)
  - Ausgeglichener Kompromiss
- Vergleichs-Tabelle mit allen ΔT-Werten
- Direkte Übernahme ins Hauptfenster

**Ausgabe:**
```
Aktuelle Werte (ΔT = 3.0 K):
  Volumenstrom: 3.19 m³/h
  Reynolds: 6066 (turbulent)
  Pumpe: 485 W
  Energiekosten: 146 EUR/Jahr

💡 OPTIMIERTES ERGEBNIS (ΔT = 2.7 K):
  Volumenstrom: 3.54 m³/h (+11%)
  Reynolds: 6730 (+11%)
  Pumpe: 585 W (+21%)
  Energiekosten: 176 EUR/Jahr (+30 EUR/Jahr)

EMPFEHLUNG:
  ⬆️ Optimierung erhöht Pumpenleistung um 21%
     → Bessere Reynolds-Zahl, höherer Wärmeübergang
     → +30 EUR/Jahr Energiekosten
```

**Vergleichs-Tabelle:**
```
ΔT (K)    Flow (m³/h)   Reynolds    Pumpe (W)   EUR/Jahr
2.0       3.98          7564        762         229      ★
2.5       3.19          6066        485         146      ← 
3.0       2.65          5043        333         100      
...
```

**Technisch:**
- Echtzeit-Berechnung bei Slider-Bewegung
- Automatische Optimierung basierend auf Ziel
- "Übernehmen"-Button schreibt ΔT ins Hauptfenster

---

## 📊 Technische Änderungen

### Geänderte Dateien

1. **`VERSION`**
   - `3.3.0-beta1` → `3.3.0-beta2`

2. **`calculations/hydraulics.py`**
   - Neue Funktion: `calculate_pump_energy_consumption()`
     - 80 Zeilen Code
     - Jahresverbrauch, 10-Jahres-Bilanz
     - Vergleich mit geregelten Pumpen
     - Amortisations-Berechnung

3. **`gui/main_window_v3_professional.py`**
   - Neue Funktion: `_show_energy_prognosis()` (~150 Zeilen)
   - Neue Funktion: `_show_flow_optimizer()` (~200 Zeilen)
   - 2 neue Buttons im Hydraulik-Tab
   - Automatische Aktivierung nach Hydraulik-Berechnung

---

## 🎨 GUI-Verbesserungen

### Hydraulik-Tab

**Vorher (beta1):**
```
[🔍 Detaillierte Druckverlust-Analyse]
```

**Jetzt (beta2):**
```
[🔍 Detaillierte Druckverlust-Analyse] [💰 Energieverbrauch-Prognose] [🎯 Durchfluss optimieren]
```

### Energieverbrauch-Prognose Dialog
- 750×700 px Fenster
- Eingabefelder: Betriebsstunden, Strompreis
- "Neu berechnen"-Button
- Formatierte Ausgabe mit Effizienzklassen-Info

### Durchfluss-Optimierung Dialog
- 800×750 px Fenster
- Aktuelle Konfiguration oben
- 3 Optimierungsziele (Radio-Buttons)
- Interaktiver ΔT-Slider (2-5K)
- Echtzeit-Ergebnis-Aktualisierung
- Vergleichs-Tabelle
- "Übernehmen"-Button

---

## 🔄 Änderungen gegenüber beta1

### Was ist gleich:
- ✅ VDI-Wärmeatlas Stoffwerte
- ✅ Detaillierte Druckverlust-Analyse
- ✅ Validierungs-Tool
- ✅ Reynolds-Schwelle 2.5 m³/h

### Was ist neu:
- 🆕 Energieverbrauch-Prognose
- 🆕 Durchfluss-Optimierung
- 🆕 3 statt 1 Analyse-Button

---

## 🧪 Testing

### Wie testen?

1. **Energieverbrauch-Prognose:**
   - Projekt berechnen
   - "Hydraulik berechnen" klicken
   - "💰 Energieverbrauch-Prognose" klicken
   - Betriebsstunden anpassen (z.B. 1500-2000h)
   - Strompreis anpassen (z.B. 0.25-0.35 EUR/kWh)
   - Vergleich konstant vs. geregelt prüfen

2. **Durchfluss-Optimierung:**
   - Nach Hydraulik-Berechnung
   - "🎯 Durchfluss optimieren" klicken
   - Optimierungsziel wählen
   - ΔT-Slider bewegen (Echtzeit-Update!)
   - Vergleichs-Tabelle prüfen
   - "Übernehmen" → ΔT wird ins Hauptfenster übernommen

3. **Kombination:**
   - Durchfluss optimieren
   - Neues ΔT übernehmen
   - Hydraulik neu berechnen
   - Energieverbrauch-Prognose prüfen
   - Vergleichen: Lohnt sich die Optimierung?

---

## 💡 Anwendungsbeispiele

### Beispiel 1: Kostenoptimierung

**Ausgangslage:**
- 11 kW Projekt, ΔT=3K
- Pumpe: 485 W
- Kosten: 146 EUR/Jahr

**Durchfluss-Optimierung:**
- Ziel: "Minimale Pumpenleistung"
- Empfehlung: ΔT=3.5K
- Neue Pumpe: 365 W (-25%)
- Neue Kosten: 110 EUR/Jahr
- **Ersparnis: 36 EUR/Jahr**

**Energieverbrauch-Prognose:**
- Mit geregelter Pumpe: 61 EUR/Jahr
- **Ersparnis vs. Original: 85 EUR/Jahr**
- **10 Jahre: 850 EUR Ersparnis**

---

### Beispiel 2: Qualitätsoptimierung

**Ausgangslage:**
- Reynolds: 6066 (knapp turbulent)

**Durchfluss-Optimierung:**
- Ziel: "Optimale Reynolds-Zahl"
- Empfehlung: ΔT=2.5K
- Neuer Reynolds: 7250 (sicher turbulent)
- Pumpe steigt auf 620 W (+28%)
- **Aber: Besserer Wärmeübergang, höhere JAZ**

**Energieverbrauch-Prognose:**
- Mehrkosten: +47 EUR/Jahr
- Mit geregelter Pumpe: +26 EUR/Jahr
- **Entscheidung: Lohnt sich für Qualität?**

---

## 📚 Dokumentation

- [Beta2-Features Dokumentation](docs/BETA_v3.3.0_TESTING.md) (aktualisiert)
- [Validierungs-Tool](tools/compare_hydraulics_v3_2_vs_v3_3.py)
- [ROADMAP Update](docs/ROADMAP.md)

---

## 🐛 Bug Fixes

- Fixed: `adjusted_boreholes` Variable nicht definiert (aus beta1)

---

## 🚀 Nächste Schritte

### beta3 (in 2 Wochen):
- Pumpenauswahl-Assistent (Datenbank mit realen Pumpen)
- Erweiterte Diagramme (Kennlinien, Reynolds-Kurven)
- Feedback aus beta1 + beta2 einarbeiten

### v3.3.0 stable (in 4 Wochen):
- Release mit allen Features
- Migration-Guide von v3.2.1
- Finale Dokumentation

---

## 👥 Credits

- beta1: VDI-Wärmeatlas, UBeG Geothermie-Studie
- beta2: Pumpen-Effizienzklassen nach EU-Verordnung
- Community-Feedback

---

## ⚠️ Wichtig

**v3.2.1 bleibt als stable verfügbar während der Beta-Phase!**

**Feedback zu beta2 besonders wichtig:**
- Sind die Energiekosten-Berechnungen realistisch?
- Ist der Durchfluss-Optimizer hilfreich?
- Funktioniert die Echtzeit-Berechnung flüssig?

---

**Vielen Dank fürs Testing! 🙏**

