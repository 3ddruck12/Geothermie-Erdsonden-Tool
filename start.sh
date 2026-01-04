#!/bin/bash
# Start-Script für das Geothermie Erdsonden-Berechnungstool

# Wechsle ins Projektverzeichnis
cd "$(dirname "$0")"

# Prüfe ob virtuelle Umgebung existiert
if [ ! -d "venv" ]; then
    echo "Erstelle virtuelle Umgebung..."
    python3 -m venv venv
    source venv/bin/activate
    echo "Installiere Abhängigkeiten..."
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Starte die Anwendung
echo "Starte Geothermietool..."
python main.py





