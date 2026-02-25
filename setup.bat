@echo off
echo Creazione ambiente virtuale...
python -m venv venv

echo Installazione dipendenze...
venv\Scripts\pip install -r requirements.txt

echo Creazione lancia.bat...
(
    echo @echo off
    echo "%~dp0venv\Scripts\pythonw.exe" "%~dp0app.py"
) > "%~dp0lancia.bat"

echo.
echo Setup completato. Usa lancia.bat per avviare l'app.
pause
