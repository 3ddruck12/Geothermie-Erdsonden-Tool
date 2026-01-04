"""Tooltip-System für Hilfe-Informationen."""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional


class ToolTip:
    """Einfacher Tooltip der beim Hover erscheint."""
    
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tipwindow = None
        self.id = None
        self.x = self.y = 0
        
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)
    
    def enter(self, event=None):
        self.schedule()
    
    def leave(self, event=None):
        self.unschedule()
        self.hidetip()
    
    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(500, self.showtip)  # 500ms Verzögerung
    
    def unschedule(self):
        id = self.id
        self.id = None
        if id:
            self.widget.after_cancel(id)
    
    def showtip(self):
        if self.tipwindow or not self.text:
            return
        
        x, y, cx, cy = self.widget.bbox("insert")
        x = x + self.widget.winfo_rootx() + 25
        y = y + cy + self.widget.winfo_rooty() + 25
        
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        
        label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                        background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                        font=("Arial", 9), wraplength=300, padx=5, pady=5)
        label.pack()
    
    def hidetip(self):
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()


class InfoButton:
    """Info-Button mit ausführlicher Hilfe."""
    
    HELP_TEXTS = {
        'borehole_diameter': {
            'title': 'Bohrloch-Durchmesser',
            'text': '''Der Durchmesser des gebohrten Lochs.

Typische Werte:
• 110-130 mm - Kleine Bohrungen (bis 50m)
• 140-160 mm - Standard (50-150m)
• 180-200 mm - Große Bohrungen (>150m)

Empfohlen: 152 mm (6 Zoll)

Der Durchmesser beeinflusst:
- Verfüllmaterial-Menge
- Thermischer Widerstand
- Bohrkosten'''
        },
        'pipe_diameter': {
            'title': 'Rohr-Außendurchmesser',
            'text': '''Außendurchmesser der Kunststoffrohre.

Typische PE-Rohre:
• DN25 (32 mm) - Sehr häufig
• DN32 (40 mm) - Standard
• DN40 (50 mm) - Hohe Leistung

Wichtig:
- Größerer Durchmesser = besserer Wärmeübergang
- Aber auch höherer Druckverlust
- Muss zum Bohrloch passen'''
        },
        'fluid_selection': {
            'title': 'Wärmeträgerfluid',
            'text': '''Wärmeträgerflüssigkeit für die Erdwärmesonde.

Typen:
• Reines Wasser: Beste Wärmeübertragung, kein Frostschutz
• Ethylenglykol: Standard Frostschutzmittel
• Propylenglykol: Lebensmittelecht, umweltfreundlicher

Konzentrationen:
• 20%: Frostschutz bis -8°C
• 25%: Frostschutz bis -12°C (Standard) ⭐
• 30%: Frostschutz bis -18°C

Wichtig:
Höhere Konzentration = 
- Bessere Frostsicherheit
- Geringere Wärmeübertragung
- Höhere Viskosität (mehr Pumpenleistung)

Eigenschaften werden automatisch basierend auf
Betriebstemperatur berechnet!'''
        },
        'fluid_temperature': {
            'title': 'Betriebstemperatur',
            'text': '''Temperatur des Wärmeträgerfluids im Betrieb.

Typische Werte:
• Heizen: 0-10°C (Sondeneintritt)
• Kühlen: 15-25°C (Sondeneintritt)

Wichtig:
Die Fluid-Eigenschaften (Dichte, Viskosität, etc.)
werden automatisch für diese Temperatur berechnet!

Tipp: Verwenden Sie die erwartete mittlere
Betriebstemperatur für beste Genauigkeit.'''
        },
        'grout_material': {
            'title': 'Verfüllmaterial',
            'text': '''Material zur Verfüllung des Bohrlochs zwischen Rohren und Bohrlochwand.

Funktionen:
• Thermische Verbindung zwischen Rohr und Erdreich
• Schutz der Rohre vor Beschädigung
• Abdichtung gegen Grundwasser

Materialien:
• Bentonit: Gute Abdichtung, geringe Wärmeleitfähigkeit
• Zement-Bentonit: Standard, gute Balance
• Thermisch verbessert: Höhere Wärmeleitfähigkeit, bessere Leistung
• Hochleistung: Beste Wärmeleitfähigkeit, höhere Kosten

Wichtig:
Höhere Wärmeleitfähigkeit = Kürzere benötigte Bohrtiefe
Aber: Höhere Materialkosten

Kompromiss zwischen Kosten und Leistung!'''
        },
        'shank_spacing': {
            'title': 'Schenkelabstand',
            'text': '''Abstand zwischen Vor- und Rücklauf im Bohrloch.

Typische Werte:
• 40-60 mm - Eng (bessere Wärmeübertragung)
• 60-80 mm - Standard
• 80-100 mm - Weit (weniger thermische Kurzschlüsse)

Faustformel:
Schenkelabstand ≈ 40-50% des Bohrloch-Durchmessers

Beeinflusst den thermischen Kurzschluss zwischen
Vor- und Rücklauf!'''
        },
        'heat_pump_power': {
            'title': 'Wärmepumpenleistung',
            'text': '''Nennleistung der Wärmepumpe bei Normbedingungen.

Typische Werte:
• Einfamilienhaus (140 m²): 6-10 kW
• Passivhaus (140 m²): 3-5 kW
• Mehrfamilienhaus: 15-30 kW

Wichtig:
Sollte größer als die Spitzenlast sein!
Empfehlung: Spitzenlast × 1.2

Zu groß = häufiges Takten
Zu klein = Heizstab wird benötigt'''
        },
        'heat_pump_eer': {
            'title': 'EER - Energy Efficiency Ratio',
            'text': '''Kühlleistungszahl der Wärmepumpe.

Typische Werte:
• 3.0-3.5 - Standard
• 4.0-4.5 - Gute Anlagen ⭐
• >4.5 - Sehr gute Anlagen

Bedeutung:
EER 4.0 = Aus 1 kW Strom werden 4 kW Kälte
Davon 3 kW in die Erde abgegeben!

Höherer EER = 
- Geringere Erdbelastung
- Niedrigere Betriebskosten'''
        },
        'annual_heating': {
            'title': 'Jahres-Heizenergie',
            'text': '''Gesamte benötigte Heizenergie pro Jahr.

Typische Werte:
• Einfamilienhaus (140 m²): 12,000-18,000 kWh
• Passivhaus (140 m²): 5,000-8,000 kWh
• Mehrfamilienhaus: 30,000-60,000 kWh

Berechnung:
Heizlast × Vollbenutzungsstunden
z.B. 6 kW × 2000h = 12,000 kWh

Wichtig:
Nur Raumheizung, OHNE Warmwasser!'''
        },
        'annual_cooling': {
            'title': 'Jahres-Kühlenergie',
            'text': '''Gesamte benötigte Kühlenergie pro Jahr.

Typische Werte:
• Wohngebäude: 0-2,000 kWh
• Bürogebäude: 5,000-15,000 kWh
• Gewerbe: 10,000-50,000 kWh

Berechnung:
Kühllast × Vollbenutzungsstunden
z.B. 3 kW × 800h = 2,400 kWh

Wichtig:
Bei reiner Heizung: 0 kWh
Kühlung kann die Erdwärmesonde entlasten!'''
        },
        'peak_heating': {
            'title': 'Heiz-Spitzenlast',
            'text': '''Maximale Heizleistung bei kältestem Tag.

Typische Werte:
• Einfamilienhaus (140 m²): 6-10 kW
• Passivhaus (140 m²): 2-4 kW
• Mehrfamilienhaus: 20-40 kW

Berechnung:
Gebäude-Wärmeverlust bei -15°C Außentemperatur
+ Warmwasser-Spitzenlast

Wichtig:
Bestimmt die Mindest-Wärmepumpenleistung!
Sollte mit Gebäude-Energieberater abgestimmt werden.'''
        },
        'peak_cooling': {
            'title': 'Kühl-Spitzenlast',
            'text': '''Maximale Kühlleistung bei heißestem Tag.

Typische Werte:
• Wohngebäude: 0-3 kW
• Bürogebäude: 10-30 kW
• Gewerbe: 20-100 kW

Berechnung:
Gebäude-Wärmeeintrag bei +35°C Außentemperatur
+ Interne Lasten (Geräte, Personen)

Wichtig:
Bei reiner Heizung: 0 kW
Kühllast kann die Erdwärmesonde belasten!'''
        },
        'cop': {
            'title': 'COP - Coefficient of Performance',
            'text': '''Jahresarbeitszahl der Wärmepumpe.

Typische Werte:
• 3.0 - Alte Anlagen
• 3.5-4.0 - Gute moderne Anlagen ⭐
• 4.5-5.0 - Sehr gute Anlagen
• >5.0 - Spitzengeräte

Bedeutung:
COP 4.0 = Aus 1 kW Strom werden 4 kW Wärme
Davon 3 kW aus der Erde!

Höherer COP = 
- Geringere Erdbelastung
- Niedrigere Betriebskosten'''
        },
        'grout_thermal_cond': {
            'title': 'Wärmeleitfähigkeit Verfüllung',
            'text': '''Wie gut die Verfüllung Wärme leitet.

Materialien:
• 0.6-0.8 W/m·K - Reiner Bentonit (schlecht)
• 1.0-1.5 W/m·K - Zement-Bentonit (Standard)
• 1.5-2.0 W/m·K - Thermisch verbessert (gut)
• 2.0-2.5 W/m·K - Hochleistung (sehr gut) ⭐

Wichtig:
Höhere Wärmeleitfähigkeit = 
- Kürzere benötigte Bohrtiefe
- Höhere Materialkosten

Kompromiss zwischen Kosten und Leistung!'''
        },
        'ground_thermal_cond': {
            'title': 'Wärmeleitfähigkeit Boden',
            'text': '''Wie gut der Untergrund Wärme leitet.

Typische Werte:
• 0.5-1.0 W/m·K - Trockener Ton (schlecht)
• 1.5-2.0 W/m·K - Lehm, Sand trocken
• 2.0-2.5 W/m·K - Sand feucht (gut)
• 2.5-4.0 W/m·K - Fels, Kalkstein (sehr gut) ⭐
• >2.0 W/m·K - Kies wasserführend (optimal!)

Wichtig:
Wassergehalt erhöht die Wärmeleitfähigkeit stark!

Bei Unsicherheit: Bodengutachten empfohlen.'''
        },
        'num_boreholes': {
            'title': 'Anzahl Bohrungen',
            'text': '''Wie viele separate Bohrungen gebohrt werden.

Vorteile mehrerer Bohrungen:
• Verteilung der Last
• Geringere Einzeltiefe
• Redundanz bei Ausfall
• Bessere thermische Regeneration

Nachteile:
• Höhere Bohrkosten (Mobilisierung)
• Mehr Platz benötigt
• Komplexere Hydraulik

Mindestabstände:
• Zwischen Bohrungen: 5-6 m
• Zum Grundstück: 3 m
• Zum Gebäude: 3 m'''
        },
        'antifreeze': {
            'title': 'Frostschutzkonzentration',
            'text': '''Ethylenglykol-Anteil in der Sole.

Konzentration → Gefrierpunkt:
• 0% (Wasser) → 0°C (nur bei T > 0°C!)
• 20% → -8°C
• 25% → -11°C (Standard) ⭐
• 30% → -15°C
• 40% → -24°C

Nachteile höherer Konzentration:
- Höhere Viskosität (Pumpenmehr Leistung)
- Geringere Wärmekapazität
- Höhere Kosten

Wählen Sie die Konzentration basierend auf
der minimalen Soletemperatur + Sicherheit!'''
        },
        'fluid_thermal_cond': {
            'title': 'Wärmeleitfähigkeit Wärmeträgerflüssigkeit',
            'text': '''Wärmeleitfähigkeit der Sole (Wärmeträgerflüssigkeit).

Typische Werte:
• Reines Wasser: 0.60 W/m·K
• 25% Ethylenglykol: 0.48 W/m·K ⭐
• 30% Ethylenglykol: 0.46 W/m·K
• 40% Ethylenglykol: 0.43 W/m·K

Wichtig:
- Höherer Frostschutz = niedrigere Wärmeleitfähigkeit
- Beeinflusst den Wärmeübergang im Rohr
- Temperaturabhängig (Werte für ~0°C)

Die Wärmeleitfähigkeit sinkt mit steigender
Frostschutzkonzentration!'''
        },
        'fluid_flow_rate': {
            'title': 'Volumenstrom Wärmeträgerflüssigkeit',
            'text': '''Durchflussrate der Sole durch die Erdwärmesonde.

Typische Werte:
• Einfamilienhaus: 0.0003-0.0006 m³/s (1.1-2.2 m³/h)
• Pro kW Heizleistung: ~0.15 L/min
• 6 kW WP: ~0.9 L/min = 0.00015 m³/s

Wichtig:
- Höherer Durchfluss = besserer Wärmeübergang
- Aber auch höherer Druckverlust
- Optimum: Re ≈ 3000-5000 (turbulent)

Zu niedrig: Schlechter Wärmeübergang
Zu hoch: Hohe Pumpenleistung, Lärm

Faustformel: 3 L/min pro kW Entzugsleistung'''
        },
        'pipe_wall_thickness': {
            'title': 'Rohr-Wandstärke',
            'text': '''Wandstärke der PE-Rohre.

Typische Werte:
• DN25 (32mm): 2.4-3.0 mm
• DN32 (40mm): 3.0-3.7 mm ⭐
• DN40 (50mm): 3.7-4.6 mm

SDR-Reihen (Standard Dimension Ratio):
• SDR 11: Dickere Wand, höherer Druck
• SDR 17: Standard
• SDR 21: Dünnere Wand

Wichtig:
- Dickere Wand = höherer thermischer Widerstand
- Aber bessere Druckfestigkeit
- Muss zu Betriebsdruck passen (meist 6-10 bar)'''
        },
        'pipe_outer_diameter': {
            'title': 'Rohr-Außendurchmesser',
            'text': '''Außendurchmesser der PE-Erdwärmesonden-Rohre.

Standard PE-100 Rohre:
• DN20 (25 mm) - Kleine Anlagen
• DN25 (32 mm) - Sehr häufig ⭐
• DN32 (40 mm) - Standard
• DN40 (50 mm) - Hohe Leistung

Wichtig:
- Größerer Durchmesser = mehr Wärmeübertragungsfläche
- Aber auch höherer Druckverlust
- Muss ins Bohrloch passen!

Faustformel:
4 × Rohrdurchmesser < Bohrlochdurchmesser

Beispiel: 4 × 32mm = 128mm < 152mm Bohrloch ✓'''
        }
    }
    
    @staticmethod
    def create_info_button(parent, row, col, help_key):
        """Erstellt einen Info-Button mit Tooltip und Popup."""
        btn = ttk.Button(parent, text="❓", width=3,
                        command=lambda: InfoButton.show_help(help_key))
        btn.grid(row=row, column=col, padx=(5, 10), pady=5, sticky="w")
        
        # Kurzer Tooltip
        short_text = InfoButton.HELP_TEXTS.get(help_key, {}).get('title', 'Info')
        ToolTip(btn, f"Klicken für Details zu: {short_text}")
        
        return btn
    
    @staticmethod
    def show_help(help_key):
        """Zeigt ausführliche Hilfe in Popup."""
        help_data = InfoButton.HELP_TEXTS.get(help_key, {
            'title': 'Hilfe',
            'text': 'Keine Hilfe verfügbar.'
        })
        
        messagebox.showinfo(
            help_data['title'],
            help_data['text']
        )


def create_label_with_info(parent, row, label_text, help_key=None):
    """Erstellt ein Label mit optionalem Info-Button."""
    ttk.Label(parent, text=label_text).grid(
        row=row, column=0, sticky="w", padx=10, pady=5
    )
    
    if help_key:
        InfoButton.create_info_button(parent, row, 2, help_key)


if __name__ == "__main__":
    # Test
    root = tk.Tk()
    root.title("Tooltip Test")
    
    # Test Tooltip
    btn1 = ttk.Button(root, text="Hover über mich")
    btn1.pack(pady=10)
    ToolTip(btn1, "Das ist ein Tooltip!\nMit mehreren Zeilen.")
    
    # Test Info-Button
    frame = ttk.Frame(root)
    frame.pack(pady=10)
    
    ttk.Label(frame, text="Bohrloch-Durchmesser:").grid(row=0, column=0)
    ttk.Entry(frame).grid(row=0, column=1)
    InfoButton.create_info_button(frame, 0, 2, 'borehole_diameter')
    
    root.mainloop()

