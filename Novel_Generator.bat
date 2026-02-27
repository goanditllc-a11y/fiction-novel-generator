@echo off
:: ============================================================
:: Novel_Generator.bat
:: Simple launcher for Fiction Novel Generator
::
:: Double-click this after running setup_and_run.bat once.
:: ============================================================

title Fiction Novel Generator

call venv\Scripts\activate.bat
python main.py
