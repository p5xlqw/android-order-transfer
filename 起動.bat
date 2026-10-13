@echo off
setlocal
cd /d "%~dp0"

where pyw >nul 2>nul
if not errorlevel 1 (
    pyw -3 -c "import sys, tkinter; sys.exit(0 if sys.version_info >= (3,10) else 1)" >nul 2>nul
    if not errorlevel 1 (
        start "" pyw -3 "%~dp0main.py"
        exit /b 0
    )
)

where pythonw >nul 2>nul
if not errorlevel 1 (
    pythonw -c "import sys, tkinter; sys.exit(0 if sys.version_info >= (3,10) else 1)" >nul 2>nul
    if not errorlevel 1 (
        start "" pythonw "%~dp0main.py"
        exit /b 0
    )
)

echo Python 3.10 or later with Tkinter was not found.
echo Install Python from python.org, enable the Python Launcher, then try again.
pause
endlocal
