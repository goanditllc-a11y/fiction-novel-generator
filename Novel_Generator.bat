@echo off
:: ============================================================
:: Novel_Generator.bat
:: Simple launcher for Fiction Novel Generator
::
:: Double-click this after running setup_and_run.bat once.
:: ============================================================

title Fiction Novel Generator

:: Guard: make sure setup has been run first
if not exist "venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found.
    echo Please run setup_and_run.bat first to set up the application.
    echo.
    pause
    exit /b 1
)

call venv\Scripts\activate.bat
python main.py
if errorlevel 1 (
    echo.
    echo The application exited with an error. See the message above.
    pause
)
