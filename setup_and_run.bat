@echo off
:: ============================================================
:: setup_and_run.bat
:: One-click setup and launcher for Fiction Novel Generator
::
:: Double-click this file to:
::   1. Check Python is installed
::   2. Create a virtual environment
::   3. Install dependencies (requests, beautifulsoup4, python-dotenv)
::   4. Launch the app
::
:: No API key required!
:: - Research uses the free Wikipedia API (internet connection needed)
:: - Novel generation runs 100% locally on your PC
:: - For author-quality prose: install Ollama from https://ollama.ai
:: ============================================================

title Fiction Novel Generator - Setup

echo ============================================================
echo  Fiction Novel Generator - Setup and Launch
echo ============================================================
echo.
echo  No API key required.
echo  Research: free Wikipedia API (internet needed for research only)
echo  Generation: runs entirely on your PC
echo.
echo  For author-quality prose, install Ollama from https://ollama.ai
echo  then run:  ollama pull llama3.2
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
:: Step 4: Create placeholder .env if it doesn't exist
:: --------------------------------------------------
if not exist ".env" (
    echo [4/4] Creating .env placeholder...
    echo # Fiction Novel Generator configuration> .env
    echo # No API key required - research uses free Wikipedia API>> .env
    echo # Optional: set OLLAMA_HOST if using a remote Ollama server>> .env
    echo # OLLAMA_HOST=http://localhost:11434>> .env
    echo .env created.
) else (
    echo [4/4] .env already exists. Skipping.
)
echo.

:: --------------------------------------------------
:: Step 5: Launch the app
:: --------------------------------------------------
echo Launching Fiction Novel Generator...
echo.
python main.py

pause
