"""User configuration manager for SSG.

Stores persistent user preferences in a JSON file, such as:
- last_site_path: last selected or created site directory
- recent_sites: small MRU list of site directories
- theme: selected Textual theme for the TUI
- last_base_dir: last base directory used in the new-site wizard
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional
import json


class ConfigManager:
    """Manage a JSON-based user configuration for the TUI.

    By default, stores the config in the user's home directory as
    ~/.ssg_user_config.json (Windows: %USERPROFILE%\.ssg_user_config.json).
    """

    DEFAULTS: Dict[str, Any] = {
        "last_site_path": "",
        "recent_sites": [],
        "theme": "gruvbox",
        "language": "en",  # Default to English
        "last_base_dir": str(Path.home()),
    }

    def __init__(self, config_path: Optional[Path] = None) -> None:
        """Initialize the configuration manager.

        Args:
            config_path: Optional path to the JSON configuration file. If not
                provided, a `config.json` in the current module directory will be
                used.
        """
        if config_path is None:
            # Use current script directory instead of user home
            current_dir = Path(__file__).parent
            self.config_path: Path = current_dir / "config.json"
        else:
            self.config_path: Path = config_path
        self._data: Dict[str, Any] = dict(self.DEFAULTS)
        self._load()

    # -------------------------- IO -------------------------- #
    def _load(self) -> None:
        """Load configuration from disk or initialize with defaults.

        Merges the stored values with DEFAULTS to ensure forward compatibility.
        Any read/parse error falls back to defaults to avoid crashing the TUI.
        """
        try:
            if self.config_path.exists():
                raw = self.config_path.read_text(encoding="utf-8")
                data = json.loads(raw)
                if isinstance(data, dict):
                    # Merge with defaults to keep forward compatibility
                    merged = dict(self.DEFAULTS)
                    merged.update(data)
                    self._data = merged
                else:
                    self._data = dict(self.DEFAULTS)
            else:
                # Ensure parent exists for later writes
                self.config_path.parent.mkdir(parents=True, exist_ok=True)
                self._data = dict(self.DEFAULTS)
        except Exception as e:
            # On any error, fall back to defaults (avoid crashing the TUI)
            # This might be called without the TUI available yet, so print to console as fallback
            try:
                from .ui.log import UILog  # Absolute import for internal usage
                log = UILog()
                log.write(f"Warning: Failed to load user config, using defaults: {e}")
            except (ImportError, Exception):
                print(f"Warning: Failed to load user config, using defaults: {e}")
            self._data = dict(self.DEFAULTS)

    def _save(self) -> None:
        """Persist the in-memory configuration to disk.

        Silently ignores IO errors to avoid disrupting the UI.
        """
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            self.config_path.write_text(json.dumps(self._data, indent=2), encoding="utf-8")
        except Exception as e:
            # Silently ignore to not disturb the UI; logging can be added by caller if needed
            # This might be called without the TUI available yet, so print to console as fallback
            try:
                import sys
                # Try to find and use the current UILog if available
                if 'ssg_app' in sys.modules:
                    ssg_app = sys.modules['ssg_app']
                    if hasattr(ssg_app, '_current_log'):
                        ssg_app._current_log.write(f"Warning: Failed to save user config: {e}")
                    elif hasattr(ssg_app, 'ui_log'):
                        ssg_app.ui_log.write(f"Warning: Failed to save user config: {e}")
                else:
                    print(f"Warning: Failed to save user config: {e}")
            except Exception:
                print(f"Warning: Failed to save user config: {e}")

    # -------------------------- Theme -------------------------- #
    def get_theme(self) -> str:
        """Return the current UI theme name.

        Returns:
            The theme identifier stored in the configuration.
        """
        return str(self._data.get("theme", self.DEFAULTS["theme"]))

    def set_theme(self, theme: str) -> None:
        """Persist a new UI theme name.

        Args:
            theme: Name of the theme to set.
        """
        self._data["theme"] = str(theme)
        self._save()

    # -------------------------- Language -------------------------- #
    def get_language(self) -> str:
        """Return the current language code (e.g., 'en', 'it').

        Returns:
            The ISO-like language code stored in the configuration.
        """
        return str(self._data.get("language", self.DEFAULTS["language"]))

    def set_language(self, language: str) -> None:
        """Persist the current language code.

        Args:
            language: Language identifier (e.g., 'en', 'it').
        """
        self._data["language"] = str(language)
        self._save()

    # -------------------------- Site paths -------------------------- #
    def get_last_site_path(self) -> str:
        """Return the last opened/created site path.

        Returns:
            Absolute path string of the last site used, or empty string.
        """
        return str(self._data.get("last_site_path", ""))

    def set_last_site_path(self, path: str | Path) -> None:
        """Persist the given site path as the last used and add to MRU.

        Args:
            path: Filesystem path of the site directory.
        """
        path_str = str(Path(path))
        self._data["last_site_path"] = path_str
        self._add_recent_internal(path_str)
        self._save()

    def get_recent_sites(self) -> List[str]:
        """Return the MRU list of recent site paths.

        Returns:
            List of absolute path strings ordered by recency.
        """
        items = self._data.get("recent_sites", [])
        if isinstance(items, list):
            # Keep strings only
            return [str(x) for x in items]
        return []

    def add_recent_site(self, path: str | Path) -> None:
        """Add a path to the MRU list and persist.

        Args:
            path: Filesystem path of the site directory.
        """
        self._add_recent_internal(str(Path(path)))
        self._save()

    def _add_recent_internal(self, path_str: str) -> None:
        """Insert a path at the top of the MRU list (de-duplicated, capped).

        Args:
            path_str: Absolute path string to insert.
        """
        # Keep a small MRU list without duplicates
        mru: List[str] = [str(p) for p in self._data.get("recent_sites", []) if isinstance(p, (str,))]
        # Remove if exists, then insert at top
        mru = [p for p in mru if p != path_str]
        mru.insert(0, path_str)
        # Trim to 10 entries
        self._data["recent_sites"] = mru[:10]

    # -------------------------- Wizard base dir -------------------------- #
    def get_last_base_dir(self) -> str:
        """Return the last base directory used for site creation.

        Returns:
            Absolute path string for the last base directory.
        """
        return str(self._data.get("last_base_dir", self.DEFAULTS["last_base_dir"]))

    def set_last_base_dir(self, path: str | Path) -> None:
        """Persist the last base directory path.

        Args:
            path: Filesystem path to store as the last base directory.
        """
        self._data["last_base_dir"] = str(Path(path))
        self._save()
