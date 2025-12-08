#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
构建语义搜索索引
一次性为所有化学品生成向量嵌入
"""

import pymysql
import sys
from semantic_search_engine import LocalSemanticSearchEngine

# 数据库配置（与app.py保持一致）
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '1234',  # 请修改为你的MySQL密码
    'database': '危化品简化数据库',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}


def get_all_chemicals():
    """从数据库获取所有化学品"""
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 查询所有化学品及其别名
        cursor.execute("""
            SELECT 
                c.编号,
                c.CAS号,
                c.中文名,
                c.英文名,
                c.分子式,
                c.EC编号,
                GROUP_CONCAT(a.别名 SEPARATOR '、') AS 所有别名
            FROM 化学品 c
            LEFT JOIN 化学品别名 a ON c.编号 = a.化学品编号
            GROUP BY c.编号, c.CAS号, c.中文名, c.英文名, c.分子式, c.EC编号
            ORDER BY c.编号
        """)
        
        chemicals = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return chemicals
    
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        print(f"   请检查:")
        print(f"   1. MySQL服务是否启动")
        print(f"   2. 数据库密码是否正确 (当前: {DB_CONFIG['password']})")
        print(f"   3. 数据库是否存在: {DB_CONFIG['database']}")
        sys.exit(1)


def main():
    """主函数"""
    print("=" * 70)
    print("🚀 语义搜索索引构建工具")
    print("=" * 70)
    print()
    
    # 1. 从数据库获取化学品
    print("📊 正在从数据库获取化学品数据...")
    chemicals = get_all_chemicals()
    
    if not chemicals:
        print("❌ 数据库中没有化学品数据")
        print("   请先导入化学品数据")
        sys.exit(1)
    
    print(f"✅ 获取到 {len(chemicals)} 个化学品")
    print()
    
    # 显示前3个化学品示例
    print("📝 数据示例:")
    for i, chem in enumerate(chemicals[:3], 1):
        print(f"   {i}. {chem['中文名']} (CAS: {chem['CAS号']})")
        if chem['所有别名']:
            print(f"      别名: {chem['所有别名']}")
    print()
    
    # 2. 初始化语义搜索引擎
    print("🤖 正在初始化语义搜索引擎...")
    print("   (首次运行会下载模型，约420MB，请耐心等待)")
    print()
    
    try:
        engine = LocalSemanticSearchEngine()
    except ImportError as e:
        print("❌ 缺少依赖库")
        print("   请运行: pip install sentence-transformers scikit-learn")
        sys.exit(1)
    
    # 3. 构建索引
    print()
    engine.build_index(chemicals, batch_size=32)
    
    # 4. 显示统计信息
    print()
    stats = engine.get_stats()
    print("📊 索引统计:")
    print(f"   化学品数量: {stats['total_chemicals']}")
    print(f"   模型: {stats['model_name']}")
    print(f"   向量维度: {stats['embedding_dimension']}")
    print(f"   缓存大小: {stats['cache_size_mb']:.2f} MB")
    print()
    
    # 5. 测试搜索
    print("=" * 70)
    print("🧪 测试搜索功能")
    print("=" * 70)
    print()
    
    test_queries = [
        "易燃液体",
        "有毒化学品",
        "酒精"
    ]
    
    for query in test_queries:
        print(f"🔍 测试查询: {query}")
        results = engine.search(query, top_k=3)
        
        if results:
            for i, result in enumerate(results, 1):
                print(f"   {i}. {result['name']} (CAS: {result['cas']}) - 相似度: {result['score']:.3f}")
        else:
            print("   未找到结果")
        print()
    
    print("=" * 70)
    print("✅ 索引构建完成！")
    print("=" * 70)
    print()
    print("💡 使用方法:")
    print("   1. 在 app.py 中导入: from semantic_search_engine import LocalSemanticSearchEngine")
    print("   2. 初始化引擎: engine = LocalSemanticSearchEngine()")
    print("   3. 搜索: results = engine.search('易燃液体', top_k=10)")
    print()


if __name__ == '__main__':
    main()
