"""Site generation logic for Gio's static site generator."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import json
import os
import re
import shutil
import time

import frontmatter  # type: ignore
import markdown  # type: ignore
from jinja2 import Template, Environment, FileSystemLoader  # type: ignore
try:
    from PIL import Image, ImageOps  # type: ignore
except Exception:
    Image = None  # type: ignore
    ImageOps = None  # type: ignore

try:
    from config import SiteConfig, read_config, sanitize_path
    from i18n import translate, set_global_language
    from nav_builder import (
        NavNode,
        discover_markdown_files,
        build_nav_tree,
        render_sidebar_html,
        build_breadcrumbs,
        load_title_from_markdown
    )
except ImportError:
    from .config import SiteConfig, read_config, sanitize_path
    from .i18n import translate, set_global_language
    from .nav_builder import (
        NavNode,
        discover_markdown_files,
        build_nav_tree,
        render_sidebar_html,
        build_breadcrumbs,
        load_title_from_markdown
    )


# Type alias for log function
UILog = Any


def convert_markdown_to_html(md_text: str) -> str:
    """Convert Markdown text to HTML using Python-Markdown."""
    return markdown.markdown(md_text, extensions=["extra", "toc", "sane_lists"])


def strip_html(html: str) -> str:
    """Remove HTML tags and collapse whitespace for search index content."""
    # Remove tags
    text = re.sub(r"<[^>]+>", " ", html)
    # Unescape basic entities
    text = text.replace("&nbsp;", " ")
    text = text.replace("&", "&")
    text = text.replace("<", "<")
    text = text.replace(">", ">")
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def load_template(theme_path: Path, assets_dir: Path = None) -> Template:
    """Load a Jinja2 template from a file path, with loader if assets_dir provided."""
    if assets_dir:
        loader = FileSystemLoader(assets_dir)
        env = Environment(loader=loader)
        return env.get_template(theme_path.name)
    else:
        return Template(theme_path.read_text(encoding="utf-8"))


def copy_assets(site_root: Path, output_root: Path) -> None:
    """Copy specific assets to output root: JS/CSS files referenced by templates.

    - Ensures gallery.css, gallery.js, common.js are placed in the output ROOT.
    - Falls back to repository defaults if the site doesn't provide them.
    """
    try:
        REPO_ROOT = Path(__file__).resolve().parent
        repo_assets = REPO_ROOT / "assets"
        src = site_root / "assets"
        for fname in ("gallery.css", "gallery.js", "common.js"):
            site_assets_file = src / fname                    # e.g., site_root/assets/blog.html
            target_root = output_root / fname                 # output/blog.html

            if site_assets_file.exists():
                shutil.copyfile(site_assets_file, target_root)
            elif (repo_assets / fname).exists():
                repo_file = repo_assets / fname
                shutil.copyfile(repo_file, target_root)
    except Exception:
        pass


def copy_non_markdown_files(content_root: Path, output_root: Path, log: Optional[UILog] = None) -> None:
    """Copy all non-Markdown files from content_root to output_root, preserving structure."""
    def info(msg: str) -> None:
        if log is not None:
            log.write(msg)
        else:
            print(msg)

    for src_file in content_root.rglob("*"):
        if src_file.is_file() and src_file.suffix.lower() != ".md":
            rel_path = src_file.relative_to(content_root)
            dst_file = output_root / rel_path
            dst_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src_file, dst_file)
            info(f"Copied static file: {rel_path}")


# Supported image extensions for galleries
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}


def _gather_gallery_items(
    content_root: Path,
    gallery_dir: Path,
    output_root: Path,
    thumb_max_side: int,
    log: Optional[UILog] = None,
) -> list[dict[str, Any]]:
    """Prepare gallery items and generate thumbnails.

    Returns list of dicts with keys: full (Path), thumb (Path), alt (str)
    Paths are absolute paths under output_root.
    """
    def info(msg: str) -> None:
        if log is not None:
            log.write(msg)
        else:
            print(msg)

    items: list[dict[str, Path]] = []
    if not gallery_dir.exists() or not gallery_dir.is_dir():
        return items

    warned_no_pillow = False

    MAX_GALLERY_ITEMS = 1000
    gallery_files = list(sorted(gallery_dir.iterdir()))[:MAX_GALLERY_ITEMS]
    for src_file in gallery_files:
        if not src_file.is_file():
            continue
        ext = src_file.suffix.lower()
        if ext not in IMAGE_EXTS:
            continue
        # Output path for original (already copied by copy_non_markdown_files)
        try:
            rel_from_content = src_file.relative_to(content_root)
        except Exception:
            # If relative fails, skip the file
            continue
        full_out = output_root / rel_from_content
        # Thumbnail path: sibling directory "_thumbs"
        thumbs_dir = full_out.parent / "_thumbs"
        thumbs_dir.mkdir(parents=True, exist_ok=True)
        thumb_out = thumbs_dir / src_file.name

        # Create/refresh thumbnail if Pillow available
        if Image is None:
            if not warned_no_pillow:
                info("[Gallery] Pillow not installed: thumbnails will use original images.")
                warned_no_pillow = True
            thumb_out = full_out
        else:
            try:
                # Regenerate if missing or source is newer
                if (not thumb_out.exists()) or (src_file.stat().st_mtime > thumb_out.stat().st_mtime):
                    with Image.open(src_file) as im:
                        im = im.convert("RGB") if ext in {".jpg", ".jpeg"} else im
                        # Auto-orient via EXIF
                        try:
                            if ImageOps is not None:
                                im = ImageOps.exif_transpose(im)
                        except Exception:
                            pass
                        # Create square center-cropped thumbnail to avoid letterboxing
                        target = (thumb_max_side, thumb_max_side)
                        try:
                            im_thumb = ImageOps.fit(im, target, method=getattr(Image, "LANCZOS", Image.BICUBIC), centering=(0.5, 0.5))
                        except Exception:
                            # Fallback: preserve aspect ratio thumbnail (may cause bands in CSS-only layouts)
                            im_thumb = im.copy()
                            im_thumb.thumbnail(target)
                        save_kwargs = {}
                        if ext in {".jpg", ".jpeg"}:
                            save_kwargs = {"quality": 85, "optimize": True}
                            thumb_out = thumb_out.with_suffix(".jpg")  # normalize extension
                        im_thumb.save(thumb_out, **save_kwargs)
                        info(f"[Gallery] Thumbnail created: {thumb_out.relative_to(output_root)}")
            except Exception as e:
                info(f"[Gallery] Error creating thumbnail for {src_file.name}: {e}")
                thumb_out = full_out

        alt_text = src_file.stem.replace("_", " ").replace("-", " ")
        items.append({"full": full_out, "thumb": thumb_out, "alt": alt_text})

    return items


def _render_gallery_html(
    items: list[dict[str, Path]],
    current_out_dir: Path,
    assets_root: Path,
    gallery_id: str,
    gallery_template: Template,
) -> str:
    """Build gallery HTML (grid + modal) using external gallery.html template."""
    if not items:
        return ""

    # Compute relative URLs
    def href(p: Path) -> str:
        try:
            rel = os.path.relpath(p, start=current_out_dir)
        except Exception:
            rel = p.name
        return rel.replace(os.sep, "/")

    cards = "\n".join(
        [
            (
                f'<a class="gallery-item" href="#" data-full="{href(it["full"])}" data-alt="{it["alt"]}">'
                f'<img src="{href(it["thumb"])}" alt="{it["alt"]}" loading="lazy" />'
                f"</a>"
            )
            for it in items
        ]
    )

    # Resolve gallery asset URLs relative to the current output file
    assets_css = href(assets_root / "gallery.css")
    assets_js = href(assets_root / "gallery.js")

    # Render using external template
    html = gallery_template.render(
        id=gallery_id,
        css_href=assets_css,
        js_href=assets_js,
        cards=cards,
    )
    return html


def _gather_gallery_subtree(
    content_root: Path,
    current_content_dir: Path,
    output_root: Path,
    assets_root: Path,
    thumb_max_side: int,
    gallery_template: Template,
    current_out_dir: Path,
    log: Optional[UILog] = None,
) -> str:
    """Gather all _gallery directories in the subtree of current_content_dir that lack index.md, and render them all into HTML."""
    galleries_html = []
    gallery_id_counter = 0

    # Find immediate _gallery dir only
    gallery_dir = current_content_dir / "_gallery"
    if gallery_dir.is_dir() and not (gallery_dir / "index.md").exists():
        try:
            items = _gather_gallery_items(content_root, gallery_dir, output_root, thumb_max_side, log=log)
            if items:
                gallery_id = f"gallery-subtree-{gallery_id_counter}"
                gallery_id_counter += 1
                html = _render_gallery_html(
                    items,
                    current_out_dir,
                    assets_root,
                    gallery_id,
                    gallery_template,
                )
                if html:
                    galleries_html.append(html)
        except Exception as e:
            if log is not None:
                log.write(f"[Gallery] Error gathering gallery in {gallery_dir}: {e}")

    return "\n\n".join(galleries_html)


def _gather_files_items(
    content_root: Path,
    files_dir: Path,
    log: Optional[UILog] = None,
) -> list[dict[str, str]]:
    """Prepare files list items.

    Returns list of dicts with keys: name, size, date, href
    """
    def info(msg: str) -> None:
        if log is not None:
            log.write(msg)
        else:
            print(msg)

    items: list[dict[str, str]] = []
    if not files_dir.exists() or not files_dir.is_dir():
        return items

    MAX_FILES_ITEMS = 1000
    files_list = list(sorted(files_dir.iterdir()))[:MAX_FILES_ITEMS]
    for src_file in files_list:
        if not src_file.is_file():
            continue
        ext = src_file.suffix.lower()
        if ext in {".html", ".md"}:
            continue
        # Get file info
        stat = src_file.stat()
        size_bytes = stat.st_size
        if size_bytes < 1024:
            size_str = f"{size_bytes} B"
        elif size_bytes < 1024**2:
            size_str = f"{size_bytes / 1024:.1f} KB"
        else:
            size_str = f"{size_bytes / (1024**2):.1f} MB"
        # Date
        date_str = time.strftime("%Y-%m-%d %H:%M", time.localtime(stat.st_mtime))
        # Href
        try:
            rel_from_content = src_file.relative_to(content_root)
        except Exception:
            continue
        href = rel_from_content.as_posix()
        items.append({
            "name": src_file.name,
            "size": size_str,
            "date": date_str,
            "href": href,
        })

    return items


def _render_files_html(
    items: list[dict[str, str]],
    current_out_dir: Path,
    output_root: Path,
    files_template: Template,
) -> str:
    """Build files list HTML (table) using external files.html template."""
    if not items:
        return ""

    # Compute relative URLs
    def rel_href(p: str) -> str:
        full_p = output_root / p
        return os.path.relpath(full_p, start=current_out_dir).replace(os.sep, "/")

    name_header = translate("files_name")
    size_header = translate("files_size")
    date_header = translate("files_date")
    download_header = translate("files_download")

    rows = "\n".join(
        f'<tr><td>{it["name"]}</td><td>{it["size"]}</td><td>{it["date"]}</td><td><a href="{rel_href(it["href"])}" download>{download_header}</a></td></tr>'
        for it in items
    )

    # Render using external template
    html = files_template.render(
        name_header=name_header,
        size_header=size_header,
        date_header=date_header,
        download_header=download_header,
        rows=rows,
    )
    return html


def _gather_blog_posts(
    blog_dir: Path,
    log: Optional[UILog] = None,
) -> List[Tuple[Path, str, str, Optional[str]]]:
    """Collect and sort blog posts from a _blog directory.

    Returns list of (md_file_path, title, body_html, date_str) tuples sorted chronologically.
    """
    posts = []
    for md_file in blog_dir.glob("*.md"):
        if md_file.is_file() and md_file.name != "index.md":  # Skip index.md as it's used for blog intro
            try:
                post = frontmatter.load(md_file)
                # Skip draft posts
                if post.metadata.get("draft"):
                    continue
                title = post.metadata.get("title") or md_file.stem.replace("_", " ").replace("-", " ")
                date = post.metadata.get("date")
                body_md = post.content
                body_html = convert_markdown_to_html(body_md)
                posts.append((md_file, title, body_html, date))
            except Exception as e:
                if log is not None:
                    log.write(f"[Blog] Error processing {md_file.name}: {e}")

    # Sort by date (frontmatter or mtime), most recent first
    def sort_key(p: Tuple[Path, str, str, Optional[str]]):
        import time
        from datetime import datetime, date

        post_date = p[3]
        if post_date:
            try:
                # Handle different date formats
                if isinstance(post_date, str):
                    # Try to convert string to datetime
                    return datetime.fromisoformat(post_date.replace('Z', '+00:00')).timestamp()
                elif isinstance(post_date, (datetime, date)):
                    # Convert date/datetime objects to timestamp
                    if isinstance(post_date, date) and not isinstance(post_date, datetime):
                        return datetime.combine(post_date, datetime.min.time()).timestamp()
                    return post_date.timestamp()
            except Exception:
                pass
        # Use file modification time as fallback
        return p[0].stat().st_mtime

    posts.sort(key=sort_key, reverse=True)
    return posts


def _render_blog_html(
    posts: List[Tuple[Path, str, str, Optional[str]]],
) -> str:
    """Render combined HTML for all blog posts using card-style article elements."""
    if not posts:
        return ""

    articles = []
    for md_file, title, body_html, date in posts:
        date_meta = f'<p class="meta">{date}</p>' if date else ""
        article_html = f"""
