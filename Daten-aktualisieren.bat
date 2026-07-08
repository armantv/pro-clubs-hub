@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================
echo   Pro Clubs Hub - Daten aktualisieren
echo   (Katalin FC / Cedric sigmas / Kepler AllStars)
echo ============================================
echo.
echo Holt die Spiele aller drei Vereine direkt von EA
echo und schreibt sie in die Webseite. Ein Browserfenster
echo blitzt evtl. kurz auf - einfach warten, laeuft von allein.
echo.
python update.py
echo.
echo Fertig. Du kannst dieses Fenster schliessen.
echo Danach die Webseite mit Strg+F5 neu laden.
pause
