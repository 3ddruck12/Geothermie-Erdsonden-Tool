"""GET Dateiformat Handler mit Versionierung und Abwärtskompatibilität.

Das .get Format ist das native Austauschformat des Geothermie Erdsonden-Tools.
Es basiert auf JSON und unterstützt Versionierung sowie Migration älterer Dateien.
"""

import json
from typing import Dict, Any, Optional
from datetime import datetime
import os

from utils.version import APP_VERSION

# Versionskonstanten
CURRENT_FORMAT_VERSION = "3.4"
SUPPORTED_VERSIONS = ["3.0", "3.1", "3.2", "3.3", "3.4"]


class GETFileHandler:
    """Handler für .get Dateien mit Abwärtskompatibilität."""
    
    def __init__(self):
        """Initialisiert den Handler."""
        self.format_version = CURRENT_FORMAT_VERSION
    
    def export_to_get(
        self,
        filepath: str,
        metadata: Dict[str, Any],
        ground_props: Dict[str, Any],
        borehole_config: Dict[str, Any],
        pipe_props: Dict[str, Any],
        grout_material: Dict[str, Any],
        fluid_props: Dict[str, Any],
        loads: Dict[str, Any],
        temp_limits: Dict[str, Any],
        simulation: Dict[str, Any],
        climate_data: Optional[Dict[str, Any]] = None,
        borefield_data: Optional[Dict[str, Any]] = None,
        results: Optional[Dict[str, Any]] = None,
        vdi4640_result: Optional[Dict[str, Any]] = None,
        hydraulics_result: Optional[Dict[str, Any]] = None,
        fluid_database_info: Optional[Dict[str, Any]] = None,
        grout_calculation: Optional[Dict[str, Any]] = None,
        custom_pipes_txt: Optional[str] = None,
        diagrams: Optional[Dict[str, Any]] = None,
        bohranzeige_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Exportiert alle Daten in eine .get Datei.
        
        Args:
            filepath: Pfad zur .get Datei
            metadata: Projektmetadaten (project_name, customer_name, address, postal_code,
                      city, latitude, longitude, date, notes)
            ground_props: Bodeneigenschaften (thermal_conductivity, heat_capacity, etc.)
            borehole_config: Bohrlochkonfiguration (diameter_mm, depth_m, etc.)
            pipe_props: Rohreigenschaften (material, outer_diameter_mm, etc.)
            grout_material: Verfüllmaterial (name, thermal_conductivity, etc.)
            fluid_props: Wärmeträgerflüssigkeit (type, thermal_conductivity, etc.)
            loads: Lastdaten (annual_heating_kwh, peak_heating_kw, etc.)
            temp_limits: Temperaturgrenzen (min_fluid_temp, max_fluid_temp)
            simulation: Simulationseinstellungen (years, initial_depth)
            climate_data: Klimadaten (optional, von PVGIS)
            borefield_data: Bohrfeld-Daten für V3.2 (optional, pygfunction)
            results: Berechnungsergebnisse (optional)
            vdi4640_result: VDI 4640 Berechnungsergebnis (optional)
            hydraulics_result: Hydraulik-Berechnungsergebnis (optional)
            fluid_database_info: Fluid-Datenbank-Informationen (optional, name, temperature)
            grout_calculation: Verfüllmaterial-Berechnung (optional)
            custom_pipes_txt: Inhalt einer benutzerdefinierten pipe.txt (optional)
            diagrams: Diagramm-Konfigurationen (optional, Version 3.3)
        
        Returns:
            True bei Erfolg, False bei Fehler
        """
        try:
            # Stelle sicher, dass Dateiendung .get ist
            if not filepath.endswith('.get'):
                filepath += '.get'
            
            # Erstelle Verzeichnis falls nötig
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            # Baue Datenstruktur
            data = {
                "file_format": "GET",
                "format_version": CURRENT_FORMAT_VERSION,
                "created_with": f"Geothermie Erdsonden-Tool v{APP_VERSION}",
                "created_date": datetime.now().isoformat() + "Z",
                "encoding": "UTF-8",
                "metadata": metadata,
                "ground_properties": ground_props,
                "borehole_config": borehole_config,
                "pipe_properties": pipe_props,
                "grout_material": grout_material,
                "heat_carrier_fluid": fluid_props,
                "loads": loads,
                "temperature_limits": temp_limits,
                "simulation_settings": simulation
            }
            
            # Optionale Daten hinzufügen
            if climate_data:
                data["climate_data"] = climate_data
            
            if borefield_data:
                data["borefield_v32"] = borefield_data
            
            if results:
                data["results"] = results
            
            # NEU in V3.2.1: VDI 4640 Ergebnisse, Hydraulik, Fluid-Datenbank
            if vdi4640_result:
                data["vdi4640_result"] = vdi4640_result
            
            if hydraulics_result:
                data["hydraulics_result"] = hydraulics_result
            
            if fluid_database_info:
                data["fluid_database_info"] = fluid_database_info
            
            if grout_calculation:
                data["grout_calculation"] = grout_calculation
            
            if custom_pipes_txt:
                data["custom_pipes_txt"] = custom_pipes_txt
            
            # NEU in V3.3: Diagramm-Konfigurationen
            if diagrams:
                data["diagrams"] = diagrams
            
            # NEU in V3.3.6: Bohranzeige-Daten
            if bohranzeige_data:
                data["bohranzeige_data"] = bohranzeige_data

            # Sicherstellen, dass V3.4-Pflichtfelder in metadata vorhanden sind
            meta = data.get("metadata", {})
            for field in ("project_name", "customer_name", "address",
                          "postal_code", "city", "date"):
                meta.setdefault(field, "")
            meta.setdefault("latitude", None)
            meta.setdefault("longitude", None)
            data["metadata"] = meta
            
            # Schreibe JSON mit Formatierung
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ .get Datei gespeichert: {filepath}")
            return True
            
        except Exception as e:
            print(f"❌ Export-Fehler: {e}")
            return False
    
    def import_from_get(self, filepath: str) -> Optional[Dict[str, Any]]:
        """
        Importiert Daten aus .get Datei mit Versionsprüfung.
        
        Args:
            filepath: Pfad zur .get Datei
        
        Returns:
            Dict mit allen Daten oder None bei Fehler
        """
        try:
            # Prüfe ob Datei existiert
            if not os.path.exists(filepath):
                raise FileNotFoundError(f"Datei nicht gefunden: {filepath}")
            
            # Lese JSON
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Validiere Format
            if data.get("file_format") != "GET":
                raise ValueError("Ungültiges Dateiformat. Erwartet: GET")
            
            # Versionsprüfung
            file_version = data.get("format_version", "3.0")
            
            if file_version not in SUPPORTED_VERSIONS:
                raise ValueError(
                    f"Nicht unterstützte Version: {file_version}. "
                    f"Unterstützte Versionen: {', '.join(SUPPORTED_VERSIONS)}"
                )
            
            # Migriere ältere Versionen
            if file_version != CURRENT_FORMAT_VERSION:
                print(f"🔄 Migriere {file_version} → {CURRENT_FORMAT_VERSION}")
                data = self._migrate_version(data, file_version)
            
            print(f"✅ .get Datei geladen: {filepath}")
            return data
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON-Fehler: {e}")
            return None
        except Exception as e:
            print(f"❌ Import-Fehler: {e}")
            return None
    
    def _migrate_version(
        self,
        data: Dict[str, Any],
        from_version: str
    ) -> Dict[str, Any]:
        """
        Migriert Daten von älteren Versionen auf aktuelle Version.
        
        Args:
            data: Originaldaten
            from_version: Quellversion
        
        Returns:
            Migrierte Daten
        """
        # Migration 3.0 → 3.1
        if from_version == "3.0":
            # Füge fehlende Felder hinzu
            if "climate_data" not in data:
                data["climate_data"] = None
            
            # Füge erweiterte Metadaten hinzu
            if "metadata" not in data:
                data["metadata"] = {
                    "project_name": "",
                    "location": "",
                    "designer": "",
                    "date": "",
                    "notes": ""
                }
            
            # Update Version
            data["format_version"] = "3.1"
            from_version = "3.1"
            print("  ✓ Migriert auf 3.1")
        
            # Migration 3.1 → 3.2
        if from_version == "3.1":
            # Füge Bohrfeld-Daten hinzu (deaktiviert per Default)
            if "borefield_v32" not in data:
                data["borefield_v32"] = {
                    "enabled": False,
                    "layout": "rectangle",
                    "num_boreholes_x": 1,
                    "num_boreholes_y": 1,
                    "spacing_x_m": 6.0,
                    "spacing_y_m": 6.0,
                    "borehole_diameter_mm": 152.0,
                    "soil_thermal_diffusivity": 1.0e-6,
                    "simulation_years": 25
                }
            
            # Füge neue Felder für V3.2 hinzu
            if "vdi4640_result" not in data:
                data["vdi4640_result"] = None
            if "hydraulics_result" not in data:
                data["hydraulics_result"] = None
            if "fluid_database_info" not in data:
                data["fluid_database_info"] = None
            if "grout_calculation" not in data:
                data["grout_calculation"] = None
            
            # Update Version
            data["format_version"] = "3.2"
            print("  ✓ Migriert auf 3.2")
            from_version = "3.2"
        
        # Migration 3.2 → 3.3
        if from_version == "3.2":
            if "diagrams" not in data:
                data["diagrams"] = {
                    "pump_characteristics": {"enabled": True},
                    "reynolds_curve": {"enabled": True, "glycol_concentrations": [0, 25, 30, 40]},
                    "pressure_components": {"enabled": True, "chart_type": "pie"},
                    "flow_vs_pressure": {"enabled": True},
                    "pump_power_time": {"enabled": True},
                    "temperature_spread": {"enabled": True},
                    "cop_inlet_temp": {"enabled": True},
                    "cop_flow_temp": {"enabled": True},
                    "jaz_estimation": {"enabled": True},
                    "energy_consumption": {"enabled": True, "show_10_year": True}
                }
            data["format_version"] = "3.3"
            from_version = "3.3"
            print("  ✓ Migriert auf 3.3")

        # Migration 3.3 → 3.4
        if from_version == "3.3":
            meta = data.get("metadata", {})
            # Altes "notes"-Feld → "address" (Straße)
            if "address" not in meta:
                meta["address"] = meta.pop("notes", "")
            else:
                meta.pop("notes", None)
            # Altes "designer"-Feld → "customer_name"
            if "customer_name" not in meta:
                meta["customer_name"] = meta.pop("designer", "")
            else:
                meta.pop("designer", None)
            # Altes "location"-Feld (z.B. "Berlin 10115") → city + postal_code trennen
            if "city" not in meta or "postal_code" not in meta:
                location = meta.pop("location", "") or ""
                parts = location.strip().rsplit(" ", 1)
                if len(parts) == 2 and parts[1].isdigit():
                    meta.setdefault("city", parts[0])
                    meta.setdefault("postal_code", parts[1])
                else:
                    meta.setdefault("city", location)
                    meta.setdefault("postal_code", "")
            else:
                meta.pop("location", None)
            # Koordinaten neu
            meta.setdefault("latitude", None)
            meta.setdefault("longitude", None)
            meta.setdefault("date", "")
            data["metadata"] = meta
            data["format_version"] = "3.4"
            from_version = "3.4"
            print("  ✓ Migriert auf 3.4")

        return data
    
    def validate_get_file(self, filepath: str) -> tuple[bool, str]:
        """
        Validiert eine .get Datei.
        
        Args:
            filepath: Pfad zur Datei
        
        Returns:
            (is_valid, message) - True/False und Beschreibung
        """
        try:
            data = self.import_from_get(filepath)
            
            if data is None:
                return False, "Datei konnte nicht gelesen werden"
            
            # Prüfe Pflichtfelder
            required_keys = [
                "file_format", "format_version", "metadata",
                "ground_properties", "borehole_config", "loads"
            ]
            
            missing_keys = []
            for key in required_keys:
                if key not in data:
                    missing_keys.append(key)
            
            if missing_keys:
                return False, f"Pflichtfelder fehlen: {', '.join(missing_keys)}"
            
            # Prüfe numerische Werte
            ground = data.get("ground_properties", {})
            if ground.get("thermal_conductivity", 0) <= 0:
                return False, "Ungültige Bodenwärmeleitfähigkeit"
            
            return True, f"✅ Gültige GET-Datei (Version {data['format_version']})"
            
        except Exception as e:
            return False, f"Validierungsfehler: {e}"
    
    def get_file_info(self, filepath: str) -> Optional[Dict[str, Any]]:
        """
        Gibt Informationen über eine .get Datei zurück ohne kompletten Import.
        
        Args:
            filepath: Pfad zur Datei
        
        Returns:
            Dict mit Datei-Informationen oder None
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            meta = data.get("metadata", {})
            city = meta.get("city") or ""
            postal = meta.get("postal_code") or ""
            location = (f"{city} {postal}".strip()
                        or meta.get("location", ""))
            return {
                "format": data.get("file_format", "unbekannt"),
                "version": data.get("format_version", "unbekannt"),
                "created_with": data.get("created_with", "unbekannt"),
                "created_date": data.get("created_date", "unbekannt"),
                "project_name": meta.get("project_name", ""),
                "location": location,
                "customer_name": (meta.get("customer_name")
                                  or meta.get("designer", "")),
                "latitude": meta.get("latitude"),
                "longitude": meta.get("longitude"),
                "has_climate_data": ("climate_data" in data
                                     and data["climate_data"] is not None),
                "has_borefield": ("borefield_v32" in data
                                  and data.get("borefield_v32", {}).get(
                                      "enabled", False)),
                "has_results": "results" in data and data["results"] is not None,
            }
        except Exception as e:
            print(f"Fehler beim Lesen der Datei-Info: {e}")
            return None




