"""Pumpenauswahl-Assistent Dialog."""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Dict, Any
import sys
import os

# Füge data-Verzeichnis zum Pfad hinzu
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from data.pump_db import PumpDatabase


class PumpSelectionDialog:
    """Dialog für intelligente Pumpenauswahl."""
    
    def __init__(self, parent, hydraulics_data: Dict[str, Any]):
        """
        Initialisiert den Pumpenauswahl-Dialog.
        
        Args:
            parent: Eltern-Widget
            hydraulics_data: Hydraulik-Berechnungsergebnisse
        """
        self.parent = parent
        self.hydraulics_data = hydraulics_data
        self.selected_pump = None
        
        # Lade Pumpen-Datenbank
        try:
            self.pump_db = PumpDatabase()
        except Exception as e:
            messagebox.showerror("Fehler", f"Pumpen-Datenbank konnte nicht geladen werden:\n{e}")
            return
        
        # Erstelle Dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("🔧 Pumpenauswahl-Assistent")
        self.dialog.geometry("900x700")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self._create_widgets()
        self._find_suitable_pumps()
        
        # Zentriere Dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")
    
    def _create_widgets(self):
        """Erstellt die Dialog-Widgets."""
        # Header
        header_frame = ttk.Frame(self.dialog)
        header_frame.pack(fill="x", padx=20, pady=10)
        
        title = ttk.Label(header_frame, text="Pumpenauswahl-Assistent",
                         font=("Arial", 16, "bold"))
        title.pack(anchor="w")
        
        subtitle = ttk.Label(header_frame, 
                            text="Empfohlene Umwälzpumpen basierend auf Ihrer Hydraulik-Berechnung",
                            font=("Arial", 10))
        subtitle.pack(anchor="w")
        
        ttk.Separator(self.dialog, orient="horizontal").pack(fill="x", padx=20, pady=5)
        
        # Anforderungen anzeigen
        req_frame = ttk.LabelFrame(self.dialog, text="📊 Ihre Anforderungen", padding=10)
        req_frame.pack(fill="x", padx=20, pady=10)
        
        # Extrahiere Daten
        flow_m3h = self.hydraulics_data.get('flow', {}).get('volume_flow_m3_h', 0)
        total_dp = self.hydraulics_data.get('system', {}).get('total_pressure_drop_bar', 0)
        head_m = total_dp * 10.2  # bar → m Wassersäule
        power_kw = self.hydraulics_data.get('heat_power', 11)
        
        req_grid = ttk.Frame(req_frame)
        req_grid.pack(fill="x")
        
        ttk.Label(req_grid, text="Volumenstrom:", font=("Arial", 9, "bold")).grid(row=0, column=0, sticky="w", padx=5)
        ttk.Label(req_grid, text=f"{flow_m3h:.2f} m³/h").grid(row=0, column=1, sticky="w", padx=5)
        
        ttk.Label(req_grid, text="Förderhöhe:", font=("Arial", 9, "bold")).grid(row=0, column=2, sticky="w", padx=20)
        ttk.Label(req_grid, text=f"{head_m:.1f} m").grid(row=0, column=3, sticky="w", padx=5)
        
        ttk.Label(req_grid, text="Wärmepumpe:", font=("Arial", 9, "bold")).grid(row=1, column=0, sticky="w", padx=5)
        ttk.Label(req_grid, text=f"{power_kw:.0f} kW").grid(row=1, column=1, sticky="w", padx=5)
        
        ttk.Label(req_grid, text="Druckverlust:", font=("Arial", 9, "bold")).grid(row=1, column=2, sticky="w", padx=20)
        ttk.Label(req_grid, text=f"{total_dp:.2f} bar").grid(row=1, column=3, sticky="w", padx=5)
        
        # Empfehlungen
        rec_frame = ttk.LabelFrame(self.dialog, text="✅ Empfohlene Pumpen", padding=10)
        rec_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Treeview für Pumpen
        tree_frame = ttk.Frame(rec_frame)
        tree_frame.pack(fill="both", expand=True)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical")
        scrollbar.pack(side="right", fill="y")
        
        # Treeview
        columns = ("score", "model", "type", "flow", "head", "power", "efficiency", "price")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="tree headings",
                                 yscrollcommand=scrollbar.set, selectmode="browse")
        scrollbar.config(command=self.tree.yview)
        
        # Spalten konfigurieren
        self.tree.heading("#0", text="Rang")
        self.tree.heading("score", text="Score")
        self.tree.heading("model", text="Modell")
        self.tree.heading("type", text="Typ")
        self.tree.heading("flow", text="Max. Flow")
        self.tree.heading("head", text="Max. Head")
        self.tree.heading("power", text="Leistung")
        self.tree.heading("efficiency", text="Effizienz")
        self.tree.heading("price", text="Preis")
        
        self.tree.column("#0", width=50, anchor="center")
        self.tree.column("score", width=70, anchor="center")
        self.tree.column("model", width=200, anchor="w")
        self.tree.column("type", width=90, anchor="center")
        self.tree.column("flow", width=80, anchor="center")
        self.tree.column("head", width=80, anchor="center")
        self.tree.column("power", width=80, anchor="center")
        self.tree.column("efficiency", width=70, anchor="center")
        self.tree.column("price", width=80, anchor="center")
        
        self.tree.pack(fill="both", expand=True)
        
        # Details-Bereich
        detail_frame = ttk.LabelFrame(self.dialog, text="ℹ️ Details", padding=10)
        detail_frame.pack(fill="x", padx=20, pady=10)
        
        self.detail_text = tk.Text(detail_frame, height=8, wrap="word", font=("Courier", 9))
        self.detail_text.pack(fill="both", expand=True)
        
        # Buttons
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(fill="x", padx=20, pady=10)
        
        ttk.Button(button_frame, text="Auswählen", command=self._on_select).pack(side="right", padx=5)
        ttk.Button(button_frame, text="Abbrechen", command=self.dialog.destroy).pack(side="right", padx=5)
        
        # Event Binding
        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)
    
    def _find_suitable_pumps(self):
        """Findet passende Pumpen und zeigt sie an."""
        # Extrahiere Hydraulik-Daten
        flow_m3h = self.hydraulics_data.get('flow', {}).get('volume_flow_m3_h', 0)
        total_dp = self.hydraulics_data.get('system', {}).get('total_pressure_drop_bar', 0)
        head_m = total_dp * 10.2  # bar → m Wassersäule
        power_kw = self.hydraulics_data.get('heat_power', 11)
        
        # Suche passende Pumpen
        suitable_pumps = self.pump_db.find_suitable_pumps(
            flow_m3h=flow_m3h,
            head_m=head_m,
            power_kw=power_kw,
            max_results=10
        )
        
        if not suitable_pumps:
            messagebox.showwarning("Keine Pumpen gefunden",
                                 "Es wurden keine passenden Pumpen in der Datenbank gefunden.\n"
                                 "Bitte überprüfen Sie Ihre Hydraulik-Berechnung.")
            return
        
        # Fülle Treeview
        for i, (score, pump) in enumerate(suitable_pumps, 1):
            # Rang-Symbol
            if i == 1:
                rank = "🥇"
            elif i == 2:
                rank = "🥈"
            elif i == 3:
                rank = "🥉"
            else:
                rank = f"#{i}"
            
            # Score-Farbe
            if score >= 90:
                score_text = f"{score:.0f} ⭐⭐⭐"
            elif score >= 70:
                score_text = f"{score:.0f} ⭐⭐"
            elif score >= 50:
                score_text = f"{score:.0f} ⭐"
            else:
                score_text = f"{score:.0f}"
            
            # Typ
            pump_type = "Geregelt" if pump.pump_type == "regulated" else "Konstant"
            
            values = (
                score_text,
                pump.get_full_name(),
                pump_type,
                f"{pump.specs.max_flow_m3h} m³/h",
                f"{pump.specs.max_head_m} m",
                f"{pump.specs.power_avg_w} W",
                pump.efficiency_class,
                f"{pump.price_eur:.0f} €"
            )
            
            item_id = self.tree.insert("", "end", text=rank, values=values)
            # Speichere Pumpe als Attribut
            self.tree.item(item_id, tags=(f"pump_{i}",))
            
            # Speichere Pump-Objekt für Details
            if not hasattr(self, 'pump_objects'):
                self.pump_objects = {}
            self.pump_objects[item_id] = pump
        
        # Wähle erste Pumpe
        first_item = self.tree.get_children()[0]
        self.tree.selection_set(first_item)
        self.tree.focus(first_item)
        self._show_pump_details(first_item)
    
    def _on_tree_select(self, event):
        """Wird aufgerufen wenn eine Pumpe ausgewählt wird."""
        selection = self.tree.selection()
        if selection:
            self._show_pump_details(selection[0])
    
    def _show_pump_details(self, item_id):
        """Zeigt Details für ausgewählte Pumpe."""
        if not hasattr(self, 'pump_objects') or item_id not in self.pump_objects:
            return
        
        pump = self.pump_objects[item_id]
        
        # Baue Detail-Text
        details = []
        details.append(f"═══ {pump.get_full_name()} ═══\n")
        details.append(f"Hersteller: {pump.manufacturer}")
        details.append(f"Serie: {pump.series}")
        details.append(f"Typ: {'Geregelte Pumpe' if pump.pump_type == 'regulated' else 'Konstantpumpe'}")
        details.append(f"Effizienzklasse: {pump.efficiency_class}\n")
        
        details.append("TECHNISCHE DATEN:")
        details.append(f"  Max. Volumenstrom: {pump.specs.max_flow_m3h} m³/h")
        details.append(f"  Max. Förderhöhe: {pump.specs.max_head_m} m")
        details.append(f"  Leistung: {pump.specs.power_min_w}-{pump.specs.power_max_w} W (Ø {pump.specs.power_avg_w} W)")
        details.append(f"  Anschluss: {pump.specs.connection_size}")
        details.append(f"  Spannung: {pump.specs.voltage}\n")
        
        details.append("ANWENDUNG:")
        details.append(f"  Geeignet für: {pump.suitable_for['application']}")
        details.append(f"  Leistungsbereich: {pump.suitable_for['min_power_kw']}-{pump.suitable_for['max_power_kw']} kW\n")
        
        if pump.features:
            details.append("FEATURES:")
            for feature in pump.features:
                details.append(f"  • {feature}")
            details.append("")
        
        details.append("PREIS:")
        details.append(f"  {pump.price_eur:.2f} EUR ({pump.price_range})")
        
        if pump.note:
            details.append(f"\n💡 Hinweis: {pump.note}")
        
        # Zeige Details
        self.detail_text.delete(1.0, tk.END)
        self.detail_text.insert(1.0, "\n".join(details))
    
    def _on_select(self):
        """Wird aufgerufen wenn Benutzer eine Pumpe auswählt."""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Keine Auswahl", "Bitte wählen Sie eine Pumpe aus.")
            return
        
        item_id = selection[0]
        if hasattr(self, 'pump_objects') and item_id in self.pump_objects:
            self.selected_pump = self.pump_objects[item_id]
            self.dialog.destroy()
    
    def show(self) -> Optional[Any]:
        """Zeigt Dialog und gibt ausgewählte Pumpe zurück."""
        self.dialog.wait_window()
        return self.selected_pump


# Test-Funktion
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    
    # Test-Daten
    test_hydraulics = {
        'heat_power': 11,
        'flow': {
            'volume_flow_m3_h': 2.5
        },
        'system': {
            'total_pressure_drop_bar': 0.55
        }
    }
    
    dialog = PumpSelectionDialog(root, test_hydraulics)
    result = dialog.show()
    
    if result:
        print(f"✅ Ausgewählt: {result.get_full_name()}")
    else:
        print("❌ Abgebrochen")

