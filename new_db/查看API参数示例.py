#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查看实际传给AI API的参数
"""

import pymysql
from ai_analyzer import construct_compatibility_prompt, extract_chapter_summary
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
    print("=" * 80)
    print("📤 查看实际传给AI API的参数")
    print("=" * 80)
    print()
    
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    # 查询甲醛和丙醇
    test_chemicals = ['甲醛', '丙醇']
    chemicals_data = []
    
    for keyword in test_chemicals:
        cursor.execute("""
            SELECT 编号 FROM 化学品 
            WHERE 中文名 LIKE %s 
            LIMIT 1
        """, (f'%{keyword}%',))
        
        result = cursor.fetchone()
        if not result:
            continue
        
        chem_id = result['编号']
        
        # 获取基本信息
        cursor.execute("""
            SELECT 
                c.编号, c.CAS号, c.中文名, c.英文名, c.分子式,
                GROUP_CONCAT(a.别名 SEPARATOR '、') AS 所有别名
            FROM 化学品 c
            LEFT JOIN 化学品别名 a ON c.编号 = a.化学品编号
            WHERE c.编号 = %s
            GROUP BY c.编号, c.CAS号, c.中文名, c.英文名, c.分子式
        """, (chem_id,))
        
        basic = cursor.fetchone()
        
        # 获取第2章
        cursor.execute("""
            SELECT s.内容
            FROM MSDS文档 d
            JOIN MSDS章节 s ON d.编号 = s.文档编号
            WHERE d.化学品编号 = %s AND s.章节序号 = 2
        """, (chem_id,))
        
        chapter2 = cursor.fetchone()
        chapter2_content = chapter2['内容'] if chapter2 else ''
        
        # 获取第10章
        cursor.execute("""
            SELECT s.内容
            FROM MSDS文档 d
            JOIN MSDS章节 s ON d.编号 = s.文档编号
            WHERE d.化学品编号 = %s AND s.章节序号 = 10
        """, (chem_id,))
        
        chapter10 = cursor.fetchone()
        chapter10_content = chapter10['内容'] if chapter10 else ''
        
        # 提取关键信息
        incompatible = extract_incompatible_substances(chapter10_content)
        ghs_categories = extract_ghs_categories(chapter2_content)
        
        chemicals_data.append({
            'id': basic['编号'],
            'name': basic['中文名'],
            'cas': basic['CAS号'],
            'formula': basic['分子式'],
            'aliases': basic.get('所有别名', ''),
            'incompatible': incompatible,
            'ghs_categories': ghs_categories,
            'chapter2_summary': extract_chapter_summary(chapter2_content, 300),
            'chapter10_summary': extract_chapter_summary(chapter10_content, 300)
        })
    
    cursor.close()
    conn.close()
    
    print("【1. 化学品数据对象】")
    print("=" * 80)
    print(json.dumps(chemicals_data, ensure_ascii=False, indent=2))
    print()
    
    print("【2. 构建的完整Prompt】")
    print("=" * 80)
    prompt = construct_compatibility_prompt(chemicals_data)
    print(prompt)
    print()
    
    print("【3. 发送给硅基流动API的完整payload】")
    print("=" * 80)
    api_payload = {
        "model": "Qwen/Qwen2.5-7B-Instruct",
        "messages": [
            {
                "role": "system",
                "content": "你是专业的化学品安全分析专家，擅长分析化学品的共存安全性。你必须严格按照JSON格式输出分析结果。"
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.3,
        "max_tokens": 2000,
        "stream": False
    }
    
    # 不打印完整内容（太长），只显示结构
    print(f"模型: {api_payload['model']}")
    print(f"温度: {api_payload['temperature']}")
    print(f"最大tokens: {api_payload['max_tokens']}")
    print(f"消息数量: {len(api_payload['messages'])}")
    print(f"System消息: {api_payload['messages'][0]['content'][:50]}...")
    print(f"User消息长度: {len(api_payload['messages'][1]['content'])} 字符")
    print()
    
    # 估算Token数量
    total_chars = len(api_payload['messages'][0]['content']) + len(api_payload['messages'][1]['content'])
    estimated_tokens = total_chars // 2  # 粗略估算：中文约2字符=1token
    print(f"📊 预估输入Token: ~{estimated_tokens}")
    print(f"📊 预估总Token: ~{estimated_tokens + 300} (含输出)")
    print()
    
    print("=" * 80)
    print("✅ 参数查看完成！")
    print("=" * 80)

if __name__ == '__main__':
    main()

