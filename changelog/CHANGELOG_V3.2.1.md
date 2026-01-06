# Changelog V3.2.1

## 🚀 Version 3.2.1 - "Maximale Sondenlänge" (Januar 2026)

### 🆕 Neue Features

#### VDI 4640: Maximale Sondenlänge pro Bohrung
- **Eingabefeld**: "Max. Sondenlänge pro Bohrung [m]" in der Bohrloch-Konfiguration
- **Automatische Anpassung**: Wenn die berechnete Sondenlänge die maximale Länge überschreitet, wird automatisch die Anzahl der Bohrungen erhöht
- **Intelligente Optimierung**: System findet die optimale Kombination aus Tiefe und Anzahl der Bohrungen
- **Nur VDI 4640**: Diese Funktion wird nur bei der VDI 4640 Methode verwendet, bei der iterativen Methode ignoriert

#### Verbesserte Ergebnisanzeige
- **Gesamtlänge der Leitungen**: Wird jetzt für beide Berechnungsmethoden angezeigt
- **Leitungen pro Bohrung**: 
  - Single-U: 2 Leitungen (Vorlauf + Rücklauf)
  - Double-U / 4-Rohr: 4 Leitungen
  - Coaxial: 2 Leitungen
- **Klarere Darstellung**: Unterscheidung zwischen Gesamtlänge (Bohrungen) und Gesamtlänge (Leitungen)

### 🔧 Verbesserungen

#### GUI
- **Bessere Beschriftung**: "Gesamtlänge (Bohrungen)" und "Gesamtlänge (Leitungen)" klar getrennt
- **Info-Hinweis**: Eingabefeld zeigt an, dass es nur bei VDI 4640 verwendet wird
- **Automatische Aktualisierung**: Anzahl Bohrungen wird automatisch im Eingabefeld aktualisiert, wenn Anpassung erfolgt

#### Berechnungslogik
- **Robuste Parameter-Sammlung**: Verbesserte Fehlerbehandlung bei leeren Eingabefeldern
- **Iterative Optimierung**: Bis zu 20 Iterationen zur Findung der optimalen Bohrungsanzahl

### 🐛 Bugfixes
- Keine bekannten Bugs in dieser Version

### 📝 Technische Details

#### Neue Methode
- `_get_pipe_length_factor(pipe_config)`: Berechnet die Anzahl der Leitungen pro Bohrung basierend auf der Rohrkonfiguration

#### Geänderte Methoden
- `_add_borehole_config_section()`: Neues Eingabefeld hinzugefügt
- `_run_calculation()`: VDI 4640 Logik erweitert um maximale Sondenlänge
- `_display_results()`: Gesamtlänge der Leitungen hinzugefügt

### 🔄 Migration

Keine Migration erforderlich. V3.2.1 ist vollständig kompatibel mit V3.2.0 `.get` Dateien.

---

**Vollständige Dokumentation**: Siehe [README.md](README.md) und [VDI4640_SCHNELLANLEITUNG.py](VDI4640_SCHNELLANLEITUNG.py)





