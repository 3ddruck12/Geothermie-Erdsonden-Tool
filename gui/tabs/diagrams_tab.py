"""Diagramme-Tab: Alle Visualisierungen und Plot-Funktionen.

Extrahiert aus main_window_v3_professional.py (V3.4 Refactoring).
Enthält 17 Diagramme:
  1. Monatliche Temperaturen
  2. Bohrloch-Schema (Querschnitt)
  3. Monatliche Entzugsleistung (W/m)
  4. Pumpen-Kennlinien (H-Q-Kurven)
  5. Reynolds-Kurve
  6. Druckverlust-Komponenten
  7. Volumenstrom vs. Druckverlust
  8. Pumpenleistung über Betriebszeit
  9. Temperaturspreizung Sole
 10. COP vs. Sole-Eintrittstemperatur
 11. COP vs. Vorlauftemperatur
 12. JAZ-Abschätzung
 13. Energieverbrauch-Vergleich
 14. Langzeit-Temperaturentwicklung (Phase 3)
 15. Thermische Balance / Regeneration (Phase 3)
 16. Monatlicher COP Langzeit (Phase 3)
 17. JAZ-Vergleich bei verschiedenen Tiefen (Phase 3)
"""

import tkinter as tk
from tkinter import ttk
import numpy as np
import math

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.patches import Circle


