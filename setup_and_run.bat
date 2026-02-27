@echo off
:: ============================================================
:: setup_and_run.bat
:: One-click setup and launcher for Fiction Novel Generator
::
:: Double-click this file to:
::   1. Check Python is installed
::   2. Create a virtual environment
::   3. Install dependencies
::   4. Prompt for your Gemini API key (first run only)
::   5. Launch the app
:: ============================================================

title Fiction Novel Generator - Setup

echo ============================================================
echo  Fiction Novel Generator - Setup and Launch
echo ============================================================
echo.

:: --------------------------------------------------
:: Step 1: Check Python is installed
:: --------------------------------------------------
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in your PATH.
    echo.
    echo Please install Python 3.9 or newer from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

echo [1/4] Python found:
python --version
echo.

:: --------------------------------------------------
:: Step 2: Create virtual environment if needed
:: --------------------------------------------------
if not exist "venv\" (
    echo [2/4] Creating virtual environment...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo ERROR: Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo Virtual environment created successfully.
) else (
    echo [2/4] Virtual environment already exists. Skipping creation.
)
echo.

:: --------------------------------------------------
:: Step 3: Install / update dependencies
:: --------------------------------------------------
echo [3/4] Installing dependencies from requirements.txt...
call venv\Scripts\activate.bat
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies.
    pause
    exit /b 1
)
echo Dependencies installed successfully.
echo.

:: --------------------------------------------------
:: Step 4: Create .env if it does not exist
:: --------------------------------------------------
if not exist ".env" (
    echo [4/4] First-time setup: Setting up your API key...
    echo.
    echo You need a free Gemini API key to use this app.
    echo Get one at: https://aistudio.google.com/app/apikey
    echo.
    set /p API_KEY="Paste your Gemini API key here and press Enter: "
    echo GEMINI_API_KEY=%API_KEY%> .env
    echo API key saved to .env
) else (
    echo [4/4] .env file already exists. Skipping API key setup.
    echo       (Use the Settings button inside the app to update it.)
)
echo.

:: --------------------------------------------------
:: Step 5: Launch the app
:: --------------------------------------------------
echo Launching Fiction Novel Generator...
python main.py

pause
