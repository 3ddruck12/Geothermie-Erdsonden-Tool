"""Controller für .get-Datei Import/Export und GUI-Populating.

Extrahiert aus main_window_v3_professional.py (V3.4 Refactoring).
V3.4: Auto-Save und save_to_path hinzugefügt.
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
from typing import Any, Dict
import logging

logger = logging.getLogger(__name__)


class FileController:
    """Verwaltet Import/Export von .get-Projektdateien und Bohranzeige-PDF.

    Alle GUI-Referenzen werden über ``self.app`` aufgelöst.
    """

    def __init__(self, app):
        self.app = app

    def _build_loads_dict(self, params: Dict, hp_data: Dict) -> Dict:
        """Baut das loads-Dict für Export inkl. Lastprofil-Daten."""
        loads = {
            "annual_heating_kwh": params.get("annual_heating", 45000.0),
            "annual_cooling_kwh": params.get("annual_cooling", 0.0),
            "peak_heating_kw": params.get("peak_heating", 12.5),
            "peak_cooling_kw": params.get("peak_cooling", 0.0),
            "heat_pump_cop": hp_data.get("cop_heating", 4.5),
        }
        if hasattr(self.app, 'load_profiles_tab') and self.app.load_profiles_tab:
            lp_data = self.app.load_profiles_tab.get_load_profile_data()
            loads["monthly_heating_kwh"] = lp_data.get("monthly_heating_kwh", [])
            loads["monthly_cooling_kwh"] = lp_data.get("monthly_cooling_kwh", [])
            loads["monthly_dhw_kwh"] = lp_data.get("monthly_dhw_kwh", [])
            loads["dhw_enabled"] = lp_data.get("dhw_enabled", True)
            loads["dhw_persons"] = lp_data.get("dhw_persons", 4)
        return loads

    # ──────────────── .get Export ────────────────

    def export_get_file(self):
        """Exportiert aktuelles Projekt als .get Datei."""
        app = self.app
        filepath = filedialog.asksaveasfilename(
            defaultextension=".get",
            filetypes=[("GET Projekt", "*.get"), ("Alle Dateien", "*.*")],
            title="Projekt speichern")
        if not filepath:
            return
        try:
            params = self._collect_entry_values(app.entries)
            project_data = {k: e.get() for k, e in app.project_entries.items()}
            borehole_data = self._collect_entry_values(app.borehole_entries)
            hp_data = self._collect_entry_values(app.heat_pump_entries)

            success = app.get_handler.export_to_get(
                filepath=filepath,
                metadata={
                    "project_name": project_data.get("project_name", ""),
                    "location": (f"{project_data.get('city', '')} "
                                 f"{project_data.get('postal_code', '')}"),
                    "designer": project_data.get("customer_name", ""),
                    "date": project_data.get("date", ""),
                    "notes": project_data.get("address", ""),
                },
                ground_props={
                    "thermal_conductivity": params.get("ground_thermal_cond", 2.5),
                    "heat_capacity": params.get("ground_heat_cap", 2.4e6),
                    "undisturbed_temp": params.get("ground_temp", 10.0),
                    "geothermal_gradient": params.get("geothermal_gradient", 0.03),
                    "soil_type": (app.soil_type_var.get()
                                  if hasattr(app, 'soil_type_var') else ""),
                },
                borehole_config={
                    "diameter_mm": params.get("borehole_diameter", 152.0),
                    "depth_m": params.get("initial_depth", 100.0),
                    "pipe_configuration": app.pipe_config_var.get(),
                    "shank_spacing_mm": float(
                        app.entries.get("shank_spacing", ttk.Entry()).get()
                        or "65"),
                    "num_boreholes": int(borehole_data.get("num_boreholes", 1)),
                },
                pipe_props={
                    "material": (app.pipe_type_var.get()
                                 if hasattr(app, 'pipe_type_var')
                                 else "PE-100"),
                    "outer_diameter_mm": params.get("pipe_outer_diameter", 32.0),
                    "wall_thickness_mm": params.get("pipe_thickness", 2.9),
                    "thermal_conductivity": params.get("pipe_thermal_cond", 0.42),
                    "inner_diameter_mm": (
                        params.get("pipe_outer_diameter", 32.0)
                        - 2 * params.get("pipe_thickness", 2.9)),
                },
                grout_material={
                    "name": (app.grout_type_var.get()
                             if hasattr(app, 'grout_type_var') else ""),
                    "thermal_conductivity": params.get("grout_thermal_cond", 2.0),
                    "density": 1800.0,
                    "volume_per_borehole_liters": (
                        app.grout_calculation.get('volume_liters', 0.0)
                        if app.grout_calculation else 0.0),
                },
                fluid_props={
                    "type": "Wasser/Glykol",
                    "thermal_conductivity": params.get("fluid_thermal_cond", 0.48),
                    "heat_capacity": params.get("fluid_heat_cap", 3795.0),
                    "density": params.get("fluid_density", 1042.0),
                    "viscosity": params.get("fluid_viscosity", 0.00345),
                    "flow_rate_m3h": params.get("fluid_flow_rate", 1.8),
                    "freeze_temperature": -15.0,
                },
                fluid_database_info=(
                    {
                        "fluid_name": app.fluid_var.get(),
                        "operating_temperature": float(
                            app.entries.get("fluid_temperature",
                                            ttk.Entry()).get() or "5.0"
                        ) if "fluid_temperature" in app.entries else 5.0,
                    }
                    if (hasattr(app, 'fluid_var') and app.fluid_var.get())
                    else None
                ),
                loads=self._build_loads_dict(params, hp_data),
                temp_limits={
                    "min_fluid_temp": params.get("min_fluid_temp", -3.0),
                    "max_fluid_temp": params.get("max_fluid_temp", 20.0),
                },
                simulation={
                    "years": int(params.get("simulation_years", 50)),
                    "initial_depth": params.get("initial_depth", 100.0),
                    "calculation_method": (
                        app.calculation_method_var.get()
                        if hasattr(app, 'calculation_method_var')
                        else "iterativ"),
                    "heat_pump_eer": params.get(
                        "heat_pump_eer", params.get("heat_pump_cop", 4.0)),
                    "delta_t_fluid": params.get("delta_t_fluid", 3.0),
                    "max_depth_per_borehole": float(
                        app.borehole_entries.get(
                            "max_depth_per_borehole", ttk.Entry()
                        ).get() or "100.0"
                    ) if "max_depth_per_borehole" in app.borehole_entries
                    else 100.0,
                },
                climate_data=app.climate_data,
                borefield_data=app.borefield_config,
                results={
                    "standard": (app.result.__dict__
                                 if app.result and hasattr(app.result, '__dict__')
                                 else None),
                    "vdi4640": (app.vdi4640_result.__dict__
                                if hasattr(app, 'vdi4640_result')
                                and app.vdi4640_result else None),
                },
                vdi4640_result=(
                    app.vdi4640_result.__dict__
                    if hasattr(app, 'vdi4640_result') and app.vdi4640_result
                    else None),
                hydraulics_result=(
                    app.hydraulics_result
                    if hasattr(app, 'hydraulics_result')
                    and app.hydraulics_result else None),
                grout_calculation=(
                    app.grout_calculation
                    if hasattr(app, 'grout_calculation')
                    and app.grout_calculation else None),
                diagrams={
                    "pump_characteristics": {"enabled": True},
                    "reynolds_curve": {"enabled": True,
                                       "glycol_concentrations": [0, 25, 30, 40]},
                    "pressure_components": {"enabled": True,
                                             "chart_type": "pie"},
                    "flow_vs_pressure": {"enabled": True},
                    "pump_power_time": {"enabled": True},
                    "temperature_spread": {"enabled": True},
                    "cop_inlet_temp": {"enabled": True},
                    "cop_flow_temp": {"enabled": True},
                    "jaz_estimation": {"enabled": True},
                    "energy_consumption": {"enabled": True,
                                            "show_10_year": True},
                },
                bohranzeige_data=(
                    app.bohranzeige_tab.collect_all_data()
                    if hasattr(app, 'bohranzeige_tab') else None),
            )

            if success:
                app._current_file_path = filepath
                messagebox.showinfo(
                    "Erfolg",
                    f"✅ Projekt gespeichert:\n{os.path.basename(filepath)}")
                app.status_var.set(
                    f"💾 Gespeichert: {os.path.basename(filepath)}")
            else:
                messagebox.showerror("Fehler", "❌ Speichern fehlgeschlagen")
        except Exception as e:
            messagebox.showerror("Fehler", f"❌ Export-Fehler:\n{str(e)}")

    # ──────────────── .get Import ────────────────

    def import_get_file(self):
        """Importiert ein .get Projekt."""
        app = self.app
        filepath = filedialog.askopenfilename(
            filetypes=[("GET Projekt", "*.get"), ("Alle Dateien", "*.*")],
            title="Projekt laden")
        if not filepath:
            return
        try:
            data = app.get_handler.import_from_get(filepath)
            if not data:
                messagebox.showerror(
                    "Fehler", "❌ Datei konnte nicht geladen werden")
                return

            version = data.get("format_version", "unbekannt")
            if version != app.get_handler.format_version:
                messagebox.showinfo(
                    "Migration",
                    f"🔄 Datei wurde von Version {version} auf "
                    f"{app.get_handler.format_version} migriert")

            self._populate_from_get_data(data)
            app._current_file_path = filepath
            messagebox.showinfo(
                "Erfolg",
                f"✅ Projekt geladen:\n{os.path.basename(filepath)}")
            app.status_var.set(
                f"📥 Geladen: {os.path.basename(filepath)}")
        except Exception as e:
            messagebox.showerror("Fehler", f"❌ Import-Fehler:\n{str(e)}")

    # ──────────────── Bohranzeige PDF ────────────────

    def export_bohranzeige_pdf(self, data: Dict[str, Any]):
        """Exportiert die Bohranzeige als PDF."""
        app = self.app
        filepath = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF Dateien", "*.pdf"), ("Alle Dateien", "*.*")],
            title="Bohranzeige als PDF speichern",
            initialfile=f"Bohranzeige_{datetime.now().strftime('%Y%m%d')}.pdf")
        if not filepath:
            return
        try:
            technik_raw = data.get('technik', {})
            technik_pdf = {}
            for key, val in technik_raw.items():
                if isinstance(val, str):
                    try:
                        num = float(val.split()[0].replace(",", ""))
                        technik_pdf[key] = num
                    except (ValueError, IndexError):
                        technik_pdf[key] = val
                else:
                    technik_pdf[key] = val

            pdf_data = {
                'antragsteller': data.get('antragsteller', {}),
                'grundstueck': data.get('grundstueck', {}),
                'koordinaten': data.get('koordinaten', {}),
                'bohrunternehmen': data.get('bohrunternehmen', {}),
                'ausfuehrung': data.get('ausfuehrung', {}),
                'technik': technik_pdf,
                'gewaesserschutz': data.get('gewaesserschutz', {}),
            }

            success = app.bohranzeige_pdf.generate(filepath, pdf_data)
            if success:
                messagebox.showinfo(
                    "Erfolg",
                    f"✅ Bohranzeige gespeichert:\n{os.path.basename(filepath)}")
                app.status_var.set(
                    f"📄 Bohranzeige: {os.path.basename(filepath)}")
            else:
                messagebox.showerror(
                    "Fehler", "❌ PDF-Erstellung fehlgeschlagen")
        except Exception as e:
            messagebox.showerror(
                "Fehler", f"❌ Bohranzeige-Fehler:\n{str(e)}")

    # ──────────────── GUI Populating ────────────────

    def _populate_from_get_data(self, data: Dict[str, Any]):
        """Füllt GUI mit Daten aus .get Datei."""
        app = self.app
        try:
            # Bodeneigenschaften
            ground = data.get("ground_properties", {})
            self._set_entry("ground_thermal_cond",
                            ground.get("thermal_conductivity", 2.5))
            self._set_entry("ground_heat_cap",
                            ground.get("heat_capacity", 2.4e6))
            self._set_entry("ground_temp",
                            ground.get("undisturbed_temp", 10.0))
            self._set_entry("geothermal_gradient",
                            ground.get("geothermal_gradient", 0.03))

            # Bohrloch
            borehole = data.get("borehole_config", {})
            self._set_entry("borehole_diameter",
                            borehole.get("diameter_mm", 152.0))
            self._set_entry("initial_depth",
                            borehole.get("depth_m", 100.0))
            self._set_entry("shank_spacing",
                            borehole.get("shank_spacing_mm", 80.0))
            if hasattr(app, 'pipe_config_var'):
                app.pipe_config_var.set(
                    borehole.get("pipe_configuration", "2-rohr-u (Serie)"))

            # Rohre
            pipe = data.get("pipe_properties", {})
            self._set_entry("pipe_outer_diameter",
                            pipe.get("outer_diameter_mm", 32.0))
            self._set_entry("pipe_thickness",
                            pipe.get("wall_thickness_mm", 2.9))
            self._set_entry("pipe_thermal_cond",
                            pipe.get("thermal_conductivity", 0.42))

            # Verfüllung
            grout = data.get("grout_material", {})
            self._set_entry("grout_thermal_cond",
                            grout.get("thermal_conductivity", 2.0))

            # Fluid
            fluid = data.get("heat_carrier_fluid", {})
            self._set_entry("fluid_thermal_cond",
                            fluid.get("thermal_conductivity", 0.48))
            self._set_entry("fluid_heat_cap",
                            fluid.get("heat_capacity", 3795.0))
            self._set_entry("fluid_density", fluid.get("density", 1042.0))
            self._set_entry("fluid_viscosity",
                            fluid.get("viscosity", 0.00345))
            self._set_entry("fluid_flow_rate",
                            fluid.get("flow_rate_m3h", 1.8))

            # Lasten
            loads = data.get("loads", {})
            self._set_entry("annual_heating",
                            loads.get("annual_heating_kwh", 45000.0))
            self._set_entry("annual_cooling",
                            loads.get("annual_cooling_kwh", 0.0))
            self._set_entry("peak_heating",
                            loads.get("peak_heating_kw", 12.5))
            self._set_entry("peak_cooling",
                            loads.get("peak_cooling_kw", 0.0))

            # Lastprofile (monatliche Werte, Warmwasser)
            if (hasattr(app, 'load_profiles_tab') and app.load_profiles_tab
                    and any(k in loads for k in ("monthly_heating_kwh",
                                                 "monthly_cooling_kwh",
                                                 "dhw_enabled"))):
                lp_data = {
                    "monthly_heating_kwh": loads.get("monthly_heating_kwh"),
                    "monthly_cooling_kwh": loads.get("monthly_cooling_kwh"),
                    "monthly_dhw_kwh": loads.get("monthly_dhw_kwh"),
                    "dhw_enabled": loads.get("dhw_enabled", True),
                    "dhw_persons": loads.get("dhw_persons", 4),
                }
                app.load_profiles_tab.set_load_profile_data(lp_data)

            # Temperaturgrenzen
            temp = data.get("temperature_limits", {})
            self._set_entry("min_fluid_temp",
                            temp.get("min_fluid_temp", -3.0))
            self._set_entry("max_fluid_temp",
                            temp.get("max_fluid_temp", 20.0))

            # Simulation
            sim = data.get("simulation_settings", {})
            self._set_entry("simulation_years", sim.get("years", 50))
            if hasattr(app, 'calculation_method_var'):
                app.calculation_method_var.set(
                    sim.get("calculation_method", "iterativ"))
            if "heat_pump_eer" in sim:
                self._set_entry("heat_pump_eer",
                                sim.get("heat_pump_eer", 4.0))
            if "delta_t_fluid" in sim:
                self._set_entry("delta_t_fluid",
                                sim.get("delta_t_fluid", 3.0))
            if "max_depth_per_borehole" in sim:
                if "max_depth_per_borehole" in app.borehole_entries:
                    app.borehole_entries["max_depth_per_borehole"].delete(
                        0, tk.END)
                    app.borehole_entries["max_depth_per_borehole"].insert(
                        0, str(sim.get("max_depth_per_borehole", 100.0)))

            # Fluid-Datenbank
            fluid_db_info = data.get("fluid_database_info")
            if fluid_db_info and hasattr(app, 'fluid_var'):
                fluid_name = fluid_db_info.get("fluid_name")
                if fluid_name and fluid_name in app.fluid_db.get_all_names():
                    app.fluid_var.set(fluid_name)
                    app._on_fluid_selected(None)
                if ("operating_temperature" in fluid_db_info
                        and "fluid_temperature" in app.entries):
                    app.entries["fluid_temperature"].delete(0, tk.END)
                    app.entries["fluid_temperature"].insert(
                        0, str(fluid_db_info["operating_temperature"]))
                    app._on_fluid_temperature_changed()

            # VDI 4640 Ergebnis
            vdi_result = data.get("vdi4640_result")
            if vdi_result:
                from calculations.vdi4640 import VDI4640Result
                if isinstance(vdi_result, dict):
                    try:
                        app.vdi4640_result = VDI4640Result(**vdi_result)
                    except Exception as e:
                        print(
                            f"⚠️ Konnte VDI4640Result nicht "
                            f"rekonstruieren: {e}")
                        app.vdi4640_result = vdi_result
                else:
                    app.vdi4640_result = vdi_result

            # Hydraulik
            hydraulics_result = data.get("hydraulics_result")
            if hydraulics_result:
                app.hydraulics_result = hydraulics_result
                if hasattr(app, 'hydraulics_result_text'):
                    text = ("=" * 60 + "\n"
                            "HYDRAULIK-BERECHNUNG (aus .get Datei geladen)\n"
                            + "=" * 60 + "\n\n")
                    fl = hydraulics_result.get('flow', {})
                    sy = hydraulics_result.get('system', {})
                    pu = hydraulics_result.get('pump', {})
                    if fl and sy and pu:
                        text += (
                            f"Volumenstrom: "
                            f"{fl.get('volume_flow_m3_h', 0):.3f} m³/h\n"
                            f"Druckverlust: "
                            f"{sy.get('total_pressure_drop_bar', 0):.2f} bar\n"
                            f"Pumpenleistung: "
                            f"{pu.get('electric_power_w', 0):.0f} W\n")
                    app.hydraulics_result_text.delete("1.0", tk.END)
                    app.hydraulics_result_text.insert("1.0", text)

            # Verfüllmaterial
            grout_calc = data.get("grout_calculation")
            if grout_calc:
                app.grout_calculation = grout_calc
                if hasattr(app, 'grout_result_text'):
                    material = grout_calc.get('material', {})
                    amounts = grout_calc.get('amounts', {})
                    text = ("=" * 60 + "\n"
                            "VERFÜLLMATERIAL-BERECHNUNG "
                            "(aus .get Datei geladen)\n"
                            + "=" * 60 + "\n\n")
                    if isinstance(material, dict):
                        text += f"Material: {material.get('name', 'N/A')}\n"
                        text += (f"Volumen gesamt: "
                                 f"{amounts.get('mass_kg', 0):.1f} kg\n")
                    app.grout_result_text.delete("1.0", tk.END)
                    app.grout_result_text.insert("1.0", text)

            app.climate_data = data.get("climate_data")
            app.borefield_config = data.get("borefield_v32")

            # Bohranzeige
            bohranzeige = data.get("bohranzeige_data")
            if bohranzeige and hasattr(app, 'bohranzeige_tab'):
                app.bohranzeige_tab.set_data(bohranzeige)

            # Bohrfeld-Tab
            if (app.borefield_config
                    and app.borefield_config.get("enabled")):
                self.populate_borefield_tab(app.borefield_config)

            print("✅ GUI mit .get Daten gefüllt")

        except Exception as e:
            print(f"⚠️ Fehler beim Füllen der GUI: {e}")

    def populate_borefield_tab(self, borefield_data: Dict[str, Any]):
        """Füllt Bohrfeld-Tab mit geladenen Daten."""
        app = self.app
        try:
            if not hasattr(app, 'borefield_entries'):
                return

            if hasattr(app, 'borefield_layout_var'):
                app.borefield_layout_var.set(
                    borefield_data.get('layout', 'rectangle'))

            fields = {
                'num_x': ('num_boreholes_x', 3),
                'num_y': ('num_boreholes_y', 2),
                'spacing_x': ('spacing_x_m', 6.5),
                'spacing_y': ('spacing_y_m', 6.5),
            }
            for key, (data_key, default) in fields.items():
                app.borefield_entries[key].delete(0, tk.END)
                app.borefield_entries[key].insert(
                    0, str(borefield_data.get(data_key, default)))

            # Durchmesser
            if 'borehole_diameter_mm' in borefield_data:
                app.borefield_entries['diameter'].delete(0, tk.END)
                app.borefield_entries['diameter'].insert(
                    0, str(borefield_data.get('borehole_diameter_mm', 152.0)))
            elif 'borehole_radius_m' in borefield_data:
                diam_mm = borefield_data.get('borehole_radius_m', 0.076) * 2000.0
                app.borefield_entries['diameter'].delete(0, tk.END)
                app.borefield_entries['diameter'].insert(0, str(diam_mm))
            elif 'borehole_diameter' in app.entries:
                try:
                    app.borefield_entries['diameter'].delete(0, tk.END)
                    app.borefield_entries['diameter'].insert(
                        0, app.entries['borehole_diameter'].get())
                except Exception:
                    pass

            diff = borefield_data.get('soil_thermal_diffusivity', 1.0e-6)
            app.borefield_entries['diffusivity'].delete(0, tk.END)
            app.borefield_entries['diffusivity'].insert(0, str(diff))

            app.borefield_entries['years'].delete(0, tk.END)
            app.borefield_entries['years'].insert(
                0, str(borefield_data.get('simulation_years', 25)))

            if hasattr(app, 'borefield_result_text'):
                app.borefield_result_text.config(state="normal")
                app.borefield_result_text.delete("1.0", tk.END)
                layout = borefield_data.get('layout', 'N/A').upper()
                nx = borefield_data.get('num_boreholes_x', 0)
                ny = borefield_data.get('num_boreholes_y', 0)
                sx = borefield_data.get('spacing_x_m', 0)
                sy = borefield_data.get('spacing_y_m', 0)
                app.borefield_result_text.insert(
                    "1.0",
                    f"📥 Bohrfeld-Konfiguration geladen!\n\n"
                    f"Layout: {layout}\n"
                    f"Bohrungen: {nx}×{ny}\n"
                    f"Abstand: {sx} × {sy} m\n\n"
                    f"Klicke 'g-Funktion berechnen'\n"
                    f"um die Simulation zu starten.")
                app.borefield_result_text.config(state="disabled")

            print(f"✅ Bohrfeld-Tab gefüllt: "
                  f"{borefield_data.get('layout', 'N/A').upper()}")

        except Exception as e:
            print(f"⚠️ Fehler beim Füllen des Bohrfeld-Tabs: {e}")

    # ──────────────── Hilfsmethoden ────────────────

    def _set_entry(self, key: str, value: Any):
        """Setzt Entry-Wert in einem der Dictionaries."""
        app = self.app
        entry = None
        for d in (app.entries, app.project_entries,
                  app.borehole_entries, app.heat_pump_entries):
            if key in d:
                entry = d[key]
                break
        if entry:
            was_readonly = entry.cget("state") == "readonly"
            if was_readonly:
                entry.config(state="normal")
            entry.delete(0, tk.END)
            entry.insert(0, str(value))

    @staticmethod
    def _collect_entry_values(entries_dict) -> dict:
        """Sammelt numerische/string Werte aus Entry-Dictionary."""
        result = {}
        for key, entry in entries_dict.items():
            try:
                result[key] = float(entry.get())
            except (ValueError, AttributeError):
                val = entry.get() if hasattr(entry, 'get') else ""
                result[key] = val if val else 0.0
        return result

    # ──────────────── Auto-Save ────────────────

    def save_to_path(self, filepath: str) -> bool:
        """Speichert Projekt still an den angegebenen Pfad (ohne Dialog).

        Verwendet die gleiche Logik wie export_get_file, aber ohne
        Dateidialog und Info-Meldung. Für Auto-Save.

        Args:
            filepath: Ziel-Dateipfad (.get)

        Returns:
            True bei Erfolg, False bei Fehler
        """
        app = self.app
        try:
            params = self._collect_entry_values(app.entries)
            project_data = {k: e.get() for k, e in app.project_entries.items()}
            borehole_data = self._collect_entry_values(app.borehole_entries)
            hp_data = self._collect_entry_values(app.heat_pump_entries)

            success = app.get_handler.export_to_get(
                filepath=filepath,
                metadata={
                    "project_name": project_data.get("project_name", ""),
                    "location": (f"{project_data.get('city', '')} "
                                 f"{project_data.get('postal_code', '')}"),
                    "designer": project_data.get("customer_name", ""),
                    "date": project_data.get("date", ""),
                    "notes": project_data.get("address", ""),
                },
                ground_props={
                    "thermal_conductivity": params.get("ground_thermal_cond", 2.5),
                    "heat_capacity": params.get("ground_heat_cap", 2.4e6),
                    "undisturbed_temp": params.get("ground_temp", 10.0),
                    "geothermal_gradient": params.get("geothermal_gradient", 0.03),
                    "soil_type": (app.soil_type_var.get()
                                  if hasattr(app, 'soil_type_var') else ""),
                },
                borehole_config={
                    "diameter_mm": params.get("borehole_diameter", 152.0),
                    "depth_m": params.get("initial_depth", 100.0),
                    "pipe_configuration": app.pipe_config_var.get(),
                    "shank_spacing_mm": float(
                        app.entries.get("shank_spacing", ttk.Entry()).get()
                        or "65"),
                    "num_boreholes": int(borehole_data.get("num_boreholes", 1)),
                },
                pipe_props={
                    "material": (app.pipe_type_var.get()
                                 if hasattr(app, 'pipe_type_var')
                                 else "PE-100"),
                    "outer_diameter_mm": params.get("pipe_outer_diameter", 32.0),
                    "wall_thickness_mm": params.get("pipe_thickness", 2.9),
                    "thermal_conductivity": params.get("pipe_thermal_cond", 0.42),
                    "inner_diameter_mm": (
                        params.get("pipe_outer_diameter", 32.0)
                        - 2 * params.get("pipe_thickness", 2.9)),
                },
                grout_material={
                    "name": (app.grout_type_var.get()
                             if hasattr(app, 'grout_type_var') else ""),
                    "thermal_conductivity": params.get("grout_thermal_cond", 2.0),
                    "density": 1800.0,
                    "volume_per_borehole_liters": (
                        app.grout_calculation.get('volume_liters', 0.0)
                        if app.grout_calculation else 0.0),
                },
                fluid_props={
                    "type": "Wasser/Glykol",
                    "thermal_conductivity": params.get("fluid_thermal_cond", 0.48),
                    "heat_capacity": params.get("fluid_heat_cap", 3795.0),
                    "density": params.get("fluid_density", 1042.0),
                    "viscosity": params.get("fluid_viscosity", 0.00345),
                    "flow_rate_m3h": params.get("fluid_flow_rate", 1.8),
                    "freeze_temperature": -15.0,
                },
                fluid_database_info=(
                    {
                        "fluid_name": app.fluid_var.get(),
                        "operating_temperature": float(
                            app.entries.get("fluid_temperature",
                                            ttk.Entry()).get() or "5.0"
                        ) if "fluid_temperature" in app.entries else 5.0,
                    }
                    if (hasattr(app, 'fluid_var') and app.fluid_var.get())
                    else None
                ),
                loads=self._build_loads_dict(params, hp_data),
                temp_limits={
                    "min_fluid_temp": params.get("min_fluid_temp", -3.0),
                    "max_fluid_temp": params.get("max_fluid_temp", 20.0),
                },
                simulation={
                    "years": int(params.get("simulation_years", 50)),
                    "initial_depth": params.get("initial_depth", 100.0),
                    "calculation_method": (
                        app.calculation_method_var.get()
                        if hasattr(app, 'calculation_method_var')
                        else "iterativ"),
                    "heat_pump_eer": params.get(
                        "heat_pump_eer", params.get("heat_pump_cop", 4.0)),
                    "delta_t_fluid": params.get("delta_t_fluid", 3.0),
                },
                climate_data=app.climate_data,
                borefield_data=app.borefield_config,
                results={
                    "standard": (app.result.__dict__
                                 if app.result and hasattr(app.result, '__dict__')
                                 else None),
                    "vdi4640": (app.vdi4640_result.__dict__
                                if hasattr(app, 'vdi4640_result')
                                and app.vdi4640_result else None),
                },
            )
            if success:
                logger.info(f"Auto-Save: {filepath}")
            return success
        except Exception as e:
            logger.error(f"Auto-Save fehlgeschlagen: {e}")
            return False
