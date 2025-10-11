@echo off
chcp 65001 >nul
title Install Dependencies

echo.
echo ========================================================
echo        Installing Scraper Dependencies               
echo ========================================================
echo.
echo Installing Python packages...
echo.

pip install -r requirements.txt

echo.
echo ========================================================
echo.
echo Installing Playwright browser...
echo.

python -m playwright install chromium

echo.
echo ========================================================
echo.
echo Installation complete!
echo.
echo You can now use the scraper:
echo   - Double click: run_scraper.bat
echo.
pause

