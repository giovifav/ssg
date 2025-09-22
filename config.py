"""Configuration management for Gio's static site generator."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Optional, Any

# Configure logging for config module
logger = logging.getLogger(__name__)

# Initialize TOML library imports
tomllib: Optional[object] = None
toml: Optional[object] = None

try:
    # Python 3.11+ has built-in tomllib
    if sys.version_info >= (3, 11):
        import tomllib  # type: ignore
except ImportError:
    logger.debug("tomllib not available (Python < 3.11)")
    tomllib = None

try:
    # Fallback TOML library for older Python versions
    import toml  # type: ignore
except ImportError:
    logger.debug("toml package not available. Install with: pip install toml")
    toml = None
except Exception as e:
    logger.warning(f"Error importing toml package: {e}")
    toml = None


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
        base_url: Base URL of the site (used for sitemap generation).
    """

    site_name: str
    author: str
    footer: str
    output: str
    base_theme: str
    theme_css: str
    base_url: Optional[str] = None


def read_config(site_root: Path) -> SiteConfig:
    """Read site's config.toml and return a SiteConfig object.

    Args:
        site_root: Path to the site project root (contains config.toml).

    Returns:
        SiteConfig instance.

    Raises:
        FileNotFoundError: If config.toml doesn't exist.
        ValueError: If config file is invalid or contains invalid values.
        RuntimeError: If no TOML library is available.
    """
    cfg_path = site_root / "config.toml"

    # Check if config file exists
    if not cfg_path.exists():
        raise FileNotFoundError(f"config.toml not found at: {cfg_path}")

    # Read and parse the file
    try:
        raw = cfg_path.read_bytes()
        if tomllib is not None:
            data = tomllib.loads(raw.decode("utf-8"))
            logger.debug("Using tomllib for TOML parsing")
        elif toml is not None:  # pragma: no cover
            data = toml.loads(raw.decode("utf-8"))
            logger.debug("Using toml package for TOML parsing (fallback)")
        else:  # pragma: no cover
            raise RuntimeError(
                "No TOML reader available. Use Python 3.11+ or install 'toml' package."
            )
    except UnicodeDecodeError as e:
        raise ValueError(f"config.toml contains invalid UTF-8 encoding: {e}")
    except Exception as e:
        raise ValueError(f"Failed to parse config.toml: {e}")

    # Validate configuration data
    config_data, validation_errors = _validate_config_data(data)
    if validation_errors:
        error_msg = "Invalid configuration in config.toml:\n" + "\n".join(f"  - {err}" for err in validation_errors)
        raise ValueError(error_msg)

    # Validate theme file paths
    theme_path = config_data["base_theme"]
    css_path = config_data["theme_css"]

    # Check if theme files exist relative to site root
    theme_file = site_root / theme_path
    css_file = site_root / css_path

    warnings = []
    if not theme_file.exists():
        warnings.append(f"Theme file '{theme_path}' not found at {theme_file}")
    if not css_file.exists():
        warnings.append(f"CSS file '{css_path}' not found at {css_file}")

    if warnings:
        for warning in warnings:
            logger.warning(warning)

    return SiteConfig(**config_data)


