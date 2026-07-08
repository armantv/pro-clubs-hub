@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================
echo   Pro Clubs Hub - Auto-Update EINRICHTEN
echo ============================================
echo.
echo Richtet zwei Aufgaben in der Windows-Aufgabenplanung ein:
echo   1. Alle 2 Stunden Daten holen (unsichtbar im Hintergrund)
echo   2. Einmal kurz nach jeder PC-Anmeldung
echo.
echo Liegt der Ordner in einem Git-Repo mit Remote (siehe HOSTING.md),
echo werden neue Daten automatisch zur gehosteten Webseite gepusht.
echo.

schtasks /Create /F /TN "ProClubsHub Auto-Update" /SC HOURLY /MO 2 ^
  /TR "wscript.exe \"%~dp0update-silent.vbs\""
if errorlevel 1 goto :fehler

schtasks /Create /F /TN "ProClubsHub Auto-Update (Anmeldung)" /SC ONLOGON /DELAY 0002:00 ^
  /TR "wscript.exe \"%~dp0update-silent.vbs\""
if errorlevel 1 goto :fehler

echo.
echo OK - Auto-Update ist aktiv. Erster Hintergrund-Lauf startet jetzt ...
schtasks /Run /TN "ProClubsHub Auto-Update" >nul
echo.
echo Kontrolle jederzeit in update.log oder in der Aufgabenplanung.
echo Entfernen: Auto-Update-entfernen.bat
echo.
pause
exit /b 0

:fehler
echo.
echo FEHLER beim Einrichten. Bitte die .bat einmal per Rechtsklick
echo "Als Administrator ausfuehren" starten und erneut versuchen.
echo.
pause
exit /b 1
