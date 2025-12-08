@echo off
chcp 65001 >nul
echo 正在导出数据库...
echo.

REM 使用mysqldump导出数据库
REM 请根据你的MySQL配置修改用户名和密码
REM --hex-blob 选项将二进制数据转换为十六进制格式，避免导入时的编码问题
mysqldump -u root -p1234 --default-character-set=utf8mb4 --single-transaction --routines --triggers --hex-blob "危化品简化数据库" > database_backup.sql

if %errorlevel% equ 0 (
    echo ✅ 数据库导出成功！
    echo 文件: database_backup.sql
    echo.
    dir database_backup.sql
) else (
    echo ❌ 数据库导出失败！
    pause
    exit /b 1
)

pause

