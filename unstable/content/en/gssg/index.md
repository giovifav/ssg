---
title: Gio's static site generator
date: 2025-09-17
---

# Gio's Static Site Generator

A modern and intuitive static site generator written in Python with a Textual-based terminal interface.

## Description

This tool allows you to create static websites starting from Markdown files. It offers a simple graphical interface to manage content, apply themes, and generate sites ready for publication. Supports image galleries, blog systems, automatic navigation, and much more.

[Download](https://github.com/giovifav/ssg)

## Main Features

- **Markdown Processing**: Converts Markdown files into HTML pages using frontmatter for metadata.
- **Customizable Themes**: Flexible templates with Jinja2 to customize the site's appearance.
- **Automatic Galleries**: Creates image galleries with thumbnails and integrated viewer.
- **Blog Systems**: Organizes content into articles with chronological sorting.
- **User Interface**: Modern TUI to manage sites without complex commands.
- **Automatic Navigation**: Sidebar and breadcrumbs generated automatically.
- **Multilingual**: Support for Italian and English.

## System Requirements

- Python 3.8 or higher
- Dependencies listed in `requirements.txt`

## Installation

```bash
git clone https://github.com/giovifav/ssg.git
cd ssg

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Launch the application
python main.py
```

## Usage

Launch the application with `python main.py`.

### Basic Steps

1. **Initialize a new site**: Choose a folder and configure name and author.
2. **Add content**: Create `.md` files in the `content/` folder with frontmatter for title, date, author.
3. **Add images and assets**: Place static files in the `assets/` folder.
4. **Generate the site**: The application automatically creates HTML output in the configured directory.

### Basic Structure of a Site

```
my-site/
├── content/
│   └── index.md
├── assets/
│   ├── theme.html
│   └── theme.css
└── config.toml
```

## License

This project is open source under MIT license.

For support or issues, visit the [GitHub repository](https://github.com/giovifav/ssg).
