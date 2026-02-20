"""Zentrale Versionsverwaltung – liest aus VERSION-Datei."""

import os

# Projekt-Root (ein Verzeichnis über utils/)
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_VERSION_FILE = os.path.join(_ROOT, "VERSION")


def get_version() -> str:
    """Liest die aktuelle Version aus der VERSION-Datei."""
    try:
        with open(_VERSION_FILE, encoding="utf-8") as f:
            return f.read().strip()
    except (FileNotFoundError, OSError):
        return "3.4.1-beta2"


# Beim Import einmal laden
APP_VERSION = get_version()
