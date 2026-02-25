@echo off
if not exist venv\Scripts\python.exe (
    echo Venv non trovato. Esegui prima setup.bat
    pause
    exit /b 1
)
venv\Scripts\python.exe -m PyInstaller --onefile --windowed --icon=convertICO.ico --name=ConvertICO ^
  --collect-all customtkinter ^
  --collect-all rembg ^
  --copy-metadata rembg ^
  --copy-metadata pymatting ^
  --copy-metadata onnxruntime ^
  --copy-metadata Pillow ^
  --copy-metadata numpy ^
  app.py
echo.
echo Build completata. L'eseguibile si trova in dist\ConvertICO.exe
pause
