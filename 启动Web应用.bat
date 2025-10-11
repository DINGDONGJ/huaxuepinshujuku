@echo off
chcp 65001 >nul
echo ============================================================
echo 🚀 危化品数据库 Web应用启动脚本
echo ============================================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未检测到Python，请先安装Python 3.7+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo ✅ Python已安装
echo.

REM 检查依赖
echo 📦 检查Python依赖...
pip show Flask >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Flask未安装，正在安装依赖...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ❌ 依赖安装失败
        pause
        exit /b 1
    )
    echo ✅ 依赖安装成功
) else (
    echo ✅ 依赖已安装
)
echo.

REM 提醒配置数据库
echo ⚠️  重要提醒:
echo    请确保已在 app.py 中配置正确的MySQL密码
echo    DB_CONFIG = {'password': '你的密码', ...}
echo.

REM 启动应用
echo 🚀 启动Web应用...
echo ============================================================
echo.
python app.py

pause

