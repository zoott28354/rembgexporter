@echo off
echo Creating virtual environment...
python -m venv venv

echo Installing dependencies...
venv\Scripts\pip install -r requirements.txt

echo Creating start.vbs...
(
    echo Dim sDir, oShell
    echo sDir = Left^(WScript.ScriptFullName, InStrRev^(WScript.ScriptFullName, "\"^)^)
    echo Set oShell = CreateObject^("WScript.Shell"^)
    echo oShell.Run """" ^& sDir ^& "venv\Scripts\pythonw.exe"" """ ^& sDir ^& "app.py""", 0, False
) > "%~dp0start.vbs"

echo.
echo Setup complete. Use start.vbs to launch the app (no CMD window).
pause
