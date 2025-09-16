"""Gio's static site generator."""

if __name__ == "__main__":
    """CLI entry: run the TUI application or handle CLI commands."""
    import argparse
    from pathlib import Path
    from site_generator import generate_site
    from initialization import initialize_site
    from ui import SSGApp

    parser = argparse.ArgumentParser(description="Gio's static site generator")
    parser.add_argument(
        "-g", "--generate",
        metavar="FOLDER",
        help="Generate site HTML for the specified folder"
    )
    parser.add_argument(
        "-i", "--initialize",
        metavar="FOLDER",
        help="Initialize a new site in the specified folder"
    )

    args = parser.parse_args()

    if args.generate:
        folder = Path(args.generate)
        if not folder.exists():
            print(f"Error: Folder {folder} does not exist.")
            exit(1)
        print(f"Generating site in {folder}...")
        generate_site(folder)
        print("Site generation complete.")
    elif args.initialize:
        folder_name = args.initialize
        site_name = folder_name.replace("_", " ").replace("-", " ").title()
        print(f"Initializing site '{site_name}' in folder {folder_name}...")
        site_root = initialize_site(Path("."), folder_name, site_name, "Site Author")
        print(f"Site initialized at {site_root}")
    else:
        # No arguments provided, run TUI
        SSGApp().run()
