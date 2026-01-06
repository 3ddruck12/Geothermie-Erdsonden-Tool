"""Professional Edition V3 GUI mit allen Features.

Neue Features in V3:
- Verfüllmaterial-Dropdown mit Mengenberechnung
- Bodentyp-Dropdown nach VDI 4640
- PVGIS Klimadaten-Integration
- Hydraulik-Berechnungen
- Erweiterte Wärmepumpendaten
- Frostschutz-Konfiguration
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import os
from typing import Optional, Dict, Any
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.patches import Circle
import numpy as np
import math

from parsers import PipeParser, EEDParser
from calculations import BoreholeCalculator
from calculations.hydraulics import HydraulicsCalculator
from calculations.vdi4640 import VDI4640Calculator
from utils import PDFReportGenerator
from utils.pvgis_api import PVGISClient, FALLBACK_CLIMATE_DATA
from data import GroutMaterialDB, SoilTypeDB, FluidDatabase, FluidDatabase
from gui.tooltips import InfoButton
from gui.pump_selection_dialog import PumpSelectionDialog
from utils.get_file_handler import GETFileHandler


class GeothermieGUIProfessional:
    """Professional Edition V3 GUI."""
    
    def __init__(self, root):
        """Initialisiert die Professional GUI."""
        self.root = root
        self.root.title("Geothermie Erdsonden-Tool - Professional Edition V3.2.1")
        self.root.geometry("1800x1100")
        
        # Module
        self.pipe_parser = PipeParser()
        self.eed_parser = EEDParser()
        self.calculator = BoreholeCalculator()
        # VDI 4640 Calculator mit Debug-Modus
        debug_file = os.path.join(os.path.expanduser("~"), "vdi4640_debug.log")
        self.vdi4640_calc = VDI4640Calculator(debug=True, debug_file=debug_file)
        self.hydraulics_calc = HydraulicsCalculator()
        self.pdf_generator = PDFReportGenerator()
        self.pvgis_client = PVGISClient()
        self.grout_db = GroutMaterialDB()
        self.soil_db = SoilTypeDB()
        self.fluid_db = FluidDatabase()
        self.get_handler = GETFileHandler()
        
        # Daten
        self.pipes = []
        self.result = None
        self.vdi4640_result = None  # NEU: VDI 4640 Ergebnis
        self.current_params = {}
        self.hydraulics_result = None
        self.grout_calculation = None
        self.climate_data = None
        self.borefield_config = None
        
        # GUI aufbauen
        self._create_menu()
        self._create_main_layout()
        self._create_status_bar()
        
        # Lade Daten
        self._load_default_pipes()
    
    def _create_menu(self):
        """Erstellt die Menüleiste."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Datei", menu=file_menu)
        file_menu.add_command(label="📥 .get Projekt laden...", command=self._import_get_file, accelerator="Ctrl+O")
        file_menu.add_command(label="💾 Als .get speichern...", command=self._export_get_file, accelerator="Ctrl+S")
        file_menu.add_separator()
        file_menu.add_command(label="Pipe.txt laden", command=self._load_pipe_file)
        file_menu.add_command(label="EED .dat laden", command=self._load_eed_file)
        file_menu.add_separator()
        file_menu.add_command(label="PDF-Bericht erstellen", command=self._export_pdf, accelerator="Ctrl+P")
        file_menu.add_command(label="Text exportieren", command=self._export_results)
        file_menu.add_separator()
        file_menu.add_command(label="Beenden", command=self.root.quit)
        
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Extras", menu=tools_menu)
        tools_menu.add_command(label="🌍 PVGIS Klimadaten laden", command=self._load_pvgis_data)
        tools_menu.add_command(label="💧 Materialmengen berechnen", command=self._calculate_grout_materials)
        tools_menu.add_command(label="💨 Hydraulik berechnen", command=self._calculate_hydraulics)
        
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Hilfe", menu=help_menu)
        help_menu.add_command(label="Über", command=self._show_about)
        help_menu.add_command(label="PVGIS Info", command=self._show_pvgis_info)
        
        self.root.bind('<Control-o>', lambda e: self._import_get_file())
        self.root.bind('<Control-s>', lambda e: self._export_get_file())
        self.root.bind('<Control-p>', lambda e: self._export_pdf())
    
    def _create_main_layout(self):
        """Erstellt das Hauptlayout."""
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Tabs
        self.input_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.input_frame, text="📝 Eingabe & Konfiguration")
        self._create_input_tab()
        
        self.results_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.results_frame, text="📊 Ergebnisse")
        self._create_results_tab()
        
        self.materials_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.materials_frame, text="💧 Material & Hydraulik")
        self._create_materials_tab()
        
        self.borefield_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.borefield_frame, text="🌐 Bohrfeld-Simulation")
        self._create_borefield_tab()
        
        self.viz_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.viz_frame, text="📈 Diagramme")
        self._create_visualization_tab()
    
    def _create_input_tab(self):
        """Erstellt den Eingabe-Tab mit allen Professional Features."""
        # 2-Spalten-Layout: Eingaben links, Grafik rechts
        main_container = ttk.Frame(self.input_frame)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Linke Seite: Scrollbarer Container für Eingaben
        left_frame = ttk.Frame(main_container)
        left_frame.pack(side="left", fill="both", expand=True)
        
        canvas = tk.Canvas(left_frame)
        scrollbar = ttk.Scrollbar(left_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Rechte Seite: Statische Grafik
        right_frame = ttk.Frame(main_container, relief=tk.RIDGE, borderwidth=2)
        right_frame.pack(side="right", fill="both", padx=10, pady=10)
        self._create_static_borehole_graphic(right_frame)
        
        row = 0
        self.entries = {}
        self.project_entries = {}
        self.borehole_entries = {}
        self.heat_pump_entries = {}
        self.climate_entries = {}
        self.hydraulics_entries = {}
        
        # === PROJEKTINFORMATIONEN ===
        self._add_section_header(scrollable_frame, row, "🏢 PROJEKTINFORMATIONEN")
        row += 1
        row = self._add_project_section(scrollable_frame, row)
        
        # === BOHRFELD-KONFIGURATION ===
        self._add_section_header(scrollable_frame, row, "🎯 BOHRFELD-KONFIGURATION")
        row += 1
        row = self._add_borehole_section(scrollable_frame, row)
        
        # === KLIMADATEN ===
        self._add_section_header(scrollable_frame, row, "🌍 KLIMADATEN (PVGIS)")
        row += 1
        row = self._add_climate_section(scrollable_frame, row)
        
        # === BODENTYP ===
        self._add_section_header(scrollable_frame, row, "🪨 BODENTYP & BODENWERTE")
        row += 1
        row = self._add_soil_section(scrollable_frame, row)
        
        # === BOHRLOCH-KONFIGURATION ===
        self._add_section_header(scrollable_frame, row, "⚙️ BOHRLOCH-KONFIGURATION")
        row += 1
        row = self._add_borehole_config_section(scrollable_frame, row)
        
        # === VERFÜLLMATERIAL ===
        self._add_section_header(scrollable_frame, row, "💧 VERFÜLLMATERIAL")
        row += 1
        row = self._add_grout_section(scrollable_frame, row)
        
        # === WÄRMETRÄGERFLÜSSIGKEIT ===
        self._add_section_header(scrollable_frame, row, "🧪 WÄRMETRÄGERFLÜSSIGKEIT & HYDRAULIK")
        row += 1
        row = self._add_fluid_hydraulics_section(scrollable_frame, row)
        
        # === WÄRMEPUMPE ===
        self._add_section_header(scrollable_frame, row, "♨️ WÄRMEPUMPE & LASTEN")
        row += 1
        row = self._add_heat_pump_section(scrollable_frame, row)
        
        # === SIMULATION ===
        self._add_section_header(scrollable_frame, row, "⏱️ SIMULATION")
        row += 1
        row = self._add_simulation_section(scrollable_frame, row)
        
        # === BUTTONS ===
        self._add_action_buttons(scrollable_frame, row)
    
    def _add_section_header(self, parent, row, text):
        """Fügt eine Sections-Überschrift hinzu."""
        ttk.Label(parent, text=text, font=("Arial", 12, "bold"), 
                 foreground="#1f4788").grid(
            row=row, column=0, columnspan=2, sticky="w", padx=10, pady=(15, 5)
        )
    
    def _add_project_section(self, parent, row):
        """Projektdaten-Sektion."""
        self._add_entry(parent, row, "Projektname:", "project_name", "", self.project_entries)
        row += 1
        self._add_entry(parent, row, "Kundenname:", "customer_name", "", self.project_entries)
        row += 1
        self._add_entry(parent, row, "Straße + Nr.:", "address", "", self.project_entries)
        row += 1
        self._add_entry(parent, row, "PLZ:", "postal_code", "", self.project_entries)
        row += 1
        self._add_entry(parent, row, "Ort:", "city", "", self.project_entries)
        row += 1
        return row
    
    def _add_borehole_section(self, parent, row):
        """Bohrfeld-Konfiguration."""
        self._add_entry(parent, row, "Anzahl Bohrungen:", "num_boreholes", "1", self.borehole_entries)
        row += 1
        self._add_entry(parent, row, "Abstand zwischen Bohrungen [m]:", "spacing_between", "6", self.borehole_entries)
        row += 1
        self._add_entry(parent, row, "Abstand zum Grundstücksrand [m]:", "spacing_property", "3", self.borehole_entries)
        row += 1
        self._add_entry(parent, row, "Abstand zum Gebäude [m]:", "spacing_building", "3", self.borehole_entries)
        row += 1
        return row
    
    def _add_climate_section(self, parent, row):
        """Klimadaten-Sektion."""
        # Button zum Laden
        btn_frame = ttk.Frame(parent)
        btn_frame.grid(row=row, column=0, columnspan=2, sticky="w", padx=10, pady=5)
        ttk.Button(btn_frame, text="🌍 Klimadaten von PVGIS laden", 
                  command=self._load_pvgis_data).pack(side=tk.LEFT)
        ttk.Label(btn_frame, text="  oder Fallback verwenden:", 
                 foreground="gray").pack(side=tk.LEFT, padx=10)
        
        self.climate_fallback_var = tk.StringVar(value="Deutschland Mitte")
        climate_combo = ttk.Combobox(btn_frame, textvariable=self.climate_fallback_var,
                                     values=list(FALLBACK_CLIMATE_DATA.keys()),
                                     state="readonly", width=20)
        climate_combo.pack(side=tk.LEFT)
        climate_combo.bind("<<ComboboxSelected>>", self._on_climate_fallback_selected)
        row += 1
        
        self._add_entry(parent, row, "Ø Temperatur Außenluft [°C]:", "avg_air_temp", "10.0", self.climate_entries)
        row += 1
        self._add_entry(parent, row, "Ø Temperatur kältester Monat [°C]:", "coldest_month_temp", "0.5", self.climate_entries)
        row += 1
        self._add_entry(parent, row, "Korrekturfaktor [%]:", "correction_factor", "100", self.climate_entries)
        row += 1
        return row
    
    def _add_soil_section(self, parent, row):
        """Bodentyp-Sektion."""
        ttk.Label(parent, text="Bodentyp:").grid(row=row, column=0, sticky="w", padx=10, pady=5)
        self.soil_type_var = tk.StringVar()
        soil_combo = ttk.Combobox(parent, textvariable=self.soil_type_var,
                                  values=self.soil_db.get_all_names(),
                                  state="readonly", width=30)
        soil_combo.grid(row=row, column=1, sticky="w", padx=10, pady=5)
        soil_combo.bind("<<ComboboxSelected>>", self._on_soil_selected)
        soil_combo.current(0)  # Sand als Standard
        row += 1
        
        # Boden-Info Label
        self.soil_info_label = ttk.Label(parent, text="", foreground="blue", wraplength=400)
        self.soil_info_label.grid(row=row, column=0, columnspan=2, sticky="w", padx=10, pady=2)
        row += 1
        
        self._add_entry(parent, row, "Wärmeleitfähigkeit Boden [W/m·K]:", "ground_thermal_cond", "1.8", self.entries)
        row += 1
        self._add_entry(parent, row, "Wärmekapazität Boden [J/m³·K]:", "ground_heat_cap", "2400000", self.entries)
        row += 1
        self._add_entry(parent, row, "Ungestörte Bodentemperatur [°C]:", "ground_temp", "10.0", self.entries)
        row += 1
        self._add_entry(parent, row, "Geothermischer Gradient [K/m]:", "geothermal_gradient", "0.03", self.entries)
        row += 1
        
        # Trigger initial selection
        self._on_soil_selected(None)
        return row
    
    def _add_borehole_config_section(self, parent, row):
        """Bohrloch-Konfigurations-Sektion."""
        self._add_entry(parent, row, "Bohrloch-Durchmesser [mm]:", "borehole_diameter", "152", self.entries, "borehole_diameter")
        row += 1
        
        ttk.Label(parent, text="Rohrkonfiguration:").grid(row=row, column=0, sticky="w", padx=10, pady=5)
        self.pipe_config_var = tk.StringVar(value="4-rohr-dual")
        config_combo = ttk.Combobox(parent, textvariable=self.pipe_config_var,
                                    values=["single-u", "double-u", "4-rohr-dual", "4-rohr-4verbinder", "coaxial"],
                                    state="readonly", width=30)
        config_combo.grid(row=row, column=1, sticky="w", padx=10, pady=5)
        row += 1
        
        # Rohrtyp
        ttk.Label(parent, text="Rohrtyp:").grid(row=row, column=0, sticky="w", padx=10, pady=5)
        self.pipe_type_var = tk.StringVar()
        self.pipe_type_combo = ttk.Combobox(parent, textvariable=self.pipe_type_var,
                                            state="readonly", width=30)
        self.pipe_type_combo.grid(row=row, column=1, sticky="w", padx=10, pady=5)
        self.pipe_type_combo.bind("<<ComboboxSelected>>", self._on_pipe_selected)
        row += 1
        
        self._add_entry(parent, row, "Rohr Außendurchmesser [mm]:", "pipe_outer_diameter", "32", self.entries, "pipe_outer_diameter")
        row += 1
        self._add_entry(parent, row, "Rohr Wandstärke [mm]:", "pipe_thickness", "3", self.entries, "pipe_wall_thickness")
        row += 1
        self._add_entry(parent, row, "Rohr Wärmeleitfähigkeit [W/m·K]:", "pipe_thermal_cond", "0.42", self.entries)
        row += 1
        self._add_entry(parent, row, "Schenkelabstand [mm]:", "shank_spacing", "65", self.entries, "shank_spacing")
        row += 1
        
        # Max. Sondenlänge (wird nur bei VDI 4640 verwendet)
        ttk.Label(parent, text="Max. Sondenlänge pro Bohrung [m]:", foreground="gray").grid(
            row=row, column=0, sticky="w", padx=10, pady=5)
        entry = ttk.Entry(parent, width=32)
        entry.insert(0, "100")
        entry.grid(row=row, column=1, sticky="w", padx=10, pady=5)
        self.entries["max_depth_per_borehole"] = entry
        row += 1
        
        # Info-Label
        info_label = ttk.Label(parent, 
            text="(wird nur bei VDI 4640 Methode verwendet)", 
            foreground="gray", 
            font=("Arial", 8, "italic")
        )
        info_label.grid(row=row, column=1, sticky="w", padx=10, pady=(0, 5))
        row += 1
        
        return row
    
    def _add_grout_section(self, parent, row):
        """Verfüllmaterial-Sektion."""
        ttk.Label(parent, text="Material:").grid(row=row, column=0, sticky="w", padx=10, pady=5)
        self.grout_material_var = tk.StringVar()
        grout_combo = ttk.Combobox(parent, textvariable=self.grout_material_var,
                                   values=self.grout_db.get_all_names(),
                                   state="readonly", width=30)
        grout_combo.grid(row=row, column=1, sticky="w", padx=10, pady=5)
        grout_combo.bind("<<ComboboxSelected>>", self._on_grout_selected)
        grout_combo.current(1)  # Zement-Bentonit verbessert
        InfoButton.create_info_button(parent, row, 2, "grout_material")
        row += 1
        
        # Material-Info
        self.grout_info_label = ttk.Label(parent, text="", foreground="blue", wraplength=400)
        self.grout_info_label.grid(row=row, column=0, columnspan=2, sticky="w", padx=10, pady=2)
        row += 1
        
        self._add_entry(parent, row, "Wärmeleitfähigkeit Verfüllung [W/m·K]:", "grout_thermal_cond", "1.3", self.entries)
        row += 1
        
        # Button zur Mengenberechnung
        ttk.Button(parent, text="💧 Materialmengen berechnen", 
                  command=self._calculate_grout_materials).grid(
            row=row, column=0, columnspan=2, pady=5, padx=10)
        row += 1
        
        # Trigger initial selection
        self._on_grout_selected(None)
        return row
    
    def _add_fluid_hydraulics_section(self, parent, row):
        """Fluid und Hydraulik-Sektion."""
        # Fluid-Auswahl
        ttk.Label(parent, text="Wärmeträgerfluid:").grid(row=row, column=0, sticky="w", padx=10, pady=5)
        self.fluid_var = tk.StringVar()
        fluid_combo = ttk.Combobox(parent, textvariable=self.fluid_var,
                                   values=self.fluid_db.get_all_names(),
                                   state="readonly", width=30)
        fluid_combo.grid(row=row, column=1, sticky="w", padx=10, pady=5)
        fluid_combo.bind("<<ComboboxSelected>>", self._on_fluid_selected)
        # Standard: Ethylenglykol 25%
        if "Ethylenglykol 25%" in self.fluid_db.get_all_names():
            fluid_combo.current(self.fluid_db.get_all_names().index("Ethylenglykol 25%"))
        InfoButton.create_info_button(parent, row, 2, "fluid_selection")
        row += 1
        
        # Temperatur für Fluid-Eigenschaften
        temp_entry = ttk.Entry(parent, width=32)
        temp_entry.insert(0, "5.0")
        temp_entry.grid(row=row, column=1, sticky="w", padx=10, pady=5)
        self.entries["fluid_temperature"] = temp_entry
        ttk.Label(parent, text="Betriebstemperatur [°C]:").grid(row=row, column=0, sticky="w", padx=10, pady=5)
        InfoButton.create_info_button(parent, row, 2, "fluid_temperature")
        temp_entry.bind("<KeyRelease>", lambda e: self._on_fluid_temperature_changed())
        row += 1
        
        self._add_entry(parent, row, "Anzahl Solekreise:", "num_circuits", "1", self.hydraulics_entries)
        row += 1
        
        # Volumenstrom (immer editierbar, wird automatisch berechnet) - jetzt in m³/h
        self._add_entry(parent, row, "Volumenstrom [m³/h]:", "fluid_flow_rate", "1.8", self.entries, "fluid_flow_rate")
        row += 1
        self._add_entry(parent, row, "Wärmeleitfähigkeit [W/m·K]:", "fluid_thermal_cond", "0.48", self.entries, "fluid_thermal_cond")
        row += 1
        self._add_entry(parent, row, "Wärmekapazität [J/kg·K]:", "fluid_heat_cap", "3800", self.entries)
        row += 1
        self._add_entry(parent, row, "Dichte [kg/m³]:", "fluid_density", "1030", self.entries)
        row += 1
        self._add_entry(parent, row, "Viskosität [Pa·s]:", "fluid_viscosity", "0.004", self.entries)
        row += 1
        
        # Fluid-Info-Label
        self.fluid_info_label = ttk.Label(parent, text="", foreground="blue", wraplength=400)
        self.fluid_info_label.grid(row=row, column=0, columnspan=2, sticky="w", padx=10, pady=2)
        row += 1
        
        # Hydraulik-Button
        ttk.Button(parent, text="💨 Hydraulik berechnen", 
                  command=self._calculate_hydraulics).grid(
            row=row, column=0, columnspan=2, pady=5, padx=10)
        row += 1
        
        # Trigger initial selection
        self._on_fluid_selected(None)
        return row
    
    def _add_heat_pump_section(self, parent, row):
        """Wärmepumpen-Sektion."""
        heat_power_entry = ttk.Entry(parent, width=32)
        heat_power_entry.insert(0, "6.0")
        heat_power_entry.grid(row=row, column=1, sticky="w", padx=10, pady=5)
        self.heat_pump_entries["heat_pump_power"] = heat_power_entry
        ttk.Label(parent, text="Wärmepumpenleistung [kW]:").grid(row=row, column=0, sticky="w", padx=10, pady=5)
        InfoButton.create_info_button(parent, row, 2, "heat_pump_power")
        heat_power_entry.bind("<KeyRelease>", lambda e: self._on_parameter_changed())
        row += 1
        row += 1
        self._add_entry(parent, row, "COP Heizen (Coefficient of Performance):", "heat_pump_cop", "4.0", self.entries, "cop")
        row += 1
        self._add_entry(parent, row, "EER Kühlen (Energy Efficiency Ratio):", "heat_pump_eer", "4.0", self.entries, "heat_pump_eer")
        row += 1
        
        # Kälteleistung wird automatisch berechnet
        ttk.Label(parent, text="Kälteleistung [kW]:", foreground="gray").grid(
            row=row, column=0, sticky="w", padx=10, pady=5)
        self.cold_power_label = ttk.Label(parent, text="(wird berechnet)", foreground="gray")
        self.cold_power_label.grid(row=row, column=1, sticky="w", padx=10, pady=5)
        row += 1
        
        self._add_entry(parent, row, "Warmwasser (Anzahl Personen):", "num_persons_dhw", "4", self.heat_pump_entries)
        row += 1
        
        self._add_entry(parent, row, "Jahres-Heizenergie [kWh]:", "annual_heating", "12000.0", self.entries, "annual_heating")
        row += 1
        self._add_entry(parent, row, "Jahres-Kühlenergie [kWh]:", "annual_cooling", "0.0", self.entries, "annual_cooling")
        row += 1
        self._add_entry(parent, row, "Heiz-Spitzenlast [kW]:", "peak_heating", "6.0", self.entries, "peak_heating")
        row += 1
        self._add_entry(parent, row, "Kühl-Spitzenlast [kW]:", "peak_cooling", "0.0", self.entries, "peak_cooling")
        row += 1
        
        self._add_entry(parent, row, "Min. Fluidtemperatur [°C]:", "min_fluid_temp", "-2.0", self.entries)
        row += 1
        self._add_entry(parent, row, "Max. Fluidtemperatur [°C]:", "max_fluid_temp", "15.0", self.entries)
        row += 1
        delta_t_entry = ttk.Entry(parent, width=32)
        delta_t_entry.insert(0, "3.0")
        delta_t_entry.grid(row=row, column=1, sticky="w", padx=10, pady=5)
        self.entries["delta_t_fluid"] = delta_t_entry
        ttk.Label(parent, text="Temperaturdifferenz Fluid [K]:").grid(row=row, column=0, sticky="w", padx=10, pady=5)
        delta_t_entry.bind("<KeyRelease>", lambda e: self._on_parameter_changed())
        row += 1
        row += 1
        return row
    
    def _add_simulation_section(self, parent, row):
        """Simulations-Sektion."""
        self._add_entry(parent, row, "Simulationsdauer [Jahre]:", "simulation_years", "25", self.entries)
        row += 1
        self._add_entry(parent, row, "Startwert Bohrtiefe [m]:", "initial_depth", "100", self.entries)
        row += 1
        
        # === BERECHNUNGSMETHODE ===
        ttk.Separator(parent, orient="horizontal").grid(
            row=row, column=0, columnspan=2, sticky="ew", padx=10, pady=10
        )
        row += 1
        
        ttk.Label(parent, text="Berechnungsmethode:", font=("Arial", 10, "bold")).grid(
            row=row, column=0, sticky="w", padx=10, pady=5
        )
        row += 1
        
        self.calculation_method_var = tk.StringVar(value="iterativ")
        
        method_frame = ttk.Frame(parent)
        method_frame.grid(row=row, column=0, columnspan=2, sticky="w", padx=20, pady=5)
        
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
        
        # Info-Text
        info_text = ttk.Label(
            parent, 
            text="VDI 4640: Berücksichtigt Heiz- und Kühllast getrennt, erkennt dominante Last automatisch.",
            foreground="gray",
            font=("Arial", 8, "italic"),
            wraplength=500
        )
        info_text.grid(row=row, column=0, columnspan=2, sticky="w", padx=20, pady=(0, 5))
        row += 1
        
        return row
    
    def _add_action_buttons(self, parent, row):
        """Action-Buttons."""
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=row, column=0, columnspan=2, pady=20, padx=10)
        
        ttk.Button(button_frame, text="🚀 Berechnung starten", 
                  command=self._run_calculation, width=25).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="📄 PDF-Bericht erstellen", 
                  command=self._export_pdf, width=25).pack(side=tk.LEFT, padx=5)
    
    def _add_entry(self, parent, row, label, key, default, dict_target, info_key=None):
        """Fügt ein Eingabefeld hinzu, optional mit Info-Button."""
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=10, pady=5)
        entry = ttk.Entry(parent, width=32)
        entry.insert(0, default)
        entry.grid(row=row, column=1, sticky="w", padx=10, pady=5)
        dict_target[key] = entry
        
        # Optional: Info-Button
        if info_key:
            InfoButton.create_info_button(parent, row, 2, info_key)
        
        # Spezialbehandlung für Anzahl Bohrungen: Event-Handler für automatische Solekreise
        if key == "num_boreholes":
            entry.bind("<KeyRelease>", self._on_borehole_count_changed)
    
    def _create_results_tab(self):
        """Erstellt den Ergebnisse-Tab."""
        # Container für volle Breite
        container = ttk.Frame(self.results_frame)
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Text-Frame für Ergebnisse (volle Breite)
        text_frame = ttk.LabelFrame(container, text="📊 Berechnungsergebnisse", padding=5)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.results_text = tk.Text(text_frame, wrap=tk.WORD, font=("Courier", 10),
                                    yscrollcommand=scrollbar.set)
        self.results_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.results_text.yview)
        
        self.results_text.insert("1.0", "Keine Berechnung durchgeführt.\n\nBitte Parameter eingeben und Berechnung starten.")
        self.results_text.config(state=tk.DISABLED)
    
    def _create_materials_tab(self):
        """Erstellt den Material & Hydraulik Tab."""
        # Scrollbarer Container
        canvas = tk.Canvas(self.materials_frame)
        scrollbar = ttk.Scrollbar(self.materials_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Materialmengen-Anzeige
        ttk.Label(scrollable_frame, text="💧 Verfüllmaterial-Berechnung", 
                 font=("Arial", 14, "bold"), foreground="#1f4788").pack(pady=10)
        
        # Scrollbares Text-Widget für Materialmengen
        grout_frame = ttk.Frame(scrollable_frame)
        grout_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        grout_scrollbar = ttk.Scrollbar(grout_frame)
        grout_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.grout_result_text = tk.Text(grout_frame, height=20, font=("Courier", 10),
                                         wrap=tk.WORD, yscrollcommand=grout_scrollbar.set)
        self.grout_result_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        grout_scrollbar.config(command=self.grout_result_text.yview)
        self.grout_result_text.insert("1.0", "Noch keine Berechnung durchgeführt.\n\nKlicken Sie auf 'Materialmengen berechnen'.")
        
        # Hydraulik-Anzeige
        ttk.Label(scrollable_frame, text="💨 Hydraulik-Berechnung", 
                 font=("Arial", 14, "bold"), foreground="#1f4788").pack(pady=10)
        
        # Layout untereinander: Ergebnisse → Buttons → Analysen (alle volle Breite)
        hydraulics_container = ttk.Frame(scrollable_frame)
        hydraulics_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 1. Hauptergebnisse (oben, volle Breite)
        results_frame = ttk.LabelFrame(hydraulics_container, text="📊 Hydraulik-Ergebnisse", padding=5)
        results_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        hydraulics_text_frame = ttk.Frame(results_frame)
        hydraulics_text_frame.pack(fill=tk.BOTH, expand=True)
        
        hydraulics_scrollbar = ttk.Scrollbar(hydraulics_text_frame)
        hydraulics_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.hydraulics_result_text = tk.Text(hydraulics_text_frame, height=15, font=("Courier", 9),
                                             wrap=tk.WORD, yscrollcommand=hydraulics_scrollbar.set)
        self.hydraulics_result_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        hydraulics_scrollbar.config(command=self.hydraulics_result_text.yview)
        self.hydraulics_result_text.insert("1.0", "Noch keine Berechnung durchgeführt.\n\nKlicken Sie auf 'Hydraulik berechnen'.")
        
        # 2. Buttons für Assistenten (mitte, volle Breite)
        button_container = ttk.Frame(hydraulics_container)
        button_container.pack(fill=tk.X, pady=5)
        
        ttk.Button(button_container, text="🔧 Pumpenauswahl-Assistent", 
                  command=self._show_pump_selection, width=35).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_container, text="⚡ Durchfluss-Optimierung", 
                  command=self._show_flow_optimizer, width=35).pack(side=tk.LEFT, padx=5)
        
        # 3. Schnellanalyse-Tabs (unten, volle Breite, volle Höhe)
        analysis_frame = ttk.LabelFrame(hydraulics_container, text="📈 Detailanalysen", padding=5)
        analysis_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        # Notebook für verschiedene Analysen
        self.analysis_notebook = ttk.Notebook(analysis_frame)
        self.analysis_notebook.pack(fill=tk.BOTH, expand=True)
        
        # Tab 1: Energieprognose
        energy_tab = ttk.Frame(self.analysis_notebook)
        self.analysis_notebook.add(energy_tab, text="💰 Energie")
        
        self.energy_analysis_text = tk.Text(energy_tab, font=("Courier", 9), wrap=tk.WORD)
        energy_scrollbar = ttk.Scrollbar(energy_tab, command=self.energy_analysis_text.yview)
        self.energy_analysis_text.config(yscrollcommand=energy_scrollbar.set)
        self.energy_analysis_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        energy_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.energy_analysis_text.insert("1.0", "Energieprognose wird nach\nHydraulik-Berechnung angezeigt.")
        
        # Tab 2: Druckverlust-Details
        pressure_tab = ttk.Frame(self.analysis_notebook)
        self.analysis_notebook.add(pressure_tab, text="🔍 Druckverlust")
        
        self.pressure_analysis_text = tk.Text(pressure_tab, font=("Courier", 9), wrap=tk.WORD)
        pressure_scrollbar = ttk.Scrollbar(pressure_tab, command=self.pressure_analysis_text.yview)
        self.pressure_analysis_text.config(yscrollcommand=pressure_scrollbar.set)
        self.pressure_analysis_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        pressure_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.pressure_analysis_text.insert("1.0", "Druckverlust-Details werden nach\nHydraulik-Berechnung angezeigt.")
        
        # Tab 3: Pumpenauswahl
        pump_tab = ttk.Frame(self.analysis_notebook)
        self.analysis_notebook.add(pump_tab, text="🔧 Pumpen")
        
        self.pump_analysis_text = tk.Text(pump_tab, font=("Courier", 9), wrap=tk.WORD)
        pump_scrollbar = ttk.Scrollbar(pump_tab, command=self.pump_analysis_text.yview)
        self.pump_analysis_text.config(yscrollcommand=pump_scrollbar.set)
        self.pump_analysis_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        pump_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.pump_analysis_text.insert("1.0", "Pumpen-Empfehlungen werden nach\nHydraulik-Berechnung angezeigt.")
    
    def _create_visualization_tab(self):
        """Erstellt den Visualisierungs-Tab."""
        self.fig = Figure(figsize=(18, 6))  # Breiter für 3 Subplots
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.viz_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    def _create_static_borehole_graphic(self, parent):
        """Erstellt eine statische Erklärungsgrafik einer Erdsonde mit 4 Leitungen."""
        # Titel
        title_label = ttk.Label(parent, text="📐 Erdsonden-Aufbau", 
                               font=("Arial", 14, "bold"))
        title_label.pack(pady=(10, 5))
        
        # Erstelle Figure für statische Grafik
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        from matplotlib.patches import Circle, Rectangle, FancyArrow
        
        fig = Figure(figsize=(5.5, 8), facecolor='white')
        ax = fig.add_subplot(111)
        
        # === SEITLICHE ANSICHT (Schnitt durch Sonde) ===
        # Boden (braun)
        ground = Rectangle((0, 0), 10, 15, facecolor='#8B4513', alpha=0.3, label='Boden')
        ax.add_patch(ground)
        
        # Bohrloch (hellgrau) - EIN Bohrloch mit 4 Leitungen ENGER zusammen
        borehole_width = 1.0
        borehole_center = 5.0
        borehole = Rectangle((borehole_center - borehole_width/2, 0), borehole_width, 15, 
                            facecolor='#d9d9d9', edgecolor='black', linewidth=2)
        ax.add_patch(borehole)
        
        # 4 Leitungen ENGER zusammen (alle im gleichen Bohrloch)
        # Abstand zwischen Rohren: nur 0.2 Einheiten
        spacing = 0.2
        center_offset = spacing * 1.5  # Gesamtbreite der 4 Rohre
        
        # Rohr 1 & 2 (links im Bohrloch)
        ax.plot([borehole_center - center_offset, borehole_center - center_offset], [0, 15], 
               color='#ff6b6b', linewidth=5, solid_capstyle='round')
        ax.plot([borehole_center - center_offset + spacing, borehole_center - center_offset + spacing], [0, 15], 
               color='#4ecdc4', linewidth=5, solid_capstyle='round')
        
        # Rohr 3 & 4 (rechts im Bohrloch)
        ax.plot([borehole_center + center_offset - spacing, borehole_center + center_offset - spacing], [0, 15], 
               color='#ff6b6b', linewidth=5, solid_capstyle='round')
        ax.plot([borehole_center + center_offset, borehole_center + center_offset], [0, 15], 
               color='#4ecdc4', linewidth=5, solid_capstyle='round')
        
        # U-Bogen unten (verbindet Rohr 1-2 und 3-4)
        from matplotlib.patches import Arc
        arc1 = Arc((borehole_center - center_offset + spacing/2, 0.3), spacing*1.5, 0.4, 
                  angle=0, theta1=180, theta2=360, color='black', linewidth=2)
        arc2 = Arc((borehole_center + center_offset - spacing/2, 0.3), spacing*1.5, 0.4, 
                  angle=0, theta1=180, theta2=360, color='black', linewidth=2)
        ax.add_patch(arc1)
        ax.add_patch(arc2)
        
        # === BESCHRIFTUNGEN ===
        # Durchmesser
        bh_left = borehole_center - borehole_width/2
        bh_right = borehole_center + borehole_width/2
        ax.annotate('', xy=(bh_left, 16), xytext=(bh_right, 16),
                   arrowprops=dict(arrowstyle='<->', color='black', lw=2))
        ax.text(borehole_center, 16.6, 'Bohrloch Ø 152mm', ha='center', fontsize=11, 
               fontweight='bold', bbox=dict(boxstyle='round,pad=0.5', 
               facecolor='yellow', edgecolor='black'))
        
        # Tiefe
        ax.annotate('', xy=(0.5, 0), xytext=(0.5, 15),
                   arrowprops=dict(arrowstyle='<->', color='#2196f3', lw=2))
        ax.text(-0.3, 7.5, 'Tiefe\nbis 100m', ha='center', fontsize=10, 
               fontweight='bold', color='#1976d2', rotation=90,
               bbox=dict(boxstyle='round,pad=0.4', facecolor='white', edgecolor='#2196f3'))
        
        # Nummern entfernt - sind nur im Querschnitt sichtbar
        
        # Verfüllung
        ax.text(borehole_center, 10, 'Verfüllung\n(Zement-Bentonit)', ha='center', fontsize=9,
               bbox=dict(boxstyle='round,pad=0.4', facecolor='#e0e0e0', edgecolor='black'))
        
        # Rohrmaterial
        ax.text(7.5, 12, 'PE 100 RC\nØ 32mm', ha='left', fontsize=9,
               bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='black'))
        ax.annotate('', xy=(bh_right + 0.1, 12), xytext=(7.3, 12),
                   arrowprops=dict(arrowstyle='->', color='black', lw=1.5))
        
        # === QUERSCHNITT (größer, ohne Text - nur Nummern) ===
        ax_inset = fig.add_axes([0.58, 0.52, 0.38, 0.42])  # Größer: breiter und höher
        
        # Bohrloch-Kreis
        bh_circle = Circle((0, 0), 1, facecolor='#d9d9d9', edgecolor='black', linewidth=2.5)
        ax_inset.add_patch(bh_circle)
        
        # 4 Rohre in QUADRAT-Anordnung
        # Links-oben, Rechts-oben, Links-unten, Rechts-unten
        positions = [(-0.35, 0.35), (0.35, 0.35), (-0.35, -0.35), (0.35, -0.35)]
        colors = ['#ff6b6b', '#4ecdc4', '#ff6b6b', '#4ecdc4']
        
        for i, ((x, y), color) in enumerate(zip(positions, colors)):
            pipe_circle = Circle((x, y), 0.2, facecolor=color, edgecolor='black', linewidth=1.5)
            ax_inset.add_patch(pipe_circle)
            ax_inset.text(x, y, str(i+1), ha='center', va='center', 
                         fontsize=11, fontweight='bold', color='white')
        
        ax_inset.set_xlim(-1.1, 1.1)
        ax_inset.set_ylim(-1.1, 1.1)
        ax_inset.set_aspect('equal')
        ax_inset.axis('off')
        
        # Hauptgrafik-Einstellungen (angepasst für enge Sonde)
        ax.set_xlim(0, 9)
        ax.set_ylim(-1, 18)
        ax.set_aspect('equal')
        ax.axis('off')
        
        fig.tight_layout()
        
        # Canvas in Frame einbetten
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Erklärungstext
        info_text = ttk.Label(parent, text=
            "4-Rohr-System (Double-U)\n" +
            "• 2× Vorlauf (rot)\n" +
            "• 2× Rücklauf (blau)\n" +
            "• Geschlossenes System\n" +
            "• Sole zirkuliert kontinuierlich",
            font=("Arial", 9), justify=tk.LEFT, foreground='#424242')
        info_text.pack(pady=(0, 10))
    
    def _create_status_bar(self):
        """Erstellt die Statusleiste."""
        self.status_var = tk.StringVar(value="Bereit - Professional Edition V3.0")
        status_bar = ttk.Label(self.root, textvariable=self.status_var,
                              relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    # =========== EVENT HANDLER ===========
    
    def _on_soil_selected(self, event):
        """Wenn ein Bodentyp ausgewählt wird."""
        soil_name = self.soil_type_var.get()
        soil = self.soil_db.get_soil_type(soil_name)
        
        if soil:
            # Update Werte
            self.entries["ground_thermal_cond"].delete(0, tk.END)
            self.entries["ground_thermal_cond"].insert(0, str(soil.thermal_conductivity_typical))
            
            self.entries["ground_heat_cap"].delete(0, tk.END)
            self.entries["ground_heat_cap"].insert(0, str(soil.heat_capacity_typical * 1e6))
            
            # Info anzeigen
            info = f"{soil.description}\nλ: {soil.thermal_conductivity_min}-{soil.thermal_conductivity_max} W/m·K (typ: {soil.thermal_conductivity_typical})\nWärmeentzug: {soil.heat_extraction_rate_min}-{soil.heat_extraction_rate_max} W/m"
            self.soil_info_label.config(text=info)
    
    def _on_fluid_selected(self, event):
        """Wenn ein Fluid ausgewählt wird."""
        self._update_fluid_properties()
    
    def _on_parameter_changed(self):
        """Wird aufgerufen, wenn sich Parameter ändern, die den Volumenstrom beeinflussen."""
        # Automatische Neuberechnung
        try:
            self._calculate_hydraulics()
        except:
            pass  # Fehler ignorieren, wenn noch nicht alle Parameter gesetzt sind
    
    def _on_fluid_temperature_changed(self):
        """Wenn die Betriebstemperatur geändert wird."""
        self._update_fluid_properties()
    
    def _update_fluid_properties(self):
        """Aktualisiert die Fluid-Eigenschaften basierend auf Auswahl und Temperatur."""
        if not hasattr(self, 'fluid_var') or not self.fluid_var.get():
            return
        
        fluid_name = self.fluid_var.get()
        fluid = self.fluid_db.get_fluid(fluid_name)
        
        if fluid:
            # Hole Betriebstemperatur
            try:
                temp_entry = self.entries.get("fluid_temperature")
                if temp_entry:
                    temp = float(temp_entry.get() or "5.0")
                else:
                    temp = 5.0
            except (ValueError, AttributeError):
                temp = 5.0
            
            # Hole Eigenschaften bei Betriebstemperatur
            props = fluid.get_properties_at_temp(temp)
            
            # Update Werte
            if "fluid_thermal_cond" in self.entries:
                self.entries["fluid_thermal_cond"].delete(0, tk.END)
                self.entries["fluid_thermal_cond"].insert(0, f"{props['thermal_conductivity']:.3f}")
            
            if "fluid_heat_cap" in self.entries:
                self.entries["fluid_heat_cap"].delete(0, tk.END)
                self.entries["fluid_heat_cap"].insert(0, f"{props['heat_capacity']:.1f}")
            
            if "fluid_density" in self.entries:
                self.entries["fluid_density"].delete(0, tk.END)
                self.entries["fluid_density"].insert(0, f"{props['density']:.1f}")
            
            if "fluid_viscosity" in self.entries:
                self.entries["fluid_viscosity"].delete(0, tk.END)
                self.entries["fluid_viscosity"].insert(0, f"{props['viscosity']:.6f}")
            
            # Info anzeigen
            info = f"{fluid.name}\nFrostschutz: {fluid.min_temp:.1f}°C\nBetriebstemp: {temp:.1f}°C\nKonzentration: {fluid.concentration_percent:.0f}%"
            if hasattr(self, 'fluid_info_label'):
                self.fluid_info_label.config(text=info)
    
    def _on_grout_selected(self, event):
        """Wenn ein Verfüllmaterial ausgewählt wird."""
        material_name = self.grout_material_var.get()
        material = self.grout_db.get_material(material_name)
        
        if material:
            # Update Wert
            self.entries["grout_thermal_cond"].delete(0, tk.END)
            self.entries["grout_thermal_cond"].insert(0, str(material.thermal_conductivity))
            
            # Info anzeigen
            info = f"{material.description}\nλ: {material.thermal_conductivity} W/m·K, ρ: {material.density} kg/m³, Preis: {material.price_per_kg} EUR/kg\n{material.typical_application}"
            self.grout_info_label.config(text=info)
    
    def _on_pipe_selected(self, event):
        """Wenn ein Rohrtyp ausgewählt wird."""
        if not self.pipes:
            return
        
        selected_name = self.pipe_type_var.get()
        for pipe in self.pipes:
            if pipe.name == selected_name:
                # Konvertiere m → mm für Anzeige
                self.entries["pipe_outer_diameter"].delete(0, tk.END)
                self.entries["pipe_outer_diameter"].insert(0, f"{pipe.diameter_m * 1000:.1f}")
                
                self.entries["pipe_thickness"].delete(0, tk.END)
                self.entries["pipe_thickness"].insert(0, f"{pipe.thickness_m * 1000:.1f}")
                
                self.entries["pipe_thermal_cond"].delete(0, tk.END)
                self.entries["pipe_thermal_cond"].insert(0, str(pipe.thermal_conductivity))
                break
    
    def _on_climate_fallback_selected(self, event):
        """Wenn Fallback-Klimadaten ausgewählt werden."""
        region = self.climate_fallback_var.get()
        data = FALLBACK_CLIMATE_DATA.get(region)
        
        if data:
            self.climate_entries["avg_air_temp"].delete(0, tk.END)
            self.climate_entries["avg_air_temp"].insert(0, str(data['yearly_avg_temp']))
            
            self.climate_entries["coldest_month_temp"].delete(0, tk.END)
            self.climate_entries["coldest_month_temp"].insert(0, str(data['coldest_month_temp']))
            
            self.status_var.set(f"✓ Klimadaten geladen: {region}")
    
    # =========== BERECHNUNGEN ===========
    
    def _calculate_grout_materials(self):
        """Berechnet Verfüllmaterial-Mengen."""
        try:
            # Hole Parameter
            depth = float(self.entries["initial_depth"].get())
            bh_diameter = float(self.entries["borehole_diameter"].get()) / 1000.0  # mm → m
            pipe_diameter = float(self.entries["pipe_outer_diameter"].get()) / 1000.0  # mm → m
            num_boreholes = int(self.borehole_entries["num_boreholes"].get())
            
            # Anzahl Rohre basierend auf Konfiguration
            config = self.pipe_config_var.get()
            if "4-rohr" in config or "double" in config:
                num_pipes = 4
            else:
                num_pipes = 2
            
            # Volumen berechnen
            volume_per_bh = self.grout_db.calculate_volume(depth, bh_diameter, pipe_diameter, num_pipes)
            total_volume = volume_per_bh * num_boreholes
            
            # Material-Eigenschaften
            material_name = self.grout_material_var.get()
            material = self.grout_db.get_material(material_name)
            
            # Mengen berechnen
            amounts = self.grout_db.calculate_material_amount(total_volume, material)
            
            # Speichern
            self.grout_calculation = {
                'material': material,
                'amounts': amounts,
                'num_boreholes': num_boreholes,
                'volume_per_bh': volume_per_bh
            }
            
            # Anzeigen
            text = "=" * 60 + "\n"
            text += "VERFÜLLMATERIAL-BERECHNUNG\n"
            text += "=" * 60 + "\n\n"
            text += f"Material: {material.name}\n"
            text += f"  λ = {material.thermal_conductivity} W/m·K\n"
            text += f"  ρ = {material.density} kg/m³\n"
            text += f"  Preis: {material.price_per_kg} EUR/kg\n\n"
            text += f"Konfiguration:\n"
            text += f"  Anzahl Bohrungen: {num_boreholes}\n"
            text += f"  Tiefe pro Bohrung: {depth} m\n"
            text += f"  Bohrloch-Ø: {bh_diameter*1000:.0f} mm\n"
            text += f"  Rohre: {num_pipes} × Ø {pipe_diameter*1000:.0f} mm\n\n"
            text += f"Benötigte Mengen:\n"
            text += f"  Volumen pro Bohrung: {volume_per_bh:.3f} m³ ({volume_per_bh*1000:.1f} Liter)\n"
            text += f"  Volumen gesamt: {total_volume:.3f} m³ ({total_volume*1000:.1f} Liter)\n"
            text += f"  Masse gesamt: {amounts['mass_kg']:.1f} kg\n"
            text += f"  Säcke (25 kg): {amounts['bags_25kg']:.1f} Stück\n\n"
            text += f"Kosten:\n"
            text += f"  Gesamt: {amounts['total_cost_eur']:.2f} EUR\n"
            text += f"  Pro Meter: {amounts['cost_per_m']:.2f} EUR/m\n\n"
            text += "=" * 60 + "\n"
            
            self.grout_result_text.delete("1.0", tk.END)
            self.grout_result_text.insert("1.0", text)
            
            self.status_var.set(f"✓ Materialberechnung: {total_volume*1000:.0f} Liter ({amounts['bags_25kg']:.0f} Säcke), {amounts['total_cost_eur']:.2f} EUR")
            
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler bei Materialberechnung: {str(e)}")
    
    def _calculate_hydraulics(self):
        """Berechnet Hydraulik-Parameter."""
        try:
            # Hole Parameter
            heat_power = float(self.heat_pump_entries["heat_pump_power"].get())
            
            # Hole Frostschutzkonzentration aus Fluid-Datenbank
            if hasattr(self, 'fluid_var') and self.fluid_var.get():
                fluid_name = self.fluid_var.get()
                fluid = self.fluid_db.get_fluid(fluid_name)
                if fluid:
                    antifreeze_conc = fluid.concentration_percent
                else:
                    # Fallback: Versuche aus altem Eingabefeld
                    try:
                        antifreeze_conc = float(self.hydraulics_entries.get("antifreeze_concentration", ttk.Entry()).get() or "25")
                    except (AttributeError, ValueError, KeyError):
                        antifreeze_conc = 25.0  # Standard: 25%
            else:
                # Fallback: Versuche aus altem Eingabefeld
                try:
                    antifreeze_conc = float(self.hydraulics_entries.get("antifreeze_concentration", ttk.Entry()).get() or "25")
                except (AttributeError, ValueError, KeyError):
                    antifreeze_conc = 25.0  # Standard: 25%
            
            num_circuits = int(self.hydraulics_entries["num_circuits"].get())
            num_boreholes = int(self.borehole_entries["num_boreholes"].get())
            
            # Verwende tatsächliche berechnete Tiefe (aus VDI 4640), falls vorhanden
            if hasattr(self, 'vdi4640_result') and self.vdi4640_result and self.vdi4640_result.required_depth_final > 0:
                depth = self.vdi4640_result.required_depth_final
            else:
                depth = float(self.entries["initial_depth"].get())
            
            # Konvertiere mm → m für Innendurchmesser-Berechnung
            pipe_outer_d_m = float(self.entries["pipe_outer_diameter"].get()) / 1000.0
            pipe_thickness_m = float(self.entries["pipe_thickness"].get()) / 1000.0
            pipe_inner_d = pipe_outer_d_m - 2 * pipe_thickness_m
            
            # Hole COP für Kälteleistung
            cop = float(self.entries["heat_pump_cop"].get())
            
            # Berechne Entzugsleistung (Kälteleistung) aus dem Erdreich
            # Q_Entzug = Q_WP × (COP - 1) / COP
            extraction_power = heat_power * (cop - 1) / cop
            
            # Hole Temperaturdifferenz für Volumenstrom-Berechnung (BUG-FIX: nicht COP!)
            delta_t_fluid = float(self.entries.get("delta_t_fluid", ttk.Entry()).get() or "3.0")
            
            # Volumenstrom berechnen (KORREKT: delta_t_fluid statt COP)
            # Verwende Entzugsleistung für physikalisch korrekte Berechnung
            # Die Empfehlung 0.8-1.5 l/s/kW bezieht sich auf Wärmeleistung (mit Sicherheitsfaktor)
            flow = self.hydraulics_calc.calculate_required_flow_rate(
                extraction_power, delta_t_fluid, antifreeze_conc
            )
            
            # Automatische Übernahme des berechneten Volumenstroms (in m³/h)
            calculated_flow_m3h = flow['volume_flow_m3_h']
            flow_entry = self.entries.get("fluid_flow_rate")
            if flow_entry:
                flow_entry.delete(0, tk.END)
                flow_entry.insert(0, f"{calculated_flow_m3h:.3f}")
            
            # Warnung bei abweichenden Werten (wird später im Ergebnis-Text angezeigt)
            calculated_flow_m3s = flow['volume_flow_m3_s']
            flow_warnings = self._check_flow_rate_warnings(
                heat_power, calculated_flow_m3s, num_boreholes, 
                delta_t_fluid, antifreeze_conc, extraction_power
            )
            
            # Bestimme Anzahl Kreise pro Bohrung basierend auf Rohrkonfiguration
            pipe_config = self.pipe_config_var.get()
            if "4-rohr" in pipe_config.lower() or "double" in pipe_config.lower():
                circuits_per_borehole = 2  # 4-Rohr-Systeme haben 2 Kreise pro Bohrung
            else:
                circuits_per_borehole = 1  # Single-U hat 1 Kreis pro Bohrung
            
            # System-Druckverlust
            system = self.hydraulics_calc.calculate_total_system_pressure_drop(
                depth, num_boreholes, num_circuits, pipe_inner_d,
                flow['volume_flow_m3_h'], antifreeze_conc, circuits_per_borehole
            )
            
            # Pumpenleistung
            pump = self.hydraulics_calc.calculate_pump_power(
                flow['volume_flow_m3_h'], system['total_pressure_drop_bar']
            )
            
            # Kälteleistung berechnen (COP wurde bereits oben geholt)
            cold_power = heat_power * (cop - 1) / cop
            self.cold_power_label.config(text=f"{cold_power:.2f} kW", foreground="blue")
            
            # Speichern
            self.hydraulics_result = {
                'flow': flow,
                'system': system,
                'pump': pump,
                'cold_power': cold_power
            }
            
            # Anzeigen
            text = "=" * 60 + "\n"
            text += "HYDRAULIK-BERECHNUNG\n"
            text += "=" * 60 + "\n\n"
            text += f"Wärmeleistung: {heat_power} kW\n"
            text += f"COP: {cop}\n"
            text += f"Entzugsleistung (Kälteleistung): {extraction_power:.2f} kW\n"
            text += f"Frostschutz: {antifreeze_conc} Vol%\n"
            text += f"Anzahl System-Kreise: {num_circuits}\n"
            text += f"Anzahl Bohrungen: {num_boreholes}\n"
            text += f"Kreise pro Bohrung: {circuits_per_borehole}\n"
            text += f"Bohrtiefe: {depth:.1f} m\n"
            text += f"Bohrungen pro System-Kreis: {num_boreholes / num_circuits:.1f}\n"
            text += f"Rohrlänge pro System-Kreis: {system['pipe_length_per_circuit_m']:.1f} m\n\n"
            text += f"Volumenstrom:\n"
            text += f"  Gesamt: {flow['volume_flow_m3_h']:.3f} m³/h ({flow['volume_flow_l_min']:.1f} l/min)\n"
            text += f"  Pro Kreis: {system['volume_flow_per_circuit_m3h']:.3f} m³/h\n"
            text += f"  Geschwindigkeit: {system['velocity_m_s']:.2f} m/s\n"
            text += f"  Reynolds: {system['reynolds']:.0f}\n\n"
            text += f"Druckverlust:\n"
            text += f"  Bohrungen: {system['pressure_drop_borehole_bar']:.2f} bar\n"
            text += f"  Zusatzverluste: {system['additional_losses_bar']:.2f} bar\n"
            text += f"  GESAMT: {system['total_pressure_drop_bar']:.2f} bar ({system['total_pressure_drop_mbar']:.0f} mbar)\n\n"
            text += f"Pumpe:\n"
            text += f"  Hydraulische Leistung: {pump['hydraulic_power_w']:.0f} W\n"
            text += f"  Elektrische Leistung: {pump['electric_power_w']:.0f} W ({pump['electric_power_kw']:.2f} kW)\n\n"
            
            # Warnungen einfügen (falls vorhanden)
            if flow_warnings:
                text += flow_warnings + "\n\n"
            
            text += "=" * 60 + "\n"
            
            self.hydraulics_result_text.delete("1.0", tk.END)
            self.hydraulics_result_text.insert("1.0", text)
            
            # Aktiviere Durchfluss-Optimierung Button (v3.3.0)
            if hasattr(self, 'flow_optimizer_button'):
                self.flow_optimizer_button.config(state="normal")
            
            # Fülle Analyse-Tabs automatisch (v3.3.0-beta3)
            self._update_energy_analysis()
            self._update_pressure_analysis()
            self._update_pump_analysis()
            
            self.status_var.set(f"✓ Hydraulik: {flow['volume_flow_m3_h']:.2f} m³/h, {system['total_pressure_drop_mbar']:.0f} mbar, {pump['electric_power_w']:.0f} W")
            
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler bei Hydraulik-Berechnung: {str(e)}")
    
    def _update_energy_analysis(self):
        """Aktualisiert die Energieprognose im Analyse-Tab."""
        if not hasattr(self, 'hydraulics_result') or not self.hydraulics_result:
            return
        
        if not hasattr(self, 'energy_analysis_text'):
            return
        
        try:
            pump_power = self.hydraulics_result['pump']['electric_power_w']
            hours = 1800  # Standard-Betriebsstunden
            price = 0.30  # EUR/kWh
            
            energy = self.hydraulics_calc.calculate_pump_energy_consumption(
                pump_power, hours, price
            )
            
            text = "═══ ENERGIEVERBRAUCH-PROGNOSE ═══\n\n"
            text += f"Pumpenleistung: {pump_power:.0f} W\n"
            text += f"Betriebsstunden/Jahr: {hours} h\n"
            text += f"Strompreis: {price:.2f} EUR/kWh\n\n"
            text += "KONSTANTE PUMPE:\n"
            text += f"  Verbrauch: {energy['annual_kwh']:.1f} kWh/Jahr\n"
            text += f"  Kosten: {energy['annual_cost_eur']:.2f} EUR/Jahr\n\n"
            text += "GEREGELTE PUMPE (30% Einsparung):\n"
            regulated_kwh = energy['annual_kwh'] * 0.7
            regulated_cost = energy['annual_cost_eur'] * 0.7
            text += f"  Verbrauch: {regulated_kwh:.1f} kWh/Jahr\n"
            text += f"  Kosten: {regulated_cost:.2f} EUR/Jahr\n\n"
            text += "EINSPARUNG:\n"
            savings_kwh = energy['annual_kwh'] - regulated_kwh
            savings_eur = energy['annual_cost_eur'] - regulated_cost
            text += f"  {savings_kwh:.1f} kWh/Jahr\n"
            text += f"  {savings_eur:.2f} EUR/Jahr\n\n"
            text += "─────────────────────────────\n\n"
            text += "💡 Empfehlung: Geregelte Hocheffizienz-\n"
            text += "   Pumpe (Klasse A) verwenden!\n"
            
            self.energy_analysis_text.delete("1.0", tk.END)
            self.energy_analysis_text.insert("1.0", text)
        except Exception as e:
            if hasattr(self, 'energy_analysis_text'):
                self.energy_analysis_text.delete("1.0", tk.END)
                self.energy_analysis_text.insert("1.0", f"Fehler: {str(e)}")
    
    def _update_pressure_analysis(self):
        """Aktualisiert die Druckverlust-Analyse im Analyse-Tab."""
        if not hasattr(self, 'hydraulics_result') or not self.hydraulics_result:
            return
        
        if not hasattr(self, 'pressure_analysis_text'):
            return
        
        try:
            system = self.hydraulics_result.get('system', {})
            flow = self.hydraulics_result.get('flow', {})
            
            text = "═══ DRUCKVERLUST-ANALYSE ═══\n\n"
            text += f"Volumenstrom: {flow.get('volume_flow_m3_h', 0):.2f} m³/h\n"
            text += f"Geschwindigkeit: {system.get('velocity', 0):.2f} m/s\n"
            text += f"Reynolds: {system.get('reynolds', 0):.0f}\n\n"
            
            # Strömungsregime
            reynolds = system.get('reynolds', 0)
            if reynolds < 2300:
                text += "⚠️  LAMINAR (Re < 2300)\n"
                text += "    Risiko schlechter Wärmeübergang!\n"
            elif reynolds < 2500:
                text += "⚡ ÜBERGANGSBEREICH (Re 2300-2500)\n"
                text += "   Grenzbereich, knapp turbulent\n"
            else:
                text += "✅ TURBULENT (Re > 2500)\n"
                text += "   Guter Wärmeübergang\n"
            
            text += "\n─────────────────────────────\n\n"
            text += "DRUCKVERLUSTE:\n"
            text += f"  Total: {system.get('total_pressure_drop_bar', 0):.3f} bar\n"
            text += f"        ({system.get('total_pressure_drop_mbar', 0):.0f} mbar)\n"
            text += f"  Förderhöhe: {system.get('total_pressure_drop_bar', 0)*10.2:.1f} m\n\n"
            
            text += f"Rohrlänge/Kreis: {system.get('pipe_length_per_circuit_m', 0):.1f} m\n"
            text += f"Reibungsverlust: {system.get('friction_factor', 0):.4f}\n\n"
            
            text += "─────────────────────────────\n\n"
            text += "💡 Tipp: Für niedrigere Druckverluste\n"
            text += "   größeren Rohrdurchmesser wählen!\n"
            
            self.pressure_analysis_text.delete("1.0", tk.END)
            self.pressure_analysis_text.insert("1.0", text)
        except Exception as e:
            self.pressure_analysis_text.delete("1.0", tk.END)
            self.pressure_analysis_text.insert("1.0", f"Fehler: {str(e)}")
    
    def _update_pump_analysis(self):
        """Aktualisiert die Pumpen-Empfehlungen im Analyse-Tab."""
        if not hasattr(self, 'hydraulics_result') or not self.hydraulics_result:
            return
        
        if not hasattr(self, 'pump_analysis_text'):
            return
        
        try:
            from data.pump_db import PumpDatabase
            
            # Hole Hydraulik-Daten
            flow_m3h = self.hydraulics_result['flow']['volume_flow_m3_h']
            total_dp = self.hydraulics_result['system']['total_pressure_drop_bar']
            head_m = total_dp * 10.2
            power_kw = float(self.heat_pump_entries["heat_pump_power"].get() or "11")
            
            # Lade Pumpen-Datenbank
            pump_db = PumpDatabase()
            
            text = "═══ PUMPEN-EMPFEHLUNGEN ═══\n\n"
            text += f"Volumenstrom: {flow_m3h:.2f} m³/h\n"
            text += f"Förderhöhe: {head_m:.1f} m\n"
            text += f"Leistung WP: {power_kw:.0f} kW\n"
            text += f"Pumpen in DB: {len(pump_db.pumps)}\n\n"
            text += "─────────────────────────────\n\n"
            
            suitable_pumps = pump_db.find_suitable_pumps(
                flow_m3h=flow_m3h,
                head_m=head_m,
                power_kw=power_kw,
                max_results=5
            )
            
            if suitable_pumps:
                for i, (score, pump) in enumerate(suitable_pumps, 1):
                    if i == 1:
                        text += "🥇 "
                    elif i == 2:
                        text += "🥈 "
                    elif i == 3:
                        text += "🥉 "
                    else:
                        text += f"#{i} "
                    
                    text += f"{pump.get_full_name()}\n"
                    text += f"   Score: {score:.0f}/100\n"
                    text += f"   Typ: {'Geregelt' if pump.pump_type == 'regulated' else 'Konstant'}\n"
                    text += f"   Max: {pump.specs.max_flow_m3h} m³/h, {pump.specs.max_head_m} m\n"
                    text += f"   Leistung: {pump.specs.power_avg_w} W\n"
                    text += f"   Effizienz: {pump.efficiency_class}\n"
                    text += f"   Preis: {pump.price_eur:.0f} EUR\n\n"
            else:
                text += "⚠️ Keine passenden Pumpen gefunden.\n\n"
                text += "Mögliche Gründe:\n"
                text += f"• Volumenstrom zu hoch (> {flow_m3h/1.1:.1f} m³/h nötig)\n"
                text += f"• Förderhöhe zu hoch (> {head_m/1.1:.1f} m nötig)\n"
                text += "• Leistungsbereich passt nicht\n\n"
                text += "Prüfen Sie:\n"
                text += "- Anzahl Bohrungen erhöhen\n"
                text += "- ΔT erhöhen (weniger Volumenstrom)\n"
                text += "- Rohrdurchmesser vergrößern\n"
            
            text += "\n─────────────────────────────\n\n"
            text += "💡 Empfehlung: Geregelte Hocheffizienz-\n"
            text += "   Pumpe für beste Energieeffizienz!\n"
            
            self.pump_analysis_text.delete("1.0", tk.END)
            self.pump_analysis_text.insert("1.0", text)
        except Exception as e:
            self.pump_analysis_text.delete("1.0", tk.END)
            self.pump_analysis_text.insert("1.0", f"Fehler: {str(e)}\n\nPumpen-Datenbank konnte nicht\ngeladen werden.")
    
    def _on_borehole_count_changed(self, event=None):
        """Wird aufgerufen, wenn sich die Anzahl der Bohrungen ändert."""
        try:
            num_boreholes = int(self.borehole_entries["num_boreholes"].get() or "1")
            pipe_config = self.pipe_config_var.get()
            
            # Bei 4-Rohr-Systemen: Anzahl Kreise = Anzahl Bohrungen × 2
            # Bei Single-U: Anzahl Kreise = Anzahl Bohrungen
            if "4-rohr" in pipe_config.lower() or "double" in pipe_config.lower():
                suggested_circuits = num_boreholes * 2
            else:
                suggested_circuits = num_boreholes
            
            # Setze automatisch die Anzahl der Solekreise
            if "num_circuits" in self.hydraulics_entries:
                self.hydraulics_entries["num_circuits"].delete(0, tk.END)
                self.hydraulics_entries["num_circuits"].insert(0, str(suggested_circuits))
        except (ValueError, KeyError):
            pass  # Ignoriere Fehler bei leerem Feld oder fehlendem Eintrag
    
    def _show_energy_prognosis(self):
        """Zeigt Energieverbrauch-Prognose für Pumpe (v3.3.0-beta2)."""
        if not hasattr(self, 'hydraulics_result') or not self.hydraulics_result:
            messagebox.showinfo("Hinweis", "Bitte erst Hydraulik berechnen!")
            return
        
        try:
            pump_power = self.hydraulics_result['pump']['electric_power_w']
            
            # Erstelle Dialog
            dialog = tk.Toplevel(self.root)
            dialog.title("Energieverbrauch-Prognose")
            dialog.geometry("1200x800")
            
            # Haupt-Frame
            main_frame = ttk.Frame(dialog)
            main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
            
            # Titel
            title = ttk.Label(main_frame, text="💰 ENERGIEVERBRAUCH-PROGNOSE", 
                            font=("Arial", 14, "bold"))
            title.pack(pady=(0, 15))
            
            # Parameter-Frame
            param_frame = ttk.LabelFrame(main_frame, text="Parameter", padding=10)
            param_frame.pack(fill="x", pady=(0, 10))
            
            ttk.Label(param_frame, text="Betriebsstunden/Jahr:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
            hours_var = tk.StringVar(value="1800")
            hours_entry = ttk.Entry(param_frame, textvariable=hours_var, width=10)
            hours_entry.grid(row=0, column=1, sticky="w", padx=5, pady=5)
            ttk.Label(param_frame, text="h").grid(row=0, column=2, sticky="w")
            
            ttk.Label(param_frame, text="Strompreis:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
            price_var = tk.StringVar(value="0.30")
            price_entry = ttk.Entry(param_frame, textvariable=price_var, width=10)
            price_entry.grid(row=1, column=1, sticky="w", padx=5, pady=5)
            ttk.Label(param_frame, text="EUR/kWh").grid(row=1, column=2, sticky="w")
            
            # Ergebnis-Text
            result_frame = ttk.Frame(main_frame)
            result_frame.pack(fill=tk.BOTH, expand=True)
            
            scrollbar = ttk.Scrollbar(result_frame)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            result_text = tk.Text(result_frame, wrap=tk.WORD, yscrollcommand=scrollbar.set,
                                 font=("Courier", 10), height=25)
            result_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.config(command=result_text.yview)
            
            def update_calculation():
                try:
                    hours = float(hours_var.get())
                    price = float(price_var.get())
                    
                    # Berechne für konstante Pumpe
                    result_const = self.hydraulics_calc.calculate_pump_energy_consumption(
                        pump_power, hours, price, regulation_factor=1.0, 
                        pump_efficiency_curve="constant"
                    )
                    
                    # Berechne für geregelte Pumpe
                    result_reg = self.hydraulics_calc.calculate_pump_energy_consumption(
                        pump_power, hours, price, regulation_factor=0.55,
                        pump_efficiency_curve="regulated"
                    )
                    
                    # Formatiere Ausgabe
                    output = "=" * 70 + "\n"
                    output += "ENERGIEVERBRAUCH-PROGNOSE\n"
                    output += "=" * 70 + "\n\n"
                    
                    output += f"Pumpenleistung (Auslegung): {pump_power:.0f} W\n"
                    output += f"Betriebsstunden/Jahr: {hours:.0f} h\n"
                    output += f"Strompreis: {price:.2f} EUR/kWh\n\n"
                    
                    output += "=" * 70 + "\n"
                    output += "OPTION 1: KONSTANTE PUMPE (ungeregelter Betrieb)\n"
                    output += "=" * 70 + "\n\n"
                    
                    output += f"Durchschnittliche Leistung: {result_const['avg_power_w']:.0f} W\n"
                    output += f"(Läuft immer mit 100% Leistung)\n\n"
                    
                    output += "Jahresverbrauch:\n"
                    output += f"  • Energie: {result_const['annual_kwh']:.0f} kWh/Jahr\n"
                    output += f"  • Kosten: {result_const['annual_cost_eur']:.2f} EUR/Jahr\n\n"
                    
                    output += "10-Jahres-Bilanz:\n"
                    output += f"  • Energie: {result_const['lifetime_10y_kwh']:.0f} kWh\n"
                    output += f"  • Kosten: {result_const['lifetime_10y_cost_eur']:.2f} EUR\n\n"
                    
                    output += "=" * 70 + "\n"
                    output += "OPTION 2: GEREGELTE PUMPE (Hocheffizienz)\n"
                    output += "=" * 70 + "\n\n"
                    
                    output += f"Durchschnittliche Leistung: {result_reg['avg_power_w']:.0f} W\n"
                    output += f"(Läuft bei ~55% Durchschnitts-Leistung durch Regelung)\n\n"
                    
                    output += "Jahresverbrauch:\n"
                    output += f"  • Energie: {result_reg['annual_kwh']:.0f} kWh/Jahr\n"
                    output += f"  • Kosten: {result_reg['annual_cost_eur']:.2f} EUR/Jahr\n\n"
                    
                    output += "10-Jahres-Bilanz:\n"
                    output += f"  • Energie: {result_reg['lifetime_10y_kwh']:.0f} kWh\n"
                    output += f"  • Kosten: {result_reg['lifetime_10y_cost_eur']:.2f} EUR\n\n"
                    
                    # Mehrkosten
                    output += f"Mehrkosten geregelte Pumpe: ~{result_const['regulated']['extra_cost_eur']:.0f} EUR\n\n"
                    
                    output += "=" * 70 + "\n"
                    output += "💡 VERGLEICH & EMPFEHLUNG\n"
                    output += "=" * 70 + "\n\n"
                    
                    savings_annual = result_const['regulated']['savings_annual_eur']
                    savings_10y = result_const['regulated']['savings_10y_eur']
                    payback = result_const['regulated']['payback_years']
                    
                    output += f"Ersparnis pro Jahr: {savings_annual:.2f} EUR\n"
                    output += f"Ersparnis in 10 Jahren: {savings_10y:.2f} EUR\n"
                    output += f"Amortisation: {payback:.1f} Jahre\n\n"
                    
                    if payback < 5:
                        output += "✅ EMPFEHLUNG: Geregelte Pumpe lohnt sich!\n"
                        output += f"   Die Mehrkosten amortisieren sich in {payback:.1f} Jahren.\n"
                        output += f"   Über 10 Jahre sparen Sie {savings_10y:.2f} EUR.\n"
                    elif payback < 10:
                        output += "⚠️  EMPFEHLUNG: Geregelte Pumpe kann sich lohnen.\n"
                        output += f"   Die Mehrkosten amortisieren sich in {payback:.1f} Jahren.\n"
                    else:
                        output += "ℹ️  HINWEIS: Bei kurzer Laufzeit lohnt sich evtl. konstante Pumpe.\n"
                    
                    output += "\n" + "=" * 70 + "\n"
                    output += "⚡ ENERGIEEFFIZIENZ-KLASSEN\n"
                    output += "=" * 70 + "\n\n"
                    
                    output += "Hocheffizienz-Pumpen (z.B. Grundfos Alpha2, Wilo Stratos):\n"
                    output += "  • A++ Effizienz\n"
                    output += f"  • Sparen ~{(1-0.55)*100:.0f}% Energie\n"
                    output += "  • Automatische Lastanpassung\n"
                    output += "  • Typisch +150-250 EUR Mehrkosten\n\n"
                    
                    output += "Standard-Pumpen:\n"
                    output += "  • D-Klasse Effizienz\n"
                    output += "  • Konstante Leistung\n"
                    output += "  • Günstiger in der Anschaffung\n"
                    output += "  • Höhere Betriebskosten\n\n"
                    
                    output += "HINWEISE:\n"
                    output += "• Betriebsstunden abhängig von Heizlast und JAZ\n"
                    output += "• Strompreis-Entwicklung beachten\n"
                    output += "• Bei Neuanlagen: Geregelte Pumpen sind Stand der Technik\n"
                    
                    result_text.delete("1.0", tk.END)
                    result_text.insert("1.0", output)
                    result_text.config(state="disabled")
                    
                except Exception as e:
                    messagebox.showerror("Fehler", f"Fehler bei Berechnung:\n{str(e)}")
            
            # Initial berechnen
            update_calculation()
            
            # Button-Frame
            button_frame = ttk.Frame(main_frame)
            button_frame.pack(fill="x", pady=(10, 0))
            
            ttk.Button(button_frame, text="Neu berechnen", 
                      command=update_calculation).pack(side="left", padx=5)
            ttk.Button(button_frame, text="Schließen", 
                      command=dialog.destroy).pack(side="right", padx=5)
            
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler bei Energieverbrauch-Prognose:\n{str(e)}")
    
    def _show_detailed_pressure_analysis(self):
        """Zeigt detaillierte Druckverlust-Analyse (v3.3.0-beta1)."""
        if not hasattr(self, 'hydraulics_result') or not self.hydraulics_result:
            messagebox.showinfo("Hinweis", "Bitte erst Hydraulik berechnen!")
            return
        
        try:
            # Hole Parameter aus letzter Berechnung
            depth = float(self.borehole_entries["depth"].get())
            num_boreholes = int(self.borehole_entries["num_boreholes"].get())
            num_circuits = int(self.entries.get("num_circuits", ttk.Entry()).get() or str(num_boreholes))
            pipe_inner_d = float(self.entries.get("pipe_inner_d", ttk.Entry()).get() or "0.026")
            antifreeze_conc = float(self.antifreeze_var.get())
            volume_flow = self.hydraulics_result['flow']['volume_flow_m3_h']
            
            # Bestimme Kreise pro Bohrung
            pipe_config = self.pipe_config_var.get()
            if "4-rohr" in pipe_config.lower() or "double" in pipe_config.lower():
                circuits_per_borehole = 2
            else:
                circuits_per_borehole = 1
            
            # Berechne detaillierte Analyse
            analysis = self.hydraulics_calc.calculate_detailed_pressure_analysis(
                depth, num_boreholes, num_circuits, pipe_inner_d,
                volume_flow, antifreeze_conc,
                circuits_per_borehole=circuits_per_borehole
            )
            
            # Erstelle Dialog
            dialog = tk.Toplevel(self.root)
            dialog.title("Detaillierte Druckverlust-Analyse")
            dialog.geometry("1200x800")
            
            # Text-Widget mit Scrollbar
            frame = ttk.Frame(dialog)
            frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            scrollbar = ttk.Scrollbar(frame)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            text = tk.Text(frame, wrap=tk.WORD, yscrollcommand=scrollbar.set,
                          font=("Courier", 10))
            text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.config(command=text.yview)
            
            # Formatiere Ausgabe
            output = "=" * 70 + "\n"
            output += "DETAILLIERTE DRUCKVERLUST-ANALYSE\n"
            output += "=" * 70 + "\n\n"
            
            comp = analysis['components']
            
            output += "1. ERDWÄRMESONDEN (vertikal)\n"
            output += f"   • Rohrlänge: {comp['boreholes']['length_m']:.1f} m\n"
            output += f"   • Geschwindigkeit: {comp['boreholes']['velocity_m_s']:.2f} m/s\n"
            output += f"   • Reynolds: {comp['boreholes']['reynolds']:.0f} ({comp['boreholes']['flow_regime']})\n"
            output += f"   • ΔP: {comp['boreholes']['pressure_drop_bar']:.3f} bar\n"
            output += f"   • Anteil: {comp['boreholes']['percent']:.1f}%\n\n"
            
            output += "2. HORIZONTALE ANBINDUNG\n"
            output += f"   • Rohrlänge: {comp['horizontal']['length_m']:.1f} m (geschätzt)\n"
            output += f"   • Geschwindigkeit: {comp['horizontal']['velocity_m_s']:.2f} m/s\n"
            output += f"   • Reynolds: {comp['horizontal']['reynolds']:.0f}\n"
            output += f"   • ΔP: {comp['horizontal']['pressure_drop_bar']:.3f} bar\n"
            output += f"   • Anteil: {comp['horizontal']['percent']:.1f}%\n\n"
            
            output += "3. FORMSTÜCKE & VENTILE\n"
            for fitting_type, count in comp['fittings']['items'].items():
                output += f"   • {fitting_type}: {count}×\n"
            output += f"   • Gesamt-ζ: {comp['fittings']['total_zeta']:.2f}\n"
            output += f"   • ΔP: {comp['fittings']['pressure_drop_bar']:.3f} bar\n"
            output += f"   • Anteil: {comp['fittings']['percent']:.1f}%\n\n"
            
            output += "4. WÄRMETAUSCHER/FILTER\n"
            output += f"   • ΔP: {comp['heat_exchanger']['pressure_drop_bar']:.3f} bar (angenommen)\n"
            output += f"   • Anteil: {comp['heat_exchanger']['percent']:.1f}%\n\n"
            
            output += "=" * 70 + "\n"
            output += f"GESAMT: {analysis['total_pressure_drop_bar']:.3f} bar "
            output += f"({analysis['total_pressure_drop_mbar']:.0f} mbar)\n"
            output += "=" * 70 + "\n\n"
            
            if analysis['suggestions']:
                output += "💡 OPTIMIERUNGSVORSCHLÄGE:\n"
                for i, suggestion in enumerate(analysis['suggestions'], 1):
                    output += f"   {i}. {suggestion}\n"
                output += "\n"
            
            output += "HINWEIS:\n"
            output += "• Horizontale Länge ist geschätzt (50m standard)\n"
            output += "• Formstücke basieren auf typischer Installation\n"
            output += "• Wärmetauscher-Verlust ist pauschalisiert (0.05 bar)\n"
            output += "• Für präzise Werte: Anlagen-spezifische Daten eingeben\n"
            
            text.insert("1.0", output)
            text.config(state="disabled")
            
            # Schließen-Button
            ttk.Button(dialog, text="Schließen", command=dialog.destroy).pack(pady=10)
            
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler bei detaillierter Analyse:\n{str(e)}")
    
    def _show_flow_optimizer(self):
        """Zeigt interaktiven Durchfluss-Optimizer (v3.3.0-beta2)."""
        if not hasattr(self, 'hydraulics_result') or not self.hydraulics_result:
            messagebox.showinfo("Hinweis", "Bitte erst Hydraulik berechnen!")
            return
        
        try:
            # Hole aktuelle Parameter
            heat_power = float(self.heat_pump_entries.get("heat_pump_power", ttk.Entry()).get() or "11")
            cop = float(self.heat_pump_entries.get("heat_pump_cop", ttk.Entry()).get() or "4.0")
            depth = float(self.borehole_entries.get("depth", ttk.Entry()).get() or "100")
            num_boreholes = int(self.borehole_entries.get("num_boreholes", ttk.Entry()).get() or "2")
            num_circuits = int(self.hydraulics_entries.get("num_circuits", ttk.Entry()).get() or str(num_boreholes))
            pipe_inner_d = float(self.entries.get("pipe_inner_d", ttk.Entry()).get() or "0.026")
            antifreeze_conc = float(self.hydraulics_entries.get("antifreeze_concentration", ttk.Entry()).get() or "25")
            current_delta_t = float(self.entries.get("delta_t_fluid", ttk.Entry()).get() or "3.0")
            
            extraction_power = heat_power * (cop - 1) / cop
            
            # Bestimme Kreise pro Bohrung
            pipe_config = self.pipe_config_var.get()
            if "4-rohr" in pipe_config.lower() or "double" in pipe_config.lower():
                circuits_per_borehole = 2
            else:
                circuits_per_borehole = 1
            
            # Erstelle Dialog
            dialog = tk.Toplevel(self.root)
            dialog.title("Durchfluss-Optimierung")
            dialog.geometry("1200x800")
            
            # Haupt-Frame
            main_frame = ttk.Frame(dialog)
            main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
            
            # Titel
            title = ttk.Label(main_frame, text="🎯 DURCHFLUSS-OPTIMIERUNG", 
                            font=("Arial", 14, "bold"))
            title.pack(pady=(0, 15))
            
            # Info-Frame
            info_frame = ttk.LabelFrame(main_frame, text="Aktuelle Konfiguration", padding=10)
            info_frame.pack(fill="x", pady=(0, 10))
            
            info_text = f"Leistung: {heat_power:.1f} kW | COP: {cop:.1f} | "
            info_text += f"Bohrungen: {num_boreholes}×{depth:.0f}m | "
            info_text += f"Glykol: {antifreeze_conc:.0f}%"
            ttk.Label(info_frame, text=info_text).pack()
            
            # Optimierungsziel
            target_frame = ttk.LabelFrame(main_frame, text="Optimierungsziel", padding=10)
            target_frame.pack(fill="x", pady=(0, 10))
            
            target_var = tk.StringVar(value="balanced")
            ttk.Radiobutton(target_frame, text="Minimale Pumpenleistung", 
                           variable=target_var, value="min_pump").pack(anchor="w")
            ttk.Radiobutton(target_frame, text="Optimale Reynolds-Zahl (Re > 3000)", 
                           variable=target_var, value="optimal_reynolds").pack(anchor="w")
            ttk.Radiobutton(target_frame, text="Ausgeglichener Kompromiss", 
                           variable=target_var, value="balanced").pack(anchor="w")
            
            # Slider-Frame
            slider_frame = ttk.LabelFrame(main_frame, text="ΔT-Einstellung", padding=10)
            slider_frame.pack(fill="x", pady=(0, 10))
            
            delta_t_var = tk.DoubleVar(value=current_delta_t)
            delta_t_label = ttk.Label(slider_frame, text=f"ΔT: {current_delta_t:.1f} K")
            delta_t_label.pack()
            
            delta_t_slider = ttk.Scale(slider_frame, from_=2.0, to=5.0, 
                                      variable=delta_t_var, orient="horizontal")
            delta_t_slider.pack(fill="x", padx=20, pady=5)
            
            # Ergebnis-Frame
            result_frame = ttk.LabelFrame(main_frame, text="Ergebnisse", padding=10)
            result_frame.pack(fill="both", expand=True, pady=(0, 10))
            
            scrollbar = ttk.Scrollbar(result_frame)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            result_text = tk.Text(result_frame, wrap=tk.WORD, yscrollcommand=scrollbar.set,
                                 font=("Courier", 10), height=20)
            result_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.config(command=result_text.yview)
            
            def calculate_for_delta_t(delta_t):
                """Berechnet Hydraulik für gegebenes ΔT."""
                flow = self.hydraulics_calc.calculate_required_flow_rate(
                    extraction_power, delta_t, antifreeze_conc
                )
                
                system = self.hydraulics_calc.calculate_total_system_pressure_drop(
                    depth, num_boreholes, num_circuits, pipe_inner_d,
                    flow['volume_flow_m3_h'], antifreeze_conc,
                    circuits_per_borehole=circuits_per_borehole
                )
                
                pump = self.hydraulics_calc.calculate_pump_power(
                    flow['volume_flow_m3_h'], system['total_pressure_drop_bar']
                )
                
                # Energie-Prognose
                energy = self.hydraulics_calc.calculate_pump_energy_consumption(
                    pump['electric_power_w'], 1800, 0.30
                )
                
                return {
                    'delta_t': delta_t,
                    'flow': flow,
                    'system': system,
                    'pump': pump,
                    'energy': energy
                }
            
            def update_results(*args):
                try:
                    delta_t = delta_t_var.get()
                    delta_t_label.config(text=f"ΔT: {delta_t:.1f} K")
                    
                    # Berechne aktuell
                    current = calculate_for_delta_t(delta_t)
                    
                    # Berechne optimal für Ziel
                    target = target_var.get()
                    best_delta_t = delta_t
                    best_score = 0
                    
                    for test_dt in [2.0, 2.2, 2.5, 2.7, 3.0, 3.5, 4.0, 4.5, 5.0]:
                        test_result = calculate_for_delta_t(test_dt)
                        
                        if target == "min_pump":
                            score = -test_result['pump']['electric_power_w']
                        elif target == "optimal_reynolds":
                            re = test_result['system']['reynolds']
                            score = -abs(re - 3500)  # Ziel: Re = 3500
                        else:  # balanced
                            re = test_result['system']['reynolds']
                            pump_w = test_result['pump']['electric_power_w']
                            score = (min(re, 3500) / 3500) * 1000 - (pump_w / 10)
                        
                        if score > best_score:
                            best_score = score
                            best_delta_t = test_dt
                    
                    optimal = calculate_for_delta_t(best_delta_t)
                    
                    # Formatiere Ausgabe
                    output = "=" * 75 + "\n"
                    output += "DURCHFLUSS-OPTIMIERUNG\n"
                    output += "=" * 75 + "\n\n"
                    
                    output += f"Aktuelle Werte (ΔT = {current['delta_t']:.1f} K):\n"
                    output += f"  Volumenstrom: {current['flow']['volume_flow_m3_h']:.2f} m³/h\n"
                    output += f"  Reynolds: {current['system']['reynolds']:.0f} "
                    output += f"({'turbulent' if current['system']['reynolds'] > 2300 else 'laminar'})\n"
                    output += f"  Druckverlust: {current['system']['total_pressure_drop_bar']:.2f} bar\n"
                    output += f"  Pumpe: {current['pump']['electric_power_w']:.0f} W\n"
                    output += f"  Energiekosten: {current['energy']['annual_cost_eur']:.2f} EUR/Jahr\n\n"
                    
                    if abs(best_delta_t - delta_t) > 0.2:
                        output += "=" * 75 + "\n"
                        output += f"💡 OPTIMIERTES ERGEBNIS (ΔT = {optimal['delta_t']:.1f} K):\n"
                        output += "=" * 75 + "\n\n"
                        
                        output += f"  Volumenstrom: {optimal['flow']['volume_flow_m3_h']:.2f} m³/h "
                        vol_change = ((optimal['flow']['volume_flow_m3_h'] / current['flow']['volume_flow_m3_h']) - 1) * 100
                        output += f"({vol_change:+.1f}%)\n"
                        
                        output += f"  Reynolds: {optimal['system']['reynolds']:.0f} "
                        re_change = ((optimal['system']['reynolds'] / current['system']['reynolds']) - 1) * 100
                        output += f"({re_change:+.1f}%)\n"
                        
                        output += f"  Druckverlust: {optimal['system']['total_pressure_drop_bar']:.2f} bar "
                        dp_change = ((optimal['system']['total_pressure_drop_bar'] / current['system']['total_pressure_drop_bar']) - 1) * 100
                        output += f"({dp_change:+.1f}%)\n"
                        
                        output += f"  Pumpe: {optimal['pump']['electric_power_w']:.0f} W "
                        pump_change = ((optimal['pump']['electric_power_w'] / current['pump']['electric_power_w']) - 1) * 100
                        output += f"({pump_change:+.1f}%)\n"
                        
                        output += f"  Energiekosten: {optimal['energy']['annual_cost_eur']:.2f} EUR/Jahr "
                        energy_change = optimal['energy']['annual_cost_eur'] - current['energy']['annual_cost_eur']
                        output += f"({energy_change:+.2f} EUR/Jahr)\n\n"
                        
                        output += "EMPFEHLUNG:\n"
                        if abs(pump_change) < 5:
                            output += f"  ✅ Aktueller Wert ist gut (< 5% Unterschied)\n"
                        elif pump_change > 0:
                            output += f"  ⬆️  Optimierung erhöht Pumpenleistung um {abs(pump_change):.1f}%\n"
                            output += f"     → Bessere Reynolds-Zahl, höherer Wärmeübergang\n"
                            output += f"     → +{abs(energy_change):.2f} EUR/Jahr Energiekosten\n"
                        else:
                            output += f"  ⬇️  Optimierung senkt Pumpenleistung um {abs(pump_change):.1f}%\n"
                            output += f"     → {abs(energy_change):.2f} EUR/Jahr Ersparnis\n"
                            if optimal['system']['reynolds'] < 2500:
                                output += f"     ⚠️  Reynolds knapp turbulent ({optimal['system']['reynolds']:.0f})\n"
                    else:
                        output += "✅ Aktueller Wert ist bereits optimal!\n\n"
                    
                    output += "\n" + "=" * 75 + "\n"
                    output += "VERGLEICHS-ÜBERSICHT\n"
                    output += "=" * 75 + "\n\n"
                    output += f"{'ΔT (K)':<10} {'Flow (m³/h)':<15} {'Reynolds':<12} {'Pumpe (W)':<12} {'EUR/Jahr':<12}\n"
                    output += "-" * 75 + "\n"
                    
                    for test_dt in [2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0]:
                        test = calculate_for_delta_t(test_dt)
                        marker = " ← " if abs(test_dt - delta_t) < 0.1 else ""
                        marker += " ★" if abs(test_dt - best_delta_t) < 0.1 else ""
                        output += f"{test_dt:<10.1f} {test['flow']['volume_flow_m3_h']:<15.2f} "
                        output += f"{test['system']['reynolds']:<12.0f} {test['pump']['electric_power_w']:<12.0f} "
                        output += f"{test['energy']['annual_cost_eur']:<12.2f}{marker}\n"
                    
                    output += "\n← = Aktuelle Einstellung | ★ = Optimal für Ziel\n"
                    
                    result_text.config(state="normal")
                    result_text.delete("1.0", tk.END)
                    result_text.insert("1.0", output)
                    result_text.config(state="disabled")
                    
                except Exception as e:
                    result_text.config(state="normal")
                    result_text.delete("1.0", tk.END)
                    result_text.insert("1.0", f"Fehler: {str(e)}")
                    result_text.config(state="disabled")
            
            # Events binden
            delta_t_slider.config(command=lambda *args: update_results())
            target_var.trace_add("write", update_results)
            
            # Initial berechnen
            update_results()
            
            # Button-Frame
            button_frame = ttk.Frame(main_frame)
            button_frame.pack(fill="x", pady=(10, 0))
            
            def apply_optimal():
                best_dt = None
                for test_dt in [2.0, 2.2, 2.5, 2.7, 3.0, 3.5, 4.0, 4.5, 5.0]:
                    # Finde optimales ΔT basierend auf Ziel
                    pass  # Logik wie oben
                # Setze in Hauptfenster
                self.entries.get("delta_t_fluid", ttk.Entry()).delete(0, tk.END)
                self.entries.get("delta_t_fluid", ttk.Entry()).insert(0, f"{delta_t_var.get():.1f}")
                messagebox.showinfo("Erfolg", f"ΔT auf {delta_t_var.get():.1f} K gesetzt.\n\nBitte Hydraulik neu berechnen!")
                dialog.destroy()
            
            ttk.Button(button_frame, text="Übernehmen", 
                      command=apply_optimal).pack(side="left", padx=5)
            ttk.Button(button_frame, text="Schließen", 
                      command=dialog.destroy).pack(side="right", padx=5)
            
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler bei Durchfluss-Optimierung:\n{str(e)}")
    
    def _show_pump_selection(self):
        """Zeigt Pumpenauswahl-Assistenten (v3.3.0-beta3)."""
        if not hasattr(self, 'hydraulics_result') or not self.hydraulics_result:
            messagebox.showinfo("Hinweis", "Bitte erst Hydraulik berechnen!")
            return
        
        try:
            # Hole Wärmeleistung von der ersten Seite (Wärmepumpen-Tab)
            heat_power = float(self.heat_pump_entries["heat_pump_power"].get() or "11")
            
            # Erstelle Hydraulik-Daten für Dialog (mit allen benötigten Feldern)
            hydraulics_data = {
                'heat_power': heat_power,
                'flow': self.hydraulics_result.get('flow', {}),
                'system': self.hydraulics_result.get('system', {}),
                'depth': float(self.borehole_entries.get("depth", ttk.Entry()).get() or "100"),
                'num_boreholes': int(self.borehole_entries.get("num_boreholes", ttk.Entry()).get() or "2")
            }
            
            # Zeige Dialog
            dialog = PumpSelectionDialog(self.root, hydraulics_data)
            selected_pump = dialog.show()
            
            if selected_pump:
                # Zeige Bestätigung mit Details
                msg = f"Ausgewählte Pumpe:\n\n"
                msg += f"{selected_pump.get_full_name()}\n\n"
                msg += f"Typ: {'Geregelt' if selected_pump.pump_type == 'regulated' else 'Konstant'}\n"
                msg += f"Effizienz: {selected_pump.efficiency_class}\n"
                msg += f"Max. Flow: {selected_pump.specs.max_flow_m3h} m³/h\n"
                msg += f"Max. Head: {selected_pump.specs.max_head_m} m\n"
                msg += f"Leistung: {selected_pump.specs.power_avg_w} W\n"
                msg += f"Preis: {selected_pump.price_eur:.2f} EUR\n\n"
                msg += "Diese Informationen wurden in die Zwischenablage kopiert."
                
                # Kopiere in Zwischenablage
                self.root.clipboard_clear()
                self.root.clipboard_append(msg)
                
                messagebox.showinfo("Pumpe ausgewählt", msg)
        
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler bei Pumpenauswahl:\n{str(e)}")
    
    def _check_flow_rate_warnings(self, heat_power_kw: float, flow_rate_m3s: float, num_boreholes: int,
                                   current_delta_t: float, antifreeze_conc: float, extraction_power: float):
        """Prüft Volumenstrom auf empfohlene Werte und gibt Warnungen als Text zurück."""
        # Empfohlene Werte: 0.8 - 1.5 l/s pro kW (für Sole-Wasser-WP)
        recommended_min_ls_per_kw = 0.8  # l/s pro kW
        recommended_max_ls_per_kw = 1.5   # l/s pro kW
        
        # Umrechnung: m³/s → l/s
        flow_rate_ls = flow_rate_m3s * 1000
        flow_rate_ls_per_kw = flow_rate_ls / heat_power_kw if heat_power_kw > 0 else 0
        
        # Mindestwert pro Sonde für turbulente Strömung (Re > 2500)
        # v3.3.0-beta1: Erhöht von 2.1 auf 2.5 m³/h aufgrund korrigierter Viskosität
        # Mit realistischen VDI-Wärmeatlas Werten (0°C) ist höherer Volumenstrom nötig
        min_per_borehole_m3h = 2.5  # Entspricht Re ≈ 2500 bei 0°C, 25% Glykol
        flow_rate_m3h = flow_rate_m3s * 3600
        flow_per_borehole_m3h = flow_rate_m3h / num_boreholes if num_boreholes > 0 else 0
        
        warnings = []
        
        # Prüfe Empfehlung pro kW (zeige auch in m³/h)
        flow_rate_m3h = flow_rate_m3s * 3600
        recommended_min_m3h = recommended_min_ls_per_kw * heat_power_kw * 3.6  # l/s → m³/h
        recommended_max_m3h = recommended_max_ls_per_kw * heat_power_kw * 3.6
        
        if flow_rate_ls_per_kw < recommended_min_ls_per_kw:
            # Berechne optimale ΔT für empfohlenen Mindest-Volumenstrom
            # V̇ = Q / (c_p × ρ × ΔT) → ΔT = Q / (c_p × ρ × V̇)
            props = self.hydraulics_calc._get_fluid_properties(antifreeze_conc)
            target_flow_m3s = (recommended_min_ls_per_kw * heat_power_kw) / 1000  # l/s → m³/s
            optimal_delta_t = (extraction_power * 1000) / (props['heat_capacity'] * props['density'] * target_flow_m3s)
            
            # Schätze Pumpenleistung bei optimalem Volumenstrom (grob)
            # Druckverlust steigt quadratisch mit Volumenstrom
            if hasattr(self, 'hydraulics_result') and self.hydraulics_result:
                current_pump_w = self.hydraulics_result.get('pump', {}).get('electric_power_w', 0)
                flow_ratio = target_flow_m3s / flow_rate_m3s if flow_rate_m3s > 0 else 1
                estimated_pump_w = current_pump_w * (flow_ratio ** 2)
            else:
                estimated_pump_w = 150  # Schätzwert
            
            warnings.append(
                f"⚠️ VOLUMENSTROM ZU NIEDRIG:\n"
                f"   Aktuell: {flow_rate_m3h:.2f} m³/h ({flow_rate_ls_per_kw:.2f} l/s/kW)\n"
                f"   Empfohlen: {recommended_min_m3h:.1f} - {recommended_max_m3h:.1f} m³/h\n"
                f"   \n"
                f"   💡 OPTIMIERUNGSVORSCHLAG:\n"
                f"   • ΔT von {current_delta_t:.1f}K auf ca. {optimal_delta_t:.1f}K reduzieren\n"
                f"   • Volumenstrom steigt dann auf ca. {target_flow_m3s * 3600:.2f} m³/h\n"
                f"   • Pumpenleistung steigt auf ca. {estimated_pump_w:.0f} W\n"
                f"   \n"
                f"   ⚡ FOLGEN BEI ZU NIEDRIGEM VOLUMENSTROM:\n"
                f"   • Schlechterer Wärmeübergang\n"
                f"   • Höhere Vorlauftemperatur nötig\n"
                f"   • JAZ-Reduktion: 8-15%"
            )
        elif flow_rate_ls_per_kw > recommended_max_ls_per_kw:
            warnings.append(
                f"⚠️ VOLUMENSTROM ZU HOCH:\n"
                f"   Aktuell: {flow_rate_m3h:.2f} m³/h ({flow_rate_ls_per_kw:.2f} l/s/kW)\n"
                f"   Empfohlen: {recommended_min_m3h:.1f} - {recommended_max_m3h:.1f} m³/h\n"
                f"   \n"
                f"   ⚡ FOLGEN:\n"
                f"   • Hoher Druckverlust\n"
                f"   • Hohe Pumpenleistung\n"
                f"   • Parasitäre Verluste: 3-8%"
            )
        
        # Prüfe Mindestwert pro Sonde
        if flow_per_borehole_m3h < min_per_borehole_m3h:
            warnings.append(
                f"⚠️ VOLUMENSTROM PRO SONDE ZU NIEDRIG:\n"
                f"   Aktuell: {flow_per_borehole_m3h:.2f} m³/h pro Sonde\n"
                f"   Minimum: {min_per_borehole_m3h} m³/h pro Sonde\n"
                f"   \n"
                f"   ⚡ PROBLEM: Strömung nicht turbulent (Re < 2300)\n"
                f"   → Schlechter Wärmeübergang"
            )
        
        # Zeige Warnungen (nur erste, um nicht zu überladen)
        if warnings:
            return warnings[0]
        return ""
    
    def _load_pvgis_data(self):
        """Lädt Klimadaten von PVGIS."""
        # Benutzerdefinierten Dialog für bessere Sichtbarkeit
        dialog = tk.Toplevel(self.root)
        dialog.title("🌍 PVGIS Klimadaten laden")
        dialog.geometry("500x350")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Zentrierung
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (500 // 2)
        y = (dialog.winfo_screenheight() // 2) - (350 // 2)
        dialog.geometry(f"500x350+{x}+{y}")
        
        result = {'choice': None, 'address': None, 'lat': None, 'lon': None}
        
        # Frame für Inhalte
        content_frame = ttk.Frame(dialog, padding=20)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(content_frame, text="Wählen Sie die Eingabemethode:", 
                 font=("Arial", 11, "bold")).pack(pady=10)
        
        # Radio-Buttons für Auswahl
        choice_var = tk.StringVar(value="address")
        ttk.Radiobutton(content_frame, text="📍 Adresse eingeben", 
                       variable=choice_var, value="address").pack(anchor=tk.W, pady=5)
        ttk.Radiobutton(content_frame, text="🌐 Koordinaten eingeben (Lat/Lon)", 
                       variable=choice_var, value="coords").pack(anchor=tk.W, pady=5)
        
        # Eingabefelder
        input_frame = ttk.LabelFrame(content_frame, text="Eingabe", padding=10)
        input_frame.pack(fill=tk.BOTH, expand=True, pady=15)
        
        ttk.Label(input_frame, text="Adresse:").grid(row=0, column=0, sticky=tk.W, pady=5)
        address_entry = ttk.Entry(input_frame, width=40)
        address_entry.grid(row=0, column=1, pady=5, padx=5)
        address_entry.insert(0, "z.B. Musterstraße 1, 80331 München")
        
        ttk.Label(input_frame, text="Breitengrad:").grid(row=1, column=0, sticky=tk.W, pady=5)
        lat_entry = ttk.Entry(input_frame, width=20)
        lat_entry.grid(row=1, column=1, pady=5, padx=5, sticky=tk.W)
        lat_entry.insert(0, "z.B. 48.14")
        
        ttk.Label(input_frame, text="Längengrad:").grid(row=2, column=0, sticky=tk.W, pady=5)
        lon_entry = ttk.Entry(input_frame, width=20)
        lon_entry.grid(row=2, column=1, pady=5, padx=5, sticky=tk.W)
        lon_entry.insert(0, "z.B. 11.58")
        
        # Buttons
        btn_frame = ttk.Frame(content_frame)
        btn_frame.pack(pady=10)
        
        def on_load():
            result['choice'] = choice_var.get()
            result['address'] = address_entry.get()
            try:
                result['lat'] = float(lat_entry.get())
                result['lon'] = float(lon_entry.get())
            except:
                pass
            dialog.destroy()
        
        def on_cancel():
            dialog.destroy()
        
        ttk.Button(btn_frame, text="🌍 Klimadaten laden", 
                  command=on_load).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Abbrechen", 
                  command=on_cancel).pack(side=tk.LEFT, padx=5)
        
        # Warte auf Dialog
        self.root.wait_window(dialog)
        
        # Verarbeite Ergebnis
        try:
            if result['choice'] == 'address' and result['address']:
                address = result['address']
                if "z.B." not in address:
                    self.status_var.set("⏳ Lade Klimadaten von PVGIS...")
                    self.root.update()
                    data = self.pvgis_client.get_climate_data_for_address(address)
                else:
                    return
            elif result['choice'] == 'coords' and result['lat'] and result['lon']:
                lat, lon = result['lat'], result['lon']
                self.status_var.set("⏳ Lade Klimadaten von PVGIS...")
                self.root.update()
                data = self.pvgis_client.get_monthly_temperature_data(lat, lon)
            else:
                return
            
            if data:
                # Übernehme Daten
                self.climate_entries["avg_air_temp"].delete(0, tk.END)
                self.climate_entries["avg_air_temp"].insert(0, f"{data['yearly_avg_temp']:.1f}")
                
                self.climate_entries["coldest_month_temp"].delete(0, tk.END)
                self.climate_entries["coldest_month_temp"].insert(0, f"{data['coldest_month_temp']:.1f}")
                
                # Bodentemperatur schätzen
                ground_temp = self.soil_db.estimate_ground_temperature(
                    data['yearly_avg_temp'], data['coldest_month_temp']
                )
                self.entries["ground_temp"].delete(0, tk.END)
                self.entries["ground_temp"].insert(0, f"{ground_temp:.1f}")
                
                messagebox.showinfo("Erfolg", f"Klimadaten erfolgreich geladen!\n\n" +
                                   f"Jahresmittel: {data['yearly_avg_temp']:.1f}°C\n" +
                                   f"Kältester Monat: {data['coldest_month_temp']:.1f}°C\n" +
                                   f"Geschätzte Bodentemp.: {ground_temp:.1f}°C")
                
                self.status_var.set("✓ PVGIS Klimadaten erfolgreich geladen")
            else:
                messagebox.showwarning("Keine Daten", "Keine Daten von PVGIS erhalten. Verwenden Sie Fallback-Daten.")
                self.status_var.set("❌ PVGIS nicht erreichbar - Verwende Fallback")
                
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Laden der PVGIS-Daten: {str(e)}")
            self.status_var.set("❌ PVGIS-Fehler")
    
    def _run_calculation(self):
        """Führt die Hauptberechnung durch."""
        try:
            # Sammle Parameter
            params = {}
            for key, entry in self.entries.items():
                value = entry.get()
                if value:
                    try:
                        params[key] = float(value)
                    except ValueError:
                        params[key] = value  # String-Werte behalten
                else:
                    params[key] = 0.0  # Default für leere numerische Felder
            
            # Konvertiere mm → m für Rohr-Parameter und Bohrlochdurchmesser
            params["pipe_outer_diameter"] = params["pipe_outer_diameter"] / 1000.0
            params["pipe_thickness"] = params["pipe_thickness"] / 1000.0
            params["borehole_diameter"] = params["borehole_diameter"] / 1000.0
            # Konvertiere Schenkelabstand von mm → m
            params["shank_spacing"] = params["shank_spacing"] / 1000.0
            
            self.status_var.set("⏳ Berechnung läuft...")
            self.root.update()
            
            # Pipe Config anpassen
            pipe_config = self.pipe_config_var.get()
            if "4-rohr" in pipe_config:
                pipe_config = "double-u"
            
            # Anzahl Bohrungen
            num_boreholes = int(self.borehole_entries["num_boreholes"].get())
            
            # Prüfe Berechnungsmethode
            method = self.calculation_method_var.get()
            
            if method == "vdi4640":
                # === VDI 4640 BERECHNUNG ===
                
                # Berechne Bohrlochwiderstand (vereinfachte Methode)
                # Für eine genauere Berechnung könnte hier die Multipol-Methode verwendet werden
                # Hier verwenden wir einen typischen Wert basierend auf der Geometrie
                
                # Vereinfachter Bohrlochwiderstand nach VDI 4640
                borehole_radius = params["borehole_diameter"] / 2
                pipe_outer_radius = params["pipe_outer_diameter"] / 2
                
                # Thermischer Widerstand Verfüllung (vereinfacht)
                r_grout = (1 / (2 * math.pi * params["grout_thermal_cond"])) * \
                          math.log(borehole_radius / pipe_outer_radius)
                
                # Thermischer Widerstand Rohr
                pipe_inner_radius = (params["pipe_outer_diameter"] - 2 * params["pipe_thickness"]) / 2
                r_pipe = (1 / (2 * math.pi * params["pipe_thermal_cond"])) * \
                         math.log(params["pipe_outer_diameter"] / (2 * pipe_inner_radius))
                
                # Konvektiver Widerstand (vereinfacht)
                r_conv = 1 / (2 * math.pi * pipe_inner_radius * 500)  # h ≈ 500 W/m²K typisch
                
                # Gesamtwiderstand (vereinfacht für Single-U oder Double-U)
                if pipe_config == "single-u":
                    r_borehole = r_grout + r_pipe + r_conv
                else:  # double-u
                    r_borehole = 0.8 * (r_grout + r_pipe + r_conv)  # Reduktion durch 4 Rohre
                
                # Mindestens 0.05 m·K/W
                r_borehole = max(0.05, r_borehole)
                
                # Thermische Diffusivität
                thermal_diffusivity = params["ground_thermal_cond"] / params["ground_heat_cap"]
                
                # VDI 4640 Berechnung (Debug-Modus ist bereits aktiviert)
                self.vdi4640_result = self.vdi4640_calc.calculate_complete(
                    ground_thermal_conductivity=params["ground_thermal_cond"],
                    ground_thermal_diffusivity=thermal_diffusivity,
                    t_undisturbed=params["ground_temp"],
                    borehole_diameter=params["borehole_diameter"] * 1000,  # zurück in mm
                    borehole_depth_initial=params["initial_depth"],
                    n_boreholes=num_boreholes,
                    r_borehole=r_borehole,
                    annual_heating_demand=params["annual_heating"],  # jetzt in kWh
                    peak_heating_load=params["peak_heating"],
                    annual_cooling_demand=params["annual_cooling"],  # jetzt in kWh
                    peak_cooling_load=params["peak_cooling"],
                    heat_pump_cop_heating=params["heat_pump_cop"],
                    heat_pump_cop_cooling=params.get("heat_pump_eer", params["heat_pump_cop"]),
                    t_fluid_min_required=params["min_fluid_temp"],
                    t_fluid_max_required=params["max_fluid_temp"],
                    delta_t_fluid=params.get("delta_t_fluid", 3.0)
                )
                
                # Prüfe maximale Sondenlänge (nur bei VDI 4640) - nur Warnung, keine automatische Anpassung
                max_depth_entry = self.entries.get("max_depth_per_borehole")
                if max_depth_entry:
                    max_depth_per_borehole = float(max_depth_entry.get() or "999")
                else:
                    max_depth_per_borehole = 999.0
                
                # Nur Warnung anzeigen, wenn Tiefe über Maximum liegt
                # KEINE automatische Anpassung der Bohrlochanzahl mehr!
                if max_depth_per_borehole < 999 and self.vdi4640_result.required_depth_final > max_depth_per_borehole:
                    # Berechne Vorschlag: Mehr Bohrungen mit geringerer Tiefe
                    total_length_needed = self.vdi4640_result.required_depth_final * num_boreholes
                    suggested_num_boreholes = int(num_boreholes) + 1
                    suggested_depth = min(80.0, total_length_needed / suggested_num_boreholes)
                    
                    # Versuche verschiedene Konfigurationen
                    for test_boreholes in range(int(num_boreholes) + 1, int(num_boreholes) + 4):
                        test_depth = total_length_needed / test_boreholes
                        if test_depth <= max_depth_per_borehole:
                            suggested_num_boreholes = test_boreholes
                            suggested_depth = test_depth
                            break
                    
                    messagebox.showwarning(
                        "Hinweis - Maximale Sondenlänge überschritten", 
                        f"Die berechnete Sondenlänge beträgt {self.vdi4640_result.required_depth_final:.1f} m pro Bohrung "
                        f"bei {num_boreholes} Bohrungen.\n\n"
                        f"Dies überschreitet Ihr Maximum von {max_depth_per_borehole:.0f} m pro Bohrung.\n\n"
                        f"📊 AKTUELLE KONFIGURATION:\n"
                        f"   {num_boreholes} Bohrungen à {self.vdi4640_result.required_depth_final:.1f} m\n"
                        f"   Gesamtlänge: {total_length_needed:.1f} m\n\n"
                        f"💡 VORSCHLAG:\n"
                        f"   {suggested_num_boreholes} Bohrungen à {suggested_depth:.1f} m\n"
                        f"   Gesamtlänge: {total_length_needed:.1f} m\n\n"
                        f"Bitte passen Sie die Anzahl der Bohrungen manuell an."
                    )
                
                # Erstelle BoreholeResult für Kompatibilität
                from calculations.borehole import BoreholeResult
                self.result = BoreholeResult(
                    required_depth=self.vdi4640_result.required_depth_final,
                    fluid_temperature_min=self.vdi4640_result.t_wp_aus_heating_min,
                    fluid_temperature_max=self.vdi4640_result.t_wp_aus_cooling_max,
                    borehole_resistance=r_borehole,
                    effective_resistance=r_borehole + self.vdi4640_result.r_grundlast,
                    heat_extraction_rate=self.vdi4640_result.q_nettogrundlast_heating / self.vdi4640_result.required_depth_final if self.vdi4640_result.required_depth_final > 0 else 0,
                    monthly_temperatures=[self.vdi4640_result.t_wp_aus_heating_min] * 12
                )
                
                # Status anzeigen
                self.status_var.set(f"✓ VDI 4640 Berechnung: {self.vdi4640_result.required_depth_final:.1f}m (ausgelegt für {self.vdi4640_result.design_case.upper()})")
                
            else:
                # === ITERATIVE BERECHNUNG (Original) ===
                self.result = self.calculator.calculate_required_depth(
                    ground_thermal_conductivity=params["ground_thermal_cond"],
                    ground_heat_capacity=params["ground_heat_cap"],
                    undisturbed_ground_temp=params["ground_temp"],
                    geothermal_gradient=params["geothermal_gradient"],
                    borehole_diameter=params["borehole_diameter"],
                    pipe_configuration=pipe_config,
                    pipe_outer_diameter=params["pipe_outer_diameter"],
                    pipe_wall_thickness=params["pipe_thickness"],
                    pipe_thermal_conductivity=params["pipe_thermal_cond"],
                    shank_spacing=params["shank_spacing"],
                    grout_thermal_conductivity=params["grout_thermal_cond"],
                    fluid_thermal_conductivity=params["fluid_thermal_cond"],
                    fluid_heat_capacity=params["fluid_heat_cap"],
                    fluid_density=params["fluid_density"],
                    fluid_viscosity=params["fluid_viscosity"],
                    fluid_flow_rate=params["fluid_flow_rate"] / 3600.0,  # m³/h → m³/s
                    annual_heating_demand=params["annual_heating"] / 1000,  # kWh → MWh
                    annual_cooling_demand=params["annual_cooling"] / 1000,  # kWh → MWh
                    peak_heating_load=params["peak_heating"],
                    peak_cooling_load=params["peak_cooling"],
                    heat_pump_cop=params["heat_pump_cop"],
                    min_fluid_temperature=params["min_fluid_temp"],
                    max_fluid_temperature=params["max_fluid_temp"],
                    simulation_years=int(params["simulation_years"]),
                    initial_depth=params["initial_depth"]
                )
                
                self.vdi4640_result = None
                self.status_var.set(f"✓ Berechnung erfolgreich! {self.result.required_depth:.1f}m × {num_boreholes} = {self.result.required_depth * num_boreholes:.1f}m gesamt")
            
            self.current_params = params
            self.current_params['pipe_configuration'] = self.pipe_config_var.get()
            self.current_params['calculation_method'] = method
            
            self._display_results()
            self._plot_results()
            
            self.notebook.select(self.results_frame)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            messagebox.showerror("Fehler", f"Fehler bei der Berechnung: {str(e)}")
            self.status_var.set("❌ Berechnung fehlgeschlagen")
    
    def _get_pipe_length_factor(self, pipe_config: str) -> int:
        """
        Gibt den Faktor für die Gesamtlänge der Leitungen zurück.
        
        Args:
            pipe_config: Rohrkonfiguration (single-u, double-u, coaxial, etc.)
        
        Returns:
            Anzahl der Leitungen pro Bohrung
        """
        config_lower = pipe_config.lower()
        
        if "single-u" in config_lower or "single" in config_lower:
            return 2  # 2 Rohre: 1 Vorlauf + 1 Rücklauf = 2 Leitungen
        elif "double-u" in config_lower or "double" in config_lower or "4-rohr" in config_lower:
            return 4  # 4 Rohre: 2 Vorlauf + 2 Rücklauf = 4 Leitungen
        elif "coaxial" in config_lower:
            return 2  # Vorlauf + Rücklauf (ähnlich Single-U)
        else:
            return 2  # Standard: Single-U
    
    def _get_pipe_positions(self, pipe_config, params):
        """Gibt Rohrpositionen für Bohrlochwiderstand zurück."""
        borehole_radius = params["borehole_diameter"] / 2
        shank_spacing = params["shank_spacing"]
        
        if pipe_config == "single-u":
            return [
                (-shank_spacing / 2, 0),
                (shank_spacing / 2, 0)
            ]
        elif pipe_config == "double-u":
            offset = shank_spacing / 2
            return [
                (-offset, -offset),
                (offset, -offset),
                (-offset, offset),
                (offset, offset)
            ]
        else:
            return [(0, 0), (0, 0)]
    
    def _display_results(self):
        """Zeigt Ergebnisse an."""
        if not self.result:
            return
        
        num_bh = int(self.borehole_entries["num_boreholes"].get())
        
        self.results_text.config(state=tk.NORMAL)
        self.results_text.delete("1.0", tk.END)
        
        # === HEADER ===
        text = "=" * 80 + "\n"
        text += "ERDWÄRMESONDEN-BERECHNUNGSERGEBNIS (Professional V3.2.1)\n"
        text += "=" * 80 + "\n\n"
        
        # Projekt Info
        proj_name = self.project_entries["project_name"].get()
        if proj_name:
            text += f"📋 Projekt: {proj_name}\n"
            text += f"👤 Kunde: {self.project_entries['customer_name'].get()}\n\n"
        
        # === BERECHNUNGSMETHODE ===
        method = self.current_params.get('calculation_method', 'iterativ')
        if method == "vdi4640" and self.vdi4640_result:
            text += "📐 BERECHNUNGSMETHODE: VDI 4640 (Koenigsdorff)\n"
            text += "=" * 80 + "\n\n"
            
            # === AUSLEGUNGSFALL ===
            text += "🎯 AUSLEGUNGSFALL\n"
            text += "-" * 80 + "\n"
            if self.vdi4640_result.design_case == "heating":
                text += "✓ HEIZEN ist auslegungsrelevant\n"
                text += f"  Erforderliche Sondenlänge: {self.vdi4640_result.required_depth_heating:.1f} m\n"
                text += f"  (Kühlen würde nur {self.vdi4640_result.required_depth_cooling:.1f} m benötigen)\n"
            else:
                text += "✓ KÜHLEN ist auslegungsrelevant (dominante Kühllast!)\n"
                text += f"  Erforderliche Sondenlänge: {self.vdi4640_result.required_depth_cooling:.1f} m\n"
                text += f"  (Heizen würde nur {self.vdi4640_result.required_depth_heating:.1f} m benötigen)\n"
            text += f"\n  → Ausgelegte Sondenlänge: {self.vdi4640_result.required_depth_final:.1f} m\n"
            text += f"  → Anzahl Bohrungen: {num_bh}\n"
            text += f"  → Gesamtlänge (Bohrungen): {self.vdi4640_result.required_depth_final * num_bh:.1f} m\n"
            
            # Berechne Gesamtlänge der Leitungen
            pipe_config = self.pipe_config_var.get()
            pipe_length_factor = self._get_pipe_length_factor(pipe_config)
            pipe_length_per_borehole = self.vdi4640_result.required_depth_final * pipe_length_factor
            total_pipe_length = pipe_length_per_borehole * num_bh
            text += f"  → Gesamtlänge (Leitungen): {total_pipe_length:.1f} m\n"
            text += f"     ({pipe_length_factor} Leitungen pro Bohrung × {self.vdi4640_result.required_depth_final:.1f} m = {pipe_length_per_borehole:.1f} m pro Bohrung)\n\n"
            
            # === WÄRMEPUMPENAUSTRITTSTEMPERATUREN ===
            text += "🌡️  WÄRMEPUMPENAUSTRITTSTEMPERATUREN\n"
            text += "-" * 80 + "\n"
            text += f"Heizen (minimale WP-Austrittstemperatur): {self.vdi4640_result.t_wp_aus_heating_min:.2f} °C\n"
            text += f"  Komponenten:\n"
            text += f"    T_ungestört:            {self.current_params['ground_temp']:.2f} °C\n"
            text += f"    - ΔT_Grundlast:        {self.vdi4640_result.delta_t_grundlast_heating:.3f} K\n"
            text += f"    - ΔT_Periodisch:       {self.vdi4640_result.delta_t_per_heating:.3f} K\n"
            text += f"    - ΔT_Peak:             {self.vdi4640_result.delta_t_peak_heating:.3f} K\n"
            text += f"    - 0.5 · ΔT_Fluid:      {self.vdi4640_result.delta_t_fluid_heating / 2:.2f} K\n\n"
            
            text += f"Kühlen (maximale WP-Austrittstemperatur): {self.vdi4640_result.t_wp_aus_cooling_max:.2f} °C\n"
            text += f"  Komponenten:\n"
            text += f"    T_ungestört:            {self.current_params['ground_temp']:.2f} °C\n"
            text += f"    + ΔT_Grundlast:        {self.vdi4640_result.delta_t_grundlast_cooling:.3f} K\n"
            text += f"    + ΔT_Periodisch:       {self.vdi4640_result.delta_t_per_cooling:.3f} K\n"
            text += f"    + ΔT_Peak:             {self.vdi4640_result.delta_t_peak_cooling:.3f} K\n"
            text += f"    - 0.5 · ΔT_Fluid:      {self.vdi4640_result.delta_t_fluid_cooling / 2:.2f} K\n\n"
            
            # === THERMISCHE WIDERSTÄNDE ===
            text += "♨️  THERMISCHE WIDERSTÄNDE\n"
            text += "-" * 80 + "\n"
            text += f"R_Grundlast (10 Jahre):     {self.vdi4640_result.r_grundlast:.6f} m·K/W  (g={self.vdi4640_result.g_grundlast:.4f})\n"
            text += f"R_Periodisch (1 Monat):     {self.vdi4640_result.r_per:.6f} m·K/W  (g={self.vdi4640_result.g_per:.4f})\n"
            text += f"R_Peak (6 Stunden):         {self.vdi4640_result.r_peak:.6f} m·K/W  (g={self.vdi4640_result.g_peak:.4f})\n"
            text += f"R_Bohrloch:                 {self.vdi4640_result.r_borehole:.6f} m·K/W\n\n"
            
            # === LASTEN ===
            text += "⚡ LASTDATEN\n"
            text += "-" * 80 + "\n"
            text += "HEIZEN:\n"
            text += f"  Jahresenergie:         {self.current_params['annual_heating']:.0f} kWh\n"
            text += f"  Q_Nettogrundlast:      {self.vdi4640_result.q_nettogrundlast_heating/1000:.3f} kW  (Jahresmittel)\n"
            text += f"  Q_Periodisch:          {self.vdi4640_result.q_per_heating/1000:.3f} kW  (kritischster Monat)\n"
            text += f"  Q_Peak:                {self.vdi4640_result.q_peak_heating/1000:.3f} kW  (Spitzenlast)\n\n"
            
            text += "KÜHLEN:\n"
            text += f"  Jahresenergie:         {self.current_params['annual_cooling']:.0f} kWh\n"
            text += f"  Q_Nettogrundlast:      {self.vdi4640_result.q_nettogrundlast_cooling/1000:.3f} kW  (Jahresmittel)\n"
            text += f"  Q_Periodisch:          {self.vdi4640_result.q_per_cooling/1000:.3f} kW  (kritischster Monat)\n"
            text += f"  Q_Peak:                {self.vdi4640_result.q_peak_cooling/1000:.3f} kW  (Spitzenlast)\n\n"
            
        else:
            # === ITERATIVE METHODE ===
            text += "⚙️  BERECHNUNGSMETHODE: Iterativ (Eskilson/Hellström)\n"
            text += "=" * 80 + "\n\n"
            
            text += "🎯 BOHRFELD\n"
            text += "-" * 80 + "\n"
            text += f"Anzahl Bohrungen:      {num_bh}\n"
            text += f"Tiefe pro Bohrung:     {self.result.required_depth:.1f} m\n"
            text += f"Gesamtlänge (Bohrungen): {self.result.required_depth * num_bh:.1f} m\n"
            
            # Berechne Gesamtlänge der Leitungen
            pipe_config = self.pipe_config_var.get()
            pipe_length_factor = self._get_pipe_length_factor(pipe_config)
            total_pipe_length = self.result.required_depth * num_bh * pipe_length_factor
            text += f"Gesamtlänge (Leitungen): {total_pipe_length:.1f} m\n"
            text += f"  ({pipe_length_factor} Leitungen pro Bohrung)\n\n"
            
            text += "🌡️  TEMPERATUREN\n"
            text += "-" * 80 + "\n"
            text += f"Min. Fluidtemperatur:  {self.result.fluid_temperature_min:.2f} °C\n"
            text += f"Max. Fluidtemperatur:  {self.result.fluid_temperature_max:.2f} °C\n\n"
            
            text += "♨️  WIDERSTÄNDE\n"
            text += "-" * 80 + "\n"
            text += f"R_Bohrloch:            {self.result.borehole_resistance:.6f} m·K/W\n"
            text += f"R_effektiv:            {self.result.effective_resistance:.6f} m·K/W\n\n"
            
            text += "⚡ ENTZUGSLEISTUNG\n"
            text += "-" * 80 + "\n"
            text += f"Spezifisch:            {self.result.heat_extraction_rate:.2f} W/m\n\n"
        
        text += "=" * 80 + "\n"
        
        self.results_text.insert("1.0", text)
        self.results_text.config(state=tk.DISABLED)
    
    def _plot_results(self):
        """Erstellt Visualisierungen: Temperaturen, Bohrloch-Querschnitt, Bohrfeld-Layout."""
        if not self.result:
            return
        
        self.fig.clear()
        
        # 3 Subplots: Temperaturen links, Bohrfeld-Layout Mitte, Bohrloch-Querschnitt rechts
        ax1 = self.fig.add_subplot(1, 3, 1)
        ax2 = self.fig.add_subplot(1, 3, 2)
        ax3 = self.fig.add_subplot(1, 3, 3)
        
        # Temperaturen
        months = ["J", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"]
        x = np.arange(len(months))
        
        ax1.plot(x, self.result.monthly_temperatures, 'o-', linewidth=2.5, markersize=8, color='#1f4788')
        ax1.axhline(y=self.result.fluid_temperature_min, color='b', linestyle='--', linewidth=2,
                    label=f'Min: {self.result.fluid_temperature_min:.1f}°C')
        ax1.axhline(y=self.result.fluid_temperature_max, color='r', linestyle='--', linewidth=2,
                    label=f'Max: {self.result.fluid_temperature_max:.1f}°C')
        ax1.set_xlabel('Monat', fontsize=11, fontweight='bold')
        ax1.set_ylabel('Temperatur [°C]', fontsize=11, fontweight='bold')
        ax1.set_title('Monatliche Temperaturen', fontsize=12, fontweight='bold')
        ax1.set_xticks(x)
        ax1.set_xticklabels(months)
        ax1.grid(True, alpha=0.3)
        ax1.legend(fontsize=9)
        
        # === 2. BOHRFELD-LAYOUT (Draufsicht) ===
        try:
            from matplotlib.patches import Rectangle
            
            # Sichere Werte mit Fallback
            num_boreholes = int(self.borehole_entries.get("num_boreholes", ttk.Entry()).get() or "1")
            spacing = float(self.borehole_entries.get("borehole_spacing", ttk.Entry()).get() or "6.0")
            boundary_dist = float(self.borehole_entries.get("boundary_distance", ttk.Entry()).get() or "3.0")
            house_dist = float(self.borehole_entries.get("house_distance", ttk.Entry()).get() or "3.0")
            
            # Grundstück zeichnen (Rechteck)
            total_width = max(20, spacing * max(1, num_boreholes - 1) + 2 * boundary_dist + 10)
            total_height = max(20, spacing + 2 * boundary_dist + house_dist + 10)
            
            # Grundstück (hellgrün)
            property_rect = Rectangle((-total_width/2, -total_height/2), total_width, total_height,
                                     facecolor='#e8f5e9', edgecolor='#4caf50', linewidth=2, 
                                     label='Grundstück')
            ax2.add_patch(property_rect)
            
            # Haus (grau, oben)
            house_width = total_width * 0.4
            house_height = min(house_dist * 0.8, total_height * 0.3)
            house_y = total_height/2 - house_height - 2
            house_rect = Rectangle((-house_width/2, house_y), house_width, house_height,
                                  facecolor='#bdbdbd', edgecolor='#424242', linewidth=2,
                                  label='Gebäude')
            ax2.add_patch(house_rect)
            
            # Bohrungen anordnen (unten im Grundstück)
            bh_y = -total_height/2 + boundary_dist + 3
            if num_boreholes == 1:
                bh_positions = [(0, bh_y)]
            else:
                start_x = -(num_boreholes - 1) * spacing / 2
                bh_positions = [(start_x + i * spacing, bh_y) for i in range(num_boreholes)]
            
            # Bohrungen zeichnen
            for i, (bh_x, bh_y_pos) in enumerate(bh_positions):
                bh_circle = Circle((bh_x, bh_y_pos), 1.2, facecolor='#ff9800', 
                                  edgecolor='#e65100', linewidth=2)
                ax2.add_patch(bh_circle)
                ax2.text(bh_x, bh_y_pos, str(i+1), ha='center', va='center', 
                        fontsize=10, fontweight='bold', color='white')
            
            # Abstände als Pfeile mit Text
            if num_boreholes > 1:
                # Abstand zwischen Bohrungen
                ax2.annotate('', xy=(bh_positions[1][0], bh_y-2), xytext=(bh_positions[0][0], bh_y-2),
                           arrowprops=dict(arrowstyle='<->', color='#2196f3', lw=2))
                ax2.text((bh_positions[0][0] + bh_positions[1][0])/2, bh_y-3, 
                        f'{spacing}m', ha='center', fontsize=9, color='#1976d2', fontweight='bold',
                        bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='#2196f3'))
            
            # Abstand zum Grundstücksrand
            ax2.annotate('', xy=(bh_positions[0][0], -total_height/2), xytext=(bh_positions[0][0], bh_y-1.5),
                       arrowprops=dict(arrowstyle='<->', color='#4caf50', lw=1.5))
            ax2.text(bh_positions[0][0]+2, (-total_height/2 + bh_y-1.5)/2, 
                    f'{boundary_dist}m', ha='left', fontsize=8, color='#2e7d32',
                    bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor='#4caf50'))
            
            # Abstand zum Haus
            ax2.annotate('', xy=(0, house_y), xytext=(0, bh_y+1.5),
                       arrowprops=dict(arrowstyle='<->', color='#f44336', lw=1.5))
            ax2.text(2.5, (house_y + bh_y+1.5)/2, 
                    f'{house_dist}m', ha='left', fontsize=8, color='#c62828',
                    bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor='#f44336'))
            
            ax2.set_xlim(-total_width/2-2, total_width/2+2)
            ax2.set_ylim(-total_height/2-2, total_height/2+2)
            ax2.set_aspect('equal')
            ax2.set_title(f'Bohrfeld ({num_boreholes} Bohrung{"en" if num_boreholes > 1 else ""})', 
                         fontsize=12, fontweight='bold')
            ax2.axis('off')
            ax2.legend(fontsize=8, loc='upper right')
            
        except Exception as e:
            ax2.text(0.5, 0.5, f'Bohrfeld-Visualisierung\nfehlgeschlagen', 
                    ha='center', va='center', fontsize=10, transform=ax2.transAxes)
            ax2.axis('off')
        
        # === 3. BOHRLOCH-QUERSCHNITT ===
        bh_d_mm = float(self.entries["borehole_diameter"].get())
        pipe_d = float(self.entries["pipe_outer_diameter"].get()) / 1000.0  # mm → m
        bh_d = bh_d_mm / 1000.0  # mm → m für Skalierung
        
        scale = 100
        bh_r = (bh_d / 2) * scale
        pipe_r = (pipe_d / 2) * scale
        
        borehole = Circle((0, 0), bh_r, facecolor='#d9d9d9', edgecolor='black', linewidth=2)
        ax3.add_patch(borehole)
        
        positions = [(-bh_r*0.5, bh_r*0.5), (bh_r*0.5, bh_r*0.5),
                    (-bh_r*0.5, -bh_r*0.5), (bh_r*0.5, -bh_r*0.5)]
        colors = ['#ff6b6b', '#4ecdc4', '#ff6b6b', '#4ecdc4']
        
        for i, ((x, y), color) in enumerate(zip(positions, colors)):
            pipe = Circle((x, y), pipe_r*1.5, facecolor=color, edgecolor='black', linewidth=1, alpha=0.8)
            ax3.add_patch(pipe)
            ax3.text(x, y, str(i+1), ha='center', va='center', fontsize=9, fontweight='bold', color='white')
        
        # Durchmesser-Annotation
        ax3.plot([-bh_r, bh_r], [0, 0], 'k--', linewidth=1, alpha=0.5)
        ax3.text(0, -bh_r*1.7, f'Ø {bh_d_mm:.0f}mm', ha='center', fontsize=11, fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.4', facecolor='#ffeb3b', edgecolor='black'))
        
        ax3.set_xlim(-bh_r*1.8, bh_r*1.8)
        ax3.set_ylim(-bh_r*1.9, bh_r*1.5)
        ax3.set_aspect('equal')
        ax3.set_title('Bohrloch-Querschnitt', fontsize=12, fontweight='bold')
        ax3.axis('off')
        
        self.fig.tight_layout()
        self.canvas.draw()
    
    def _export_pdf(self):
        """Exportiert PDF mit allen Daten."""
        if not self.result:
            messagebox.showwarning("Keine Daten", "Bitte zuerst Berechnung durchführen.")
            return
        
        # Dateiname
        proj_name = self.project_entries["project_name"].get() or "Projekt"
        filename = filedialog.asksaveasfilename(
            title="PDF-Bericht speichern",
            defaultextension=".pdf",
            initialfile=f"Bericht_{proj_name.replace(' ', '_')}_V3.pdf",
            filetypes=[("PDF", "*.pdf")]
        )
        
        if filename:
            try:
                self.status_var.set("📄 Erstelle PDF-Bericht...")
                self.root.update()
                
                # Projektinfo
                project_info = {key: entry.get() for key, entry in self.project_entries.items()}
                
                # Bohrfeld
                borehole_config = {key: float(entry.get()) for key, entry in self.borehole_entries.items()}
                
                # Fluid-Info für PDF
                fluid_info = None
                if hasattr(self, 'fluid_var') and self.fluid_var.get():
                    fluid_name = self.fluid_var.get()
                    fluid = self.fluid_db.get_fluid(fluid_name)
                    if fluid:
                        try:
                            temp = float(self.entries.get("fluid_temperature", ttk.Entry()).get() or "5.0")
                        except (ValueError, AttributeError):
                            temp = 5.0
                        props = fluid.get_properties_at_temp(temp)
                        fluid_info = {
                            'name': fluid.name,
                            'type': fluid.type,
                            'concentration_percent': fluid.concentration_percent,
                            'min_temp': fluid.min_temp,
                            'max_temp': fluid.max_temp,
                            **props
                        }
                
                # PDF erstellen (mit optionalen Verfüllmaterial-, Hydraulik-, Bohrfeld-, VDI4640- und Fluid-Daten)
                self.pdf_generator.generate_report(
                    filename, self.result, self.current_params,
                    project_info, borehole_config,
                    grout_calculation=getattr(self, 'grout_calculation', None),
                    hydraulics_result=getattr(self, 'hydraulics_result', None),
                    borefield_result=getattr(self, 'borefield_result', None),
                    vdi4640_result=getattr(self, 'vdi4640_result', None),
                    fluid_info=fluid_info
                )
                
                self.status_var.set(f"✓ PDF erstellt: {os.path.basename(filename)}")
                messagebox.showinfo("Erfolg", f"PDF-Bericht wurde erstellt!")
                
            except Exception as e:
                messagebox.showerror("Fehler", f"PDF-Fehler: {str(e)}")
                self.status_var.set("❌ PDF-Export fehlgeschlagen")
    
    def _export_results(self):
        """Exportiert Text."""
        if not self.result:
            messagebox.showwarning("Keine Daten", "Keine Ergebnisse vorhanden.")
            return
        
        filename = filedialog.asksaveasfilename(defaultextension=".txt",
                                               filetypes=[("Text", "*.txt")])
        if filename:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(self.results_text.get("1.0", tk.END))
            self.status_var.set(f"✓ Text exportiert")
    
    def _create_borefield_tab(self):
        """Erstellt den Bohrfeld-Simulation Tab mit g-Funktionen."""
        # Import hier, um OptionalDependency zu behandeln
        try:
            from calculations.borefield_gfunction import BorefieldCalculator, check_pygfunction_installation
            pygfunction_available, version = check_pygfunction_installation()
        except:
            pygfunction_available = False
            version = "nicht installiert"
        
        # Hauptcontainer
        main_container = ttk.Frame(self.borefield_frame)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Linke Seite: Eingaben
        left_frame = ttk.Frame(main_container)
        left_frame.pack(side="left", fill="both", expand=False, padx=(0, 10))
        
        # Rechte Seite: Visualisierung
        right_frame = ttk.Frame(main_container)
        right_frame.pack(side="right", fill="both", expand=True)
        
        # === KONFIGURATION ===
        ttk.Label(left_frame, text="🌐 BOHRFELD-KONFIGURATION", 
                 font=("Arial", 14, "bold"), foreground="#1f4788").pack(pady=(0, 15))
        
        if not pygfunction_available:
            warning = ttk.Label(left_frame, 
                              text="⚠️  pygfunction nicht installiert!\n\nInstalliere mit:\npip install pygfunction[plot]",
                              foreground="red", font=("Arial", 10))
            warning.pack(pady=10)
            return
        
        # Status
        status_label = ttk.Label(left_frame, 
                                text=f"✅ pygfunction {version} geladen",
                                foreground="green")
        status_label.pack(pady=(0, 10))
        
        # Eingabefelder
        self.borefield_entries = {}
        
        # Layout-Auswahl
        ttk.Label(left_frame, text="Layout:", font=("Arial", 10, "bold")).pack(anchor="w", pady=(10, 2))
        self.borefield_layout_var = tk.StringVar(value="rectangle")
        layouts = ["rectangle", "L", "U", "line"]
        layout_frame = ttk.Frame(left_frame)
        layout_frame.pack(fill="x", pady=(0, 10))
        
        for layout in layouts:
            ttk.Radiobutton(layout_frame, text=layout.upper(), 
                           variable=self.borefield_layout_var, 
                           value=layout).pack(side="left", padx=5)
        
        # Anzahl Bohrungen
        ttk.Label(left_frame, text="Anzahl Bohrungen X:", font=("Arial", 10)).pack(anchor="w", pady=(5, 2))
        self.borefield_entries['num_x'] = ttk.Entry(left_frame, width=15)
        self.borefield_entries['num_x'].insert(0, "3")
        self.borefield_entries['num_x'].pack(anchor="w", pady=(0, 5))
        
        ttk.Label(left_frame, text="Anzahl Bohrungen Y:", font=("Arial", 10)).pack(anchor="w", pady=(5, 2))
        self.borefield_entries['num_y'] = ttk.Entry(left_frame, width=15)
        self.borefield_entries['num_y'].insert(0, "2")
        self.borefield_entries['num_y'].pack(anchor="w", pady=(0, 5))
        
        # Abstände
        ttk.Label(left_frame, text="Abstand X [m]:", font=("Arial", 10)).pack(anchor="w", pady=(5, 2))
        self.borefield_entries['spacing_x'] = ttk.Entry(left_frame, width=15)
        self.borefield_entries['spacing_x'].insert(0, "6.5")
        self.borefield_entries['spacing_x'].pack(anchor="w", pady=(0, 5))
        
        ttk.Label(left_frame, text="Abstand Y [m]:", font=("Arial", 10)).pack(anchor="w", pady=(5, 2))
        self.borefield_entries['spacing_y'] = ttk.Entry(left_frame, width=15)
        self.borefield_entries['spacing_y'].insert(0, "6.5")
        self.borefield_entries['spacing_y'].pack(anchor="w", pady=(0, 5))
        
        # Bohrungsparameter
        ttk.Label(left_frame, text="Bohrtiefe [m]:", font=("Arial", 10)).pack(anchor="w", pady=(5, 2))
        self.borefield_entries['depth'] = ttk.Entry(left_frame, width=15)
        self.borefield_entries['depth'].insert(0, "120.0")
        self.borefield_entries['depth'].pack(anchor="w", pady=(0, 5))
        
        ttk.Label(left_frame, text="Bohrdurchmesser [mm]:", font=("Arial", 10)).pack(anchor="w", pady=(5, 2))
        self.borefield_entries['diameter'] = ttk.Entry(left_frame, width=15)
        # Übernehme Wert aus Hauptmaske wenn vorhanden
        initial_diameter = self.entries.get('borehole_diameter')
        if initial_diameter:
            try:
                self.borefield_entries['diameter'].insert(0, initial_diameter.get())
            except:
                self.borefield_entries['diameter'].insert(0, "152.0")
        else:
            self.borefield_entries['diameter'].insert(0, "152.0")
        self.borefield_entries['diameter'].pack(anchor="w", pady=(0, 5))
        
        # Bodeneigenschaften
        ttk.Label(left_frame, text="Thermische Diffusivität [m²/s]:", 
                 font=("Arial", 10)).pack(anchor="w", pady=(10, 2))
        self.borefield_entries['diffusivity'] = ttk.Entry(left_frame, width=15)
        self.borefield_entries['diffusivity'].insert(0, "1.0e-6")
        self.borefield_entries['diffusivity'].pack(anchor="w", pady=(0, 5))
        
        # Simulationsdauer
        ttk.Label(left_frame, text="Simulationsjahre:", font=("Arial", 10)).pack(anchor="w", pady=(10, 2))
        self.borefield_entries['years'] = ttk.Entry(left_frame, width=15)
        self.borefield_entries['years'].insert(0, "25")
        self.borefield_entries['years'].pack(anchor="w", pady=(0, 10))
        
        # Berechnen-Button
        ttk.Button(left_frame, text="🔄 g-Funktion berechnen", 
                  command=self._calculate_borefield_gfunction,
                  style="Accent.TButton").pack(pady=10, fill="x")
        
        # Ergebnis-Text
        self.borefield_result_text = tk.Text(left_frame, height=8, width=35, 
                                            font=("Courier", 9), wrap=tk.WORD)
        self.borefield_result_text.pack(pady=(10, 0), fill="both", expand=True)
        self.borefield_result_text.insert("1.0", "Noch keine Berechnung durchgeführt.\n\nKlicke 'g-Funktion berechnen' um zu starten.")
        self.borefield_result_text.config(state="disabled")
        
        # Rechte Seite: Visualisierung
        ttk.Label(right_frame, text="📊 BOHRFELD-VISUALISIERUNG", 
                 font=("Arial", 14, "bold"), foreground="#1f4788").pack(pady=(0, 15))
        
        # Matplotlib Figure für Bohrfeld
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        
        self.borefield_fig = Figure(figsize=(10, 8), dpi=100)
        self.borefield_canvas = FigureCanvasTkAgg(self.borefield_fig, right_frame)
        self.borefield_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Platzhalter-Text
        ax = self.borefield_fig.add_subplot(111)
        ax.text(0.5, 0.5, 'Klicke "g-Funktion berechnen"\num Visualisierung zu sehen',
               ha='center', va='center', fontsize=14, color='gray')
        ax.axis('off')
        self.borefield_canvas.draw()
    
    def _calculate_borefield_gfunction(self):
        """Berechnet g-Funktion und visualisiert Bohrfeld."""
        try:
            from calculations.borefield_gfunction import BorefieldCalculator
            
            # Sammle Parameter
            layout = self.borefield_layout_var.get()
            num_x = int(self.borefield_entries['num_x'].get())
            num_y = int(self.borefield_entries['num_y'].get())
            spacing_x = float(self.borefield_entries['spacing_x'].get())
            spacing_y = float(self.borefield_entries['spacing_y'].get())
            depth = float(self.borefield_entries['depth'].get())
            diameter_mm = float(self.borefield_entries['diameter'].get())
            radius = diameter_mm / 2000.0  # mm → m und Durchmesser → Radius
            diffusivity = float(self.borefield_entries['diffusivity'].get())
            years = int(self.borefield_entries['years'].get())
            
            # Status
            self.status_var.set("⏳ Berechne g-Funktion...")
            self.root.update()
            
            # Berechnung
            calc = BorefieldCalculator()
            result = calc.calculate_gfunction(
                layout=layout,
                num_boreholes_x=num_x,
                num_boreholes_y=num_y,
                spacing_x=spacing_x,
                spacing_y=spacing_y,
                borehole_depth=depth,
                borehole_radius=radius,
                soil_thermal_diffusivity=diffusivity,
                simulation_years=years,
                time_resolution="monthly"
            )
            
            # Speichere Ergebnis
            self.borefield_config = {
                "enabled": True,
                "layout": layout,
                "num_boreholes_x": num_x,
                "num_boreholes_y": num_y,
                "spacing_x_m": spacing_x,
                "spacing_y_m": spacing_y,
                "borehole_diameter_mm": diameter_mm,
                "soil_thermal_diffusivity": diffusivity,
                "simulation_years": years
            }
            
            # Speichere Bohrfeld-Ergebnis für PDF-Export
            self.borefield_result = result
            
            # Aktualisiere Ergebnis-Text
            self.borefield_result_text.config(state="normal")
            self.borefield_result_text.delete("1.0", tk.END)
            self.borefield_result_text.insert("1.0", f"""✅ BERECHNUNG ERFOLGREICH

Layout: {layout.upper()}
Bohrungen: {result['num_boreholes']}
Gesamttiefe: {result['total_depth']} m
Feldgröße: {result['field_area']:.1f} m²

Tiefe pro Bohrung: {depth} m
Durchmesser: {diameter_mm} mm
Abstand X: {spacing_x} m
Abstand Y: {spacing_y} m

Simulationsjahre: {years}
Zeitpunkte: {len(result['time'])}

Die g-Funktion wurde berechnet
und wird rechts visualisiert.""")
            self.borefield_result_text.config(state="disabled")
            
            # Visualisierung
            self._plot_borefield_visualization(result)
            
            self.status_var.set(f"✅ g-Funktion berechnet: {result['num_boreholes']} Bohrungen")
            
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler bei g-Funktionen-Berechnung:\n{str(e)}")
            self.status_var.set("❌ Berechnung fehlgeschlagen")
    
    def _plot_borefield_visualization(self, result):
        """Plottet Bohrfeld-Layout und g-Funktion."""
        self.borefield_fig.clear()
        
        import numpy as np
        
        # 2 Subplots: Bohrfeld-Layout und g-Funktion
        ax1 = self.borefield_fig.add_subplot(121)
        ax2 = self.borefield_fig.add_subplot(122)
        
        # Plot 1: Bohrfeld-Layout
        boreField = result['boreField']
        x_coords = [b.x for b in boreField]
        y_coords = [b.y for b in boreField]
        
        ax1.scatter(x_coords, y_coords, s=200, c='#1f4788', alpha=0.6, edgecolors='black', linewidths=2)
        
        # Nummerierung
        for i, (x, y) in enumerate(zip(x_coords, y_coords), 1):
            ax1.text(x, y, str(i), ha='center', va='center', color='white', fontweight='bold', fontsize=10)
        
        ax1.set_xlabel('X-Position [m]', fontsize=11)
        ax1.set_ylabel('Y-Position [m]', fontsize=11)
        ax1.set_title(f'Bohrfeld-Layout: {result["layout"].upper()}\n{result["num_boreholes"]} Bohrungen', 
                     fontsize=12, fontweight='bold')
        ax1.grid(True, alpha=0.3)
        ax1.set_aspect('equal')
        
        # Plot 2: g-Funktion
        gFunc = result['gFunction']
        time_years = result['time'] / (365.25 * 24 * 3600)  # Sekunden → Jahre
        
        ax2.plot(time_years, gFunc.gFunc, 'b-', linewidth=2, label='g-Funktion')
        ax2.set_xlabel('Zeit [Jahre]', fontsize=11)
        ax2.set_ylabel('g-Funktion [-]', fontsize=11)
        ax2.set_title(f'Thermische Response\n{result["simulation_years"]} Jahre Simulation', 
                     fontsize=12, fontweight='bold')
        ax2.grid(True, alpha=0.3)
        ax2.legend()
        
        # Info-Text
        info_text = f"Gesamttiefe: {result['total_depth']} m | Feldgröße: {result['field_area']:.1f} m²"
        self.borefield_fig.text(0.5, 0.02, info_text, ha='center', fontsize=9, style='italic')
        
        self.borefield_fig.tight_layout()
        self.borefield_canvas.draw()
    
    def _show_about(self):
        """Zeigt Über-Dialog."""
        about = """Geothermie Erdsonden-Tool
Professional Edition V3.0

Neue Features in V3:
✓ 7 Verfüllmaterialien mit Mengenberechnung
✓ 11 Bodentypen nach VDI 4640
✓ PVGIS EU-Klimadaten Integration
✓ Vollständige Hydraulik-Berechnungen
✓ Erweiterte Wärmepumpendaten
✓ Frostschutz-Konfiguration

© 2026 - Open Source (MIT Lizenz)"""
        messagebox.showinfo("Über", about)
    
    def _show_pvgis_info(self):
        """Zeigt PVGIS-Info."""
        info = """PVGIS - Photovoltaic Geographical Information System

Ein kostenloser Service der EU (Joint Research Centre)

Bietet Klimadaten für:
- Europa (vollständig)
- Afrika, Asien, Amerika

Website:
https://joint-research-centre.ec.europa.eu/photovoltaic-geographical-information-system-pvgis_en

In diesem Tool verfügbar über:
- Menü: Extras → PVGIS Klimadaten laden
- Eingabe: Adresse oder Koordinaten
- Fallback: Vorgespeicherte Daten für DE, AT, CH"""
        messagebox.showinfo("PVGIS Information", info)
    
    def _load_default_pipes(self):
        """Lädt Standard-Rohre."""
        pipe_file = os.path.join(os.path.dirname(__file__), "..", "import", "pipe.txt")
        if os.path.exists(pipe_file):
            try:
                self.pipes = self.pipe_parser.parse_file(pipe_file)
                self.pipe_type_combo['values'] = [p.name for p in self.pipes]
                # Setze PE 100 RC als Standard
                for i, pipe in enumerate(self.pipes):
                    if "PE 100 RC DN32" in pipe.name and "Dual" in pipe.name:
                        self.pipe_type_combo.current(i)
                        self._on_pipe_selected(None)
                        break
                self.status_var.set(f"✓ {len(self.pipes)} Rohrtypen geladen (inkl. PE 100 RC)")
            except Exception as e:
                print(f"Fehler beim Laden: {e}")
    
    def _load_pipe_file(self):
        """Lädt Pipe-Datei."""
        filename = filedialog.askopenfilename(filetypes=[("Text", "*.txt")])
        if filename:
            try:
                self.pipes = self.pipe_parser.parse_file(filename)
                self.pipe_type_combo['values'] = [p.name for p in self.pipes]
                self.status_var.set(f"✓ {len(self.pipes)} Rohrtypen geladen")
                messagebox.showinfo("Erfolg", f"{len(self.pipes)} Rohrtypen geladen.")
            except Exception as e:
                messagebox.showerror("Fehler", str(e))
    
    def _load_eed_file(self):
        """Lädt EED-Datei."""
        filename = filedialog.askopenfilename(filetypes=[("DAT", "*.dat")])
        if filename:
            try:
                config = self.eed_parser.parse_file(filename)
                # ... Werte übernehmen (wie vorher) ...
                self.status_var.set(f"✓ EED-Datei geladen")
                messagebox.showinfo("Erfolg", "EED-Konfiguration geladen.")
            except Exception as e:
                messagebox.showerror("Fehler", str(e))
    
    def _export_get_file(self):
        """Exportiert aktuelles Projekt als .get Datei."""
        filepath = filedialog.asksaveasfilename(
            defaultextension=".get",
            filetypes=[("GET Projekt", "*.get"), ("Alle Dateien", "*.*")],
            title="Projekt speichern"
        )
        
        if not filepath:
            return
        
        try:
            # Sammle alle Daten aus GUI
            params = {}
            for key, entry in self.entries.items():
                try:
                    params[key] = float(entry.get())
                except:
                    params[key] = entry.get() if entry.get() else 0.0
            
            # Projektdaten
            project_data = {}
            for key, entry in self.project_entries.items():
                project_data[key] = entry.get()
            
            # Bohrfeld-Daten
            borehole_data = {}
            for key, entry in self.borehole_entries.items():
                try:
                    borehole_data[key] = float(entry.get())
                except:
                    borehole_data[key] = entry.get() if entry.get() else 0.0
            
            # Wärmepumpen-Daten
            hp_data = {}
            for key, entry in self.heat_pump_entries.items():
                try:
                    hp_data[key] = float(entry.get())
                except:
                    hp_data[key] = entry.get() if entry.get() else 0.0
            
            # Exportiere
            success = self.get_handler.export_to_get(
                filepath=filepath,
                metadata={
                    "project_name": project_data.get("project_name", ""),
                    "location": f"{project_data.get('city', '')} {project_data.get('postal_code', '')}",
                    "designer": project_data.get("customer_name", ""),
                    "date": project_data.get("date", ""),
                    "notes": f"{project_data.get('address', '')}"
                },
                ground_props={
                    "thermal_conductivity": params.get("ground_thermal_cond", 2.5),
                    "heat_capacity": params.get("ground_heat_cap", 2.4e6),
                    "undisturbed_temp": params.get("ground_temp", 10.0),
                    "geothermal_gradient": params.get("geothermal_gradient", 0.03),
                    "soil_type": self.soil_type_var.get() if hasattr(self, 'soil_type_var') else ""
                },
                borehole_config={
                    "diameter_mm": params.get("borehole_diameter", 152.0),
                    "depth_m": params.get("initial_depth", 100.0),
                    "pipe_configuration": self.pipe_config_var.get(),
                    "shank_spacing_mm": float(self.entries.get("shank_spacing", ttk.Entry()).get() or "65"),  # Wert in mm direkt aus Entry
                    "num_boreholes": int(borehole_data.get("num_boreholes", 1))
                },
                pipe_props={
                    "material": self.pipe_type_var.get() if hasattr(self, 'pipe_type_var') else "PE-100",
                    "outer_diameter_mm": params.get("pipe_outer_diameter", 32.0),
                    "wall_thickness_mm": params.get("pipe_thickness", 2.9),
                    "thermal_conductivity": params.get("pipe_thermal_cond", 0.42),
                    "inner_diameter_mm": params.get("pipe_outer_diameter", 32.0) - 2 * params.get("pipe_thickness", 2.9)
                },
                grout_material={
                    "name": self.grout_type_var.get() if hasattr(self, 'grout_type_var') else "",
                    "thermal_conductivity": params.get("grout_thermal_cond", 2.0),
                    "density": 1800.0,
                    "volume_per_borehole_liters": self.grout_calculation.get('volume_liters', 0.0) if self.grout_calculation else 0.0
                },
                fluid_props={
                    "type": "Wasser/Glykol",
                    "thermal_conductivity": params.get("fluid_thermal_cond", 0.48),
                    "heat_capacity": params.get("fluid_heat_cap", 3795.0),
                    "density": params.get("fluid_density", 1042.0),
                    "viscosity": params.get("fluid_viscosity", 0.00345),
                    "flow_rate_m3h": params.get("fluid_flow_rate", 1.8),  # bereits in m³/h
                    "freeze_temperature": -15.0
                },
                # NEU: Fluid-Datenbank-Informationen
                fluid_database_info={
                    "fluid_name": self.fluid_var.get() if hasattr(self, 'fluid_var') and self.fluid_var.get() else None,
                    "operating_temperature": float(self.entries.get("fluid_temperature", ttk.Entry()).get() or "5.0") if "fluid_temperature" in self.entries else 5.0
                } if (hasattr(self, 'fluid_var') and self.fluid_var.get()) else None,
                loads={
                    "annual_heating_kwh": params.get("annual_heating", 45000.0),
                    "annual_cooling_kwh": params.get("annual_cooling", 0.0),
                    "peak_heating_kw": params.get("peak_heating", 12.5),
                    "peak_cooling_kw": params.get("peak_cooling", 0.0),
                    "heat_pump_cop": hp_data.get("cop_heating", 4.5)
                },
                temp_limits={
                    "min_fluid_temp": params.get("min_fluid_temp", -3.0),
                    "max_fluid_temp": params.get("max_fluid_temp", 20.0)
                },
                simulation={
                    "years": int(params.get("simulation_years", 50)),
                    "initial_depth": params.get("initial_depth", 100.0),
                    "calculation_method": self.calculation_method_var.get() if hasattr(self, 'calculation_method_var') else "iterativ",
                    "heat_pump_eer": params.get("heat_pump_eer", params.get("heat_pump_cop", 4.0)),
                    "delta_t_fluid": params.get("delta_t_fluid", 3.0),
                    "max_depth_per_borehole": float(self.borehole_entries.get("max_depth_per_borehole", ttk.Entry()).get() or "100.0") if "max_depth_per_borehole" in self.borehole_entries else 100.0
                },
                climate_data=self.climate_data,
                borefield_data=self.borefield_config,
                results={
                    "standard": self.result.__dict__ if self.result and hasattr(self.result, '__dict__') else None,
                    "vdi4640": self.vdi4640_result.__dict__ if hasattr(self, 'vdi4640_result') and self.vdi4640_result else None
                },
                # NEU: Separate Export-Felder für bessere Struktur
                vdi4640_result=self.vdi4640_result.__dict__ if hasattr(self, 'vdi4640_result') and self.vdi4640_result else None,
                hydraulics_result=self.hydraulics_result if hasattr(self, 'hydraulics_result') and self.hydraulics_result else None,
                grout_calculation=self.grout_calculation if hasattr(self, 'grout_calculation') and self.grout_calculation else None
            )
            
            if success:
                messagebox.showinfo("Erfolg", f"✅ Projekt gespeichert:\n{os.path.basename(filepath)}")
                self.status_var.set(f"💾 Gespeichert: {os.path.basename(filepath)}")
            else:
                messagebox.showerror("Fehler", "❌ Speichern fehlgeschlagen")
        
        except Exception as e:
            messagebox.showerror("Fehler", f"❌ Export-Fehler:\n{str(e)}")
    
    def _import_get_file(self):
        """Importiert ein .get Projekt."""
        filepath = filedialog.askopenfilename(
            filetypes=[("GET Projekt", "*.get"), ("Alle Dateien", "*.*")],
            title="Projekt laden"
        )
        
        if not filepath:
            return
        
        try:
            data = self.get_handler.import_from_get(filepath)
            
            if not data:
                messagebox.showerror("Fehler", "❌ Datei konnte nicht geladen werden")
                return
            
            # Zeige Versions-Info
            version = data.get("format_version", "unbekannt")
            if version != self.get_handler.format_version:
                messagebox.showinfo(
                    "Migration",
                    f"🔄 Datei wurde von Version {version} auf {self.get_handler.format_version} migriert"
                )
            
            # Fülle GUI-Felder
            self._populate_from_get_data(data)
            
            messagebox.showinfo("Erfolg", f"✅ Projekt geladen:\n{os.path.basename(filepath)}")
            self.status_var.set(f"📥 Geladen: {os.path.basename(filepath)}")
        
        except Exception as e:
            messagebox.showerror("Fehler", f"❌ Import-Fehler:\n{str(e)}")
    
    def _populate_from_get_data(self, data: Dict[str, Any]):
        """Füllt GUI mit Daten aus .get Datei."""
        try:
            # Bodeneigenschaften
            ground = data.get("ground_properties", {})
            self._set_entry("ground_thermal_cond", ground.get("thermal_conductivity", 2.5))
            self._set_entry("ground_heat_cap", ground.get("heat_capacity", 2.4e6))
            self._set_entry("ground_temp", ground.get("undisturbed_temp", 10.0))
            self._set_entry("geothermal_gradient", ground.get("geothermal_gradient", 0.03))
            
            # Bohrlochkonfiguration
            borehole = data.get("borehole_config", {})
            self._set_entry("borehole_diameter", borehole.get("diameter_mm", 152.0))
            self._set_entry("initial_depth", borehole.get("depth_m", 100.0))
            self._set_entry("shank_spacing", borehole.get("shank_spacing_mm", 80.0))
            
            if hasattr(self, 'pipe_config_var'):
                self.pipe_config_var.set(borehole.get("pipe_configuration", "2-rohr-u (Serie)"))
            
            # Rohreigenschaften
            pipe = data.get("pipe_properties", {})
            self._set_entry("pipe_outer_diameter", pipe.get("outer_diameter_mm", 32.0))
            self._set_entry("pipe_thickness", pipe.get("wall_thickness_mm", 2.9))
            self._set_entry("pipe_thermal_cond", pipe.get("thermal_conductivity", 0.42))
            
            # Verfüllmaterial
            grout = data.get("grout_material", {})
            self._set_entry("grout_thermal_cond", grout.get("thermal_conductivity", 2.0))
            
            # Flüssigkeit
            fluid = data.get("heat_carrier_fluid", {})
            self._set_entry("fluid_thermal_cond", fluid.get("thermal_conductivity", 0.48))
            self._set_entry("fluid_heat_cap", fluid.get("heat_capacity", 3795.0))
            self._set_entry("fluid_density", fluid.get("density", 1042.0))
            self._set_entry("fluid_viscosity", fluid.get("viscosity", 0.00345))
            # Volumenstrom ist bereits in m³/h
            flow_rate_m3h = fluid.get("flow_rate_m3h", 1.8)
            self._set_entry("fluid_flow_rate", flow_rate_m3h)
            
            # Lasten
            loads = data.get("loads", {})
            self._set_entry("annual_heating", loads.get("annual_heating_kwh", 45000.0))
            self._set_entry("annual_cooling", loads.get("annual_cooling_kwh", 0.0))
            self._set_entry("peak_heating", loads.get("peak_heating_kw", 12.5))
            self._set_entry("peak_cooling", loads.get("peak_cooling_kw", 0.0))
            
            # Temperaturgrenzen
            temp = data.get("temperature_limits", {})
            self._set_entry("min_fluid_temp", temp.get("min_fluid_temp", -3.0))
            self._set_entry("max_fluid_temp", temp.get("max_fluid_temp", 20.0))
            
            # Simulation
            sim = data.get("simulation_settings", {})
            self._set_entry("simulation_years", sim.get("years", 50))
            
            # Berechnungsmethode (NEU in V3.2)
            if hasattr(self, 'calculation_method_var'):
                method = sim.get("calculation_method", "iterativ")
                self.calculation_method_var.set(method)
            
            # VDI 4640 Parameter (NEU in V3.2)
            if "heat_pump_eer" in sim:
                self._set_entry("heat_pump_eer", sim.get("heat_pump_eer", 4.0))
            if "delta_t_fluid" in sim:
                self._set_entry("delta_t_fluid", sim.get("delta_t_fluid", 3.0))
            if "max_depth_per_borehole" in sim:
                if "max_depth_per_borehole" in self.borehole_entries:
                    self.borehole_entries["max_depth_per_borehole"].delete(0, tk.END)
                    self.borehole_entries["max_depth_per_borehole"].insert(0, str(sim.get("max_depth_per_borehole", 100.0)))
            
            # NEU: Fluid-Datenbank-Informationen importieren
            fluid_db_info = data.get("fluid_database_info")
            if fluid_db_info and hasattr(self, 'fluid_var'):
                fluid_name = fluid_db_info.get("fluid_name")
                if fluid_name and fluid_name in self.fluid_db.get_all_names():
                    self.fluid_var.set(fluid_name)
                    # Trigger Fluid-Auswahl-Event
                    self._on_fluid_selected(None)
                # Betriebstemperatur setzen
                if "operating_temperature" in fluid_db_info and "fluid_temperature" in self.entries:
                    self.entries["fluid_temperature"].delete(0, tk.END)
                    self.entries["fluid_temperature"].insert(0, str(fluid_db_info["operating_temperature"]))
                    self._on_fluid_temperature_changed()
            
            # NEU: VDI 4640 Ergebnis importieren
            vdi_result = data.get("vdi4640_result")
            if vdi_result:
                from calculations.vdi4640 import VDI4640Result
                # Konvertiere Dict zurück zu VDI4640Result
                if isinstance(vdi_result, dict):
                    try:
                        # Rekonstruiere VDI4640Result aus Dict (dataclass)
                        self.vdi4640_result = VDI4640Result(**vdi_result)
                    except Exception as e:
                        print(f"⚠️ Konnte VDI4640Result nicht rekonstruieren: {e}")
                        # Fallback: Speichere als Dict
                        self.vdi4640_result = vdi_result
                else:
                    self.vdi4640_result = vdi_result
            
            # NEU: Hydraulik-Ergebnis importieren
            hydraulics_result = data.get("hydraulics_result")
            if hydraulics_result:
                self.hydraulics_result = hydraulics_result
                # Aktualisiere Hydraulik-Anzeige
                if hasattr(self, 'hydraulics_result_text'):
                    text = "=" * 60 + "\n"
                    text += "HYDRAULIK-BERECHNUNG (aus .get Datei geladen)\n"
                    text += "=" * 60 + "\n\n"
                    flow = hydraulics_result.get('flow', {})
                    system = hydraulics_result.get('system', {})
                    pump = hydraulics_result.get('pump', {})
                    if flow and system and pump:
                        text += f"Volumenstrom: {flow.get('volume_flow_m3_h', 0):.3f} m³/h\n"
                        text += f"Druckverlust: {system.get('total_pressure_drop_bar', 0):.2f} bar\n"
                        text += f"Pumpenleistung: {pump.get('electric_power_w', 0):.0f} W\n"
                    self.hydraulics_result_text.delete("1.0", tk.END)
                    self.hydraulics_result_text.insert("1.0", text)
            
            # NEU: Verfüllmaterial-Berechnung importieren
            grout_calc = data.get("grout_calculation")
            if grout_calc:
                self.grout_calculation = grout_calc
                # Aktualisiere Material-Anzeige
                if hasattr(self, 'grout_result_text'):
                    material = grout_calc.get('material', {})
                    amounts = grout_calc.get('amounts', {})
                    text = "=" * 60 + "\n"
                    text += "VERFÜLLMATERIAL-BERECHNUNG (aus .get Datei geladen)\n"
                    text += "=" * 60 + "\n\n"
                    if isinstance(material, dict):
                        text += f"Material: {material.get('name', 'N/A')}\n"
                        text += f"Volumen gesamt: {amounts.get('mass_kg', 0):.1f} kg\n"
                    self.grout_result_text.delete("1.0", tk.END)
                    self.grout_result_text.insert("1.0", text)
            
            # Klimadaten speichern
            self.climate_data = data.get("climate_data")
            
            # Bohrfeld-Daten V3.2
            self.borefield_config = data.get("borefield_v32")
            
            # Fülle Bohrfeld-Tab wenn Daten vorhanden
            if self.borefield_config and self.borefield_config.get("enabled"):
                self._populate_borefield_tab(self.borefield_config)
            
            print("✅ GUI mit .get Daten gefüllt")
            
        except Exception as e:
            print(f"⚠️ Fehler beim Füllen der GUI: {e}")
    
    def _populate_borefield_tab(self, borefield_data: Dict[str, Any]):
        """Füllt Bohrfeld-Tab mit geladenen Daten."""
        try:
            if not hasattr(self, 'borefield_entries'):
                return
            
            # Layout setzen
            if hasattr(self, 'borefield_layout_var'):
                layout = borefield_data.get('layout', 'rectangle')
                self.borefield_layout_var.set(layout)
            
            # Eingabefelder füllen
            self.borefield_entries['num_x'].delete(0, tk.END)
            self.borefield_entries['num_x'].insert(0, str(borefield_data.get('num_boreholes_x', 3)))
            
            self.borefield_entries['num_y'].delete(0, tk.END)
            self.borefield_entries['num_y'].insert(0, str(borefield_data.get('num_boreholes_y', 2)))
            
            self.borefield_entries['spacing_x'].delete(0, tk.END)
            self.borefield_entries['spacing_x'].insert(0, str(borefield_data.get('spacing_x_m', 6.5)))
            
            self.borefield_entries['spacing_y'].delete(0, tk.END)
            self.borefield_entries['spacing_y'].insert(0, str(borefield_data.get('spacing_y_m', 6.5)))
            
            # Durchmesser setzen (entweder aus Daten oder aus Hauptmaske)
            if 'borehole_diameter_mm' in borefield_data:
                self.borefield_entries['diameter'].delete(0, tk.END)
                self.borefield_entries['diameter'].insert(0, str(borefield_data.get('borehole_diameter_mm', 152.0)))
            elif 'borehole_radius_m' in borefield_data:
                # Alte Dateien mit Radius konvertieren
                radius_m = borefield_data.get('borehole_radius_m', 0.076)
                diameter_mm = radius_m * 2000.0
                self.borefield_entries['diameter'].delete(0, tk.END)
                self.borefield_entries['diameter'].insert(0, str(diameter_mm))
            else:
                # Nutze Wert aus Hauptmaske
                if 'borehole_diameter' in self.entries:
                    try:
                        self.borefield_entries['diameter'].delete(0, tk.END)
                        self.borefield_entries['diameter'].insert(0, self.entries['borehole_diameter'].get())
                    except:
                        pass
            
            # Diffusivität berechnen aus Bodendaten wenn vorhanden
            diffusivity = borefield_data.get('soil_thermal_diffusivity', 1.0e-6)
            self.borefield_entries['diffusivity'].delete(0, tk.END)
            self.borefield_entries['diffusivity'].insert(0, str(diffusivity))
            
            self.borefield_entries['years'].delete(0, tk.END)
            self.borefield_entries['years'].insert(0, str(borefield_data.get('simulation_years', 25)))
            
            # Info in Ergebnis-Textfeld
            if hasattr(self, 'borefield_result_text'):
                self.borefield_result_text.config(state="normal")
                self.borefield_result_text.delete("1.0", tk.END)
                self.borefield_result_text.insert("1.0", 
                    f"📥 Bohrfeld-Konfiguration geladen!\n\n"
                    f"Layout: {borefield_data.get('layout', 'N/A').upper()}\n"
                    f"Bohrungen: {borefield_data.get('num_boreholes_x', 0)}×{borefield_data.get('num_boreholes_y', 0)}\n"
                    f"Abstand: {borefield_data.get('spacing_x_m', 0)} × {borefield_data.get('spacing_y_m', 0)} m\n\n"
                    f"Klicke 'g-Funktion berechnen'\num die Simulation zu starten."
                )
                self.borefield_result_text.config(state="disabled")
            
            print(f"✅ Bohrfeld-Tab gefüllt: {borefield_data.get('layout', 'N/A').upper()}")
            
        except Exception as e:
            print(f"⚠️ Fehler beim Füllen des Bohrfeld-Tabs: {e}")
    
    def _set_entry(self, key: str, value: Any):
        """Hilfsmethode zum Setzen von Entry-Werten."""
        entry = None
        was_readonly = False
        
        if key in self.entries:
            entry = self.entries[key]
        elif key in self.project_entries:
            entry = self.project_entries[key]
        elif key in self.borehole_entries:
            entry = self.borehole_entries[key]
        elif key in self.heat_pump_entries:
            entry = self.heat_pump_entries[key]
        
        if entry:
            # Temporär readonly aufheben, falls nötig
            was_readonly = entry.cget("state") == "readonly"
            if was_readonly:
                entry.config(state="normal")
            entry.delete(0, tk.END)
            entry.insert(0, str(value))
            # Feld bleibt immer editierbar (readonly wird nicht wieder gesetzt)


def main():
    """Haupteinstiegspunkt."""
    root = tk.Tk()
    app = GeothermieGUIProfessional(root)
    root.mainloop()


if __name__ == "__main__":
    main()

