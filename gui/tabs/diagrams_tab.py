"""Diagramme-Tab: Alle Visualisierungen und Plot-Funktionen.

Extrahiert aus main_window_v3_professional.py (V3.4 Refactoring).
Enthält 12 Diagramme:
  1. Monatliche Temperaturen
  2. Bohrloch-Schema (Querschnitt)
  3. Pumpen-Kennlinien (H-Q-Kurven)
  4. Reynolds-Kurve
  5. Druckverlust-Komponenten
  6. Volumenstrom vs. Druckverlust
  7. Pumpenleistung über Betriebszeit
  8. Temperaturspreizung Sole
  9. COP vs. Sole-Eintrittstemperatur
 10. COP vs. Vorlauftemperatur
 11. JAZ-Abschätzung
 12. Energieverbrauch-Vergleich
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
        ]

        for title, plot_fn in diagrams:
            self._add_diagram_frame(scrollable_frame, title, plot_fn)

        # Mousewheel
        def _on_mousewheel(event):
            canvas_container.yview_scroll(int(-1 * (event.delta / 120)),
                                           "units")
        canvas_container.bind_all("<MouseWheel>", _on_mousewheel)

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
