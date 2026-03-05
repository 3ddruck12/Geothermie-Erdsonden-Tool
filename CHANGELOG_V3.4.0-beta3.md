# Changelog V3.4.0-beta3

> **Release: Februar 2026**
> **Baut auf V3.4.0-beta2.2 auf**

## 🆕 Neue Features – Phase 3: Langzeit-Simulation

### Langzeit-Temperaturentwicklung
- **`calculations/longterm_simulation.py`**: Implementiert `LongtermSimulator` mittels Temporal Superposition nach Eskilson (1987)
- Berechnung monatlicher Fluid- und Erdreich-Temperaturen über konfigurierbare Zeiträume (Desktop: max. 25 Jahre, Cloud-ready: bis 50 Jahre)
- Neues Diagramm **„Langzeit-Temperaturentwicklung"**: Jahre vs. Fluid-Temperatur mit Min/Max-Toleranzband
- Warnmeldungen bei zu niedrigen Fluid-Temperaturen werden in den Erweiterten Ergebnissen angezeigt

### Regenerations-Analyse
- **`calculations/regeneration_analysis.py`**: Analysiert die jährliche thermische Balance (Wärmeeintrag vs. Wärmeentzug)
- `check_ground_depletion()`: Erkennt langfristige Abkühltrends und gibt Handlungsempfehlungen
- `calculate_optimal_balance()`: Berechnet den optimalen Kühlanteil für Langzeitstabilität
- Neues Diagramm **„Thermische Balance"**: Jährlicher Entzug/Eintrag und kumulative Bilanz

### Saisonale Effizienz (SCOP/SEER/JAZ)
- **`calculations/seasonal_efficiency.py`**: Physikalisch basiertes Carnot-COP-Modell
- Temperatur- und teillastabhängige COP-Berechnung (`SeasonalEfficiencyCalculator`)
- `calculate_monthly_cop()`: Monatliche COP-Werte basierend auf Fluid-Temperatur
- `calculate_jaz()`: Jahresarbeitszahl (JAZ) aus monatlichen Lastprofilen
- `compare_jaz_by_depth()`: JAZ-Vergleich bei verschiedenen Sondentiefen
- Neues Diagramm **„Monatliche COP-Entwicklung"**: COP-Verlauf über die Betriebsjahre
- Neues Diagramm **„JAZ-Vergleich"**: Jahresarbeitszahl vs. Sondenteife

## 🔧 Fixes
- **`calculations/g_functions.py`**: Interpolationsmethode repariert – Finite Line Source läuft korrekt gegen ICS und stationäre Grenzwerte
- **Thermik-Vorzeichen-Logik**: Abkühlung bei Entzug jetzt physikalisch korrekt (positive Vorzeichen-Konvention durchgängig)
- **G-Funktions-Interpolation**: Langzeit-Trends sind damit physikalisch plausibel

## 🧪 Tests
- `tests/test_longterm_simulation.py` – Neue Unit-Tests für Langzeit-Simulation
- `tests/test_regeneration_analysis.py` – Neue Unit-Tests für Regenerations-Analyse
- `tests/test_seasonal_efficiency.py` – Neue Unit-Tests für JAZ und COP-Modell
- **Gesamt: 129 Tests, alle grün** (`pytest` läuft fehlerfrei durch)

## 📊 Diagramme-Tab (gesamt: 17)
Vier neue Langzeit-Diagramme hinzugefügt:
- **14.** Langzeit-Temperaturentwicklung
- **15.** Thermische Balance / Regeneration
- **16.** Monatliche COP-Entwicklung über Jahre
- **17.** JAZ-Vergleich bei verschiedenen Sondentiefen

## Vollständige Feature-Liste

Siehe:
- [CHANGELOG_V3.4.0-beta1.md](CHANGELOG_V3.4.0-beta1.md) – Architektur-Refactoring, Unit-Tests
- [CHANGELOG_V3.4.0-beta2.md](CHANGELOG_V3.4.0-beta2.md) – Monatliche Lastprofile, Warmwasser
- [CHANGELOG_V3.4.0-beta2.2.md](CHANGELOG_V3.4.0-beta2.2.md) – W/m-Zeitreihe, Build-Fixes
