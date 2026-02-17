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
from datetime import datetime
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
from data import GroutMaterialDB, SoilTypeDB, FluidDatabase
from data.pipes import PipeDatabase
from gui.tooltips import InfoButton
from gui.pump_selection_dialog import PumpSelectionDialog
from gui.bohranzeige_tab import BohranzeigTab
from gui.map_widget import OSMMapWidget
from utils.get_file_handler import GETFileHandler
from utils.bohranzeige_pdf import BohranzeigePDFGenerator

# V3.4 Modulare Architektur
from gui.tabs.input_tab import InputTab
from gui.tabs.results_tab import ResultsTab
from gui.tabs.materials_tab import MaterialsTab
from gui.tabs.diagrams_tab import DiagramsTab
from gui.tabs.borefield_tab import BorefieldTab
from gui.controllers.calculation_controller import CalculationController
from gui.controllers.file_controller import FileController


class GeothermieGUIProfessional:
    """Professional Edition V3 GUI."""
    
    def __init__(self, root):
        """Initialisiert die Professional GUI."""
        self.root = root
        self.root.title("Geothermie Erdsonden-Tool - Professional Edition V3.4.0-beta1.8")
        self.root.geometry("1800x1100")
        
        # Module
        self.pipe_parser = PipeParser()
        self.eed_parser = EEDParser()
        self.calculator = BoreholeCalculator()
        # VDI 4640 Calculator (Debug standardmäßig deaktiviert)
        self.vdi4640_calc = VDI4640Calculator(debug=False)
        self.hydraulics_calc = HydraulicsCalculator()
        self.pdf_generator = PDFReportGenerator()
        self.pvgis_client = PVGISClient()
        self.grout_db = GroutMaterialDB()
        self.soil_db = SoilTypeDB()
        self.fluid_db = FluidDatabase()
        self.pipe_db = PipeDatabase()  # NEU: XML-basierte Rohr-Datenbank
        self.get_handler = GETFileHandler()
        self.bohranzeige_pdf = BohranzeigePDFGenerator()
        
        # Debounce-Timer für automatische Neuberechnung
        self._hydraulics_debounce_id = None
        
        # Daten
        self.pipes = []
        self.result = None
        self.vdi4640_result = None  # NEU: VDI 4640 Ergebnis
        self.current_params = {}
        self.hydraulics_result = None
        self.grout_calculation = None
        self.climate_data = None
        self.borefield_config = None
        
        # V3.4 Controller
        self.calc_controller = CalculationController(self)
        self.file_controller = FileController(self)

        # V3.4 Auto-Save
        self._current_file_path = None
        self._auto_save_interval = 300_000  # 5 Minuten in ms

        # GUI aufbauen
        self._create_menu()
        self._create_main_layout()
        self._create_status_bar()
        
        # Lade Daten
        self._load_default_pipes()
        
        # V3.4 Auto-Save starten
        self._start_auto_save()
    
    def _create_menu(self):
        """Erstellt die Menüleiste."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Datei", menu=file_menu)
        file_menu.add_command(label="📥 .get Projekt laden...", command=self.file_controller.import_get_file, accelerator="Ctrl+O")
        file_menu.add_command(label="💾 Als .get speichern...", command=self.file_controller.export_get_file, accelerator="Ctrl+S")
        file_menu.add_separator()
        file_menu.add_command(label="Pipe.txt laden", command=self._load_pipe_file)
        file_menu.add_command(label="EED .dat laden", command=self._load_eed_file)
        file_menu.add_separator()
        file_menu.add_command(label="PDF-Bericht erstellen", command=self.calc_controller.export_pdf, accelerator="Ctrl+P")
        file_menu.add_command(label="📄 Bohranzeige als PDF", command=lambda: self.file_controller.export_bohranzeige_pdf(self.bohranzeige_tab.collect_all_data()))
        file_menu.add_command(label="Text exportieren", command=self.calc_controller.export_results_text)
        file_menu.add_separator()
        file_menu.add_command(label="Beenden", command=self.root.quit)
        
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Extras", menu=tools_menu)
        tools_menu.add_command(label="🌍 PVGIS Klimadaten laden", command=self._load_pvgis_data)
        tools_menu.add_command(label="💧 Materialmengen berechnen", command=self.calc_controller.calculate_grout_materials)
        tools_menu.add_command(label="💨 Hydraulik berechnen", command=self.calc_controller.calculate_hydraulics)
        
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Hilfe", menu=help_menu)
        help_menu.add_command(label="Über", command=self._show_about)
        help_menu.add_command(label="PVGIS Info", command=self._show_pvgis_info)
        
        self.root.bind('<Control-o>', lambda e: self.file_controller.import_get_file())
        self.root.bind('<Control-s>', lambda e: self.file_controller.export_get_file())
        self.root.bind('<Control-p>', lambda e: self.calc_controller.export_pdf())
    
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
        
        self.bohranzeige_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.bohranzeige_frame, text="📄 Bohranzeige")
        self.bohranzeige_tab = BohranzeigTab(
            self.bohranzeige_frame,
            get_berechnung_callback=self._get_bohranzeige_data,
            export_pdf_callback=self._export_bohranzeige_pdf
        )

        # Auto-Übernahme: Projektdaten → Bohranzeige beim Tab-Wechsel
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)
    
    def _on_tab_changed(self, event=None):
        """Wird bei jedem Tab-Wechsel aufgerufen."""
        try:
            selected = self.notebook.select()
            tab_text = self.notebook.tab(selected, "text")
            if "Bohranzeige" in tab_text:
                self._sync_projekt_to_bohranzeige()
        except Exception:
            pass

    def _sync_projekt_to_bohranzeige(self):
        """Überträgt Projektdaten aus dem Eingabe-Tab in die Bohranzeige (nur leere Felder)."""
        if not hasattr(self, 'bohranzeige_tab') or not hasattr(self, 'project_entries'):
            return

        tab = self.bohranzeige_tab

        # Projektdaten → Antragsteller (nur wenn leer)
        mapping = {
            'customer_name': 'name',
            'address': 'strasse',
            'postal_code': 'plz',
            'city': 'ort',
        }
        for proj_key, ba_key in mapping.items():
            proj_entry = self.project_entries.get(proj_key)
            ba_entry = tab.antragsteller_entries.get(ba_key)
            if proj_entry and ba_entry:
                value = proj_entry.get().strip()
                if value and not ba_entry.get().strip():
                    ba_entry.insert(0, value)

        # Ort → Grundstück Gemeinde (nur wenn leer)
        city_entry = self.project_entries.get('city')
        gemeinde_entry = tab.grundstueck_entries.get('gemeinde')
        if city_entry and gemeinde_entry:
            city_val = city_entry.get().strip()
            if city_val and not gemeinde_entry.get().strip():
                gemeinde_entry.insert(0, city_val)

        # Koordinaten aus Karte / climate_data
        if self.climate_data and isinstance(self.climate_data, dict):
            lat = self.climate_data.get('latitude')
            lon = self.climate_data.get('longitude')
            if lat and lon:
                koord_text = tab.koordinaten_label.cget("text")
                if "werden aus" in koord_text or "PVGIS" in koord_text:
                    try:
                        tab.koordinaten_label.configure(
                            text=f"Breite: {float(lat):.4f}°  |  Länge: {float(lon):.4f}°",
                            foreground="#1f4788"
                        )
                    except (TypeError, ValueError):
                        pass

    def _create_input_tab(self):
        """Erstellt den Eingabe-Tab mit allen Professional Features."""
        # 2-Spalten-Layout: Eingaben links, Grafik rechts (PanedWindow für Verschiebbarkeit)
        main_container = ttk.PanedWindow(self.input_frame, orient=tk.HORIZONTAL)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Linke Seite: Scrollbarer Container für Eingaben
        left_frame = ttk.Frame(main_container)
        
        canvas = tk.Canvas(left_frame)
        scrollbar = ttk.Scrollbar(left_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Rechte Seite: Karte + Grafik (scrollbar)
        right_frame = ttk.Frame(main_container, relief=tk.RIDGE, borderwidth=2)
        
        # PanedWindow: linke Seite bekommt mehr Platz (70/30) – Trennlinie verschiebbar
        main_container.add(left_frame, weight=7)
        main_container.add(right_frame, weight=3)

        right_canvas = tk.Canvas(right_frame)
        right_scrollbar = ttk.Scrollbar(right_frame, orient="vertical", command=right_canvas.yview)
        right_scrollable = ttk.Frame(right_canvas)
        right_scrollable.bind("<Configure>", lambda e: right_canvas.configure(scrollregion=right_canvas.bbox("all")))
        right_canvas.create_window((0, 0), window=right_scrollable, anchor="nw")
        right_canvas.configure(yscrollcommand=right_scrollbar.set)
        right_canvas.pack(side="left", fill="both", expand=True)
        right_scrollbar.pack(side="right", fill="y")

        # OSM-Karte (interaktiv) oben in der rechten Seite
        try:
            from gui.map_widget import OSMMapWidget
            self.map_widget = OSMMapWidget(
                right_scrollable,
                width=500,
                height=320,
                default_lat=51.1657,
                default_lon=10.4515,
                default_zoom=6,
                on_position_change=self._on_map_position_changed,
            )
        except Exception as e:
            self.map_widget = None
            logger.warning(f"Kartenwidget konnte nicht geladen werden: {e}")

        self._create_static_borehole_graphic(right_scrollable)
        
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
                  command=self.calc_controller.calculate_grout_materials).grid(
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
                  command=self.calc_controller.calculate_hydraulics).grid(
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
        
        # Erstelle Window im Canvas - nutze volle Breite
        canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Funktion zum Anpassen der Canvas-Breite, damit Inhalte nicht abgeschnitten werden
        def configure_canvas_width(event):
            # Stelle sicher, dass scrollable_frame die volle Canvas-Breite nutzt
            canvas_width = event.width
            canvas.itemconfig(canvas_window, width=canvas_width)
            canvas.configure(scrollregion=canvas.bbox("all"))
        
        canvas.bind('<Configure>', configure_canvas_width)
        scrollable_frame.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        
        canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)
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
        """Erstellt den Visualisierungs-Tab mit scrollbarem Bereich für alle Diagramme."""
        # Obere Steuerleiste mit Button links oben
        control_frame = ttk.Frame(self.viz_frame)
        control_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
        
        ttk.Button(control_frame, text="🔄 Alle Diagramme aktualisieren",
                   command=self._update_all_diagrams).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(control_frame,
                  text="ℹ️ Diagramme werden automatisch in PDF-Bericht eingefügt (Strg+P oder Datei → PDF-Bericht)",
                  font=("Arial", 9), foreground="gray").pack(side=tk.LEFT, padx=10)
        
        # Scrollbarer Container
        canvas_container = tk.Canvas(self.viz_frame)
        scrollbar = ttk.Scrollbar(self.viz_frame, orient="vertical", command=canvas_container.yview)
        scrollable_frame = ttk.Frame(canvas_container)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas_container.configure(scrollregion=canvas_container.bbox("all"))
        )
        
        # Erstelle Window im Canvas - nutze volle Breite
        canvas_window = canvas_container.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas_container.configure(yscrollcommand=scrollbar.set)
        
        # Funktion zum Anpassen der Canvas-Breite, damit Diagramme nicht abgeschnitten werden
        def configure_canvas_width(event):
            # Stelle sicher, dass scrollable_frame die volle Canvas-Breite nutzt
            canvas_width = event.width
            canvas_container.itemconfig(canvas_window, width=canvas_width)
            canvas_container.configure(scrollregion=canvas_container.bbox("all"))
        
        canvas_container.bind('<Configure>', configure_canvas_width)
        scrollable_frame.bind('<Configure>', lambda e: canvas_container.configure(scrollregion=canvas_container.bbox("all")))
        
        # Pack scrollbar und canvas
        canvas_container.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        scrollbar.pack(side="right", fill="y")
        
        # Liste aller Diagramme (alte + neue)
        self.diagram_frames = []
        self.diagram_figures = []
        
        # 1. Monatliche Temperaturen (alt, falls vorhanden)
        self._add_diagram_frame(scrollable_frame, "Monatliche Temperaturen", 
                               self._plot_monthly_temperatures)
        
        # 2. Bohrloch-Schema (alt, falls vorhanden)
        self._add_diagram_frame(scrollable_frame, "Bohrloch-Schema",
                               self._plot_borehole_schema)
        
        # 3. Pumpen-Kennlinien (neu)
        self._add_diagram_frame(scrollable_frame, "Pumpen-Kennlinien",
                               self._plot_pump_characteristics)
        
        # 4. Reynolds-Kurve (neu)
        self._add_diagram_frame(scrollable_frame, "Reynolds-Kurve",
                               self._plot_reynolds_curve)
        
        # 5. Druckverlust-Komponenten (neu)
        self._add_diagram_frame(scrollable_frame, "Druckverlust-Komponenten",
                               self._plot_pressure_components)
        
        # 6. Volumenstrom vs. Druckverlust (neu)
        self._add_diagram_frame(scrollable_frame, "Volumenstrom vs. Druckverlust",
                               self._plot_flow_vs_pressure)
        
        # 7. Pumpenleistung über Betriebszeit (neu)
        self._add_diagram_frame(scrollable_frame, "Pumpenleistung über Betriebszeit",
                               self._plot_pump_power_over_time)
        
        # 8. Temperaturspreizung Sole (neu)
        self._add_diagram_frame(scrollable_frame, "Temperaturspreizung Sole",
                               self._plot_temperature_spread)
        
        # 9. COP vs. Sole-Eintrittstemperatur (neu)
        self._add_diagram_frame(scrollable_frame, "COP vs. Sole-Eintrittstemperatur",
                               self._plot_cop_vs_inlet_temp)
        
        # 10. COP vs. Vorlauftemperatur (neu)
        self._add_diagram_frame(scrollable_frame, "COP vs. Vorlauftemperatur",
                               self._plot_cop_vs_flow_temp)
        
        # 11. JAZ-Abschätzung (neu)
        self._add_diagram_frame(scrollable_frame, "JAZ-Abschätzung",
                               self._plot_jaz_estimation)
        
        # 12. Energieverbrauch-Vergleich (neu)
        self._add_diagram_frame(scrollable_frame, "Energieverbrauch-Vergleich",
                               self._plot_energy_consumption)
        
        # Mousewheel-Scrolling
        def _on_mousewheel(event):
            canvas_container.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas_container.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Store references for scrolling
        self.canvas_container = canvas_container
        self.scrollable_frame = scrollable_frame
    
    def _add_diagram_frame(self, parent, title, plot_function):
        """Fügt ein Diagramm-Frame hinzu."""
        # Frame für dieses Diagramm
        diagram_frame = ttk.LabelFrame(parent, text=f"📊 {title}", padding=10)
        diagram_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=10)
        
        # Matplotlib Figure - größere Breite für vollständige Anzeige
        fig = Figure(figsize=(16, 6), dpi=100)
        canvas = FigureCanvasTkAgg(fig, master=diagram_frame)
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Speichere Referenzen
        self.diagram_frames.append(diagram_frame)
        self.diagram_figures.append({
            'frame': diagram_frame,
            'figure': fig,
            'canvas': canvas,
            'title': title,
            'plot_function': plot_function
        })
        
        # Initial: Platzhalter oder leeres Diagramm
        ax = fig.add_subplot(111)
        ax.text(0.5, 0.5, f"{title}\n\nDiagramm wird nach Berechnung angezeigt",
                ha='center', va='center', fontsize=12, color='gray')
        ax.axis('off')
        canvas.draw()
    
    def _update_all_diagrams(self):
        """Aktualisiert alle Diagramme."""
        for diagram_info in self.diagram_figures:
            try:
                diagram_info['plot_function'](diagram_info['figure'], diagram_info['canvas'])
            except Exception as e:
                # Fehlerbehandlung: Zeige Fehlermeldung im Diagramm
                ax = diagram_info['figure'].gca()
                ax.clear()
                ax.text(0.5, 0.5, f"Fehler beim Erstellen des Diagramms:\n{str(e)}",
                        ha='center', va='center', fontsize=10, color='red')
                diagram_info['canvas'].draw()
    
    # ========== DIAGRAMM-FUNKTIONEN ==========
    
    def _plot_monthly_temperatures(self, fig, canvas):
        """Plottet monatliche Temperaturen."""
        fig.clear()
        ax = fig.add_subplot(111)
        
        if not self.result:
            ax.text(0.5, 0.5, "Keine Berechnung durchgeführt.\n\nBitte Parameter eingeben und Berechnung starten.",
                    ha='center', va='center', fontsize=12, color='gray')
            ax.axis('off')
            canvas.draw()
            return
        
        months = ["J", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"]
        x = np.arange(len(months))
        
        ax.plot(x, self.result.monthly_temperatures, 'o-', linewidth=2.5, markersize=8, color='#1f4788')
        ax.axhline(y=self.result.fluid_temperature_min, color='b', linestyle='--', linewidth=2,
                    label=f'Min: {self.result.fluid_temperature_min:.1f}°C')
        ax.axhline(y=self.result.fluid_temperature_max, color='r', linestyle='--', linewidth=2,
                    label=f'Max: {self.result.fluid_temperature_max:.1f}°C')
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
            bh_d_mm = float(self.entries["borehole_diameter"].get())
            pipe_d = float(self.entries["pipe_outer_diameter"].get()) / 1000.0  # mm → m
            bh_d = bh_d_mm / 1000.0  # mm → m für Skalierung
            
            scale = 100
            bh_r = (bh_d / 2) * scale
            pipe_r = (pipe_d / 2) * scale
            
            borehole = Circle((0, 0), bh_r, facecolor='#d9d9d9', edgecolor='black', linewidth=2)
            ax.add_patch(borehole)
            
            positions = [(-bh_r*0.5, bh_r*0.5), (bh_r*0.5, bh_r*0.5),
                        (-bh_r*0.5, -bh_r*0.5), (bh_r*0.5, -bh_r*0.5)]
            colors = ['#ff6b6b', '#4ecdc4', '#ff6b6b', '#4ecdc4']
            
            for i, ((x, y), color) in enumerate(zip(positions, colors)):
                pipe = Circle((x, y), pipe_r*1.5, facecolor=color, edgecolor='black', linewidth=1, alpha=0.8)
                ax.add_patch(pipe)
                ax.text(x, y, str(i+1), ha='center', va='center', fontsize=9, fontweight='bold', color='white')
            
            # Durchmesser-Annotation
            ax.plot([-bh_r, bh_r], [0, 0], 'k--', linewidth=1, alpha=0.5)
            ax.text(0, -bh_r*1.7, f'Ø {bh_d_mm:.0f}mm', ha='center', fontsize=11, fontweight='bold',
                    bbox=dict(boxstyle='round,pad=0.4', facecolor='#ffeb3b', edgecolor='black'))
            
            ax.set_xlim(-bh_r*1.8, bh_r*1.8)
            ax.set_ylim(-bh_r*1.9, bh_r*1.5)
            ax.set_aspect('equal')
            ax.set_title('Bohrloch-Querschnitt', fontsize=12, fontweight='bold')
            ax.axis('off')
        except Exception as e:
            ax.text(0.5, 0.5, f"Bohrloch-Schema konnte nicht erstellt werden:\n{str(e)}",
                    ha='center', va='center', fontsize=10, color='red')
            ax.axis('off')
        
        fig.tight_layout()
        canvas.draw()
    
    def _plot_pump_characteristics(self, fig, canvas):
        """Plottet Pumpen-Kennlinien (H-Q-Kurve) mit Betriebspunkt."""
        fig.clear()
        ax = fig.add_subplot(111)
        
        if not self.hydraulics_result:
            ax.text(0.5, 0.5, "Keine Hydraulik-Berechnung durchgeführt.\n\nBitte zuerst Hydraulik berechnen.",
                    ha='center', va='center', fontsize=12, color='gray')
            ax.axis('off')
            canvas.draw()
            return
        
        try:
            from data.pump_db import PumpDatabase
            
            # Lade Pumpen-Datenbank
            pump_db = PumpDatabase()
            
            # Hole aktuelle Betriebsdaten
            flow = self.hydraulics_result.get('flow', {})
            system = self.hydraulics_result.get('system', {})
            current_flow = flow.get('volume_flow_m3_h', 0)
            current_head = system.get('total_pressure_drop_bar', 0) * 10.2  # bar → m
            
            # Finde passende Pumpen (2-3 Beispiele)
            suitable_pumps = []
            for pump in pump_db.pumps:
                if (pump.specs.max_flow_m3h >= current_flow * 1.2 and 
                    pump.specs.max_head_m >= current_head * 1.2):
                    suitable_pumps.append(pump)
                    if len(suitable_pumps) >= 3:
                        break
            
            # Wenn keine passenden Pumpen, zeige alle verfügbaren
            if not suitable_pumps:
                suitable_pumps = pump_db.pumps[:3] if len(pump_db.pumps) > 0 else []
            
            # Plot H-Q-Kurven für jede Pumpe (quadratische Approximation)
            colors = ['#2196F3', '#4CAF50', '#FF9800']
            for i, pump in enumerate(suitable_pumps):
                q_max = pump.specs.max_flow_m3h
                h_max = pump.specs.max_head_m
                
                # Quadratische Approximation: H = H_max * (1 - (Q/Q_max)^2)
                q_range = np.linspace(0, q_max, 50)
                h_range = h_max * (1 - (q_range / q_max) ** 2)
                
                ax.plot(q_range, h_range, linewidth=2, color=colors[i % len(colors)],
                       label=f'{pump.manufacturer} {pump.model}\n(H_max={h_max:.1f}m, Q_max={q_max:.1f}m³/h)')
            
            # Betriebspunkt
            if current_flow > 0 and current_head > 0:
                ax.plot(current_flow, current_head, 'ro', markersize=12,
                       label=f'Betriebspunkt\n({current_flow:.2f} m³/h, {current_head:.1f} m)', zorder=5)
            
            # System-Kennlinie (optional, als Referenz)
            if current_flow > 0 and current_head > 0:
                # Annahme: System-Kennlinie ist quadratisch
                q_sys = np.linspace(0, current_flow * 1.5, 30)
                # p ~ Q^2, also H ~ Q^2
                h_sys = current_head * (q_sys / current_flow) ** 2
                ax.plot(q_sys, h_sys, 'k--', linewidth=1.5, alpha=0.5, label='System-Kennlinie')
            
            ax.set_xlabel('Volumenstrom [m³/h]', fontsize=11, fontweight='bold')
            ax.set_ylabel('Förderhöhe [m]', fontsize=11, fontweight='bold')
            ax.set_title('Pumpen-Kennlinien (H-Q-Kurven)', fontsize=12, fontweight='bold')
            ax.grid(True, alpha=0.3)
            ax.legend(fontsize=8, loc='best')
            
            fig.tight_layout()
            canvas.draw()
        except Exception as e:
            ax.text(0.5, 0.5, f"Fehler beim Erstellen des Diagramms:\n{str(e)}",
                    ha='center', va='center', fontsize=10, color='red')
            ax.axis('off')
            canvas.draw()
    
    def _plot_reynolds_curve(self, fig, canvas):
        """Plottet Reynolds-Zahl vs. Volumenstrom für verschiedene Glykol-Konzentrationen."""
        fig.clear()
        ax = fig.add_subplot(111)
        
        if not self.hydraulics_result:
            ax.text(0.5, 0.5, "Keine Hydraulik-Berechnung durchgeführt.\n\nBitte zuerst Hydraulik berechnen.",
                    ha='center', va='center', fontsize=12, color='gray')
            ax.axis('off')
            canvas.draw()
            return
        
        try:
            # Hole aktuelle Parameter
            flow = self.hydraulics_result.get('flow', {})
            current_flow = flow.get('volume_flow_m3_h', 2.5)
            
            # Hole Rohrdurchmesser
            pipe_d = float(self.entries.get("pipe_outer_diameter", ttk.Entry()).get() or "32") / 1000.0  # mm → m
            # Schätzung Innendurchmesser (ca. 2mm Wandstärke)
            pipe_d_inner = pipe_d - 0.004  # ca. 26mm für DN32
            
            # Volumenstrom-Bereich
            flow_range = np.linspace(0.5, 5.0, 50)
            
            # Verschiedene Glykol-Konzentrationen
            concentrations = [0, 25, 30, 40]
            colors = ['#2196F3', '#4CAF50', '#FF9800', '#F44336']
            
            for conc, color in zip(concentrations, colors):
                reynolds_list = []
                props = self.hydraulics_calc._get_fluid_properties(conc)
                density = props['density']
                viscosity = props['viscosity']
                
                area = math.pi * (pipe_d_inner / 2) ** 2
                
                for flow_m3h in flow_range:
                    velocity = (flow_m3h / 3600) / area
                    reynolds = (density * velocity * pipe_d_inner) / viscosity
                    reynolds_list.append(reynolds)
                
                ax.plot(flow_range, reynolds_list, linewidth=2, color=color, 
                       label=f'{conc}% Glykol')
            
            # Turbulenz-Grenze
            ax.axhline(y=2300, color='red', linestyle='--', linewidth=2, 
                      label='Turbulenz-Grenze (Re=2300)')
            
            # Aktueller Betriebspunkt
            if current_flow > 0:
                # Berechne Reynolds für aktuelle Konzentration
                antifreeze_conc = float(self.entries.get("antifreeze_concentration", ttk.Entry()).get() or "25")
                props = self.hydraulics_calc._get_fluid_properties(antifreeze_conc)
                density = props['density']
                viscosity = props['viscosity']
                area = math.pi * (pipe_d_inner / 2) ** 2
                velocity = (current_flow / 3600) / area
                current_reynolds = (density * velocity * pipe_d_inner) / viscosity
                
                ax.plot(current_flow, current_reynolds, 'ro', markersize=12, 
                       label=f'Betriebspunkt (Re={current_reynolds:.0f})', zorder=5)
            
            ax.set_xlabel('Volumenstrom [m³/h]', fontsize=11, fontweight='bold')
            ax.set_ylabel('Reynolds-Zahl [-]', fontsize=11, fontweight='bold')
            ax.set_title('Reynolds-Zahl vs. Volumenstrom', fontsize=12, fontweight='bold')
            ax.grid(True, alpha=0.3)
            ax.legend(fontsize=9, loc='best')
            ax.set_xlim(0.5, 5.0)
            
            # Warnung bei laminarer Strömung
            if current_flow > 0 and current_reynolds < 2300:
                ax.text(0.05, 0.95, '⚠️ LAMINARE STRÖMUNG\nRe < 2300', 
                       transform=ax.transAxes, fontsize=10, color='red',
                       verticalalignment='top', bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.7))
            
            fig.tight_layout()
            canvas.draw()
        except Exception as e:
            ax.text(0.5, 0.5, f"Fehler beim Erstellen der Reynolds-Kurve:\n{str(e)}",
                    ha='center', va='center', fontsize=10, color='red')
            ax.axis('off')
            canvas.draw()
    
    def _plot_pressure_components(self, fig, canvas):
        """Plottet Druckverlust-Komponenten als Tortendiagramm und Balkendiagramm."""
        fig.clear()
        
        if not self.hydraulics_result:
            ax = fig.add_subplot(111)
            ax.text(0.5, 0.5, "Keine Hydraulik-Berechnung durchgeführt.\n\nBitte zuerst Hydraulik berechnen.",
                    ha='center', va='center', fontsize=12, color='gray')
            ax.axis('off')
            canvas.draw()
            return
        
        try:
            # Berechne detaillierte Druckverlust-Analyse
            system = self.hydraulics_result.get('system', {})
            flow = self.hydraulics_result.get('flow', {})
            
            # Hole Parameter
            depth = float(self.entries.get("borehole_depth", ttk.Entry()).get() or "100")
            num_boreholes = int(self.borehole_entries.get("num_boreholes", ttk.Entry()).get() or "1")
            num_circuits = int(self.borehole_entries.get("num_circuits", ttk.Entry()).get() or "1")
            pipe_d = float(self.entries.get("pipe_outer_diameter", ttk.Entry()).get() or "32") / 1000.0
            pipe_d_inner = pipe_d - 0.004  # Schätzung
            volume_flow = flow.get('volume_flow_m3_h', 2.5)
            antifreeze_conc = float(self.entries.get("antifreeze_concentration", ttk.Entry()).get() or "25")
            pipe_config = self.pipe_config_var.get()
            circuits_per_borehole = 2 if 'double' in pipe_config.lower() or '4' in pipe_config else 1
            
            # Detaillierte Analyse
            analysis = self.hydraulics_calc.calculate_detailed_pressure_analysis(
                depth, num_boreholes, num_circuits, pipe_d_inner, volume_flow,
                antifreeze_conc, circuits_per_borehole=circuits_per_borehole
            )
            
            components = analysis['components']
            
            # Zwei Subplots: Tortendiagramm und Balkendiagramm
            ax1 = fig.add_subplot(1, 2, 1)
            ax2 = fig.add_subplot(1, 2, 2)
            
            # Tortendiagramm
            labels = ['Bohrungen', 'Horizontal', 'Formstücke', 'Wärmetauscher']
            sizes = [
                components['boreholes']['percent'],
                components['horizontal']['percent'],
                components['fittings']['percent'],
                components['heat_exchanger']['percent']
            ]
            colors_pie = ['#FF6B6B', '#4ECDC4', '#FFE66D', '#95E1D3']
            
            ax1.pie(sizes, labels=labels, colors=colors_pie, autopct='%1.1f%%',
                   startangle=90, textprops={'fontsize': 10, 'fontweight': 'bold'})
            ax1.set_title('Druckverlust-Anteile', fontsize=12, fontweight='bold')
            
            # Balkendiagramm
            values = [
                components['boreholes']['pressure_drop_bar'],
                components['horizontal']['pressure_drop_bar'],
                components['fittings']['pressure_drop_bar'],
                components['heat_exchanger']['pressure_drop_bar']
            ]
            
            bars = ax2.barh(labels, values, color=colors_pie)
            ax2.set_xlabel('Druckverlust [bar]', fontsize=11, fontweight='bold')
            ax2.set_title('Druckverlust nach Komponenten', fontsize=12, fontweight='bold')
            ax2.grid(True, alpha=0.3, axis='x')
            
            # Werte auf Balken
            for i, (bar, val) in enumerate(zip(bars, values)):
                ax2.text(val + 0.01, i, f'{val:.3f} bar\n({sizes[i]:.1f}%)',
                        va='center', fontsize=9, fontweight='bold')
            
            fig.tight_layout()
            canvas.draw()
        except Exception as e:
            ax = fig.add_subplot(111)
            ax.text(0.5, 0.5, f"Fehler beim Erstellen des Diagramms:\n{str(e)}",
                    ha='center', va='center', fontsize=10, color='red')
            ax.axis('off')
            canvas.draw()
    
    def _plot_flow_vs_pressure(self, fig, canvas):
        """Plottet Volumenstrom vs. Druckverlust (Solekreis-Kennlinie)."""
        fig.clear()
        ax = fig.add_subplot(111)
        
        if not self.hydraulics_result:
            ax.text(0.5, 0.5, "Keine Hydraulik-Berechnung durchgeführt.\n\nBitte zuerst Hydraulik berechnen.",
                    ha='center', va='center', fontsize=12, color='gray')
            ax.axis('off')
            canvas.draw()
            return
        
        try:
            # Hole Parameter
            depth = float(self.entries.get("borehole_depth", ttk.Entry()).get() or "100")
            num_boreholes = int(self.borehole_entries.get("num_boreholes", ttk.Entry()).get() or "1")
            num_circuits = int(self.borehole_entries.get("num_circuits", ttk.Entry()).get() or "1")
            pipe_d = float(self.entries.get("pipe_outer_diameter", ttk.Entry()).get() or "32") / 1000.0
            pipe_d_inner = pipe_d - 0.004
            antifreeze_conc = float(self.entries.get("antifreeze_concentration", ttk.Entry()).get() or "25")
            pipe_config = self.pipe_config_var.get()
            circuits_per_borehole = 2 if 'double' in pipe_config.lower() or '4' in pipe_config else 1
            
            # Volumenstrom-Bereich
            flow_range = np.linspace(0.5, 5.0, 30)
            pressure_range = []
            
            # Berechne Druckverlust für verschiedene Volumenströme
            for flow_m3h in flow_range:
                system_dp = self.hydraulics_calc.calculate_total_system_pressure_drop(
                    depth, num_boreholes, num_circuits, pipe_d_inner, flow_m3h,
                    antifreeze_conc, circuits_per_borehole=circuits_per_borehole
                )
                pressure_range.append(system_dp['total_pressure_drop_bar'])
            
            # Plot Kennlinie
            ax.plot(flow_range, pressure_range, 'b-', linewidth=2.5, label='Solekreis-Kennlinie')
            
            # Aktueller Betriebspunkt
            flow = self.hydraulics_result.get('flow', {})
            system = self.hydraulics_result.get('system', {})
            current_flow = flow.get('volume_flow_m3_h', 0)
            current_pressure = system.get('total_pressure_drop_bar', 0)
            
            if current_flow > 0 and current_pressure > 0:
                ax.plot(current_flow, current_pressure, 'ro', markersize=12,
                       label=f'Betriebspunkt ({current_flow:.2f} m³/h, {current_pressure:.2f} bar)', zorder=5)
            
            ax.set_xlabel('Volumenstrom [m³/h]', fontsize=11, fontweight='bold')
            ax.set_ylabel('Druckverlust [bar]', fontsize=11, fontweight='bold')
            ax.set_title('Volumenstrom vs. Druckverlust (Solekreis-Kennlinie)', fontsize=12, fontweight='bold')
            ax.grid(True, alpha=0.3)
            ax.legend(fontsize=9, loc='best')
            
            fig.tight_layout()
            canvas.draw()
        except Exception as e:
            ax.text(0.5, 0.5, f"Fehler beim Erstellen des Diagramms:\n{str(e)}",
                    ha='center', va='center', fontsize=10, color='red')
            ax.axis('off')
            canvas.draw()
    
    def _plot_pump_power_over_time(self, fig, canvas):
        """Plottet Pumpenleistung über Betriebszeit (monatlich/jährlich)."""
        fig.clear()
        ax = fig.add_subplot(111)
        
        if not self.hydraulics_result:
            ax.text(0.5, 0.5, "Keine Hydraulik-Berechnung durchgeführt.\n\nBitte zuerst Hydraulik berechnen.",
                    ha='center', va='center', fontsize=12, color='gray')
            ax.axis('off')
            canvas.draw()
            return
        
        try:
            pump_power = self.hydraulics_result['pump']['electric_power_w']
            
            # Monatliche Betriebsstunden (Heizperiode)
            months = ["J", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"]
            # Schätzung: Mehr Betrieb im Winter
            monthly_hours = [200, 180, 150, 100, 50, 20, 20, 30, 60, 120, 160, 190]
            total_hours = sum(monthly_hours)
            
            # Monatliche Energieverbrauch
            monthly_energy = [hours * pump_power / 1000 for hours in monthly_hours]  # kWh
            
            # Balkendiagramm
            x = np.arange(len(months))
            bars = ax.bar(x, monthly_energy, color='#2196F3', alpha=0.7, edgecolor='black', linewidth=1)
            
            # Werte auf Balken
            for i, (bar, energy) in enumerate(zip(bars, monthly_energy)):
                if energy > 5:  # Nur wenn Wert groß genug
                    ax.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.5,
                           f'{energy:.0f} kWh',
                           ha='center', va='bottom', fontsize=8)
            
            ax.set_xlabel('Monat', fontsize=11, fontweight='bold')
            ax.set_ylabel('Energieverbrauch [kWh]', fontsize=11, fontweight='bold')
            ax.set_title(f'Pumpenleistung über Betriebszeit\n({pump_power:.0f} W, {total_hours} h/Jahr)', 
                        fontsize=12, fontweight='bold')
            ax.set_xticks(x)
            ax.set_xticklabels(months)
            ax.grid(True, alpha=0.3, axis='y')
            
            # Gesamtverbrauch als Text
            total_energy = sum(monthly_energy)
            ax.text(0.02, 0.98, f'Gesamtverbrauch:\n{total_energy:.0f} kWh/Jahr\n({total_energy * 0.30:.0f} EUR/Jahr)',
                   transform=ax.transAxes, fontsize=9, verticalalignment='top',
                   bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.5))
            
            fig.tight_layout()
            canvas.draw()
        except Exception as e:
            ax.text(0.5, 0.5, f"Fehler beim Erstellen des Diagramms:\n{str(e)}",
                    ha='center', va='center', fontsize=10, color='red')
            ax.axis('off')
            canvas.draw()
    
    def _plot_temperature_spread(self, fig, canvas):
        """Plottet Temperaturspreizung Sole (ΔT vs. Volumenstrom)."""
        fig.clear()
        ax = fig.add_subplot(111)
        
        if not self.hydraulics_result:
            ax.text(0.5, 0.5, "Keine Hydraulik-Berechnung durchgeführt.\n\nBitte zuerst Hydraulik berechnen.",
                    ha='center', va='center', fontsize=12, color='gray')
            ax.axis('off')
            canvas.draw()
            return
        
        try:
            # Hole aktuelle Parameter
            flow = self.hydraulics_result.get('flow', {})
            current_flow = flow.get('volume_flow_m3_h', 2.5)
            
            # Hole Entzugsleistung (Kälteleistung) - ist direkt ein Float in kW
            cold_power = self.hydraulics_result.get('cold_power', 6.0)
            # Prüfe ob cold_power ein Dict oder direkt ein Wert ist
            if isinstance(cold_power, dict):
                extraction_power_kw = cold_power.get('extraction_power_kw', 6.0)
            elif isinstance(cold_power, (int, float)):
                # cold_power ist bereits in kW
                extraction_power_kw = float(cold_power)
            else:
                # Fallback: Berechne aus Wärmeleistung und COP
                try:
                    heat_power_entry = self.entries.get("heat_power")
                    if heat_power_entry:
                        heat_power = float(heat_power_entry.get() if isinstance(heat_power_entry, ttk.Entry) else heat_power_entry or "6.0")
                    else:
                        heat_power = 6.0
                    cop_entry = self.entries.get("heat_pump_cop_heating")
                    if cop_entry:
                        cop = float(cop_entry.get() if isinstance(cop_entry, ttk.Entry) else cop_entry or "4.0")
                    else:
                        cop = 4.0
                    extraction_power_kw = heat_power * (cop - 1) / cop
                except (ValueError, AttributeError, TypeError):
                    extraction_power_kw = 6.0
            
            # Volumenstrom-Bereich
            flow_range = np.linspace(1.0, 5.0, 30)
            
            # Berechne ΔT für verschiedene Volumenströme
            # ΔT = Q / (m_dot * cp) = Q / (ρ * V * cp)
            # Vereinfacht: ΔT = Q / (V * c) mit c ≈ 4 kJ/kgK für Sole
            # Hole Frostschutz-Konzentration sicher
            try:
                antifreeze_entry = self.entries.get("antifreeze_concentration")
                if antifreeze_entry:
                    if isinstance(antifreeze_entry, ttk.Entry):
                        antifreeze_conc = float(antifreeze_entry.get() or "25")
                    else:
                        antifreeze_conc = float(antifreeze_entry or "25")
                else:
                    antifreeze_conc = 25.0
            except (ValueError, AttributeError, TypeError):
                antifreeze_conc = 25.0
            
            props = self.hydraulics_calc._get_fluid_properties(antifreeze_conc)
            density = props['density']  # kg/m³
            cp = props['heat_capacity']  # J/kgK
            
            delta_t_range = []
            for flow_m3h in flow_range:
                # Massenstrom in kg/s
                mass_flow = (flow_m3h / 3600) * density  # kg/s
                # ΔT = Q / (m_dot * cp)
                if mass_flow > 0:
                    delta_t = (extraction_power_kw * 1000) / (mass_flow * cp)  # K
                else:
                    delta_t = 0
                delta_t_range.append(delta_t)
            
            # Plot
            ax.plot(flow_range, delta_t_range, 'b-', linewidth=2.5, label='Temperaturspreizung')
            
            # Aktueller Betriebspunkt
            if current_flow > 0:
                mass_flow = (current_flow / 3600) * density
                current_delta_t = (extraction_power_kw * 1000) / (mass_flow * cp) if mass_flow > 0 else 0
                ax.plot(current_flow, current_delta_t, 'ro', markersize=12,
                       label=f'Betriebspunkt\n(ΔT={current_delta_t:.2f} K)', zorder=5)
            
            # Optimaler Bereich (2-4 K)
            ax.axhspan(2, 4, alpha=0.2, color='green', label='Optimaler Bereich (2-4 K)')
            
            ax.set_xlabel('Volumenstrom [m³/h]', fontsize=11, fontweight='bold')
            ax.set_ylabel('Temperaturspreizung ΔT [K]', fontsize=11, fontweight='bold')
            ax.set_title('Temperaturspreizung Sole (ΔT vs. Volumenstrom)', fontsize=12, fontweight='bold')
            ax.grid(True, alpha=0.3)
            ax.legend(fontsize=9, loc='best')
            ax.set_ylim(0, max(delta_t_range) * 1.1 if delta_t_range else 5)
            
            fig.tight_layout()
            canvas.draw()
        except Exception as e:
            ax.text(0.5, 0.5, f"Fehler beim Erstellen des Diagramms:\n{str(e)}",
                    ha='center', va='center', fontsize=10, color='red')
            ax.axis('off')
            canvas.draw()
    
    def _plot_cop_vs_inlet_temp(self, fig, canvas):
        """Plottet COP vs. Sole-Eintrittstemperatur."""
        fig.clear()
        ax = fig.add_subplot(111)
        
        try:
            # Hole Wärmepumpen-Parameter
            cop_heating = float(self.entries.get("heat_pump_cop_heating", ttk.Entry()).get() or "4.0")
            flow_temp = float(self.entries.get("flow_temperature", ttk.Entry()).get() or "35.0")
            
            # Sole-Eintrittstemperatur-Bereich
            inlet_temp_range = np.linspace(-5, 15, 50)
            
            # Vereinfachte COP-Berechnung: COP steigt mit höherer Eintrittstemperatur
            # COP ≈ COP_nenn * (1 + 0.05 * (T_inlet - T_nenn))
            # T_nenn typischerweise 0°C für Sole/Wasser-WP
            cop_range = []
            for t_inlet in inlet_temp_range:
                # Vereinfachte Formel: COP steigt linear mit Temperatur
                cop = cop_heating * (1 + 0.04 * (t_inlet - 0))
                cop_range.append(max(2.0, min(6.0, cop)))  # Begrenzung auf realistische Werte
            
            # Plot
            ax.plot(inlet_temp_range, cop_range, 'b-', linewidth=2.5, label='COP-Kurve')
            
            # Aktueller Betriebspunkt (falls verfügbar)
            if hasattr(self, 'vdi4640_result') and self.vdi4640_result:
                t_inlet = self.vdi4640_result.t_wp_aus_heating_min
                cop_actual = cop_heating * (1 + 0.04 * (t_inlet - 0))
                cop_actual = max(2.0, min(6.0, cop_actual))
                ax.plot(t_inlet, cop_actual, 'ro', markersize=12,
                       label=f'Betriebspunkt\n(T={t_inlet:.1f}°C, COP={cop_actual:.2f})', zorder=5)
            
            ax.set_xlabel('Sole-Eintrittstemperatur [°C]', fontsize=11, fontweight='bold')
            ax.set_ylabel('COP [-]', fontsize=11, fontweight='bold')
            ax.set_title('COP vs. Sole-Eintrittstemperatur', fontsize=12, fontweight='bold')
            ax.grid(True, alpha=0.3)
            ax.legend(fontsize=9, loc='best')
            
            fig.tight_layout()
            canvas.draw()
        except Exception as e:
            ax.text(0.5, 0.5, f"Fehler beim Erstellen des Diagramms:\n{str(e)}",
                    ha='center', va='center', fontsize=10, color='red')
            ax.axis('off')
            canvas.draw()
    
    def _plot_cop_vs_flow_temp(self, fig, canvas):
        """Plottet COP vs. Vorlauftemperatur."""
        fig.clear()
        ax = fig.add_subplot(111)
        
        try:
            # Hole Wärmepumpen-Parameter
            cop_heating = float(self.entries.get("heat_pump_cop_heating", ttk.Entry()).get() or "4.0")
            flow_temp = float(self.entries.get("flow_temperature", ttk.Entry()).get() or "35.0")
            
            # Vorlauftemperatur-Bereich
            flow_temp_range = np.linspace(25, 55, 50)
            
            # Vereinfachte COP-Berechnung: COP sinkt mit höherer Vorlauftemperatur
            # COP ≈ COP_nenn * (1 - 0.03 * (T_flow - T_nenn))
            # T_nenn typischerweise 35°C für Fußbodenheizung
            cop_range = []
            for t_flow in flow_temp_range:
                # Vereinfachte Formel: COP sinkt linear mit Temperatur
                cop = cop_heating * (1 - 0.025 * (t_flow - 35))
                cop_range.append(max(2.0, min(6.0, cop)))  # Begrenzung auf realistische Werte
            
            # Plot
            ax.plot(flow_temp_range, cop_range, 'r-', linewidth=2.5, label='COP-Kurve')
            
            # Aktueller Betriebspunkt
            cop_actual = cop_heating * (1 - 0.025 * (flow_temp - 35))
            cop_actual = max(2.0, min(6.0, cop_actual))
            ax.plot(flow_temp, cop_actual, 'ro', markersize=12,
                   label=f'Betriebspunkt\n(T={flow_temp:.1f}°C, COP={cop_actual:.2f})', zorder=5)
            
            ax.set_xlabel('Vorlauftemperatur [°C]', fontsize=11, fontweight='bold')
            ax.set_ylabel('COP [-]', fontsize=11, fontweight='bold')
            ax.set_title('COP vs. Vorlauftemperatur', fontsize=12, fontweight='bold')
            ax.grid(True, alpha=0.3)
            ax.legend(fontsize=9, loc='best')
            
            fig.tight_layout()
            canvas.draw()
        except Exception as e:
            ax.text(0.5, 0.5, f"Fehler beim Erstellen des Diagramms:\n{str(e)}",
                    ha='center', va='center', fontsize=10, color='red')
            ax.axis('off')
            canvas.draw()
    
    def _plot_jaz_estimation(self, fig, canvas):
        """Plottet JAZ-Abschätzung (Jahresarbeitszahl)."""
        fig.clear()
        ax = fig.add_subplot(111)
        
        try:
            # Hole Parameter
            cop_heating = float(self.entries.get("heat_pump_cop_heating", ttk.Entry()).get() or "4.0")
            annual_heating = float(self.entries.get("annual_heating", ttk.Entry()).get() or "10000")
            
            # Vereinfachte JAZ-Abschätzung basierend auf COP
            # JAZ ist typischerweise 10-20% niedriger als COP_nenn
            # wegen Teillastbetrieb und verschiedenen Betriebsbedingungen
            jaz_estimated = cop_heating * 0.85  # 15% Abschlag
            
            # Vergleich mit verschiedenen Szenarien
            scenarios = ['Optimistisch\n(COP_nenn)', 'Realistisch\n(JAZ geschätzt)', 'Pessimistisch\n(-20%)']
            values = [cop_heating, jaz_estimated, cop_heating * 0.80]
            colors = ['#4CAF50', '#2196F3', '#FF9800']
            
            # Balkendiagramm
            bars = ax.barh(scenarios, values, color=colors, alpha=0.7, edgecolor='black', linewidth=2)
            
            # Werte auf Balken
            for bar, val in zip(bars, values):
                width = bar.get_width()
                ax.text(width + 0.05, bar.get_y() + bar.get_height()/2,
                       f'{val:.2f}',
                       va='center', fontsize=10, fontweight='bold')
            
            # Energieverbrauch-Annotation
            energy_consumption = annual_heating / jaz_estimated  # kWh
            ax.text(0.02, 0.98, f'JAZ-Abschätzung: {jaz_estimated:.2f}\n\nJahresenergieverbrauch:\n{energy_consumption:.0f} kWh/Jahr\n({energy_consumption * 0.30:.0f} EUR/Jahr)',
                   transform=ax.transAxes, fontsize=9, verticalalignment='top',
                   bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.5))
            
            ax.set_xlabel('COP / JAZ [-]', fontsize=11, fontweight='bold')
            ax.set_title('JAZ-Abschätzung (Jahresarbeitszahl)', fontsize=12, fontweight='bold')
            ax.grid(True, alpha=0.3, axis='x')
            ax.set_xlim(0, max(values) * 1.3)
            
            fig.tight_layout()
            canvas.draw()
        except Exception as e:
            ax.text(0.5, 0.5, f"Fehler beim Erstellen des Diagramms:\n{str(e)}",
                    ha='center', va='center', fontsize=10, color='red')
            ax.axis('off')
            canvas.draw()
    
    def _plot_energy_consumption(self, fig, canvas):
        """Plottet Energieverbrauch-Vergleich (konstant vs. geregelt)."""
        fig.clear()
        ax = fig.add_subplot(111)
        
        if not self.hydraulics_result:
            ax.text(0.5, 0.5, "Keine Hydraulik-Berechnung durchgeführt.\n\nBitte zuerst Hydraulik berechnen.",
                    ha='center', va='center', fontsize=12, color='gray')
            ax.axis('off')
            canvas.draw()
            return
        
        try:
            pump_power = self.hydraulics_result['pump']['electric_power_w']
            hours = 1800  # Standard-Betriebsstunden
            price = 0.30  # EUR/kWh
            
            # Berechne Energieverbrauch
            energy = self.hydraulics_calc.calculate_pump_energy_consumption(
                pump_power, hours, price
            )
            
            # Geregelte Pumpe (30% Einsparung)
            regulated_kwh = energy['annual_kwh'] * 0.7
            regulated_cost = energy['annual_cost_eur'] * 0.7
            
            # 10-Jahres-Kosten
            constant_10y = energy['annual_cost_eur'] * 10
            regulated_10y = regulated_cost * 10
            savings_10y = constant_10y - regulated_10y
            
            # Balkendiagramm
            categories = ['Konstante\nPumpe', 'Geregelte\nPumpe']
            annual_costs = [energy['annual_cost_eur'], regulated_cost]
            colors = ['#F44336', '#4CAF50']
            
            bars = ax.bar(categories, annual_costs, color=colors, alpha=0.7, edgecolor='black', linewidth=2)
            
            # Werte auf Balken
            for bar, cost in zip(bars, annual_costs):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 5,
                       f'{cost:.0f} EUR/Jahr\n({cost/price:.0f} kWh)',
                       ha='center', va='bottom', fontsize=10, fontweight='bold')
            
            # Einsparung annotieren
            savings = energy['annual_cost_eur'] - regulated_cost
            ax.annotate('', xy=(1, regulated_cost), xytext=(0, energy['annual_cost_eur']),
                       arrowprops=dict(arrowstyle='<->', color='blue', lw=2))
            ax.text(0.5, (energy['annual_cost_eur'] + regulated_cost)/2,
                   f'Einsparung:\n{savings:.0f} EUR/Jahr\n({savings_10y:.0f} EUR/10a)',
                   ha='center', va='center', fontsize=10, fontweight='bold',
                   bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow', alpha=0.7))
            
            ax.set_ylabel('Kosten [EUR/Jahr]', fontsize=11, fontweight='bold')
            ax.set_title('Energieverbrauch-Vergleich: Konstante vs. Geregelte Pumpe', 
                        fontsize=12, fontweight='bold')
            ax.grid(True, alpha=0.3, axis='y')
            
            # 10-Jahres-Kosten als Text
            ax.text(0.02, 0.98, f'10-Jahres-Kosten:\nKonstant: {constant_10y:.0f} EUR\nGeregelt: {regulated_10y:.0f} EUR\n\nEinsparung: {savings_10y:.0f} EUR',
                   transform=ax.transAxes, fontsize=9, verticalalignment='top',
                   bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.5))
            
            fig.tight_layout()
            canvas.draw()
        except Exception as e:
            ax.text(0.5, 0.5, f"Fehler beim Erstellen des Diagramms:\n{str(e)}",
                    ha='center', va='center', fontsize=10, color='red')
            ax.axis('off')
            canvas.draw()
    
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
        self.status_var = tk.StringVar(value="Bereit - Professional Edition V3.4.0-beta1.8")
        status_bar = ttk.Label(self.root, textvariable=self.status_var,
                              relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    # =========== AUTO-SAVE ===========

    def _start_auto_save(self):
        """Startet den Auto-Save-Timer."""
        self.root.after(self._auto_save_interval, self._auto_save)

    def _auto_save(self):
        """Speichert das Projekt automatisch, wenn ein Dateipfad bekannt ist."""
        if self._current_file_path:
            try:
                success = self.file_controller.save_to_path(self._current_file_path)
                if success:
                    timestamp = datetime.now().strftime('%H:%M:%S')
                    self.status_var.set(
                        f"💾 Auto-Save: {os.path.basename(self._current_file_path)} "
                        f"({timestamp})")
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(f"Auto-Save Fehler: {e}")
        # Timer neu starten
        self.root.after(self._auto_save_interval, self._auto_save)

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
        # Debounce: Verzögere Berechnung um 500ms, damit nicht bei jedem Tastendruck
        # eine komplette Neuberechnung ausgelöst wird
        if self._hydraulics_debounce_id is not None:
            self.root.after_cancel(self._hydraulics_debounce_id)
        self._hydraulics_debounce_id = self.root.after(500, self._on_parameter_changed_debounced)
    
    def _on_parameter_changed_debounced(self):
        """Tatsächliche Neuberechnung nach Debounce-Verzögerung."""
        self._hydraulics_debounce_id = None
        try:
            self._calculate_hydraulics()
        except Exception:
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
        """Berechnet Verfüllmaterial-Mengen. (Delegiert an CalculationController)"""
        self.calc_controller.calculate_grout_materials()

    def _calculate_hydraulics(self):
        """Berechnet Hydraulik-Parameter. (Delegiert an CalculationController)"""
        self.calc_controller.calculate_hydraulics()

    def _update_energy_analysis(self):
        """Aktualisiert die Energieprognose. (Delegiert an CalculationController)"""
        self.calc_controller.update_energy_analysis()

    def _update_pressure_analysis(self):
        """Aktualisiert die Druckverlust-Analyse. (Delegiert an CalculationController)"""
        self.calc_controller.update_pressure_analysis()

    def _update_pump_analysis(self):
        """Aktualisiert die Pumpen-Empfehlungen. (Delegiert an CalculationController)"""
        self.calc_controller.update_pump_analysis()

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
        """Prüft Volumenstrom. (Delegiert an CalculationController)"""
        return self.calc_controller._check_flow_rate_warnings(
            heat_power_kw, flow_rate_m3s, num_boreholes,
            current_delta_t, antifreeze_conc, extraction_power)

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
            lat, lon = None, None

            if result['choice'] == 'address' and result['address']:
                address = result['address']
                if "z.B." not in address:
                    self.status_var.set("⏳ Lade Klimadaten von PVGIS...")
                    self.root.update()
                    # Erst Geocoding, dann Klimadaten
                    coords = self.pvgis_client.get_location_from_address(address)
                    if coords:
                        lat, lon = coords
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
                # Koordinaten in climate_data speichern
                if lat is not None and lon is not None:
                    data['latitude'] = lat
                    data['longitude'] = lon
                self.climate_data = data

                # Karte aktualisieren
                if lat is not None and lon is not None:
                    self._update_map_position(lat, lon)

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
        """Führt die Hauptberechnung durch. (Delegiert an CalculationController)"""
        self.calc_controller.run_calculation()

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
        """Zeigt Ergebnisse an. (Delegiert an CalculationController)"""
        self.calc_controller.display_results()

    def _plot_results(self):
        """Aktualisiert alle Diagramme im neuen Diagramm-Tab."""
        # Aktualisiere alle Diagramme im neuen System
        if hasattr(self, 'diagram_figures'):
            self._update_all_diagrams()
    
    def _export_pdf(self):
        """Exportiert PDF. (Delegiert an CalculationController)"""
        self.calc_controller.export_pdf()

    def _export_results(self):
        """Exportiert Text. (Delegiert an CalculationController)"""
        self.calc_controller.export_results_text()

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
Professional Edition V3.4.0-beta1.8

Für eine vollständige Liste aller Änderungen und neuen Features
siehe bitte den Changelog:

CHANGELOG_V3.4.0-beta1.md

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
        """Lädt Standard-Rohre aus XML-Datenbank (inkl. DN40, DN50, Coaxial)."""
        try:
            # Lade aus XML-Datenbank (enthält DN20, DN25, DN32, DN40, DN50)
            all_pipes = list(self.pipe_db.pipes.values())
            
            # Sortiere nach Durchmesser
            all_pipes.sort(key=lambda p: p.dimensions.outer_diameter)
            
            # Konvertiere Pipe-Objekte zu kompatiblen Format für GUI
            # Erstelle kompatible Pipe-Objekte (mit name, diameter_m, thickness_m, thermal_conductivity)
            class CompatiblePipe:
                def __init__(self, pipe):
                    self.name = pipe.name
                    self.diameter_m = pipe.dimensions.outer_diameter
                    self.thickness_m = pipe.dimensions.wall_thickness
                    self.thermal_conductivity = pipe.thermal_conductivity
            
            self.pipes = [CompatiblePipe(p) for p in all_pipes]
            
            # Setze Dropdown-Werte
            if hasattr(self, 'pipe_type_combo'):
                self.pipe_type_combo['values'] = [p.name for p in self.pipes]
                
                # Setze Standard (DN32 falls verfügbar, sonst erstes)
                default_set = False
                for i, pipe in enumerate(self.pipes):
                    if "DN32" in pipe.name or "32" in pipe.name:
                        self.pipe_type_combo.current(i)
                        self._on_pipe_selected(None)
                        default_set = True
                        break
                
                if not default_set and self.pipes:
                    self.pipe_type_combo.current(0)
                    self._on_pipe_selected(None)
            
            self.status_var.set(f"✓ {len(self.pipes)} Rohrtypen geladen (inkl. DN40, DN50)")
            
        except Exception as e:
            print(f"Fehler beim Laden der Rohr-Datenbank: {e}")
            # Fallback: Lade aus pipe.txt falls vorhanden
            pipe_file = os.path.join(os.path.dirname(__file__), "..", "import", "pipe.txt")
            if os.path.exists(pipe_file):
                try:
                    self.pipes = self.pipe_parser.parse_file(pipe_file)
                    if hasattr(self, 'pipe_type_combo'):
                        self.pipe_type_combo['values'] = [p.name for p in self.pipes]
                    self.status_var.set(f"✓ {len(self.pipes)} Rohrtypen geladen (Fallback)")
                except Exception as e2:
                    print(f"Fehler beim Fallback-Laden: {e2}")
    
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
    
    # ─── Karten-Callbacks ───────────────────────────────────

    def _update_map_position(self, lat: float, lon: float, zoom: int = 15):
        """Aktualisiert die OSM-Karte mit neuen Koordinaten."""
        if hasattr(self, 'map_widget') and self.map_widget:
            try:
                self.map_widget.set_position(lat, lon, zoom=zoom)
            except Exception as e:
                logger.warning(f"Kartenaktualisierung fehlgeschlagen: {e}")

    def _on_map_position_changed(self, lat: float, lon: float):
        """Callback wenn der Benutzer den Kartenmarker verschiebt."""
        # Koordinaten in climate_data aktualisieren
        if self.climate_data is None:
            self.climate_data = {}
        if isinstance(self.climate_data, dict):
            self.climate_data['latitude'] = lat
            self.climate_data['longitude'] = lon

        # Bohranzeige-Tab Koordinaten immer aktualisieren (Standort ist zentral)
        if hasattr(self, 'bohranzeige_tab'):
            self.bohranzeige_tab.koordinaten_label.configure(
                text=f"Breite: {lat:.4f}°  |  Länge: {lon:.4f}°",
                foreground="#1f4788"
            )

        self.status_var.set(f"📍 Standort: {lat:.5f}°, {lon:.5f}°")

    # ─── Bohranzeige Callbacks ──────────────────────────────
    
    def _get_bohranzeige_data(self) -> Dict[str, Any]:
        """Sammelt aktuelle Berechnungsdaten für die Bohranzeige."""
        if not self.result and not self.vdi4640_result:
            return {}
        
        # Technische Daten aus aktueller Berechnung
        try:
            num_bh = int(float(self.borehole_entries.get("num_boreholes", ttk.Entry()).get() or "1"))
        except (ValueError, AttributeError):
            num_bh = 1
        
        # Bohrtiefe ermitteln
        tiefe = 0
        if self.vdi4640_result and hasattr(self.vdi4640_result, 'required_depth'):
            tiefe = self.vdi4640_result.required_depth
        elif self.result and hasattr(self.result, 'required_depth'):
            tiefe = self.result.required_depth
        
        # Sondentyp
        sondentyp = self.pipe_config_var.get() if hasattr(self, 'pipe_config_var') else 'double-u'
        
        # Verfüllmaterial
        verfuellmaterial = ''
        if hasattr(self, 'grout_material_var'):
            verfuellmaterial = self.grout_material_var.get()
        
        # Fluid-Infos
        fluid_typ = ''
        if hasattr(self, 'fluid_var'):
            fluid_typ = self.fluid_var.get()
        
        # COP
        try:
            cop = float(self.entries.get("heat_pump_cop", ttk.Entry()).get() or "4.0")
        except (ValueError, AttributeError):
            cop = 4.0
        
        technik = {
            'anzahl_bohrungen': f"{num_bh}",
            'bohrtiefe_m': f"{tiefe:.1f} m",
            'gesamtbohrmeter': f"{tiefe * num_bh:.1f} m",
            'bohrdurchmesser_mm': f"{float(self.entries.get('borehole_diameter', ttk.Entry()).get() or '152'):.0f} mm",
            'abstand_bohrungen_m': f"{float(self.borehole_entries.get('spacing_between', ttk.Entry()).get() or '6'):.1f} m",
            'sondentyp': sondentyp,
            'rohrmaterial': self.pipe_type_var.get() if hasattr(self, 'pipe_type_var') else 'PE 100 RC',
            'rohrdurchmesser_mm': f"{float(self.entries.get('pipe_outer_diameter', ttk.Entry()).get() or '32'):.1f} mm",
            'wandstaerke_mm': f"{float(self.entries.get('pipe_thickness', ttk.Entry()).get() or '3'):.1f} mm",
            'verfuellmaterial': verfuellmaterial,
            'verfuell_lambda': f"{float(self.entries.get('grout_thermal_cond', ttk.Entry()).get() or '2.0'):.2f} W/(m·K)",
            'fluid_typ': fluid_typ,
            'heizleistung_kw': f"{float(self.entries.get('peak_heating', ttk.Entry()).get() or '0'):.1f} kW",
            'kuehlleistung_kw': f"{float(self.entries.get('peak_cooling', ttk.Entry()).get() or '0'):.1f} kW",
            'jahres_heizenergie_kwh': f"{float(self.entries.get('annual_heating', ttk.Entry()).get() or '0'):,.0f} kWh",
            'jahres_kuehlenergie_kwh': f"{float(self.entries.get('annual_cooling', ttk.Entry()).get() or '0'):,.0f} kWh",
            'cop': f"{cop:.1f}",
        }
        
        # Koordinaten aus Klimadaten
        koordinaten = {}
        if self.climate_data and isinstance(self.climate_data, dict):
            koordinaten = {
                'latitude': self.climate_data.get('latitude', ''),
                'longitude': self.climate_data.get('longitude', ''),
            }
        
        # Gewässerschutz
        gewaesserschutz = {
            'bodentyp': self.soil_type_var.get() if hasattr(self, 'soil_type_var') else '',
            'lambda_boden': float(self.entries.get('ground_thermal_cond', ttk.Entry()).get() or '0'),
            'bodentemperatur': float(self.entries.get('ground_temp', ttk.Entry()).get() or '0'),
        }
        
        # Projektdaten
        projekt = {
            'kunde': self.project_entries.get('customer_name', ttk.Entry()).get() if 'customer_name' in self.project_entries else '',
            'adresse': self.project_entries.get('address', ttk.Entry()).get() if 'address' in self.project_entries else '',
            'plz': self.project_entries.get('postal_code', ttk.Entry()).get() if 'postal_code' in self.project_entries else '',
            'ort': self.project_entries.get('city', ttk.Entry()).get() if 'city' in self.project_entries else '',
        }
        
        return {
            'technik': technik,
            'koordinaten': koordinaten,
            'gewaesserschutz': gewaesserschutz,
            'projekt': projekt,
        }
    
    def _export_bohranzeige_pdf(self, data: Dict[str, Any]):
        """Exportiert die Bohranzeige als PDF. (Delegiert an FileController)"""
        self.file_controller.export_bohranzeige_pdf(data)

    def _export_get_file(self):
        """Exportiert Projekt als .get Datei. (Delegiert an FileController)"""
        self.file_controller.export_get_file()

    def _import_get_file(self):
        """Importiert ein .get Projekt. (Delegiert an FileController)"""
        self.file_controller.import_get_file()

    def _populate_from_get_data(self, data: Dict[str, Any]):
        """Füllt GUI mit Daten. (Delegiert an FileController)"""
        self.file_controller._populate_from_get_data(data)

    def _populate_borefield_tab(self, borefield_data: Dict[str, Any]):
        """Füllt Bohrfeld-Tab. (Delegiert an FileController)"""
        self.file_controller.populate_borefield_tab(borefield_data)

    def _set_entry(self, key: str, value: Any):
        """Setzt Entry-Werte. (Delegiert an FileController)"""
        self.file_controller._set_entry(key, value)

def main():
    """Haupteinstiegspunkt."""
    root = tk.Tk()
    app = GeothermieGUIProfessional(root)
    root.mainloop()


if __name__ == "__main__":
    main()

