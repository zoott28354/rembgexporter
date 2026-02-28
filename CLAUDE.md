# Instructions for Claude — RembgExporter

This file contains instructions to follow every time you work on this project.

## Stack and Environment
- **Python 3.11+** + **CustomTkinter** (dark theme, 3-column layout)
- **rembg** for AI background removal, **ImageMagick** (portable) for ICO generation
- **Windows-only** distribution via PyInstaller
- Virtual environment in `/venv` (created by `scripts/setup.bat`)

## Project Structure
```
scripts/          # Developer toolchain (setup, build)
  setup.bat       # Creates venv, installs deps, generates start.vbs in root
  build.bat       # PyInstaller build — run from scripts/, cd to root automatically
  version_info.txt
src/
  assets/         # Static resources
    RembgExporter.ico
  third-party/    # Portable executables bundled with the project
    imagemagick/
app.py            # GUI — CustomTkinter, 3-column layout
core.py           # Processing pipeline — ImageMagick, rembg, PIL
requirements.txt
tests/
```

## Code Rules
- **Type hints** on all public functions
- `snake_case` for variables/functions, `PascalCase` for classes
- No `print()` in production — use `log_fn` callback for user-visible messages
- All code, comments and UI default in **English**; Italian available via IT/EN switcher

## Key Patterns (do NOT change without asking)
- `_resource_path(name)` in `app.py` — resolves asset paths in dev and PyInstaller exe
- `_get_imagemagick_path()` in `core.py` — finds magick.exe in src/third-party or system PATH
- `_t(key)` + `STRINGS` dict — i18n system, always add both EN and IT keys together
- `_tt(widget, key)` — registers tooltips for automatic language updates
- `log_fn` callback pattern — never use print() inside core.py functions

## scripts/ Rules
> **All `.bat` in `scripts/` must start with `cd /d "%~dp0.."` as first operation.**
> Without this, relative paths (`venv\`, `requirements.txt`, `src\`) resolve inside
> `scripts\` instead of the project root.

## Important Rules
- Do not modify `requirements.txt` without explaining what is being added and why
- Do not rename existing files without asking first
- Do not create files outside the defined structure

## Commit Conventions
- `feat:` new feature
- `fix:` bug fix
- `refactor:` refactoring without functional change
- `style:` colors, layout, UI without logic change
- `docs:` documentation only
- `test:` add/modify tests
- `bump:` version update

## What NOT to Do
- Do not hardcode absolute paths — use `_resource_path()` or `os.path.join()`
- Do not commit `venv/`, `dist/`, `build/`, `start.vbs`
- Do not use global variables
- Do not leave commented-out code without explanation
