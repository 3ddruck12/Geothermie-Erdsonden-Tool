"""Lastprofil-Tab: Monatliche Wärmebedarfs-Eingabe, Warmwasser, Diagramme.

Phase 2 ROADMAP: Monatliche Lastprofile.
- 12×3 Tabelle (Monat | Heizlast | Kühllast)
- Rechte Seite: Live-Vorschau-Diagramm (wie Eingabe-Tab mit Karte)
- Schnelleingabe, Vorlagen, Warmwasser, Export
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import List, Optional, Tuple
import logging

import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from utils.validators import safe_float
from data.load_profiles import (
    MONTH_NAMES,
    get_load_profile_template_names,
    get_load_profile_template,
    calculate_dhw_demand_vdi2067,
    get_monthly_dhw_distribution,
    monthly_values_to_factors,
    calculate_monthly_extraction_rate_w_per_m,
)

logger = logging.getLogger(__name__)

_COLOR_ERROR = "#ffcccc"
_COLOR_NORMAL = "white"
_COLOR_OK = "#ccffcc"


class LoadProfilesTab:
    """Tab für monatliche Lastprofile, Warmwasser und Schnelleingabe."""

    def __init__(self, parent_frame, app):
        self.frame = parent_frame
        self.app = app
        self.monthly_heating_entries: List[tk.Entry] = []
        self.monthly_cooling_entries: List[tk.Entry] = []
        self.dhw_enabled_var = tk.BooleanVar(value=True)
        self._build()

    def _build(self):
        """Erstellt den Tab-Inhalt: links Tabelle, rechts Live-Diagramm."""
        # 2-Spalten-Layout wie Eingabe-Tab (links Tabelle, rechts Grafik)
        main_container = ttk.PanedWindow(self.frame, orient=tk.HORIZONTAL)
        main_container.pack(fill=tk.BOTH, expand=True)

        # ─── Linke Seite: Tabelle + Steuerung ───
        left_frame = ttk.Frame(main_container, padding=10)
        canvas = tk.Canvas(left_frame)
        scrollbar = ttk.Scrollbar(left_frame, orient="vertical", command=canvas.yview)
        scrollable = ttk.Frame(canvas)
        scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Steuerleiste
        ctrl = ttk.Frame(scrollable)
        ctrl.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(ctrl, text="Vorlage laden:", font=("Arial", 10, "bold")).pack(
            side=tk.LEFT, padx=(0, 5))
        self.template_var = tk.StringVar(value="EFH (Einfamilienhaus)")
        template_combo = ttk.Combobox(
            ctrl,
            textvariable=self.template_var,
            values=get_load_profile_template_names(),
            state="readonly",
            width=25,
        )
        template_combo.pack(side=tk.LEFT, padx=5)
        template_combo.bind("<<ComboboxSelected>>", self._on_template_selected)

        ttk.Button(ctrl, text="📋 Vorlage übernehmen",
                   command=self._apply_template).pack(side=tk.LEFT, padx=10)

        ttk.Separator(ctrl, orient=tk.VERTICAL).pack(
            side=tk.LEFT, fill=tk.Y, padx=15)

        ttk.Label(ctrl, text="Schnelleingabe:", font=("Arial", 10, "bold")).pack(
            side=tk.LEFT, padx=(0, 5))
        ttk.Button(ctrl, text="Jahres-Heizen verteilen",
                   command=self._spread_annual_heating).pack(side=tk.LEFT, padx=2)
        ttk.Button(ctrl, text="Jahres-Kühlen verteilen",
                   command=self._spread_annual_cooling).pack(side=tk.LEFT, padx=2)

        # 12×3 Tabelle
        table_frame = ttk.LabelFrame(scrollable, text="Monatliche Lasten [kWh]",
                                     padding=10)
        table_frame.pack(fill=tk.X, pady=5)

        # Header
        ttk.Label(table_frame, text="Monat", font=("Arial", 10, "bold")).grid(
            row=0, column=0, padx=5, pady=3, sticky="w")
        ttk.Label(table_frame, text="Heizlast [kWh]", font=("Arial", 10, "bold")).grid(
            row=0, column=1, padx=5, pady=3, sticky="w")
        ttk.Label(table_frame, text="Kühllast [kWh]", font=("Arial", 10, "bold")).grid(
            row=0, column=2, padx=5, pady=3, sticky="w")

        self.monthly_heating_entries = []
        self.monthly_cooling_entries = []

        for i, month in enumerate(MONTH_NAMES):
            row = i + 1
            ttk.Label(table_frame, text=month).grid(
                row=row, column=0, padx=5, pady=2, sticky="w")

            he_entry = tk.Entry(table_frame, width=12, bg=_COLOR_NORMAL)
            he_entry.insert(0, "0")
            he_entry.grid(row=row, column=1, padx=5, pady=2, sticky="w")
            he_entry.bind("<KeyRelease>", lambda e: self._on_table_changed())
            self.monthly_heating_entries.append(he_entry)

            co_entry = tk.Entry(table_frame, width=12, bg=_COLOR_NORMAL)
            co_entry.insert(0, "0")
            co_entry.grid(row=row, column=2, padx=5, pady=2, sticky="w")
            co_entry.bind("<KeyRelease>", lambda e: self._on_table_changed())
            self.monthly_cooling_entries.append(co_entry)

        # Summenzeile
        sum_row = 13
        ttk.Label(table_frame, text="Summe", font=("Arial", 10, "bold")).grid(
            row=sum_row, column=0, padx=5, pady=5, sticky="w")
        self.sum_heating_label = ttk.Label(table_frame, text="0 kWh",
                                           foreground="#1f4788", font=("Arial", 10, "bold"))
        self.sum_heating_label.grid(row=sum_row, column=1, padx=5, pady=5, sticky="w")
        self.sum_cooling_label = ttk.Label(table_frame, text="0 kWh",
                                           foreground="#1f4788", font=("Arial", 10, "bold"))
        self.sum_cooling_label.grid(row=sum_row, column=2, padx=5, pady=5, sticky="w")

        self.plausibility_label = ttk.Label(
            table_frame, text="", foreground="gray", font=("Arial", 9))
        self.plausibility_label.grid(row=sum_row + 1, column=0, columnspan=3,
                                     padx=5, pady=2, sticky="w")

        # Warmwasser
        dhw_frame = ttk.LabelFrame(scrollable, text="Warmwasser (VDI 2067)",
                                    padding=10)
        dhw_frame.pack(fill=tk.X, pady=10)

        ttk.Checkbutton(
            dhw_frame,
            text="Warmwasser berücksichtigen",
            variable=self.dhw_enabled_var,
            command=self._on_dhw_toggled
        ).pack(anchor="w")

        dhw_inner = ttk.Frame(dhw_frame)
        dhw_inner.pack(fill=tk.X, pady=5)

        ttk.Label(dhw_inner, text="Anzahl Personen:").pack(side=tk.LEFT, padx=(0, 5))
        self.dhw_persons_entry = tk.Entry(dhw_inner, width=6, bg=_COLOR_NORMAL)
        self.dhw_persons_entry.insert(0, "4")
        self.dhw_persons_entry.pack(side=tk.LEFT, padx=5)
        self.dhw_persons_entry.bind("<KeyRelease>", lambda e: self._on_dhw_changed())

        self.dhw_result_label = ttk.Label(
            dhw_inner, text="", foreground="#1f4788")
        self.dhw_result_label.pack(side=tk.LEFT, padx=15)

        ttk.Button(dhw_inner, text="Warmwasser auf Heizlast addieren",
                   command=self._add_dhw_to_heating).pack(side=tk.LEFT, padx=10)

        # Export-Buttons
        export_frame = ttk.Frame(scrollable)
        export_frame.pack(fill=tk.X, pady=15)
        ttk.Label(export_frame, text="Diagramm exportieren:",
                  font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(export_frame, text="📷 PNG",
                   command=lambda: self._export_diagram("png")).pack(
            side=tk.LEFT, padx=5)
        ttk.Button(export_frame, text="📄 PDF",
                   command=lambda: self._export_diagram("pdf")).pack(
            side=tk.LEFT, padx=5)

        main_container.add(left_frame, weight=6)

        # ─── Rechte Seite: Live-Vorschau-Diagramm ───
        right_frame = ttk.Frame(main_container, relief=tk.RIDGE, borderwidth=2)
        right_inner = ttk.Frame(right_frame, padding=10)
        right_inner.pack(fill=tk.BOTH, expand=True)

        ttk.Label(right_inner, text="📊 Lastprofil-Vorschau",
                  font=("Arial", 11, "bold")).pack(anchor="w", pady=(0, 5))

        self.preview_fig = Figure(figsize=(5, 5), dpi=90)
        self.preview_canvas = FigureCanvasTkAgg(self.preview_fig, master=right_inner)
        self.preview_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Kennzahlen-Box
        self.stats_label = ttk.Label(
            right_inner,
            text="Heizen: 0 kWh  |  Kühlen: 0 kWh  |  Σ: 0 kWh",
            font=("Arial", 9), foreground="#1f4788"
        )
        self.stats_label.pack(anchor="w", pady=5)

        main_container.add(right_frame, weight=4)

        self._on_dhw_toggled()
        self._update_sums()
        self._update_preview_diagram()

    def _on_template_selected(self, event=None):
        """Vorlage auswählen (nur Combo ändern, nicht sofort anwenden)."""
        pass

    def _apply_template(self):
        """Wendet die gewählte Vorlage an und verteilt Jahreswerte."""
        heating_annual = safe_float(
            self.app.entries.get("annual_heating", tk.Entry()).get() or "12000",
            default=12000.0
        )
        cooling_annual = safe_float(
            self.app.entries.get("annual_cooling", tk.Entry()).get() or "0",
            default=0.0
        )
        h_factors, c_factors = get_load_profile_template(
            self.template_var.get()
        )
        for i, (hf, cf) in enumerate(zip(h_factors, c_factors)):
            self.monthly_heating_entries[i].delete(0, tk.END)
            self.monthly_heating_entries[i].insert(
                0, f"{heating_annual * hf:.1f}")
            self.monthly_cooling_entries[i].delete(0, tk.END)
            self.monthly_cooling_entries[i].insert(
                0, f"{cooling_annual * cf:.1f}")
        self._update_sums()
        self._sync_to_annual_entries()
        self.app.status_var.set(
            f"✓ Vorlage '{self.template_var.get()}' übernommen")

    def _spread_annual_heating(self):
        """Verteilt Jahres-Heizenergie gleichmäßig auf Heizmonate (Okt–Apr)."""
        annual = safe_float(
            self.app.entries.get("annual_heating", tk.Entry()).get() or "12000",
            default=12000.0
        )
        h_factors, _ = get_load_profile_template(self.template_var.get())
        for i, hf in enumerate(h_factors):
            self.monthly_heating_entries[i].delete(0, tk.END)
            self.monthly_heating_entries[i].insert(0, f"{annual * hf:.1f}")
        self._update_sums()
        self._sync_to_annual_entries()

    def _spread_annual_cooling(self):
        """Verteilt Jahres-Kühlenergie auf Kühlmonate."""
        annual = safe_float(
            self.app.entries.get("annual_cooling", tk.Entry()).get() or "0",
            default=0.0
        )
        _, c_factors = get_load_profile_template(self.template_var.get())
        for i, cf in enumerate(c_factors):
            self.monthly_cooling_entries[i].delete(0, tk.END)
            self.monthly_cooling_entries[i].insert(0, f"{annual * cf:.1f}")
        self._update_sums()
        self._sync_to_annual_entries()

    def _on_table_changed(self):
        """Bei Tabellenänderung Summen und Plausibilität aktualisieren."""
        self._update_sums()

    def _on_dhw_toggled(self):
        """Warmwasser aktiviert/deaktiviert."""
        enabled = self.dhw_enabled_var.get()
        state = "normal" if enabled else "disabled"
        self.dhw_persons_entry.config(state=state)
        self._on_dhw_changed()

    def _on_dhw_changed(self):
        """Warmwasser-Personenzahl geändert."""
        if not self.dhw_enabled_var.get():
            self.dhw_result_label.config(text="")
            return
        n = safe_float(self.dhw_persons_entry.get() or "4", default=4)
        annual = calculate_dhw_demand_vdi2067(int(n))
        self.dhw_result_label.config(
            text=f"≈ {annual:.0f} kWh/Jahr (VDI 2067)")

    def _add_dhw_to_heating(self):
        """Addiert Warmwasser-Bedarf zu den Heizlast-Monaten (proportional)."""
        if not self.dhw_enabled_var.get():
            messagebox.showinfo(
                "Warmwasser",
                "Bitte zuerst 'Warmwasser berücksichtigen' aktivieren.")
            return
        n = safe_float(self.dhw_persons_entry.get() or "4", default=4)
        monthly_dhw = get_monthly_dhw_distribution(int(n))
        for i, dhw_kwh in enumerate(monthly_dhw):
            cur = safe_float(
                self.monthly_heating_entries[i].get() or "0", default=0.0)
            self.monthly_heating_entries[i].delete(0, tk.END)
            self.monthly_heating_entries[i].insert(
                0, f"{cur + dhw_kwh:.1f}")
        self._update_sums()
        self._sync_to_annual_entries()
        annual_dhw = sum(monthly_dhw)
        self.app.status_var.set(
            f"✓ Warmwasser {annual_dhw:.0f} kWh zu Heizlast addiert")

    def _update_sums(self):
        """Aktualisiert Summenzeile und Plausibilitäts-Check."""
        h_vals = []
        c_vals = []
        for he, co in zip(self.monthly_heating_entries,
                          self.monthly_cooling_entries):
            h_vals.append(safe_float(he.get() or "0", default=0.0))
            c_vals.append(safe_float(co.get() or "0", default=0.0))

        sum_h = sum(h_vals)
        sum_c = sum(c_vals)

        self.sum_heating_label.config(text=f"{sum_h:.0f} kWh")
        self.sum_cooling_label.config(text=f"{sum_c:.0f} kWh")

        annual_h = safe_float(
            self.app.entries.get("annual_heating", tk.Entry()).get() or "0",
            default=0.0
        )
        annual_c = safe_float(
            self.app.entries.get("annual_cooling", tk.Entry()).get() or "0",
            default=0.0
        )

        msgs = []
        if annual_h > 0 and abs(sum_h - annual_h) > annual_h * 0.05:
            msgs.append(
                f"⚠ Heiz-Summe ({sum_h:.0f}) weicht vom Jahreswert ({annual_h:.0f}) ab")
        elif annual_h > 0:
            msgs.append("✓ Heiz-Summe passt zum Jahresbedarf")
        if annual_c > 0 and abs(sum_c - annual_c) > annual_c * 0.05:
            msgs.append(
                f"⚠ Kühl-Summe ({sum_c:.0f}) weicht vom Jahreswert ({annual_c:.0f}) ab")
        elif annual_c > 0:
            msgs.append("✓ Kühl-Summe passt zum Jahresbedarf")

        self.plausibility_label.config(
            text=" | ".join(msgs) if msgs else "Summe = Jahresbedarf (Plausibilität OK)")

        self._update_preview_diagram()

    def _update_preview_diagram(self):
        """Aktualisiert die Live-Vorschau rechts (Balkendiagramm + W/m-Zeitreihe)."""
        if not hasattr(self, 'preview_fig'):
            return
        self.preview_fig.clear()

        h = np.array(self.get_monthly_heating_kwh())
        c = np.array(self.get_monthly_cooling_kwh())
        d = np.array(self.get_monthly_dhw_kwh())
        total = sum(h) + sum(c) + sum(d)

        months_short = ["J", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"]
        x = np.arange(12)
        width = 0.6

        # Oben: Monatliche Verteilung (kWh)
        ax1 = self.preview_fig.add_subplot(211)
        if total > 0:
            ax1.bar(x, h, width, label="Heizen", color="#e74c3c", alpha=0.85)
            ax1.bar(x, c, width, bottom=h, label="Kühlen", color="#3498db", alpha=0.85)
            ax1.bar(x, d, width, bottom=h + c, label="Warmwasser", color="#2ecc71", alpha=0.85)
        else:
            ax1.text(0.5, 0.5, "Keine Daten.\nVorlage laden oder\neingeben.",
                     ha="center", va="center", fontsize=11, color="gray",
                     transform=ax1.transAxes)
            ax1.set_xlim(-0.5, 11.5)
            ax1.set_ylim(0, 1)

        ax1.set_ylabel("kWh")
        ax1.set_xticks(x)
        ax1.set_xticklabels(months_short, fontsize=8)
        if total > 0:
            ax1.legend(loc="upper right", fontsize=8)
            ax1.grid(True, alpha=0.3, axis="y")
        ax1.set_title("Monatliche Verteilung", fontsize=10)

        # Unten: Entzugsleistung (W/m) als Zeitreihe
        ax2 = self.preview_fig.add_subplot(212)
        depth = safe_float(
            self.app.entries.get("initial_depth", tk.Entry()).get() or "100",
            default=100.0
        )
        n_bh = int(safe_float(
            self.app.borehole_entries.get("num_boreholes", tk.Entry()).get() or "1",
            default=1.0
        ))
        try:
            e_cop = self.app.entries.get("heat_pump_cop")
            e_eer = self.app.entries.get("heat_pump_eer")
            cop = safe_float(e_cop.get() if e_cop else "4.0", default=4.0)
            eer = safe_float(e_eer.get() if e_eer else "4.0", default=4.0)
        except (AttributeError, KeyError):
            cop, eer = 4.0, 4.0
        total_length = depth * n_bh if n_bh > 0 else 1.0

        h_wm, c_wm, net_wm = calculate_monthly_extraction_rate_w_per_m(
            list(h), list(c), cop, eer, total_length
        )
        h_wm_arr = np.array(h_wm)
        c_wm_arr = np.array(c_wm)
        net_wm_arr = np.array(net_wm)

        if any(h_wm_arr != 0) or any(c_wm_arr != 0):
            ax2.bar(x - 0.2, h_wm_arr, 0.35, label="Entzug (Heizen)", color="#e74c3c", alpha=0.85)
            ax2.bar(x + 0.2, [-v for v in c_wm_arr], 0.35, label="Eintrag (Kühlen)", color="#3498db", alpha=0.85)
            ax2.axhline(0, color="black", linewidth=0.5)
        else:
            ax2.text(0.5, 0.5, "W/m: Sondentiefe und Bohrungen eingeben.",
                     ha="center", va="center", fontsize=9, color="gray",
                     transform=ax2.transAxes)

        ax2.set_xlabel("Monat")
        ax2.set_ylabel("W/m")
        ax2.set_xticks(x)
        ax2.set_xticklabels(months_short, fontsize=8)
        if any(h_wm_arr != 0) or any(c_wm_arr != 0):
            ax2.legend(loc="upper right", fontsize=8)
            ax2.grid(True, alpha=0.3, axis="y")
        ax2.set_title("Monatliche Entzugsleistung (W/m)", fontsize=10)

        self.preview_fig.tight_layout()
        self.preview_canvas.draw()

        if hasattr(self, 'stats_label'):
            self.stats_label.config(
                text=f"Heizen: {sum(h):.0f} kWh  |  Kühlen: {sum(c):.0f} kWh  |  Σ: {total:.0f} kWh"
            )

    def _sync_to_annual_entries(self):
        """Synchronisiert Tabellensummen zurück zu Jahres-Heizen/Kühlen."""
        sum_h = sum(
            safe_float(e.get() or "0", default=0.0)
            for e in self.monthly_heating_entries
        )
        sum_c = sum(
            safe_float(e.get() or "0", default=0.0)
            for e in self.monthly_cooling_entries
        )
        if "annual_heating" in self.app.entries:
            self.app.entries["annual_heating"].delete(0, tk.END)
            self.app.entries["annual_heating"].insert(0, f"{sum_h:.1f}")
        if "annual_cooling" in self.app.entries:
            self.app.entries["annual_cooling"].delete(0, tk.END)
            self.app.entries["annual_cooling"].insert(0, f"{sum_c:.1f}")

    def load_from_annual_entries(self):
        """Lädt Jahreswerte aus Eingabe-Tab und verteilt mit Vorlage."""
        annual_h = safe_float(
            self.app.entries.get("annual_heating", tk.Entry()).get() or "12000",
            default=12000.0
        )
        annual_c = safe_float(
            self.app.entries.get("annual_cooling", tk.Entry()).get() or "0",
            default=0.0
        )
        h_factors, c_factors = get_load_profile_template(
            self.template_var.get()
        )
        for i, (hf, cf) in enumerate(zip(h_factors, c_factors)):
            self.monthly_heating_entries[i].delete(0, tk.END)
            self.monthly_heating_entries[i].insert(0, f"{annual_h * hf:.1f}")
            self.monthly_cooling_entries[i].delete(0, tk.END)
            self.monthly_cooling_entries[i].insert(0, f"{annual_c * cf:.1f}")
        self._update_sums()

    # ─── API für Berechnung ───

    def get_monthly_heating_kwh(self) -> List[float]:
        """Gibt 12 Heizlast-Werte [kWh] zurück."""
        return [
            safe_float(e.get() or "0", default=0.0)
            for e in self.monthly_heating_entries
        ]

    def get_monthly_cooling_kwh(self) -> List[float]:
        """Gibt 12 Kühllast-Werte [kWh] zurück."""
        return [
            safe_float(e.get() or "0", default=0.0)
            for e in self.monthly_cooling_entries
        ]

    def get_monthly_heating_factors(self) -> List[float]:
        """Gibt 12 Heizfaktoren zurück (Anteile, Summe=1)."""
        vals = self.get_monthly_heating_kwh()
        return monthly_values_to_factors(vals)

    def get_monthly_cooling_factors(self) -> List[float]:
        """Gibt 12 Kühlfaktoren zurück (Anteile, Summe=1)."""
        vals = self.get_monthly_cooling_kwh()
        return monthly_values_to_factors(vals)

    def get_monthly_dhw_kwh(self) -> List[float]:
        """Gibt 12 Warmwasser-Werte [kWh] zurück (0 wenn deaktiviert)."""
        if not self.dhw_enabled_var.get():
            return [0.0] * 12
        n = safe_float(self.dhw_persons_entry.get() or "4", default=4)
        return get_monthly_dhw_distribution(int(n))

    def get_load_profile_data(self) -> dict:
        """Sammelt alle Lastprofil-Daten für Export/Diagramme."""
        return {
            "monthly_heating_kwh": self.get_monthly_heating_kwh(),
            "monthly_cooling_kwh": self.get_monthly_cooling_kwh(),
            "monthly_dhw_kwh": self.get_monthly_dhw_kwh(),
            "dhw_enabled": self.dhw_enabled_var.get(),
            "dhw_persons": safe_float(
                self.dhw_persons_entry.get() or "4", default=4),
        }

    def set_load_profile_data(self, data: dict):
        """Lädt Lastprofil-Daten (z.B. aus .get Datei)."""
        h = data.get("monthly_heating_kwh")
        c = data.get("monthly_cooling_kwh")
        if h and len(h) == 12:
            for i, v in enumerate(h):
                self.monthly_heating_entries[i].delete(0, tk.END)
                self.monthly_heating_entries[i].insert(0, f"{v:.1f}")
        if c and len(c) == 12:
            for i, v in enumerate(c):
                self.monthly_cooling_entries[i].delete(0, tk.END)
                self.monthly_cooling_entries[i].insert(0, f"{v:.1f}")
        self.dhw_enabled_var.set(data.get("dhw_enabled", True))
        if "dhw_persons" in data:
            self.dhw_persons_entry.delete(0, tk.END)
            self.dhw_persons_entry.insert(0, str(int(data["dhw_persons"])))
        self._update_sums()
        self._sync_to_annual_entries()

    def _export_diagram(self, fmt: str):
        """Exportiert Lastprofil-Diagramm als PNG oder PDF."""
        import numpy as np
        from matplotlib.figure import Figure

        data = self.get_load_profile_data()
        if not data or (sum(data["monthly_heating_kwh"]) == 0
                       and sum(data["monthly_cooling_kwh"]) == 0
                       and sum(data["monthly_dhw_kwh"]) == 0):
            messagebox.showwarning(
                "Keine Daten",
                "Bitte zuerst Lastprofil-Daten eingeben.")
            return

        ext = ".png" if fmt == "png" else ".pdf"
        filetypes = [("PNG", "*.png")] if fmt == "png" else [("PDF", "*.pdf")]
        filename = filedialog.asksaveasfilename(
            defaultextension=ext,
            filetypes=filetypes,
            title=f"Lastprofil als {fmt.upper()} speichern"
        )
        if not filename:
            return

        try:
            fig = Figure(figsize=(10, 6), dpi=150)
            ax = fig.add_subplot(111)

            months = ["Jan", "Feb", "Mär", "Apr", "Mai", "Jun",
                      "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"]
            x = np.arange(len(months))
            width = 0.6

            h = np.array(data["monthly_heating_kwh"])
            c = np.array(data["monthly_cooling_kwh"])
            d = np.array(data["monthly_dhw_kwh"])

            ax.bar(x, h, width, label="Heizen", color="#e74c3c", alpha=0.8)
            ax.bar(x, c, width, bottom=h, label="Kühlen", color="#3498db", alpha=0.8)
            ax.bar(x, d, width, bottom=h + c, label="Warmwasser",
                   color="#2ecc71", alpha=0.8)

            ax.set_xlabel("Monat", fontsize=11, fontweight="bold")
            ax.set_ylabel("Energie [kWh]", fontsize=11, fontweight="bold")
            ax.set_title("Lastprofil: Heizen + Kühlen + Warmwasser pro Monat",
                         fontsize=12, fontweight="bold")
            ax.set_xticks(x)
            ax.set_xticklabels(months)
            ax.legend(loc="upper right", fontsize=9)
            ax.grid(True, alpha=0.3, axis="y")
            fig.tight_layout()
            fig.savefig(filename, dpi=150, bbox_inches="tight")
            self.app.status_var.set(f"✓ Diagramm exportiert: {filename}")
            messagebox.showinfo("Erfolg", f"Diagramm wurde als {fmt.upper()} gespeichert.")
        except Exception as e:
            import traceback
            traceback.print_exc()
            messagebox.showerror("Fehler", f"Export fehlgeschlagen: {str(e)}")
