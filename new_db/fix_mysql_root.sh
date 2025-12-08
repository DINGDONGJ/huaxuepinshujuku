#!/bin/bash
# 修复MySQL root用户访问权限

echo "========================================================"
echo "      MySQL Root用户访问权限修复脚本"
echo "========================================================"
echo ""

# 检查MySQL是否安装
if ! command -v mysql &> /dev/null; then
    echo "❌ Error: MySQL client is not installed!"
    exit 1
fi

echo "MySQL root用户访问问题常见原因："
echo "1. MySQL 8.0+ 默认使用 auth_socket 插件"
echo "2. root用户需要使用密码认证"
echo ""
echo "解决方案："
echo ""

# 尝试使用sudo访问MySQL
echo "尝试使用sudo访问MySQL..."
sudo mysql -e "SELECT 1;" 2>/dev/null

if [ $? -eq 0 ]; then
    echo "✅ 可以使用sudo访问MySQL"
    echo ""
    echo "正在设置root用户密码认证..."
    echo ""
    
    read -sp "请输入要设置的root密码（留空则设置为空密码）: " ROOT_PASSWORD
    echo ""
    
    if [ -z "$ROOT_PASSWORD" ]; then
        # 设置为空密码
        sudo mysql <<EOF
ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY '';
FLUSH PRIVILEGES;
SELECT 'Root password set to empty (no password)' AS status;
EOF
        echo ""
        echo "✅ Root用户已设置为无密码访问"
        MYSQL_PASSWORD=""
    else
        # 设置密码
        sudo mysql <<EOF
ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY '$ROOT_PASSWORD';
FLUSH PRIVILEGES;
SELECT 'Root password set successfully' AS status;
EOF
        echo ""
        echo "✅ Root用户密码已设置"
        MYSQL_PASSWORD="$ROOT_PASSWORD"
    fi
    
    echo ""
    echo "测试新的连接方式..."
    if [ -z "$MYSQL_PASSWORD" ]; then
        mysql -u root -e "SELECT 'Connection successful!' AS status;" 2>/dev/null
    else
        mysql -u root -p"$MYSQL_PASSWORD" -e "SELECT 'Connection successful!' AS status;" 2>/dev/null
    fi
    
    if [ $? -eq 0 ]; then
        echo "✅ 连接测试成功！"
        echo ""
        echo "========================================================"
        echo "修复完成！"
        echo ""
        if [ -z "$MYSQL_PASSWORD" ]; then
            echo "Root用户密码：无密码"
        else
            echo "Root用户密码：已设置（请记住这个密码）"
        fi
        echo ""
        echo "请更新 app.py 中的数据库配置："
        echo "  'password': '',  # 如果没有密码"
        echo "  或"
        echo "  'password': '你的密码',  # 如果设置了密码"
        echo "========================================================"
    else
        echo "❌ 连接测试失败，请检查错误信息"
    fi
else
    echo "❌ 无法使用sudo访问MySQL"
    echo ""
    echo "请尝试以下方法："
    echo "1. 确保MySQL服务正在运行: sudo systemctl status mysql"
    echo "2. 尝试手动修复:"
    echo "   sudo mysql"
    echo "   ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY '你的密码';"
    echo "   FLUSH PRIVILEGES;"
    echo "   exit;"
fi

