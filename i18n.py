"""i18n - Internationalization module for the static site generator TUI.

Loads translations from JSON files and provides translation functions.
Supports English and Italian with fallback handling.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any


class I18N:
    """Internationalization class that loads translations from JSON files."""

    DEFAULT_LANGUAGE = "en"

    def __init__(self, language: str = DEFAULT_LANGUAGE) -> None:
        self._translations: Dict[str, Dict[str, Any]] = {}
        self._current_language = language
        self._languages_dir = Path(__file__).parent / "languages"

        # Create languages directory if it doesn't exist
        self._languages_dir.mkdir(exist_ok=True)

        # Load default language first, then current language
        self._load_language("en")
        self._load_language(language)

    def _load_language(self, language: str) -> None:
        """Load translations for a specific language."""
        lang_file = self._languages_dir / f"{language}.json"
        if lang_file.exists():
            try:
                with open(lang_file, 'r', encoding='utf-8') as f:
                    translations = json.load(f)
                    if isinstance(translations, dict):
                        self._translations[language] = translations
            except Exception:
                # If loading fails, skip this language
                pass

    def set_language(self, language: str) -> None:
        """Change the current language."""
        if language in self._translations:
            self._current_language = language
        else:
            # Load language if not already loaded
            self._load_language(language)
            if language in self._translations:
                self._current_language = language

    def get_language(self) -> str:
        """Get current language."""
        return self._current_language

    def translate(self, key: str, fallback: str = "") -> str:
        """Get translation for a key with fallback."""
        if self._current_language in self._translations:
            lang_dict = self._translations[self._current_language]
            if key in lang_dict:
                return str(lang_dict[key])

        # Fallback to English
        if "en" in self._translations:
            en_dict = self._translations["en"]
            if key in en_dict:
                return str(en_dict[key])

        # Final fallback to provided fallback or the key itself
        return fallback or key

    def __call__(self, key: str, fallback: str = "") -> str:
        """Shortcut for translate method."""
        return self.translate(key, fallback)


# Global i18n instance
_i18n_instance: I18N | None = None


def get_i18n() -> I18N:
    """Get the global i18n instance."""
    global _i18n_instance
    if _i18n_instance is None:
        _i18n_instance = I18N()
    return _i18n_instance


def translate(key: str, fallback: str = "") -> str:
    """Global translate function."""
    return get_i18n().translate(key, fallback)


def set_global_language(language: str) -> None:
    """Set global language."""
    get_i18n().set_language(language)


def get_global_language() -> str:
    """Get global language."""
    return get_i18n().get_language()
