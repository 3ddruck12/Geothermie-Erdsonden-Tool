"""Internationalisierungs-Infrastruktur (i18n) für GET.

Stellt die _()-Funktion bereit, die Strings für zukünftige Übersetzung markiert.
Aktuell: reiner Passthrough (alle Texte bleiben auf Deutsch).

Zukünftig: gettext-Integration mit .po-Dateien in locales/.

Verwendung:
    from utils.i18n import _
    label = _("Bohrtiefe")
"""

import gettext
import os
import logging

logger = logging.getLogger(__name__)

_LOCALE_DIR = os.path.join(os.path.dirname(__file__), '..', 'locales')
_CURRENT_LANG = 'de'
_translation = None


def _(text: str) -> str:
    """Markiert einen String für Übersetzung.

    Aktuell: gibt den Text unverändert zurück (Passthrough).
    Wird aktiviert, sobald .po-Dateien in locales/ vorhanden sind.
    """
    if _translation is not None:
        return _translation.gettext(text)
    return text


def set_language(lang: str) -> None:
    """Setzt die aktive Sprache.

    Args:
        lang: Sprachcode (z.B. 'de', 'en', 'fr')
    """
    global _CURRENT_LANG, _translation
    _CURRENT_LANG = lang

    if lang == 'de':
        # Deutsch ist die Standardsprache → kein gettext nötig
        _translation = None
        logger.info("Sprache auf Deutsch gesetzt (Standard)")
        return

    try:
        _translation = gettext.translation(
            'get',
            localedir=_LOCALE_DIR,
            languages=[lang],
            fallback=True
        )
        logger.info(f"Sprache auf '{lang}' gesetzt")
    except Exception as e:
        logger.warning(f"Übersetzung für '{lang}' nicht gefunden: {e}")
        _translation = None


def get_language() -> str:
    """Gibt die aktive Sprache zurück."""
    return _CURRENT_LANG


def get_available_languages() -> list:
    """Gibt eine Liste verfügbarer Sprachen zurück."""
    languages = ['de']  # Deutsch ist immer verfügbar

    if os.path.isdir(_LOCALE_DIR):
        for entry in os.listdir(_LOCALE_DIR):
            locale_path = os.path.join(_LOCALE_DIR, entry, 'LC_MESSAGES')
            if os.path.isdir(locale_path):
                languages.append(entry)

    return sorted(set(languages))
