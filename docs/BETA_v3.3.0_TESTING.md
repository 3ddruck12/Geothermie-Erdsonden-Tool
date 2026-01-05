# Beta-Testing v3.3.0: Verbesserte Hydraulik-Berechnung

**Version:** v3.3.0-beta1  
**Release-Datum:** Januar 2026  
**Beta-Phase:** 2 Wochen  
**Status:** 🧪 BETA - Für Testing und Validierung

---

## 📋 Was ist neu?

### Phase 1 (beta1): Kern-Korrekturen & Detaillierte Analyse

#### ✅ Hauptänderung: Realistische Stoffwerte nach VDI-Wärmeatlas

Die **Viskosität** von Sole (Wasser-Glykol-Gemisch) wurde für typische Betriebstemperaturen (0°C) korrigiert.

**Quelle:** VDI-Wärmeatlas D3.1, 11. Auflage

**Warum diese Änderung?**
- Die alten Werte entsprachen einer Temperatur von ~15°C
- Reale Betriebstemperatur: -3°C bis 13°C (Mittelwert: ~0°C)
- Quelle: UBeG Geothermie-Studie Gau-Algesheim

#### 🔧 Technische Änderungen

| Konzentration | Viskosität alt | Viskosität neu | Änderung |
|---------------|----------------|----------------|----------|
| 0% (Wasser) | 0.001 Pa·s | 0.0018 Pa·s | +80% |
| 25% Glykol | 0.0019 Pa·s | 0.0037 Pa·s | **+95%** |
| 40% Glykol | 0.0038 Pa·s | 0.0075 Pa·s | +97% |

---

### ⚡ Auswirkungen auf Ihre Berechnungen

#### Was ändert sich?

| Parameter | Wie stark? | Was bedeutet das? |
|-----------|------------|-------------------|
| **Viskosität** | +95% höher | Sole ist "zäher" bei 0°C (realistisch) |
| **Reynolds-Zahl** | -49% niedriger | Strömung weniger turbulent |
| **Druckverlust** | +16% höher | Mehr Widerstand im System |
| **Pumpenleistung** | +16% höher | **Größere Pumpe nötig** |
| **Warnungen** | Häufiger | Mehr Hinweise bei kritischen Werten |

#### Beispiel: 11 kW, 2×100m, ΔT=3K, 25% Glykol

**v3.2.1 (alt):**
- Volumenstrom: 3.19 m³/h
- Reynolds: 11.813 → "Alles gut, turbulent"
- Druckverlust: 2.35 bar
- Pumpe: **418 W**

**v3.3.0-beta1 (neu):**
- Volumenstrom: 3.19 m³/h (unverändert)
- Reynolds: 6.066 → "Noch turbulent, aber näher an Grenze"
- Druckverlust: 2.73 bar (+16%)
- Pumpe: **485 W (+16%)**

---

### 🆕 Neue Features in beta1

#### 1. Detaillierte Druckverlust-Analyse

Neuer Button: **🔍 Detaillierte Druckverlust-Analyse**

Zeigt Aufschlüsselung aller Druckverlust-Komponenten:
- Erdwärmesonden (vertikal)
- Horizontale Anbindung
- Formstücke & Ventile (T-Stücke, Bögen, Absperrschieber)
- Wärmetauscher/Filter
- **Mit prozentualen Anteilen**
- **Mit Optimierungsvorschlägen**

#### 2. Validierungs-Tool

Neues Skript: `tools/compare_hydraulics_v3_2_vs_v3_3.py`

Vergleicht alte vs. neue Berechnungen mit konkreten Zahlen.

**Verwendung:**
```bash
cd "/pfad/zum/Geothermietool"
source venv/bin/activate
python3 tools/compare_hydraulics_v3_2_vs_v3_3.py
```

---

## 🧪 Was sollen Sie testen?

### 1. Vergleichen Sie mit v3.2.1

**Schritte:**
1. Laden Sie Ihre bestehenden `.get`-Projekte in **v3.2.1**
2. Notieren Sie die Hydraulik-Ergebnisse (Pumpenleistung)
3. Laden Sie dieselben Projekte in **v3.3.0-beta1**
4. Vergleichen Sie die Unterschiede

**Zu dokumentieren:**
- Projekt-Parameter (kW, Bohrungen, Tiefe, ΔT)
- Pumpenleistung alt: ___ W
- Pumpenleistung neu: ___ W
- Änderung: _____%

### 2. Vergleichen Sie mit realen Anlagen

**Besonders wichtig!** Wenn Sie bereits Anlagen gebaut haben:

**Fragen:**
- Welche Pumpenleistung haben Sie verbaut?
- Ist die Berechnung von v3.3.0 näher an der Realität?
- Wie hoch ist der tatsächlich gemessene Druckverlust?
- Funktioniert die Anlage wie erwartet?

