@echo off
:: ============================================================
:: create_shortcut.bat
:: Creates a desktop shortcut to Novel_Generator.bat
::
:: Run this once after setup to get a convenient desktop icon.
:: ============================================================

title Creating Desktop Shortcut...

set "APP_DIR=%~dp0"
set "TARGET=%APP_DIR%Novel_Generator.bat"
set "ICON=%APP_DIR%icon.ico"
set "SHORTCUT=%USERPROFILE%\Desktop\Fiction Novel Generator.lnk"

:: Use PowerShell to create a proper Windows .lnk shortcut
powershell -NoProfile -Command ^
  "$ws = New-Object -ComObject WScript.Shell; " ^
  "$s = $ws.CreateShortcut('%SHORTCUT%'); " ^
  "$s.TargetPath = '%TARGET%'; " ^
  "$s.WorkingDirectory = '%APP_DIR%'; " ^
  "if (Test-Path '%ICON%') { $s.IconLocation = '%ICON%' }; " ^
  "$s.Description = 'Fiction Novel Generator'; " ^
  "$s.Save()"

if %errorlevel% equ 0 (
    echo Desktop shortcut created successfully!
    echo You can now launch the app from your desktop.
) else (
    echo WARNING: Could not create desktop shortcut.
    echo You can still run the app using Novel_Generator.bat directly.
)

pause
