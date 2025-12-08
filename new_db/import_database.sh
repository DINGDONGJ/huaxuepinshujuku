#!/bin/bash
# 在服务器上导入数据库脚本

echo "========================================================"
echo "          数据库导入脚本"
echo "========================================================"
echo ""

# 检查MySQL是否安装
if ! command -v mysql &> /dev/null; then
    echo "❌ Error: MySQL client is not installed!"
    echo ""
    echo "Please install MySQL first:"
    echo "  sudo apt-get update"
    echo "  sudo apt-get install mysql-server mysql-client"
    echo ""
    exit 1
fi

# 检查备份文件是否存在
if [ ! -f "database_backup.sql" ]; then
    echo "❌ Error: database_backup.sql not found!"
    echo ""
    echo "Please upload database_backup.sql to the server first."
    exit 1
fi

echo "📦 Database backup file found!"
echo "   File: database_backup.sql"
echo "   Size: $(ls -lh database_backup.sql | awk '{print $5}')"
echo ""

# 尝试无密码连接MySQL
echo "Testing MySQL connection..."
MYSQL_PASSWORD=""
MYSQL_CMD="mysql -u root"

# 先尝试无密码连接
mysql -u root -e "SELECT 1;" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ MySQL connection successful (no password required)"
    MYSQL_CMD="mysql -u root"
    MYSQL_PASSWORD=""
else
    # 需要密码，提示输入
    echo "MySQL requires password."
    read -sp "Enter MySQL root password (press Enter if no password): " MYSQL_PASSWORD
    echo ""
    
    if [ -z "$MYSQL_PASSWORD" ]; then
        # 空密码，再试一次
        mysql -u root -e "SELECT 1;" 2>/dev/null
        if [ $? -eq 0 ]; then
            echo "✅ MySQL connection successful (no password)"
            MYSQL_CMD="mysql -u root"
        else
            echo "❌ Error: Cannot connect to MySQL without password!"
            exit 1
        fi
    else
        # 有密码
        mysql -u root -p"$MYSQL_PASSWORD" -e "SELECT 1;" 2>/dev/null
        if [ $? -eq 0 ]; then
            echo "✅ MySQL connection successful"
            MYSQL_CMD="mysql -u root -p\"$MYSQL_PASSWORD\""
        else
            echo "❌ Error: Wrong password or cannot connect to MySQL!"
            exit 1
        fi
    fi
fi

echo ""

# 创建数据库（如果不存在）
echo "Creating database if not exists..."
if [ -z "$MYSQL_PASSWORD" ]; then
    mysql -u root -e "CREATE DATABASE IF NOT EXISTS \`危化品简化数据库\` CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;" 2>/dev/null
else
    mysql -u root -p"$MYSQL_PASSWORD" -e "CREATE DATABASE IF NOT EXISTS \`危化品简化数据库\` CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;" 2>/dev/null
fi

if [ $? -ne 0 ]; then
    echo "❌ Error: Failed to create database!"
    exit 1
fi

echo "✅ Database created/verified"
echo ""

# 导入数据
echo "Importing database..."
echo "Note: This may take a while if the database is large..."
if [ -z "$MYSQL_PASSWORD" ]; then
    mysql -u root --binary-mode --default-character-set=utf8mb4 "危化品简化数据库" < database_backup.sql
else
    mysql -u root -p"$MYSQL_PASSWORD" --binary-mode --default-character-set=utf8mb4 "危化品简化数据库" < database_backup.sql
fi

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Database imported successfully!"
    echo ""
    echo "Verifying import..."
    if [ -z "$MYSQL_PASSWORD" ]; then
        mysql -u root -e "USE \`危化品简化数据库\`; SELECT COUNT(*) AS total_chemicals FROM 化学品;" 2>/dev/null
    else
        mysql -u root -p"$MYSQL_PASSWORD" -e "USE \`危化品简化数据库\`; SELECT COUNT(*) AS total_chemicals FROM 化学品;" 2>/dev/null
    fi
    echo ""
    echo "✅ Import completed!"
else
    echo ""
    echo "❌ Error: Failed to import database!"
    exit 1
fi

