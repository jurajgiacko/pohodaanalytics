@echo off
REM ============================================================
REM  Pohoda Analytics konektor - instalace (v1, vyzaduje Python)
REM  1. overi Python
REM  2. spusti pruvodce nastavenim (config.json)
REM  3. zaregistruje hodinovy sync do Task Scheduleru
REM  Pozdeji nahradi jednosouborovy setup.exe (PyInstaller).
REM ============================================================
setlocal
set SCRIPT_DIR=%~dp0

where python >nul 2>nul
if errorlevel 1 (
    echo [CHYBA] Python nebyl nalezen. Nainstalujte jej z https://www.python.org/downloads/
    echo         a pri instalaci zaskrtnete "Add Python to PATH".
    pause
    exit /b 1
)

if not exist "%SCRIPT_DIR%config.json" (
    echo — Prvni spusteni: nastaveni konektoru —
    python "%SCRIPT_DIR%sync.py" --init
)

echo Testovaci sync...
python "%SCRIPT_DIR%sync.py"
if errorlevel 1 (
    echo [CHYBA] Sync selhal - zkontrolujte config.json a zkuste znovu.
    pause
    exit /b 1
)

echo Registruji hodinovy sync do Task Scheduleru...
schtasks /Create /TN "PohodaAnalyticsSync" /TR "python \"%SCRIPT_DIR%sync.py\"" /SC HOURLY /F
if errorlevel 1 (
    echo [CHYBA] Registrace ulohy selhala - spustte install.bat jako spravce.
    pause
    exit /b 1
)

echo.
echo Hotovo! Konektor bude synchronizovat kazdou hodinu.
echo Uloha v Task Scheduleru: PohodaAnalyticsSync
pause
