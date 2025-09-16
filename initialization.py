"""Site initialization logic for Gio's static site generator."""

from __future__ import annotations

from pathlib import Path
import shutil

from config import write_config_toml


def initialize_site(
    base_path: Path,
    folder_name: str,
    site_name: str,
    author: str,
) -> Path:
    """Create a new site skeleton under base_path/folder_name.

    Creates the target directory, copies theme files, writes config.toml,
    scaffolds content/index.md, and ensures an empty output/ directory.
    Returns the path to the created site root.
    """
    site_root = base_path / folder_name
    site_root.mkdir(parents=True, exist_ok=True)

    # Copy theme assets (no longer copying to site root - only to assets folder)
    # Use repository root where this file resides (not parent of parent)
    REPO_ROOT = Path(__file__).resolve().parent

    # Copy default assets folder (including gallery assets) into the new site
    assets_src = REPO_ROOT / "assets"
    assets_dst = site_root / "assets"
    if assets_src.exists() and assets_src.is_dir():
        if assets_dst.exists():
            shutil.rmtree(assets_dst)
        shutil.copytree(assets_src, assets_dst)

    # Write config.toml
    write_config_toml(
        site_root,
        site_name=site_name,
        author=author,
        output="output",
        footer="Copyright 2025",
        base_theme="assets/theme.html",
        theme_css="assets/theme.css",
    )

    # Create content/index.md
    content_dir = site_root / "content"
    content_dir.mkdir(parents=True, exist_ok=True)
    index_md = (
        "---\n"
        f"title: {site_name}\n"
        "date: 2025-01-01\n"
        "---\n\n"
        "# Welcome\n\nThis is your new site. Edit content/index.md to get started.\n"
    )
    (content_dir / "index.md").write_text(index_md, encoding="utf-8")

    # Ensure output directory exists (empty)
    (site_root / "output").mkdir(parents=True, exist_ok=True)

    return site_root
