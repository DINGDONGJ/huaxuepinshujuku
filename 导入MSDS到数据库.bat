@echo off
chcp 65001 >nul
title MSDS数据导入工具 - 智能版

:MENU
cls
echo.
echo ╔══════════════════════════════════════════════════════════╗
echo ║          MSDS数据导入工具 - 智能版 v2.0                  ║
echo ║     自动识别化学品信息，一键导入MySQL数据库               ║
echo ╚══════════════════════════════════════════════════════════╝
echo.
echo  ✨ 新功能：自动从HTML提取化学品信息
echo  • 自动识别：名称、CAS号、分子式、EC编号
echo  • 自动创建：如果数据库中不存在该化学品
echo  • 只需指定文件夹，其他全自动！
echo.
echo ══════════════════════════════════════════════════════════
echo  当前可导入的MSDS数据：
echo.

REM 检查并列出所有msds_开头的文件夹
set count=0
for /d %%D in (msds_*) do (
    set /a count+=1
    echo  [!count!] %%D
)

if %count%==0 (
    echo  ❌ 未找到任何MSDS文件夹
    echo.
    echo  请先使用智能爬虫爬取数据！
    echo.
    pause
    exit
)

echo.
echo ══════════════════════════════════════════════════════════
echo.

set /p folder=请输入要导入的文件夹名称（如: msds_甲苯）: 

if "%folder%"=="" (
    echo.
    echo ❌ 未输入文件夹名称！
    echo.
    pause
    goto MENU
)

if not exist "%folder%" (
    echo.
    echo ❌ 文件夹不存在: %folder%
    echo.
    pause
    goto MENU
)

echo.
echo ══════════════════════════════════════════════════════════
echo  可选设置（直接回车使用默认值）
echo ══════════════════════════════════════════════════════════
echo.

set /p cas=CAS号（留空则自动识别）: 

echo.
set /p password=MySQL密码（默认: 123456）: 

if "%password%"=="" (
    set password=123456
)

echo.
echo ══════════════════════════════════════════════════════════
echo  开始导入...
echo ══════════════════════════════════════════════════════════
echo.

REM 根据是否提供CAS号选择不同命令
if "%cas%"=="" (
    python import_msds_to_db.py --folder "%folder%" --password "%password%"
) else (
    python import_msds_to_db.py --folder "%folder%" --cas "%cas%" --password "%password%"
)

if errorlevel 1 (
    echo.
    echo ══════════════════════════════════════════════════════════
    echo  ❌ 导入失败！
    echo ══════════════════════════════════════════════════════════
    echo.
    echo  可能的原因：
    echo  1. 数据库连接失败（检查密码和MySQL服务）
    echo  2. 化学品不存在（请先添加化学品基本信息）
    echo  3. HTML文件格式错误
    echo.
) else (
    echo.
    echo ══════════════════════════════════════════════════════════
    echo  ✓ 导入成功！
    echo ══════════════════════════════════════════════════════════
    echo.
)

set /p again=是否继续导入其他化学品？(y/n): 

if /i "%again%"=="y" (
    goto MENU
) else (
    echo.
    echo 感谢使用！
    timeout /t 2 >nul
    exit
)

