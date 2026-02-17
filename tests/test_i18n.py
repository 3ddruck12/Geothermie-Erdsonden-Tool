"""Tests für utils/i18n.py – Internationalisierungs-Infrastruktur."""

import pytest
from utils.i18n import _, set_language, get_language, get_available_languages


class TestI18nPassthrough:
    """Tests für den i18n Passthrough-Modus."""

    def test_passthrough_returns_same_string(self):
        """_() gibt den Text unverändert zurück."""
        assert _("Hallo Welt") == "Hallo Welt"

    def test_passthrough_empty_string(self):
        """Leerer String bleibt leer."""
        assert _("") == ""

    def test_passthrough_special_chars(self):
        """Sonderzeichen werden nicht verändert."""
        assert _("Wärmeleitfähigkeit [W/m·K]") == "Wärmeleitfähigkeit [W/m·K]"

    def test_passthrough_unicode(self):
        """Unicode-Strings funktionieren."""
        assert _("Ø Temperatur") == "Ø Temperatur"


class TestSetLanguage:
    """Tests für Spracheinstellungen."""

    def test_default_language_is_german(self):
        """Standardsprache ist Deutsch."""
        assert get_language() == "de"

    def test_set_language_german(self):
        """Deutsch setzen funktioniert ohne Fehler."""
        set_language("de")
        assert get_language() == "de"

    def test_set_language_english_fallback(self):
        """Englisch setzen funktioniert (Fallback)."""
        set_language("en")
        assert get_language() == "en"
        # Zurücksetzen
        set_language("de")

    def test_passthrough_after_unknown_language(self):
        """Unbekannte Sprache → Fallback auf Passthrough."""
        set_language("xx")
        assert _("Test") == "Test"
        # Zurücksetzen
        set_language("de")


class TestAvailableLanguages:
    """Tests für verfügbare Sprachen."""

    def test_german_always_available(self):
        """Deutsch ist immer verfügbar."""
        langs = get_available_languages()
        assert "de" in langs

    def test_returns_list(self):
        """Gibt eine Liste zurück."""
        langs = get_available_languages()
        assert isinstance(langs, list)
