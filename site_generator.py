"""Site generation logic for Gio's static site generator."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import json
import os
import re
import shutil

import frontmatter  # type: ignore
import markdown  # type: ignore
from jinja2 import Template  # type: ignore
try:
    from PIL import Image, ImageOps  # type: ignore
except Exception:
    Image = None  # type: ignore
    ImageOps = None  # type: ignore

try:
    from config import SiteConfig, read_config
    from nav_builder import (
        NavNode,
        discover_markdown_files,
        build_nav_tree,
        render_sidebar_html,
        build_breadcrumbs,
        load_title_from_markdown
    )
except ImportError:
    from .config import SiteConfig, read_config
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
    text = text.replace("&nbsp;", " ").replace("&", "&").replace("<", "<").replace(">", ">")
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def load_template(theme_path: Path) -> Template:
    """Load a Jinja2 template from a file path."""
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

    for src_file in sorted(gallery_dir.iterdir()):
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
    output_root: Path,
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

    # Resolve gallery asset URLs relative to the current output file (now at output root)
    assets_css = href(output_root / "gallery.css")
    assets_js = href(output_root / "gallery.js")

    # Render using external template
    html = gallery_template.render(
        id=gallery_id,
        css_href=assets_css,
        js_href=assets_js,
        cards=cards,
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

    content_root = site_root / "content"
    if not content_root.exists():
        raise FileNotFoundError(f"content/ folder not found in: {site_root}")

    output_root = site_root / cfg.output
    # Clean output directory before generation
    if output_root.exists():
        try:
            shutil.rmtree(output_root)
            info(f"Cleaned output directory: {output_root}")
        except Exception as e:
            info(f"Warning: failed to clean output directory {output_root}: {e}")
    output_root.mkdir(parents=True, exist_ok=True)

    # Load theme template. Prefer site-local theme; else fall back to repo root theme.
    REPO_ROOT = Path(__file__).resolve().parent  # Adjusted to parent for assets path
    theme_path = site_root / cfg.base_theme
    if not theme_path.exists():
        theme_path = REPO_ROOT / "assets" / Path(cfg.base_theme).name  # Fallback to repo assets
    if not theme_path.exists():
        raise FileNotFoundError(f"Theme not found: {cfg.base_theme}")
    template = load_template(theme_path)

    # Load blog template if available. Use site assets first, fallback to repo assets
    blog_template_path = site_root / "assets" / "blog.html"
    if not blog_template_path.exists():
        blog_template_path = REPO_ROOT / "assets" / "blog.html"  # Repo fallback
    if blog_template_path.exists():
        blog_template = load_template(blog_template_path)
        info("[Blog] Using blog-specific template")
    else:
        blog_template = template  # Fallback to main theme template if blog template not found
        info("[Blog] Using fallback template")

    # Ensure CSS copied to output root
    css_src = site_root / cfg.theme_css
    if not css_src.exists():
        css_src = REPO_ROOT / "assets" / Path(cfg.theme_css).name  # Fallback to repo assets
    if not css_src.exists():
        raise FileNotFoundError(f"Theme CSS not found: {cfg.theme_css}")
    css_dst = output_root / css_src.name
    shutil.copyfile(css_src, css_dst)

    # Copy non-markdown files
    copy_non_markdown_files(content_root, output_root, log)

    # Build nav tree
    nav_root = build_nav_tree(content_root, output_root)

    # Collect markdown files to render
    md_files = discover_markdown_files(content_root)
    info(f"Discovered {len(md_files)} markdown files")

    # Collect data for search index
    search_items: list[dict[str, Any]] = []

    # Track blog folders that have been processed
    processed_blog_folders = set()

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
                            blog_title = index_post.metadata.get("title") or load_title_from_markdown(index_md_path) or "Blog"
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
                    breadcrumbs = build_breadcrumbs(content_root, output_root, blog_rel_path.with_suffix(".md"), current_out_dir)
                    sidebar_html = render_sidebar_html(nav_root, current_out_dir, output_root, blog_rel_path)

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
                    output_root=output_root,
                    gallery_id=f"gallery-{rel_md.parent.as_posix().replace('/', '-') or 'root'}",
                    gallery_template=gallery_template,
                )
                # Replace the page content with gallery HTML for dedicated gallery pages
                if gallery_html:
                    body_html = gallery_html
                    info(f"[Gallery] Gallery rendered in: {rel_md}")
            except Exception as e:
                info(f"[Gallery] Error generating gallery for {rel_md}: {e}")
        # 2) Otherwise, if this is a parent index.md and a sibling _gallery exists WITHOUT its own index.md,
        #    append the gallery to the parent page.
        elif md_file.name.lower() == "index.md":
            gallery_dir = md_file.parent / "_gallery"
            if gallery_dir.exists() and gallery_dir.is_dir() and not (gallery_dir / "index.md").exists():
                try:
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
                        output_root=output_root,
                        gallery_id=f"gallery-{rel_md.parent.as_posix().replace('/', '-') or 'root'}",
                        gallery_template=gallery_template,
                    )
                    # Append gallery HTML after the main page content
                    if gallery_html:
                        body_html = f"{body_html}\n\n{gallery_html}"
                        info(f"[Gallery] Gallery appended to parent: {rel_md.parent or Path('.')}")
                except Exception as e:
                    info(f"[Gallery] Error generating gallery for {rel_md}: {e}")

        # Use default template
        current_template = template

        # Build breadcrumbs (relative to this file's directory)
        current_out_dir = out_path.parent
        breadcrumbs = build_breadcrumbs(content_root, output_root, rel_md, current_out_dir)

        # Sidebar HTML (links relative to this file)
        sidebar_html = render_sidebar_html(nav_root, current_out_dir, output_root, out_rel)

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
        tpl = load_template(tpl_path)
        out_path = output_root / "404.html"
        current_out_dir = output_root
        breadcrumbs = '<span class="current">404 - Page Not Found</span>'
        sidebar_html = render_sidebar_html(nav_root, current_out_dir, output_root, Path("404.html"))
        css_url = css_dst.name  # At root
        common_js_url = "common.js"  # At root
        html = tpl.render(
            site_name=cfg.site_name,
            author=cfg.author,
            footer=cfg.footer,
            page_title="404 - Page Not Found",
            page_date=None,
            content_html="",  # Template has fixed content
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

    info(f"Done. Output: {output_root}")
