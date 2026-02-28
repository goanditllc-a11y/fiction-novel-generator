@echo off
echo Building Fiction Novel Editor...
pip install -r requirements.txt
pyinstaller app.spec
echo Build complete! Find the executable in dist/
pause
