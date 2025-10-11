"""
数据库连接测试脚本
用于验证数据库配置是否正确
"""

import pymysql
import sys

# ============================================
# 配置区域 - 请修改为你的数据库配置
# ============================================
DB_CONFIG = {
    'host': 'localhost',              # 数据库主机地址
    'user': 'root',                   # 数据库用户名
    'password': '1234',               # 数据库密码
    'database': '危化品简化数据库',    # 数据库名称
    'charset': 'utf8mb4'
}

def test_connection():
    """测试数据库连接"""
    print("=" * 60)
    print("🔍 数据库连接测试")
    print("=" * 60)
    print(f"📍 主机地址: {DB_CONFIG['host']}")
    print(f"👤 用户名: {DB_CONFIG['user']}")
    print(f"💾 数据库: {DB_CONFIG['database']}")
    print("=" * 60)
    
    try:
        print("\n🔌 正在连接数据库...")
        conn = pymysql.connect(**DB_CONFIG)
        print("✅ 数据库连接成功！\n")
        
        cursor = conn.cursor()
        
        # 测试1：查看表
        print("📋 测试1: 查看数据库表")
        print("-" * 60)
        cursor.execute("SHOW TABLES;")
        tables = cursor.fetchall()
        
        if len(tables) == 0:
            print("⚠️  警告: 数据库中没有表，请执行初始化脚本")
            print("   运行命令: mysql -u root -p < new_db/init_simple_db.sql")
        else:
            print(f"✅ 找到 {len(tables)} 个表:")
            for table in tables:
                print(f"   - {table[0]}")
        
        # 测试2：查看化学品数量
        print(f"\n📊 测试2: 查看数据统计")
        print("-" * 60)
        
        expected_tables = ['化学品', '化学品别名', 'MSDS文档', 'MSDS章节']
        
        for table_name in expected_tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
                count = cursor.fetchone()[0]
                status = "✅" if count > 0 else "⚠️ "
                print(f"   {status} {table_name}: {count} 条记录")
            except pymysql.err.ProgrammingError:
                print(f"   ❌ {table_name}: 表不存在")
        
        # 测试3：测试查询功能
        print(f"\n🔍 测试3: 测试查询功能")
        print("-" * 60)
        
        cursor.execute("SELECT COUNT(*) FROM 化学品;")
        chem_count = cursor.fetchone()[0]
        
        if chem_count > 0:
            cursor.execute("SELECT 中文名, CAS号, 英文名 FROM 化学品 LIMIT 3;")
            chemicals = cursor.fetchall()
            print(f"✅ 查询成功，显示前3个化学品:")
            for chem in chemicals:
                print(f"   - {chem[0]} ({chem[1]}) - {chem[2]}")
        else:
            print("⚠️  数据库为空，请先导入化学品数据")
            print("   使用命令: python scrape_to_json.py \"URL\" --import")
        
        # 测试4：测试存储过程
        print(f"\n🔧 测试4: 测试存储过程")
        print("-" * 60)
        
        cursor.execute("SHOW PROCEDURE STATUS WHERE Db = %s;", (DB_CONFIG['database'],))
        procedures = cursor.fetchall()
        
        if len(procedures) > 0:
            print(f"✅ 找到 {len(procedures)} 个存储过程:")
            for proc in procedures:
                print(f"   - {proc[1]}")
        else:
            print("⚠️  未找到存储过程，请检查初始化脚本是否完整执行")
        
        cursor.close()
        conn.close()
        
        print("\n" + "=" * 60)
        print("✅ 所有测试完成！数据库配置正常")
        print("=" * 60)
        print("\n💡 下一步:")
        print("   1. 启动Web应用: python app.py")
        print("   2. 导入化学品数据: python scrape_to_json.py \"URL\" --import")
        print("   3. 访问Web界面: http://localhost:5001\n")
        
        return True
        
    except pymysql.err.OperationalError as e:
        print(f"\n❌ 连接失败: {e}\n")
        
        print("🔧 故障排查建议:")
        print("-" * 60)
        
        if "Access denied" in str(e):
            print("❌ 用户名或密码错误")
            print("   - 检查 DB_CONFIG 中的 user 和 password")
            print("   - 确认MySQL用户是否存在:")
            print("     mysql> SELECT user, host FROM mysql.user;")
            
        elif "Unknown database" in str(e):
            print("❌ 数据库不存在")
            print("   - 执行初始化脚本创建数据库:")
            print("     mysql -u root -p < new_db/init_simple_db.sql")
            print("   - 或手动创建:")
            print("     mysql> CREATE DATABASE 危化品简化数据库 CHARACTER SET utf8mb4;")
            
        elif "Can't connect" in str(e) or "Connection refused" in str(e):
            print("❌ 无法连接到数据库服务器")
            print("   - 检查MySQL服务是否启动:")
            print("     Windows: net start mysql")
            print("     Linux: systemctl status mysql")
            print("   - 检查主机地址是否正确")
            print("   - 检查端口3306是否开放")
            
        elif "timed out" in str(e):
            print("❌ 连接超时")
            print("   - 检查网络连接")
            print("   - 检查防火墙规则")
            print("   - 如果是远程连接，检查MySQL配置:")
            print("     bind-address = 0.0.0.0")
            
        else:
            print(f"❌ 未知错误: {e}")
            print("   - 检查数据库配置是否完整")
            print("   - 查看MySQL错误日志")
        
        print("\n💡 配置文件位置:")
        print("   - Web应用配置: new_db/app.py (第21-28行)")
        print("   - 测试脚本配置: new_db/test_db.py (第10-16行)")
        print("   - 详细说明: new_db/部署配置说明.md\n")
        
        return False
        
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        print(f"   错误类型: {type(e).__name__}\n")
        return False

if __name__ == "__main__":
    print("\n")
    success = test_connection()
    print("\n")
    
    sys.exit(0 if success else 1)

