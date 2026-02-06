#!/usr/bin/env python3
"""
Geothermie Erdsonden-Berechnungstool

Haupteinstiegspunkt für die Anwendung.
"""

import tkinter as tk
import sys
import os
import logging

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
try:
    # Versuche zuerst die Professional V3 GUI mit allen Features
    from gui.main_window_v3_professional import GeothermieGUIProfessional as GUI
    logger.info("Starte Professional GUI V3")
except ImportError as e:
    logger.warning("Import der V3 Professional GUI fehlgeschlagen: %s", e)
    try:
        # Fallback auf Extended V2 GUI
        from gui.main_window_extended import GeothermieGUIExtended as GUI
        logger.info("Starte Extended GUI V2 (Fallback)")
    except ImportError as e2:
        logger.warning("Import der Extended GUI fehlgeschlagen: %s", e2)
        # Letzter Fallback auf Original
        from gui.main_window import GeothermieGUI as GUI
        logger.info("Starte Original GUI V1 (Fallback)")


def main():
    """Hauptfunktion - startet die GUI."""
    try:
        # Erstelle Hauptfenster
        root = tk.Tk()
        
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

