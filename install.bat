@echo off
:: ============================================================
:: install.bat
:: One-click installer for Fiction Novel Generator
::
:: What this does:
::   1. Checks Python is installed (3.9+)
::   2. Copies the app to %USERPROFILE%\FictionNovelGenerator
::   3. Creates a Python virtual environment and installs dependencies
::   4. Creates a Desktop shortcut
::   5. Creates a Start Menu shortcut
::   6. Launches the app
::
:: Run this file once from wherever you extracted the ZIP.
:: After installation, launch the app from your Desktop or Start Menu.
::
:: To uninstall: delete  %USERPROFILE%\FictionNovelGenerator
::               and remove the shortcuts from your Desktop / Start Menu
:: ============================================================

title Fiction Novel Generator — Installer
color 0A

echo.
echo  ============================================================
echo   Fiction Novel Generator — Installer
echo  ============================================================
echo.
echo   This installer will:
echo     * Copy the app to your user folder
echo     * Install required Python packages (once)
echo     * Create a Desktop shortcut
echo     * Create a Start Menu shortcut
echo.
echo   No API key required.
echo   For author-quality prose, optionally install Ollama later:
echo     https://ollama.ai  then:  ollama pull llama3.2
echo  ============================================================
echo.

:: ------------------------------------------------------------------
:: Step 1 — Check Python
:: ------------------------------------------------------------------
echo [1/5] Checking Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo  ERROR: Python is not installed or not in your PATH.
    echo.
    echo  Please install Python 3.9 or newer:
    echo    1. Open:  https://www.python.org/downloads/
    echo    2. Click "Download Python 3.x.x"
    echo    3. Run the installer
    echo    4. IMPORTANT: tick "Add Python to PATH" before clicking Install
    echo    5. Re-run this installer
    echo.
    pause
    exit /b 1
)
for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PY_VER=%%v
echo  Python %PY_VER% found. OK
echo.

:: ------------------------------------------------------------------
:: Step 2 — Choose install location
:: ------------------------------------------------------------------
set "INSTALL_DIR=%USERPROFILE%\FictionNovelGenerator"
echo [2/5] Install location: %INSTALL_DIR%

if exist "%INSTALL_DIR%\" (
    echo  Folder already exists — updating in place.
) else (
    echo  Creating folder...
    mkdir "%INSTALL_DIR%"
)

:: Files and folders to exclude from the copy:
::   venv       — virtual environment (rebuilt in the install folder)
::   novels     — generated novel output (user data, kept separate)
::   __pycache__ / .git — build artefacts and source-control metadata
::   .env       — user secrets file (created fresh below)
::   *.pyc/pyo  — compiled Python bytecode
set "XCOPY_XD=venv novels __pycache__ .git"
set "XCOPY_XF=.env *.pyc *.pyo"

echo  Copying application files...
:: robocopy exit codes 0-7 are success/informational; 8+ are errors
robocopy "%~dp0" "%INSTALL_DIR%" /E /XD %XCOPY_XD% /XF %XCOPY_XF% /NFL /NDL /NJH /NJS >nul
if %errorlevel% gtr 7 (
    echo  ERROR: Failed to copy files (robocopy exit code %errorlevel%).
    pause
    exit /b 1
)
echo  Files copied. OK
echo.

:: ------------------------------------------------------------------
:: Step 3 — Create virtual environment and install dependencies
:: ------------------------------------------------------------------
echo [3/5] Setting up Python virtual environment...
if not exist "%INSTALL_DIR%\venv\" (
    python -m venv "%INSTALL_DIR%\venv"
    if %errorlevel% neq 0 (
        echo  ERROR: Could not create virtual environment.
        pause
        exit /b 1
    )
) else (
    echo  Virtual environment already exists. Skipping creation.
)

echo  Installing dependencies...
call "%INSTALL_DIR%\venv\Scripts\activate.bat"
pip install --quiet --upgrade pip
pip install --quiet -r "%INSTALL_DIR%\requirements.txt"
if %errorlevel% neq 0 (
    echo  ERROR: Failed to install dependencies.
    pause
    exit /b 1
)
echo  Dependencies installed. OK
echo.

:: ------------------------------------------------------------------
:: Step 4 — Create .env placeholder if absent
:: ------------------------------------------------------------------
if not exist "%INSTALL_DIR%\.env" (
    echo # Fiction Novel Generator — configuration> "%INSTALL_DIR%\.env"
    echo # No API key required.>> "%INSTALL_DIR%\.env"
    echo # Optional: change OLLAMA_HOST if using a remote Ollama server>> "%INSTALL_DIR%\.env"
    echo # OLLAMA_HOST=http://localhost:11434>> "%INSTALL_DIR%\.env"
)

:: ------------------------------------------------------------------
:: Step 5 — Create Desktop shortcut
:: ------------------------------------------------------------------
echo [4/5] Creating Desktop shortcut...
set "LAUNCHER=%INSTALL_DIR%\Novel_Generator.bat"
set "DESKTOP_LNK=%USERPROFILE%\Desktop\Fiction Novel Generator.lnk"

powershell -NoProfile -Command ^
  "$ws = New-Object -ComObject WScript.Shell; " ^
  "$s = $ws.CreateShortcut('%DESKTOP_LNK%'); " ^
  "$s.TargetPath = '%LAUNCHER%'; " ^
  "$s.WorkingDirectory = '%INSTALL_DIR%'; " ^
  "$s.Description = 'Fiction Novel Generator'; " ^
  "$s.Save()"

if %errorlevel% equ 0 (
    echo  Desktop shortcut created. OK
) else (
    echo  WARNING: Desktop shortcut could not be created. You can still run Novel_Generator.bat directly.
)

:: ------------------------------------------------------------------
:: Step 6 — Create Start Menu shortcut
:: ------------------------------------------------------------------
echo [5/5] Creating Start Menu shortcut...
set "START_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs"
set "START_LNK=%START_DIR%\Fiction Novel Generator.lnk"

powershell -NoProfile -Command ^
  "$ws = New-Object -ComObject WScript.Shell; " ^
  "$s = $ws.CreateShortcut('%START_LNK%'); " ^
  "$s.TargetPath = '%LAUNCHER%'; " ^
  "$s.WorkingDirectory = '%INSTALL_DIR%'; " ^
  "$s.Description = 'Fiction Novel Generator'; " ^
  "$s.Save()"

if %errorlevel% equ 0 (
    echo  Start Menu shortcut created. OK
) else (
    echo  WARNING: Start Menu shortcut could not be created.
)
echo.

:: ------------------------------------------------------------------
:: Done — launch the app
:: ------------------------------------------------------------------
echo  ============================================================
echo   Installation complete!
echo.
echo   Installed to:  %INSTALL_DIR%
echo   Desktop icon:  Fiction Novel Generator
echo   Start Menu:    Fiction Novel Generator
echo.
echo   The app will launch now.
echo   In future, open it from your Desktop or Start Menu.
echo  ============================================================
echo.

call "%INSTALL_DIR%\venv\Scripts\activate.bat"
python "%INSTALL_DIR%\main.py"

pause
