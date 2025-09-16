"""Configuration management for Gio's static site generator."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys

try:  # Python 3.11+
    import tomllib  # type: ignore
except Exception:  # pragma: no cover
    tomllib = None  # type: ignore

try:  # Fallback for reading TOML on older Python versions
    import toml  # type: ignore
except Exception:  # pragma: no cover
    toml = None  # type: ignore


@dataclass
class SiteConfig:
    """Configuration for a site read from config.toml.

    Attributes:
        site_name: Human-readable site name.
        author: Author name.
        footer: Footer text.
        output: Output directory name (relative to site root).
        base_theme: Theme HTML filename (located in the site root).
        theme_css: Theme CSS filename (located in the site root).
    """

    site_name: str
    author: str
    footer: str
    output: str
    base_theme: str
    theme_css: str


def read_config(site_root: Path) -> SiteConfig:
    """Read site's config.toml and return a SiteConfig object.

    Args:
        site_root: Path to the site project root (contains config.toml).

    Returns:
        SiteConfig instance.
    """
    cfg_path = site_root / "config.toml"
    if not cfg_path.exists():
        raise FileNotFoundError(f"config.toml not found at: {cfg_path}")

    raw = cfg_path.read_bytes()

    if tomllib is not None:
        data = tomllib.loads(raw.decode("utf-8"))
    elif toml is not None:  # pragma: no cover
        data = toml.loads(raw.decode("utf-8"))
    else:  # pragma: no cover
        raise RuntimeError(
            "No TOML reader available. Use Python 3.11+ or install 'toml'."
        )

    # Validate and build config
    site_name = str(data.get("site_name", "My Site"))
    author = str(data.get("author", "Unknown"))
    footer = str(data.get("footer", "Copyright 2025"))
    output = str(data.get("output", "output"))
    base_theme = str(data.get("base_theme", "assets/theme.html"))
    theme_css = str(data.get("theme_css", "assets/theme.css"))

    return SiteConfig(
        site_name=site_name,
        author=author,
        footer=footer,
        output=output,
        base_theme=base_theme,
        theme_css=theme_css,
    )


def write_config_toml(
    site_root: Path,
    site_name: str,
    author: str,
    *,
    output: str = "output",
    footer: str = "Copyright 2025",
    base_theme: str = "assets/theme.html",
    theme_css: str = "assets/theme.css",
) -> None:
    """Create a config.toml file with provided values.

    Args:
        site_root: Target site root directory.
        site_name: Site name.
        author: Author name.
        output: Output directory name.
        footer: Footer text.
        base_theme: Theme HTML filename.
        theme_css: Theme CSS filename.
    """
    content = (
        f"site_name = \"{site_name}\"\n"
        f"author = \"{author}\"\n"
        f"footer = \"{footer}\"\n"
        f"output = \"{output}\"\n"
        f"base_theme = \"{base_theme}\"\n"
        f"theme_css = \"{theme_css}\"\n"
    )
    (site_root / "config.toml").write_text(content, encoding="utf-8")
