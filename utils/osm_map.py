"""OSM-Kartenmodul für statische Karten (PDF) und GUI-Integration.

Lädt OpenStreetMap-Kacheln herunter und erzeugt ein statisches Kartenbild
mit Standort-Marker. Wird für den Lageplan in der Bohranzeige-PDF und
die interaktive Kartenanzeige in der GUI verwendet.

Tile-Server: OpenStreetMap (© OpenStreetMap contributors)
Lizenz: ODbL (https://www.openstreetmap.org/copyright)
"""

import math
import io
import os
import tempfile
import logging
from typing import Optional, Tuple

import requests
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)

# ── Konstanten ───────────────────────────────────────────────

TILE_SIZE = 256
OSM_TILE_URL = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
USER_AGENT = "GeothermieErdsonden-Tool/3.3 (Bohranzeige-Lageplan)"

# Standard-Zoom und Bildgröße
DEFAULT_ZOOM = 16
DEFAULT_IMAGE_WIDTH = 600    # Pixel
DEFAULT_IMAGE_HEIGHT = 400   # Pixel

# Marker-Farben
MARKER_COLOR_OUTER = (31, 71, 136)      # #1f4788 – Tool-Blau
MARKER_COLOR_INNER = (255, 80, 80)      # Rot-Punkt
MARKER_COLOR_WHITE = (255, 255, 255)


# ── Tile-Berechnungen ────────────────────────────────────────

def _lat_lon_to_tile(lat: float, lon: float, zoom: int) -> Tuple[float, float]:
    """Berechnet fraktionale Tile-Koordinaten aus Lat/Lon."""
    n = 2 ** zoom
    x = (lon + 180.0) / 360.0 * n
    lat_rad = math.radians(lat)
    y = (1.0 - math.log(math.tan(lat_rad) + 1.0 / math.cos(lat_rad)) / math.pi) / 2.0 * n
    return x, y


def _download_tile(z: int, x: int, y: int) -> Optional[Image.Image]:
    """Lädt eine einzelne OSM-Kachel herunter."""
    url = OSM_TILE_URL.format(z=z, x=x, y=y)
    try:
        resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=10)
        if resp.status_code == 200:
            return Image.open(io.BytesIO(resp.content)).convert("RGB")
        else:
            logger.warning(f"Tile-Download fehlgeschlagen: {url} → {resp.status_code}")
            return None
    except Exception as e:
        logger.warning(f"Tile-Download Fehler: {e}")
        return None


def _draw_marker(img: Image.Image, px: int, py: int, size: int = 14):
    """Zeichnet einen Standort-Marker auf das Bild."""
    draw = ImageDraw.Draw(img)

    # Äußerer Kreis (blau)
    r_outer = size
    draw.ellipse(
        [px - r_outer, py - r_outer, px + r_outer, py + r_outer],
        fill=MARKER_COLOR_OUTER, outline=MARKER_COLOR_WHITE, width=2
    )

    # Innerer Kreis (rot)
    r_inner = size // 3
    draw.ellipse(
        [px - r_inner, py - r_inner, px + r_inner, py + r_inner],
        fill=MARKER_COLOR_INNER
    )

    # Fadenkreuz
    line_len = size + 6
    draw.line([px - line_len, py, px - r_outer - 2, py], fill=MARKER_COLOR_OUTER, width=2)
    draw.line([px + r_outer + 2, py, px + line_len, py], fill=MARKER_COLOR_OUTER, width=2)
    draw.line([px, py - line_len, px, py - r_outer - 2], fill=MARKER_COLOR_OUTER, width=2)
    draw.line([px, py + r_outer + 2, px, py + line_len], fill=MARKER_COLOR_OUTER, width=2)


def _add_attribution(img: Image.Image):
    """Fügt OSM-Attribution unten rechts hinzu."""
    draw = ImageDraw.Draw(img)
    text = "© OpenStreetMap"
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 10)
    except (IOError, OSError):
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]

    x = img.width - tw - 6
    y = img.height - th - 6
    # Hintergrund
    draw.rectangle([x - 3, y - 2, x + tw + 3, y + th + 2], fill=(255, 255, 255, 200))
    draw.text((x, y), text, fill=(80, 80, 80), font=font)


def _add_coordinates_label(img: Image.Image, lat: float, lon: float):
    """Fügt Koordinaten-Beschriftung oben links hinzu."""
    draw = ImageDraw.Draw(img)
    text = f"Breite: {lat:.5f}°  |  Länge: {lon:.5f}°"
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 11)
    except (IOError, OSError):
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]

    x, y = 6, 6
    draw.rectangle([x - 3, y - 2, x + tw + 6, y + th + 4], fill=(255, 255, 255, 220))
    draw.text((x, y), text, fill=MARKER_COLOR_OUTER, font=font)


# ── Öffentliche API ──────────────────────────────────────────