<div class="blog-card">
    <article class="blog-post">
        <header class="blog-post-header">
            <h2 class="blog-post-title">{title}</h2>
            {date_meta}
        </header>
        <div class="blog-post-content markdown-body">
            {body_html}
        </div>
    </article>
</div>
""".strip()
        articles.append(article_html)

    return "\n\n".join(articles)


def generate_sitemap_xml(base_url: Optional[str], output_root: Path, search_items: list[dict[str, Any]], log: Optional[UILog] = None) -> None:
    """Generate XML sitemap at output_root/sitemap.xml.

    Args:
        base_url: Base URL of the site (e.g., "https://example.com"). If None, sitemap is not generated.
        output_root: Output directory root.
        search_items: List of search index items with 'url' and optional 'date'.
        log: Optional log function.
    """
    def info(msg: str) -> None:
        if log is not None:
            log.write(msg)
        else:
            print(msg)

    if base_url is None:
        info("[Sitemap] Not generating sitemap.xml because base_url is not configured in config.toml")
        return

    from datetime import datetime

    xml_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
    ]

    for item in search_items:
        url = item["url"]
        loc = f"{base_url.rstrip('/')}/{url.lstrip('/')}"
        lastmod = item.get("date")
        if lastmod:
            # Try to format date, fallback to today if invalid
            try:
                if isinstance(lastmod, str):
                    # Assume ISO format like "2023-09-19" or "2023-09-19T12:00:00"
                    if 'T' in lastmod:
                        lastmod = lastmod.split('T')[0]
                    elif lastmod.count('-') == 2 and len(lastmod) == 10:
                        pass  # already YYYY-MM-DD
                    else:
                        raise ValueError
                else:
                    lastmod = datetime.now().date().isoformat()
            except ValueError:
                lastmod = datetime.now().date().isoformat()
        else:
            lastmod = datetime.now().date().isoformat()

        url_element = f" <url>\n  <loc>{loc}</loc>\n  <lastmod>{lastmod}</lastmod>\n </url>"
        xml_lines.append(url_element)

    xml_lines.append('</urlset>')

    sitemap_path = output_root / "sitemap.xml"
    sitemap_content = "\n".join(xml_lines)
    sitemap_path.write_text(sitemap_content, encoding="utf-8")
    info(f"[Sitemap] Generated: {sitemap_path.relative_to(output_root)}")


def _detect_languages(site_root: Path) -> tuple[bool, list[str]]:
    """Detect if site is multilingual based on content folder structure.

    Returns (is_multilingual, detected_languages).
    Multilingual if content/ contains only folders matching language pattern,
    and no other files/folders.

    Language pattern: /^[a-z]{2}(_[A-Z]{2})?$/ (e.g., "en", "it", "it_IT")
    """
    content_dir = site_root / "content"
    if not content_dir.exists():
        return False, []

    lang_pattern = re.compile(r'^[a-z]{2}(_[A-Z]{2})?$')
    all_entries = list(content_dir.iterdir())
    detected_langs = []

    for entry in all_entries:
        if entry.is_dir():
            if lang_pattern.match(entry.name):
                # Handle cases like "en_US" -> normalize to "en"
                lang = entry.name.split('_')[0].lower()
                detected_langs.append(lang)
            else:
                # Non-language folder found, site is monolingual
                return False, []

    # Check for any files (monolingual if files present)
    if any(e.is_file() for e in all_entries):
        return False, []

    return bool(detected_langs and len(detected_langs) > 1), detected_langs


def generate_site(site_root: Path, log: Optional[UILog] = None) -> None:
    """Generate the static HTML site from a project directory.

    Reads config.toml, builds navigation and breadcrumbs, renders Markdown via
    Jinja2 theme to HTML, writes a search-index.json, and copies assets.

    Args:
        site_root: Path to the site project root.
        log: Optional log widget to report progress in the TUI.
    """
    def info(msg: str) -> None:
        if log is not None:
            log.write(msg)
        else:
            print(msg)

    cfg = read_config(site_root)
    info("Loaded config.toml")

    # Detect if multilingual based on content structure
    is_multilingual, detected_langs = _detect_languages(site_root)
    if is_multilingual:
        cfg.languages = detected_langs
        if cfg.default_language not in cfg.languages:
            cfg.default_language = cfg.languages[0]
        info(f"Detected multilingual site with languages: {cfg.languages}")
    else:
        cfg.languages = [cfg.default_language]  # Monolingual
        info("Detected monolingual site, ignoring language settings")

    # Clean root output directory before generation
    output_root = sanitize_path(cfg.output, site_root, site_root)
    if output_root.exists():
        try:
            shutil.rmtree(output_root)
            info(f"Cleaned output directory: {output_root}")
        except Exception as e:
            info(f"Warning: failed to clean output directory {output_root}: {e}")
    output_root.mkdir(parents=True, exist_ok=True)

    # Copy shared assets to root
    copy_assets(site_root, output_root)
    # Copy theme CSS to root if available
    try:
        css_src = sanitize_path(cfg.theme_css, site_root, site_root)
        if css_src.exists():
            css_dst = output_root / css_src.name
            shutil.copyfile(css_src, css_dst)
            info("Copied theme.css for root")
    except Exception:
        pass

    # Generate for each language
    for lang in cfg.languages:
        set_global_language(lang)
        info(f"Generating site for language: {lang}")

        # Language-specific content and output directories
        content_root = site_root / "content"
        if len(cfg.languages) > 1:
            content_root = content_root / lang
            if not content_root.exists():
                info(f"Content directory not found for language {lang}: {content_root}")
                continue
        # For monolingual, content_root is site_root / "content"

        lang_output_root = output_root / lang if len(cfg.languages) > 1 else output_root
        lang_output_root.mkdir(parents=True, exist_ok=True)

        # Generate site for this language
        _generate_site_for_language(site_root, content_root, lang_output_root, cfg, lang, is_multilingual, log=log)

    # If multilingual, generate root redirect to default language
    if is_multilingual:
        # Create root index.html as redirect page to default language
        redirect_url = f"{cfg.default_language}/"
        root_index_html = f"""<!DOCTYPE html>
