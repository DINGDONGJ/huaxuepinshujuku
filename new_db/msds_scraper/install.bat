@echo off
cls

echo ========================================================
echo MSDS Scraper - Dependencies Installation
echo ========================================================
echo.
echo Installing Python packages...
echo.

pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Python packages installation failed!
    echo.
    echo Please check that Python and pip are installed
    echo.
    pause
    exit /b 1
)

echo.
echo [SUCCESS] Python packages installed successfully!
echo.
echo ========================================================
echo Downloading Chromium browser driver
echo This may take several minutes, please wait
echo ========================================================
echo.

playwright install chromium

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Chromium download failed!
    echo.
    echo Please check your network connection
    echo Or manually run: playwright install chromium
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================================
echo [SUCCESS] All dependencies installed!
echo ========================================================
echo.
echo You can now run run_scraper.bat
echo.
pause
