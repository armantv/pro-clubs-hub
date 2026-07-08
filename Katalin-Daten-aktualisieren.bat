@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================
echo   Katalin FC - Daten aktualisieren
echo ============================================
echo.
echo Holt deine Spiele direkt von EA und schreibt sie
echo in die Webseite. Ein Browserfenster blitzt evtl.
echo kurz auf - einfach warten, laeuft von allein.
echo.
python update.py
echo.
echo Fertig. Du kannst dieses Fenster schliessen.
echo Danach die Webseite mit Strg+F5 neu laden.
pause
