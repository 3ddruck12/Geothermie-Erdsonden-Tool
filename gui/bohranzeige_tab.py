"""GUI-Tab für die wasserrechtliche Bohranzeige.

Stellt Eingabefelder für Antragsteller, Grundstück, Bohrunternehmen etc.
bereit und kann technische Daten aus der aktuellen Berechnung übernehmen.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Optional, Dict, Any, Callable
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class BohranzeigTab:
    """Tab-Inhalt für Bohranzeige / wasserrechtliche Anzeige."""

    def __init__(
        self,
        parent: ttk.Frame,
        get_berechnung_callback: Callable[[], Dict[str, Any]],
        export_pdf_callback: Callable[[Dict[str, Any]], None]
    ):
        """
        Initialisiert den Bohranzeige-Tab.

        Args:
            parent: Übergeordnetes Frame (Tab im Notebook)
            get_berechnung_callback: Funktion, die aktuelle Berechnungsdaten liefert
            export_pdf_callback: Funktion zum Erstellen der PDF
        """
        self.parent = parent
        self.get_berechnung = get_berechnung_callback
        self.export_pdf = export_pdf_callback

        # Entry-Dictionaries
        self.antragsteller_entries = {}
        self.grundstueck_entries = {}
        self.bohrunternehmen_entries = {}
        self.ausfuehrung_entries = {}
        self.gewaesserschutz_entries = {}
        self.technik_labels = {}  # Labels für automatisch befüllte Werte

        # Checkbox-Variablen
        self.wasserschutzgebiet_var = tk.BooleanVar(value=False)
        self.altlasten_var = tk.BooleanVar(value=False)
        self.wasserschutz_geprueft_var = tk.BooleanVar(value=True)

        self._build_tab()

    def _build_tab(self):
        """Baut den Tab-Inhalt auf."""
        # Scrollbarer Container
        canvas = tk.Canvas(self.parent)
        scrollbar = ttk.Scrollbar(self.parent, orient="vertical", command=canvas.yview)
        scrollable = ttk.Frame(canvas)

        scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Titel
        title_frame = ttk.Frame(scrollable)
        title_frame.pack(fill="x", padx=15, pady=(15, 5))
        ttk.Label(
            title_frame,
            text="📄 Wasserrechtliche Bohranzeige (§ 49 WHG)",
            font=("Arial", 14, "bold"),
            foreground="#1f4788"
        ).pack(anchor="w")
        ttk.Label(
            title_frame,
            text="Formular zur Anzeige einer Erdwärmesonden-Bohrung bei der Unteren Wasserbehörde",
            foreground="gray",
            font=("Arial", 9, "italic")
        ).pack(anchor="w", pady=(2, 0))

        # Separator
        ttk.Separator(scrollable, orient="horizontal").pack(fill="x", padx=15, pady=10)

        # ── Sektionen ──
        self._build_antragsteller(scrollable)
        self._build_grundstueck(scrollable)
        self._build_bohrunternehmen(scrollable)
        self._build_ausfuehrung(scrollable)

        ttk.Separator(scrollable, orient="horizontal").pack(fill="x", padx=15, pady=10)

        # Technik-Übernahme-Button
        btn_frame = ttk.Frame(scrollable)
        btn_frame.pack(fill="x", padx=15, pady=5)
        ttk.Button(
            btn_frame,
            text="⬇️ Technische Daten aus Berechnung übernehmen",
            command=self._uebernehme_berechnung,
            width=45
        ).pack(side="left")
        ttk.Label(
            btn_frame,
            text="  Befüllt die technischen Angaben automatisch",
            foreground="gray",
            font=("Arial", 8, "italic")
        ).pack(side="left", padx=5)

        self._build_technik_anzeige(scrollable)
        self._build_gewaesserschutz(scrollable)

        ttk.Separator(scrollable, orient="horizontal").pack(fill="x", padx=15, pady=10)

        # ── Aktions-Buttons ──
        action_frame = ttk.Frame(scrollable)
        action_frame.pack(fill="x", padx=15, pady=15)

        ttk.Button(
            action_frame,
            text="📄 Bohranzeige als PDF erstellen",
            command=self._on_export_pdf,
            width=35
        ).pack(side="left", padx=5)

        ttk.Button(
            action_frame,
            text="🗑️ Alle Felder leeren",
            command=self._clear_all,
            width=20
        ).pack(side="right", padx=5)

        # Platz am Ende
        ttk.Frame(scrollable, height=30).pack()

    # ─── Sektionen ──────────────────────────────────────────

    def _build_antragsteller(self, parent):
        """1. Antragsteller / Bauherr."""
        frame = self._section_frame(parent, "1. Antragsteller / Bauherr")
        fields = [
            ("Name:", "name", ""),
            ("Straße, Nr.:", "strasse", ""),
            ("PLZ:", "plz", ""),
            ("Ort:", "ort", ""),
            ("Telefon:", "telefon", ""),
            ("E-Mail:", "email", ""),
        ]
        self._add_fields(frame, fields, self.antragsteller_entries)

    def _build_grundstueck(self, parent):
        """2. Grundstück / Standort."""
        frame = self._section_frame(parent, "2. Grundstück / Standort der Bohrung")
        fields = [
            ("Flurstück-Nr.:", "flurstueck", ""),
            ("Gemarkung:", "gemarkung", ""),
            ("Gemeinde:", "gemeinde", ""),
            ("Landkreis:", "landkreis", ""),
        ]
        self._add_fields(frame, fields, self.grundstueck_entries)

        # Koordinaten (readonly, werden aus PVGIS übernommen)
        coord_frame = ttk.Frame(frame)
        coord_frame.pack(fill="x", padx=5, pady=2)
        ttk.Label(coord_frame, text="Koordinaten:", width=20, anchor="e").pack(side="left", padx=(0, 5))
        self.koordinaten_label = ttk.Label(
            coord_frame, text="(werden aus PVGIS-Daten übernommen)", foreground="gray"
        )
        self.koordinaten_label.pack(side="left")

    def _build_bohrunternehmen(self, parent):
        """3. Bohrunternehmen."""
        frame = self._section_frame(parent, "3. Bohrunternehmen")
        fields = [
            ("Firma:", "firma", ""),
            ("Ansprechpartner:", "ansprechpartner", ""),
            ("DVGW W 120-1 (optional):", "dvgw_w120", ""),
        ]
        self._add_fields(frame, fields, self.bohrunternehmen_entries)
        ttk.Label(
            frame,
            text="Hinweis: Die DVGW W 120-1 Zertifizierung wird von vielen Wasserbehörden empfohlen, ist aber nicht überall Pflicht.",
            foreground="gray",
            font=("Arial", 7, "italic"),
            wraplength=500
        ).pack(anchor="w", padx=5, pady=(0, 5))

    def _build_ausfuehrung(self, parent):
        """4. Ausführungszeitraum."""
        frame = self._section_frame(parent, "4. Geplanter Ausführungszeitraum")
        fields = [
            ("Beginn (TT.MM.JJJJ):", "start_datum", ""),
            ("Ende (TT.MM.JJJJ):", "end_datum", ""),
        ]
        self._add_fields(frame, fields, self.ausfuehrung_entries)

    def _build_technik_anzeige(self, parent):
        """5. Technische Angaben – automatisch befüllt."""
        frame = self._section_frame(parent, "5. Technische Angaben (aus Berechnung)")

        technik_fields = [
            ("Anzahl Bohrungen:", "anzahl_bohrungen"),
            ("Bohrtiefe je Bohrung:", "bohrtiefe_m"),
            ("Gesamtbohrmeter:", "gesamtbohrmeter"),
            ("Bohrdurchmesser:", "bohrdurchmesser_mm"),
            ("Abstand zw. Bohrungen:", "abstand_bohrungen_m"),
            ("Sondentyp:", "sondentyp"),
            ("Rohrmaterial:", "rohrmaterial"),
            ("Rohrdurchmesser (außen):", "rohrdurchmesser_mm"),
            ("Wandstärke:", "wandstaerke_mm"),
            ("Verfüllmaterial:", "verfuellmaterial"),
            ("λ Verfüllung:", "verfuell_lambda"),
            ("Wärmeträgerfluid:", "fluid_typ"),
            ("Heizleistung:", "heizleistung_kw"),
            ("Kühlleistung:", "kuehlleistung_kw"),
            ("Jahres-Heizenergie:", "jahres_heizenergie_kwh"),
            ("Jahres-Kühlenergie:", "jahres_kuehlenergie_kwh"),
            ("COP:", "cop"),
        ]

        for label_text, key in technik_fields:
            row_frame = ttk.Frame(frame)
            row_frame.pack(fill="x", padx=5, pady=1)
            ttk.Label(row_frame, text=label_text, width=25, anchor="e",
                      font=("Arial", 9)).pack(side="left", padx=(0, 5))
            lbl = ttk.Label(row_frame, text="—", foreground="#555555",
                            font=("Arial", 9))
            lbl.pack(side="left")
            self.technik_labels[key] = lbl

    def _build_gewaesserschutz(self, parent):
        """6. Gewässerschutz."""
        frame = self._section_frame(parent, "6. Standort- und Gewässerschutz")

        # Wasserschutzgebiet
        wsg_frame = ttk.Frame(frame)
        wsg_frame.pack(fill="x", padx=5, pady=3)
        ttk.Checkbutton(
            wsg_frame, text="Standort liegt in einem Wasserschutzgebiet",
            variable=self.wasserschutzgebiet_var
        ).pack(side="left")

        zone_frame = ttk.Frame(frame)
        zone_frame.pack(fill="x", padx=25, pady=2)
        ttk.Label(zone_frame, text="Zone:").pack(side="left", padx=(0, 5))
        self.zone_var = tk.StringVar()
        zone_combo = ttk.Combobox(
            zone_frame, textvariable=self.zone_var,
            values=["", "I", "II", "III", "IIIA", "IIIB"],
            state="readonly", width=8
        )
        zone_combo.pack(side="left")

        # Grundwasserflurabstand
        gw_frame = ttk.Frame(frame)
        gw_frame.pack(fill="x", padx=5, pady=3)
        ttk.Label(gw_frame, text="Grundwasserflurabstand [m]:", width=25, anchor="e").pack(side="left", padx=(0, 5))
        gw_entry = ttk.Entry(gw_frame, width=15)
        gw_entry.pack(side="left")
        self.gewaesserschutz_entries['grundwasserflurabstand'] = gw_entry

        # Checkboxen
        ttk.Separator(frame, orient="horizontal").pack(fill="x", padx=5, pady=8)
        ttk.Checkbutton(
            frame, text="Altlastenkataster wurde geprüft",
            variable=self.altlasten_var
        ).pack(anchor="w", padx=5, pady=2)
        ttk.Checkbutton(
            frame, text="Lage in Wasser-/Heilquellenschutzgebiet wurde geprüft",
            variable=self.wasserschutz_geprueft_var
        ).pack(anchor="w", padx=5, pady=2)

    # ─── Hilfsfunktionen ────────────────────────────────────

    def _section_frame(self, parent, title: str) -> ttk.LabelFrame:
        """Erstellt einen beschrifteten Rahmen für eine Sektion."""
        frame = ttk.LabelFrame(parent, text=title, padding=10)
        frame.pack(fill="x", padx=15, pady=5)
        return frame

    def _add_fields(self, parent, fields: list, entries_dict: dict):
        """Fügt Eingabefelder in ein Frame ein."""
        for label_text, key, default in fields:
            row = ttk.Frame(parent)
            row.pack(fill="x", padx=5, pady=2)
            ttk.Label(row, text=label_text, width=20, anchor="e").pack(side="left", padx=(0, 5))
            entry = ttk.Entry(row, width=40)
            if default:
                entry.insert(0, default)
            entry.pack(side="left", fill="x", expand=True)
            entries_dict[key] = entry

    def _uebernehme_berechnung(self):
        """Übernimmt technische Daten aus der aktuellen Berechnung."""
        try:
            data = self.get_berechnung()
            if not data:
                messagebox.showwarning(
                    "Keine Berechnung",
                    "Bitte zuerst eine Berechnung durchführen,\n"
                    "dann können die technischen Daten übernommen werden."
                )
                return

            # Technik-Labels aktualisieren
            technik = data.get('technik', {})
            for key, label in self.technik_labels.items():
                value = technik.get(key, '—')
                if value and value != '—':
                    label.configure(text=str(value), foreground="#1f4788")
                else:
                    label.configure(text="—", foreground="#999999")

            # Projektdaten in Antragsteller übernehmen (falls leer)
            projekt = data.get('projekt', {})
            if projekt:
                self._fill_if_empty(self.antragsteller_entries, 'name', projekt.get('kunde', ''))
                self._fill_if_empty(self.antragsteller_entries, 'strasse', projekt.get('adresse', ''))
                self._fill_if_empty(self.antragsteller_entries, 'plz', projekt.get('plz', ''))
                self._fill_if_empty(self.antragsteller_entries, 'ort', projekt.get('ort', ''))

            # Koordinaten
            koordinaten = data.get('koordinaten', {})
            if koordinaten and koordinaten.get('latitude'):
                self.koordinaten_label.configure(
                    text=f"Breite: {koordinaten['latitude']:.4f}°  |  Länge: {koordinaten['longitude']:.4f}°",
                    foreground="#1f4788"
                )

            # Gewässerschutz-Daten
            geo = data.get('gewaesserschutz', {})
            if geo.get('bodentyp'):
                # Info-Text aktualisieren
                pass

            messagebox.showinfo(
                "Daten übernommen",
                "✅ Technische Daten wurden aus der aktuellen Berechnung übernommen."
            )

        except Exception as e:
            logger.error(f"Fehler bei Datenübernahme: {e}")
            messagebox.showerror("Fehler", f"Datenübernahme fehlgeschlagen:\n{e}")

    def _fill_if_empty(self, entries: dict, key: str, value: str):
        """Befüllt ein Entry nur, wenn es leer ist."""
        entry = entries.get(key)
        if entry and not entry.get().strip() and value:
            entry.insert(0, value)

    def _on_export_pdf(self):
        """Startet den PDF-Export."""
        data = self.collect_all_data()
        self.export_pdf(data)

    def collect_all_data(self) -> Dict[str, Any]:
        """Sammelt alle Formulardaten in ein Dictionary."""
        # Antragsteller
        antragsteller = {k: e.get().strip() for k, e in self.antragsteller_entries.items()}

        # Grundstück
        grundstueck = {k: e.get().strip() for k, e in self.grundstueck_entries.items()}

        # Koordinaten aus Label parsen
        koordinaten = {}
        koord_text = self.koordinaten_label.cget("text")
        if "Breite:" in koord_text and "Länge:" in koord_text:
            try:
                parts = koord_text.replace("°", "").split("|")
                lat_str = parts[0].split(":")[1].strip()
                lon_str = parts[1].split(":")[1].strip()
                koordinaten = {'latitude': float(lat_str), 'longitude': float(lon_str)}
            except (ValueError, IndexError):
                pass

        # Bohrunternehmen
        bohrunternehmen = {k: e.get().strip() for k, e in self.bohrunternehmen_entries.items()}

        # Ausführung
        ausfuehrung = {k: e.get().strip() for k, e in self.ausfuehrung_entries.items()}

        # Technik aus Labels
        technik = {}
        for key, label in self.technik_labels.items():
            text = label.cget("text")
            if text != "—":
                # Versuche numerischen Wert zu extrahieren
                try:
                    # "152 mm" → 152, "6.0 kW" → 6.0
                    num_part = text.split()[0].replace(",", "")
                    technik[key] = float(num_part)
                except (ValueError, IndexError):
                    technik[key] = text
            else:
                technik[key] = text

        # Gewässerschutz
        gw_entry = self.gewaesserschutz_entries.get('grundwasserflurabstand')
        gw_value = gw_entry.get().strip() if gw_entry else ''

        gewaesserschutz = {
            'wasserschutzgebiet': self.wasserschutzgebiet_var.get(),
            'zone': self.zone_var.get() if self.wasserschutzgebiet_var.get() else '',
            'grundwasserflurabstand': gw_value,
            'altlasten_geprueft': self.altlasten_var.get(),
            'wasserschutz_geprueft': self.wasserschutz_geprueft_var.get(),
        }

        return {
            'antragsteller': antragsteller,
            'grundstueck': grundstueck,
            'koordinaten': koordinaten,
            'bohrunternehmen': bohrunternehmen,
            'ausfuehrung': ausfuehrung,
            'technik': technik,
            'gewaesserschutz': gewaesserschutz,
        }

    def set_data(self, data: Dict[str, Any]):
        """Setzt alle Felder aus einem Dictionary (z.B. beim Laden einer .get Datei)."""
        if not data:
            return

        # Antragsteller
        for key, value in data.get('antragsteller', {}).items():
            if key in self.antragsteller_entries:
                entry = self.antragsteller_entries[key]
                entry.delete(0, tk.END)
                entry.insert(0, str(value))

        # Grundstück
        for key, value in data.get('grundstueck', {}).items():
            if key in self.grundstueck_entries:
                entry = self.grundstueck_entries[key]
                entry.delete(0, tk.END)
                entry.insert(0, str(value))

        # Koordinaten
        koord = data.get('koordinaten', {})
        if koord and koord.get('latitude'):
            self.koordinaten_label.configure(
                text=f"Breite: {koord['latitude']}°  |  Länge: {koord['longitude']}°",
                foreground="#1f4788"
            )

        # Bohrunternehmen
        for key, value in data.get('bohrunternehmen', {}).items():
            if key in self.bohrunternehmen_entries:
                entry = self.bohrunternehmen_entries[key]
                entry.delete(0, tk.END)
                entry.insert(0, str(value))

        # Ausführung
        for key, value in data.get('ausfuehrung', {}).items():
            if key in self.ausfuehrung_entries:
                entry = self.ausfuehrung_entries[key]
                entry.delete(0, tk.END)
                entry.insert(0, str(value))

        # Technik-Labels
        for key, value in data.get('technik', {}).items():
            if key in self.technik_labels:
                self.technik_labels[key].configure(
                    text=str(value), foreground="#1f4788"
                )

        # Gewässerschutz
        geo = data.get('gewaesserschutz', {})
        self.wasserschutzgebiet_var.set(geo.get('wasserschutzgebiet', False))
        self.zone_var.set(geo.get('zone', ''))
        self.altlasten_var.set(geo.get('altlasten_geprueft', False))
        self.wasserschutz_geprueft_var.set(geo.get('wasserschutz_geprueft', True))

        gw_entry = self.gewaesserschutz_entries.get('grundwasserflurabstand')
        if gw_entry and geo.get('grundwasserflurabstand'):
            gw_entry.delete(0, tk.END)
            gw_entry.insert(0, str(geo['grundwasserflurabstand']))

    def _clear_all(self):
        """Leert alle Eingabefelder."""
        if not messagebox.askyesno("Felder leeren", "Alle Eingabefelder wirklich leeren?"):
            return

        for entries in [self.antragsteller_entries, self.grundstueck_entries,
                        self.bohrunternehmen_entries, self.ausfuehrung_entries,
                        self.gewaesserschutz_entries]:
            for entry in entries.values():
                entry.delete(0, tk.END)

        for label in self.technik_labels.values():
            label.configure(text="—", foreground="#999999")

        self.koordinaten_label.configure(
            text="(werden aus PVGIS-Daten übernommen)", foreground="gray"
        )
        self.wasserschutzgebiet_var.set(False)
        self.zone_var.set("")
        self.altlasten_var.set(False)
        self.wasserschutz_geprueft_var.set(True)
