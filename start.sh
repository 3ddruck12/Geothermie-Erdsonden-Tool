#!/bin/bash
# Startskript für Geothermie Erdsonden-Tool

cd "$(dirname "$0")"

# Aktiviere virtuelle Umgebung
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "Fehler: Virtuelle Umgebung 'venv' nicht gefunden!"
    echo "Bitte führen Sie zuerst 'python3 -m venv venv' aus."
    exit 1
fi

# Starte Programm
python3 main.py