class DiagramsTab:
    """Verwaltet den Visualisierungs-Tab mit scrollbarem Bereich für alle Diagramme."""

    def __init__(self, parent_frame, app):
        """
        Args:
            parent_frame: ttk.Frame in dem der Tab aufgebaut wird.
            app: Referenz auf GeothermieGUIProfessional (für Berechnungsdaten).
        """
        self.frame = parent_frame
        self.app = app
        self.diagram_frames = []
        self.diagram_figures = []
        self._build()

    def _build(self):
        """Erstellt den Visualisierungs-Tab."""
        # Steuerleiste
        control_frame = ttk.Frame(self.frame)
        control_frame.pack(fill=tk.X, padx=10, pady=(10, 5))

        ttk.Button(control_frame, text="🔄 Alle Diagramme aktualisieren",
                   command=self.update_all).pack(side=tk.LEFT, padx=5)

        ttk.Label(
            control_frame,
            text="ℹ️ Diagramme werden automatisch in PDF-Bericht eingefügt"
                 " (Strg+P oder Datei → PDF-Bericht)",
            font=("Arial", 9), foreground="gray"
        ).pack(side=tk.LEFT, padx=10)

        # Scrollbarer Container
        canvas_container = tk.Canvas(self.frame)
        scrollbar = ttk.Scrollbar(self.frame, orient="vertical",
                                   command=canvas_container.yview)
        scrollable_frame = ttk.Frame(canvas_container)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas_container.configure(
                scrollregion=canvas_container.bbox("all")))

        canvas_window = canvas_container.create_window(
            (0, 0), window=scrollable_frame, anchor="nw")
        canvas_container.configure(yscrollcommand=scrollbar.set)

        def configure_canvas_width(event):
            canvas_container.itemconfig(canvas_window, width=event.width)
            canvas_container.configure(
                scrollregion=canvas_container.bbox("all"))

        canvas_container.bind('<Configure>', configure_canvas_width)
        scrollable_frame.bind(
            '<Configure>',
            lambda e: canvas_container.configure(
                scrollregion=canvas_container.bbox("all")))

        canvas_container.pack(side="left", fill="both", expand=True,
                               padx=10, pady=10)
        scrollbar.pack(side="right", fill="y")

        # Alle 12 Diagramme registrieren
        diagrams = [
            ("Monatliche Temperaturen", self._plot_monthly_temperatures),
            ("Bohrloch-Schema", self._plot_borehole_schema),
            ("Monatliche Entzugsleistung (W/m)", self._plot_monthly_extraction_w_per_m),
            ("Pumpen-Kennlinien", self._plot_pump_characteristics),
            ("Reynolds-Kurve", self._plot_reynolds_curve),
            ("Druckverlust-Komponenten", self._plot_pressure_components),
            ("Volumenstrom vs. Druckverlust", self._plot_flow_vs_pressure),
            ("Pumpenleistung über Betriebszeit",
             self._plot_pump_power_over_time),
            ("Temperaturspreizung Sole", self._plot_temperature_spread),
            ("COP vs. Sole-Eintrittstemperatur",
             self._plot_cop_vs_inlet_temp),
            ("COP vs. Vorlauftemperatur", self._plot_cop_vs_flow_temp),
            ("JAZ-Abschätzung", self._plot_jaz_estimation),
            ("Energieverbrauch-Vergleich", self._plot_energy_consumption),
        # --- Langzeit-Simulation (V3.4 Phase 3) ---
        ("Langzeit-Temperaturentwicklung",
         self._plot_longterm_temperatures),
        ("Thermische Balance (Entzug/Eintrag)",
         self._plot_thermal_balance),
        ("Monatliche COP-Entwicklung",
         self._plot_monthly_cop_longterm),
        ("JAZ-Vergleich bei verschiedenen Tiefen",
         self._plot_jaz_depth_comparison),
    ]

        for title, plot_fn in diagrams:
            self._add_diagram_frame(scrollable_frame, title, plot_fn)

        # Mousewheel-Scrolling (Widget-spezifisch, kein bind_all)
        from gui.utils import bind_mousewheel_to_canvas
        bind_mousewheel_to_canvas(canvas_container)

        # Referenzen für App-Zugriff
        self.canvas_container = canvas_container
        self.scrollable_frame_widget = scrollable_frame
        self.app.diagram_figures = self.diagram_figures
        self.app.diagram_frames = self.diagram_frames

    def _add_diagram_frame(self, parent, title, plot_function):
        """Fügt ein Diagramm-Frame hinzu."""
        diagram_frame = ttk.LabelFrame(parent, text=f"📊 {title}",
                                        padding=10)
        diagram_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=10)

        fig = Figure(figsize=(16, 6), dpi=100)
        canvas = FigureCanvasTkAgg(fig, master=diagram_frame)
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        self.diagram_frames.append(diagram_frame)
        self.diagram_figures.append({
            'frame': diagram_frame,
            'figure': fig,
            'canvas': canvas,
            'title': title,
            'plot_function': plot_function,
        })

        ax = fig.add_subplot(111)
        ax.text(0.5, 0.5, f"{title}\n\nDiagramm wird nach Berechnung angezeigt",
                ha='center', va='center', fontsize=12, color='gray')
        ax.axis('off')
        canvas.draw()

    def update_all(self):
        """Aktualisiert alle Diagramme."""
        for info in self.diagram_figures:
            try:
                info['plot_function'](info['figure'], info['canvas'])
            except Exception as e:
                ax = info['figure'].gca()
                ax.clear()
                ax.text(0.5, 0.5,
                        f"Fehler beim Erstellen des Diagramms:\n{str(e)}",
                        ha='center', va='center', fontsize=10, color='red')
                info['canvas'].draw()

    # ───── Plot-Funktionen ────────────────────────────────────────

    def _plot_monthly_temperatures(self, fig, canvas):
        """Plottet monatliche Temperaturen."""
        fig.clear()
        ax = fig.add_subplot(111)

        if not self.app.result:
            ax.text(0.5, 0.5,
                    "Keine Berechnung durchgeführt.\n\n"
                    "Bitte Parameter eingeben und Berechnung starten.",
                    ha='center', va='center', fontsize=12, color='gray')
            ax.axis('off')
            canvas.draw()
            return

        months = ["J", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"]
        x = np.arange(len(months))
        r = self.app.result

        ax.plot(x, r.monthly_temperatures, 'o-', linewidth=2.5,
                markersize=8, color='#1f4788')
        ax.axhline(y=r.fluid_temperature_min, color='b', linestyle='--',
                    linewidth=2, label=f'Min: {r.fluid_temperature_min:.1f}°C')
        ax.axhline(y=r.fluid_temperature_max, color='r', linestyle='--',
                    linewidth=2, label=f'Max: {r.fluid_temperature_max:.1f}°C')
        ax.set_xlabel('Monat', fontsize=11, fontweight='bold')
        ax.set_ylabel('Temperatur [°C]', fontsize=11, fontweight='bold')
        ax.set_title('Monatliche Temperaturen', fontsize=12, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(months)
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=9)
        fig.tight_layout()
        canvas.draw()

    def _plot_borehole_schema(self, fig, canvas):
        """Plottet Bohrloch-Querschnitt."""
        fig.clear()
        ax = fig.add_subplot(111)

        try:
            bh_d_mm = float(self.app.entries["borehole_diameter"].get())
            pipe_d = float(self.app.entries["pipe_outer_diameter"].get()) / 1000.0
            bh_d = bh_d_mm / 1000.0
            scale = 100
            bh_r = (bh_d / 2) * scale
            pipe_r = (pipe_d / 2) * scale

            borehole = Circle((0, 0), bh_r, facecolor='#d9d9d9',
                               edgecolor='black', linewidth=2)
            ax.add_patch(borehole)

            positions = [(-bh_r * 0.5, bh_r * 0.5), (bh_r * 0.5, bh_r * 0.5),
                         (-bh_r * 0.5, -bh_r * 0.5), (bh_r * 0.5, -bh_r * 0.5)]
            colors = ['#ff6b6b', '#4ecdc4', '#ff6b6b', '#4ecdc4']

            for i, ((x, y), color) in enumerate(zip(positions, colors)):
                pipe = Circle((x, y), pipe_r * 1.5, facecolor=color,
                               edgecolor='black', linewidth=1, alpha=0.8)
                ax.add_patch(pipe)
                ax.text(x, y, str(i + 1), ha='center', va='center',
                        fontsize=9, fontweight='bold', color='white')

            ax.plot([-bh_r, bh_r], [0, 0], 'k--', linewidth=1, alpha=0.5)
            ax.text(0, -bh_r * 1.7, f'Ø {bh_d_mm:.0f}mm', ha='center',
                    fontsize=11, fontweight='bold',
                    bbox=dict(boxstyle='round,pad=0.4', facecolor='#ffeb3b',
                              edgecolor='black'))

            ax.set_xlim(-bh_r * 1.8, bh_r * 1.8)
            ax.set_ylim(-bh_r * 1.9, bh_r * 1.5)
            ax.set_aspect('equal')
            ax.set_title('Bohrloch-Querschnitt', fontsize=12, fontweight='bold')
            ax.axis('off')
        except Exception as e:
            ax.text(0.5, 0.5,
                    f"Bohrloch-Schema konnte nicht erstellt werden:\n{str(e)}",
                    ha='center', va='center', fontsize=10, color='red')
            ax.axis('off')

        fig.tight_layout()
        canvas.draw()

    def _plot_monthly_extraction_w_per_m(self, fig, canvas):
        """Plottet monatliche Entzugsleistung (W/m) als Zeitreihe."""
        fig.clear()
        ax = fig.add_subplot(111)

        try:
            from data.load_profiles import (
                calculate_monthly_extraction_rate_w_per_m,
                MONTH_NAMES,
            )
            from utils.validators import safe_float

            if not hasattr(self.app, 'load_profiles_tab') or not self.app.load_profiles_tab:
                ax.text(0.5, 0.5,
                        "Lastprofile-Tab nicht geladen.\n\n"
                        "Monatliche Entzugsleistung wird aus Lastprofilen berechnet.",
                        ha='center', va='center', fontsize=12, color='gray')
                ax.axis('off')
                canvas.draw()
                return

            lp = self.app.load_profiles_tab
            h_kwh = lp.get_monthly_heating_kwh()
            c_kwh = lp.get_monthly_cooling_kwh()

            e_depth = self.app.entries.get("initial_depth")
            e_nbh = self.app.borehole_entries.get("num_boreholes")
            depth = safe_float(e_depth.get() if e_depth else "100", default=100.0)
            n_bh = int(safe_float(e_nbh.get() if e_nbh else "1", default=1.0))
            e_cop = self.app.entries.get("heat_pump_cop")
            e_eer = self.app.entries.get("heat_pump_eer")
            cop = safe_float(e_cop.get() if e_cop else "4.0", default=4.0)
            eer = safe_float(e_eer.get() if e_eer else "4.0", default=4.0)

            total_length = depth * n_bh if n_bh > 0 else 1.0
            h_wm, c_wm, net_wm = calculate_monthly_extraction_rate_w_per_m(
                h_kwh, c_kwh, cop, eer, total_length
            )

            x = np.arange(12)
            width = 0.35

            if any(h_wm) or any(c_wm):
                ax.bar(x - width/2, h_wm, width, label="Entzug (Heizen)", color="#e74c3c", alpha=0.85)
                ax.bar(x + width/2, [-v for v in c_wm], width, label="Eintrag (Kühlen)", color="#3498db", alpha=0.85)
                ax.axhline(0, color="black", linewidth=0.5)
            else:
                ax.text(0.5, 0.5,
                        "Keine Lastdaten.\n\nLastprofile-Tab ausfüllen oder Vorlage laden.",
                        ha='center', va='center', fontsize=12, color='gray',
                        transform=ax.transAxes)

            ax.set_xlabel("Monat", fontsize=11, fontweight='bold')
            ax.set_ylabel("Entzugsleistung [W/m]", fontsize=11, fontweight='bold')
            ax.set_xticks(x)
            ax.set_xticklabels(MONTH_NAMES, fontsize=9)
            if any(h_wm) or any(c_wm):
                ax.legend(loc="upper right", fontsize=9)
                ax.grid(True, alpha=0.3, axis="y")
            ax.set_title("Monatliche Entzugsleistung (W/m) als Zeitreihe",
                        fontsize=12, fontweight='bold')
            fig.tight_layout()
            canvas.draw()
        except Exception as e:
            ax.text(0.5, 0.5,
                    f"Fehler beim Erstellen des Diagramms:\n{str(e)}",
                    ha='center', va='center', fontsize=10, color='red')
            ax.axis('off')
            canvas.draw()

    def _plot_pump_characteristics(self, fig, canvas):
        """Plottet Pumpen-Kennlinien (H-Q-Kurve) mit Betriebspunkt."""
        fig.clear()
        ax = fig.add_subplot(111)

        if not self.app.hydraulics_result:
            ax.text(0.5, 0.5,
                    "Keine Hydraulik-Berechnung durchgeführt.\n\n"
                    "Bitte zuerst Hydraulik berechnen.",
                    ha='center', va='center', fontsize=12, color='gray')
            ax.axis('off')
            canvas.draw()
            return

        try:
            from data.pump_db import PumpDatabase
            pump_db = PumpDatabase()

            flow = self.app.hydraulics_result.get('flow', {})
            system = self.app.hydraulics_result.get('system', {})
            current_flow = flow.get('volume_flow_m3_h', 0)
            current_head = system.get('total_pressure_drop_bar', 0) * 10.2

            suitable = []
            for pump in pump_db.pumps:
                if (pump.specs.max_flow_m3h >= current_flow * 1.2 and
                        pump.specs.max_head_m >= current_head * 1.2):
                    suitable.append(pump)
                    if len(suitable) >= 3:
                        break

            if not suitable:
                suitable = pump_db.pumps[:3]

            colors = ['#2196F3', '#4CAF50', '#FF9800']
            for i, pump in enumerate(suitable):
                q_max = pump.specs.max_flow_m3h
                h_max = pump.specs.max_head_m
                q_range = np.linspace(0, q_max, 50)
                h_range = h_max * (1 - (q_range / q_max) ** 2)
                ax.plot(q_range, h_range, linewidth=2,
                        color=colors[i % len(colors)],
                        label=f'{pump.manufacturer} {pump.model}\n'
                              f'(H_max={h_max:.1f}m, Q_max={q_max:.1f}m³/h)')

            if current_flow > 0 and current_head > 0:
                ax.plot(current_flow, current_head, 'ro', markersize=12,
                        label=f'Betriebspunkt\n'
                              f'({current_flow:.2f} m³/h, {current_head:.1f} m)',
                        zorder=5)
                q_sys = np.linspace(0, current_flow * 1.5, 30)
                h_sys = current_head * (q_sys / current_flow) ** 2
                ax.plot(q_sys, h_sys, 'k--', linewidth=1.5, alpha=0.5,
                        label='System-Kennlinie')

            ax.set_xlabel('Volumenstrom [m³/h]', fontsize=11, fontweight='bold')
            ax.set_ylabel('Förderhöhe [m]', fontsize=11, fontweight='bold')
            ax.set_title('Pumpen-Kennlinien (H-Q-Kurven)', fontsize=12,
                          fontweight='bold')
            ax.grid(True, alpha=0.3)
            ax.legend(fontsize=8, loc='best')
            fig.tight_layout()
            canvas.draw()
        except Exception as e:
            ax.text(0.5, 0.5,
                    f"Fehler beim Erstellen des Diagramms:\n{str(e)}",
                    ha='center', va='center', fontsize=10, color='red')
            ax.axis('off')
            canvas.draw()

    def _plot_reynolds_curve(self, fig, canvas):
        """Plottet Reynolds-Zahl vs. Volumenstrom."""
        fig.clear()
        ax = fig.add_subplot(111)

        if not self.app.hydraulics_result:
            ax.text(0.5, 0.5,
                    "Keine Hydraulik-Berechnung durchgeführt.\n\n"
                    "Bitte zuerst Hydraulik berechnen.",
                    ha='center', va='center', fontsize=12, color='gray')
            ax.axis('off')
            canvas.draw()
            return

        try:
            flow = self.app.hydraulics_result.get('flow', {})
            current_flow = flow.get('volume_flow_m3_h', 2.5)
            pipe_d = float(self.app.entries.get("pipe_outer_diameter",
                           ttk.Entry()).get() or "32") / 1000.0
            pipe_d_inner = pipe_d - 0.004

            flow_range = np.linspace(0.5, 5.0, 50)
            concentrations = [0, 25, 30, 40]
            colors = ['#2196F3', '#4CAF50', '#FF9800', '#F44336']

            current_reynolds = 0
            for conc, color in zip(concentrations, colors):
                props = self.app.hydraulics_calc._get_fluid_properties(conc)
                density = props['density']
                viscosity = props['viscosity']
                area = math.pi * (pipe_d_inner / 2) ** 2
                reynolds_list = []
                for flow_m3h in flow_range:
                    velocity = (flow_m3h / 3600) / area
                    re = (density * velocity * pipe_d_inner) / viscosity
                    reynolds_list.append(re)
                ax.plot(flow_range, reynolds_list, linewidth=2, color=color,
                        label=f'{conc}% Glykol')

            ax.axhline(y=2300, color='red', linestyle='--', linewidth=2,
                        label='Turbulenz-Grenze (Re=2300)')

            if current_flow > 0:
                antifreeze_conc = float(
                    self.app.entries.get("antifreeze_concentration",
                                        ttk.Entry()).get() or "25")
                props = self.app.hydraulics_calc._get_fluid_properties(
                    antifreeze_conc)
                area = math.pi * (pipe_d_inner / 2) ** 2
                velocity = (current_flow / 3600) / area
                current_reynolds = (props['density'] * velocity
                                     * pipe_d_inner) / props['viscosity']
                ax.plot(current_flow, current_reynolds, 'ro', markersize=12,
                        label=f'Betriebspunkt (Re={current_reynolds:.0f})',
                        zorder=5)

            ax.set_xlabel('Volumenstrom [m³/h]', fontsize=11, fontweight='bold')
            ax.set_ylabel('Reynolds-Zahl [-]', fontsize=11, fontweight='bold')
            ax.set_title('Reynolds-Zahl vs. Volumenstrom', fontsize=12,
                          fontweight='bold')
            ax.grid(True, alpha=0.3)
            ax.legend(fontsize=9, loc='best')
            ax.set_xlim(0.5, 5.0)

            if current_flow > 0 and current_reynolds < 2300:
                ax.text(0.05, 0.95, '⚠️ LAMINARE STRÖMUNG\nRe < 2300',
                        transform=ax.transAxes, fontsize=10, color='red',
                        verticalalignment='top',
                        bbox=dict(boxstyle='round', facecolor='yellow',
                                  alpha=0.7))

            fig.tight_layout()
            canvas.draw()
        except Exception as e:
            ax.text(0.5, 0.5,
                    f"Fehler beim Erstellen der Reynolds-Kurve:\n{str(e)}",
                    ha='center', va='center', fontsize=10, color='red')
            ax.axis('off')
            canvas.draw()

    def _plot_pressure_components(self, fig, canvas):
        """Plottet Druckverlust-Komponenten als Torten- und Balkendiagramm."""
        fig.clear()

        if not self.app.hydraulics_result:
            ax = fig.add_subplot(111)
            ax.text(0.5, 0.5,
                    "Keine Hydraulik-Berechnung durchgeführt.\n\n"
                    "Bitte zuerst Hydraulik berechnen.",
                    ha='center', va='center', fontsize=12, color='gray')
            ax.axis('off')
            canvas.draw()
            return

        try:
            system = self.app.hydraulics_result.get('system', {})
            flow = self.app.hydraulics_result.get('flow', {})

            depth = float(self.app.entries.get("borehole_depth",
                          ttk.Entry()).get() or "100")
            num_bh = int(self.app.borehole_entries.get("num_boreholes",
                         ttk.Entry()).get() or "1")
            num_circ = int(self.app.borehole_entries.get("num_circuits",
                           ttk.Entry()).get() or "1")
            pipe_d = float(self.app.entries.get("pipe_outer_diameter",
                           ttk.Entry()).get() or "32") / 1000.0
            pipe_d_inner = pipe_d - 0.004
            volume_flow = flow.get('volume_flow_m3_h', 2.5)
            antifreeze_conc = float(
                self.app.entries.get("antifreeze_concentration",
                                    ttk.Entry()).get() or "25")
            pipe_config = self.app.pipe_config_var.get()
            circuits_per_bh = (2 if 'double' in pipe_config.lower()
                               or '4' in pipe_config else 1)

            analysis = self.app.hydraulics_calc.calculate_detailed_pressure_analysis(
                depth, num_bh, num_circ, pipe_d_inner, volume_flow,
                antifreeze_conc, circuits_per_borehole=circuits_per_bh)

            components = analysis['components']
            labels = ['Bohrungen', 'Horizontal', 'Formstücke', 'Wärmetauscher']
            sizes = [components[k]['percent']
                     for k in ['boreholes', 'horizontal', 'fittings',
                               'heat_exchanger']]
            values = [components[k]['pressure_drop_bar']
                      for k in ['boreholes', 'horizontal', 'fittings',
                                'heat_exchanger']]
            colors_pie = ['#FF6B6B', '#4ECDC4', '#FFE66D', '#95E1D3']

            ax1 = fig.add_subplot(1, 2, 1)
            ax1.pie(sizes, labels=labels, colors=colors_pie,
                    autopct='%1.1f%%', startangle=90,
                    textprops={'fontsize': 10, 'fontweight': 'bold'})
            ax1.set_title('Druckverlust-Anteile', fontsize=12,
                           fontweight='bold')

            ax2 = fig.add_subplot(1, 2, 2)
            bars = ax2.barh(labels, values, color=colors_pie)
            ax2.set_xlabel('Druckverlust [bar]', fontsize=11,
                            fontweight='bold')
            ax2.set_title('Druckverlust nach Komponenten', fontsize=12,
                           fontweight='bold')
            ax2.grid(True, alpha=0.3, axis='x')
            for i, (bar, val) in enumerate(zip(bars, values)):
                ax2.text(val + 0.01, i,
                         f'{val:.3f} bar\n({sizes[i]:.1f}%)',
                         va='center', fontsize=9, fontweight='bold')

            fig.tight_layout()
            canvas.draw()
        except Exception as e:
            ax = fig.add_subplot(111)
            ax.text(0.5, 0.5,
                    f"Fehler beim Erstellen des Diagramms:\n{str(e)}",
                    ha='center', va='center', fontsize=10, color='red')
            ax.axis('off')
            canvas.draw()

    def _plot_flow_vs_pressure(self, fig, canvas):
        """Plottet Volumenstrom vs. Druckverlust."""
        fig.clear()
        ax = fig.add_subplot(111)

        if not self.app.hydraulics_result:
            ax.text(0.5, 0.5,
                    "Keine Hydraulik-Berechnung durchgeführt.\n\n"
                    "Bitte zuerst Hydraulik berechnen.",
                    ha='center', va='center', fontsize=12, color='gray')
            ax.axis('off')
            canvas.draw()
            return

        try:
            depth = float(self.app.entries.get("borehole_depth",
                          ttk.Entry()).get() or "100")
            num_bh = int(self.app.borehole_entries.get("num_boreholes",
                         ttk.Entry()).get() or "1")
            num_circ = int(self.app.borehole_entries.get("num_circuits",
                           ttk.Entry()).get() or "1")
            pipe_d = float(self.app.entries.get("pipe_outer_diameter",
                           ttk.Entry()).get() or "32") / 1000.0
            pipe_d_inner = pipe_d - 0.004
            antifreeze_conc = float(
                self.app.entries.get("antifreeze_concentration",
                                    ttk.Entry()).get() or "25")
            pipe_config = self.app.pipe_config_var.get()
            circuits_per_bh = (2 if 'double' in pipe_config.lower()
                               or '4' in pipe_config else 1)

            flow_range = np.linspace(0.5, 5.0, 30)
            pressure_range = []
            for flow_m3h in flow_range:
                dp = self.app.hydraulics_calc.calculate_total_system_pressure_drop(
                    depth, num_bh, num_circ, pipe_d_inner, flow_m3h,
                    antifreeze_conc, circuits_per_borehole=circuits_per_bh)
                pressure_range.append(dp['total_pressure_drop_bar'])

            ax.plot(flow_range, pressure_range, 'b-', linewidth=2.5,
                    label='Solekreis-Kennlinie')

            flow_data = self.app.hydraulics_result.get('flow', {})
            system_data = self.app.hydraulics_result.get('system', {})
            cf = flow_data.get('volume_flow_m3_h', 0)
            cp = system_data.get('total_pressure_drop_bar', 0)
            if cf > 0 and cp > 0:
                ax.plot(cf, cp, 'ro', markersize=12,
                        label=f'Betriebspunkt ({cf:.2f} m³/h, {cp:.2f} bar)',
                        zorder=5)

            ax.set_xlabel('Volumenstrom [m³/h]', fontsize=11, fontweight='bold')
            ax.set_ylabel('Druckverlust [bar]', fontsize=11, fontweight='bold')
            ax.set_title('Volumenstrom vs. Druckverlust (Solekreis-Kennlinie)',
                          fontsize=12, fontweight='bold')
            ax.grid(True, alpha=0.3)
            ax.legend(fontsize=9, loc='best')
            fig.tight_layout()
            canvas.draw()
        except Exception as e:
            ax.text(0.5, 0.5,
                    f"Fehler beim Erstellen des Diagramms:\n{str(e)}",
                    ha='center', va='center', fontsize=10, color='red')
            ax.axis('off')
            canvas.draw()

    def _plot_pump_power_over_time(self, fig, canvas):
        """Plottet Pumpenleistung über Betriebszeit."""
        fig.clear()
        ax = fig.add_subplot(111)

        if not self.app.hydraulics_result:
            ax.text(0.5, 0.5,
                    "Keine Hydraulik-Berechnung durchgeführt.\n\n"
                    "Bitte zuerst Hydraulik berechnen.",
                    ha='center', va='center', fontsize=12, color='gray')
            ax.axis('off')
            canvas.draw()
            return

        try:
            pump_power = self.app.hydraulics_result['pump']['electric_power_w']
            months = ["J", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"]
            monthly_hours = [200, 180, 150, 100, 50, 20, 20, 30, 60, 120, 160, 190]
            total_hours = sum(monthly_hours)
            monthly_energy = [h * pump_power / 1000 for h in monthly_hours]

            x = np.arange(len(months))
            bars = ax.bar(x, monthly_energy, color='#2196F3', alpha=0.7,
                           edgecolor='black', linewidth=1)
            for bar, energy in zip(bars, monthly_energy):
                if energy > 5:
                    ax.text(bar.get_x() + bar.get_width() / 2.,
                            bar.get_height() + 0.5, f'{energy:.0f} kWh',
                            ha='center', va='bottom', fontsize=8)

            ax.set_xlabel('Monat', fontsize=11, fontweight='bold')
            ax.set_ylabel('Energieverbrauch [kWh]', fontsize=11,
                            fontweight='bold')
            ax.set_title(f'Pumpenleistung über Betriebszeit\n'
                          f'({pump_power:.0f} W, {total_hours} h/Jahr)',
                          fontsize=12, fontweight='bold')
            ax.set_xticks(x)
            ax.set_xticklabels(months)
            ax.grid(True, alpha=0.3, axis='y')

            total_energy = sum(monthly_energy)
            ax.text(0.02, 0.98,
                    f'Gesamtverbrauch:\n{total_energy:.0f} kWh/Jahr\n'
                    f'({total_energy * 0.30:.0f} EUR/Jahr)',
                    transform=ax.transAxes, fontsize=9,
                    verticalalignment='top',
                    bbox=dict(boxstyle='round', facecolor='lightgreen',
                              alpha=0.5))

            fig.tight_layout()
            canvas.draw()
        except Exception as e:
            ax.text(0.5, 0.5,
                    f"Fehler beim Erstellen des Diagramms:\n{str(e)}",
                    ha='center', va='center', fontsize=10, color='red')
            ax.axis('off')
            canvas.draw()

    def _plot_temperature_spread(self, fig, canvas):
        """Plottet Temperaturspreizung Sole (ΔT vs. Volumenstrom)."""
        fig.clear()
        ax = fig.add_subplot(111)

        if not self.app.hydraulics_result:
            ax.text(0.5, 0.5,
                    "Keine Hydraulik-Berechnung durchgeführt.\n\n"
                    "Bitte zuerst Hydraulik berechnen.",
                    ha='center', va='center', fontsize=12, color='gray')
            ax.axis('off')
            canvas.draw()
            return

        try:
            flow = self.app.hydraulics_result.get('flow', {})
            current_flow = flow.get('volume_flow_m3_h', 2.5)
            cold_power = self.app.hydraulics_result.get('cold_power', 6.0)

            if isinstance(cold_power, dict):
                extraction_power_kw = cold_power.get('extraction_power_kw', 6.0)
            elif isinstance(cold_power, (int, float)):
                extraction_power_kw = float(cold_power)
            else:
                try:
                    hp = self.app.entries.get("heat_power")
                    heat_power = float(hp.get() or "6.0") if hp else 6.0
                    cop_e = self.app.entries.get("heat_pump_cop_heating")
                    cop = float(cop_e.get() or "4.0") if cop_e else 4.0
                    extraction_power_kw = heat_power * (cop - 1) / cop
                except (ValueError, AttributeError, TypeError):
                    extraction_power_kw = 6.0

            flow_range = np.linspace(1.0, 5.0, 30)

            try:
                af_entry = self.app.entries.get("antifreeze_concentration")
                antifreeze_conc = (float(af_entry.get() or "25")
                                    if af_entry else 25.0)
            except (ValueError, AttributeError, TypeError):
                antifreeze_conc = 25.0

            props = self.app.hydraulics_calc._get_fluid_properties(
                antifreeze_conc)
            density = props['density']
            cp = props['heat_capacity']

            delta_t_range = []
            for flow_m3h in flow_range:
                mass_flow = (flow_m3h / 3600) * density
                dt = ((extraction_power_kw * 1000) / (mass_flow * cp)
                      if mass_flow > 0 else 0)
                delta_t_range.append(dt)

            ax.plot(flow_range, delta_t_range, 'b-', linewidth=2.5,
                    label='Temperaturspreizung')

            if current_flow > 0:
                mf = (current_flow / 3600) * density
                cdt = ((extraction_power_kw * 1000) / (mf * cp)
                       if mf > 0 else 0)
                ax.plot(current_flow, cdt, 'ro', markersize=12,
                        label=f'Betriebspunkt\n(ΔT={cdt:.2f} K)', zorder=5)

            ax.axhspan(2, 4, alpha=0.2, color='green',
                        label='Optimaler Bereich (2-4 K)')
            ax.set_xlabel('Volumenstrom [m³/h]', fontsize=11, fontweight='bold')
            ax.set_ylabel('Temperaturspreizung ΔT [K]', fontsize=11,
                            fontweight='bold')
            ax.set_title('Temperaturspreizung Sole (ΔT vs. Volumenstrom)',
                          fontsize=12, fontweight='bold')
            ax.grid(True, alpha=0.3)
            ax.legend(fontsize=9, loc='best')
            ax.set_ylim(0, max(delta_t_range) * 1.1 if delta_t_range else 5)
            fig.tight_layout()
            canvas.draw()
        except Exception as e:
            ax.text(0.5, 0.5,
                    f"Fehler beim Erstellen des Diagramms:\n{str(e)}",
                    ha='center', va='center', fontsize=10, color='red')
            ax.axis('off')
            canvas.draw()

    def _plot_cop_vs_inlet_temp(self, fig, canvas):
        """Plottet COP vs. Sole-Eintrittstemperatur."""
        fig.clear()
        ax = fig.add_subplot(111)

        try:
            cop_heating = float(
                self.app.entries.get("heat_pump_cop_heating",
                                    ttk.Entry()).get() or "4.0")
            inlet_temp_range = np.linspace(-5, 15, 50)
            cop_range = [max(2.0, min(6.0, cop_heating * (1 + 0.04 * t)))
                         for t in inlet_temp_range]

            ax.plot(inlet_temp_range, cop_range, 'b-', linewidth=2.5,
                    label='COP-Kurve')

            if hasattr(self.app, 'vdi4640_result') and self.app.vdi4640_result:
                ti = self.app.vdi4640_result.t_wp_aus_heating_min
                ca = max(2.0, min(6.0, cop_heating * (1 + 0.04 * ti)))
                ax.plot(ti, ca, 'ro', markersize=12,
                        label=f'Betriebspunkt\n(T={ti:.1f}°C, COP={ca:.2f})',
                        zorder=5)

            ax.set_xlabel('Sole-Eintrittstemperatur [°C]', fontsize=11,
                            fontweight='bold')
            ax.set_ylabel('COP [-]', fontsize=11, fontweight='bold')
            ax.set_title('COP vs. Sole-Eintrittstemperatur', fontsize=12,
                          fontweight='bold')
            ax.grid(True, alpha=0.3)
            ax.legend(fontsize=9, loc='best')
            fig.tight_layout()
            canvas.draw()
        except Exception as e:
            ax.text(0.5, 0.5,
                    f"Fehler beim Erstellen des Diagramms:\n{str(e)}",
                    ha='center', va='center', fontsize=10, color='red')
            ax.axis('off')
            canvas.draw()

    def _plot_cop_vs_flow_temp(self, fig, canvas):
        """Plottet COP vs. Vorlauftemperatur."""
        fig.clear()
        ax = fig.add_subplot(111)

        try:
            cop_heating = float(
                self.app.entries.get("heat_pump_cop_heating",
                                    ttk.Entry()).get() or "4.0")
            flow_temp = float(
                self.app.entries.get("flow_temperature",
                                    ttk.Entry()).get() or "35.0")

            flow_temp_range = np.linspace(25, 55, 50)
            cop_range = [max(2.0, min(6.0,
                            cop_heating * (1 - 0.025 * (t - 35))))
                         for t in flow_temp_range]

            ax.plot(flow_temp_range, cop_range, 'r-', linewidth=2.5,
                    label='COP-Kurve')

            cop_actual = max(2.0, min(6.0,
                             cop_heating * (1 - 0.025 * (flow_temp - 35))))
            ax.plot(flow_temp, cop_actual, 'ro', markersize=12,
                    label=f'Betriebspunkt\n(T={flow_temp:.1f}°C,'
                          f' COP={cop_actual:.2f})', zorder=5)

            ax.set_xlabel('Vorlauftemperatur [°C]', fontsize=11,
                            fontweight='bold')
            ax.set_ylabel('COP [-]', fontsize=11, fontweight='bold')
            ax.set_title('COP vs. Vorlauftemperatur', fontsize=12,
                          fontweight='bold')
            ax.grid(True, alpha=0.3)
            ax.legend(fontsize=9, loc='best')
            fig.tight_layout()
            canvas.draw()
        except Exception as e:
            ax.text(0.5, 0.5,
                    f"Fehler beim Erstellen des Diagramms:\n{str(e)}",
                    ha='center', va='center', fontsize=10, color='red')
            ax.axis('off')
            canvas.draw()

    def _plot_jaz_estimation(self, fig, canvas):
        """Plottet JAZ-Abschätzung (Jahresarbeitszahl)."""
        fig.clear()
        ax = fig.add_subplot(111)

        try:
            cop_heating = float(
                self.app.entries.get("heat_pump_cop_heating",
                                    ttk.Entry()).get() or "4.0")
            annual_heating = float(
                self.app.entries.get("annual_heating",
                                    ttk.Entry()).get() or "10000")

            jaz_estimated = cop_heating * 0.85
            scenarios = ['Optimistisch\n(COP_nenn)',
                         'Realistisch\n(JAZ geschätzt)',
                         'Pessimistisch\n(-20%)']
            values = [cop_heating, jaz_estimated, cop_heating * 0.80]
            colors = ['#4CAF50', '#2196F3', '#FF9800']

            bars = ax.barh(scenarios, values, color=colors, alpha=0.7,
                            edgecolor='black', linewidth=2)
            for bar, val in zip(bars, values):
                ax.text(bar.get_width() + 0.05,
                        bar.get_y() + bar.get_height() / 2,
                        f'{val:.2f}', va='center', fontsize=10,
                        fontweight='bold')

            ec = annual_heating / jaz_estimated
            ax.text(0.02, 0.98,
                    f'JAZ-Abschätzung: {jaz_estimated:.2f}\n\n'
                    f'Jahresenergieverbrauch:\n{ec:.0f} kWh/Jahr\n'
                    f'({ec * 0.30:.0f} EUR/Jahr)',
                    transform=ax.transAxes, fontsize=9,
                    verticalalignment='top',
                    bbox=dict(boxstyle='round', facecolor='lightblue',
                              alpha=0.5))

            ax.set_xlabel('COP / JAZ [-]', fontsize=11, fontweight='bold')
            ax.set_title('JAZ-Abschätzung (Jahresarbeitszahl)', fontsize=12,
                          fontweight='bold')
            ax.grid(True, alpha=0.3, axis='x')
            ax.set_xlim(0, max(values) * 1.3)
            fig.tight_layout()
            canvas.draw()
        except Exception as e:
            ax.text(0.5, 0.5,
                    f"Fehler beim Erstellen des Diagramms:\n{str(e)}",
                    ha='center', va='center', fontsize=10, color='red')
            ax.axis('off')
            canvas.draw()

    def _plot_energy_consumption(self, fig, canvas):
        """Plottet Energieverbrauch-Vergleich (konstant vs. geregelt)."""
        fig.clear()
        ax = fig.add_subplot(111)

        if not self.app.hydraulics_result:
            ax.text(0.5, 0.5,
                    "Keine Hydraulik-Berechnung durchgeführt.\n\n"
                    "Bitte zuerst Hydraulik berechnen.",
                    ha='center', va='center', fontsize=12, color='gray')
            ax.axis('off')
            canvas.draw()
            return

        try:
            pump_power = self.app.hydraulics_result['pump']['electric_power_w']
            hours = 1800
            price = 0.30

            energy = self.app.hydraulics_calc.calculate_pump_energy_consumption(
                pump_power, hours, price)

            regulated_kwh = energy['annual_kwh'] * 0.7
            regulated_cost = energy['annual_cost_eur'] * 0.7
            constant_10y = energy['annual_cost_eur'] * 10
            regulated_10y = regulated_cost * 10
            savings_10y = constant_10y - regulated_10y

            categories = ['Konstante\nPumpe', 'Geregelte\nPumpe']
            annual_costs = [energy['annual_cost_eur'], regulated_cost]
            colors = ['#F44336', '#4CAF50']

            bars = ax.bar(categories, annual_costs, color=colors, alpha=0.7,
                           edgecolor='black', linewidth=2)
            for bar, cost in zip(bars, annual_costs):
                ax.text(bar.get_x() + bar.get_width() / 2.,
                        bar.get_height() + 5,
                        f'{cost:.0f} EUR/Jahr\n({cost / price:.0f} kWh)',
                        ha='center', va='bottom', fontsize=10,
                        fontweight='bold')

            savings = energy['annual_cost_eur'] - regulated_cost
            ax.annotate('', xy=(1, regulated_cost),
                        xytext=(0, energy['annual_cost_eur']),
                        arrowprops=dict(arrowstyle='<->', color='blue', lw=2))
            ax.text(0.5, (energy['annual_cost_eur'] + regulated_cost) / 2,
                    f'Einsparung:\n{savings:.0f} EUR/Jahr\n'
                    f'({savings_10y:.0f} EUR/10a)',
                    ha='center', va='center', fontsize=10, fontweight='bold',
                    bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow',
                              alpha=0.7))

            ax.set_ylabel('Kosten [EUR/Jahr]', fontsize=11, fontweight='bold')
            ax.set_title('Energieverbrauch-Vergleich: '
                          'Konstante vs. Geregelte Pumpe',
                          fontsize=12, fontweight='bold')
            ax.grid(True, alpha=0.3, axis='y')

            ax.text(0.02, 0.98,
                    f'10-Jahres-Kosten:\nKonstant: {constant_10y:.0f} EUR\n'
                    f'Geregelt: {regulated_10y:.0f} EUR\n\n'
                    f'Einsparung: {savings_10y:.0f} EUR',
                    transform=ax.transAxes, fontsize=9,
                    verticalalignment='top',
                    bbox=dict(boxstyle='round', facecolor='lightblue',
                              alpha=0.5))

            fig.tight_layout()
            canvas.draw()
        except Exception as e:
            ax.text(0.5, 0.5,
                    f"Fehler beim Erstellen des Diagramms:\n{str(e)}",
                    ha='center', va='center', fontsize=10, color='red')
            ax.axis('off')
            canvas.draw()

    # ───── Langzeit-Simulation Diagramme (V3.4 Phase 3) ──────────

    def _plot_longterm_temperatures(self, fig, canvas):
        """Plottet Langzeit-Temperaturentwicklung über Jahre."""
        fig.clear()
        ax = fig.add_subplot(111)

        if not hasattr(self.app, 'longterm_result') or not self.app.longterm_result:
            ax.text(0.5, 0.5,
                    "Keine Langzeit-Simulation verfügbar.\n\n"
                    "Bitte Berechnung durchführen.",
                    ha='center', va='center', fontsize=12, color='gray')
            ax.axis('off')
            canvas.draw()
            return

        try:
            lt = self.app.longterm_result
            years = list(range(1, lt.years + 1))

            # Min/Max Band
            ax.fill_between(years, lt.annual_fluid_temp_min,
                           lt.annual_fluid_temp_max,
                           alpha=0.2, color='#1f77b4',
                           label='Temperaturband (Min/Max)')

            # Min-Linie
            ax.plot(years, lt.annual_fluid_temp_min, 'b-', linewidth=2,
                    label=f'Min. Fluid-T ({lt.annual_fluid_temp_min[-1]:.1f}°C)')
            # Max-Linie
            ax.plot(years, lt.annual_fluid_temp_max, 'r-', linewidth=2,
                    label=f'Max. Fluid-T ({lt.annual_fluid_temp_max[-1]:.1f}°C)')

            # Boden-Temperatur (Jahresmittel)
            if lt.monthly_ground_temps:
                annual_ground_mean = [
                    sum(gt) / len(gt) for gt in lt.monthly_ground_temps
                ]
                ax.plot(years, annual_ground_mean, 'g--', linewidth=1.5,
                        alpha=0.7, label='Ø Bodentemperatur')

            # Grenzlinien
            try:
                t_min_limit = float(
                    self.app.entries.get("min_fluid_temperature",
                                        ttk.Entry()).get() or "-2")
            except (ValueError, AttributeError):
                t_min_limit = -2.0
            ax.axhline(y=t_min_limit, color='blue', linestyle=':',
                       linewidth=1.5, alpha=0.5,
                       label=f'Grenzwert ({t_min_limit:.0f}°C)')
            ax.axhline(y=0, color='gray', linestyle='-',
                       linewidth=0.5, alpha=0.3)

            # Depletion-Warnung
            if hasattr(self.app, 'depletion_warning') and self.app.depletion_warning:
                dw = self.app.depletion_warning
                if dw.is_warning:
                    color = {'critical': 'red', 'warning': 'orange',
                             'info': 'blue'}.get(dw.warning_level, 'gray')
                    ax.text(0.02, 0.02, f'⚠️ {dw.warning_level.upper()}\n'
                            f'Trend: {dw.temperature_trend:.2f} K/Dekade',
                            transform=ax.transAxes, fontsize=9,
                            verticalalignment='bottom', color=color,
                            bbox=dict(boxstyle='round', facecolor='lightyellow',
                                      alpha=0.8))

            ax.set_xlabel('Jahr', fontsize=11, fontweight='bold')
            ax.set_ylabel('Fluid-Temperatur [°C]', fontsize=11,
                          fontweight='bold')
            ax.set_title('Langzeit-Temperaturentwicklung', fontsize=12,
                         fontweight='bold')
            ax.grid(True, alpha=0.3)
            ax.legend(fontsize=8, loc='best')
            fig.tight_layout()
            canvas.draw()
        except Exception as e:
            ax.text(0.5, 0.5,
                    f"Fehler beim Erstellen des Diagramms:\n{str(e)}",
                    ha='center', va='center', fontsize=10, color='red')
            ax.axis('off')
            canvas.draw()

    def _plot_thermal_balance(self, fig, canvas):
        """Plottet thermische Balance (Entzug vs. Eintrag pro Jahr)."""
        fig.clear()

        if not hasattr(self.app, 'thermal_balance') or not self.app.thermal_balance:
            ax = fig.add_subplot(111)
            ax.text(0.5, 0.5,
                    "Keine Langzeit-Simulation verfügbar.\n\n"
                    "Bitte Berechnung durchführen.",
                    ha='center', va='center', fontsize=12, color='gray')
            ax.axis('off')
            canvas.draw()
            return

        try:
            tb = self.app.thermal_balance
            years = list(range(1, len(tb.annual_extraction) + 1))

            ax1 = fig.add_subplot(111)

            # Balken: Entzug (positiv) und Eintrag (negativ)
            width = 0.6
            ax1.bar(years, tb.annual_extraction, width, color='#e74c3c',
                    alpha=0.7, label='Wärmeentzug (Heizen)')
            negative_injection = [-v for v in tb.annual_injection]
            ax1.bar(years, negative_injection, width, color='#3498db',
                    alpha=0.7, label='Wärmeeintrag (Kühlen)')

            ax1.axhline(y=0, color='black', linewidth=0.5)

            # Kumulative Bilanz auf zweiter Y-Achse
            ax2 = ax1.twinx()
            ax2.plot(years, [c / 1000 for c in tb.cumulative_balance],
                     'k-', linewidth=2.5, marker='o', markersize=3,
                     label='Kumulierte Bilanz')
            ax2.set_ylabel('Kumulierte Bilanz [MWh]', fontsize=10,
                          fontweight='bold')

            # Info-Box
            ratio_text = (f'{tb.imbalance_ratio:.1f}x'
                         if tb.imbalance_ratio != float('inf')
                         else 'Nur Heizen')
            ax1.text(0.02, 0.98,
                     f'Bilanz-Verhältnis: {ratio_text}\n'
                     f'Gesamt-Entzug: {tb.total_extraction/1000:.1f} MWh\n'
                     f'Gesamt-Eintrag: {tb.total_injection/1000:.1f} MWh',
                     transform=ax1.transAxes, fontsize=8,
                     verticalalignment='top',
                     bbox=dict(boxstyle='round', facecolor='lightyellow',
                               alpha=0.7))

            ax1.set_xlabel('Jahr', fontsize=11, fontweight='bold')
            ax1.set_ylabel('Energie [kWh/Jahr]', fontsize=11,
                          fontweight='bold')
            ax1.set_title('Thermische Balance (Entzug/Eintrag)',
                         fontsize=12, fontweight='bold')
            ax1.grid(True, alpha=0.3)

            # Legenden kombinieren
            h1, l1 = ax1.get_legend_handles_labels()
            h2, l2 = ax2.get_legend_handles_labels()
            ax1.legend(h1 + h2, l1 + l2, fontsize=8, loc='upper right')

            fig.tight_layout()
            canvas.draw()
        except Exception as e:
            ax = fig.add_subplot(111)
            ax.text(0.5, 0.5,
                    f"Fehler beim Erstellen des Diagramms:\n{str(e)}",
                    ha='center', va='center', fontsize=10, color='red')
            ax.axis('off')
            canvas.draw()

    def _plot_monthly_cop_longterm(self, fig, canvas):
        """Plottet monatliche COP-Entwicklung über Jahre (Liniendiagramm)."""
        fig.clear()
        ax = fig.add_subplot(111)

        if (not hasattr(self.app, 'longterm_result')
                or not self.app.longterm_result
                or not hasattr(self.app, 'longterm_monthly_cop')
                or not self.app.longterm_monthly_cop):
            ax.text(0.5, 0.5,
                    "Keine Langzeit-Simulation verfügbar.\n\n"
                    "Bitte Berechnung durchführen.",
                    ha='center', va='center', fontsize=12, color='gray')
            ax.axis('off')
            canvas.draw()
            return

        try:
            lt = self.app.longterm_result
            monthly_cops = self.app.longterm_monthly_cop  # [year][month]
            n_years = len(monthly_cops)

            # JAZ pro Jahr
            jaz_per_year = []
            for year_cops in monthly_cops:
                # Gewichteter Durchschnitt (Heizmonate gewichten mehr)
                valid = [c for c in year_cops if c > 0]
                jaz_per_year.append(
                    sum(valid) / len(valid) if valid else 0
                )

            years = list(range(1, n_years + 1))

            # JAZ-Verlauf
            ax.plot(years, jaz_per_year, 'g-o', linewidth=2.5,
                    markersize=4, label='JAZ pro Jahr')

            # Min/Max COP pro Jahr
            min_cops = [min(c for c in yc if c > 0) if any(c > 0 for c in yc)
                       else 0 for yc in monthly_cops]
            max_cops = [max(yc) for yc in monthly_cops]

            ax.fill_between(years, min_cops, max_cops, alpha=0.15,
                           color='green', label='COP-Spanne (Min/Max)')
            ax.plot(years, min_cops, 'b--', linewidth=1, alpha=0.6,
                    label=f'Min. COP ({min_cops[-1]:.2f})')

            # Nenn-COP
            try:
                cop_nominal = float(
                    self.app.entries.get("heat_pump_cop_heating",
                                        ttk.Entry()).get() or "4.0")
                ax.axhline(y=cop_nominal, color='gray', linestyle=':',
                          linewidth=1.5, alpha=0.5,
                          label=f'Nenn-COP ({cop_nominal:.1f})')
            except (ValueError, AttributeError):
                pass

            ax.set_xlabel('Jahr', fontsize=11, fontweight='bold')
            ax.set_ylabel('COP / JAZ [-]', fontsize=11, fontweight='bold')
            ax.set_title('Monatliche COP-Entwicklung über Jahre',
                        fontsize=12, fontweight='bold')
            ax.grid(True, alpha=0.3)
            ax.legend(fontsize=8, loc='best')
            fig.tight_layout()
            canvas.draw()
        except Exception as e:
            ax.text(0.5, 0.5,
                    f"Fehler beim Erstellen des Diagramms:\n{str(e)}",
                    ha='center', va='center', fontsize=10, color='red')
            ax.axis('off')
            canvas.draw()

    def _plot_jaz_depth_comparison(self, fig, canvas):
        """Plottet JAZ-Vergleich bei verschiedenen Sondentiefen."""
        fig.clear()
        ax = fig.add_subplot(111)

        if (not hasattr(self.app, 'jaz_comparison')
                or not self.app.jaz_comparison
                or not self.app.jaz_comparison.depths):
            ax.text(0.5, 0.5,
                    "Keine JAZ-Vergleichsdaten verfügbar.\n\n"
                    "Bitte Berechnung durchführen.",
                    ha='center', va='center', fontsize=12, color='gray')
            ax.axis('off')
            canvas.draw()
            return

        try:
            jc = self.app.jaz_comparison
            depths = jc.depths
            jaz_vals = jc.jaz_values

            colors = ['#3498db' if i != len(depths) - 1 else '#2ecc71'
                     for i in range(len(depths))]

            bars = ax.bar([f'{d:.0f}m' for d in depths], jaz_vals,
                         color=colors, alpha=0.8, edgecolor='black',
                         linewidth=1)

            for bar, val in zip(bars, jaz_vals):
                ax.text(bar.get_x() + bar.get_width() / 2.,
                        bar.get_height() + 0.02,
                        f'{val:.2f}', ha='center', va='bottom',
                        fontsize=10, fontweight='bold')

            # Grenznutzen
            if len(depths) >= 2:
                marginal = []
                for i in range(1, len(depths)):
                    d_depth = depths[i] - depths[i-1]
                    d_jaz = jaz_vals[i] - jaz_vals[i-1]
                    marginal.append(d_jaz / d_depth * 10 if d_depth > 0
                                   else 0)

                ax.text(0.02, 0.98,
                        'Grenznutzen (ΔJAZ / 10m):\n' +
                        '\n'.join(
                            f'{depths[i-1]:.0f}→{depths[i]:.0f}m: '
                            f'+{marginal[i-1]:.3f}'
                            for i in range(1, len(depths))
                        ),
                        transform=ax.transAxes, fontsize=8,
                        verticalalignment='top',
                        bbox=dict(boxstyle='round', facecolor='lightgreen',
                                  alpha=0.5))

            ax.set_xlabel('Sondentiefe', fontsize=11, fontweight='bold')
            ax.set_ylabel('JAZ [-]', fontsize=11, fontweight='bold')
            ax.set_title('JAZ-Vergleich bei verschiedenen Sondentiefen',
                        fontsize=12, fontweight='bold')
            ax.grid(True, alpha=0.3, axis='y')

            # Y-Achse beginnt etwas unter dem Min-Wert
            if jaz_vals:
                ax.set_ylim(min(jaz_vals) * 0.85, max(jaz_vals) * 1.1)

            fig.tight_layout()
            canvas.draw()
        except Exception as e:
            ax.text(0.5, 0.5,
                    f"Fehler beim Erstellen des Diagramms:\n{str(e)}",
                    ha='center', va='center', fontsize=10, color='red')
            ax.axis('off')
            canvas.draw()

