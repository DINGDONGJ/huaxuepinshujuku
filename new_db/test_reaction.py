#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试会发生化学反应的化学品组合
"""

import pymysql
from ai_analyzer import analyze_compatibility_with_ai, extract_chapter_summary
import json

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '1234',
    'database': '危化品简化数据库',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

def extract_incompatible_substances(content):
    if not content:
        return []
    import re
    incompatible = []
    lines = content.split('\n')
    for i, line in enumerate(lines):
        line = line.strip()
        if re.search(r'禁配物|不相容[的]?物质|应避免[与]?接触[的]?物质', line, re.IGNORECASE):
            match = re.search(r'[：:]\s*(.+)', line)
            if match:
                substances_str = match.group(1).strip()
            elif i + 1 < len(lines):
                substances_str = lines[i + 1].strip()
            else:
                continue
            if substances_str:
                substances = re.split(r'[、,，;；/和与]+', substances_str)
                for substance in substances:
                    substance = substance.strip()
                    substance = re.sub(r'[。，,;；]$', '', substance)
                    if substance and len(substance) > 1 and substance not in ['无', '未明确', '无数据']:
                        incompatible.append(substance)
    return list(set(incompatible))

def extract_ghs_categories(content):
    if not content:
        return []
    categories = []
    ghs_keywords = [
        '易燃液体', '易燃气体', '易燃固体', '爆炸物', '氧化性液体', 
        '氧化性固体', '氧化性气体', '加压气体', '自反应物质', 
        '自燃液体', '自燃固体', '自热物质', '遇水放出易燃气体',
        '有机过氧化物', '金属腐蚀物', '急性毒性', '皮肤腐蚀',
        '严重眼损伤', '呼吸道致敏', '皮肤致敏', '生殖细胞致突变',
        '致癌性', '生殖毒性', '特异性靶器官毒性', '吸入危害',
        '对水生环境的危害', '对臭氧层的危害'
    ]
    for keyword in ghs_keywords:
        if keyword in content:
            categories.append(keyword)
    return categories

def test_chemicals(keywords):
    """测试指定的化学品组合"""
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    chemicals_data = []
    
    for keyword in keywords:
        cursor.execute("""
            SELECT 编号 FROM 化学品 
            WHERE 中文名 LIKE %s OR CAS号 = %s
            LIMIT 1
        """, (f'%{keyword}%', keyword))
        
        result = cursor.fetchone()
        if not result:
            print(f"❌ 未找到: {keyword}")
            continue
        
        chemical_id = result['编号']
        
        cursor.execute("""
            SELECT 
                c.编号, c.CAS号, c.中文名, c.英文名, c.分子式,
                GROUP_CONCAT(a.别名 SEPARATOR '、') AS 所有别名
            FROM 化学品 c
            LEFT JOIN 化学品别名 a ON c.编号 = a.化学品编号
            WHERE c.编号 = %s
            GROUP BY c.编号, c.CAS号, c.中文名, c.英文名, c.分子式
        """, (chemical_id,))
        
        basic_info = cursor.fetchone()
        
        cursor.execute("""
            SELECT s.内容
            FROM MSDS文档 d
            JOIN MSDS章节 s ON d.编号 = s.文档编号
            WHERE d.化学品编号 = %s AND s.章节序号 = 2
        """, (chemical_id,))
        chapter2 = cursor.fetchone()
        chapter2_content = chapter2['内容'] if chapter2 else ''
        
        cursor.execute("""
            SELECT s.内容
            FROM MSDS文档 d
            JOIN MSDS章节 s ON d.编号 = s.文档编号
            WHERE d.化学品编号 = %s AND s.章节序号 = 10
        """, (chemical_id,))
        chapter10 = cursor.fetchone()
        chapter10_content = chapter10['内容'] if chapter10 else ''
        
        incompatible = extract_incompatible_substances(chapter10_content)
        ghs_categories = extract_ghs_categories(chapter2_content)
        
        chemicals_data.append({
            'id': basic_info['编号'],
            'name': basic_info['中文名'],
            'cas': basic_info['CAS号'],
            'formula': basic_info['分子式'],
            'aliases': basic_info.get('所有别名', ''),
            'incompatible': incompatible,
            'ghs_categories': ghs_categories,
            'chapter2_summary': extract_chapter_summary(chapter2_content, 300),
            'chapter10_summary': extract_chapter_summary(chapter10_content, 300)
        })
        
        print(f"✅ 已加载: {basic_info['中文名']} ({basic_info['CAS号']})")
    
    cursor.close()
    conn.close()
    
    return chemicals_data

def main():
    print("=" * 80)
    print("⚗️ 测试化学反应方程式生成")
    print("=" * 80)
    print()
    
    # 测试可能发生反应的组合
    test_cases = [
        ['过氧化氢', '甲醇'],  # 氧化剂 + 醇类
        ['盐酸', '甲醛'],      # 酸 + 醛
    ]
    
    for i, keywords in enumerate(test_cases, 1):
        print(f"\n【测试案例{i}】{' + '.join(keywords)}")
        print("-" * 80)
        
        chemicals_data = test_chemicals(keywords)
        
        if len(chemicals_data) < 2:
            print("❌ 数据不足，跳过")
            continue
        
        print("\n🚀 开始AI分析...")
        result = analyze_compatibility_with_ai(chemicals_data)
        
        if not result['success']:
            print(f"❌ 分析失败: {result['error']}")
            continue
        
        report = result['report']
        
        print(f"\n📊 风险等级: {report['compatibility']['risk_level']}")
        print(f"💯 风险评分: {report['compatibility']['risk_score']}/100")
        
        # 重点查看化学反应
        if 'chemical_reactions' in report and report['chemical_reactions']:
            print(f"\n⚗️ 发现 {len(report['chemical_reactions'])} 个化学反应：")
            for j, reaction in enumerate(report['chemical_reactions'], 1):
                print(f"\n  反应{j}:")
                print(f"  方程式: {reaction.get('equation', 'N/A')}")
                print(f"  反应物: {', '.join(reaction.get('reactants', []))}")
                print(f"  生成物: {', '.join(reaction.get('products', []))}")
                print(f"  条件: {reaction.get('conditions', 'N/A')}")
                print(f"  剧烈程度: {reaction.get('danger_level', 'N/A')}")
                print(f"  说明: {reaction.get('description', 'N/A')}")
        else:
            print("\n✅ 无明显化学反应")
        
        print(f"\n💰 Token消耗: {result.get('usage', {}).get('total_tokens', 0)}")
        print("=" * 80)

if __name__ == '__main__':
    main()