### 3. Testen Sie die detaillierte Analyse

**Schritte:**
1. Berechnen Sie ein Projekt
2. Klicken Sie auf "Hydraulik berechnen"
3. Klicken Sie auf **"🔍 Detaillierte Druckverlust-Analyse"**

**Zu bewerten:**
- Sind die prozentualen Anteile plausibel?
- Helfen die Optimierungsvorschläge?
- Stimmen die Reynolds-Zahlen mit Erwartungen überein?

### 4. Testen Sie Grenzfälle

**Test-Szenarien:**
- Sehr niedrige Volumenströme (ΔT=5K)
- Hohe Volumenströme (ΔT=2K)
- Tiefe Bohrungen (>150m)
- Viele Bohrungen (>5)
- Hohe Glykol-Konzentrationen (>30%)

---

## 📊 Feedback-Formular

### Projektdaten

**Projekt-Name:** ___________________  
**Leistung:** ___ kW  
**Bohrungen:** ___ × ___ m  
**ΔT:** ___ K  
**Rohrkonfiguration:** Single-U / Doppel-U  
**Glykol-Konzentration:** ___ %

### Vergleich v3.2.1 → v3.3.0-beta1

**Pumpenleistung alt:** ___ W  
**Pumpenleistung neu:** ___ W  
**Änderung:** _____% 

**Reynolds-Zahl alt:** ___  
**Reynolds-Zahl neu:** ___

**Warnungen alt:** Ja / Nein  
**Warnungen neu:** Ja / Nein

### Realitäts-Check (falls Anlage gebaut)

**Verbaute Pumpe:** ___ W  
**Gemessener Druck:** ___ bar  
**Funktioniert die Anlage?** Ja / Nein  
**Welche Version war näher an der Realität?** v3.2.1 / v3.3.0

### Detaillierte Analyse

**Haben Sie die detaillierte Analyse getestet?** Ja / Nein  
**War die Aufschlüsselung hilfreich?** Ja / Nein  
**Waren die Optimierungsvorschläge sinnvoll?** Ja / Nein

### Allgemeines Feedback

**Sind die neuen Werte plausibel?** Ja / Nein  
**Sind die Warnungen hilfreich?** Ja / Nein  
**Ist die Dokumentation verständlich?** Ja / Nein  
**Fehlt etwas?** ___________________

**Weitere Kommentare:**  
_________________________________  
_________________________________  
_________________________________

---

## 📅 Zeitplan

- **Beta-Start:** [Einsetzen bei Release]
- **Beta-Ende:** [+2 Wochen]
- **Stable Release v3.3.0:** [+3 Wochen]

**Während der Beta-Phase bleibt v3.2.1 als stable verfügbar!**

---

## 💡 Feedback senden

**GitHub Issues:** [Link zum Repository]  
**E-Mail:** [Kontakt-E-Mail]  
**Forum:** [Falls vorhanden]

---

## ❓ Häufige Fragen

### Warum sind die Pumpenleistungen höher?

Die alten Werte waren zu optimistisch. Sole bei 0°C ist viskoser als bei 15°C. Die neuen Werte entsprechen der realen Betriebstemperatur und verhindern Unterdimensionierung.

### Sind meine alten Projekte jetzt falsch?

Nicht falsch, aber zu optimistisch. Wenn Sie bereits eine Anlage gebaut haben und sie funktioniert, ist alles gut. Für neue Projekte sind die neuen Werte sicherer.

### Kann ich die alten Werte weiter nutzen?

In v3.2.1 (stable) bleiben die alten Werte verfügbar. Nach der Beta-Phase wird v3.3.0 stable und ersetzt v3.2.1. Ein "Legacy-Modus" ist nicht geplant.

### Stimmen die neuen Werte mit professioneller Software überein?

Ja! Die Werte basieren auf VDI-Wärmeatlas und wurden mit Referenz-Studien (z.B. UBeG Gau-Algesheim) abgeglichen. Tools wie EED und GHEtool nutzen ähnliche Werte.

---

## 📚 Referenzen

1. **VDI-Wärmeatlas D3.1** (11. Auflage, 2024)  
   Stoffwerte für Ethylenglykol-Wasser-Gemische

2. **UBeG Geothermie-Studie Gau-Algesheim** (2019)  
   "Temperaturen im Heizbetrieb zwischen etwa 13°C und -3°C"  
   [Link zur Studie](https://www.vg-gau-algesheim.de/.../Geothermie_Studie.pdf)

3. **GHEtool** (Open Source)  
   Wissenschaftlich validiertes Tool aus Belgien (KU Leuven)  
   [GitHub](https://github.com/wouterpeere/GHEtool)

---

**Vielen Dank fürs Testing! 🙏**

Ihr Feedback hilft, das Tool zu verbessern und sicherzustellen, dass die Berechnungen der Realität entsprechen.

