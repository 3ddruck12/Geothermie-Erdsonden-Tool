@echo off
REM Startskript für Geothermie Erdsonden-Tool (Windows)

cd /d "%~dp0"

REM Aktiviere virtuelle Umgebung
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else (
    echo Fehler: Virtuelle Umgebung 'venv' nicht gefunden!
    echo Bitte führen Sie zuerst 'python -m venv venv' aus.
    pause
    exit /b 1
)

REM Starte Programm
python main.py

pause


