#!/usr/bin/env python3
"""Sort the files in a folder (e.g. Downloads) into subfolders by type.

Usage:
    python3 organize.py ~/Downloads            # move files
    python3 organize.py ~/Downloads --dry-run  # only show what would happen
"""
import argparse
import shutil
import sys
from pathlib import Path

CATEGORIES = {
    "Images": {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp", ".heic"},
    "Documents": {".pdf", ".doc", ".docx", ".txt", ".md", ".rtf", ".odt", ".pages"},
    "Spreadsheets": {".xls", ".xlsx", ".csv", ".numbers", ".ods"},
    "Presentations": {".ppt", ".pptx", ".key", ".odp"},
    "Archives": {".zip", ".tar", ".gz", ".rar", ".7z", ".bz2"},
    "Audio": {".mp3", ".wav", ".flac", ".aac", ".m4a", ".ogg"},
    "Video": {".mp4", ".mov", ".avi", ".mkv", ".webm"},
    "Code": {".py", ".js", ".ts", ".html", ".css", ".json", ".sh", ".java", ".c", ".cpp"},
    "Installers": {".dmg", ".pkg", ".exe", ".msi", ".deb", ".app"},
}
OTHER = "Other"
FOLDER_NAMES = {name.lower() for name in CATEGORIES} | {OTHER.lower()}


def category_for(path: Path) -> str:
    """Return the category folder name for a file based on its extension."""
    ext = path.suffix.lower()
    for name, extensions in CATEGORIES.items():
        if ext in extensions:
            return name
    return OTHER


def unique_destination(dest: Path, taken: set = frozenset()) -> Path:
    """Return dest, or 'name (1).ext', 'name (2).ext', ... if it is already used.

    A path counts as used if it exists on disk (including broken symlinks)
    or is in `taken` (destinations already planned in this run).
    """
    def used(p: Path) -> bool:
        return p.exists() or p.is_symlink() or p in taken

    if not used(dest):
        return dest
    counter = 1
    while True:
        candidate = dest.with_name(f"{dest.stem} ({counter}){dest.suffix}")
        if not used(candidate):
            return candidate
        counter += 1


def organize(folder: Path, dry_run: bool = False) -> list[tuple[Path, Path]]:
    """Move each top-level file in folder into a category subfolder.

    Hidden files (starting with '.'), subdirectories, symlinks and files named
    like a category folder (e.g. a file called 'Images') are left alone, as are
    files whose category folder is blocked by such a file.
    Returns the list of (source, destination) moves performed or planned.
    """
    folder = Path(folder)
    if not folder.is_dir():
        raise NotADirectoryError(f"Not a directory: {folder}")

    moves = []
    planned = set()
    for item in sorted(folder.iterdir()):
        if not item.is_file() or item.is_symlink() or item.name.startswith("."):
            continue
        if item.name.lower() in FOLDER_NAMES:
            continue  # would block creating the category folder of the same name
        target_dir = folder / category_for(item)
        if target_dir.exists() and not target_dir.is_dir():
            continue  # a regular file occupies the category folder's name
        dest = unique_destination(target_dir / item.name, planned)
        planned.add(dest)
        moves.append((item, dest))
        if not dry_run:
            target_dir.mkdir(exist_ok=True)
            shutil.move(str(item), str(dest))
    return moves


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Sort files into folders by type.")
    parser.add_argument("folder", type=Path, help="folder to organize")
    parser.add_argument("--dry-run", action="store_true", help="show moves without doing them")
    args = parser.parse_args(argv)

    try:
        moves = organize(args.folder, dry_run=args.dry_run)
    except OSError as err:  # missing folder, no permission, etc.
        print(err, file=sys.stderr)
        return 1

    prefix = "[dry run] " if args.dry_run else ""
    for src, dest in moves:
        print(f"{prefix}{src.name} -> {dest.parent.name}/{dest.name}")
    print(f"{prefix}{len(moves)} file(s) {'would be ' if args.dry_run else ''}moved.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