def _validate_config_data(data: dict) -> tuple[dict, list[str]]:
    """Validate configuration data from TOML file.

    Args:
        data: Dictionary containing parsed TOML data.

    Returns:
        Tuple of (validated_config_dict, list_of_error_messages).
        If errors are present, the second element will contain error messages.
    """
    errors = []
    validated = {}

    # Define required and optional fields with their expected types and defaults
    schema = {
        "site_name": {"type": str, "default": "My Site", "required": False},
        "author": {"type": str, "default": "Unknown", "required": False},
        "footer": {"type": str, "default": "Copyright 2025", "required": False},
        "output": {"type": str, "default": "output", "required": False},
        "base_theme": {"type": str, "default": "assets/theme.html", "required": False},
        "theme_css": {"type": str, "default": "assets/theme.css", "required": False},
        "base_url": {"type": str, "default": None, "required": False},
    }

    for field_name, field_config in schema.items():
        value = data.get(field_name)

        if value is None:
            # Use default value for optional fields
            if not field_config["required"]:
                validated[field_name] = field_config["default"]
                logger.debug(f"Using default value for {field_name}: {field_config['default']}")
            else:
                errors.append(f"Required field '{field_name}' is missing")
            continue

        # Type validation
        expected_type = field_config["type"]
        if not isinstance(value, expected_type):
            try:
                # Try to convert to expected type
                if expected_type == str:
                    validated[field_name] = str(value)
                elif expected_type == int:
                    validated[field_name] = int(value)
                else:
                    errors.append(f"Field '{field_name}' has invalid type. Expected {expected_type.__name__}, got {type(value).__name__}")
                    continue
            except (ValueError, TypeError):
                errors.append(f"Field '{field_name}' cannot be converted to {expected_type.__name__}: {value}")
                continue
        else:
            validated[field_name] = value

        # Additional validations for specific fields
        if field_name in ["base_theme", "theme_css"]:
            _validate_path_field(validated[field_name], field_name, errors)
        elif field_name == "output":
            if not validated[field_name] or not isinstance(validated[field_name], str):
                errors.append(f"Field '{field_name}' must be a non-empty string")
        elif field_name == "base_url":
            if validated[field_name] and not isinstance(validated[field_name], str):
                errors.append(f"Field '{field_name}' must be a string")

    return validated, errors


def _validate_path_field(value: str, field_name: str, errors: list[str]) -> None:
    """Validate path-related fields for basic sanity checks."""
    if not value:
        errors.append(f"Field '{field_name}' cannot be empty")
        return

    # Check for obvious path traversal attempts
    if ".." in value:
        errors.append(f"Field '{field_name}' contains potential path traversal: '..' not allowed in {value}")

    # Path should be relative (not absolute)
    path = Path(value)
    if path.is_absolute():
        errors.append(f"Field '{field_name}' should be a relative path, not absolute: {value}")


def sanitize_path(user_path: str, allowed_base_path: Path, base_dir: Path = None) -> Path:
    """Sanitize a user-provided path to prevent directory traversal attacks.

    Args:
        user_path: The user-provided path string.
        allowed_base_path: The base path that the resolved path must be within.
        base_dir: Optional directory to join user_path with before resolving.

    Returns:
        Resolved Path object if within allowed base.

    Raises:
        ValueError: If the resolved path is outside allowed_base_path.
    """
    if base_dir:
        full_path = base_dir / user_path
    else:
        full_path = Path(user_path)
    resolved = full_path.resolve()
    allowed_resolved = allowed_base_path.resolve()
    if not resolved.is_relative_to(allowed_resolved):
        raise ValueError("Path traversal attempt detected")
    return resolved


def write_config_toml(
    site_root: Path,
    site_name: str,
    author: str,
    *,
    output: str = "output",
    footer: str = "Copyright 2025",
    base_theme: str = "assets/theme.html",
    theme_css: str = "assets/theme.css",
    base_url: Optional[str] = None,
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

    Raises:
        ValueError: If provided values are invalid.
        IOError: If file cannot be written.
    """
    # Validate input parameters
    config_dict = {
        "site_name": site_name,
        "author": author,
        "footer": footer,
        "output": output,
        "base_theme": base_theme,
        "theme_css": theme_css,
        "base_url": base_url,
    }

    _, validation_errors = _validate_config_data(config_dict)
    if validation_errors:
        error_msg = "Invalid configuration values:\n" + "\n".join(f"  - {err}" for err in validation_errors)
        raise ValueError(error_msg)

    # Write the config file
    try:
        content = (
            f"site_name = \"{site_name}\"\n"
            f"author = \"{author}\"\n"
            f"footer = \"{footer}\"\n"
            f"output = \"{output}\"\n"
            f"base_theme = \"{base_theme}\"\n"
            f"theme_css = \"{theme_css}\"\n"
        )
        if base_url is not None:
            content += f"base_url = \"{base_url}\"\n"
        cfg_path = site_root / "config.toml"
        cfg_path.write_text(content, encoding="utf-8")
        logger.info(f"Successfully wrote config.toml to {cfg_path}")
    except Exception as e:
        raise IOError(f"Failed to write config.toml: {e}") from e
