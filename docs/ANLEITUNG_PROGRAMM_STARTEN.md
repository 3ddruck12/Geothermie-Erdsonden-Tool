# Anleitung: Programm starten

## Geothermie Erdsonden-Tool V3.3.0-beta3

---

## 🚀 Schnellstart

### Option 1: Direkt starten (mit venv)

```bash
cd "/home/jens/Dokumente/Software Projekte/Geothermietool"
source venv/bin/activate
python3 main.py
```

### Option 2: Mit Start-Skript

```bash
cd "/home/jens/Dokumente/Software Projekte/Geothermietool"
./start.sh
```

### Option 3: Windows (falls vorhanden)

```cmd
cd "C:\Pfad\zum\Geothermietool"
start.bat
```

---

## 📋 Voraussetzungen

### Python-Version
- Python 3.8 oder höher erforderlich

### Abhängigkeiten
Alle benötigten Pakete sind in `requirements.txt` aufgelistet:
- numpy >= 1.24.0
- matplotlib >= 3.7.0
- pandas >= 2.0.0
- scipy >= 1.10.0
- reportlab >= 4.0.0
- requests >= 2.31.0
- pygfunction[plot] >= 2.3.0 (optional, für Bohrfeld-Simulationen)

### Installation der Abhängigkeiten

Falls das Programm nicht startet (z.B. "ModuleNotFoundError: No module named 'matplotlib'"):

```bash
cd "/home/jens/Dokumente/Software Projekte/Geothermietool"

# Mit virtuellem Environment
source venv/bin/activate
pip install -r requirements.txt

# Oder ohne venv (nicht empfohlen)
pip3 install -r requirements.txt
```

---

## 🖥️ Programm starten

### Schritt 1: Terminal öffnen

- **Linux**: Terminal öffnen (Strg+Alt+T)
- **Windows**: CMD oder PowerShell öffnen

### Schritt 2: Zum Programmverzeichnis wechseln

```bash
cd "/home/jens/Dokumente/Software Projekte/Geothermietool"
```

### Schritt 3: Virtuelles Environment aktivieren (falls vorhanden)

```bash
source venv/bin/activate
```

Sie sollten dann `(venv)` am Anfang der Zeile sehen.

### Schritt 4: Programm starten

```bash
python3 main.py
```

---

## ✅ Erfolgreicher Start

Wenn alles funktioniert, sollten Sie sehen:

```
✓ Starte Professional GUI V3
✓ GUI erstellt, starte Event-Loop...
```

Das Hauptfenster öffnet sich mit:
- **Titel**: "Geothermie Erdsonden-Tool - Professional Edition V3.2.1"
- **Größe**: 1800x1100 Pixel
- **Tabs**: Eingabe, Ergebnisse, Diagramme, Material & Hydraulik, etc.

---

## ❌ Fehlerbehebung

### Fehler: "No module named 'matplotlib'"

**Lösung**: Abhängigkeiten installieren
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Fehler: "python3: command not found"

**Lösung**: Python 3 installieren oder `python` statt `python3` verwenden
```bash
python main.py
```

### Fehler: "Permission denied"

**Lösung**: Ausführungsrechte setzen
```bash
chmod +x start.sh
chmod +x main.py
```

### Programm startet, aber Fenster erscheint nicht

**Mögliche Ursachen**:
- Programm läuft im Hintergrund
- Display-Variable nicht gesetzt (bei SSH)
- Andere GUI läuft bereits

**Lösung**: 
```bash
# Prüfen ob Programm läuft
ps aux | grep "python.*main.py"

# Bei SSH: X11-Forwarding aktivieren
ssh -X username@hostname
```

---

## 📝 Tastenkürzel

Nach dem Start:
- **Strg+O**: Projekt laden (.get Datei)
- **Strg+S**: Projekt speichern (.get Datei)
- **Strg+P**: PDF-Bericht erstellen

---

## 🔄 Programm beenden

- **Fenster schließen**: Klicken Sie auf das X-Symbol
- **Menü**: Datei → Beenden
- **Terminal**: Strg+C (falls im Terminal gestartet)

---

## 💡 Tipps

1. **Erstes Mal starten**: 
   - Prüfen Sie, ob alle Abhängigkeiten installiert sind
   - Testen Sie mit einem Beispiel-Projekt

2. **Performance**:
   - Bei vielen Diagrammen kann das Laden etwas dauern
   - Diagramme werden bei Bedarf aktualisiert

3. **Updates**:
   - Regelmäßig `git pull` ausführen für Updates
   - Bei Problemen: `pip install -r requirements.txt --upgrade`

---

## 📞 Support

Bei Problemen:
1. Prüfen Sie die Fehlermeldungen im Terminal
2. Prüfen Sie die Log-Dateien (falls vorhanden)
3. Dokumentation: `docs/` Verzeichnis

---

**Version**: 3.3.0-beta3  
**Letzte Aktualisierung**: Januar 2026
