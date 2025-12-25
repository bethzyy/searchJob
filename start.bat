@echo off
echo ====================================
echo Job Finder v1.0
echo ====================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python not found
    echo Please install Python 3.8+
    pause
    exit /b 1
)

REM Check dependencies
echo Checking dependencies...
pip show selenium >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r requirements.txt
)

echo.
echo Starting GUI...
echo.

REM Start GUI
start "" pythonw gui.py

echo GUI launched. Check the window for status.
timeout /t 3 >nul
