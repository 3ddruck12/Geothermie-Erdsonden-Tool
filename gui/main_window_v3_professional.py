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
from typing import Optional, Dict
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.patches import Circle
import numpy as np

from parsers import PipeParser, EEDParser
from calculations import BoreholeCalculator
from calculations.hydraulics import HydraulicsCalculator
from utils import PDFReportGenerator
from utils.pvgis_api import PVGISClient, FALLBACK_CLIMATE_DATA
from data import GroutMaterialDB, SoilTypeDB
from gui.tooltips import InfoButton


class GeothermieGUIProfessional:
    """Professional Edition V3 GUI."""
    
    def __init__(self, root):
        """Initialisiert die Professional GUI."""
        self.root = root
        self.root.title("Geothermie Erdsonden-Tool - Professional Edition V3.0")
        self.root.geometry("1700x1000")
        
        # Module
        self.pipe_parser = PipeParser()
        self.eed_parser = EEDParser()
        self.calculator = BoreholeCalculator()
        self.hydraulics_calc = HydraulicsCalculator()
        self.pdf_generator = PDFReportGenerator()
        self.pvgis_client = PVGISClient()
        self.grout_db = GroutMaterialDB()
        self.soil_db = SoilTypeDB()
        
        # Daten
        self.pipes = []
        self.result = None
        self.current_params = {}
        self.hydraulics_result = None
        self.grout_calculation = None
        
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
        self._add_entry(parent, row, "Schenkelabstand [m]:", "shank_spacing", "0.065", self.entries)
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
        self._add_entry(parent, row, "Anzahl Solekreise:", "num_circuits", "1", self.hydraulics_entries)
        row += 1
        self._add_entry(parent, row, "Frostschutzkonzentration [Vol%]:", "antifreeze_concentration", "25", self.hydraulics_entries)
        row += 1
        
        self._add_entry(parent, row, "Volumenstrom [m³/s]:", "fluid_flow_rate", "0.0005", self.entries, "fluid_flow_rate")
        row += 1
        self._add_entry(parent, row, "Wärmeleitfähigkeit [W/m·K]:", "fluid_thermal_cond", "0.48", self.entries, "fluid_thermal_cond")
        row += 1
        self._add_entry(parent, row, "Wärmekapazität [J/kg·K]:", "fluid_heat_cap", "3800", self.entries)
        row += 1
        self._add_entry(parent, row, "Dichte [kg/m³]:", "fluid_density", "1030", self.entries)
        row += 1
        self._add_entry(parent, row, "Viskosität [Pa·s]:", "fluid_viscosity", "0.004", self.entries)
        row += 1
        
        # Hydraulik-Button
        ttk.Button(parent, text="💨 Hydraulik berechnen", 
                  command=self._calculate_hydraulics).grid(
            row=row, column=0, columnspan=2, pady=5, padx=10)
        row += 1
        return row
    
    def _add_heat_pump_section(self, parent, row):
        """Wärmepumpen-Sektion."""
        self._add_entry(parent, row, "Wärmepumpenleistung [kW]:", "heat_pump_power", "6.0", self.heat_pump_entries)
        row += 1
        self._add_entry(parent, row, "COP (Coefficient of Performance):", "heat_pump_cop", "4.0", self.entries)
        row += 1
        
        # Kälteleistung wird automatisch berechnet
        ttk.Label(parent, text="Kälteleistung [kW]:", foreground="gray").grid(
            row=row, column=0, sticky="w", padx=10, pady=5)
        self.cold_power_label = ttk.Label(parent, text="(wird berechnet)", foreground="gray")
        self.cold_power_label.grid(row=row, column=1, sticky="w", padx=10, pady=5)
        row += 1
        
        self._add_entry(parent, row, "Warmwasser (Anzahl Personen):", "num_persons_dhw", "4", self.heat_pump_entries)
        row += 1
        
        self._add_entry(parent, row, "Jahres-Heizenergie [MWh]:", "annual_heating", "12.0", self.entries)
        row += 1
        self._add_entry(parent, row, "Jahres-Kühlenergie [MWh]:", "annual_cooling", "0.0", self.entries)
        row += 1
        self._add_entry(parent, row, "Heiz-Spitzenlast [kW]:", "peak_heating", "6.0", self.entries)
        row += 1
        self._add_entry(parent, row, "Kühl-Spitzenlast [kW]:", "peak_cooling", "0.0", self.entries)
        row += 1
        
        self._add_entry(parent, row, "Min. Fluidtemperatur [°C]:", "min_fluid_temp", "-2.0", self.entries)
        row += 1
        self._add_entry(parent, row, "Max. Fluidtemperatur [°C]:", "max_fluid_temp", "15.0", self.entries)
        row += 1
        return row
    
    def _add_simulation_section(self, parent, row):
        """Simulations-Sektion."""
        self._add_entry(parent, row, "Simulationsdauer [Jahre]:", "simulation_years", "25", self.entries)
        row += 1
        self._add_entry(parent, row, "Startwert Bohrtiefe [m]:", "initial_depth", "100", self.entries)
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
    
    def _create_results_tab(self):
        """Erstellt den Ergebnisse-Tab."""
        text_frame = ttk.Frame(self.results_frame)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
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
        
        self.grout_result_text = tk.Text(scrollable_frame, height=15, width=80, font=("Courier", 10))
        self.grout_result_text.pack(padx=10, pady=5)
        self.grout_result_text.insert("1.0", "Noch keine Berechnung durchgeführt.\n\nKlicken Sie auf 'Materialmengen berechnen'.")
        
        # Hydraulik-Anzeige
        ttk.Label(scrollable_frame, text="💨 Hydraulik-Berechnung", 
                 font=("Arial", 14, "bold"), foreground="#1f4788").pack(pady=10)
        
        self.hydraulics_result_text = tk.Text(scrollable_frame, height=15, width=80, font=("Courier", 10))
        self.hydraulics_result_text.pack(padx=10, pady=5)
        self.hydraulics_result_text.insert("1.0", "Noch keine Berechnung durchgeführt.\n\nKlicken Sie auf 'Hydraulik berechnen'.")
    
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
        
        # === QUERSCHNITT (größer, nicht zusammengequetscht) ===
        ax_inset = fig.add_axes([0.58, 0.52, 0.38, 0.42])  # Größer: breiter und höher
        ax_inset.set_title('Querschnitt von oben', fontsize=10, fontweight='bold', pad=10)
        
        # Bohrloch-Kreis
        bh_circle = Circle((0, 0), 1, facecolor='#d9d9d9', edgecolor='black', linewidth=2.5, label='Bohrloch')
        ax_inset.add_patch(bh_circle)
        
        # 4 Rohre in QUADRAT-Anordnung
        # Links-oben, Rechts-oben, Links-unten, Rechts-unten
        positions = [(-0.35, 0.35), (0.35, 0.35), (-0.35, -0.35), (0.35, -0.35)]
        colors = ['#ff6b6b', '#4ecdc4', '#ff6b6b', '#4ecdc4']
        
        for i, ((x, y), color) in enumerate(zip(positions, colors)):
            pipe_circle = Circle((x, y), 0.2, facecolor=color, edgecolor='black', linewidth=1.5)
            ax_inset.add_patch(pipe_circle)
            ax_inset.text(x, y, str(i+1), ha='center', va='center', 
                         fontsize=10, fontweight='bold', color='white')
        
        # Legende UNTEN
        ax_inset.text(0, -1.25, 'Vorlauf (rot)  |  Rücklauf (blau)', 
                     ha='center', fontsize=9, style='italic', fontweight='bold')
        
        ax_inset.set_xlim(-1.1, 1.1)
        ax_inset.set_ylim(-1.5, 1.1)
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
            text += f"  Volumen pro Bohrung: {volume_per_bh:.3f} m³\n"
            text += f"  Volumen gesamt: {total_volume:.3f} m³\n"
            text += f"  Masse gesamt: {amounts['mass_kg']:.1f} kg\n"
            text += f"  Säcke (25 kg): {amounts['bags_25kg']:.1f} Stück\n\n"
            text += f"Kosten:\n"
            text += f"  Gesamt: {amounts['total_cost_eur']:.2f} EUR\n"
            text += f"  Pro Meter: {amounts['cost_per_m']:.2f} EUR/m\n\n"
            text += "=" * 60 + "\n"
            
            self.grout_result_text.delete("1.0", tk.END)
            self.grout_result_text.insert("1.0", text)
            
            self.status_var.set(f"✓ Materialberechnung: {amounts['bags_25kg']:.0f} Säcke, {amounts['total_cost_eur']:.2f} EUR")
            
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler bei Materialberechnung: {str(e)}")
    
    def _calculate_hydraulics(self):
        """Berechnet Hydraulik-Parameter."""
        try:
            # Hole Parameter
            heat_power = float(self.heat_pump_entries["heat_pump_power"].get())
            antifreeze_conc = float(self.hydraulics_entries["antifreeze_concentration"].get())
            num_circuits = int(self.hydraulics_entries["num_circuits"].get())
            depth = float(self.entries["initial_depth"].get())
            num_boreholes = int(self.borehole_entries["num_boreholes"].get())
            # Konvertiere mm → m für Innendurchmesser-Berechnung
            pipe_outer_d_m = float(self.entries["pipe_outer_diameter"].get()) / 1000.0
            pipe_thickness_m = float(self.entries["pipe_thickness"].get()) / 1000.0
            pipe_inner_d = pipe_outer_d_m - 2 * pipe_thickness_m
            
            # Volumenstrom berechnen
            flow = self.hydraulics_calc.calculate_required_flow_rate(
                heat_power, 3.0, antifreeze_conc
            )
            
            # System-Druckverlust
            system = self.hydraulics_calc.calculate_total_system_pressure_drop(
                depth, num_boreholes, num_circuits, pipe_inner_d,
                flow['volume_flow_m3_h'], antifreeze_conc
            )
            
            # Pumpenleistung
            pump = self.hydraulics_calc.calculate_pump_power(
                flow['volume_flow_m3_h'], system['total_pressure_drop_bar']
            )
            
            # Kälteleistung berechnen (COP)
            cop = float(self.entries["heat_pump_cop"].get())
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
            text += f"Kälteleistung: {cold_power:.2f} kW\n"
            text += f"Frostschutz: {antifreeze_conc} Vol%\n"
            text += f"Anzahl Kreise: {num_circuits}\n\n"
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
            text += "=" * 60 + "\n"
            
            self.hydraulics_result_text.delete("1.0", tk.END)
            self.hydraulics_result_text.insert("1.0", text)
            
            self.status_var.set(f"✓ Hydraulik: {flow['volume_flow_m3_h']:.2f} m³/h, {system['total_pressure_drop_mbar']:.0f} mbar, {pump['electric_power_w']:.0f} W")
            
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler bei Hydraulik-Berechnung: {str(e)}")
    
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
                params[key] = float(entry.get())
            
            # Konvertiere mm → m für Rohr-Parameter und Bohrlochdurchmesser
            params["pipe_outer_diameter"] = params["pipe_outer_diameter"] / 1000.0
            params["pipe_thickness"] = params["pipe_thickness"] / 1000.0
            params["borehole_diameter"] = params["borehole_diameter"] / 1000.0
            
            self.status_var.set("⏳ Berechnung läuft...")
            self.root.update()
            
            # Pipe Config anpassen
            pipe_config = self.pipe_config_var.get()
            if "4-rohr" in pipe_config:
                pipe_config = "double-u"
            
            # Berechnung
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
                fluid_flow_rate=params["fluid_flow_rate"],
                annual_heating_demand=params["annual_heating"],
                annual_cooling_demand=params["annual_cooling"],
                peak_heating_load=params["peak_heating"],
                peak_cooling_load=params["peak_cooling"],
                heat_pump_cop=params["heat_pump_cop"],
                min_fluid_temperature=params["min_fluid_temp"],
                max_fluid_temperature=params["max_fluid_temp"],
                simulation_years=int(params["simulation_years"]),
                initial_depth=params["initial_depth"]
            )
            
            self.current_params = params
            self.current_params['pipe_configuration'] = self.pipe_config_var.get()
            
            self._display_results()
            self._plot_results()
            
            num_bh = int(self.borehole_entries["num_boreholes"].get())
            self.status_var.set(f"✓ Berechnung erfolgreich! {self.result.required_depth:.1f}m × {num_bh} = {self.result.required_depth * num_bh:.1f}m gesamt")
            
            self.notebook.select(self.results_frame)
            
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler bei der Berechnung: {str(e)}")
            self.status_var.set("❌ Berechnung fehlgeschlagen")
    
    def _display_results(self):
        """Zeigt Ergebnisse an."""
        if not self.result:
            return
        
        num_bh = int(self.borehole_entries["num_boreholes"].get())
        
        self.results_text.config(state=tk.NORMAL)
        self.results_text.delete("1.0", tk.END)
        
        text = "=" * 70 + "\n"
        text += "ERDWÄRMESONDEN-BERECHNUNGSERGEBNIS (Professional V3)\n"
        text += "=" * 70 + "\n\n"
        
        proj_name = self.project_entries["project_name"].get()
        if proj_name:
            text += f"Projekt: {proj_name}\n"
            text += f"Kunde: {self.project_entries['customer_name'].get()}\n\n"
        
        text += "BOHRFELD\n" + "-" * 70 + "\n"
        text += f"Anzahl: {num_bh}, Tiefe/Bohrung: {self.result.required_depth:.1f}m, Gesamt: {self.result.required_depth * num_bh:.1f}m\n\n"
        
        text += "TEMPERATUREN\n" + "-" * 70 + "\n"
        text += f"Min: {self.result.fluid_temperature_min:.2f}°C, Max: {self.result.fluid_temperature_max:.2f}°C\n\n"
        
        text += "WIDERSTÄNDE\n" + "-" * 70 + "\n"
        text += f"R_b: {self.result.borehole_resistance:.4f} m·K/W, R_eff: {self.result.effective_resistance:.4f} m·K/W\n\n"
        
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
                
                # PDF erstellen
                self.pdf_generator.generate_report(filename, self.result, self.current_params,
                                                   project_info, borehole_config)
                
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
        pipe_file = os.path.join(os.path.dirname(__file__), "..", "Material", "pipe.txt")
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


def main():
    """Haupteinstiegspunkt."""
    root = tk.Tk()
    app = GeothermieGUIProfessional(root)
    root.mainloop()


if __name__ == "__main__":
    main()

