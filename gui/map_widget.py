"""Interaktives OSM-Karten-Widget für tkinter.

Nutzt tkintermapview für eine eingebettete OpenStreetMap-Karte.
Wird sowohl im Eingabe-Tab (Standort-Visualisierung) als auch
im Bohranzeige-Tab (Lageplan-Vorschau) verwendet.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Callable, Tuple
import logging
import threading

logger = logging.getLogger(__name__)

# tkintermapview optional laden (graceful degradation)
try:
    import tkintermapview
    HAS_MAPVIEW = True
except ImportError:
    HAS_MAPVIEW = False
    logger.warning("tkintermapview nicht installiert – Kartenansicht deaktiviert")

# Statische Karte als Fallback
try:
    from utils.osm_map import generate_static_map
    from PIL import ImageTk
    HAS_STATIC_MAP = True
except ImportError:
    HAS_STATIC_MAP = False


class OSMMapWidget:
    """Interaktives OSM-Karten-Widget mit Marker-Unterstützung.

    Verwendet tkintermapview für die interaktive Karte.
    Fällt auf ein statisches Bild zurück wenn tkintermapview fehlt.
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
        """
        Args:
            parent:              Übergeordnetes tkinter-Widget
            width:               Kartenbreite in Pixel
            height:              Kartenhöhe in Pixel
            default_lat:         Standard-Breitengrad (Deutschland-Mitte)
            default_lon:         Standard-Längengrad
            default_zoom:        Standard-Zoomstufe
            on_position_change:  Callback bei Positionsänderung (lat, lon)
        """
        self.parent = parent
        self.width = width
        self.height = height
        self.on_position_change = on_position_change

        self._lat = default_lat
        self._lon = default_lon
        self._zoom = default_zoom
        self._marker = None
        self._map_widget = None
        self._photo_image = None  # Referenz halten für GC

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
            font=("Arial", 9, "bold")
        )
        self.coord_label.pack(side="left")

        self.status_label = ttk.Label(
            info_frame, text="", foreground="gray", font=("Arial", 8, "italic")
        )
        self.status_label.pack(side="right")

        # Karte einbauen
        if HAS_MAPVIEW:
            self._build_interactive_map()
        elif HAS_STATIC_MAP:
            self._build_static_fallback()
        else:
            self._build_text_fallback()

        # Zoom-Buttons
        btn_frame = ttk.Frame(self.frame)
        btn_frame.pack(fill="x", padx=5, pady=(2, 5))

        ttk.Button(btn_frame, text="➕ Zoom +", width=10,
                   command=self._zoom_in).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="➖ Zoom −", width=10,
                   command=self._zoom_out).pack(side="left", padx=2)
        ttk.Label(btn_frame, text="© OpenStreetMap contributors",
                  foreground="gray", font=("Arial", 7)).pack(side="right", padx=5)

    # ─── Karten-Builder ─────────────────────────────────────

    def _build_interactive_map(self):
        """Baut die interaktive tkintermapview-Karte."""
        try:
            self._map_widget = tkintermapview.TkinterMapView(
                self.frame,
                width=self.width,
                height=self.height,
                corner_radius=0,
            )
            self._map_widget.pack(fill="both", expand=True, padx=5, pady=2)

            # Position setzen
            self._map_widget.set_position(self._lat, self._lon)
            self._map_widget.set_zoom(self._zoom)

            # Klick-Handler für Marker-Platzierung
            self._map_widget.add_right_click_menu_command(
                label="📍 Standort hier setzen",
                command=self._on_map_right_click,
                pass_coords=True,
            )

            self.status_label.configure(text="Rechtsklick → Standort setzen")
            logger.info("Interaktive OSM-Karte initialisiert")

        except Exception as e:
            logger.error(f"Fehler bei interaktiver Karte: {e}")
            self._build_static_fallback()

    def _build_static_fallback(self):
        """Zeigt ein statisches Kartenbild als Fallback."""
        self._canvas = tk.Canvas(
            self.frame, width=self.width, height=self.height,
            bg="#e8e8e8", highlightthickness=0
        )
        self._canvas.pack(fill="both", expand=True, padx=5, pady=2)
        self.status_label.configure(text="Statische Karte (Vorschau)")
        self._update_static_image()

    def _build_text_fallback(self):
        """Einfacher Text-Fallback wenn keine Kartenbibliothek vorhanden."""
        lbl = ttk.Label(
            self.frame,
            text="🗺️ Kartenvorschau nicht verfügbar\n\n"
                 "Installieren Sie tkintermapview:\n"
                 "pip install tkintermapview",
            foreground="gray",
            font=("Arial", 10),
            justify="center",
        )
        lbl.pack(fill="both", expand=True, padx=20, pady=30)

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

        # Koordinaten-Label aktualisieren
        self.coord_label.configure(
            text=f"Breite: {latitude:.5f}°  |  Länge: {longitude:.5f}°"
        )

        if self._map_widget and HAS_MAPVIEW:
            # Alten Marker entfernen
            if self._marker:
                self._marker.delete()

            self._map_widget.set_position(latitude, longitude)
            if zoom is not None:
                self._map_widget.set_zoom(zoom)

            # Neuen Marker setzen
            self._marker = self._map_widget.set_marker(
                latitude, longitude,
                text=f"Bohrstandort\n{latitude:.4f}°, {longitude:.4f}°"
            )
        elif hasattr(self, '_canvas'):
            self._update_static_image()

        # Callback aufrufen
        if self.on_position_change:
            self.on_position_change(latitude, longitude)

    def get_position(self) -> Tuple[float, float]:
        """Gibt die aktuelle Position zurück."""
        return self._lat, self._lon

    def set_address(self, address: str):
        """Setzt die Position über eine Adresse (Geocoding via tkintermapview)."""
        if self._map_widget and HAS_MAPVIEW:
            try:
                self._map_widget.set_address(address)
                # Position und Marker nach kurzer Verzögerung aktualisieren
                self.parent.after(1000, self._sync_position_from_map)
            except Exception as e:
                logger.warning(f"Geocoding fehlgeschlagen: {e}")
        else:
            # Fallback: eigene Geocoding-Funktion
            from utils.pvgis_api import PVGISClient
            coords = PVGISClient.get_location_from_address(address)
            if coords:
                self.set_position(coords[0], coords[1], zoom=15)

    # ─── Private Methoden ────────────────────────────────────

    def _on_map_right_click(self, coords):
        """Handler für Rechtsklick auf die Karte."""
        lat, lon = coords
        self.set_position(lat, lon)

    def _sync_position_from_map(self):
        """Synchronisiert die Position aus der interaktiven Karte."""
        if self._map_widget:
            pos = self._map_widget.get_position()
            if pos:
                self._lat, self._lon = pos
                self.coord_label.configure(
                    text=f"Breite: {self._lat:.5f}°  |  Länge: {self._lon:.5f}°"
                )

    def _update_static_image(self):
        """Aktualisiert das statische Kartenbild (Fallback)."""
        if not HAS_STATIC_MAP:
            return

        def _load():
            img = generate_static_map(
                self._lat, self._lon,
                zoom=self._zoom,
                width=self.width,
                height=self.height
            )
            if img:
                self.parent.after(0, lambda: self._set_canvas_image(img))

        threading.Thread(target=_load, daemon=True).start()

    def _set_canvas_image(self, img):
        """Setzt das Canvas-Bild (muss im Hauptthread laufen)."""
        try:
            self._photo_image = ImageTk.PhotoImage(img)
            self._canvas.delete("all")
            self._canvas.create_image(
                self.width // 2, self.height // 2,
                image=self._photo_image, anchor="center"
            )
        except Exception as e:
            logger.warning(f"Canvas-Bild konnte nicht gesetzt werden: {e}")

    def _zoom_in(self):
        """Zoom vergrößern."""
        if self._zoom < 19:
            self._zoom += 1
            if self._map_widget and HAS_MAPVIEW:
                self._map_widget.set_zoom(self._zoom)
            elif hasattr(self, '_canvas'):
                self._update_static_image()

    def _zoom_out(self):
        """Zoom verkleinern."""
        if self._zoom > 1:
            self._zoom -= 1
            if self._map_widget and HAS_MAPVIEW:
                self._map_widget.set_zoom(self._zoom)
            elif hasattr(self, '_canvas'):
                self._update_static_image()
