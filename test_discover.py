from pathlib import Path
from nav_builder import discover_markdown_files

content_root = Path('unstablecode/content')
md_files = discover_markdown_files(content_root)
print(f'Discovered {len(md_files)} markdown files:')
for mf in md_files:
    print(f'  {mf.relative_to(content_root)}')
