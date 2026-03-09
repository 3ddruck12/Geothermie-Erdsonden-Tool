"""Interaktives OSM-Karten-Widget für tkinter.

Nutzt tkintermapview für eine eingebettete OpenStreetMap-Karte.
Wird sowohl im Eingabe-Tab (Standort-Visualisierung) als auch
im Bohranzeige-Tab (Lageplan-Vorschau) verwendet.
"""

import sys
import os
import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable, Tuple
import logging

logger = logging.getLogger(__name__)

FROZEN = getattr(sys, "frozen", False)

# #region agent log
def _dbg(m, d):
    """Debug-Log in /tmp und in Session-Logdatei (für frozen builds)."""
    try:
        import json, time
        entry = json.dumps({"sessionId": "435298", "location": "map_widget",
                            "message": m, "data": d, "hypothesisId": "PIL",
                            "timestamp": int(time.time() * 1000)}, ensure_ascii=False)
        # Session-Log (lokale Entwicklung)
        session_log = "/home/jens/Dokumente/Software Projekte/Geothermietool/.cursor/debug-435298.log"
        try:
            with open(session_log, "a", encoding="utf-8") as f:
                f.write(entry + "\n")
        except Exception:
            pass
        # /tmp-Log (frozen AppImage/DEB)
        if FROZEN:
            with open("/tmp/get_map_debug.log", "a", encoding="utf-8") as f:
                f.write(entry + "\n")
    except Exception:
        pass
# #endregion

# tkintermapview laden
MAPVIEW_ERROR = None
try:
    import tkintermapview
    HAS_MAPVIEW = True
except Exception as e:
    HAS_MAPVIEW = False
    MAPVIEW_ERROR = f"{type(e).__name__}: {e}"
    logger.warning(f"tkintermapview nicht verfügbar – {MAPVIEW_ERROR}")

# #region agent log
_dbg("module load", {
    "HAS_MAPVIEW": HAS_MAPVIEW,
    "FROZEN": FROZEN,
    "MAPVIEW_ERR": MAPVIEW_ERROR,
    "python": sys.version,
})
# #endregion


