"""Material & Hydraulik Tab: Verfüllmaterial- und Hydraulik-Anzeige.

Extrahiert aus main_window_v3_professional.py (V3.4 Refactoring).
"""

import tkinter as tk
from tkinter import ttk


class MaterialsTab:
    """Verwaltet den Material & Hydraulik Tab.
    
    Zeigt Verfüllmaterial-Berechnungen, Hydraulik-Ergebnisse,
    und Detailanalysen (Energie, Druckverlust, Pumpen).
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
        """Erstellt den Material & Hydraulik Tab."""
        # Scrollbarer Container
        canvas = tk.Canvas(self.frame)
        scrollbar = ttk.Scrollbar(self.frame, orient="vertical",
                                   command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        canvas_window = canvas.create_window((0, 0), window=scrollable_frame,
                                              anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        def configure_canvas_width(event):
            canvas.itemconfig(canvas_window, width=event.width)
            canvas.configure(scrollregion=canvas.bbox("all"))

        canvas.bind('<Configure>', configure_canvas_width)
        scrollable_frame.bind(
            '<Configure>',
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        scrollbar.pack(side="right", fill="y")

        # ── Materialmengen-Anzeige ──
        ttk.Label(scrollable_frame, text="💧 Verfüllmaterial-Berechnung",
                  font=("Arial", 14, "bold"),
                  foreground="#1f4788").pack(pady=10)

        grout_frame = ttk.Frame(scrollable_frame)
        grout_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        grout_scrollbar = ttk.Scrollbar(grout_frame)
        grout_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.grout_result_text = tk.Text(
            grout_frame, height=20, font=("Courier", 10),
            wrap=tk.WORD, yscrollcommand=grout_scrollbar.set)
        self.grout_result_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        grout_scrollbar.config(command=self.grout_result_text.yview)
        self.grout_result_text.insert(
            "1.0",
            "Noch keine Berechnung durchgeführt.\n\n"
            "Klicken Sie auf 'Materialmengen berechnen'.")
        self.app.grout_result_text = self.grout_result_text

        # ── Hydraulik-Anzeige ──
        ttk.Label(scrollable_frame, text="💨 Hydraulik-Berechnung",
                  font=("Arial", 14, "bold"),
                  foreground="#1f4788").pack(pady=10)

        hydraulics_container = ttk.Frame(scrollable_frame)
        hydraulics_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # 1. Hauptergebnisse
        results_frame = ttk.LabelFrame(hydraulics_container,
                                        text="📊 Hydraulik-Ergebnisse",
                                        padding=5)
        results_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))

        hydraulics_text_frame = ttk.Frame(results_frame)
        hydraulics_text_frame.pack(fill=tk.BOTH, expand=True)

        hydraulics_scrollbar = ttk.Scrollbar(hydraulics_text_frame)
        hydraulics_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.hydraulics_result_text = tk.Text(
            hydraulics_text_frame, height=15, font=("Courier", 9),
            wrap=tk.WORD, yscrollcommand=hydraulics_scrollbar.set)
        self.hydraulics_result_text.pack(side=tk.LEFT, fill=tk.BOTH,
                                          expand=True)
        hydraulics_scrollbar.config(command=self.hydraulics_result_text.yview)
        self.hydraulics_result_text.insert(
            "1.0",
            "Noch keine Berechnung durchgeführt.\n\n"
            "Klicken Sie auf 'Hydraulik berechnen'.")
        self.app.hydraulics_result_text = self.hydraulics_result_text

        # 2. Buttons für Assistenten
        button_container = ttk.Frame(hydraulics_container)
        button_container.pack(fill=tk.X, pady=5)

        ttk.Button(button_container, text="🔧 Pumpenauswahl-Assistent",
                   command=self.app._show_pump_selection,
                   width=35).pack(side=tk.LEFT, padx=5)

        ttk.Button(button_container, text="⚡ Durchfluss-Optimierung",
                   command=self.app._show_flow_optimizer,
                   width=35).pack(side=tk.LEFT, padx=5)

        # 3. Schnellanalyse-Tabs
        analysis_frame = ttk.LabelFrame(hydraulics_container,
                                         text="📈 Detailanalysen", padding=5)
        analysis_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))

        self.analysis_notebook = ttk.Notebook(analysis_frame)
        self.analysis_notebook.pack(fill=tk.BOTH, expand=True)
        self.app.analysis_notebook = self.analysis_notebook

        # Tab 1: Energieprognose
        energy_tab = ttk.Frame(self.analysis_notebook)
        self.analysis_notebook.add(energy_tab, text="💰 Energie")

        self.energy_analysis_text = tk.Text(energy_tab, font=("Courier", 9),
                                             wrap=tk.WORD)
        energy_scrollbar = ttk.Scrollbar(
            energy_tab, command=self.energy_analysis_text.yview)
        self.energy_analysis_text.config(yscrollcommand=energy_scrollbar.set)
        self.energy_analysis_text.pack(side=tk.LEFT, fill=tk.BOTH,
                                        expand=True)
        energy_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.energy_analysis_text.insert(
            "1.0", "Energieprognose wird nach\nHydraulik-Berechnung angezeigt.")
        self.app.energy_analysis_text = self.energy_analysis_text

        # Tab 2: Druckverlust-Details
        pressure_tab = ttk.Frame(self.analysis_notebook)
        self.analysis_notebook.add(pressure_tab, text="🔍 Druckverlust")

        self.pressure_analysis_text = tk.Text(
            pressure_tab, font=("Courier", 9), wrap=tk.WORD)
        pressure_scrollbar = ttk.Scrollbar(
            pressure_tab, command=self.pressure_analysis_text.yview)
        self.pressure_analysis_text.config(
            yscrollcommand=pressure_scrollbar.set)
        self.pressure_analysis_text.pack(side=tk.LEFT, fill=tk.BOTH,
                                          expand=True)
        pressure_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.pressure_analysis_text.insert(
            "1.0",
            "Druckverlust-Details werden nach\nHydraulik-Berechnung angezeigt.")
        self.app.pressure_analysis_text = self.pressure_analysis_text

        # Tab 3: Pumpenauswahl
        pump_tab = ttk.Frame(self.analysis_notebook)
        self.analysis_notebook.add(pump_tab, text="🔧 Pumpen")

        self.pump_analysis_text = tk.Text(pump_tab, font=("Courier", 9),
                                           wrap=tk.WORD)
        pump_scrollbar = ttk.Scrollbar(
            pump_tab, command=self.pump_analysis_text.yview)
        self.pump_analysis_text.config(yscrollcommand=pump_scrollbar.set)
        self.pump_analysis_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        pump_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.pump_analysis_text.insert(
            "1.0",
            "Pumpen-Empfehlungen werden nach\nHydraulik-Berechnung angezeigt.")
        self.app.pump_analysis_text = self.pump_analysis_text
