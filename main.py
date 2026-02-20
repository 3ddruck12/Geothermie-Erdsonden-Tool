#!/usr/bin/env python3
"""
Geothermie Erdsonden-Berechnungstool

Haupteinstiegspunkt für die Anwendung.
"""

import tkinter as tk
import sys
import os
import logging
import ctypes

# Logging konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("geothermie")

# Füge den aktuellen Ordner zum Python-Pfad hinzu
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Importiere die GUI
from gui.main_window_v3_professional import GeothermieGUIProfessional as GUI
logger.info("Starte Professional GUI V3.4")


def main():
    """Hauptfunktion - startet die GUI."""
    try:
        # Erstelle Hauptfenster
        # className für Linux: WM_CLASS = StartupWMClass in .desktop (Taskleisten-Icon)
        root = tk.Tk(className='geothermie-erdsondentool')
        
        # Setze App-Icon für Windows Taskleiste
        try:
            # Pfad für PyInstaller (OneDir/OneFile) berücksichtigen
            base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
            icon_path = os.path.join(base_path, "Icons", "icon.ico")
            if not os.path.exists(icon_path):
                icon_path = os.path.join(base_path, "Icons", "favicon.ico")
            
            if os.path.exists(icon_path):
                root.iconbitmap(icon_path)
            
            # Windows AppUserModelID setzen, damit das Icon in der Taskleiste korrekt angezeigt wird
            if sys.platform == "win32":
                myappid = '3ddruck12.geothermie.erdsondentool.v3'
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except Exception as e:
            logger.warning("Konnte Icon nicht setzen: %s", e)
        
        # Erstelle GUI
        app = GUI(root)
        
        logger.info("GUI erstellt, starte Event-Loop...")
        
        # Starte Event-Loop
        root.mainloop()
        
    except Exception as e:
        logger.critical("Fehler beim Starten: %s", e, exc_info=True)
        
        # Zeige Fehler in Dialog
        import tkinter.messagebox as mb
        mb.showerror("Fehler", f"Fehler beim Starten:\n{e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

