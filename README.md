# Downloads Folder Cleanup

A small Python command-line tool that sorts the files in a folder (like Downloads or Desktop) into subfolders by file type: Images, Documents, Archives and so on.

Built with the help of Claude Code as a way to learn Python automation.

## Example

Before:

```
Downloads/
├── report.pdf
├── holiday.jpg
├── budget.xlsx
├── song.mp3
└── setup.dmg
```

After running `python3 organize.py ~/Downloads`:

```
Downloads/
├── Audio/song.mp3
├── Documents/report.pdf
├── Images/holiday.jpg
├── Installers/setup.dmg
└── Spreadsheets/budget.xlsx
```

## Requirements

Python 3.9 or newer. No extra packages needed.

## Usage

Preview what would happen, without moving anything:

```bash
python3 organize.py ~/Downloads --dry-run
```

Sort the files for real:

```bash
python3 organize.py ~/Downloads
```

It works on any folder, for example `python3 organize.py ~/Desktop`.

**Tip:** always try `--dry-run` first on a new folder.

## Categories

| Folder | File types |
|---|---|
| Images | jpg, jpeg, png, gif, bmp, svg, webp, heic |
| Documents | pdf, doc, docx, txt, md, rtf, odt, pages |
| Spreadsheets | xls, xlsx, csv, numbers, ods |
| Presentations | ppt, pptx, key, odp |
| Archives | zip, tar, gz, rar, 7z, bz2 |
| Audio | mp3, wav, flac, aac, m4a, ogg |
| Video | mp4, mov, avi, mkv, webm |
| Code | py, js, ts, html, css, json, sh, java, c, cpp |
| Installers | dmg, pkg, exe, msi, deb, app |
| Other | everything else |

To add your own categories or file types, edit the `CATEGORIES` dictionary at the top of `organize.py`.

## Safety

The script is designed never to lose or overwrite your files:

- **No overwriting:** if a file with the same name already exists, the new one is renamed, for example `photo (1).jpg`.
- **Only top-level files:** existing subfolders are left untouched.
- **Skips** hidden files (like `.DS_Store`) and symlinks.
- **Safe to run again:** running it twice in a row does nothing the second time.
- **Clear errors:** if the folder doesn't exist or can't be read, it prints an error and exits instead of crashing.

## Tests

The project includes a test suite covering sorting, dry runs, name collisions and edge cases:

```bash
python3 -m unittest test_organize.py
```
