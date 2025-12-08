@echo off
chcp 65001 >nul
echo ======================================================================
echo 🚀 语义搜索功能安装向导
echo ======================================================================
echo.

echo 📋 安装步骤:
echo    1. 安装Python依赖 (sentence-transformers, scikit-learn)
echo    2. 下载语义模型 (约420MB)
echo    3. 构建向量索引 (约20秒)
echo.

echo ⚠️  注意事项:
echo    - 需要约2.5GB磁盘空间
echo    - 首次运行需要下载模型 (3-5分钟)
echo    - 确保网络连接正常
echo.

pause

echo.
echo ======================================================================
echo 第1步: 安装Python依赖
echo ======================================================================
echo.

pip install sentence-transformers scikit-learn

if %errorlevel% neq 0 (
    echo.
    echo ❌ 依赖安装失败
    echo    请检查Python和pip是否正确安装
    pause
    exit /b 1
)

echo.
echo ✅ 依赖安装成功
echo.

echo ======================================================================
echo 第2步: 构建语义索引
echo ======================================================================
echo.
echo 正在构建索引，请耐心等待...
echo (首次运行会下载模型，约420MB)
echo.

python build_semantic_index.py

if %errorlevel% neq 0 (
    echo.
    echo ❌ 索引构建失败
    echo    请检查:
    echo    1. 数据库是否启动
    echo    2. 数据库密码是否正确
    echo    3. 是否有化学品数据
    pause
    exit /b 1
)

echo.
echo ======================================================================
echo ✅ 语义搜索功能安装完成！
echo ======================================================================
echo.
echo 💡 使用方法:
echo    1. 在app.py中集成语义搜索 (参考 app_with_semantic.py)
echo    2. 或直接使用: python semantic_search_engine.py
echo.
echo 📚 详细文档: SEMANTIC_SEARCH_README.md
echo.

pause
