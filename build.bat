@echo off
:: ── rembgexporter build script ────────────────────────────────────────────
:: Author : zoott28354
:: GitHub : https://github.com/zoott28354/rembgexporter
:: ─────────────────────────────────────────────────────────────────────────

if not exist venv\Scripts\python.exe (
    echo Virtual environment not found. Run setup.bat first.
    pause
    exit /b 1
)

venv\Scripts\python.exe -m PyInstaller --onefile --windowed ^
  --icon=rembgexporter.ico ^
  --name=rembgexporter ^
  --version-file=version_info.txt ^
  --collect-all customtkinter ^
  --collect-all rembg ^
  --collect-all svglib ^
  --collect-all reportlab ^
  --copy-metadata rembg ^
  --copy-metadata pymatting ^
  --copy-metadata onnxruntime ^
  --copy-metadata Pillow ^
  --copy-metadata numpy ^
  --hidden-import=click ^
  --hidden-import=scipy.special._cdflib ^
  --hidden-import=pycparser.lextab ^
  --hidden-import=pycparser.yacctab ^
  --add-data "rembgexporter.ico;." ^
  --add-data "third-party/imagemagick;imagemagick" ^
  app.py

echo.
echo Build complete. The executable is located at dist\rembgexporter.exe
pause
