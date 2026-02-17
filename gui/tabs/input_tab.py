"""Eingabe-Tab: Alle Eingabefelder, Sektionen und Event-Handler.

Extrahiert aus main_window_v3_professional.py (V3.4 Refactoring).
V3.4: Input-Validierung mit visuellem Feedback integriert.
"""

import tkinter as tk
from tkinter import ttk
import math
import logging

from gui.tooltips import InfoButton
from utils.pvgis_api import FALLBACK_CLIMATE_DATA
from utils.validators import (
    validate_gui_entry, safe_float, GUI_KEY_TO_VALIDATOR, PARAMETER_RANGES
)

logger = logging.getLogger(__name__)

# Farben für Validierungsfeedback
_COLOR_ERROR = "#ffcccc"       # Hintergrund bei Fehler
_COLOR_NORMAL = "white"        # Normaler Hintergrund
_COLOR_ERROR_FG = "#cc0000"    # Fehlermeldung Textfarbe


class InputTab:
    """Verwaltet den Eingabe-Tab mit allen Professional Features.
    
    Erstellt alle Eingabefelder, Sektionen (Projekt, Bohrfeld, Klima, Boden,
    Bohrloch, Verfüllmaterial, Fluid/Hydraulik, Wärmepumpe, Simulation) und
    die zugehörigen Event-Handler.
    """

    def __init__(self, parent_frame, app):
        """
        Args:
            parent_frame: ttk.Frame in dem der Tab aufgebaut wird.
            app: Referenz auf GeothermieGUIProfessional (für shared state).
        """
        self.frame = parent_frame
        self.app = app
        
        # Entry-Dictionaries (werden auf app gespiegelt)
        self.entries = {}
        self.project_entries = {}
        self.borehole_entries = {}
        self.heat_pump_entries = {}
        self.climate_entries = {}
        self.hydraulics_entries = {}
        
        # Dropdown-Variablen
        self.soil_type_var = tk.StringVar()
        self.grout_material_var = tk.StringVar()
        self.fluid_var = tk.StringVar()
        self.pipe_config_var = tk.StringVar(value="4-rohr-dual")
        self.pipe_type_var = tk.StringVar()
        self.climate_fallback_var = tk.StringVar(value="Deutschland Mitte")
        self.calculation_method_var = tk.StringVar(value="iterativ")
        
        self._build()

    # ─── Tab aufbauen ────────────────────────────────────────────

    def _build(self):
        """Erstellt den Eingabe-Tab mit allen Professional Features."""
        # 2-Spalten-Layout: Eingaben links, Grafik rechts
        main_container = ttk.PanedWindow(self.frame, orient=tk.HORIZONTAL)
        main_container.pack(fill=tk.BOTH, expand=True)

        # Linke Seite: Scrollbarer Container
        left_frame = ttk.Frame(main_container)
        canvas = tk.Canvas(left_frame)
        scrollbar = ttk.Scrollbar(left_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind("<Configure>",
                              lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Rechte Seite: Karte + Grafik
        right_frame = ttk.Frame(main_container, relief=tk.RIDGE, borderwidth=2)
        main_container.add(left_frame, weight=7)
        main_container.add(right_frame, weight=3)

        right_canvas = tk.Canvas(right_frame)
        right_scrollbar = ttk.Scrollbar(right_frame, orient="vertical",
                                        command=right_canvas.yview)
        right_scrollable = ttk.Frame(right_canvas)
        right_scrollable.bind("<Configure>",
                              lambda e: right_canvas.configure(
                                  scrollregion=right_canvas.bbox("all")))
        right_canvas.create_window((0, 0), window=right_scrollable, anchor="nw")
        right_canvas.configure(yscrollcommand=right_scrollbar.set)
        right_canvas.pack(side="left", fill="both", expand=True)
        right_scrollbar.pack(side="right", fill="y")

        # OSM-Karte
        try:
            from gui.map_widget import OSMMapWidget
            self.app.map_widget = OSMMapWidget(
                right_scrollable,
                width=500, height=320,
                default_lat=51.1657, default_lon=10.4515, default_zoom=6,
                on_position_change=self.app._on_map_position_changed,
            )
        except Exception as e:
            self.app.map_widget = None
            logger.warning(f"Kartenwidget konnte nicht geladen werden: {e}")

        self.app._create_static_borehole_graphic(right_scrollable)

        # ── Sektionen aufbauen ──
        row = 0

        self._add_section_header(scrollable_frame, row, "🏢 PROJEKTINFORMATIONEN")
        row += 1
        row = self._add_project_section(scrollable_frame, row)

        self._add_section_header(scrollable_frame, row, "🎯 BOHRFELD-KONFIGURATION")
        row += 1
        row = self._add_borehole_section(scrollable_frame, row)

        self._add_section_header(scrollable_frame, row, "🌍 KLIMADATEN (PVGIS)")
        row += 1
        row = self._add_climate_section(scrollable_frame, row)

        self._add_section_header(scrollable_frame, row, "🪨 BODENTYP & BODENWERTE")
        row += 1
        row = self._add_soil_section(scrollable_frame, row)

        self._add_section_header(scrollable_frame, row, "⚙️ BOHRLOCH-KONFIGURATION")
        row += 1
        row = self._add_borehole_config_section(scrollable_frame, row)

        self._add_section_header(scrollable_frame, row, "💧 VERFÜLLMATERIAL")
        row += 1
        row = self._add_grout_section(scrollable_frame, row)

        self._add_section_header(scrollable_frame, row,
                                 "🧪 WÄRMETRÄGERFLÜSSIGKEIT & HYDRAULIK")
        row += 1
        row = self._add_fluid_hydraulics_section(scrollable_frame, row)

        self._add_section_header(scrollable_frame, row, "♨️ WÄRMEPUMPE & LASTEN")
        row += 1
        row = self._add_heat_pump_section(scrollable_frame, row)

        self._add_section_header(scrollable_frame, row, "⏱️ SIMULATION")
        row += 1
        row = self._add_simulation_section(scrollable_frame, row)

        self._add_action_buttons(scrollable_frame, row)

        # Synchronisiere Dictionaries mit der Haupt-App
        self._sync_to_app()

    def _sync_to_app(self):
        """Spiegelt die Entry-Dictionaries auf das App-Objekt."""
        self.app.entries = self.entries
        self.app.project_entries = self.project_entries
        self.app.borehole_entries = self.borehole_entries
        self.app.heat_pump_entries = self.heat_pump_entries
        self.app.climate_entries = self.climate_entries
        self.app.hydraulics_entries = self.hydraulics_entries
        self.app.soil_type_var = self.soil_type_var
        self.app.grout_material_var = self.grout_material_var
        self.app.fluid_var = self.fluid_var
        self.app.pipe_config_var = self.pipe_config_var
        self.app.pipe_type_var = self.pipe_type_var
        self.app.climate_fallback_var = self.climate_fallback_var
        self.app.calculation_method_var = self.calculation_method_var

    # ── Hilfsfunktionen ──────────────────────────────────────────

    def _add_section_header(self, parent, row, text):
        """Fügt eine Sections-Überschrift hinzu."""
        ttk.Label(parent, text=text, font=("Arial", 12, "bold"),
                  foreground="#1f4788").grid(
            row=row, column=0, columnspan=2, sticky="w", padx=10, pady=(15, 5))

    def _add_entry(self, parent, row, label, key, default, dict_target,
                   info_key=None):
        """Fügt ein Eingabefeld hinzu, optional mit Info-Button und Validierung."""
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w",
                                           padx=10, pady=5)
        entry = tk.Entry(parent, width=32, bg=_COLOR_NORMAL)
        entry.insert(0, default)
        entry.grid(row=row, column=1, sticky="w", padx=10, pady=5)
        dict_target[key] = entry

        if info_key:
            InfoButton.create_info_button(parent, row, 2, info_key)

        # Validierung bei FocusOut (nur numerische Felder)
        if key in GUI_KEY_TO_VALIDATOR:
            entry.bind("<FocusOut>",
                       lambda e, k=key, ent=entry: self._validate_entry(ent, k))

        # Spezialbehandlung für Anzahl Bohrungen
        if key == "num_boreholes":
            entry.bind("<KeyRelease>", self._on_borehole_count_changed)

    # ── Sektionen ────────────────────────────────────────────────

    def _add_project_section(self, parent, row):
        self._add_entry(parent, row, "Projektname:", "project_name", "",
                        self.project_entries)
        row += 1
        self._add_entry(parent, row, "Kundenname:", "customer_name", "",
                        self.project_entries)
        row += 1
        self._add_entry(parent, row, "Straße + Nr.:", "address", "",
                        self.project_entries)
        row += 1
        self._add_entry(parent, row, "PLZ:", "postal_code", "",
                        self.project_entries)
        row += 1
        self._add_entry(parent, row, "Ort:", "city", "",
                        self.project_entries)
        row += 1
        return row

    def _add_borehole_section(self, parent, row):
        self._add_entry(parent, row, "Anzahl Bohrungen:", "num_boreholes", "1",
                        self.borehole_entries)
        row += 1
        self._add_entry(parent, row, "Abstand zwischen Bohrungen [m]:",
                        "spacing_between", "6", self.borehole_entries)
        row += 1
        self._add_entry(parent, row, "Abstand zum Grundstücksrand [m]:",
                        "spacing_property", "3", self.borehole_entries)
        row += 1
        self._add_entry(parent, row, "Abstand zum Gebäude [m]:",
                        "spacing_building", "3", self.borehole_entries)
        row += 1
        return row

    def _add_climate_section(self, parent, row):
        btn_frame = ttk.Frame(parent)
        btn_frame.grid(row=row, column=0, columnspan=2, sticky="w", padx=10,
                       pady=5)
        ttk.Button(btn_frame, text="🌍 Klimadaten von PVGIS laden",
                   command=self.app._load_pvgis_data).pack(side=tk.LEFT)
        ttk.Label(btn_frame, text="  oder Fallback verwenden:",
                  foreground="gray").pack(side=tk.LEFT, padx=10)

        climate_combo = ttk.Combobox(btn_frame,
                                     textvariable=self.climate_fallback_var,
                                     values=list(FALLBACK_CLIMATE_DATA.keys()),
                                     state="readonly", width=20)
        climate_combo.pack(side=tk.LEFT)
        climate_combo.bind("<<ComboboxSelected>>",
                           self._on_climate_fallback_selected)
        row += 1

        self._add_entry(parent, row, "Ø Temperatur Außenluft [°C]:",
                        "avg_air_temp", "10.0", self.climate_entries)
        row += 1
        self._add_entry(parent, row, "Ø Temperatur kältester Monat [°C]:",
                        "coldest_month_temp", "0.5", self.climate_entries)
        row += 1
        self._add_entry(parent, row, "Korrekturfaktor [%]:",
                        "correction_factor", "100", self.climate_entries)
        row += 1
        return row

    def _add_soil_section(self, parent, row):
        ttk.Label(parent, text="Bodentyp:").grid(row=row, column=0, sticky="w",
                                                  padx=10, pady=5)
        soil_combo = ttk.Combobox(parent, textvariable=self.soil_type_var,
                                  values=self.app.soil_db.get_all_names(),
                                  state="readonly", width=30)
        soil_combo.grid(row=row, column=1, sticky="w", padx=10, pady=5)
        soil_combo.bind("<<ComboboxSelected>>", self._on_soil_selected)
        soil_combo.current(0)
        row += 1

        self.soil_info_label = ttk.Label(parent, text="", foreground="blue",
                                         wraplength=400)
        self.soil_info_label.grid(row=row, column=0, columnspan=2, sticky="w",
                                  padx=10, pady=2)
        self.app.soil_info_label = self.soil_info_label
        row += 1

        self._add_entry(parent, row, "Wärmeleitfähigkeit Boden [W/m·K]:",
                        "ground_thermal_cond", "1.8", self.entries)
        row += 1
        self._add_entry(parent, row, "Wärmekapazität Boden [J/m³·K]:",
                        "ground_heat_cap", "2400000", self.entries)
        row += 1
        self._add_entry(parent, row, "Ungestörte Bodentemperatur [°C]:",
                        "ground_temp", "10.0", self.entries)
        row += 1
        self._add_entry(parent, row, "Geothermischer Gradient [K/m]:",
                        "geothermal_gradient", "0.03", self.entries)
        row += 1

        self._on_soil_selected(None)
        return row

    def _add_borehole_config_section(self, parent, row):
        self._add_entry(parent, row, "Bohrloch-Durchmesser [mm]:",
                        "borehole_diameter", "152", self.entries,
                        "borehole_diameter")
        row += 1

        ttk.Label(parent, text="Rohrkonfiguration:").grid(
            row=row, column=0, sticky="w", padx=10, pady=5)
        config_combo = ttk.Combobox(
            parent, textvariable=self.pipe_config_var,
            values=["single-u", "double-u", "4-rohr-dual",
                    "4-rohr-4verbinder", "coaxial"],
            state="readonly", width=30)
        config_combo.grid(row=row, column=1, sticky="w", padx=10, pady=5)
        row += 1

        ttk.Label(parent, text="Rohrtyp:").grid(
            row=row, column=0, sticky="w", padx=10, pady=5)
        self.pipe_type_combo = ttk.Combobox(
            parent, textvariable=self.pipe_type_var,
            state="readonly", width=30)
        self.pipe_type_combo.grid(row=row, column=1, sticky="w", padx=10,
                                  pady=5)
        self.pipe_type_combo.bind("<<ComboboxSelected>>",
                                  self._on_pipe_selected)
        self.app.pipe_type_combo = self.pipe_type_combo
        row += 1

        self._add_entry(parent, row, "Rohr Außendurchmesser [mm]:",
                        "pipe_outer_diameter", "32", self.entries,
                        "pipe_outer_diameter")
        row += 1
        self._add_entry(parent, row, "Rohr Wandstärke [mm]:",
                        "pipe_thickness", "3", self.entries,
                        "pipe_wall_thickness")
        row += 1
        self._add_entry(parent, row, "Rohr Wärmeleitfähigkeit [W/m·K]:",
                        "pipe_thermal_cond", "0.42", self.entries)
        row += 1
        self._add_entry(parent, row, "Schenkelabstand [mm]:",
                        "shank_spacing", "65", self.entries, "shank_spacing")
        row += 1

        ttk.Label(parent, text="Max. Sondenlänge pro Bohrung [m]:",
                  foreground="gray").grid(
            row=row, column=0, sticky="w", padx=10, pady=5)
        entry = ttk.Entry(parent, width=32)
        entry.insert(0, "100")
        entry.grid(row=row, column=1, sticky="w", padx=10, pady=5)
        self.entries["max_depth_per_borehole"] = entry
        row += 1

        ttk.Label(parent,
                  text="(wird nur bei VDI 4640 Methode verwendet)",
                  foreground="gray",
                  font=("Arial", 8, "italic")).grid(
            row=row, column=1, sticky="w", padx=10, pady=(0, 5))
        row += 1
        return row

    def _add_grout_section(self, parent, row):
        ttk.Label(parent, text="Material:").grid(
            row=row, column=0, sticky="w", padx=10, pady=5)
        grout_combo = ttk.Combobox(
            parent, textvariable=self.grout_material_var,
            values=self.app.grout_db.get_all_names(),
            state="readonly", width=30)
        grout_combo.grid(row=row, column=1, sticky="w", padx=10, pady=5)
        grout_combo.bind("<<ComboboxSelected>>", self._on_grout_selected)
        grout_combo.current(1)
        InfoButton.create_info_button(parent, row, 2, "grout_material")
        row += 1

        self.grout_info_label = ttk.Label(parent, text="", foreground="blue",
                                          wraplength=400)
        self.grout_info_label.grid(row=row, column=0, columnspan=2,
                                    sticky="w", padx=10, pady=2)
        self.app.grout_info_label = self.grout_info_label
        row += 1

        self._add_entry(parent, row,
                        "Wärmeleitfähigkeit Verfüllung [W/m·K]:",
                        "grout_thermal_cond", "1.3", self.entries)
        row += 1

        ttk.Button(parent, text="💧 Materialmengen berechnen",
                   command=self.app._calculate_grout_materials).grid(
            row=row, column=0, columnspan=2, pady=5, padx=10)
        row += 1

        self._on_grout_selected(None)
        return row

    def _add_fluid_hydraulics_section(self, parent, row):
        ttk.Label(parent, text="Wärmeträgerfluid:").grid(
            row=row, column=0, sticky="w", padx=10, pady=5)
        fluid_combo = ttk.Combobox(
            parent, textvariable=self.fluid_var,
            values=self.app.fluid_db.get_all_names(),
            state="readonly", width=30)
        fluid_combo.grid(row=row, column=1, sticky="w", padx=10, pady=5)
        fluid_combo.bind("<<ComboboxSelected>>", self._on_fluid_selected)
        if "Ethylenglykol 25%" in self.app.fluid_db.get_all_names():
            fluid_combo.current(
                self.app.fluid_db.get_all_names().index("Ethylenglykol 25%"))
        InfoButton.create_info_button(parent, row, 2, "fluid_selection")
        row += 1

        temp_entry = ttk.Entry(parent, width=32)
        temp_entry.insert(0, "5.0")
        temp_entry.grid(row=row, column=1, sticky="w", padx=10, pady=5)
        self.entries["fluid_temperature"] = temp_entry
        ttk.Label(parent, text="Betriebstemperatur [°C]:").grid(
            row=row, column=0, sticky="w", padx=10, pady=5)
        InfoButton.create_info_button(parent, row, 2, "fluid_temperature")
        temp_entry.bind("<KeyRelease>",
                        lambda e: self._on_fluid_temperature_changed())
        row += 1

        self._add_entry(parent, row, "Anzahl Solekreise:", "num_circuits", "1",
                        self.hydraulics_entries)
        row += 1

        self._add_entry(parent, row, "Volumenstrom [m³/h]:",
                        "fluid_flow_rate", "1.8", self.entries,
                        "fluid_flow_rate")
        row += 1
        self._add_entry(parent, row, "Wärmeleitfähigkeit [W/m·K]:",
                        "fluid_thermal_cond", "0.48", self.entries,
                        "fluid_thermal_cond")
        row += 1
        self._add_entry(parent, row, "Wärmekapazität [J/kg·K]:",
                        "fluid_heat_cap", "3800", self.entries)
        row += 1
        self._add_entry(parent, row, "Dichte [kg/m³]:",
                        "fluid_density", "1030", self.entries)
        row += 1
        self._add_entry(parent, row, "Viskosität [Pa·s]:",
                        "fluid_viscosity", "0.004", self.entries)
        row += 1

        self.fluid_info_label = ttk.Label(parent, text="", foreground="blue",
                                          wraplength=400)
        self.fluid_info_label.grid(row=row, column=0, columnspan=2,
                                    sticky="w", padx=10, pady=2)
        self.app.fluid_info_label = self.fluid_info_label
        row += 1

        ttk.Button(parent, text="💨 Hydraulik berechnen",
                   command=self.app._calculate_hydraulics).grid(
            row=row, column=0, columnspan=2, pady=5, padx=10)
        row += 1

        self._on_fluid_selected(None)
        return row

    def _add_heat_pump_section(self, parent, row):
        heat_power_entry = ttk.Entry(parent, width=32)
        heat_power_entry.insert(0, "6.0")
        heat_power_entry.grid(row=row, column=1, sticky="w", padx=10, pady=5)
        self.heat_pump_entries["heat_pump_power"] = heat_power_entry
        ttk.Label(parent, text="Wärmepumpenleistung [kW]:").grid(
            row=row, column=0, sticky="w", padx=10, pady=5)
        InfoButton.create_info_button(parent, row, 2, "heat_pump_power")
        heat_power_entry.bind("<KeyRelease>",
                              lambda e: self._on_parameter_changed())
        row += 1
        row += 1
        self._add_entry(parent, row,
                        "COP Heizen (Coefficient of Performance):",
                        "heat_pump_cop", "4.0", self.entries, "cop")
        row += 1
        self._add_entry(parent, row, "EER Kühlen (Energy Efficiency Ratio):",
                        "heat_pump_eer", "4.0", self.entries, "heat_pump_eer")
        row += 1

        ttk.Label(parent, text="Kälteleistung [kW]:",
                  foreground="gray").grid(
            row=row, column=0, sticky="w", padx=10, pady=5)
        self.cold_power_label = ttk.Label(parent, text="(wird berechnet)",
                                          foreground="gray")
        self.cold_power_label.grid(row=row, column=1, sticky="w",
                                    padx=10, pady=5)
        self.app.cold_power_label = self.cold_power_label
        row += 1

        self._add_entry(parent, row, "Warmwasser (Anzahl Personen):",
                        "num_persons_dhw", "4", self.heat_pump_entries)
        row += 1
        self._add_entry(parent, row, "Jahres-Heizenergie [kWh]:",
                        "annual_heating", "12000.0", self.entries,
                        "annual_heating")
        row += 1
        self._add_entry(parent, row, "Jahres-Kühlenergie [kWh]:",
                        "annual_cooling", "0.0", self.entries, "annual_cooling")
        row += 1
        self._add_entry(parent, row, "Heiz-Spitzenlast [kW]:",
                        "peak_heating", "6.0", self.entries, "peak_heating")
        row += 1
        self._add_entry(parent, row, "Kühl-Spitzenlast [kW]:",
                        "peak_cooling", "0.0", self.entries, "peak_cooling")
        row += 1
        self._add_entry(parent, row, "Min. Fluidtemperatur [°C]:",
                        "min_fluid_temp", "-2.0", self.entries)
        row += 1
        self._add_entry(parent, row, "Max. Fluidtemperatur [°C]:",
                        "max_fluid_temp", "15.0", self.entries)
        row += 1

        delta_t_entry = ttk.Entry(parent, width=32)
        delta_t_entry.insert(0, "3.0")
        delta_t_entry.grid(row=row, column=1, sticky="w", padx=10, pady=5)
        self.entries["delta_t_fluid"] = delta_t_entry
        ttk.Label(parent, text="Temperaturdifferenz Fluid [K]:").grid(
            row=row, column=0, sticky="w", padx=10, pady=5)
        delta_t_entry.bind("<KeyRelease>",
                           lambda e: self._on_parameter_changed())
        row += 1
        row += 1
        return row

    def _add_simulation_section(self, parent, row):
        self._add_entry(parent, row, "Simulationsdauer [Jahre]:",
                        "simulation_years", "25", self.entries)
        row += 1
        self._add_entry(parent, row, "Startwert Bohrtiefe [m]:",
                        "initial_depth", "100", self.entries)
        row += 1

        ttk.Separator(parent, orient="horizontal").grid(
            row=row, column=0, columnspan=2, sticky="ew", padx=10, pady=10)
        row += 1

        ttk.Label(parent, text="Berechnungsmethode:",
                  font=("Arial", 10, "bold")).grid(
            row=row, column=0, sticky="w", padx=10, pady=5)
        row += 1

        method_frame = ttk.Frame(parent)
        method_frame.grid(row=row, column=0, columnspan=2, sticky="w",
                          padx=20, pady=5)

        ttk.Radiobutton(
            method_frame,
            text="⚙️  Iterative Methode (Eskilson/Hellström)",
            variable=self.calculation_method_var,
            value="iterativ"
        ).pack(anchor="w", pady=2)

        ttk.Radiobutton(
            method_frame,
            text="📐 VDI 4640 Methode (Grundlast/Periodisch/Peak)",
            variable=self.calculation_method_var,
            value="vdi4640"
        ).pack(anchor="w", pady=2)
        row += 1

        ttk.Label(
            parent,
            text=("VDI 4640: Berücksichtigt Heiz- und Kühllast getrennt,"
                  " erkennt dominante Last automatisch."),
            foreground="gray",
            font=("Arial", 8, "italic"),
            wraplength=500
        ).grid(row=row, column=0, columnspan=2, sticky="w", padx=20,
               pady=(0, 5))
        row += 1
        return row

    def _add_action_buttons(self, parent, row):
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=row, column=0, columnspan=2, pady=20, padx=10)

        ttk.Button(button_frame, text="🚀 Berechnung starten",
                   command=self.app._run_calculation,
                   width=25).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="📄 PDF-Bericht erstellen",
                   command=self.app._export_pdf,
                   width=25).pack(side=tk.LEFT, padx=5)

    # ─── Validierung ─────────────────────────────────────────────

    def _validate_entry(self, entry, gui_key):
        """Validiert ein einzelnes Eingabefeld mit visuellem Feedback.

        Args:
            entry: tk.Entry Widget
            gui_key: GUI-Entry-Schlüssel
        """
        raw_value = entry.get().strip()
        if not raw_value:
            entry.config(bg=_COLOR_NORMAL)
            return True

        value = safe_float(raw_value)

        # Komma automatisch zu Punkt konvertieren
        if "," in raw_value:
            entry.delete(0, tk.END)
            entry.insert(0, str(value))

        is_valid, msg = validate_gui_entry(gui_key, value)

        if is_valid:
            entry.config(bg=_COLOR_NORMAL)
            # Tooltip entfernen falls vorhanden
            if hasattr(entry, '_validation_tooltip'):
                entry._validation_tooltip = None
        else:
            entry.config(bg=_COLOR_ERROR)
            entry._validation_tooltip = msg
            logger.debug(f"Validierung fehlgeschlagen: {gui_key} = {value}: {msg}")

        return is_valid

    def validate_all_entries(self):
        """Validiert alle Eingabefelder. Gibt Fehlerliste zurück.

        Returns:
            Liste von Fehlermeldungen (leer wenn alles OK)
        """
        errors = []
        all_dicts = [
            self.entries,
            self.borehole_entries,
            self.heat_pump_entries,
            self.hydraulics_entries,
        ]

        for dict_target in all_dicts:
            for key, entry in dict_target.items():
                if key not in GUI_KEY_TO_VALIDATOR:
                    continue
                raw_value = entry.get().strip()
                if not raw_value:
                    continue
                value = safe_float(raw_value)
                is_valid, msg = validate_gui_entry(key, value)
                if not is_valid:
                    entry.config(bg=_COLOR_ERROR)
                    errors.append(msg)
                else:
                    entry.config(bg=_COLOR_NORMAL)

        return errors

    # ─── Event-Handler ───────────────────────────────────────────

    def _on_soil_selected(self, event):
        """Wenn ein Bodentyp ausgewählt wird."""
        soil_name = self.soil_type_var.get()
        soil = self.app.soil_db.get_soil_type(soil_name)

        if soil:
            self.entries["ground_thermal_cond"].delete(0, tk.END)
            self.entries["ground_thermal_cond"].insert(
                0, str(soil.thermal_conductivity_typical))

            self.entries["ground_heat_cap"].delete(0, tk.END)
            self.entries["ground_heat_cap"].insert(
                0, str(soil.heat_capacity_typical * 1e6))

            info = (f"{soil.description}\n"
                    f"λ: {soil.thermal_conductivity_min}-"
                    f"{soil.thermal_conductivity_max} W/m·K "
                    f"(typ: {soil.thermal_conductivity_typical})\n"
                    f"Wärmeentzug: {soil.heat_extraction_rate_min}-"
                    f"{soil.heat_extraction_rate_max} W/m")
            self.soil_info_label.config(text=info)

    def _on_fluid_selected(self, event):
        """Wenn ein Fluid ausgewählt wird."""
        self._update_fluid_properties()

    def _on_parameter_changed(self):
        """Debounced Neuberechnung bei Parameteränderung."""
        if self.app._hydraulics_debounce_id is not None:
            self.app.root.after_cancel(self.app._hydraulics_debounce_id)
        self.app._hydraulics_debounce_id = self.app.root.after(
            500, self._on_parameter_changed_debounced)

    def _on_parameter_changed_debounced(self):
        self.app._hydraulics_debounce_id = None
        try:
            self.app._calculate_hydraulics()
        except Exception:
            pass

    def _on_fluid_temperature_changed(self):
        self._update_fluid_properties()

    def _update_fluid_properties(self):
        """Aktualisiert die Fluid-Eigenschaften basierend auf Auswahl und Temperatur."""
        if not self.fluid_var.get():
            return

        fluid_name = self.fluid_var.get()
        fluid = self.app.fluid_db.get_fluid(fluid_name)

        if fluid:
            try:
                temp_entry = self.entries.get("fluid_temperature")
                temp = float(temp_entry.get() or "5.0") if temp_entry else 5.0
            except (ValueError, AttributeError):
                temp = 5.0

            props = fluid.get_properties_at_temp(temp)

            for key, fmt in [("fluid_thermal_cond", "{:.3f}"),
                             ("fluid_heat_cap", "{:.1f}"),
                             ("fluid_density", "{:.1f}"),
                             ("fluid_viscosity", "{:.6f}")]:
                if key in self.entries:
                    self.entries[key].delete(0, tk.END)
                    self.entries[key].insert(
                        0, fmt.format(props[key.replace("fluid_", "")
                                            .replace("thermal_cond",
                                                     "thermal_conductivity")
                                            .replace("heat_cap",
                                                     "heat_capacity")]))

            info = (f"{fluid.name}\nFrostschutz: {fluid.min_temp:.1f}°C\n"
                    f"Betriebstemp: {temp:.1f}°C\n"
                    f"Konzentration: {fluid.concentration_percent:.0f}%")
            if hasattr(self, 'fluid_info_label'):
                self.fluid_info_label.config(text=info)

    def _on_grout_selected(self, event):
        """Wenn ein Verfüllmaterial ausgewählt wird."""
        material_name = self.grout_material_var.get()
        material = self.app.grout_db.get_material(material_name)

        if material:
            self.entries["grout_thermal_cond"].delete(0, tk.END)
            self.entries["grout_thermal_cond"].insert(
                0, str(material.thermal_conductivity))

            info = (f"{material.description}\n"
                    f"λ: {material.thermal_conductivity} W/m·K, "
                    f"ρ: {material.density} kg/m³, "
                    f"Preis: {material.price_per_kg} EUR/kg\n"
                    f"{material.typical_application}")
            self.grout_info_label.config(text=info)

    def _on_pipe_selected(self, event):
        """Wenn ein Rohrtyp ausgewählt wird."""
        if not self.app.pipes:
            return

        selected_name = self.pipe_type_var.get()
        for pipe in self.app.pipes:
            if pipe.name == selected_name:
                self.entries["pipe_outer_diameter"].delete(0, tk.END)
                self.entries["pipe_outer_diameter"].insert(
                    0, f"{pipe.diameter_m * 1000:.1f}")

                self.entries["pipe_thickness"].delete(0, tk.END)
                self.entries["pipe_thickness"].insert(
                    0, f"{pipe.thickness_m * 1000:.1f}")

                self.entries["pipe_thermal_cond"].delete(0, tk.END)
                self.entries["pipe_thermal_cond"].insert(
                    0, str(pipe.thermal_conductivity))
                break

    def _on_climate_fallback_selected(self, event):
        """Wenn Fallback-Klimadaten ausgewählt werden."""
        region = self.climate_fallback_var.get()
        data = FALLBACK_CLIMATE_DATA.get(region)

        if data:
            self.climate_entries["avg_air_temp"].delete(0, tk.END)
            self.climate_entries["avg_air_temp"].insert(
                0, str(data['yearly_avg_temp']))

            self.climate_entries["coldest_month_temp"].delete(0, tk.END)
            self.climate_entries["coldest_month_temp"].insert(
                0, str(data['coldest_month_temp']))

            self.app.status_var.set(f"✓ Klimadaten geladen: {region}")

    def _on_borehole_count_changed(self, event=None):
        """Wird aufgerufen, wenn sich die Anzahl der Bohrungen ändert."""
        try:
            num = int(self.borehole_entries["num_boreholes"].get())
            if "num_circuits" in self.hydraulics_entries:
                self.hydraulics_entries["num_circuits"].delete(0, tk.END)
                self.hydraulics_entries["num_circuits"].insert(0, str(num))
        except (ValueError, KeyError):
            pass
