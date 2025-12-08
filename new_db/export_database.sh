#!/bin/bash
# 导出数据库脚本 - 在本地Windows电脑上运行

echo "正在导出数据库..."
echo ""

# 使用mysqldump导出数据库
# 请根据你的MySQL配置修改用户名和密码
# --hex-blob 选项将二进制数据转换为十六进制格式，避免导入时的编码问题
mysqldump -u root -p1234 --default-character-set=utf8mb4 \
    --single-transaction \
    --routines \
    --triggers \
    --hex-blob \
    "危化品简化数据库" > database_backup.sql

if [ $? -eq 0 ]; then
    echo "✅ 数据库导出成功！"
    echo "文件: database_backup.sql"
    echo ""
    echo "文件大小:"
    ls -lh database_backup.sql
else
    echo "❌ 数据库导出失败！"
    exit 1
fi

