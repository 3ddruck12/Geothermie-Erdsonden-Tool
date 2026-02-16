"""Bohrfeld-Tab: g-Funktionen-Simulation und Visualisierung.

Extrahiert aus main_window_v3_professional.py (V3.4 Refactoring).
"""

import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
import logging

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

logger = logging.getLogger(__name__)


class BorefieldTab:
    """Verwaltet den Bohrfeld-Simulation Tab mit g-Funktionen.
    
    Berechnet und visualisiert Bohrfeld-Layouts und ihre thermalen
    Antwortfunktionen (g-Funktionen) mittels pygfunction.
    """

    def __init__(self, parent_frame, app):
        """
        Args:
            parent_frame: ttk.Frame in dem der Tab aufgebaut wird.
            app: Referenz auf GeothermieGUIProfessional.
        """
        self.frame = parent_frame
        self.app = app
        self.borefield_entries = {}
        self.borefield_layout_var = tk.StringVar(value="rectangle")
        self._build()

    def _build(self):
        """Erstellt den Bohrfeld-Simulation Tab."""
        try:
            from calculations.borefield_gfunction import (
                BorefieldCalculator, check_pygfunction_installation)
            pygfunction_available, version = check_pygfunction_installation()
        except Exception:
            pygfunction_available = False
            version = "nicht installiert"

        main_container = ttk.Frame(self.frame)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Linke Seite: Eingaben
        left_frame = ttk.Frame(main_container)
        left_frame.pack(side="left", fill="both", expand=False, padx=(0, 10))

        # Rechte Seite: Visualisierung
        right_frame = ttk.Frame(main_container)
        right_frame.pack(side="right", fill="both", expand=True)

        ttk.Label(left_frame, text="🌐 BOHRFELD-KONFIGURATION",
                  font=("Arial", 14, "bold"),
                  foreground="#1f4788").pack(pady=(0, 15))

        if not pygfunction_available:
            ttk.Label(
                left_frame,
                text="⚠️  pygfunction nicht installiert!\n\n"
                     "Installiere mit:\npip install pygfunction[plot]",
                foreground="red", font=("Arial", 10)
            ).pack(pady=10)
            return

        ttk.Label(left_frame, text=f"✅ pygfunction {version} geladen",
                  foreground="green").pack(pady=(0, 10))

        # Layout-Auswahl
        ttk.Label(left_frame, text="Layout:",
                  font=("Arial", 10, "bold")).pack(anchor="w", pady=(10, 2))
        layout_frame = ttk.Frame(left_frame)
        layout_frame.pack(fill="x", pady=(0, 10))
        for layout in ["rectangle", "L", "U", "line"]:
            ttk.Radiobutton(layout_frame, text=layout.upper(),
                            variable=self.borefield_layout_var,
                            value=layout).pack(side="left", padx=5)

        # Eingabefelder
        fields = [
            ("Anzahl Bohrungen X:", "num_x", "3"),
            ("Anzahl Bohrungen Y:", "num_y", "2"),
            ("Abstand X [m]:", "spacing_x", "6.5"),
            ("Abstand Y [m]:", "spacing_y", "6.5"),
            ("Bohrtiefe [m]:", "depth", "120.0"),
        ]
        for label, key, default in fields:
            ttk.Label(left_frame, text=label,
                      font=("Arial", 10)).pack(anchor="w", pady=(5, 2))
            entry = ttk.Entry(left_frame, width=15)
            entry.insert(0, default)
            entry.pack(anchor="w", pady=(0, 5))
            self.borefield_entries[key] = entry

        # Bohrdurchmesser (Wert aus Hauptmaske übernehmen)
        ttk.Label(left_frame, text="Bohrdurchmesser [mm]:",
                  font=("Arial", 10)).pack(anchor="w", pady=(5, 2))
        diameter_entry = ttk.Entry(left_frame, width=15)
        initial_diameter = self.app.entries.get('borehole_diameter')
        try:
            diameter_entry.insert(0, initial_diameter.get() if initial_diameter
                                  else "152.0")
        except Exception:
            diameter_entry.insert(0, "152.0")
        diameter_entry.pack(anchor="w", pady=(0, 5))
        self.borefield_entries['diameter'] = diameter_entry

        # Bodeneigenschaften + Simulationsdauer
        ttk.Label(left_frame, text="Thermische Diffusivität [m²/s]:",
                  font=("Arial", 10)).pack(anchor="w", pady=(10, 2))
        diff_entry = ttk.Entry(left_frame, width=15)
        diff_entry.insert(0, "1.0e-6")
        diff_entry.pack(anchor="w", pady=(0, 5))
        self.borefield_entries['diffusivity'] = diff_entry

        ttk.Label(left_frame, text="Simulationsjahre:",
                  font=("Arial", 10)).pack(anchor="w", pady=(10, 2))
        years_entry = ttk.Entry(left_frame, width=15)
        years_entry.insert(0, "25")
        years_entry.pack(anchor="w", pady=(0, 10))
        self.borefield_entries['years'] = years_entry

        # Berechnen-Button
        ttk.Button(left_frame, text="🔄 g-Funktion berechnen",
                   command=self.calculate_gfunction,
                   style="Accent.TButton").pack(pady=10, fill="x")

        # Ergebnis-Text
        self.borefield_result_text = tk.Text(
            left_frame, height=8, width=35, font=("Courier", 9),
            wrap=tk.WORD)
        self.borefield_result_text.pack(pady=(10, 0), fill="both",
                                         expand=True)
        self.borefield_result_text.insert(
            "1.0",
            "Noch keine Berechnung durchgeführt.\n\n"
            "Klicke 'g-Funktion berechnen' um zu starten.")
        self.borefield_result_text.config(state="disabled")
        self.app.borefield_result_text = self.borefield_result_text

        # Rechte Seite: Visualisierung
        ttk.Label(right_frame, text="📊 BOHRFELD-VISUALISIERUNG",
                  font=("Arial", 14, "bold"),
                  foreground="#1f4788").pack(pady=(0, 15))

        self.borefield_fig = Figure(figsize=(10, 8), dpi=100)
        self.borefield_canvas = FigureCanvasTkAgg(self.borefield_fig,
                                                    right_frame)
        self.borefield_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        ax = self.borefield_fig.add_subplot(111)
        ax.text(0.5, 0.5,
                'Klicke "g-Funktion berechnen"\num Visualisierung zu sehen',
                ha='center', va='center', fontsize=14, color='gray')
        ax.axis('off')
        self.borefield_canvas.draw()

        # Referenzen zurück an App
        self.app.borefield_fig = self.borefield_fig
        self.app.borefield_canvas = self.borefield_canvas
        self.app.borefield_entries = self.borefield_entries
        self.app.borefield_layout_var = self.borefield_layout_var

    def calculate_gfunction(self):
        """Berechnet g-Funktion und visualisiert Bohrfeld."""
        try:
            from calculations.borefield_gfunction import BorefieldCalculator

            layout = self.borefield_layout_var.get()
            num_x = int(self.borefield_entries['num_x'].get())
            num_y = int(self.borefield_entries['num_y'].get())
            spacing_x = float(self.borefield_entries['spacing_x'].get())
            spacing_y = float(self.borefield_entries['spacing_y'].get())
            depth = float(self.borefield_entries['depth'].get())
            diameter_mm = float(self.borefield_entries['diameter'].get())
            radius = diameter_mm / 2000.0
            diffusivity = float(self.borefield_entries['diffusivity'].get())
            years = int(self.borefield_entries['years'].get())

            self.app.status_var.set("⏳ Berechne g-Funktion...")
            self.app.root.update()

            calc = BorefieldCalculator()
            result = calc.calculate_gfunction(
                layout=layout,
                num_boreholes_x=num_x, num_boreholes_y=num_y,
                spacing_x=spacing_x, spacing_y=spacing_y,
                borehole_depth=depth, borehole_radius=radius,
                soil_thermal_diffusivity=diffusivity,
                simulation_years=years, time_resolution="monthly")

            self.app.borefield_config = {
                "enabled": True, "layout": layout,
                "num_boreholes_x": num_x, "num_boreholes_y": num_y,
                "spacing_x_m": spacing_x, "spacing_y_m": spacing_y,
                "borehole_diameter_mm": diameter_mm,
                "soil_thermal_diffusivity": diffusivity,
                "simulation_years": years,
            }
            self.app.borefield_result = result

            self.borefield_result_text.config(state="normal")
            self.borefield_result_text.delete("1.0", tk.END)
            self.borefield_result_text.insert("1.0",
                f"✅ BERECHNUNG ERFOLGREICH\n\n"
                f"Layout: {layout.upper()}\n"
                f"Bohrungen: {result['num_boreholes']}\n"
                f"Gesamttiefe: {result['total_depth']} m\n"
                f"Feldgröße: {result['field_area']:.1f} m²\n\n"
                f"Tiefe pro Bohrung: {depth} m\n"
                f"Durchmesser: {diameter_mm} mm\n"
                f"Abstand X: {spacing_x} m\n"
                f"Abstand Y: {spacing_y} m\n\n"
                f"Simulationsjahre: {years}\n"
                f"Zeitpunkte: {len(result['time'])}\n\n"
                f"Die g-Funktion wurde berechnet\n"
                f"und wird rechts visualisiert.")
            self.borefield_result_text.config(state="disabled")

            self._plot_visualization(result)
            self.app.status_var.set(
                f"✅ g-Funktion berechnet: "
                f"{result['num_boreholes']} Bohrungen")

        except Exception as e:
            messagebox.showerror(
                "Fehler",
                f"Fehler bei g-Funktionen-Berechnung:\n{str(e)}")
            self.app.status_var.set("❌ Berechnung fehlgeschlagen")

    def _plot_visualization(self, result):
        """Plottet Bohrfeld-Layout und g-Funktion."""
        self.borefield_fig.clear()

        ax1 = self.borefield_fig.add_subplot(121)
        ax2 = self.borefield_fig.add_subplot(122)

        # Plot 1: Bohrfeld-Layout
        boreField = result['boreField']
        x_coords = [b.x for b in boreField]
        y_coords = [b.y for b in boreField]

        ax1.scatter(x_coords, y_coords, s=200, c='#1f4788', alpha=0.6,
                    edgecolors='black', linewidths=2)
        for i, (x, y) in enumerate(zip(x_coords, y_coords), 1):
            ax1.text(x, y, str(i), ha='center', va='center',
                     color='white', fontweight='bold', fontsize=10)

        ax1.set_xlabel('X-Position [m]', fontsize=11)
        ax1.set_ylabel('Y-Position [m]', fontsize=11)
        ax1.set_title(
            f'Bohrfeld-Layout: {result["layout"].upper()}\n'
            f'{result["num_boreholes"]} Bohrungen',
            fontsize=12, fontweight='bold')
        ax1.grid(True, alpha=0.3)
        ax1.set_aspect('equal')

        # Plot 2: g-Funktion
        gFunc = result['gFunction']
        time_years = result['time'] / (365.25 * 24 * 3600)

        ax2.plot(time_years, gFunc.gFunc, 'b-', linewidth=2,
                 label='g-Funktion')
        ax2.set_xlabel('Zeit [Jahre]', fontsize=11)
        ax2.set_ylabel('g-Funktion [-]', fontsize=11)
        ax2.set_title(
            f'Thermische Response\n'
            f'{result["simulation_years"]} Jahre Simulation',
            fontsize=12, fontweight='bold')
        ax2.grid(True, alpha=0.3)
        ax2.legend()

        info_text = (f"Gesamttiefe: {result['total_depth']} m | "
                     f"Feldgröße: {result['field_area']:.1f} m²")
        self.borefield_fig.text(0.5, 0.02, info_text, ha='center',
                                 fontsize=9, style='italic')

        self.borefield_fig.tight_layout()
        self.borefield_canvas.draw()
