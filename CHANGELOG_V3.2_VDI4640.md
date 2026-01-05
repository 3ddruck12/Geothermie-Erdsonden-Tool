# 🆕 Changelog V3.2 - VDI 4640 Integration

## Release: V3.2.0 (Januar 2025)

### 🎯 **Hauptfeature: VDI 4640 / Koenigsdorff-Methode**

Die Version 3.2 integriert die **VDI 4640-konforme Berechnungsmethode** nach Koenigsdorff als Alternative zur iterativen Methode.

#### **Was ist neu?**

✅ **Zwei Berechnungsmethoden**:
- **Iterativ** (Eskilson/Hellström): Bisherige Standard-Methode
- **VDI 4640** (Koenigsdorff): Neue normkonforme Methode

✅ **VDI 4640 Features**:
- ✓ Drei Lasttypen (Grundlast, Periodisch, Spitzenlast)
- ✓ Drei Zeitskalen (10 Jahre, 1 Monat, 6 Stunden)
- ✓ Separate Auslegung für Heizen und Kühlen
- ✓ Automatische Erkennung der dominanten Last
- ✓ Berechnung der Wärmepumpenaustrittstemperatur
- ✓ Detaillierte Temperaturkomponenten

✅ **GUI-Anpassungen**:
- Auswahl der Berechnungsmethode auf Seite 1
- Jahres-Heizenergie jetzt in **kWh** (statt MWh)
- EER für Kühlen hinzugefügt
- Temperaturdifferenz Fluid (ΔT) hinzugefügt
- Erweiterte Ergebnis-Darstellung auf Seite 2

---

## 📐 **VDI 4640 Berechnungslogik**

### **Formel für Sondenlänge:**

```
H_Sonde = [Q_netto·(R_grundlast + R_B) + Q_per·(R_per + R_B) + Q_peak·(R_peak + R_B)]
          / (ΔT_Reaktion · N_Sonden)
```

### **Wärmepumpenaustrittstemperatur:**

```
T_WP,aus = T_ungestört ± ΔT_Grundlast ± ΔT_per ± ΔT_peak - 0.5·ΔT_Fluid
```

Vorzeichen:
- **Heizen**: `−` (Erdreich kühlt ab)
- **Kühlen**: `+` (Erdreich erwärmt sich)

### **Thermische Widerstände:**

```
R = g / (2π · λ)
```

Wobei `g` die g-Funktion für die jeweilige Zeitskala ist.

---

## 🔥 **Dominante Kühllast**

Die Methode erkennt automatisch, ob **Heizen oder Kühlen** auslegungsrelevant ist:

- **Heizen dominant**: Winterklimazonen, Wohngebäude
- **Kühlen dominant**: Bürogebäude, hohe interne Lasten, niedrige T_max

Bei **dominanter Kühllast** wird die Sonde nach Kühlen dimensioniert, um überhöhte Temperaturen zu vermeiden.

---

## 🧮 **Lastberechnung**

### **Heizen:**
```
Effizienz = (COP - 1) / COP
Q_Grundlast = Jahresenergie · Effizienz / 8760h
Q_Periodisch = (Max. Monat · Effizienz) / 730h
Q_Peak = Spitzenlast · Effizienz
```

### **Kühlen:**
```
Effizienz = (EER + 1) / EER  # inkl. elektrische Leistung
Q_Grundlast = Jahresenergie · Effizienz / 8760h
Q_Periodisch = (Max. Monat · Effizienz) / 730h
Q_Peak = Spitzenlast · Effizienz
```

---

## 🖥️ **GUI-Änderungen**

### **Seite 1 - Eingabe:**

#### **Wärmepumpe & Lasten:**
```
COP Heizen:               4.0      (vorher: nur "COP")
EER Kühlen:               4.0      (NEU)
Jahres-Heizenergie:    12000 kWh   (vorher: 12 MWh)
Jahres-Kühlenergie:        0 kWh   (vorher: 0 MWh)
Temperaturdifferenz Fluid: 3.0 K   (NEU)
```

#### **Simulation:**
```
Berechnungsmethode:
  ⚙️  Iterative Methode (Eskilson/Hellström)
  📐 VDI 4640 Methode (Grundlast/Periodisch/Peak)  ← NEU
```

### **Seite 2 - Ergebnisse:**

#### **VDI 4640 Ergebnis-Darstellung:**

```
📐 BERECHNUNGSMETHODE: VDI 4640 (Koenigsdorff)

🎯 AUSLEGUNGSFALL
✓ HEIZEN ist auslegungsrelevant
  Erforderliche Sondenlänge: 141.8 m
  (Kühlen würde nur 62.0 m benötigen)

🌡️ WÄRMEPUMPENAUSTRITTSTEMPERATUREN
Heizen (min): -3.50 °C
  Komponenten:
    T_ungestört:        10.00 °C
    - ΔT_Grundlast:      8.234 K
    - ΔT_Periodisch:     3.156 K
    - ΔT_Peak:           1.109 K
    - 0.5·ΔT_Fluid:      1.50 K

♨️ THERMISCHE WIDERSTÄNDE
R_Grundlast (10 Jahre):   0.388660 m·K/W  (g=4.8841)
R_Periodisch (1 Monat):   0.275161 m·K/W  (g=3.4578)
R_Peak (6 Stunden):       0.052481 m·K/W  (g=0.6595)
R_Bohrloch:               0.100000 m·K/W

⚡ LASTDATEN
HEIZEN:
  Jahresenergie:      10000 kWh
  Q_Nettogrundlast:   0.856 kW  (Jahresmittel)
  Q_Periodisch:       1.591 kW  (kritischster Monat)
  Q_Peak:             4.500 kW  (Spitzenlast)
```

---

## 🧪 **Tests**

Alle Tests erfolgreich:

- ✅ **Test 1**: Heizen dominant (Winterklimazone)
- ✅ **Test 2**: Kühlen dominant (Bürogebäude)
- ✅ **Test 3**: Mehrere Bohrungen
- ✅ **Test 4**: Thermische Widerstände (Plausibilität)

Run:
```bash
python3 test_vdi4640_integration.py
```

---

## 📚 **Neue Dateien**

```
calculations/vdi4640.py              # VDI 4640 Berechnungsmodul
test_vdi4640_integration.py          # Integrationstests
CHANGELOG_V3.2_VDI4640.md           # Diese Datei
```

---

## 🔄 **Abwärtskompatibilität**

- ✅ Iterative Methode bleibt Standard
- ✅ Alle bisherigen Berechnungen funktionieren weiterhin
- ✅ `.get`-Dateien werden automatisch migriert
- ✅ VDI 4640 ist opt-in (muss gewählt werden)

---

## 🎓 **Quellen**

- VDI 4640 Blatt 2: Thermische Nutzung des Untergrunds
- Koenigsdorff, R.: Oberflächennahe Geothermie für Gebäude
- Eskilson, P.: Thermal Analysis of Heat Extraction Boreholes
- Hellström, G.: Ground Heat Storage

---

## 🚀 **Ausblick V3.3**

Geplant:
- Monatliche Lastverteilungs-Editor
- ASHRAE Handbook Integration
- Export von VDI 4640 Details ins PDF
- Vergleichs-Modus (Iterativ vs. VDI)

---

**Entwickelt mit ❤️ für professionelle Erdwärmesonden-Auslegung**








