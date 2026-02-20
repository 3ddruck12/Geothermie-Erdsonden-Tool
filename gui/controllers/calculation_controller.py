"""Controller für Berechnungssteuerung, Ergebnisanzeige, Materialmengen und Hydraulik.

Extrahiert aus main_window_v3_professional.py (V3.4 Refactoring).
V3.4: Input-Validierung und VDI 4640 Compliance-Check integriert.
Delegiert GUI-Zugriffe an die App-Referenz.
"""

import math
import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import logging

from utils.validators import (
    safe_float, validate_parameters, check_vdi4640_compliance,
    format_compliance_results, GUI_KEY_TO_VALIDATOR
)

logger = logging.getLogger(__name__)


class CalculationController:
    """Orchestriert Berechnung, Ergebnisanzeige, Materialmenge und Hydraulik.

    Alle GUI-Referenzen werden über ``self.app`` aufgelöst.
    """

    def __init__(self, app):
        """
        Args:
            app: Referenz auf GeothermieGUIProfessional (shared state).
        """
        self.app = app

    # ──────────────── Hauptberechnung ────────────────

    def run_calculation(self):
        """Führt die Hauptberechnung (iterativ oder VDI 4640) durch."""
        app = self.app
        try:
            # V3.4: Input-Validierung vor Berechnung
            if hasattr(app, 'input_tab') and hasattr(app.input_tab, 'validate_all_entries'):
                errors = app.input_tab.validate_all_entries()
                if errors:
                    error_text = "Folgende Eingaben sind ungültig:\n\n"
                    for err in errors:
                        error_text += f"• {err}\n"
                    error_text += "\nBitte korrigieren Sie die rot markierten Felder."
                    messagebox.showwarning("Eingabe-Validierung", error_text)
                    app.status_var.set("❌ Validierung fehlgeschlagen")
                    return

            # Parameter sammeln (mit safe_float für Komma-Unterstützung)
            params = {}
            for key, entry in app.entries.items():
                value = entry.get()
                if value:
                    converted = safe_float(value, default=None)
                    if converted is not None:
                        params[key] = converted
                    else:
                        params[key] = value
                else:
                    params[key] = 0.0

            # mm → m
            params["pipe_outer_diameter"] = params["pipe_outer_diameter"] / 1000.0
            params["pipe_thickness"] = params["pipe_thickness"] / 1000.0
            params["borehole_diameter"] = params["borehole_diameter"] / 1000.0
            params["shank_spacing"] = params["shank_spacing"] / 1000.0

            app.status_var.set("⏳ Berechnung läuft...")
            app.root.update()

            pipe_config = app.pipe_config_var.get()
            if "4-rohr" in pipe_config:
                pipe_config = "double-u"

            num_boreholes = int(app.borehole_entries["num_boreholes"].get())
            method = app.calculation_method_var.get()

            if method == "vdi4640":
                self._run_vdi4640(params, pipe_config, num_boreholes)
            else:
                self._run_iterative(params, pipe_config, num_boreholes)

            app.current_params = params
            app.current_params['pipe_configuration'] = app.pipe_config_var.get()
            app.current_params['calculation_method'] = method

            self.display_results()
            self._plot_results()

            # V3.4: VDI 4640 Compliance-Check nach Berechnung
            self._run_compliance_check(params, num_boreholes)

            app.notebook.select(app.results_frame)

        except Exception as e:
            import traceback
            traceback.print_exc()
            messagebox.showerror("Fehler",
                                 f"Fehler bei der Berechnung: {str(e)}")
            app.status_var.set("❌ Berechnung fehlgeschlagen")

    def _run_compliance_check(self, params, num_boreholes):
        """Führt VDI 4640 Compliance-Check nach Berechnung durch."""
        app = self.app
        try:
            # Borehole-Entrys auch einbeziehen
            check_params = dict(params)
            for key, entry in app.borehole_entries.items():
                val = safe_float(entry.get(), default=None)
                if val is not None:
                    check_params[key] = val

            # Spez. Entzugsleistung ermitteln
            extraction_rate = None
            if app.result and hasattr(app.result, 'heat_extraction_rate'):
                extraction_rate = app.result.heat_extraction_rate

            soil_type = ""
            if hasattr(app, 'soil_type_var'):
                soil_type = app.soil_type_var.get()

            results = check_vdi4640_compliance(
                check_params, soil_type, extraction_rate)

            if results:
                compliance_text = format_compliance_results(results)
                # In Ergebnis-Tab anzeigen
                if hasattr(app, 'results_text'):
                    app.results_text.config(state=tk.NORMAL)
                    app.results_text.insert(tk.END, "\n" + compliance_text)
                    app.results_text.config(state=tk.DISABLED)

                # Statusleiste aktualisieren
                has_errors = any(r.level == "error" for r in results)
                has_warnings = any(r.level == "warning" for r in results)
                if has_errors:
                    status = app.status_var.get()
                    app.status_var.set(status + " | ❌ VDI 4640 Fehler")
                elif has_warnings:
                    status = app.status_var.get()
                    app.status_var.set(status + " | ⚠️ VDI 4640 Warnungen")

        except Exception as e:
            logger.warning(f"Compliance-Check Fehler: {e}")

    def _run_vdi4640(self, params, pipe_config, num_boreholes):
        """VDI 4640 Berechnungspfad."""
        app = self.app
        borehole_radius = params["borehole_diameter"] / 2
        pipe_outer_radius = params["pipe_outer_diameter"] / 2
        r_grout = (1 / (2 * math.pi * params["grout_thermal_cond"])) * \
                  math.log(borehole_radius / pipe_outer_radius)
        pipe_inner_radius = (params["pipe_outer_diameter"] -
                             2 * params["pipe_thickness"]) / 2
        r_pipe = (1 / (2 * math.pi * params["pipe_thermal_cond"])) * \
                 math.log(params["pipe_outer_diameter"] / (2 * pipe_inner_radius))
        r_conv = 1 / (2 * math.pi * pipe_inner_radius * 500)

        if pipe_config == "single-u":
            r_borehole = r_grout + r_pipe + r_conv
        else:
            r_borehole = 0.8 * (r_grout + r_pipe + r_conv)
        r_borehole = max(0.05, r_borehole)

        thermal_diffusivity = (params["ground_thermal_cond"] /
                               params["ground_heat_cap"])

        # Monatliche Faktoren aus Lastprofil-Tab (falls vorhanden)
        monthly_heating_factors = None
        monthly_cooling_factors = None
        if hasattr(app, 'load_profiles_tab') and app.load_profiles_tab:
            monthly_heating_factors = app.load_profiles_tab.get_monthly_heating_factors()
            monthly_cooling_factors = app.load_profiles_tab.get_monthly_cooling_factors()

        app.vdi4640_result = app.vdi4640_calc.calculate_complete(
            ground_thermal_conductivity=params["ground_thermal_cond"],
            ground_thermal_diffusivity=thermal_diffusivity,
            t_undisturbed=params["ground_temp"],
            borehole_diameter=params["borehole_diameter"] * 1000,
            borehole_depth_initial=params["initial_depth"],
            n_boreholes=num_boreholes,
            r_borehole=r_borehole,
            annual_heating_demand=params["annual_heating"],
            peak_heating_load=params["peak_heating"],
            annual_cooling_demand=params["annual_cooling"],
            peak_cooling_load=params["peak_cooling"],
            heat_pump_cop_heating=params["heat_pump_cop"],
            heat_pump_cop_cooling=params.get("heat_pump_eer",
                                             params["heat_pump_cop"]),
            t_fluid_min_required=params["min_fluid_temp"],
            t_fluid_max_required=params["max_fluid_temp"],
            delta_t_fluid=params.get("delta_t_fluid", 3.0),
            monthly_heating_factors=monthly_heating_factors,
            monthly_cooling_factors=monthly_cooling_factors
        )

        # Warnung bei Überschreitung maximaler Sondenlänge
        max_depth_entry = app.entries.get("max_depth_per_borehole")
        max_depth = float(max_depth_entry.get() or "999") if max_depth_entry else 999.0
        vr = app.vdi4640_result

        if max_depth < 999 and vr.required_depth_final > max_depth:
            total_length = vr.required_depth_final * num_boreholes
            suggested_num = num_boreholes + 1
            suggested_depth = min(80.0, total_length / suggested_num)
            for test_bh in range(num_boreholes + 1, num_boreholes + 4):
                test_d = total_length / test_bh
                if test_d <= max_depth:
                    suggested_num = test_bh
                    suggested_depth = test_d
                    break
            messagebox.showwarning(
                "Hinweis - Maximale Sondenlänge überschritten",
                f"Die berechnete Sondenlänge beträgt "
                f"{vr.required_depth_final:.1f} m pro Bohrung "
                f"bei {num_boreholes} Bohrungen.\n\n"
                f"Dies überschreitet Ihr Maximum von "
                f"{max_depth:.0f} m pro Bohrung.\n\n"
                f"📊 AKTUELLE KONFIGURATION:\n"
                f"   {num_boreholes} Bohrungen à "
                f"{vr.required_depth_final:.1f} m\n"
                f"   Gesamtlänge: {total_length:.1f} m\n\n"
                f"💡 VORSCHLAG:\n"
                f"   {suggested_num} Bohrungen à "
                f"{suggested_depth:.1f} m\n"
                f"   Gesamtlänge: {total_length:.1f} m\n\n"
                f"Bitte passen Sie die Anzahl der Bohrungen "
                f"manuell an.")

        # Kompatibilitäts-Result
        from calculations.borehole import BoreholeResult
        app.result = BoreholeResult(
            required_depth=vr.required_depth_final,
            fluid_temperature_min=vr.t_wp_aus_heating_min,
            fluid_temperature_max=vr.t_wp_aus_cooling_max,
            borehole_resistance=r_borehole,
            effective_resistance=(r_borehole + vr.r_grundlast),
            heat_extraction_rate=(
                vr.q_nettogrundlast_heating / vr.required_depth_final
                if vr.required_depth_final > 0 else 0),
            monthly_temperatures=[vr.t_wp_aus_heating_min] * 12)

        app.status_var.set(
            f"✓ VDI 4640 Berechnung: {vr.required_depth_final:.1f}m "
            f"(ausgelegt für {vr.design_case.upper()})")

    def _run_iterative(self, params, pipe_config, num_boreholes):
        """Iterativer Berechnungspfad (Eskilson/Hellström)."""
        app = self.app
        
        # ─────────────────────────────────────────────────────────────
        # FELD-INTERFERENZ CHECK (Neu in V3.5)
        # ─────────────────────────────────────────────────────────────
        custom_gfunction = None
        if num_boreholes > 1:
            try:
                from calculations.borefield_gfunction import BorefieldCalculator
                bf_calc = BorefieldCalculator()
                
                if bf_calc.is_available():
                    app.status_var.set("🔄 Berechne Bohrfeld-Interferenz (pygfunction)...")
                    app.root.update()
                    
                    # Layout-Schätzung (Rechteck nährungsweise quadratisch)
                    import math
                    side = math.ceil(math.sqrt(num_boreholes))
                    n_x = side
                    n_y = math.ceil(num_boreholes / side)
                    
                    # Falls das Rechteck größer ist als nötig, korrigieren wir n_y
                    # (z.B. N=2 -> side=2 -> 2x1 -> passt)
                    # (z.B. N=3 -> side=2 -> 2x2=4 -> passt für 3, einer fehlt halt)
                    # pygfunction füllt Rechtecke. Für ungerade Felder ist das eine Näherung,
                    # aber besser als keine Interferenz.
                    # Besser: Wenn N != n_x * n_y, warnen oder akzeptieren.
                    # pygfunction rechnet für volles Rechteck.
                    # Bei N=3 rechnen wir für 4 und teilen Last durch 3? Nein.
                    # Wir rechnen g-Funktion für 4 Sonden. Das überschätzt die Interferenz leicht (konservativ).
                    
                    # Abstand (Versuche aus GUI zu lesen, Fallback 6m)
                    spacing = 6.0
                    if hasattr(app, 'borefield_tab') and hasattr(app.borefield_tab, 'distance_entry'):
                         try:
                             val = float(app.borefield_tab.distance_entry.get())
                             if val > 0: spacing = val
                         except:
                             pass
                    
                    # Referenztiefe für g-Funktion (Startwert)
                    calc_depth = params.get("initial_depth", 100.0)
                    
                    # Berechnung
                    g_res = bf_calc.calculate_gfunction(
                        layout="rectangle",
                        num_boreholes_x=n_x,
                        num_boreholes_y=n_y,
                        spacing_x=spacing,
                        spacing_y=spacing,
                        borehole_depth=calc_depth,
                        borehole_radius=params["borehole_diameter"] / 2,
                        soil_thermal_diffusivity=params["ground_thermal_cond"] / params["ground_heat_cap"],
                        simulation_years=int(params["simulation_years"]),
                        time_resolution="monthly"
                    )
                    
                    custom_gfunction = bf_calc.get_gfunction_interpolator(g_res)
                    logger.info(f"Bohrfeld-Interferenz berechnet für {n_x}x{n_y} Feld, Abstand {spacing}m.")
                    
            except Exception as e:
                logger.warning(f"Konnte Bohrfeld-Interferenz nicht berechnen: {e}")
                app.status_var.set("⚠️ Warnung: Berechne ohne Feld-Interferenz (pygfunction Fehler)")
        
        # ─────────────────────────────────────────────────────────────
        
        # Monatliche Faktoren aus Lastprofil-Tab (falls vorhanden)
        monthly_heating_factors = None
        monthly_cooling_factors = None
        if hasattr(app, 'load_profiles_tab') and app.load_profiles_tab:
            monthly_heating_factors = app.load_profiles_tab.get_monthly_heating_factors()
            monthly_cooling_factors = app.load_profiles_tab.get_monthly_cooling_factors()

        app.result = app.calculator.calculate_required_depth(
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
            fluid_flow_rate=params["fluid_flow_rate"] / 3600.0,
            annual_heating_demand=params["annual_heating"] / 1000,
            annual_cooling_demand=params["annual_cooling"] / 1000,
            peak_heating_load=params["peak_heating"],
            peak_cooling_load=params["peak_cooling"],
            heat_pump_cop=params["heat_pump_cop"],
            min_fluid_temperature=params["min_fluid_temp"],
            max_fluid_temperature=params["max_fluid_temp"],
            simulation_years=int(params["simulation_years"]),
            initial_depth=params["initial_depth"],
            n_boreholes=num_boreholes,
            custom_gfunction=custom_gfunction,
            monthly_heating_factors=monthly_heating_factors,
            monthly_cooling_factors=monthly_cooling_factors
        )

        app.vdi4640_result = None
        
        msg = f"✓ Berechnung erfolgreich! {app.result.required_depth:.1f}m pro Sonde"
        if num_boreholes > 1:
            msg += f" ({num_boreholes} Sonden)"
            if custom_gfunction:
                msg += " [mit Feld-Interferenz]"
            else:
                msg += " [OHNE Interferenz]"
        
        app.status_var.set(msg)

    # ──────────────── Hilfsmethoden ────────────────

    @staticmethod
    def get_pipe_length_factor(pipe_config: str) -> int:
        """Gibt Faktor für Gesamtlänge der Leitungen zurück."""
        c = pipe_config.lower()
        if "double" in c or "4-rohr" in c:
            return 4
        return 2

    @staticmethod
    def get_pipe_positions(pipe_config, params):
        """Gibt Rohrpositionen für Bohrlochwiderstand zurück."""
        shank = params["shank_spacing"]
        if pipe_config == "single-u":
            return [(-shank / 2, 0), (shank / 2, 0)]
        elif pipe_config == "double-u":
            o = shank / 2
            return [(-o, -o), (o, -o), (-o, o), (o, o)]
        return [(0, 0), (0, 0)]

    # ──────────────── Ergebnisanzeige ────────────────

    def display_results(self):
        """Zeigt Berechnungsergebnisse im Text-Widget an."""
        app = self.app
        if not app.result:
            return

        num_bh = int(app.borehole_entries["num_boreholes"].get())
        app.results_text.config(state=tk.NORMAL)
        app.results_text.delete("1.0", tk.END)

        text = "=" * 80 + "\n"
        text += "ERDWÄRMESONDEN-BERECHNUNGSERGEBNIS (Professional V3.2.1)\n"
        text += "=" * 80 + "\n\n"

        proj_name = app.project_entries["project_name"].get()
        if proj_name:
            text += f"📋 Projekt: {proj_name}\n"
            text += f"👤 Kunde: {app.project_entries['customer_name'].get()}\n\n"

        method = app.current_params.get('calculation_method', 'iterativ')
        if method == "vdi4640" and app.vdi4640_result:
            text += self._format_vdi4640_results(num_bh)
        else:
            text += self._format_iterative_results(num_bh)

        text += "=" * 80 + "\n"
        app.results_text.insert("1.0", text)
        app.results_text.config(state=tk.DISABLED)

    def _format_vdi4640_results(self, num_bh):
        """Formatiert VDI 4640 Ergebnisse."""
        app = self.app
        vr = app.vdi4640_result
        params = app.current_params
        pipe_config = app.pipe_config_var.get()
        plf = self.get_pipe_length_factor(pipe_config)

        t = "📐 BERECHNUNGSMETHODE: VDI 4640 (Koenigsdorff)\n"
        t += "=" * 80 + "\n\n"

        t += "🎯 AUSLEGUNGSFALL\n" + "-" * 80 + "\n"
        if vr.design_case == "heating":
            t += "✓ HEIZEN ist auslegungsrelevant\n"
            t += f"  Erforderliche Sondenlänge: {vr.required_depth_heating:.1f} m\n"
            t += f"  (Kühlen würde nur {vr.required_depth_cooling:.1f} m benötigen)\n"
        else:
            t += "✓ KÜHLEN ist auslegungsrelevant (dominante Kühllast!)\n"
            t += f"  Erforderliche Sondenlänge: {vr.required_depth_cooling:.1f} m\n"
            t += f"  (Heizen würde nur {vr.required_depth_heating:.1f} m benötigen)\n"

        t += f"\n  → Ausgelegte Sondenlänge: {vr.required_depth_final:.1f} m\n"
        t += f"  → Anzahl Bohrungen: {num_bh}\n"
        t += f"  → Gesamtlänge (Bohrungen): {vr.required_depth_final * num_bh:.1f} m\n"
        ppl = vr.required_depth_final * plf
        t += f"  → Gesamtlänge (Leitungen): {ppl * num_bh:.1f} m\n"
        t += (f"     ({plf} Leitungen pro Bohrung × "
              f"{vr.required_depth_final:.1f} m = {ppl:.1f} m pro Bohrung)\n\n")

        t += "🌡️  WÄRMEPUMPENAUSTRITTSTEMPERATUREN\n" + "-" * 80 + "\n"
        t += f"Heizen (minimale WP-Austrittstemperatur): {vr.t_wp_aus_heating_min:.2f} °C\n"
        t += "  Komponenten:\n"
        t += f"    T_ungestört:            {params['ground_temp']:.2f} °C\n"
        t += f"    - ΔT_Grundlast:        {vr.delta_t_grundlast_heating:.3f} K\n"
        t += f"    - ΔT_Periodisch:       {vr.delta_t_per_heating:.3f} K\n"
        t += f"    - ΔT_Peak:             {vr.delta_t_peak_heating:.3f} K\n"
        t += f"    - 0.5 · ΔT_Fluid:      {vr.delta_t_fluid_heating / 2:.2f} K\n\n"
        t += f"Kühlen (maximale WP-Austrittstemperatur): {vr.t_wp_aus_cooling_max:.2f} °C\n"
        t += "  Komponenten:\n"
        t += f"    T_ungestört:            {params['ground_temp']:.2f} °C\n"
        t += f"    + ΔT_Grundlast:        {vr.delta_t_grundlast_cooling:.3f} K\n"
        t += f"    + ΔT_Periodisch:       {vr.delta_t_per_cooling:.3f} K\n"
        t += f"    + ΔT_Peak:             {vr.delta_t_peak_cooling:.3f} K\n"
        t += f"    - 0.5 · ΔT_Fluid:      {vr.delta_t_fluid_cooling / 2:.2f} K\n\n"

        t += "♨️  THERMISCHE WIDERSTÄNDE\n" + "-" * 80 + "\n"
        t += f"R_Grundlast (10 Jahre):     {vr.r_grundlast:.6f} m·K/W  (g={vr.g_grundlast:.4f})\n"
        t += f"R_Periodisch (1 Monat):     {vr.r_per:.6f} m·K/W  (g={vr.g_per:.4f})\n"
        t += f"R_Peak (6 Stunden):         {vr.r_peak:.6f} m·K/W  (g={vr.g_peak:.4f})\n"
        t += f"R_Bohrloch:                 {vr.r_borehole:.6f} m·K/W\n\n"

        t += "⚡ LASTDATEN\n" + "-" * 80 + "\n"
        t += "HEIZEN:\n"
        t += f"  Jahresenergie:         {params['annual_heating']:.0f} kWh\n"
        t += f"  Q_Nettogrundlast:      {vr.q_nettogrundlast_heating / 1000:.3f} kW  (Jahresmittel)\n"
        t += f"  Q_Periodisch:          {vr.q_per_heating / 1000:.3f} kW  (kritischster Monat)\n"
        t += f"  Q_Peak:                {vr.q_peak_heating / 1000:.3f} kW  (Spitzenlast)\n\n"
        t += "KÜHLEN:\n"
        t += f"  Jahresenergie:         {params['annual_cooling']:.0f} kWh\n"
        t += f"  Q_Nettogrundlast:      {vr.q_nettogrundlast_cooling / 1000:.3f} kW  (Jahresmittel)\n"
        t += f"  Q_Periodisch:          {vr.q_per_cooling / 1000:.3f} kW  (kritischster Monat)\n"
        t += f"  Q_Peak:                {vr.q_peak_cooling / 1000:.3f} kW  (Spitzenlast)\n\n"
        return t

    def _format_iterative_results(self, num_bh):
        """Formatiert iterative Ergebnisse."""
        app = self.app
        r = app.result
        pipe_config = app.pipe_config_var.get()
        plf = self.get_pipe_length_factor(pipe_config)
        total_pipe = r.required_depth * num_bh * plf

        t = "⚙️  BERECHNUNGSMETHODE: Iterativ (Eskilson/Hellström)\n"
        t += "=" * 80 + "\n\n"
        t += "🎯 BOHRFELD\n" + "-" * 80 + "\n"
        t += f"Anzahl Bohrungen:      {num_bh}\n"
        t += f"Tiefe pro Bohrung:     {r.required_depth:.1f} m\n"
        t += f"Gesamtlänge (Bohrungen): {r.required_depth * num_bh:.1f} m\n"
        t += f"Gesamtlänge (Leitungen): {total_pipe:.1f} m\n"
        t += f"  ({plf} Leitungen pro Bohrung)\n\n"
        t += "🌡️  TEMPERATUREN\n" + "-" * 80 + "\n"
        t += f"Min. Fluidtemperatur:  {r.fluid_temperature_min:.2f} °C\n"
        t += f"Max. Fluidtemperatur:  {r.fluid_temperature_max:.2f} °C\n\n"
        t += "♨️  WIDERSTÄNDE\n" + "-" * 80 + "\n"
        t += f"R_Bohrloch:            {r.borehole_resistance:.6f} m·K/W\n"
        t += f"R_effektiv:            {r.effective_resistance:.6f} m·K/W\n\n"
        t += "⚡ ENTZUGSLEISTUNG\n" + "-" * 80 + "\n"
        t += f"Spezifisch:            {r.heat_extraction_rate:.2f} W/m\n\n"
        return t

    def _plot_results(self):
        """Aktualisiert alle Diagramme."""
        app = self.app
        if hasattr(app, 'diagram_figures'):
            app._update_all_diagrams()

    # ──────────────── Materialberechnung ────────────────

    def calculate_grout_materials(self):
        """Berechnet Verfüllmaterial-Mengen."""
        app = self.app
        try:
            depth = float(app.entries["initial_depth"].get())
            bh_diam = float(app.entries["borehole_diameter"].get()) / 1000.0
            pipe_diam = float(app.entries["pipe_outer_diameter"].get()) / 1000.0
            num_bh = int(app.borehole_entries["num_boreholes"].get())

            config = app.pipe_config_var.get()
            num_pipes = 4 if ("4-rohr" in config or "double" in config) else 2

            vol_per_bh = app.grout_db.calculate_volume(
                depth, bh_diam, pipe_diam, num_pipes)
            total_vol = vol_per_bh * num_bh

            material_name = app.grout_material_var.get()
            material = app.grout_db.get_material(material_name)
            amounts = app.grout_db.calculate_material_amount(
                total_vol, material)

            app.grout_calculation = {
                'material': material, 'amounts': amounts,
                'num_boreholes': num_bh, 'volume_per_bh': vol_per_bh}

            text = "=" * 60 + "\n"
            text += "VERFÜLLMATERIAL-BERECHNUNG\n"
            text += "=" * 60 + "\n\n"
            text += f"Material: {material.name}\n"
            text += f"  λ = {material.thermal_conductivity} W/m·K\n"
            text += f"  ρ = {material.density} kg/m³\n"
            text += f"  Preis: {material.price_per_kg} EUR/kg\n\n"
            text += f"Konfiguration:\n"
            text += f"  Anzahl Bohrungen: {num_bh}\n"
            text += f"  Tiefe pro Bohrung: {depth} m\n"
            text += f"  Bohrloch-Ø: {bh_diam * 1000:.0f} mm\n"
            text += f"  Rohre: {num_pipes} × Ø {pipe_diam * 1000:.0f} mm\n\n"
            text += f"Benötigte Mengen:\n"
            text += f"  Volumen pro Bohrung: {vol_per_bh:.3f} m³ ({vol_per_bh * 1000:.1f} Liter)\n"
            text += f"  Volumen gesamt: {total_vol:.3f} m³ ({total_vol * 1000:.1f} Liter)\n"
            text += f"  Masse gesamt: {amounts['mass_kg']:.1f} kg\n"
            text += f"  Säcke (25 kg): {amounts['bags_25kg']:.1f} Stück\n\n"
            text += f"Kosten:\n"
            text += f"  Gesamt: {amounts['total_cost_eur']:.2f} EUR\n"
            text += f"  Pro Meter: {amounts['cost_per_m']:.2f} EUR/m\n\n"
            text += "=" * 60 + "\n"

            app.grout_result_text.delete("1.0", tk.END)
            app.grout_result_text.insert("1.0", text)
            app.status_var.set(
                f"✓ Materialberechnung: {total_vol * 1000:.0f} Liter "
                f"({amounts['bags_25kg']:.0f} Säcke), "
                f"{amounts['total_cost_eur']:.2f} EUR")

        except Exception as e:
            messagebox.showerror(
                "Fehler", f"Fehler bei Materialberechnung: {str(e)}")

    # ──────────────── Hydraulik ────────────────

    def calculate_hydraulics(self):
        """Berechnet Hydraulik-Parameter."""
        app = self.app
        try:
            heat_power = float(app.heat_pump_entries["heat_pump_power"].get())

            # Frostschutzkonzentration
            antifreeze_conc = self._get_antifreeze_concentration()

            num_circuits = int(app.hydraulics_entries["num_circuits"].get())
            num_boreholes = int(app.borehole_entries["num_boreholes"].get())

            # Tiefe (bevorzugt VDI 4640 Ergebnis)
            if (hasattr(app, 'vdi4640_result') and app.vdi4640_result
                    and app.vdi4640_result.required_depth_final > 0):
                depth = app.vdi4640_result.required_depth_final
            else:
                depth = float(app.entries["initial_depth"].get())

            pipe_outer_d_m = float(app.entries["pipe_outer_diameter"].get()) / 1000.0
            pipe_thickness_m = float(app.entries["pipe_thickness"].get()) / 1000.0
            pipe_inner_d = pipe_outer_d_m - 2 * pipe_thickness_m

            cop = float(app.entries["heat_pump_cop"].get())
            extraction_power = heat_power * (cop - 1) / cop

            delta_t_fluid = float(
                app.entries.get("delta_t_fluid", ttk.Entry()).get() or "3.0")

            flow = app.hydraulics_calc.calculate_required_flow_rate(
                extraction_power, delta_t_fluid, antifreeze_conc)

            # Automatisch übernehmen
            calculated_flow_m3h = flow['volume_flow_m3_h']
            flow_entry = app.entries.get("fluid_flow_rate")
            if flow_entry:
                flow_entry.delete(0, tk.END)
                flow_entry.insert(0, f"{calculated_flow_m3h:.3f}")

            flow_warnings = self._check_flow_rate_warnings(
                heat_power, flow['volume_flow_m3_s'], num_boreholes,
                delta_t_fluid, antifreeze_conc, extraction_power)

            pipe_config = app.pipe_config_var.get()
            circuits_per_bh = (2 if ("4-rohr" in pipe_config.lower()
                               or "double" in pipe_config.lower()) else 1)

            system = app.hydraulics_calc.calculate_total_system_pressure_drop(
                depth, num_boreholes, num_circuits, pipe_inner_d,
                flow['volume_flow_m3_h'], antifreeze_conc, circuits_per_bh)

            pump = app.hydraulics_calc.calculate_pump_power(
                flow['volume_flow_m3_h'], system['total_pressure_drop_bar'])

            cold_power = heat_power * (cop - 1) / cop
            app.cold_power_label.config(
                text=f"{cold_power:.2f} kW", foreground="blue")

            app.hydraulics_result = {
                'flow': flow, 'system': system,
                'pump': pump, 'cold_power': cold_power}

            # Text aufbauen
            text = self._format_hydraulics_text(
                heat_power, cop, extraction_power, antifreeze_conc,
                num_circuits, num_boreholes, circuits_per_bh, depth,
                flow, system, pump, flow_warnings)

            app.hydraulics_result_text.delete("1.0", tk.END)
            app.hydraulics_result_text.insert("1.0", text)

            if hasattr(app, 'flow_optimizer_button'):
                app.flow_optimizer_button.config(state="normal")

            self.update_energy_analysis()
            self.update_pressure_analysis()
            self.update_pump_analysis()

            app.status_var.set(
                f"✓ Hydraulik: {flow['volume_flow_m3_h']:.2f} m³/h, "
                f"{system['total_pressure_drop_mbar']:.0f} mbar, "
                f"{pump['electric_power_w']:.0f} W")

        except Exception as e:
            messagebox.showerror(
                "Fehler", f"Fehler bei Hydraulik-Berechnung: {str(e)}")

    def _get_antifreeze_concentration(self):
        """Ermittelt Frostschutzkonzentration aus Fluid-DB oder Eingabe."""
        app = self.app
        if hasattr(app, 'fluid_var') and app.fluid_var.get():
            fluid = app.fluid_db.get_fluid(app.fluid_var.get())
            if fluid:
                return fluid.concentration_percent
        try:
            return float(app.hydraulics_entries.get(
                "antifreeze_concentration", ttk.Entry()).get() or "25")
        except (AttributeError, ValueError, KeyError):
            return 25.0

    def _format_hydraulics_text(self, heat_power, cop, extraction_power,
                                antifreeze_conc, num_circuits, num_boreholes,
                                circuits_per_bh, depth, flow, system, pump,
                                flow_warnings):
        """Formatiert Hydraulik-Ergebnistext."""
        t = "=" * 60 + "\n"
        t += "HYDRAULIK-BERECHNUNG\n"
        t += "=" * 60 + "\n\n"
        t += f"Wärmeleistung: {heat_power} kW\n"
        t += f"COP: {cop}\n"
        t += f"Entzugsleistung (Kälteleistung): {extraction_power:.2f} kW\n"
        t += f"Frostschutz: {antifreeze_conc} Vol%\n"
        t += f"Anzahl System-Kreise: {num_circuits}\n"
        t += f"Anzahl Bohrungen: {num_boreholes}\n"
        t += f"Kreise pro Bohrung: {circuits_per_bh}\n"
        t += f"Bohrtiefe: {depth:.1f} m\n"
        t += f"Bohrungen pro System-Kreis: {num_boreholes / num_circuits:.1f}\n"
        t += f"Rohrlänge pro System-Kreis: {system['pipe_length_per_circuit_m']:.1f} m\n\n"
        t += f"Volumenstrom:\n"
        t += f"  Gesamt: {flow['volume_flow_m3_h']:.3f} m³/h ({flow['volume_flow_l_min']:.1f} l/min)\n"
        t += f"  Pro Kreis: {system['volume_flow_per_circuit_m3h']:.3f} m³/h\n"
        t += f"  Geschwindigkeit: {system['velocity_m_s']:.2f} m/s\n"
        t += f"  Reynolds: {system['reynolds']:.0f}\n\n"
        t += f"Druckverlust:\n"
        t += f"  Bohrungen: {system['pressure_drop_borehole_bar']:.2f} bar\n"
        t += f"  Zusatzverluste: {system['additional_losses_bar']:.2f} bar\n"
        t += f"  GESAMT: {system['total_pressure_drop_bar']:.2f} bar ({system['total_pressure_drop_mbar']:.0f} mbar)\n\n"
        t += f"Pumpe:\n"
        t += f"  Hydraulische Leistung: {pump['hydraulic_power_w']:.0f} W\n"
        t += f"  Elektrische Leistung: {pump['electric_power_w']:.0f} W ({pump['electric_power_kw']:.2f} kW)\n\n"
        if flow_warnings:
            t += flow_warnings + "\n\n"
        t += "=" * 60 + "\n"
        return t

    def _check_flow_rate_warnings(self, heat_power_kw, flow_rate_m3s,
                                   num_boreholes, current_delta_t,
                                   antifreeze_conc, extraction_power):
        """Prüft Volumenstrom auf empfohlene Werte."""
        rec_min = 0.8
        rec_max = 1.5
        flow_ls = flow_rate_m3s * 1000
        flow_ls_per_kw = flow_ls / heat_power_kw if heat_power_kw > 0 else 0
        min_per_bh_m3h = 2.5
        flow_m3h = flow_rate_m3s * 3600
        flow_per_bh = flow_m3h / num_boreholes if num_boreholes > 0 else 0
        rec_min_m3h = rec_min * heat_power_kw * 3.6
        rec_max_m3h = rec_max * heat_power_kw * 3.6

        warnings = []
        app = self.app
        if flow_ls_per_kw < rec_min:
            props = app.hydraulics_calc._get_fluid_properties(antifreeze_conc)
            target_flow = (rec_min * heat_power_kw) / 1000
            opt_dt = ((extraction_power * 1000) /
                      (props['heat_capacity'] * props['density'] * target_flow))
            est_pump_w = 150
            if hasattr(app, 'hydraulics_result') and app.hydraulics_result:
                cur_pump_w = app.hydraulics_result.get(
                    'pump', {}).get('electric_power_w', 0)
                ratio = target_flow / flow_rate_m3s if flow_rate_m3s > 0 else 1
                est_pump_w = cur_pump_w * (ratio ** 2)
            warnings.append(
                f"⚠️ VOLUMENSTROM ZU NIEDRIG:\n"
                f"   Aktuell: {flow_m3h:.2f} m³/h ({flow_ls_per_kw:.2f} l/s/kW)\n"
                f"   Empfohlen: {rec_min_m3h:.1f} - {rec_max_m3h:.1f} m³/h\n"
                f"   \n"
                f"   💡 OPTIMIERUNGSVORSCHLAG:\n"
                f"   • ΔT von {current_delta_t:.1f}K auf ca. {opt_dt:.1f}K reduzieren\n"
                f"   • Volumenstrom steigt dann auf ca. {target_flow * 3600:.2f} m³/h\n"
                f"   • Pumpenleistung steigt auf ca. {est_pump_w:.0f} W\n"
                f"   \n"
                f"   ⚡ FOLGEN BEI ZU NIEDRIGEM VOLUMENSTROM:\n"
                f"   • Schlechterer Wärmeübergang\n"
                f"   • Höhere Vorlauftemperatur nötig\n"
                f"   • JAZ-Reduktion: 8-15%")
        elif flow_ls_per_kw > rec_max:
            warnings.append(
                f"⚠️ VOLUMENSTROM ZU HOCH:\n"
                f"   Aktuell: {flow_m3h:.2f} m³/h ({flow_ls_per_kw:.2f} l/s/kW)\n"
                f"   Empfohlen: {rec_min_m3h:.1f} - {rec_max_m3h:.1f} m³/h\n"
                f"   \n"
                f"   ⚡ FOLGEN:\n"
                f"   • Hoher Druckverlust\n"
                f"   • Hohe Pumpenleistung\n"
                f"   • Parasitäre Verluste: 3-8%")

        if flow_per_bh < min_per_bh_m3h:
            warnings.append(
                f"⚠️ VOLUMENSTROM PRO SONDE ZU NIEDRIG:\n"
                f"   Aktuell: {flow_per_bh:.2f} m³/h pro Sonde\n"
                f"   Minimum: {min_per_bh_m3h} m³/h pro Sonde\n"
                f"   \n"
                f"   ⚡ PROBLEM: Strömung nicht turbulent (Re < 2300)\n"
                f"   → Schlechter Wärmeübergang")

        return warnings[0] if warnings else ""

    # ──────────────── Analyse-Tabs ────────────────

    def update_energy_analysis(self):
        """Aktualisiert Energieprognose im Analyse-Tab."""
        app = self.app
        if not getattr(app, 'hydraulics_result', None):
            return
        if not hasattr(app, 'energy_analysis_text'):
            return
        try:
            pump_power = app.hydraulics_result['pump']['electric_power_w']
            hours, price = 1800, 0.30
            energy = app.hydraulics_calc.calculate_pump_energy_consumption(
                pump_power, hours, price)

            t = "═══ ENERGIEVERBRAUCH-PROGNOSE ═══\n\n"
            t += f"Pumpenleistung: {pump_power:.0f} W\n"
            t += f"Betriebsstunden/Jahr: {hours} h\n"
            t += f"Strompreis: {price:.2f} EUR/kWh\n\n"
            t += "KONSTANTE PUMPE:\n"
            t += f"  Verbrauch: {energy['annual_kwh']:.1f} kWh/Jahr\n"
            t += f"  Kosten: {energy['annual_cost_eur']:.2f} EUR/Jahr\n\n"
            reg_kwh = energy['annual_kwh'] * 0.7
            reg_cost = energy['annual_cost_eur'] * 0.7
            t += "GEREGELTE PUMPE (30% Einsparung):\n"
            t += f"  Verbrauch: {reg_kwh:.1f} kWh/Jahr\n"
            t += f"  Kosten: {reg_cost:.2f} EUR/Jahr\n\n"
            t += "EINSPARUNG:\n"
            t += f"  {energy['annual_kwh'] - reg_kwh:.1f} kWh/Jahr\n"
            t += f"  {energy['annual_cost_eur'] - reg_cost:.2f} EUR/Jahr\n\n"
            t += "─────────────────────────────\n\n"
            t += "💡 Empfehlung: Geregelte Hocheffizienz-\n"
            t += "   Pumpe (Klasse A) verwenden!\n"

            app.energy_analysis_text.delete("1.0", tk.END)
            app.energy_analysis_text.insert("1.0", t)
        except Exception as e:
            if hasattr(app, 'energy_analysis_text'):
                app.energy_analysis_text.delete("1.0", tk.END)
                app.energy_analysis_text.insert("1.0", f"Fehler: {str(e)}")

    def update_pressure_analysis(self):
        """Aktualisiert Druckverlust-Analyse im Analyse-Tab."""
        app = self.app
        if not getattr(app, 'hydraulics_result', None):
            return
        if not hasattr(app, 'pressure_analysis_text'):
            return
        try:
            system = app.hydraulics_result.get('system', {})
            flow = app.hydraulics_result.get('flow', {})
            reynolds = system.get('reynolds', 0)

            t = "═══ DRUCKVERLUST-ANALYSE ═══\n\n"
            t += f"Volumenstrom: {flow.get('volume_flow_m3_h', 0):.2f} m³/h\n"
            t += f"Geschwindigkeit: {system.get('velocity', 0):.2f} m/s\n"
            t += f"Reynolds: {reynolds:.0f}\n\n"
            if reynolds < 2300:
                t += "⚠️  LAMINAR (Re < 2300)\n    Risiko schlechter Wärmeübergang!\n"
            elif reynolds < 2500:
                t += "⚡ ÜBERGANGSBEREICH (Re 2300-2500)\n   Grenzbereich, knapp turbulent\n"
            else:
                t += "✅ TURBULENT (Re > 2500)\n   Guter Wärmeübergang\n"
            t += "\n─────────────────────────────\n\n"
            t += "DRUCKVERLUSTE:\n"
            t += f"  Total: {system.get('total_pressure_drop_bar', 0):.3f} bar\n"
            t += f"        ({system.get('total_pressure_drop_mbar', 0):.0f} mbar)\n"
            t += f"  Förderhöhe: {system.get('total_pressure_drop_bar', 0) * 10.2:.1f} m\n\n"
            t += f"Rohrlänge/Kreis: {system.get('pipe_length_per_circuit_m', 0):.1f} m\n"
            t += f"Reibungsverlust: {system.get('friction_factor', 0):.4f}\n\n"
            t += "─────────────────────────────\n\n"
            t += "💡 Tipp: Für niedrigere Druckverluste\n"
            t += "   größeren Rohrdurchmesser wählen!\n"

            app.pressure_analysis_text.delete("1.0", tk.END)
            app.pressure_analysis_text.insert("1.0", t)
        except Exception as e:
            app.pressure_analysis_text.delete("1.0", tk.END)
            app.pressure_analysis_text.insert("1.0", f"Fehler: {str(e)}")

    def update_pump_analysis(self):
        """Aktualisiert Pumpen-Empfehlungen im Analyse-Tab."""
        app = self.app
        if not getattr(app, 'hydraulics_result', None):
            return
        if not hasattr(app, 'pump_analysis_text'):
            return
        try:
            from data.pump_db import PumpDatabase

            flow_m3h = app.hydraulics_result['flow']['volume_flow_m3_h']
            total_dp = app.hydraulics_result['system']['total_pressure_drop_bar']
            head_m = total_dp * 10.2
            power_kw = float(
                app.heat_pump_entries["heat_pump_power"].get() or "11")
            pump_db = PumpDatabase()

            t = "═══ PUMPEN-EMPFEHLUNGEN ═══\n\n"
            t += f"Volumenstrom: {flow_m3h:.2f} m³/h\n"
            t += f"Förderhöhe: {head_m:.1f} m\n"
            t += f"Leistung WP: {power_kw:.0f} kW\n"
            t += f"Pumpen in DB: {len(pump_db.pumps)}\n\n"
            t += "─────────────────────────────\n\n"

            suitable = pump_db.find_suitable_pumps(
                flow_m3h=flow_m3h, head_m=head_m,
                power_kw=power_kw, max_results=5)

            if suitable:
                medals = ["🥇 ", "🥈 ", "🥉 "]
                for i, (score, pump) in enumerate(suitable, 1):
                    prefix = medals[i - 1] if i <= 3 else f"#{i} "
                    t += f"{prefix}{pump.get_full_name()}\n"
                    t += f"   Score: {score:.0f}/100\n"
                    t += f"   Typ: {'Geregelt' if pump.pump_type == 'regulated' else 'Konstant'}\n"
                    t += f"   Max: {pump.specs.max_flow_m3h} m³/h, {pump.specs.max_head_m} m\n"
                    t += f"   Leistung: {pump.specs.power_avg_w} W\n"
                    t += f"   Effizienz: {pump.efficiency_class}\n"
                    t += f"   Preis: {pump.price_eur:.0f} EUR\n\n"
            else:
                t += "⚠️ Keine passenden Pumpen gefunden.\n\n"
                t += "Mögliche Gründe:\n"
                t += f"• Volumenstrom zu hoch (> {flow_m3h / 1.1:.1f} m³/h nötig)\n"
                t += f"• Förderhöhe zu hoch (> {head_m / 1.1:.1f} m nötig)\n"
                t += "• Leistungsbereich passt nicht\n\n"
                t += "Prüfen Sie:\n"
                t += "- Anzahl Bohrungen erhöhen\n"
                t += "- ΔT erhöhen (weniger Volumenstrom)\n"
                t += "- Rohrdurchmesser vergrößern\n"

            t += "\n─────────────────────────────\n\n"
            t += "💡 Empfehlung: Geregelte Hocheffizienz-\n"
            t += "   Pumpe für beste Energieeffizienz!\n"

            app.pump_analysis_text.delete("1.0", tk.END)
            app.pump_analysis_text.insert("1.0", t)
        except Exception as e:
            app.pump_analysis_text.delete("1.0", tk.END)
            app.pump_analysis_text.insert(
                "1.0",
                f"Fehler: {str(e)}\n\n"
                f"Pumpen-Datenbank konnte nicht\ngeladen werden.")

    # ──────────────── PDF/Text-Export ────────────────

    def export_pdf(self):
        """Exportiert PDF mit allen Daten."""
        app = self.app
        if not app.result:
            messagebox.showwarning(
                "Keine Daten", "Bitte zuerst Berechnung durchführen.")
            return

        proj_name = app.project_entries["project_name"].get() or "Projekt"
        filename = filedialog.asksaveasfilename(
            title="PDF-Bericht speichern", defaultextension=".pdf",
            initialfile=f"Bericht_{proj_name.replace(' ', '_')}_V3.pdf",
            filetypes=[("PDF", "*.pdf")])

        if not filename:
            return

        try:
            app.status_var.set("📄 Erstelle PDF-Bericht...")
            app.root.update()

            project_info = {k: e.get()
                            for k, e in app.project_entries.items()}
            borehole_config = {k: float(e.get())
                               for k, e in app.borehole_entries.items()}

            fluid_info = self._collect_fluid_info()
            diagram_data = self._collect_diagram_data()

            app.pdf_generator.generate_report(
                filename, app.result, app.current_params,
                project_info, borehole_config,
                grout_calculation=getattr(app, 'grout_calculation', None),
                hydraulics_result=getattr(app, 'hydraulics_result', None),
                borefield_result=getattr(app, 'borefield_result', None),
                vdi4640_result=getattr(app, 'vdi4640_result', None),
                fluid_info=fluid_info,
                diagram_data=diagram_data)

            app.status_var.set(
                f"✓ PDF erstellt: {os.path.basename(filename)}")
            messagebox.showinfo("Erfolg", "PDF-Bericht wurde erstellt!")

        except Exception as e:
            messagebox.showerror("Fehler", f"PDF-Fehler: {str(e)}")
            app.status_var.set("❌ PDF-Export fehlgeschlagen")

    def export_results_text(self):
        """Exportiert Ergebnis-Text."""
        app = self.app
        if not app.result:
            messagebox.showwarning("Keine Daten",
                                   "Keine Ergebnisse vorhanden.")
            return
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt", filetypes=[("Text", "*.txt")])
        if filename:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(app.results_text.get("1.0", tk.END))
            app.status_var.set("✓ Text exportiert")

    def _collect_fluid_info(self):
        """Sammelt Fluid-Info für PDF."""
        app = self.app
        if not (hasattr(app, 'fluid_var') and app.fluid_var.get()):
            return None
        fluid = app.fluid_db.get_fluid(app.fluid_var.get())
        if not fluid:
            return None
        try:
            temp = float(app.entries.get(
                "fluid_temperature", ttk.Entry()).get() or "5.0")
        except (ValueError, AttributeError):
            temp = 5.0
        props = fluid.get_properties_at_temp(temp)
        return {
            'name': fluid.name, 'type': fluid.type,
            'concentration_percent': fluid.concentration_percent,
            'min_temp': fluid.min_temp, 'max_temp': fluid.max_temp,
            **props}

    def _collect_diagram_data(self):
        """Sammelt Diagramm-Daten für PDF."""
        app = self.app
        if not hasattr(app, 'diagram_figures'):
            return {}
        app._update_all_diagrams()
        mapping = {
            'Monatliche Temperaturen': 'monthly_temperatures',
            'Bohrloch-Schema': 'borehole_schema',
            'Pumpen-Kennlinien': 'pump_characteristics',
            'Reynolds-Kurve': 'reynolds_curve',
            'Druckverlust-Komponenten': 'pressure_components',
            'Volumenstrom vs. Druckverlust': 'flow_vs_pressure',
            'Pumpenleistung über Betriebszeit': 'pump_power_time',
            'Temperaturspreizung Sole': 'temperature_spread',
            'COP vs. Sole-Eintrittstemperatur': 'cop_inlet_temp',
            'COP vs. Vorlauftemperatur': 'cop_flow_temp',
            'JAZ-Abschätzung': 'jaz_estimation',
            'Energieverbrauch-Vergleich': 'energy_consumption',
        }
        data = {}
        for di in app.diagram_figures:
            title = di['title']
            if title in mapping:
                try:
                    ax = di['figure'].gca()
                    if ax.get_lines() or ax.patches or len(ax.texts) > 1:
                        data[mapping[title]] = di['figure']
                except Exception:
                    pass
        return data