class OSMMapWidget:
    """Interaktives OSM-Karten-Widget – ausschließlich tkintermapview.

    Kein Fallback auf statische Karte. Wenn tkintermapview nicht
    verfügbar ist, wird eine Fehlertext-Anzeige eingeblendet.
    """

    def __init__(
        self,
        parent: tk.Widget,
        width: int = 500,
        height: int = 350,
        default_lat: float = 51.1657,
        default_lon: float = 10.4515,
        default_zoom: int = 6,
        on_position_change: Optional[Callable[[float, float], None]] = None,
    ):
        self.parent = parent
        self.width = width
        self.height = height
        self.on_position_change = on_position_change

        self._lat = default_lat
        self._lon = default_lon
        self._zoom = default_zoom
        self._marker = None
        self._map_widget = None

        # Container-Frame
        self.frame = ttk.LabelFrame(parent, text="🗺️ Standort-Karte (OpenStreetMap)")
        self.frame.pack(fill="x", padx=10, pady=5)

        # Info-Leiste oben
        info_frame = ttk.Frame(self.frame)
        info_frame.pack(fill="x", padx=5, pady=(5, 2))

        self.coord_label = ttk.Label(
            info_frame,
            text=f"Breite: {default_lat:.4f}°  |  Länge: {default_lon:.4f}°",
            foreground="#1f4788",
            font=("Arial", 9, "bold"),
        )
        self.coord_label.pack(side="left")

        self.status_label = ttk.Label(
            info_frame, text="", foreground="gray", font=("Arial", 8, "italic")
        )
        self.status_label.pack(side="right")

        # Karte bauen: nur tkintermapview
        if HAS_MAPVIEW:
            self._build_interactive_map()
        else:
            self._build_error_label()

    # ─── Karten-Builder ─────────────────────────────────────

    def _build_interactive_map(self):
        """Baut die interaktive tkintermapview-Karte."""
        # #region agent log
        _dbg("_build_interactive_map START", {})
        # #endregion
        try:
            self._map_widget = tkintermapview.TkinterMapView(
                self.frame,
                width=self.width,
                height=self.height,
                corner_radius=0,
            )
            self._map_widget.pack(fill="both", expand=True, padx=5, pady=2)

            self._map_widget.set_position(self._lat, self._lon)
            self._map_widget.set_zoom(self._zoom)

            self._map_widget.add_right_click_menu_command(
                label="📍 Standort hier setzen",
                command=self._on_map_right_click,
                pass_coords=True,
            )

            self.status_label.configure(text="Rechtsklick → Standort setzen")
            logger.info("Interaktive OSM-Karte initialisiert")
            # #region agent log
            _dbg("_build_interactive_map OK", {})
            # #endregion

        except Exception as e:
            # #region agent log
            _dbg("_build_interactive_map FAIL", {"err": str(e), "type": type(e).__name__})
            # #endregion
            logger.error(f"Fehler bei interaktiver Karte: {e}")
            # Widget ggf. wieder entfernen, dann Fehler anzeigen
            if self._map_widget:
                try:
                    self._map_widget.destroy()
                except Exception:
                    pass
                self._map_widget = None
            self._build_error_label(str(e))

    def _build_error_label(self, detail: str = ""):
        """Zeigt eine Fehlertext-Anzeige wenn tkintermapview nicht verfügbar."""
        err = MAPVIEW_ERROR or detail or "Unbekannter Fehler"
        lbl = ttk.Label(
            self.frame,
            text=f"🗺️ Karte nicht verfügbar\n\n{err}\n\nBitte tkintermapview installieren:\npip install tkintermapview",
            foreground="gray",
            font=("Arial", 10),
            justify="center",
            wraplength=450,
        )
        lbl.pack(fill="both", expand=True, padx=20, pady=30)
        self.status_label.configure(text="Karte nicht verfügbar")

    # ─── Öffentliche Methoden ────────────────────────────────

    def set_position(self, latitude: float, longitude: float, zoom: Optional[int] = None):
        """Setzt die Kartenposition und platziert einen Marker."""
        if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
            logger.warning(f"Ungültige Koordinaten ignoriert: {latitude}, {longitude}")
            return

        self._lat = latitude
        self._lon = longitude
        if zoom is not None:
            self._zoom = zoom

        self.coord_label.configure(
            text=f"Breite: {latitude:.5f}°  |  Länge: {longitude:.5f}°"
        )

        if self._map_widget:
            if self._marker:
                self._marker.delete()
            self._map_widget.set_position(latitude, longitude)
            if zoom is not None:
                self._map_widget.set_zoom(zoom)
            self._marker = self._map_widget.set_marker(
                latitude, longitude,
                text=f"Bohrstandort\n{latitude:.4f}°, {longitude:.4f}°",
            )

        if self.on_position_change:
            self.on_position_change(latitude, longitude)

    def get_position(self) -> Tuple[float, float]:
        """Gibt die aktuelle Position zurück."""
        return self._lat, self._lon

    def set_address(self, address: str):
        """Setzt die Position über eine Adresse (Geocoding via tkintermapview)."""
        if self._map_widget:
            try:
                self._map_widget.set_address(address)
                self.parent.after(1000, self._sync_position_from_map)
            except Exception as e:
                logger.warning(f"Geocoding fehlgeschlagen: {e}")
        else:
            try:
                from utils.pvgis_api import PVGISClient
                coords = PVGISClient.get_location_from_address(address)
                if coords:
                    self.set_position(coords[0], coords[1], zoom=15)
            except Exception:
                pass

    # ─── Private Methoden ────────────────────────────────────

    def _on_map_right_click(self, coords):
        lat, lon = coords
        self.set_position(lat, lon)

    def _sync_position_from_map(self):
        if self._map_widget:
            pos = self._map_widget.get_position()
            if pos:
                self._lat, self._lon = pos
                self.coord_label.configure(
                    text=f"Breite: {self._lat:.5f}°  |  Länge: {self._lon:.5f}°"
                )
