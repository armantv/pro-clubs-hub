@echo off
chcp 65001 >nul
echo ============================================
echo   Pro Clubs Hub - Auto-Update ENTFERNEN
echo ============================================
echo.
schtasks /Delete /F /TN "ProClubsHub Auto-Update" 2>nul
schtasks /Delete /F /TN "ProClubsHub Auto-Update (Anmeldung)" 2>nul
echo Auto-Update-Aufgaben entfernt (falls vorhanden).
echo.
pause
