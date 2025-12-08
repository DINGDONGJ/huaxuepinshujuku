@echo off
cls

:menu
echo ========================================================
echo MSDS Scraper and Database Import Tool
echo ========================================================
echo.
echo Please select mode:
echo [1] Scrape only (save as JSON)
echo [2] Scrape and import to database
echo [0] Exit
echo ========================================================
set /p choice="Select [0-2]: "

if "%choice%"=="0" goto :end
if "%choice%"=="1" goto :scrape_only
if "%choice%"=="2" goto :scrape_import
echo Invalid choice, please try again.
echo.
pause
goto :menu

:scrape_only
echo.
echo ========================================================
echo Mode: Scrape Only
echo ========================================================
set /p url="Enter MSDS URL: "
if "%url%"=="" (
    echo Error: URL cannot be empty
    pause
    goto :menu
)
echo.
python scrape_to_json.py "%url%"
echo.
pause
goto :menu

:scrape_import
echo.
echo ========================================================
echo Mode: Scrape and Import to Database
echo ========================================================
set /p url="Enter MSDS URL: "
if "%url%"=="" (
    echo Error: URL cannot be empty
    pause
    goto :menu
)
set /p dbpass="Database password (default: 1234): "
if "%dbpass%"=="" set dbpass=1234
echo.
python scrape_to_json.py "%url%" --import --password %dbpass%
echo.
pause
goto :menu

:end
echo.
echo Goodbye!
echo.
pause
