"""Erweiterte GUI mit Projektdaten, Bohrfeld und PDF-Export."""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
from typing import Optional
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.patches import Circle, Rectangle
import numpy as np

from parsers import PipeParser, EEDParser
from calculations import BoreholeCalculator
from utils import PDFReportGenerator
from gui.tooltips import InfoButton, ToolTip
from data.soil_types import SoilTypeDB
from data.grout_materials import GroutMaterialDB
from utils.pvgis_api import get_climate_data


class GeothermieGUIExtended:
    """Erweiterte GUI mit Projektdaten und PDF-Export."""
    
    def __init__(self, root):
        """Initialisiert die erweiterte GUI."""
        self.root = root
        self.root.title("Geothermie Erdsonden-Berechnungstool - Professional Edition")
        self.root.geometry("1600x1000")
        
        # Parser, Rechner und PDF-Generator
        self.pipe_parser = PipeParser()
        self.eed_parser = EEDParser()
        self.calculator = BoreholeCalculator()
        self.pdf_generator = PDFReportGenerator()
        
        # Daten
        self.pipes = []
        self.current_config = None
        self.result = None
        self.current_params = {}
        
        # GUI aufbauen
        self._create_menu()
        self._create_main_layout()
        self._create_status_bar()
        
        # Lade Standard-Rohrtypen
        self._load_default_pipes()
    
    def _create_menu(self):
        """Erstellt die Menüleiste."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # Datei-Menü
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Datei", menu=file_menu)
        file_menu.add_command(label="Pipe.txt laden", command=self._load_pipe_file)
        file_menu.add_command(label="EED .dat laden", command=self._load_eed_file)
        file_menu.add_separator()
        file_menu.add_command(label="PDF-Bericht erstellen", command=self._export_pdf, accelerator="Ctrl+P")
        file_menu.add_command(label="Ergebnis als Text exportieren", command=self._export_results)
        file_menu.add_separator()
        file_menu.add_command(label="Beenden", command=self.root.quit)
        
        # Hilfe-Menü
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Hilfe", menu=help_menu)
        help_menu.add_command(label="Über", command=self._show_about)
        
        # Keyboard Shortcuts
        self.root.bind('<Control-p>', lambda e: self._export_pdf())
    
    def _create_main_layout(self):
        """Erstellt das Hauptlayout."""
        # Hauptcontainer mit Notebook (Tabs)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Tab 1: Eingabe
        self.input_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.input_frame, text="📝 Eingabe")
        self._create_input_tab()
        
        # Tab 2: Ergebnisse
        self.results_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.results_frame, text="📊 Ergebnisse")
        self._create_results_tab()
        
        # Tab 3: Visualisierung
        self.viz_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.viz_frame, text="📈 Diagramme")
        self._create_visualization_tab()
    
    def _create_input_tab(self):
        """Erstellt den erweiterten Eingabe-Tab."""
        # Hauptcontainer mit zwei Spalten
        main_container = ttk.Frame(self.input_frame)
        main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Linke Spalte: Scrollbare Eingabe
        left_frame = ttk.Frame(main_container)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Scrollbarer Container
        canvas = tk.Canvas(left_frame)
        scrollbar = ttk.Scrollbar(left_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Rechte Spalte: Bohrloch-Grafik
        right_frame = ttk.Frame(main_container, relief=tk.RAISED, borderwidth=2)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(10, 0))
        
        # Eingabefelder linksseitig
        row = 0
        self.entries = {}
        self.project_entries = {}
        self.borehole_entries = {}
        
        # === PROJEKTINFORMATIONEN ===
        ttk.Label(scrollable_frame, text="🏢 Projektinformationen", 
                 font=("Arial", 14, "bold"), foreground="#1f4788").grid(
            row=row, column=0, columnspan=2, sticky="w", padx=10, pady=(10, 5)
        )
        row += 1
        
        self._add_project_field(scrollable_frame, row, "Projektname:", "project_name", "")
        row += 1
        self._add_project_field(scrollable_frame, row, "Kundenname:", "customer_name", "")
        row += 1
        self._add_project_field(scrollable_frame, row, "Straße + Nr.:", "address", "")
        row += 1
        self._add_project_field(scrollable_frame, row, "PLZ:", "postal_code", "")
        row += 1
        self._add_project_field(scrollable_frame, row, "Ort:", "city", "")
        row += 1
        
        # === BOHRFELD-KONFIGURATION ===
        ttk.Label(scrollable_frame, text="🎯 Bohrfeld-Konfiguration", 
                 font=("Arial", 14, "bold"), foreground="#1f4788").grid(
            row=row, column=0, columnspan=2, sticky="w", padx=10, pady=(15, 5)
        )
        row += 1
        
        self._add_borehole_field(scrollable_frame, row, "Anzahl Bohrungen:", "num_boreholes", "1", "num_boreholes")
        row += 1
        self._add_borehole_field(scrollable_frame, row, "Abstand zwischen Bohrungen [m]:", "spacing_between", "6")
        row += 1
        self._add_borehole_field(scrollable_frame, row, "Abstand zum Grundstücksrand [m]:", "spacing_property", "3")
        row += 1
        self._add_borehole_field(scrollable_frame, row, "Abstand zum Gebäude [m]:", "spacing_building", "3")
        row += 1
        
        # === BODENEIGENSCHAFTEN ===
        ttk.Label(scrollable_frame, text="🌍 Bodeneigenschaften", 
                 font=("Arial", 12, "bold")).grid(
            row=row, column=0, columnspan=2, sticky="w", padx=10, pady=(15, 5)
        )
        row += 1
        
        # Bodentyp-Dropdown
        ttk.Label(scrollable_frame, text="Bodentyp:").grid(row=row, column=0, sticky="w", padx=10, pady=5)
        self.soil_type_var = tk.StringVar(value="Sand")
        self.soil_type_combo = ttk.Combobox(
            scrollable_frame,
            textvariable=self.soil_type_var,
            values=SoilTypeDB.get_all_names(),
            state="readonly",
            width=30
        )
        self.soil_type_combo.grid(row=row, column=1, sticky="w", padx=10, pady=5)
        self.soil_type_combo.bind("<<ComboboxSelected>>", self._on_soil_type_selected)
        row += 1
        
        self._add_input_field(scrollable_frame, row, "Wärmeleitfähigkeit Boden [W/m·K]:", "ground_thermal_cond", "1.8", "ground_thermal_cond")
        row += 1
        self._add_input_field(scrollable_frame, row, "Wärmekapazität Boden [J/m³·K]:", "ground_heat_cap", "2400000")
        row += 1
        self._add_input_field(scrollable_frame, row, "Ungestörte Bodentemperatur [°C]:", "ground_temp", "10.0")
        row += 1
        self._add_input_field(scrollable_frame, row, "Geothermischer Gradient [K/m]:", "geothermal_gradient", "0.03")
        row += 1
        
        # PVGIS-Button für Klimadaten
        pvgis_button = ttk.Button(
            scrollable_frame,
            text="🌐 Klimadaten von PVGIS laden",
            command=self._load_climate_data
        )
        pvgis_button.grid(row=row, column=0, columnspan=2, padx=10, pady=10)
        row += 1
        
        # === BOHRLOCH-KONFIGURATION ===
        ttk.Label(scrollable_frame, text="⚙️ Bohrloch-Konfiguration", 
                 font=("Arial", 12, "bold")).grid(
            row=row, column=0, columnspan=2, sticky="w", padx=10, pady=(15, 5)
        )
        row += 1
        
        self._add_input_field(scrollable_frame, row, "Bohrloch-Durchmesser [mm]:", "borehole_diameter", "152", "borehole_diameter")
        row += 1
        
        ttk.Label(scrollable_frame, text="Rohrkonfiguration:").grid(row=row, column=0, sticky="w", padx=10, pady=5)
        self.pipe_config_var = tk.StringVar(value="4-rohr-dual")
        pipe_config_combo = ttk.Combobox(
            scrollable_frame, 
            textvariable=self.pipe_config_var,
            values=["single-u", "double-u", "4-rohr-dual", "4-rohr-4verbinder", "coaxial"],
            state="readonly",
            width=30
        )
        pipe_config_combo.grid(row=row, column=1, sticky="w", padx=10, pady=5)
        row += 1
        
        # === ROHR-EIGENSCHAFTEN ===
        ttk.Label(scrollable_frame, text="🔧 Rohr-Eigenschaften", 
                 font=("Arial", 12, "bold")).grid(
            row=row, column=0, columnspan=2, sticky="w", padx=10, pady=(15, 5)
        )
        row += 1
        
        ttk.Label(scrollable_frame, text="Rohrtyp:").grid(row=row, column=0, sticky="w", padx=10, pady=5)
        self.pipe_type_var = tk.StringVar()
        self.pipe_type_combo = ttk.Combobox(
            scrollable_frame, 
            textvariable=self.pipe_type_var,
            state="readonly",
            width=30
        )
        self.pipe_type_combo.grid(row=row, column=1, sticky="w", padx=10, pady=5)
        self.pipe_type_combo.bind("<<ComboboxSelected>>", self._on_pipe_selected)
        row += 1
        
        self._add_input_field(scrollable_frame, row, "Rohr Außendurchmesser [m]:", "pipe_outer_diameter", "0.032")
        row += 1
        self._add_input_field(scrollable_frame, row, "Rohr Wandstärke [m]:", "pipe_thickness", "0.003")
        row += 1
        self._add_input_field(scrollable_frame, row, "Rohr Wärmeleitfähigkeit [W/m·K]:", "pipe_thermal_cond", "0.42")
        row += 1
        self._add_input_field(scrollable_frame, row, "Schenkelabstand [mm]:", "shank_spacing", "65", "shank_spacing")
        row += 1
        
        # === VERFÜLLUNG ===
        ttk.Label(scrollable_frame, text="🏗️ Verfüllung", 
                 font=("Arial", 12, "bold")).grid(
            row=row, column=0, columnspan=2, sticky="w", padx=10, pady=(15, 5)
        )
        row += 1
        
        # Verfüllmaterial-Dropdown
        ttk.Label(scrollable_frame, text="Verfüllmaterial:").grid(row=row, column=0, sticky="w", padx=10, pady=5)
        self.grout_material_var = tk.StringVar(value="Zement-Bentonit verbessert")
        self.grout_material_combo = ttk.Combobox(
            scrollable_frame,
            textvariable=self.grout_material_var,
            values=GroutMaterialDB.get_all_names(),
            state="readonly",
            width=30
        )
        self.grout_material_combo.grid(row=row, column=1, sticky="w", padx=10, pady=5)
        self.grout_material_combo.bind("<<ComboboxSelected>>", self._on_grout_material_selected)
        row += 1
        
        self._add_input_field(scrollable_frame, row, "Wärmeleitfähigkeit Verfüllung [W/m·K]:", "grout_thermal_cond", "1.3", "grout_thermal_cond")
        row += 1
        
        # === WÄRMETRÄGERFLÜSSIGKEIT ===
        ttk.Label(scrollable_frame, text="💧 Wärmeträgerflüssigkeit", 
                 font=("Arial", 12, "bold")).grid(
            row=row, column=0, columnspan=2, sticky="w", padx=10, pady=(15, 5)
        )
        row += 1
        
        self._add_input_field(scrollable_frame, row, "Volumenstrom [m³/s]:", "fluid_flow_rate", "0.0005")
        row += 1
        self._add_input_field(scrollable_frame, row, "Wärmeleitfähigkeit [W/m·K]:", "fluid_thermal_cond", "0.48")
        row += 1
        self._add_input_field(scrollable_frame, row, "Wärmekapazität [J/kg·K]:", "fluid_heat_cap", "3800")
        row += 1
        self._add_input_field(scrollable_frame, row, "Dichte [kg/m³]:", "fluid_density", "1030")
        row += 1
        self._add_input_field(scrollable_frame, row, "Viskosität [Pa·s]:", "fluid_viscosity", "0.004")
        row += 1
        
        # === LASTEN ===
        ttk.Label(scrollable_frame, text="🔥 Heiz- und Kühllast", 
                 font=("Arial", 12, "bold")).grid(
            row=row, column=0, columnspan=2, sticky="w", padx=10, pady=(15, 5)
        )
        row += 1
        
        self._add_input_field(scrollable_frame, row, "Jahres-Heizenergie [kWh]:", "annual_heating", "12000.0", "annual_heating")
        row += 1
        self._add_input_field(scrollable_frame, row, "Jahres-Kühlenergie [kWh]:", "annual_cooling", "0.0")
        row += 1
        self._add_input_field(scrollable_frame, row, "Heiz-Spitzenlast [kW]:", "peak_heating", "6.0")
        row += 1
        self._add_input_field(scrollable_frame, row, "Kühl-Spitzenlast [kW]:", "peak_cooling", "0.0")
        row += 1
        self._add_input_field(scrollable_frame, row, "Wärmepumpen-COP:", "heat_pump_cop", "4.0", "cop")
        row += 1
        
        # === TEMPERATURANFORDERUNGEN ===
        ttk.Label(scrollable_frame, text="🌡️ Temperaturanforderungen", 
                 font=("Arial", 12, "bold")).grid(
            row=row, column=0, columnspan=2, sticky="w", padx=10, pady=(15, 5)
        )
        row += 1
        
        self._add_input_field(scrollable_frame, row, "Min. Fluidtemperatur [°C]:", "min_fluid_temp", "-2.0")
        row += 1
        self._add_input_field(scrollable_frame, row, "Max. Fluidtemperatur [°C]:", "max_fluid_temp", "15.0")
        row += 1
        
        # === SIMULATION ===
        ttk.Label(scrollable_frame, text="⏱️ Simulation", 
                 font=("Arial", 12, "bold")).grid(
            row=row, column=0, columnspan=2, sticky="w", padx=10, pady=(15, 5)
        )
        row += 1
        
        self._add_input_field(scrollable_frame, row, "Simulationsdauer [Jahre]:", "simulation_years", "25")
        row += 1
        self._add_input_field(scrollable_frame, row, "Startwert Bohrtiefe [m]:", "initial_depth", "100")
        row += 1
        
        # Berechnen-Button
        button_frame = ttk.Frame(scrollable_frame)
        button_frame.grid(row=row, column=0, columnspan=2, pady=20, padx=10)
        
        calc_button = ttk.Button(
            button_frame, 
            text="🚀 Berechnung starten",
            command=self._run_calculation,
            width=25
        )
        calc_button.pack(side=tk.LEFT, padx=5)
        
        pdf_button = ttk.Button(
            button_frame,
            text="📄 PDF-Bericht erstellen",
            command=self._export_pdf,
            width=25
        )
        pdf_button.pack(side=tk.LEFT, padx=5)
        
        # === RECHTE SPALTE: Bohrloch-Grafik ===
        self._create_borehole_preview(right_frame)
    
    def _create_borehole_preview(self, parent):
        """Erstellt die Bohrloch-Vorschau-Grafik."""
        ttk.Label(parent, text="Bohrloch-Schema", 
                 font=("Arial", 12, "bold")).pack(pady=10)
        
        # Matplotlib Figure für Vorschau
        self.preview_fig = Figure(figsize=(5, 7))
        self.preview_ax = self.preview_fig.add_subplot(111)
        self.preview_canvas = FigureCanvasTkAgg(self.preview_fig, master=parent)
        self.preview_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Initial-Grafik
        self._update_borehole_preview()
    
    def _update_borehole_preview(self):
        """Aktualisiert die Bohrloch-Vorschau."""
        self.preview_ax.clear()
        
        # Standard-Werte
        bh_diameter = 0.152
        pipe_diameter = 0.032
        
        # Skalierung
        scale = 100
        bh_radius = (bh_diameter / 2) * scale
        pipe_radius = (pipe_diameter / 2) * scale
        
        # Bohrloch
        borehole = Circle((0, 0), bh_radius, facecolor='#d9d9d9', 
                         edgecolor='black', linewidth=2)
        self.preview_ax.add_patch(borehole)
        
        # 4 Rohre
        positions = [
            (-bh_radius*0.5, bh_radius*0.5),
            (bh_radius*0.5, bh_radius*0.5),
            (-bh_radius*0.5, -bh_radius*0.5),
            (bh_radius*0.5, -bh_radius*0.5)
        ]
        
        colors = ['#ff6b6b', '#4ecdc4', '#ff6b6b', '#4ecdc4']
        
        for (x, y), color in zip(positions, colors):
            pipe = Circle((x, y), pipe_radius*1.5, facecolor=color, 
                         edgecolor='black', linewidth=1, alpha=0.8)
            self.preview_ax.add_patch(pipe)
        
        # Beschriftungen
        self.preview_ax.text(0, -bh_radius*1.5, f'Ø {bh_diameter*1000:.0f} mm',
                           ha='center', fontsize=10, fontweight='bold')
        self.preview_ax.text(0, bh_radius*1.8, '4-Rohr-System',
                           ha='center', fontsize=11, fontweight='bold')
        
        self.preview_ax.set_xlim(-bh_radius*2, bh_radius*2)
        self.preview_ax.set_ylim(-bh_radius*2, bh_radius*2.5)
        self.preview_ax.set_aspect('equal')
        self.preview_ax.axis('off')
        
        self.preview_canvas.draw()
    
    def _add_project_field(self, parent, row, label, key, default_value):
        """Fügt ein Projektdaten-Feld hinzu."""
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=10, pady=5)
        entry = ttk.Entry(parent, width=32)
        entry.insert(0, default_value)
        entry.grid(row=row, column=1, sticky="w", padx=10, pady=5)
        self.project_entries[key] = entry
    
    def _add_borehole_field(self, parent, row, label, key, default_value, help_key=None):
        """Fügt ein Bohrfeld-Parameter-Feld mit optionalem Info-Button hinzu."""
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=10, pady=5)
        entry = ttk.Entry(parent, width=32)
        entry.insert(0, default_value)
        entry.grid(row=row, column=1, sticky="w", padx=10, pady=5)
        self.borehole_entries[key] = entry
        
        # Info-Button hinzufügen, wenn help_key vorhanden
        if help_key:
            InfoButton.create_info_button(parent, row, 2, help_key)
    
    def _add_input_field(self, parent, row, label, key, default_value, help_key=None):
        """Fügt ein Eingabefeld mit optionalem Info-Button hinzu."""
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=10, pady=5)
        entry = ttk.Entry(parent, width=32)
        entry.insert(0, default_value)
        entry.grid(row=row, column=1, sticky="w", padx=10, pady=5)
        self.entries[key] = entry
        
        # Info-Button hinzufügen, wenn help_key vorhanden
        if help_key:
            InfoButton.create_info_button(parent, row, 2, help_key)
    
    def _create_results_tab(self):
        """Erstellt den Ergebnisse-Tab."""
        # Scrollbarer Text-Widget
        text_frame = ttk.Frame(self.results_frame)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.results_text = tk.Text(
            text_frame, 
            wrap=tk.WORD,
            font=("Courier", 10),
            yscrollcommand=scrollbar.set
        )
        self.results_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.results_text.yview)
        
        # Initial-Text
        self.results_text.insert("1.0", "Keine Berechnung durchgeführt.\n\nBitte Parameter eingeben und Berechnung starten.")
        self.results_text.config(state=tk.DISABLED)
    
    def _create_visualization_tab(self):
        """Erstellt den Visualisierungs-Tab."""
        # Matplotlib Figure
        self.fig = Figure(figsize=(14, 8))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.viz_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    def _create_status_bar(self):
        """Erstellt die Statusleiste."""
        self.status_var = tk.StringVar(value="Bereit - Bitte Projektdaten und Parameter eingeben")
        status_bar = ttk.Label(
            self.root, 
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def _load_default_pipes(self):
        """Lädt Standard-Rohrtypen."""
        default_pipe_file = os.path.join(os.path.dirname(__file__), "..", "Material", "pipe.txt")
        if os.path.exists(default_pipe_file):
            try:
                self.pipes = self.pipe_parser.parse_file(default_pipe_file)
                self._update_pipe_combo()
                # Setze PE 100 RC als Standard
                for i, pipe in enumerate(self.pipes):
                    if "PE 100 RC DN32" in pipe.name and "Dual" in pipe.name:
                        self.pipe_type_combo.current(i)
                        self._on_pipe_selected(None)
                        break
                self.status_var.set(f"✓ {len(self.pipes)} Rohrtypen geladen (inkl. PE 100 RC)")
            except Exception as e:
                print(f"Fehler beim Laden der Standard-Rohre: {e}")
    
    def _load_pipe_file(self):
        """Lädt eine pipe.txt Datei."""
        filename = filedialog.askopenfilename(
            title="Pipe.txt öffnen",
            filetypes=[("Text-Dateien", "*.txt"), ("Alle Dateien", "*.*")]
        )
        if filename:
            try:
                self.pipes = self.pipe_parser.parse_file(filename)
                self._update_pipe_combo()
                self.status_var.set(f"✓ {len(self.pipes)} Rohrtypen aus {os.path.basename(filename)} geladen")
                messagebox.showinfo("Erfolg", f"{len(self.pipes)} Rohrtypen wurden geladen.")
            except Exception as e:
                messagebox.showerror("Fehler", f"Fehler beim Laden: {str(e)}")
    
    def _load_eed_file(self):
        """Lädt eine EED .dat Datei."""
        filename = filedialog.askopenfilename(
            title="EED .dat öffnen",
            filetypes=[("DAT-Dateien", "*.dat"), ("Alle Dateien", "*.*")]
        )
        if filename:
            try:
                config = self.eed_parser.parse_file(filename)
                self._populate_from_eed_config(config)
                self.status_var.set(f"✓ EED-Konfiguration aus {os.path.basename(filename)} geladen")
                messagebox.showinfo("Erfolg", "EED-Konfiguration wurde geladen.")
            except Exception as e:
                messagebox.showerror("Fehler", f"Fehler beim Laden: {str(e)}")
    
    def _populate_from_eed_config(self, config):
        """Füllt Eingabefelder mit EED-Konfiguration."""
        # Bodeneigenschaften
        self.entries["ground_thermal_cond"].delete(0, tk.END)
        self.entries["ground_thermal_cond"].insert(0, str(config.thermal_conductivity_ground))
        
        self.entries["ground_heat_cap"].delete(0, tk.END)
        self.entries["ground_heat_cap"].insert(0, str(config.heat_capacity))
        
        self.entries["ground_temp"].delete(0, tk.END)
        self.entries["ground_temp"].insert(0, str(config.init_ground_surface_temp))
        
        # Bohrloch
        self.entries["borehole_diameter"].delete(0, tk.END)
        self.entries["borehole_diameter"].insert(0, str(config.borehole_diameter))
        
        # Rohr
        if config.u_pipe_diameter > 0:
            self.entries["pipe_outer_diameter"].delete(0, tk.END)
            self.entries["pipe_outer_diameter"].insert(0, str(config.u_pipe_diameter))
            
            self.entries["pipe_thickness"].delete(0, tk.END)
            self.entries["pipe_thickness"].insert(0, str(config.u_pipe_thickness))
            
            self.entries["pipe_thermal_cond"].delete(0, tk.END)
            self.entries["pipe_thermal_cond"].insert(0, str(config.u_pipe_thermal_conductivity))
            
            self.entries["shank_spacing"].delete(0, tk.END)
            self.entries["shank_spacing"].insert(0, str(config.u_pipe_shank_space))
        
        # Verfüllung
        self.entries["grout_thermal_cond"].delete(0, tk.END)
        self.entries["grout_thermal_cond"].insert(0, str(config.thermal_conductivity_fill))
        
        # Fluid
        if config.hc_thermal_conductivity > 0:
            self.entries["fluid_thermal_cond"].delete(0, tk.END)
            self.entries["fluid_thermal_cond"].insert(0, str(config.hc_thermal_conductivity))
            
            self.entries["fluid_heat_cap"].delete(0, tk.END)
            self.entries["fluid_heat_cap"].insert(0, str(config.hc_heat_capacity))
            
            self.entries["fluid_density"].delete(0, tk.END)
            self.entries["fluid_density"].insert(0, str(config.hc_density))
            
            self.entries["fluid_viscosity"].delete(0, tk.END)
            self.entries["fluid_viscosity"].insert(0, str(abs(config.hc_viscosity)))
        
        # Lasten
        self.entries["annual_heating"].delete(0, tk.END)
        self.entries["annual_heating"].insert(0, str(config.annual_heat_load))
        
        self.entries["annual_cooling"].delete(0, tk.END)
        self.entries["annual_cooling"].insert(0, str(config.annual_cool_load))
        
        self.entries["heat_pump_cop"].delete(0, tk.END)
        self.entries["heat_pump_cop"].insert(0, str(config.spf_heat))
        
        # Temperaturanforderungen
        self.entries["min_fluid_temp"].delete(0, tk.END)
        self.entries["min_fluid_temp"].insert(0, str(config.tfluid_min_required))
        
        self.entries["max_fluid_temp"].delete(0, tk.END)
        self.entries["max_fluid_temp"].insert(0, str(config.tfluid_max_required))
    
    def _update_pipe_combo(self):
        """Aktualisiert die Rohrtyp-Combobox."""
        if self.pipes:
            pipe_names = [pipe.name for pipe in self.pipes]
            self.pipe_type_combo['values'] = pipe_names
            self.pipe_type_combo.current(0)
            self._on_pipe_selected(None)
    
    def _on_pipe_selected(self, event):
        """Callback wenn ein Rohrtyp ausgewählt wird."""
        if not self.pipes:
            return
        
        selected_name = self.pipe_type_var.get()
        for pipe in self.pipes:
            if pipe.name == selected_name:
                # Aktualisiere Eingabefelder
                self.entries["pipe_outer_diameter"].delete(0, tk.END)
                self.entries["pipe_outer_diameter"].insert(0, f"{pipe.diameter_m:.4f}")
                
                self.entries["pipe_thickness"].delete(0, tk.END)
                self.entries["pipe_thickness"].insert(0, f"{pipe.thickness_m:.4f}")
                
                self.entries["pipe_thermal_cond"].delete(0, tk.END)
                self.entries["pipe_thermal_cond"].insert(0, str(pipe.thermal_conductivity))
                break
    
    def _on_soil_type_selected(self, event):
        """Callback wenn ein Bodentyp ausgewählt wird."""
        selected_name = self.soil_type_var.get()
        soil = SoilTypeDB.get_soil_type(selected_name)
        
        if soil:
            # Aktualisiere Wärmeleitfähigkeit
            self.entries["ground_thermal_cond"].delete(0, tk.END)
            self.entries["ground_thermal_cond"].insert(0, f"{soil.thermal_conductivity_typical:.1f}")
            
            # Aktualisiere Wärmekapazität (MJ/m³·K → J/m³·K)
            heat_cap_j = soil.heat_capacity_typical * 1_000_000
            self.entries["ground_heat_cap"].delete(0, tk.END)
            self.entries["ground_heat_cap"].insert(0, f"{heat_cap_j:.0f}")
            
            self.status_var.set(f"✓ Bodentyp '{selected_name}' ausgewählt: λ={soil.thermal_conductivity_typical} W/m·K")
    
    def _on_grout_material_selected(self, event):
        """Callback wenn ein Verfüllmaterial ausgewählt wird."""
        selected_name = self.grout_material_var.get()
        material = GroutMaterialDB.get_material(selected_name)
        
        if material:
            # Aktualisiere Wärmeleitfähigkeit
            self.entries["grout_thermal_cond"].delete(0, tk.END)
            self.entries["grout_thermal_cond"].insert(0, f"{material.thermal_conductivity:.1f}")
            
            self.status_var.set(f"✓ Verfüllmaterial '{selected_name}' ausgewählt: λ={material.thermal_conductivity} W/m·K")
    
    def _load_climate_data(self):
        """Lädt Klimadaten von PVGIS."""
        # Dialog für Standorteingabe
        dialog = tk.Toplevel(self.root)
        dialog.title("PVGIS Klimadaten")
        dialog.geometry("400x150")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Geben Sie Breitengrad und Längengrad ein:").pack(pady=10)
        
        frame = ttk.Frame(dialog)
        frame.pack(pady=10)
        
        ttk.Label(frame, text="Breitengrad (Lat):").grid(row=0, column=0, padx=5, pady=5)
        lat_entry = ttk.Entry(frame, width=20)
        lat_entry.insert(0, "52.52")  # Berlin als Beispiel
        lat_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(frame, text="Längengrad (Lon):").grid(row=1, column=0, padx=5, pady=5)
        lon_entry = ttk.Entry(frame, width=20)
        lon_entry.insert(0, "13.40")  # Berlin als Beispiel
        lon_entry.grid(row=1, column=1, padx=5, pady=5)
        
        def fetch_data():
            try:
                lat = float(lat_entry.get())
                lon = float(lon_entry.get())
                
                self.status_var.set("⏳ Lade Klimadaten von PVGIS...")
                self.root.update()
                
                climate_data = get_climate_data(lat, lon)
                
                if climate_data:
                    # Aktualisiere Bodentemperatur
                    ground_temp = SoilTypeDB.estimate_ground_temperature(
                        climate_data['avg_temp'],
                        climate_data['coldest_month_temp']
                    )
                    
                    self.entries["ground_temp"].delete(0, tk.END)
                    self.entries["ground_temp"].insert(0, f"{ground_temp:.1f}")
                    
                    self.status_var.set(
                        f"✓ Klimadaten geladen: Ø {climate_data['avg_temp']:.1f}°C, "
                        f"Boden geschätzt: {ground_temp:.1f}°C"
                    )
                    
                    messagebox.showinfo(
                        "Klimadaten geladen",
                        f"Durchschnittstemperatur: {climate_data['avg_temp']:.1f}°C\n"
                        f"Kältester Monat: {climate_data['coldest_month_temp']:.1f}°C\n"
                        f"Geschätzte Bodentemperatur: {ground_temp:.1f}°C"
                    )
                    
                    dialog.destroy()
                else:
                    messagebox.showerror("Fehler", "Keine Daten von PVGIS erhalten.")
                    self.status_var.set("❌ PVGIS-Abfrage fehlgeschlagen")
                    
            except ValueError:
                messagebox.showerror("Eingabefehler", "Ungültige Koordinaten!")
            except Exception as e:
                messagebox.showerror("Fehler", f"Fehler beim Laden: {str(e)}")
                self.status_var.set("❌ PVGIS-Fehler")
        
        ttk.Button(dialog, text="Laden", command=fetch_data).pack(pady=10)
    
    def _run_calculation(self):
        """Führt die Berechnung durch."""
        try:
            # Sammle Eingabewerte
            params = {}
            for key, entry in self.entries.items():
                params[key] = float(entry.get())
            
            # Status aktualisieren
            self.status_var.set("⏳ Berechnung läuft...")
            self.root.update()
            
            # Konvertiere Rohrkonfiguration
            pipe_config = self.pipe_config_var.get()
            if "4-rohr" in pipe_config:
                # Behandle 4-Rohr wie Double-U
                pipe_config = "double-u"
            
            # Berechnung durchführen (mit Einheiten-Umrechnung)
            self.result = self.calculator.calculate_required_depth(
                ground_thermal_conductivity=params["ground_thermal_cond"],
                ground_heat_capacity=params["ground_heat_cap"],
                undisturbed_ground_temp=params["ground_temp"],
                geothermal_gradient=params["geothermal_gradient"],
                borehole_diameter=params["borehole_diameter"] / 1000,  # mm → m
                pipe_configuration=pipe_config,
                pipe_outer_diameter=params["pipe_outer_diameter"],
                pipe_wall_thickness=params["pipe_thickness"],
                pipe_thermal_conductivity=params["pipe_thermal_cond"],
                shank_spacing=params["shank_spacing"] / 1000,  # mm → m
                grout_thermal_conductivity=params["grout_thermal_cond"],
                fluid_thermal_conductivity=params["fluid_thermal_cond"],
                fluid_heat_capacity=params["fluid_heat_cap"],
                fluid_density=params["fluid_density"],
                fluid_viscosity=params["fluid_viscosity"],
                fluid_flow_rate=params["fluid_flow_rate"],
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
            
            # Speichere Parameter für PDF
            self.current_params = params
            self.current_params['pipe_configuration'] = self.pipe_config_var.get()
            
            # Ergebnisse anzeigen
            self._display_results()
            self._plot_results()
            
            # Status aktualisieren
            num_boreholes = int(self.borehole_entries["num_boreholes"].get())
            total_depth = self.result.required_depth * num_boreholes
            self.status_var.set(
                f"✓ Berechnung erfolgreich! Tiefe: {self.result.required_depth:.1f}m pro Bohrung "
                f"({num_boreholes} Bohrungen = {total_depth:.1f}m gesamt)"
            )
            
            # Wechsle zum Ergebnisse-Tab
            self.notebook.select(self.results_frame)
            
        except ValueError as e:
            messagebox.showerror("Eingabefehler", f"Ungültige Eingabe: {str(e)}")
            self.status_var.set("❌ Berechnung fehlgeschlagen - Eingabefehler")
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler bei der Berechnung: {str(e)}")
            self.status_var.set("❌ Berechnung fehlgeschlagen")
    
    def _display_results(self):
        """Zeigt die Ergebnisse im Text-Widget an."""
        if not self.result:
            return
        
        num_boreholes = int(self.borehole_entries["num_boreholes"].get())
        total_depth = self.result.required_depth * num_boreholes
        
        self.results_text.config(state=tk.NORMAL)
        self.results_text.delete("1.0", tk.END)
        
        text = "=" * 70 + "\n"
        text += "         ERDWÄRMESONDEN-BERECHNUNGSERGEBNIS\n"
        text += "=" * 70 + "\n\n"
        
        # Projekt-Info
        proj_name = self.project_entries["project_name"].get()
        if proj_name:
            text += f"Projekt: {proj_name}\n"
            text += f"Kunde:   {self.project_entries['customer_name'].get()}\n\n"
        
        text += "BOHRFELD-KONFIGURATION\n"
        text += "-" * 70 + "\n"
        text += f"Anzahl Bohrungen:              {num_boreholes:>10}\n"
        text += f"Tiefe pro Bohrung:             {self.result.required_depth:>10.1f} m\n"
        text += f"Gesamte Bohrmeter:             {total_depth:>10.1f} m\n"
        text += f"Abstand zwischen Bohrungen:    {self.borehole_entries['spacing_between'].get():>10} m\n"
        text += f"Abstand zum Grundstück:        {self.borehole_entries['spacing_property'].get():>10} m\n"
        text += f"Abstand zum Gebäude:           {self.borehole_entries['spacing_building'].get():>10} m\n\n"
        
        text += "LEISTUNGSDATEN\n"
        text += "-" * 70 + "\n"
        text += f"Wärmeentzugsrate:              {self.result.heat_extraction_rate:>10.2f} W/m\n"
        total_power = self.result.heat_extraction_rate * total_depth / 1000
        text += f"Gesamtleistung Bohrfeld:       {total_power:>10.2f} kW\n\n"
        
        text += "TEMPERATUREN\n"
        text += "-" * 70 + "\n"
        text += f"Min. Fluidtemperatur:          {self.result.fluid_temperature_min:>10.2f} °C\n"
        text += f"Max. Fluidtemperatur:          {self.result.fluid_temperature_max:>10.2f} °C\n\n"
        
        text += "THERMISCHE WIDERSTÄNDE\n"
        text += "-" * 70 + "\n"
        text += f"Bohrloch-Widerstand (Rb):      {self.result.borehole_resistance:>10.4f} m·K/W\n"
        text += f"Effektiver Widerstand:         {self.result.effective_resistance:>10.4f} m·K/W\n\n"
        
        text += "MONATLICHE DURCHSCHNITTSTEMPERATUREN\n"
        text += "-" * 70 + "\n"
        months = ["Jan", "Feb", "Mär", "Apr", "Mai", "Jun", 
                  "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"]
        for i, (month, temp) in enumerate(zip(months, self.result.monthly_temperatures)):
            text += f"{month}: {temp:>6.2f} °C    "
            if (i + 1) % 3 == 0:
                text += "\n"
        
        text += "\n\n"
        text += "=" * 70 + "\n"
        text += "Berechnungsmethode: G-Funktionen (Eskilson), VDI 4640\n"
        text += "=" * 70 + "\n"
        
        self.results_text.insert("1.0", text)
        self.results_text.config(state=tk.DISABLED)
    
    def _plot_results(self):
        """Erstellt Visualisierungen der Ergebnisse."""
        if not self.result:
            return
        
        self.fig.clear()
        
        # 3 Subplots
        ax1 = self.fig.add_subplot(1, 3, 1)
        ax2 = self.fig.add_subplot(1, 3, 2)
        ax3 = self.fig.add_subplot(1, 3, 3)
        
        # Plot 1: Monatliche Temperaturen
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
        
        # Plot 2: Bohrloch-Schema
        bh_diameter = float(self.entries["borehole_diameter"].get())
        pipe_diameter = float(self.entries["pipe_outer_diameter"].get())
        
        scale = 100
        bh_radius = (bh_diameter / 2) * scale
        pipe_radius = (pipe_diameter / 2) * scale
        
        # Bohrloch
        borehole = Circle((0, 0), bh_radius, facecolor='#d9d9d9', 
                         edgecolor='black', linewidth=2)
        ax2.add_patch(borehole)
        
        # 4 Rohre
        positions = [
            (-bh_radius*0.5, bh_radius*0.5),
            (bh_radius*0.5, bh_radius*0.5),
            (-bh_radius*0.5, -bh_radius*0.5),
            (bh_radius*0.5, -bh_radius*0.5)
        ]
        
        colors_pipes = ['#ff6b6b', '#4ecdc4', '#ff6b6b', '#4ecdc4']
        
        for i, ((x, y), color) in enumerate(zip(positions, colors_pipes)):
            pipe = Circle((x, y), pipe_radius*1.5, facecolor=color, 
                         edgecolor='black', linewidth=1, alpha=0.8)
            ax2.add_patch(pipe)
            ax2.text(x, y, str(i+1), ha='center', va='center', 
                    fontsize=9, fontweight='bold', color='white')
        
        ax2.set_xlim(-bh_radius*1.5, bh_radius*1.5)
        ax2.set_ylim(-bh_radius*1.5, bh_radius*1.5)
        ax2.set_aspect('equal')
        ax2.set_title(f'Bohrloch-Querschnitt\nØ {bh_diameter*1000:.0f} mm', 
                     fontsize=12, fontweight='bold')
        ax2.axis('off')
        
        # Plot 3: Bohrfeld-Layout
        num_boreholes = int(self.borehole_entries["num_boreholes"].get())
        spacing = float(self.borehole_entries["spacing_between"].get())
        
        # Berechne Positionen (einfache Reihen-Anordnung)
        boreholes_per_row = int(np.ceil(np.sqrt(num_boreholes)))
        positions_field = []
        
        for i in range(num_boreholes):
            row = i // boreholes_per_row
            col = i % boreholes_per_row
            positions_field.append((col * spacing, row * spacing))
        
        for i, (x, y) in enumerate(positions_field):
            circle = Circle((x, y), 0.3, facecolor='#1f4788', 
                           edgecolor='black', linewidth=1.5)
            ax3.add_patch(circle)
            ax3.text(x, y, str(i+1), ha='center', va='center', 
                    fontsize=8, fontweight='bold', color='white')
        
        # Abstände einzeichnen
        if num_boreholes > 1:
            ax3.plot([0, spacing], [-1, -1], 'k-', linewidth=1.5)
            ax3.plot([0, 0], [-0.8, -1.2], 'k-', linewidth=1.5)
            ax3.plot([spacing, spacing], [-0.8, -1.2], 'k-', linewidth=1.5)
            ax3.text(spacing/2, -1.5, f'{spacing} m', ha='center', fontsize=9)
        
        ax3.set_xlim(-2, max(spacing * boreholes_per_row, 5))
        ax3.set_ylim(-3, max(spacing * np.ceil(num_boreholes / boreholes_per_row), 5))
        ax3.set_aspect('equal')
        ax3.set_title(f'Bohrfeld-Layout\n{num_boreholes} Bohrungen', 
                     fontsize=12, fontweight='bold')
        ax3.set_xlabel('Abstand [m]', fontsize=10)
        ax3.set_ylabel('Abstand [m]', fontsize=10)
        ax3.grid(True, alpha=0.3)
        
        self.fig.tight_layout()
        self.canvas.draw()
    
    def _export_pdf(self):
        """Exportiert einen PDF-Bericht."""
        if not self.result:
            messagebox.showwarning("Keine Daten", "Bitte zuerst eine Berechnung durchführen.")
            return
        
        # Dateinamen vorschlagen
        project_name = self.project_entries["project_name"].get() or "Projekt"
        default_filename = f"Bericht_{project_name.replace(' ', '_')}.pdf"
        
        filename = filedialog.asksaveasfilename(
            title="PDF-Bericht speichern",
            defaultextension=".pdf",
            initialfile=default_filename,
            filetypes=[("PDF-Dateien", "*.pdf"), ("Alle Dateien", "*.*")]
        )
        
        if filename:
            try:
                self.status_var.set("📄 PDF-Bericht wird erstellt...")
                self.root.update()
                
                # Sammle Projektinformationen
                project_info = {}
                for key, entry in self.project_entries.items():
                    project_info[key] = entry.get()
                
                # Sammle Bohrfeld-Konfiguration
                borehole_config = {}
                for key, entry in self.borehole_entries.items():
                    borehole_config[key] = float(entry.get()) if entry.get() else 0
                
                # Generiere PDF
                self.pdf_generator.generate_report(
                    filename,
                    self.result,
                    self.current_params,
                    project_info,
                    borehole_config
                )
                
                self.status_var.set(f"✓ PDF-Bericht erfolgreich erstellt: {os.path.basename(filename)}")
                messagebox.showinfo("Erfolg", f"PDF-Bericht wurde erstellt:\n{filename}")
                
            except Exception as e:
                messagebox.showerror("Fehler", f"Fehler beim PDF-Export: {str(e)}")
                self.status_var.set("❌ PDF-Export fehlgeschlagen")
    
    def _export_results(self):
        """Exportiert die Ergebnisse als Textdatei."""
        if not self.result:
            messagebox.showwarning("Keine Daten", "Keine Berechnungsergebnisse zum Exportieren vorhanden.")
            return
        
        filename = filedialog.asksaveasfilename(
            title="Ergebnisse speichern",
            defaultextension=".txt",
            filetypes=[("Text-Dateien", "*.txt"), ("Alle Dateien", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.results_text.get("1.0", tk.END))
                messagebox.showinfo("Erfolg", f"Ergebnisse wurden gespeichert.")
                self.status_var.set(f"✓ Text-Export: {os.path.basename(filename)}")
            except Exception as e:
                messagebox.showerror("Fehler", f"Fehler beim Speichern: {str(e)}")
    
    def _show_about(self):
        """Zeigt den Über-Dialog."""
        about_text = """Geothermie Erdsonden-Berechnungstool
Professional Edition

Version: 2.0

Ein Open-Source-Tool zur Dimensionierung von
Erdwärmesonden und Bohrfeldern bis 100m Tiefe.

Neue Features:
✓ Projektdaten und Kundeninformationen
✓ Bohrfeld-Konfiguration (mehrere Bohrungen)
✓ PE 100 RC 32mm 4-Rohr-Systeme
✓ Professioneller PDF-Bericht-Export
✓ Detaillierte Visualisierungen

Berechnungsmethoden:
• G-Funktionen (Eskilson, 1987)
• Multipol-Methode (Hellström, 1991)
• VDI 4640 konform

Entwickelt mit Python, tkinter und reportlab

© 2026 - Open Source (MIT Lizenz)
        """
        messagebox.showinfo("Über", about_text)


def main():
    """Haupteinstiegspunkt für die erweiterte GUI."""
    root = tk.Tk()
    app = GeothermieGUIExtended(root)
    root.mainloop()


if __name__ == "__main__":
    main()

