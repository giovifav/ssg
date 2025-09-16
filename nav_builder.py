"""Navigation tree building and rendering for Gio's static site generator."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PurePath
from typing import List, Optional, Tuple
import os

import frontmatter  # type: ignore


@dataclass
class NavNode:
    """Navigation tree node representing a directory or a markdown page."""

    name: str  # Display name (from frontmatter title or filename)
    rel_content_path: Path  # Relative path from content root (for both files and dirs)
    rel_output_path: Path  # Relative path from output root (for both files and dirs)
    is_dir: bool  # True if this node represents a directory
    children: List["NavNode"]


def discover_markdown_files(content_root: Path) -> List[Path]:
    """Recursively collect all Markdown files under a content root.

    Args:
        content_root: Path to the content directory.

    Returns:
        List of absolute paths to .md files.
    """
    files: List[Path] = []
    for path in content_root.rglob("*.md"):
        if path.is_file():
            files.append(path)
    return files


def load_title_from_markdown(md_path: Path) -> str:
    """Extract page title from markdown frontmatter.

    Falls back to filename stem (sanitized) if no title is present.

    Args:
        md_path: Markdown file path.

    Returns:
        Title string.
    """
    try:
        post = frontmatter.load(md_path)
        title = post.metadata.get("title")
        if isinstance(title, str) and title.strip():
            return title.strip()
    except Exception:
        pass
    return md_path.stem.replace("_", " ").replace("-", " ")


def build_nav_tree(content_root: Path, output_root: Path) -> NavNode:
    """Build a navigation tree reflecting content/ directory structure.

    Each markdown file is mapped to its future output HTML path.

    Args:
        content_root: Path to content/ directory.
        output_root: Path to output/ directory.

    Returns:
        Root NavNode representing the content root.
    """
    # Map directories to node - cache to avoid recreating nodes
    dir_nodes: dict[Path, NavNode] = {}

    def get_dir_node(dir_path: Path) -> NavNode:
        # Lazy creation of directory nodes with caching
        if dir_path not in dir_nodes:
            name = dir_path.name or "Home"
            rel_content = dir_path.relative_to(content_root)
            rel_output = rel_content
            # For directories, output path is the directory itself, not an index.html
            # This is important for determining active state of a directory
            dir_nodes[dir_path] = NavNode(
                name=name,
                rel_content_path=rel_content,
                rel_output_path=rel_output,
                is_dir=True,
                children=[],
            )
        return dir_nodes[dir_path]

    # Ensure root node exists
    root_node = get_dir_node(content_root)

    # First pass: Walk filesystem and create nodes for all Markdown files
    for path in sorted(content_root.rglob("*")):
        if path.is_dir():
            # Directories are handled by get_dir_node when their children or themselves are processed
            continue
        if path.suffix.lower() != ".md":
            continue

        rel_md = path.relative_to(content_root)
        out_rel = rel_md.with_suffix(".html")

        # Skip files inside _blog directories except index.md which should be navigable
        if "_blog" in rel_md.parts and path.name != "index.md":
            continue

        # Get or create parent directory node
        parent_node = get_dir_node(path.parent)
        # Create file node and attach to parent
        node = NavNode(
            name=load_title_from_markdown(path),
            rel_content_path=rel_md,
            rel_output_path=out_rel,
            is_dir=False,
            children=[],
        )
        parent_node.children.append(node)

    # Second pass: Attach subdirectories under their parents
    # This ensures directories are properly nested even when they contain no Markdown files
    for dpath, node in list(dir_nodes.items()):
        if dpath == content_root:
            continue  # Skip root node
        parent = get_dir_node(dpath.parent)
        if node not in parent.children:
            parent.children.append(node)

    # Sort children: directories first by name, then files by name
    def sort_key(n: NavNode) -> Tuple[int, str]:
        # Return tuple (priority, name) where directories have higher priority (0) than files (1)
        return (0 if n.is_dir else 1, n.name.lower())

    def sort_tree(n: NavNode) -> None:
        n.children.sort(key=sort_key)
        # Recursively sort all child nodes
        for ch in n.children:
            sort_tree(ch)

    sort_tree(root_node)
    return root_node


def render_sidebar_html(
    node: NavNode,
    current_out_dir: Path,
    output_root: Path,
    current_out_rel: Optional[Path] = None,
) -> str:
    """Render a nested sidebar HTML from the navigation tree.

    Rules:
    - Home link first.
    - Directory labels link to index.html (if present) without duplicating it.
    - Show pages inside a directory ONLY when we are on that directory's index page.
    - Root index is not duplicated (covered by Home).

    Args:
    - node: Root of the navigation tree.
    - current_out_dir: Directory of the current output HTML file.
    - output_root: Root of the output directory.
    - current_out_rel: Output path of current page relative to output_root, for active state.
    """

    def rel_href(target: Path) -> str:
        # Calculate relative href from current page location to target
        try:
            href = os.path.relpath(target, start=current_out_dir)
        except Exception:
            href = str(target)
        return href.replace(os.sep, "/")

    def is_active_node(n: NavNode) -> bool:
        # Determine if a navigation node should be highlighted as active
        if current_out_rel is None:
            return False
        if n.is_dir:
            # A directory is active if the current page's output path starts with or is equal to the directory's output path
            return current_out_rel.as_posix().startswith(n.rel_output_path.as_posix())
        else:
            # A file is active if its output path exactly matches the current page's output path
            return n.rel_output_path.as_posix() == current_out_rel.as_posix()

    def render_file(f: NavNode) -> str:
        # Render a single file navigation item
        label = f.name
        target = output_root / f.rel_output_path
        href = rel_href(target)
        active = is_active_node(f)
        cls = ' class="active"' if active else ''
        return f'<li><a href="{href}"{cls}>{label}</a></li>'

    def render_dir(d: NavNode) -> str:
        # Render a directory navigation item with optional expansion
        # Find index child if present to use its title and link
        index_child = next(
            (c for c in d.children if not c.is_dir and c.rel_output_path.name == "index.html"),
            None,
        )
        # Use index child title if available, otherwise directory name
        label = index_child.name if index_child else d.name
        href = rel_href(output_root / index_child.rel_output_path) if index_child else None

        active_dir = is_active_node(d)

        sub_items: List[str] = []
        # Only render children if the directory is active (current directory)
        if active_dir:
            for c in d.children:
                if c.is_dir:
                    sub_items.append(render_dir(c))
                else:
                    # Exclude the index.html from the direct children list if it exists
                    if index_child is not None and c.rel_output_path == index_child.rel_output_path:
                        continue
                    sub_items.append(render_file(c))

        inner_ul = f"<ul>{''.join(sub_items)}</ul>" if sub_items else ""
        # Use HTML details/summary for expandable directory
        open_attr = " open" if active_dir else ""

        if href:
            key = index_child.rel_output_path.as_posix() if index_child else d.rel_output_path.as_posix()
            summary = f'<summary><a href="{href}" data-target="{key}"{(" class=\"active\"" if active_dir else "")}>{label}</a></summary>'
        else:
            summary = f"<summary><span>{label}</span></summary>"
        return f'<li class="dir"><details{open_attr}>{summary}{inner_ul}</details></li>'

    # Build top-level navigation list
    items: List[str] = []
    # Add Home link first
    home_target = output_root / "index.html"
    home_active = bool(current_out_rel and current_out_rel.as_posix() == "index.html")
    home_cls = ' class="active"' if home_active else ''
    items.append(f'<li><a href="{rel_href(home_target)}"{home_cls}>Home</a></li>')

    # Then render root children, excluding the root index page to avoid duplicate Home
    for ch in node.children:
        if not ch.is_dir and ch.rel_output_path.name == "index.html":
            continue  # Skip root index.html to avoid duplicating Home
        if ch.is_dir:
            items.append(render_dir(ch))
        else:
            items.append(render_file(ch))

    return f"<ul>{''.join(items)}</ul>"


def build_breadcrumbs(
    content_root: Path,
    output_root: Path,
    rel_md_path: Path,
    current_out_dir: Path,
) -> List[dict[str, Optional[str]]]:
    """Build breadcrumbs for the current page.

    Computes links relative to the current output directory and only links
    segments that have an index.md.

    Args:
        content_root: Path to content/ directory.
        output_root: Path to output/ directory.
        rel_md_path: Markdown path relative to content_root for the current page.
        current_out_dir: Output directory of the current HTML page.

    Returns:
        List of dicts with keys: label, url (None for current segment or missing index).
    """
    crumbs: List[dict[str, Optional[str]]] = []

    # Home (use title from content/index.md if available)
    home_index = content_root / "index.md"
    if home_index.exists():
        target = output_root / "index.html"
        try:
            url = os.path.relpath(target, start=current_out_dir).replace(os.sep, "/")
        except Exception:
            url = "index.html"
        home_label = load_title_from_markdown(home_index) or "Home"
        crumbs.append({"label": home_label, "url": url})
    else:
        crumbs.append({"label": "Home", "url": None})

    parts = list(rel_md_path.parts)
    # Remove the filename part for intermediate dirs
    for i in range(len(parts) - 1):
        d = content_root.joinpath(*parts[: i + 1])
        idx = d / "index.md"
        if idx.exists():
            target_html = output_root.joinpath(*parts[: i + 1], "index.html")
            try:
                url = os.path.relpath(target_html, start=current_out_dir).replace(os.sep, "/")
            except Exception:
                url = (Path(*parts[: i + 1]) / "index.html").as_posix()
            label = load_title_from_markdown(idx)
        else:
            url = None
            # Fallback to directory name if no index.md
            label = Path(parts[i]).name.replace("_", " ").replace("-", " ")
        crumbs.append({"label": label, "url": url})

    # Current page (no link) — use frontmatter title if available
    current_md = content_root / rel_md_path
    try:
        label = load_title_from_markdown(current_md)
    except Exception:
        label = rel_md_path.stem.replace("_", " ").replace("-", " ")
    crumbs.append({"label": label, "url": None})
    return crumbs