def generate_static_map(
    latitude: float,
    longitude: float,
    zoom: int = DEFAULT_ZOOM,
    width: int = DEFAULT_IMAGE_WIDTH,
    height: int = DEFAULT_IMAGE_HEIGHT,
    show_marker: bool = True,
    show_coords: bool = True,
) -> Optional[Image.Image]:
    """
    Erzeugt ein statisches Kartenbild für gegebene Koordinaten.

    Args:
        latitude:    Breitengrad
        longitude:   Längengrad
        zoom:        OSM-Zoomstufe (1–19), Standard 16
        width:       Bildbreite in Pixel
        height:      Bildhöhe in Pixel
        show_marker: Standort-Marker zeichnen
        show_coords: Koordinaten-Label einblenden

    Returns:
        PIL.Image.Image oder None bei Fehler
    """
    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        logger.error(f"Ungültige Koordinaten: {latitude}, {longitude}")
        return None

    try:
        # Fraktionale Tile-Position des Zentrums
        cx, cy = _lat_lon_to_tile(latitude, longitude, zoom)

        # Wie viele Tiles in jede Richtung benötigt?
        tiles_x = math.ceil(width / TILE_SIZE) + 1
        tiles_y = math.ceil(height / TILE_SIZE) + 1

        # Start-Tile (links oben)
        start_tx = int(cx) - tiles_x // 2
        start_ty = int(cy) - tiles_y // 2

        # Großes Canvas bauen
        canvas_w = tiles_x * TILE_SIZE
        canvas_h = tiles_y * TILE_SIZE
        canvas = Image.new("RGB", (canvas_w, canvas_h), (240, 240, 240))

        n_tiles = 2 ** zoom

        for dx in range(tiles_x):
            for dy in range(tiles_y):
                tx = (start_tx + dx) % n_tiles
                ty = start_ty + dy
                if ty < 0 or ty >= n_tiles:
                    continue

                tile = _download_tile(zoom, tx, ty)
                if tile:
                    canvas.paste(tile, (dx * TILE_SIZE, dy * TILE_SIZE))

        # Pixel-Position des Zentrums auf dem Canvas
        px_center = int((cx - start_tx) * TILE_SIZE)
        py_center = int((cy - start_ty) * TILE_SIZE)

        # Ausschnitt zentriert um die Position
        left = px_center - width // 2
        top = py_center - height // 2
        crop_box = (left, top, left + width, top + height)
        result = canvas.crop(crop_box)

        # Marker
        if show_marker:
            marker_x = width // 2
            marker_y = height // 2
            _draw_marker(result, marker_x, marker_y)

        # Attribution
        _add_attribution(result)

        # Koordinaten-Label
        if show_coords:
            _add_coordinates_label(result, latitude, longitude)

        return result

    except Exception as e:
        logger.error(f"Fehler beim Erzeugen der statischen Karte: {e}")
        return None


def save_static_map(
    latitude: float,
    longitude: float,
    filepath: str,
    zoom: int = DEFAULT_ZOOM,
    width: int = DEFAULT_IMAGE_WIDTH,
    height: int = DEFAULT_IMAGE_HEIGHT,
) -> bool:
    """
    Erzeugt und speichert eine statische Karte als PNG.

    Args:
        latitude:  Breitengrad
        longitude: Längengrad
        filepath:  Zielpfad für das PNG
        zoom:      Zoomstufe
        width:     Bildbreite
        height:    Bildhöhe

    Returns:
        True bei Erfolg
    """
    img = generate_static_map(latitude, longitude, zoom, width, height)
    if img is None:
        return False

    try:
        os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else ".", exist_ok=True)
        img.save(filepath, "PNG", quality=95)
        logger.info(f"Statische Karte gespeichert: {filepath}")
        return True
    except Exception as e:
        logger.error(f"Fehler beim Speichern der Karte: {e}")
        return False


def generate_static_map_bytes(
    latitude: float,
    longitude: float,
    zoom: int = DEFAULT_ZOOM,
    width: int = DEFAULT_IMAGE_WIDTH,
    height: int = DEFAULT_IMAGE_HEIGHT,
) -> Optional[bytes]:
    """
    Erzeugt eine statische Karte und gibt PNG-Bytes zurück.

    Nützlich für die direkte Einbettung in reportlab-PDFs.
    """
    img = generate_static_map(latitude, longitude, zoom, width, height)
    if img is None:
        return None

    buf = io.BytesIO()
    img.save(buf, "PNG", quality=95)
    buf.seek(0)
    return buf.getvalue()


def generate_map_tempfile(
    latitude: float,
    longitude: float,
    zoom: int = DEFAULT_ZOOM,
    width: int = DEFAULT_IMAGE_WIDTH,
    height: int = DEFAULT_IMAGE_HEIGHT,
) -> Optional[str]:
    """
    Erzeugt eine statische Karte als temporäre PNG-Datei.

    Returns:
        Pfad zur temporären Datei oder None
    """
    img = generate_static_map(latitude, longitude, zoom, width, height)
    if img is None:
        return None

    try:
        tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False, prefix="get_lageplan_")
        img.save(tmp, "PNG", quality=95)
        tmp.close()
        logger.info(f"Lageplan-Tempfile: {tmp.name}")
        return tmp.name
    except Exception as e:
        logger.error(f"Fehler beim Erstellen der Temp-Karte: {e}")
        return None


# ── Standalone-Test ──────────────────────────────────────────

if __name__ == "__main__":
    print("OSM Static Map Test")
    print("=" * 50)

    # Testkoordinaten: Berlin Mitte
    lat, lon = 52.5200, 13.4050

    img = generate_static_map(lat, lon, zoom=15, width=600, height=400)
    if img:
        out_path = "/tmp/test_osm_map.png"
        img.save(out_path)
        print(f"✅ Karte gespeichert: {out_path}  ({img.size[0]}x{img.size[1]})")
    else:
        print("❌ Karte konnte nicht erzeugt werden")
