Dim sDir, oShell
sDir = Left(WScript.ScriptFullName, InStrRev(WScript.ScriptFullName, "\"))
Set oShell = CreateObject("WScript.Shell")
oShell.Run """" & sDir & "venv\Scripts\pythonw.exe"" """ & sDir & "app.py""", 0, False