<html lang="{cfg.default_language}">
<head>
    <meta charset="utf-8">
    <meta http-equiv="refresh" content="0; url={redirect_url}">
    <title>Redirecting...</title>
</head>
<body>
    <p>Redirecting to default language version...</p>
    <p><a href="{redirect_url}">Click here if not redirected</a></p>
</body>
</html>"""
        root_index_path = output_root / "index.html"
        root_index_path.write_text(root_index_html, encoding="utf-8")
        info(f"Generated root redirect to {redirect_url}")
        # Copy assets for root
        copy_assets(site_root, output_root)
        # Copy theme CSS for root
        css_src = site_root / "assets" / cfg.theme_css
        if css_src.exists():
            shutil.copyfile(css_src, output_root / "theme.css")
            info("Copied theme.css for root redirect")
    else:
        # Monolingual, already generated at root
        pass


def _generate_site_for_language(site_root: Path, content_root: Path, output_root: Path, cfg: SiteConfig, lang: str, is_multilingual: bool, log: Optional[UILog] = None) -> None:
    """Generate the static HTML site for a single language.

    Args:
        site_root: Path to the site project root.
        content_root: Path to the content directory for this language.
        output_root: Path to the output directory for this language.
        cfg: SiteConfig instance.
        log: Optional log widget to report progress in the TUI.
    """
    def info(msg: str) -> None:
        if log is not None:
            log.write(msg)
        else:
            print(msg)

    # Determine root output for multilingual sites
    root_output = output_root.parent if is_multilingual else output_root
    assets_root = root_output

    # Load theme template. Prefer site-local theme; else fall back to repo root theme.
    REPO_ROOT = Path(__file__).resolve().parent  # Adjusted to parent for assets path
    try:
        theme_path = sanitize_path(cfg.base_theme, site_root, site_root)
    except ValueError:
        # Attempt fallback to repo assets using only the filename to prevent traversal
        fallback_name = Path(cfg.base_theme).name
        try:
            theme_path = sanitize_path(fallback_name, REPO_ROOT / "assets", REPO_ROOT / "assets")
        except ValueError:
            raise FileNotFoundError(f"Theme not found and fallback invalid: {cfg.base_theme}")
    if not theme_path.exists():
        raise FileNotFoundError(f"Theme not found: {cfg.base_theme}")
    assets_dir = site_root / "assets"
    template = load_template(theme_path, assets_dir)

    # Load blog template if available. Use site assets first, fallback to repo assets
    blog_template_path = site_root / "assets" / "blog_theme.html"
    if not blog_template_path.exists():
        blog_template_path = REPO_ROOT / "assets" / "blog.html"  # Repo fallback
    if blog_template_path.exists():
        in_site = blog_template_path.parent == assets_dir
        blog_template = load_template(blog_template_path, assets_dir if in_site else None)
        info("[Blog] Using blog-specific template")
    else:
        blog_template = template  # Fallback to main theme template if blog template not found
        info("[Blog] Using fallback template")

    # Load gallery theme for gallery pages
    gallery_theme_path = site_root / "assets" / "gallery_theme.html"
    if gallery_theme_path.exists():
        in_site = gallery_theme_path.parent == assets_dir
        gallery_theme = load_template(gallery_theme_path, assets_dir if in_site else None)
        info("[Gallery] Using gallery-specific template")
    else:
        gallery_theme = template  # Fallback to main theme template
        info("[Gallery] Using fallback template")

    # CSS is copied to root_output
    try:
        css_src = sanitize_path(cfg.theme_css, site_root, site_root)
    except ValueError:
        # Attempt fallback to repo assets using only the filename to prevent traversal
        fallback_name = Path(cfg.theme_css).name
        try:
            css_src = sanitize_path(fallback_name, REPO_ROOT / "assets", REPO_ROOT / "assets")
        except ValueError:
            raise FileNotFoundError(f"Theme CSS not found and fallback invalid: {cfg.theme_css}")
    if not css_src.exists():
        raise FileNotFoundError(f"Theme CSS not found: {cfg.theme_css}")
    css_dst = assets_root / css_src.name

    # Copy non-markdown files
    copy_non_markdown_files(content_root, output_root, log)

    # Collect markdown files to render
    md_files = discover_markdown_files(content_root)

    # Add generated special pages to md_files for navigation
    special_generated = []
    for special_dir in content_root.rglob("*"):
        if special_dir.is_dir() and special_dir.name in {"_files", "_gallery", "_blog"}:
            if not (special_dir / "index.md").exists():
                rel_special = special_dir.relative_to(content_root)
                output_special_html = output_root / rel_special / "index.html"
                if output_special_html.exists():
                    # Create fake md path for nav
                    fake_md = special_dir / "index.md"
                    special_generated.append(fake_md)
    md_files.extend(special_generated)
    info(f"Discovered {len(md_files)} files (including generated special pages)")

    # Collect data for search index
    search_items: list[dict[str, Any]] = []

    # Track blog folders that have been processed
    processed_blog_folders = set()

    # Load templates for special directories
    files_template_path = site_root / "assets" / "files.html"
    if not files_template_path.exists():
        files_template_path = REPO_ROOT / "assets" / "files.html"
    files_template = load_template(files_template_path)
    info("[Files] Loaded files template")

    gallery_template_path = site_root / "assets" / "gallery.html"
    if not gallery_template_path.exists():
        gallery_template_path = REPO_ROOT / "assets" / "gallery.html"
    gallery_component_template = load_template(gallery_template_path)
    info("[Gallery] Loaded gallery component template")

    # Build nav tree
    nav_root = build_nav_tree(content_root, output_root)

    # Generate pages for special directories without index.md
    for special_dir in content_root.rglob("*"):
        if special_dir.name == "_gallery":
            continue  # Skip generating separate pages for _gallery without index.md per requirement
        if not special_dir.is_dir() or special_dir.name not in {"_files", "_gallery", "_blog"}:
            continue

        index_md = special_dir / "index.md"
        if index_md.exists():
            continue  # Skip if index.md exists

        # Check if special directory should be appended to parent instead of having its own page
        parent_index_md = special_dir.parent / "index.md"
        if special_dir.parent != content_root and parent_index_md.exists():
            continue  # Skip generating, will append to parent

        rel_special_dir = special_dir.relative_to(content_root)
        output_dir = output_root / rel_special_dir
        output_dir.mkdir(parents=True, exist_ok=True)
        out_path = output_dir / "index.html"

        breadcrumbs = build_breadcrumbs(content_root, output_root, Path(str(rel_special_dir) + "/index.md"), output_dir, is_multilingual, root_output)
        sidebar_html = render_sidebar_html(nav_root, output_dir, output_root, out_path.relative_to(output_root))
        css_url = os.path.relpath(css_dst, start=output_dir).replace(os.sep, "/")
        common_js_url = os.path.relpath(root_output / "common.js", start=output_dir).replace(os.sep, "/")

        special_html = ""
        title = ""
        current_template = template

        if special_dir.name == "_files":
            # Check if has non-md/html files
            has_files = any(
                f.is_file() and f.suffix.lower() not in {".md", ".html"}
                for f in special_dir.iterdir()
            )
            if has_files:
                items = _gather_files_items(content_root, special_dir, log=log)
                if items:
                    special_html = _render_files_html(items, output_dir, output_root, files_template)
                    title = translate("files_title")
                else:
                    continue
            else:
                continue
        elif special_dir.name == "_gallery":
            # Check if has images
            has_images = any(
                f.is_file() and f.suffix.lower() in IMAGE_EXTS
                for f in special_dir.iterdir()
            )
            if has_images:
                items = _gather_gallery_items(content_root, special_dir, output_root, thumb_max_side=400, log=log)
                if items:
                    special_html = _render_gallery_html(
                        items,
                        output_dir,
                        assets_root,
                        gallery_id=f"gallery-{rel_special_dir.as_posix().replace('/', '-')}",
                        gallery_template=gallery_component_template,
                    )
                    title = translate("gallery_title")
                    current_template = gallery_theme if gallery_theme_path.exists() else template
                else:
                    continue
            else:
                continue
        elif special_dir.name == "_blog":
            # Check if has md files != index.md
            has_posts = any(
                f.is_file() and f.suffix.lower() == ".md" and f.name != "index.md"
                for f in special_dir.iterdir()
            )
            if has_posts:
                posts = _gather_blog_posts(special_dir, log=log)
                if posts:
                    special_html = _render_blog_html(posts)  # blog_intro_html empty since no index.md
                    title = translate("blog_title")
                    current_template = blog_template if blog_template.exists() else template
                else:
                    continue
            else:
                continue

        if special_html:
            html = current_template.render(
                site_name=cfg.site_name,
                author=cfg.author,
                footer=cfg.footer,
                page_title=title,
                page_date=None,
                content_html=special_html,
                breadcrumbs=breadcrumbs,
                sidebar_html=sidebar_html,
                theme_css_url=css_url,
                common_js_url=common_js_url,
                is_multilingual=is_multilingual,
                current_lang=lang,
                languages=cfg.languages,
            )
            out_path.write_text(html, encoding="utf-8")
            info(f"[{special_dir.name[1:].capitalize()}] Generated: {out_path.relative_to(output_root)}")
            # Add to search
            search_items.append({
                "title": title,
                "url": out_path.relative_to(output_root).as_posix(),
                "date": None,
                "content": strip_html(special_html),
            })

    # Build nav tree
    nav_root = build_nav_tree(content_root, output_root)

    for md_file in md_files:
        rel_md = md_file.relative_to(content_root)

        # Skip 404.md files as 404.html will be generated separately
        if rel_md.name == "404.md":
            continue

        # Check if this file is inside a _blog directory
        blog_folder = None
        for part in reversed(rel_md.parts):
            if part == "_blog":
                blog_folder = md_file.parent
                break

        if blog_folder:
            # Skip processing individual files in blog folders, they'll be handled as a group
            if blog_folder not in processed_blog_folders:
                processed_blog_folders.add(blog_folder)
                # Process the blog folder
                try:
                    posts = _gather_blog_posts(blog_folder, log)
                    blog_html = _render_blog_html(posts)

                    # Determine the output path for the blog page
                    blog_rel_path = rel_md.parent / "index.html"

                    # Check if there's an index.md file in the blog folder
                    index_md_path = blog_folder / "index.md"
                    blog_intro_html = ""
                    if index_md_path.exists():
                        try:
                            index_post = frontmatter.load(index_md_path)
                            # Skip draft blog index
                            if index_post.metadata.get("draft"):
                                blog_title = md_file.parent.name.replace("_", " ").replace("-", " ") or "Blog"
                            else:
                                blog_title_from_md, _ = load_title_from_markdown(index_md_path)
                                blog_title = index_post.metadata.get("title") or blog_title_from_md or "Blog"
                                index_content_md = index_post.content.strip()
                                if index_content_md:
                                    blog_intro_html = convert_markdown_to_html(index_content_md)
                        except Exception:
                            blog_title = md_file.parent.name.replace("_", " ").replace("-", " ") or "Blog"
                    else:
                        blog_title = md_file.parent.name.replace("_", " ").replace("-", " ") or "Blog"

                    # Combine intro content with blog posts
                    if blog_intro_html:
                        blog_body_html = f"{blog_intro_html}\n\n{blog_html}" if posts else blog_intro_html
                    else:
                        blog_body_html = blog_html if posts else "No blog posts found."

                    out_path = output_root / blog_rel_path
                    out_path.parent.mkdir(parents=True, exist_ok=True)

                    # Build breadcrumbs and sidebar for blog page
                    current_out_dir = out_path.parent
                    breadcrumbs = build_breadcrumbs(content_root, output_root, blog_rel_path.with_suffix(".md"), current_out_dir, is_multilingual, root_output)
                    sidebar_html = render_sidebar_html(nav_root, current_out_dir, output_root, blog_rel_path, is_multilingual, root_output)

                    # Compute CSS URL and JS URL
                    try:
                        css_url = os.path.relpath(css_dst, start=current_out_dir).replace(os.sep, "/")
                    except Exception:
                        css_url = css_dst.name

                    # Compute common.js URL relative to the output file
                    common_js_dst = output_root / "common.js"
                    try:
                        common_js_url = os.path.relpath(common_js_dst, start=current_out_dir).replace(os.sep, "/")
                    except Exception:
                        common_js_url = common_js_dst.name

    # Blog content is ready

                    # Render blog page HTML using blog template
                    html = blog_template.render(
                        site_name=cfg.site_name,
                        author=cfg.author,
                        footer=cfg.footer,
                        page_title=blog_title,
                        page_date=None,
                        content_html=blog_intro_html,
                        blog_posts=blog_html,
                        breadcrumbs=breadcrumbs,
                        sidebar_html=sidebar_html,
                        theme_css_url=css_url,
                        common_js_url=common_js_url,
                        is_multilingual=is_multilingual,
                        current_lang=lang,
                        languages=cfg.languages,
                    )
                    info("[Blog] Successfully rendered using blog template")

                    out_path.write_text(html, encoding="utf-8")
                    info(f"Rendered blog: {blog_rel_path}")

                    # Add blog page to search index
                    search_items.append({
                        "title": blog_title,
                        "url": blog_rel_path.as_posix(),
                        "date": None,
                        "content": strip_html(blog_body_html),
                    })

                    # Add individual blog posts to search index
                    for post_md_file, post_title, post_html, post_date in posts:
                        post_url = blog_rel_path.as_posix()
                        search_items.append({
                            "title": post_title,
                            "url": post_url,
                            "date": str(post_date) if post_date else None,
                            "content": strip_html(post_html),
                        })

                except Exception as e:
                    info(f"[Blog] Error processing blog folder {blog_folder}: {e}")
            continue  # Skip this md_file since we processed the whole blog folder

        # Regular file processing (non-blog)
        out_rel = rel_md.with_suffix(".html")
        out_path = output_root / out_rel
        out_path.parent.mkdir(parents=True, exist_ok=True)

        # Parse frontmatter and content
        post = frontmatter.load(md_file)
        # Skip draft pages
        if post.metadata.get("draft"):
            continue
        title = post.metadata.get("title") or md_file.stem.replace("_", " ").replace("-", " ")
        date = post.metadata.get("date")
        body_md = post.content

        # Convert markdown to HTML
        body_html = convert_markdown_to_html(body_md)

        # Gallery rendering logic - handles different gallery placement scenarios
        # 1) If this page is _gallery/index.md, render the gallery here (preferred)
        if md_file.name.lower() == "index.md" and md_file.parent.name == "_gallery":
            try:
                gallery_dir = md_file.parent
                items = _gather_gallery_items(content_root, gallery_dir, output_root, thumb_max_side=400, log=log)
                # Load gallery component template (use site assets, fallback to repo assets)
                REPO_ROOT = Path(__file__).resolve().parent
                tpl_path = site_root / "assets" / "gallery.html"
                if not tpl_path.exists():
                    tpl_path = REPO_ROOT / "assets" / "gallery.html"
                gallery_template = load_template(tpl_path)
                gallery_html = _render_gallery_html(
                    items,
                    current_out_dir=out_path.parent,
                    assets_root=root_output,
                    gallery_id=f"gallery-{rel_md.parent.as_posix().replace('/', '-') or 'root'}",
                    gallery_template=gallery_template,
                )
                # Replace the page content with gallery HTML for dedicated gallery pages
                if gallery_html:
                    body_html = gallery_html
                    info(f"[Gallery] Gallery rendered in: {rel_md}")
            except Exception as e:
                info(f"[Gallery] Error generating gallery for {rel_md}: {e}")
        # Append galleries from subtree without index.md
        elif md_file.name.lower() == "index.md":
            try:
                current_content_dir = md_file.parent
                gallery_html = _gather_gallery_subtree(
                    content_root,
                    current_content_dir,
                    output_root,
                    assets_root,
                    thumb_max_side=400,
                    gallery_template=gallery_component_template,
                    current_out_dir=out_path.parent,
                    log=log,
                )
                # Append gallery HTML after the main page content
                if gallery_html:
                    body_html = f"{body_html}\n\n{gallery_html}"
                    info(f"[Gallery] Galleries appended to {rel_md.parent or Path('.')} from subtree")
            except Exception as e:
                info(f"[Gallery] Error generating galleries for {rel_md}: {e}")

        # Files rendering logic - handles different files list placement scenarios
        # 1) If this page is _files/index.md, render the files list here (preferred)
        if md_file.name.lower() == "index.md" and md_file.parent.name == "_files":
            try:
                files_dir = md_file.parent
                items = _gather_files_items(content_root, files_dir, log=log)
                # Load files component template (use site assets, fallback to repo assets)
                REPO_ROOT = Path(__file__).resolve().parent
                tpl_path = site_root / "assets" / "files.html"
                if not tpl_path.exists():
                    tpl_path = REPO_ROOT / "assets" / "files.html"
                files_template = load_template(tpl_path)
                files_html = _render_files_html(
                    items,
                    current_out_dir=out_path.parent,
                    output_root=output_root,
                    files_template=files_template,
                )
                # Replace the page content with files HTML for dedicated files pages
                if files_html:
                    body_html = files_html
                    info(f"[Files] Files list rendered in: {rel_md}")
            except Exception as e:
                info(f"[Files] Error generating files for {rel_md}: {e}")
        # 2) Otherwise, if this is a parent index.md and a sibling _files exists WITHOUT its own index.md,
        #    append the files list to the parent page.
        elif md_file.name.lower() == "index.md":
            files_dir = md_file.parent / "_files"
            if files_dir.exists() and files_dir.is_dir() and not (files_dir / "index.md").exists():
                try:
                    items = _gather_files_items(content_root, files_dir, log=log)
                    # Load files component template (use site assets, fallback to repo assets)
                    REPO_ROOT = Path(__file__).resolve().parent
                    tpl_path = site_root / "assets" / "files.html"
                    if not tpl_path.exists():
                        tpl_path = REPO_ROOT / "assets" / "files.html"
                    files_template = load_template(tpl_path)
                    files_html = _render_files_html(
                        items,
                        current_out_dir=out_path.parent,
                        output_root=output_root,
                        files_template=files_template,
                    )
                    # Append files HTML after the main page content
                    if files_html:
                        body_html = f"{body_html}\n\n{files_html}"
                        info(f"[Files] Files list appended to parent: {rel_md.parent or Path('.')}")
                except Exception as e:
                    info(f"[Files] Error generating files for {rel_md}: {e}")

        # Blog rendering logic - append if sibling _blog exists without index.md
        elif md_file.name.lower() == "index.md":
            blog_dir = md_file.parent / "_blog"
            if blog_dir.exists() and blog_dir.is_dir() and not (blog_dir / "index.md").exists():
                try:
                    has_posts = any(
                        f.is_file() and f.suffix.lower() == ".md" and f.name != "index.md"
                        for f in blog_dir.iterdir()
                    )
                    if has_posts:
                        posts = _gather_blog_posts(blog_dir, log=log)
                        blog_html = _render_blog_html(posts)
                        if blog_html:
                            body_html = f"{body_html}\n\n{blog_html}"
                            info(f"[Blog] Blog appended to parent: {rel_md.parent or Path('.')}")

                except Exception as e:
                    info(f"[Blog] Error generating blog for {rel_md}: {e}")

        # Use default template
        current_template = template

        # Override template for special content types
        if "_gallery" in str(rel_md):
            current_template = gallery_theme

        # Build breadcrumbs (relative to this file's directory)
        current_out_dir = out_path.parent
        breadcrumbs = build_breadcrumbs(content_root, output_root, rel_md, current_out_dir, is_multilingual, root_output)

        # Sidebar HTML (links relative to this file)
        sidebar_html = render_sidebar_html(nav_root, current_out_dir, output_root, out_rel, is_multilingual, root_output)

        # Compute CSS URL and JS URL relative to the output file
        try:
            css_url = os.path.relpath(css_dst, start=out_path.parent).replace(os.sep, "/")
        except Exception:
            css_url = css_dst.name

        # Compute common.js URL relative to the output file
        common_js_dst = output_root / "common.js"
        try:
            common_js_url = os.path.relpath(common_js_dst, start=out_path.parent).replace(os.sep, "/")
        except Exception:
            common_js_url = common_js_dst.name

        # Render final HTML
        html = current_template.render(
            site_name=cfg.site_name,
            author=cfg.author,
            footer=cfg.footer,
            page_title=title,
            page_date=str(date) if date else None,
            content_html=body_html,
            breadcrumbs=breadcrumbs,
            sidebar_html=sidebar_html,
            theme_css_url=css_url,
            common_js_url=common_js_url,
            is_multilingual=is_multilingual,
            current_lang=lang,
            languages=cfg.languages,
        )

        out_path.write_text(html, encoding="utf-8")
        info(f"Rendered: {out_rel}")

        # Add to search index
        page_url = out_rel.as_posix()
        search_items.append({
            "title": title,
            "url": page_url,
            "date": str(date) if date else None,
            "content": strip_html(body_html),
        })

    # Write search index JSON
    search_path = output_root / "search-index.json"
    search_path.write_text(json.dumps(search_items, ensure_ascii=False, indent=2), encoding="utf-8")
    info(f"Search index written: {search_path.relative_to(output_root)}")

    # Generate 404.html always in output root using 404 template
    tpl_path = site_root / "assets" / "404.html"
    if not tpl_path.exists():
        tpl_path = REPO_ROOT / "assets" / "404.html"
    if tpl_path.exists():
        in_site = tpl_path.parent == assets_dir
        tpl = load_template(tpl_path, assets_dir if in_site else None)
        out_path = output_root / "404.html"
        current_out_dir = output_root
        breadcrumbs = '<span class="current">404 - Page Not Found</span>'
        sidebar_html = render_sidebar_html(nav_root, current_out_dir, output_root, Path("404.html"), is_multilingual, root_output)
        css_url = css_dst.name  # At root
        common_js_url = "common.js"  # At root
        html = tpl.render(
            site_name=cfg.site_name,
            author=cfg.author,
            footer=cfg.footer,
            page_title=cfg.not_found_title,
            page_date=None,
            content_html=cfg.not_found_content,
            breadcrumbs=breadcrumbs,
            sidebar_html=sidebar_html,
            theme_css_url=css_url,
            common_js_url=common_js_url,
        )
        out_path.write_text(html, encoding="utf-8")
        info("Rendered 404.html")

    # Copy assets
    copy_assets(site_root, output_root)
    info("Assets copied (if any)")

    # Generate XML sitemap
    generate_sitemap_xml(cfg.base_url, output_root, search_items, log)

    info(f"Done. Output: {output_root}")


def _generate_language_selector(site_root: Path, output_root: Path, cfg: SiteConfig, log: Optional[UILog] = None) -> None:
    """Generate a root language selector page at output_root/index.html.

    Args:
        site_root: Path to the site project root.
        output_root: Path to the root output directory.
        cfg: SiteConfig instance.
        log: Optional log widget to report progress in the TUI.
    """
    def info(msg: str) -> None:
        if log is not None:
            log.write(msg)
        else:
            print(msg)

    # Create simple language selector HTML
    selector_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{cfg.site_name} - Select Language</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .language-selector {{
            text-align: center;
            margin-top: 100px;
        }}
        .language-buttons {{
            display: flex;
            justify-content: center;
            gap: 20px;
            margin-top: 40px;
        }}
        .lang-btn {{
            padding: 15px 30px;
            font-size: 18px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
            background-color: #007bff;
            color: white;
        }}
        .lang-btn:hover {{
            background-color: #0056b3;
        }}
        .site-title {{
            font-size: 2.5em;
            margin-bottom: 10px;
            color: #333;
        }}
        .site-subtitle {{
            font-size: 1.2em;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="language-selector">
        <h1 class="site-title">{cfg.site_name}</h1>
        <p class="site-subtitle">Choose your preferred language</p>
        <div class="language-buttons">"""

    for lang in cfg.languages:
        lang_name = {"en": "English", "it": "Italiano"}.get(lang, lang.upper())
        selector_html += f"""
            <a href="{lang}/" class="lang-btn">{lang_name}</a>"""

    selector_html += """
        </div>
    </div>
</body>
</html>"""

    # Write the selector page
    index_path = output_root / "index.html"
    index_path.write_text(selector_html, encoding="utf-8")
    info("Generated language selector: index.html")
