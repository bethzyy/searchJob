@echo off
echo ====================================
echo Fixing ChromeDriver Issue
echo ====================================
echo.

echo Checking Chrome version...
for /f "tokens=2*" %%a in ('reg query "HKEY_CURRENT_USER\Software\Google\Chrome\BLBeacon" /v version 2^>nul') do set "chrome_version=%%b"

if "%chrome_version%"=="" (
    echo Chrome browser not found!
    echo Please install Google Chrome first.
    echo Download: https://www.google.com/chrome/
    pause
    exit /b 1
)

echo Your Chrome version: %chrome_version%
echo.

echo Cleaning up old ChromeDriver files...
del /f /q "%USERPROFILE%\.wdm\drivers\chromedriver\win32\*.*" 2>nul

echo Reinstalling dependencies...
pip uninstall webdriver-manager -y >nul 2>&1
pip install webdriver-manager==4.0.1

echo.
echo ====================================
echo Fix completed!
echo Please run start.bat again
echo ====================================
pause
