@echo off
echo Creazione ambiente virtuale...
python -m venv venv

echo Installazione dipendenze...
venv\Scripts\pip install -r requirements.txt

echo Creazione lancia.vbs...
(
    echo Dim sDir, oShell
    echo sDir = Left^(WScript.ScriptFullName, InStrRev^(WScript.ScriptFullName, "\"^)^)
    echo Set oShell = CreateObject^("WScript.Shell"^)
    echo oShell.Run """" ^& sDir ^& "venv\Scripts\pythonw.exe"" """ ^& sDir ^& "app.py""", 0, False
) > "%~dp0lancia.vbs"

echo.
echo Setup completato. Usa lancia.vbs per avviare l'app (nessuna finestra CMD).
pause
