@echo off
echo ====================================
echo Installing ChromeDriver for Windows 11
echo ====================================
echo.

echo Python version:
python --version
echo.

echo Checking system architecture...
if defined PROCESSOR_ARCHITEW6432 (
    echo Architecture: 64-bit
    set "ARCH=64"
) else (
    echo Architecture: 32-bit
    set "ARCH=32"
)
echo.

echo Cleaning old ChromeDriver files...
rmdir /s /q "%USERPROFILE%\.wdm" 2>nul

echo Installing compatible webdriver-manager...
pip uninstall webdriver-manager -y >nul 2>&1
pip install --upgrade webdriver-manager

echo.
echo ====================================
echo Installation complete!
echo ====================================
echo.
echo Please run start.bat now
echo.
pause
