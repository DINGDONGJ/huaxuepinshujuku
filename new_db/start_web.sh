#!/bin/bash
# MSDS Query System - Web Application Startup Script for Ubuntu/Linux

# 设置控制台编码为UTF-8
export LANG=zh_CN.UTF-8
export LC_ALL=zh_CN.UTF-8

# 设置终端标题（如果支持）
echo -ne "\033]0;MSDS Query System - Web Application\007"

# 清屏并显示启动信息
clear
echo ""
echo "========================================================"
echo "        MSDS Query System - Web Application           "
echo "========================================================"
echo ""
echo "Starting web server..."
echo ""
echo "Access URL: http://localhost:5001"
echo "Database: Chemical Safety Database"
echo ""
echo "Press Ctrl+C to stop server"
echo ""
echo "========================================================"
echo ""

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python3 is not installed!"
    echo "Please install Python3 first: sudo apt-get install python3 python3-pip"
    exit 1
fi

# 检查pip是否安装
if ! command -v pip3 &> /dev/null; then
    echo "❌ Error: pip3 is not installed!"
    echo "Please install pip3 first: sudo apt-get install python3-pip"
    exit 1
fi

# 检查app.py是否存在
if [ ! -f "app.py" ]; then
    echo "❌ Error: app.py not found!"
    echo "Please make sure you are in the correct directory."
    exit 1
fi

# 检查是否在虚拟环境中
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Virtual environment not detected. Setting up virtual environment..."
    echo ""
    
    # 检查虚拟环境是否存在且完整
    if [ ! -d "venv" ] || [ ! -f "venv/bin/activate" ]; then
        echo "Creating virtual environment..."
        
        # 先检查是否安装了python3-venv
        if ! python3 -c "import venv" 2>/dev/null; then
            echo ""
            echo "❌ Error: python3-venv module is not available!"
            echo ""
            echo "Please install python3-venv first:"
            echo "  sudo apt-get update"
            echo "  sudo apt-get install python3-venv"
            echo ""
            exit 1
        fi
        
        # 创建虚拟环境
        python3 -m venv venv
        if [ $? -ne 0 ]; then
            echo ""
            echo "❌ Error: Failed to create virtual environment!"
            echo "Please check the error message above."
            exit 1
        fi
        
        # 验证虚拟环境是否创建成功
        if [ ! -f "venv/bin/activate" ]; then
            echo ""
            echo "❌ Error: Virtual environment was not created properly!"
            echo "The venv/bin/activate file is missing."
            exit 1
        fi
        
        echo "✅ Virtual environment created!"
        echo ""
    fi
    
    # 激活虚拟环境
    echo "Activating virtual environment..."
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
    else
        echo ""
        echo "❌ Error: venv/bin/activate file not found!"
        echo "Please delete the venv directory and try again: rm -rf venv"
        exit 1
    fi
    
    # 验证虚拟环境是否激活成功
    if [ -z "$VIRTUAL_ENV" ]; then
        echo ""
        echo "❌ Error: Failed to activate virtual environment!"
        echo "VIRTUAL_ENV is not set. Please check venv/bin/activate file."
        exit 1
    fi
    
    echo "✅ Virtual environment activated!"
    echo "   Python path: $(which python)"
    echo "   Pip path: $(which pip)"
    echo ""
fi

# 检查依赖是否安装（使用虚拟环境中的python）
echo "Checking Python dependencies..."
if ! python -c "import flask" 2>/dev/null; then
    echo ""
    echo "⚠️  Warning: Required Python packages are not installed!"
    echo ""
    echo "Installing dependencies from requirements.txt..."
    echo ""
    
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
        if [ $? -ne 0 ]; then
            echo ""
            echo "❌ Error: Failed to install dependencies!"
            echo "Please check the error message above."
            exit 1
        fi
        echo ""
        echo "✅ Dependencies installed successfully!"
        echo ""
    else
        echo "⚠️  Warning: requirements.txt not found!"
        echo "Installing basic dependencies..."
        pip install Flask PyMySQL requests
        if [ $? -ne 0 ]; then
            echo ""
            echo "❌ Error: Failed to install dependencies!"
            echo "Please check the error message above."
            exit 1
        fi
        echo ""
        echo "✅ Dependencies installed successfully!"
        echo ""
    fi
fi

# 启动Python应用
echo "Starting Flask application..."
echo ""
python app.py

# 如果脚本意外退出，等待用户输入
echo ""
echo "Server stopped. Press Enter to exit..."
read

