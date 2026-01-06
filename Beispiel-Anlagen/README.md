# Beispiel-Anlagen

Dieser Ordner enthält typische Beispielanlagen für Erdwärmesonden-Systeme, die für Tests und Validierungen verwendet werden können.

## Dateien

- `beispielanlagen.csv` - CSV-Datei mit 3 typischen Beispielanlagen
- `load_examples.py` - Python-Skript zum Laden der Beispielanlagen

## Beispielanlage 1 – Einfamilienhaus (Neubau, Niedertemperatur)

**Gebäudetyp:** EFH, KfW40  
**Heizsystem:** Sole/Wasser-WP, Fußbodenheizung

### Erdsondenfeld
- Anzahl Sonden: 1
- Sondentiefe: 120 m
- Bohrdurchmesser: 152 mm
- Rohr: PE100 RC, Doppel-U, 32 × 2,9 mm
- Verpressmaterial: λ = 2,0 W/mK

### Thermische Kenndaten
- Entzugsleistung spezifisch: 45 W/m
- Maximale Entzugsleistung: 5,4 kW
- Jahresarbeit aus Erdreich: 9.500 kWh/a
- Betriebsstunden WP: 2.100 h/a

### Solebetrieb
- Solemedium: 25 % Ethylenglykol
- Volumenstrom: 0,9 m³/h
- Eintritt Sole WP (min): -1,5 °C
- Austritt Sole WP (max): -4,5 °C
- ΔT Sole: 3 K

### Wärmepumpe
- Heizleistung B0/W35: 6,5 kW
- COP (B0/W35): 4,6
- Jahresarbeitszahl (JAZ): 4,4

---

## Beispielanlage 2 – Mehrfamilienhaus (Sanierung)

**Gebäudetyp:** MFH, 6 Wohneinheiten  
**Heizsystem:** Radiatoren + Teil-FBH

### Erdsondenfeld
- Anzahl Sonden: 4
- Sondentiefe: 150 m
- Sondenabstand: 6 m
- Gesamtsondenlänge: 600 m
- Rohr: Doppel-U 40 × 3,7 mm
- Verpressmaterial: λ = 2,3 W/mK

### Thermische Kenndaten
- Entzugsleistung spezifisch: 50 W/m
- Maximale Entzugsleistung: 30 kW
- Jahresenergie Erdreich: 58.000 kWh/a
- Heizlast Gebäude: 32 kW

### Solebetrieb
- Solemedium: 30 % Propylenglykol
- Volumenstrom gesamt: 4,2 m³/h
- Eintritt Sole WP (min): -2,8 °C
- Austritt Sole WP (max): -6,0 °C
- ΔT Sole: 3,2 K

### Wärmepumpe
- Heizleistung B0/W45: 28 kW
- COP (B0/W45): 3,9
- Jahresarbeitszahl: 3,6

---

## Beispielanlage 3 – Gewerbe (Bürogebäude mit Kühlung)

**Gebäudetyp:** Büro / Verwaltung  
**Heiz- & Kühlsystem:** WP + passive Kühlung

### Erdsondenfeld
- Anzahl Sonden: 10
- Sondentiefe: 180 m
- Sondenabstand: 7 m
- Gesamtsondenlänge: 1.800 m
- Rohr: Doppel-U 40 mm
- Verpressmaterial: λ = 2,5 W/mK

### Thermische Kenndaten
- Heiz-Entzugsleistung: 55 W/m
- Kühl-Eintragsleistung: 40 W/m
- Jahresheizarbeit: 120.000 kWh/a
- Jahreskühlarbeit (Rückführung): 65.000 kWh/a
- Betriebsstunden Heizen: 2.400 h
- Betriebsstunden Kühlen: 1.100 h

### Solebetrieb
- Volumenstrom gesamt: 9,5 m³/h
- Soletemperatur Winter min: -1,0 °C
- Soletemperatur Sommer max: 18 °C
- ΔT Heizen: 3 K
- ΔT Kühlen: 4 K

### Wärmepumpe
- Heizleistung B0/W35: 65 kW
- COP Heizen: 4,8
- EER passive Kühlung: >20

---

## Verwendung

Die CSV-Datei kann mit Python geladen werden:

```python
import pandas as pd

# Lade Beispielanlagen
df = pd.read_csv('Beispiel-Anlagen/beispielanlagen.csv')

# Beispielanlage 1
anlage1 = df[df['Beispielanlage'] == 1].iloc[0]
print(f"Anzahl Sonden: {anlage1['Anzahl_Sonden']}")
print(f"Sondentiefe: {anlage1['Sondentiefe_m']} m")
```

Oder verwenden Sie das bereitgestellte `load_examples.py` Skript.

