@echo off
:: ── RembgExporter build script ─────────────────────────────────────────────
:: Author : zoott28354
:: GitHub : https://github.com/zoott28354/rembgexporter
:: ─────────────────────────────────────────────────────────────────────────
cd /d "%~dp0.."

echo ==========================================
echo  RembgExporter - Build .exe
echo ==========================================

echo.
if not exist venv\Scripts\python.exe (
    echo Virtual environment not found. Run scripts\setup.bat first.
    pause
    exit /b 1
)

venv\Scripts\python.exe -m PyInstaller --onefile --windowed ^
  --icon=src\assets\RembgExporter.ico ^
  --name=RembgExporter ^
  --version-file=scripts\version_info.txt ^
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
  --add-data "src\assets\RembgExporter.ico;src\assets" ^
  --add-data "src\third-party\imagemagick;imagemagick" ^
  app.py

echo.
if exist "dist\RembgExporter.exe" (
    echo ==========================================
    echo  Build complete: dist\RembgExporter.exe
    echo ==========================================
) else (
    echo ERROR: build failed. Check output above.
)
pause
