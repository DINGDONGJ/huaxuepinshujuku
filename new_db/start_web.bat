@echo off
chcp 65001 >nul
title MSDS Query System - Web Application

echo.
echo ========================================================
echo        MSDS Query System - Web Application           
echo ========================================================
echo.
echo Starting web server...
echo.
echo Access URL: http://localhost:5001
echo Database: Chemical Safety Database
echo.
echo Press Ctrl+C to stop server
echo.
echo ========================================================
echo.

python app.py

pause

