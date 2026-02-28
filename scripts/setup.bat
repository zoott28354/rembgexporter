@echo off
:: ── RembgExporter setup script ─────────────────────────────────────────────
:: Author : zoott28354
:: GitHub : https://github.com/zoott28354/rembgexporter
:: ─────────────────────────────────────────────────────────────────────────
cd /d "%~dp0.."

echo ==========================================
echo  RembgExporter - Setup
echo ==========================================

echo.
echo Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo ERROR: cannot create venv. Make sure Python is installed.
    pause
    exit /b 1
)

echo Installing dependencies...
venv\Scripts\pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: dependency installation failed.
    pause
    exit /b 1
)

echo.
echo Creating start.vbs in root...
(
    echo Dim sDir, oShell
    echo sDir = Left^(WScript.ScriptFullName, InStrRev^(WScript.ScriptFullName, "\"^)^)
    echo Set oShell = CreateObject^("WScript.Shell"^)
    echo oShell.Run """" ^& sDir ^& "venv\Scripts\pythonw.exe"" """ ^& sDir ^& "app.py""", 0, False
) > "%~dp0..\start.vbs"

echo.
echo ==========================================
echo  Setup complete.
echo  Use start.vbs in the root to launch the app.
echo ==========================================
pause
