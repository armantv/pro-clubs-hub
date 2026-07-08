' Startet den Pro-Clubs-Updater UNSICHTBAR (kein schwarzes Fenster).
' Wird von der Windows-Aufgabenplanung aufgerufen (Auto-Update-einrichten.bat).
Option Explicit
Dim sh, fso, dir
Set sh = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
dir = fso.GetParentFolderName(WScript.ScriptFullName)
sh.CurrentDirectory = dir
sh.Run "cmd /c python update.py --auto", 0, True
