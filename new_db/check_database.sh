#!/bin/bash
# 检查数据库表结构脚本

echo "========================================================"
echo "           数据库结构检查脚本"
echo "========================================================"
echo ""

# 尝试连接MySQL
MYSQL_PASSWORD=""

# 先尝试无密码连接
mysql -u root -e "SELECT 1;" 2>/dev/null
if [ $? -ne 0 ]; then
    read -sp "Enter MySQL root password (press Enter if no password): " MYSQL_PASSWORD
    echo ""
fi

echo ""
echo "1. 检查数据库是否存在..."
echo "----------------------------------------"
if [ -z "$MYSQL_PASSWORD" ]; then
    mysql -u root -e "SHOW DATABASES LIKE '危化品简化数据库';" 2>/dev/null
else
    mysql -u root -p"$MYSQL_PASSWORD" -e "SHOW DATABASES LIKE '危化品简化数据库';" 2>/dev/null
fi

echo ""
echo "2. 列出数据库中的所有表..."
echo "----------------------------------------"
if [ -z "$MYSQL_PASSWORD" ]; then
    mysql -u root -e "USE \`危化品简化数据库\`; SHOW TABLES;" 2>/dev/null
else
    mysql -u root -p"$MYSQL_PASSWORD" -e "USE \`危化品简化数据库\`; SHOW TABLES;" 2>/dev/null
fi

echo ""
echo "3. 检查MSDS文档表是否存在..."
echo "----------------------------------------"
if [ -z "$MYSQL_PASSWORD" ]; then
    mysql -u root -e "USE \`危化品简化数据库\`; SHOW TABLES LIKE 'MSDS文档';" 2>/dev/null
    TABLE_EXISTS=$(mysql -u root -e "USE \`危化品简化数据库\`; SHOW TABLES LIKE 'MSDS文档';" 2>/dev/null | grep -c "MSDS文档")
else
    mysql -u root -p"$MYSQL_PASSWORD" -e "USE \`危化品简化数据库\`; SHOW TABLES LIKE 'MSDS文档';" 2>/dev/null
    TABLE_EXISTS=$(mysql -u root -p"$MYSQL_PASSWORD" -e "USE \`危化品简化数据库\`; SHOW TABLES LIKE 'MSDS文档';" 2>/dev/null | grep -c "MSDS文档")
fi

if [ "$TABLE_EXISTS" -eq 0 ]; then
    echo "❌ MSDS文档表不存在！"
    echo ""
    echo "4. 列出所有表名（检查表名是否正确）..."
    echo "----------------------------------------"
    if [ -z "$MYSQL_PASSWORD" ]; then
        mysql -u root -e "USE \`危化品简化数据库\`; SHOW TABLES;" 2>/dev/null
    else
        mysql -u root -p"$MYSQL_PASSWORD" -e "USE \`危化品简化数据库\`; SHOW TABLES;" 2>/dev/null
    fi
else
    echo "✅ MSDS文档表存在"
    echo ""
    echo "4. 查看MSDS文档表结构..."
    echo "----------------------------------------"
    if [ -z "$MYSQL_PASSWORD" ]; then
        mysql -u root -e "USE \`危化品简化数据库\`; DESCRIBE \`MSDS文档\`;" 2>/dev/null
    else
        mysql -u root -p"$MYSQL_PASSWORD" -e "USE \`危化品简化数据库\`; DESCRIBE \`MSDS文档\`;" 2>/dev/null
    fi
fi

echo ""
echo "5. 查看所有表的详细信息..."
echo "----------------------------------------"
if [ -z "$MYSQL_PASSWORD" ]; then
    mysql -u root -e "USE \`危化品简化数据库\`; SELECT TABLE_NAME, TABLE_ROWS, DATA_LENGTH, INDEX_LENGTH FROM information_schema.TABLES WHERE TABLE_SCHEMA = '危化品简化数据库';" 2>/dev/null
else
    mysql -u root -p"$MYSQL_PASSWORD" -e "USE \`危化品简化数据库\`; SELECT TABLE_NAME, TABLE_ROWS, DATA_LENGTH, INDEX_LENGTH FROM information_schema.TABLES WHERE TABLE_SCHEMA = '危化品简化数据库';" 2>/dev/null
fi

echo ""
echo "========================================================"
echo "检查完成！"
echo "========================================================"

