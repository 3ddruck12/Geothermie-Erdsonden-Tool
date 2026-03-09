"""Anwendungseinstellungen (Theme, Sprache, …) persistent speichern."""

import json
import os
from pathlib import Path

_CONFIG_DIR = Path.home() / ".config" / "geothermietool"
_CONFIG_FILE = _CONFIG_DIR / "settings.json"

_DEFAULTS = {
    "theme": "cosmo",
}

# Dark-Themes für Matplotlib-Anpassung
DARK_THEMES = {"darkly", "cyborg", "solar", "superhero", "vapor"}

# Hell-/Dunkel-Gruppierung für die UI
LIGHT_THEMES = [
    "cosmo", "flatly", "litera", "lumen", "minty",
    "morph", "pulse", "sandstone", "simplex",
    "united", "yeti", "journal", "cerculean",
]
DARK_THEMES_LIST = ["darkly", "cyborg", "solar", "superhero", "vapor"]


def load() -> dict:
    """Lädt Einstellungen aus der Konfigurationsdatei."""
    try:
        if _CONFIG_FILE.exists():
            with open(_CONFIG_FILE, encoding="utf-8") as f:
                data = json.load(f)
            return {**_DEFAULTS, **data}
    except Exception:
        pass
    return dict(_DEFAULTS)


def save(settings: dict) -> None:
    """Speichert Einstellungen in die Konfigurationsdatei."""
    try:
        _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


def get(key: str):
    return load().get(key, _DEFAULTS.get(key))


def set_value(key: str, value) -> None:
    s = load()
    s[key] = value
    save(s)
