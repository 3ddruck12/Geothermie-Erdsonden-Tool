"""Ergebnis-Tab: Anzeige der Berechnungsergebnisse.

Extrahiert aus main_window_v3_professional.py (V3.4 Refactoring).
"""

import tkinter as tk
from tkinter import ttk


class ResultsTab:
    """Verwaltet den Ergebnisse-Tab.
    
    Zeigt Berechnungsergebnisse als formatierten Text an.
    """

    def __init__(self, parent_frame, app):
        """
        Args:
            parent_frame: ttk.Frame in dem der Tab aufgebaut wird.
            app: Referenz auf GeothermieGUIProfessional.
        """
        self.frame = parent_frame
        self.app = app
        self._build()

    def _build(self):
        """Erstellt den Ergebnisse-Tab."""
        container = ttk.Frame(self.frame)
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        text_frame = ttk.LabelFrame(container, text="📊 Berechnungsergebnisse",
                                     padding=5)
        text_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.results_text = tk.Text(text_frame, wrap=tk.WORD,
                                     font=("Courier", 10),
                                     yscrollcommand=scrollbar.set)
        self.results_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.results_text.yview)

        self.results_text.insert(
            "1.0",
            "Keine Berechnung durchgeführt.\n\n"
            "Bitte Parameter eingeben und Berechnung starten.")
        self.results_text.config(state=tk.DISABLED)

        # Referenz auf App spiegeln
        self.app.results_text = self.results_text
