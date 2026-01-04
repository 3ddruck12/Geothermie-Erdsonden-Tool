#!/usr/bin/env python3
"""
Schnellanleitung: VDI 4640 Methode verwenden

So nutzt du die neue VDI 4640 Berechnungsmethode in V3.2:
"""

print("""
╔══════════════════════════════════════════════════════════════════════════╗
║                                                                          ║
║        🌡️  GET V3.2: VDI 4640 SCHNELLANLEITUNG 📐                      ║
║                                                                          ║
╚══════════════════════════════════════════════════════════════════════════╝

📋 NEUE FEATURES IN V3.2:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ VDI 4640 Berechnungsmethode nach Koenigsdorff
✅ Heiz- und Kühllast getrennt ausgelegt
✅ Dominante Last wird automatisch erkannt
✅ Wärmepumpenaustrittstemperatur berechnet
✅ Drei Zeitskalen (10 Jahre, 1 Monat, 6 Stunden)
✅ Jahres-Heizenergie jetzt in kWh (statt MWh)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔧 SO VERWENDEST DU VDI 4640:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1️⃣  Starte die GUI:
   $ python3 main.py

2️⃣  Gehe zu Tab "📝 Eingabe & Konfiguration"

3️⃣  Scrolle nach unten zur Sektion "⏱️ SIMULATION"

4️⃣  Wähle Berechnungsmethode:
   
   [ ] ⚙️  Iterative Methode (Eskilson/Hellström)
   [✓] 📐 VDI 4640 Methode (Grundlast/Periodisch/Peak)  ← HIER KLICKEN!

5️⃣  Fülle die Felder aus:
   
   ♨️ WÄRMEPUMPE & LASTEN:
   ├─ COP Heizen:                4.0
   ├─ EER Kühlen:                4.0
   ├─ Jahres-Heizenergie:    12000 kWh  ← NEU: jetzt kWh statt MWh!
   ├─ Jahres-Kühlenergie:        0 kWh
   ├─ Heiz-Spitzenlast:        6.0 kW
   ├─ Kühl-Spitzenlast:        0.0 kW
   ├─ Min. Fluidtemperatur:   -2.0 °C
   ├─ Max. Fluidtemperatur:   35.0 °C
   └─ Temperaturdifferenz:     3.0 K   ← NEU!

6️⃣  Klicke "Berechnung starten"

7️⃣  Gehe zu Tab "📊 Ergebnisse"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 WAS DU SIEHST (VDI 4640 ERGEBNIS):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 AUSLEGUNGSFALL
✓ HEIZEN ist auslegungsrelevant
  Erforderliche Sondenlänge: 141.8 m
  (Kühlen würde nur 62.0 m benötigen)
  
  → Ausgelegte Sondenlänge: 141.8 m
  → Anzahl Bohrungen: 1
  → Gesamtlänge: 141.8 m

🌡️  WÄRMEPUMPENAUSTRITTSTEMPERATUREN
Heizen (minimale WP-Austrittstemperatur): -3.50 °C
  Komponenten:
    T_ungestört:            10.00 °C
    - ΔT_Grundlast:          8.234 K
    - ΔT_Periodisch:         3.156 K
    - ΔT_Peak:               1.109 K
    - 0.5 · ΔT_Fluid:        1.50 K

Kühlen (maximale WP-Austrittstemperatur): 19.43 °C
  [... weitere Details ...]

♨️  THERMISCHE WIDERSTÄNDE
R_Grundlast (10 Jahre):     0.388660 m·K/W  (g=4.8841)
R_Periodisch (1 Monat):     0.275161 m·K/W  (g=3.4578)
R_Peak (6 Stunden):         0.052481 m·K/W  (g=0.6595)
R_Bohrloch:                 0.100000 m·K/W

⚡ LASTDATEN
HEIZEN:
  Jahresenergie:         10000 kWh
  Q_Nettogrundlast:      0.856 kW  (Jahresmittel)
  Q_Periodisch:          1.591 kW  (kritischster Monat)
  Q_Peak:                4.500 kW  (Spitzenlast)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🤔 WANN VDI 4640 VERWENDEN?
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Verwende VDI 4640 wenn:
   • Du normkonforme Auslegung nach VDI 4640 benötigst
   • Du Heiz- UND Kühllast hast
   • Du wissen willst, welche Last auslegungsrelevant ist
   • Du detaillierte Temperaturkomponenten brauchst
   • Du für Behörden/Gutachter dokumentieren musst

⚙️  Verwende Iterativ wenn:
   • Du das bisherige Verfahren bevorzugst
   • Du nur Heizlast hast (keine Kühlung)
   • Du die klassische Eskilson-Methode willst
   • Du Kompatibilität zu alten Projekten brauchst

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 BEISPIELSZENARIEN:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🏠 Wohnhaus (Heizen dominant):
   Jahres-Heizenergie:    15000 kWh
   Jahres-Kühlenergie:     1000 kWh
   → Ergebnis: HEIZEN ist auslegungsrelevant

🏢 Bürogebäude (Kühlen dominant):
   Jahres-Heizenergie:     8000 kWh
   Jahres-Kühlenergie:    20000 kWh
   → Ergebnis: KÜHLEN ist auslegungsrelevant!
   → Sonde wird länger dimensioniert, um Überhitzung zu vermeiden

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📖 WEITERE INFO:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Dokumentation: docs/ROADMAP.md
Changelog:     CHANGELOG_V3.2_VDI4640.md
Tests:         python3 test_vdi4640_integration.py

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Viel Erfolg mit der VDI 4640 Methode! 🚀

""")




