#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试AI化学品兼容性分析功能
"""

import pymysql
from ai_analyzer import analyze_compatibility_with_ai, extract_chapter_summary

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '1234',
    'database': '危化品简化数据库',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

def get_db_connection():
    return pymysql.connect(**DB_CONFIG)

def extract_incompatible_substances(content):
    """从第10章内容中提取不相容物质"""
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
    """从第2章提取GHS分类"""
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

def main():
    """测试AI分析功能"""
    print("=" * 70)
    print("🤖 AI化学品兼容性分析测试")
    print("=" * 70)
    print()
    
    # 测试化学品：甲醛和丙醇
    test_keywords = ['甲醛', '丙醇']
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        chemicals_data = []
        
        for keyword in test_keywords:
            # 查找化学品
            cursor.execute("""
                SELECT 编号 FROM 化学品 
                WHERE 中文名 LIKE %s OR CAS号 = %s
                LIMIT 1
            """, (f'%{keyword}%', keyword))
            
            result = cursor.fetchone()
            if not result:
                print(f"❌ 未找到化学品: {keyword}")
                continue
            
            chemical_id = result['编号']
            
            # 获取基本信息
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
            
            # 获取第2章
            cursor.execute("""
                SELECT s.内容
                FROM MSDS文档 d
                JOIN MSDS章节 s ON d.编号 = s.文档编号
                WHERE d.化学品编号 = %s AND s.章节序号 = 2
            """, (chemical_id,))
            
            chapter2 = cursor.fetchone()
            chapter2_content = chapter2['内容'] if chapter2 else ''
            
            # 获取第10章
            cursor.execute("""
                SELECT s.内容
                FROM MSDS文档 d
                JOIN MSDS章节 s ON d.编号 = s.文档编号
                WHERE d.化学品编号 = %s AND s.章节序号 = 10
            """, (chemical_id,))
            
            chapter10 = cursor.fetchone()
            chapter10_content = chapter10['内容'] if chapter10 else ''
            
            # 提取关键信息
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
        
        if len(chemicals_data) < 2:
            print("❌ 未找到足够的化学品数据")
            return
        
        print()
        print("=" * 70)
        print("🚀 开始AI分析...")
        print("=" * 70)
        print()
        
        # 调用AI分析
        result = analyze_compatibility_with_ai(chemicals_data)
        
        if not result['success']:
            print(f"❌ AI分析失败: {result['error']}")
            return
        
        report = result['report']
        
        # 显示分析结果
        print("📊 AI分析报告")
        print("=" * 70)
        print()
        
        print(f"【总结】{report.get('summary', 'N/A')}")
        print()
        
        print("【共存安全性评估】")
        print(f"  风险等级: {report['compatibility']['risk_level']}")
        print(f"  风险评分: {report['compatibility']['risk_score']}/100")
        print(f"  可否共存: {'✅ 可以' if report['compatibility']['can_coexist'] else '❌ 不建议'}")
        print()
        
        if report['compatibility'].get('incompatible_reasons'):
            print("【不相容原因】")
            for i, reason in enumerate(report['compatibility']['incompatible_reasons'], 1):
                print(f"  {i}. {reason}")
            print()
        
        if report['compatibility'].get('specific_risks'):
            print("【具体风险】")
            for i, risk in enumerate(report['compatibility']['specific_risks'], 1):
                print(f"  {i}. {risk}")
            print()
        
        print("【化学品对比】")
        print("  相同点:")
        for i, sim in enumerate(report['comparison']['similarities'], 1):
            print(f"    {i}. {sim}")
        print("  不同点:")
        for i, diff in enumerate(report['comparison']['differences'], 1):
            print(f"    {i}. {diff}")
        print()
        
        print("【推荐措施】")
        print("  存储建议:")
        for i, rec in enumerate(report['recommendations']['storage'], 1):
            print(f"    {i}. {rec}")
        print("  操作建议:")
        for i, rec in enumerate(report['recommendations']['handling'], 1):
            print(f"    {i}. {rec}")
        print("  应急措施:")
        for i, rec in enumerate(report['recommendations']['emergency'], 1):
            print(f"    {i}. {rec}")
        print()
        
        if 'usage' in result:
            usage = result['usage']
            print("=" * 70)
            print(f"💰 Token消耗: {usage.get('total_tokens', 0)} " +
                  f"(输入: {usage.get('prompt_tokens', 0)}, 输出: {usage.get('completion_tokens', 0)})")
            print("=" * 70)
        
    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()

