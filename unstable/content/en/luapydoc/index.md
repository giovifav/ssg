---
title: LuaPyDoc
date: 2025-01-01
---

Luapydoc is a Python-based documentation generator for Lua codebases. It analyzes LDoc-style documentation comments in Lua source files and generates a complete, navigable HTML documentation website with syntax highlighting, search functionality, and more.

[Repository](https://github.com/giovifav/luapydoc)
[Sample output](docs)

## Features

- Analyzes LDoc documentation comments (@param, @return, @usage, etc.)
- Supports functions, variables, tables, and types
- Generates responsive HTML pages with dark theme
- Syntax highlighting for Lua code using Pygments
- Tree-based sidebar navigation for modules, classes, and functions
- Full-text search with indexing
- Responsive design for mobile and desktop

## Requirements

- Python 3.x
- jinja2
- pygments

## Installation

1. Clone this repository.
2. Install dependencies: `pip install -r requirements.txt`

## Usage

1. Place your Lua source files in a directory (e.g. `lua_src`), organized in subdirectories if necessary.
2. Run the generator with desired options (see examples below).
3. Open the `index.html` file in the output directory in your browser to view the documentation.

### Command Line Options

```bash
# Basic usage with default directories
python docs_generator.py

# Specify custom source and output directories
python docs_generator.py --src-dir ./my_lua_code --output-dir ./my_docs

# Using short forms
python docs_generator.py -s ./src -o ./docs

# Specify only source directory (default output 'docs')
python docs_generator.py --src-dir ./lua_src
```

**Available parameters:**
- `-s, --src-dir`: Directory containing Lua source files (default: `lua_src`)
- `-o, --output-dir`: Directory to generate documentation (default: `docs`)

**Full help:**
```bash
python docs_generator.py --help
```

## Project Structure

- `docs_generator.py`: Main script that analyzes Lua files and generates documentation
- `docs_template.html`: Jinja2 template for HTML pages
- `docs_style.css`: CSS styles for the documentation website
- `requirements.txt`: Python dependencies
- `lua_src/`: Directory for Lua source files (create it)
- `docs/`: Output directory for generated HTML files

## How It Works

The generator works in two phases:
1. Parses documentation comments (e.g. --- @param name desc)
2. Associates them with function definitions or variable assignments
3. Builds a hierarchical tree for navigation
4. Generates HTML pages using Jinja2 templates
5. Includes Lua code with syntax highlighting

## Customization

You can customize the appearance by modifying `docs_style.css` and the layout by modifying `docs_template.html`.
