#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MSDS数据导入脚本 - 将爬取的HTML数据导入数据库

功能：
1. 读取爬取的MSDS HTML文件
2. 解析并清理HTML内容
3. 插入到数据库的MSDS章节表
4. 支持批量导入

使用方法：
    python import_msds_to_db.py --folder msds_甲苯 --cas 108-88-3
    
作者：AI Assistant
日期：2025-10-10
"""

import pymysql
import os
import argparse
from bs4 import BeautifulSoup
from pathlib import Path
import json
import re

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '123456',  # 修改为你的密码
    'database': '危化品数据库',
    'charset': 'utf8mb4'
}

# MSDS 16个部分的标题映射
MSDS_PARTS = {
    1: '化学品及企业标识',
    2: '危险性概述',
    3: '成分/组成信息',
    4: '急救措施',
    5: '消防措施',
    6: '泄漏应急处理',
    7: '操作处置与储存',
    8: '接触控制/个体防护',
    9: '理化特性',
    10: '稳定性和反应性',
    11: '毒理学信息',
    12: '生态学信息',
    13: '废弃处置',
    14: '运输信息',
    15: '法规信息',
    16: '其他信息'
}


def extract_chemical_info_from_html(folder_path):
    """
    从MSDS文件夹的01_化学品及企业标识.html中自动提取化学品信息
    
    参数:
        folder_path: MSDS文件夹路径
        
    返回:
        dict: 化学品信息 {'中文名': '', 'CAS号': '', '英文名': '', '分子式': '', 'EC编号': ''}
    """
    # 查找01_化学品及企业标识.html文件
    pattern = "01_*.html"
    html_files = list(Path(folder_path).glob(pattern))
    
    if not html_files:
        return None
    
    html_path = html_files[0]
    
    try:
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        info = {}
        
        # 提取化学品信息（根据HTML结构）
        # 查找所有class="mdp"的p标签（字段名）和其后的p标签（值）
        mdp_tags = soup.find_all('p', class_='mdp')
        
        for mdp in mdp_tags:
            field_name = mdp.get_text(strip=True)
            # 获取下一个p标签的内容
            next_p = mdp.find_next_sibling('p')
            if next_p:
                value = next_p.get_text(strip=True)
                
                # 映射字段
                if '产品中文名称' in field_name or '中文名' in field_name:
                    info['中文名'] = value
                elif 'CAS' in field_name.upper():
                    info['CAS号'] = value
                elif '产品英文名称' in field_name or '英文名' in field_name:
                    # 如果有多个英文名，取第一个
                    info['英文名'] = value.split('|')[0] if '|' in value else value
                elif '分子式' in field_name:
                    info['分子式'] = value
                elif 'EC' in field_name.upper():
                    info['EC编号'] = value
        
        return info
        
    except Exception as e:
        print(f"⚠ 提取化学品信息失败: {e}")
        return None


def parse_html_content(html_path):
    """
    解析HTML文件，提取纯文本和结构化数据
    
    参数:
        html_path: HTML文件路径
        
    返回:
        tuple: (纯文本内容, 结构化JSON数据)
    """
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 移除script和style标签
    for tag in soup(['script', 'style']):
        tag.decompose()
    
    # 提取纯文本
    text = soup.get_text(separator='\n', strip=True)
    
    # 尝试提取结构化数据（表格等）
    structured_data = {}
    
    # 提取表格数据
    tables = soup.find_all('table')
    if tables:
        table_data = []
        for table in tables:
            rows = []
            for tr in table.find_all('tr'):
                cells = [td.get_text(strip=True) for td in tr.find_all(['td', 'th'])]
                if cells:
                    rows.append(cells)
            if rows:
                table_data.append(rows)
        if table_data:
            structured_data['tables'] = table_data
    
    # 提取列表数据
    lists = soup.find_all(['ul', 'ol'])
    if lists:
        list_data = []
        for lst in lists:
            items = [li.get_text(strip=True) for li in lst.find_all('li')]
            if items:
                list_data.append(items)
        if list_data:
            structured_data['lists'] = list_data
    
    # 保存原始HTML（可选）
    structured_data['original_html'] = html_content
    
    return text, json.dumps(structured_data, ensure_ascii=False)


def get_chemical_id_by_cas(cursor, cas_number):
    """
    根据CAS号查询化学品ID
    
    参数:
        cursor: 数据库游标
        cas_number: CAS号
        
    返回:
        int: 化学品ID，如果不存在则返回None
    """
    cursor.execute("SELECT 编号 FROM 化学品 WHERE CAS号 = %s", (cas_number,))
    result = cursor.fetchone()
    return result[0] if result else None


def create_chemical(cursor, chem_info):
    """
    创建化学品记录
    
    参数:
        cursor: 数据库游标
        chem_info: 化学品信息字典
        
    返回:
        int: 新创建的化学品ID
    """
    cursor.execute("""
        INSERT INTO 化学品 (CAS号, 中文名, 英文名, 分子式, EC编号) 
        VALUES (%s, %s, %s, %s, %s)
    """, (
        chem_info.get('CAS号'),
        chem_info.get('中文名'),
        chem_info.get('英文名'),
        chem_info.get('分子式'),
        chem_info.get('EC编号')
    ))
    
    return cursor.lastrowid


def get_or_create_msds_doc(cursor, chemical_id):
    """
    获取或创建MSDS文档记录
    
    参数:
        cursor: 数据库游标
        chemical_id: 化学品ID
        
    返回:
        int: MSDS文档ID
    """
    # 检查是否已存在
    cursor.execute("SELECT 编号 FROM MSDS文档 WHERE 化学品编号 = %s", (chemical_id,))
    result = cursor.fetchone()
    
    if result:
        return result[0]
    
    # 创建新记录
    cursor.execute("""
        INSERT INTO MSDS文档 (化学品编号, 编制单位, 编制依据) 
        VALUES (%s, '合规化学网', 'GB/T 16483, GB/T 17519')
    """, (chemical_id,))
    
    return cursor.lastrowid


def import_msds_chapter(cursor, doc_id, chapter_num, title, content_text, structured_json):
    """
    导入MSDS章节数据
    
    参数:
        cursor: 数据库游标
        doc_id: MSDS文档ID
        chapter_num: 章节序号（1-16）
        title: 章节标题
        content_text: 纯文本内容
        structured_json: 结构化JSON数据
    """
    # 检查是否已存在该章节
    cursor.execute("""
        SELECT 编号 FROM MSDS章节 
        WHERE 文档编号 = %s AND 章节序号 = %s
    """, (doc_id, chapter_num))
    
    existing = cursor.fetchone()
    
    if existing:
        # 更新
        cursor.execute("""
            UPDATE MSDS章节 
            SET 章节标题 = %s, 内容 = %s, 结构化数据 = %s, 更新时间 = NOW()
            WHERE 编号 = %s
        """, (title, content_text, structured_json, existing[0]))
        print(f"  更新章节 {chapter_num:02d}: {title}")
    else:
        # 插入
        cursor.execute("""
            INSERT INTO MSDS章节 
            (文档编号, 章节序号, 章节标题, 内容, 结构化数据) 
            VALUES (%s, %s, %s, %s, %s)
        """, (doc_id, chapter_num, title, content_text, structured_json))
        print(f"  插入章节 {chapter_num:02d}: {title}")


def import_msds_folder(folder_path, cas_number=None):
    """
    导入整个MSDS文件夹的数据到数据库
    
    参数:
        folder_path: MSDS文件夹路径
        cas_number: 化学品CAS号（可选，如果不提供则自动从HTML提取）
        
    返回:
        bool: 是否成功
    """
    print("=" * 70)
    print("MSDS数据导入工具 - 智能版")
    print("=" * 70)
    print(f"文件夹: {folder_path}")
    print("=" * 70)
    print()
    
    # 如果没有提供CAS号，自动从HTML提取
    if not cas_number:
        print("📍 步骤1：自动识别化学品信息...")
        chem_info = extract_chemical_info_from_html(folder_path)
        
        if not chem_info or not chem_info.get('CAS号'):
            print("❌ 无法从HTML文件中提取化学品信息")
            print("提示: 请确保文件夹中包含 01_化学品及企业标识.html")
            return False
        
        cas_number = chem_info['CAS号']
        print(f"✓ 化学品名称: {chem_info.get('中文名', '未知')}")
        print(f"✓ CAS号: {cas_number}")
        if chem_info.get('英文名'):
            print(f"✓ 英文名: {chem_info.get('英文名')}")
        if chem_info.get('分子式'):
            print(f"✓ 分子式: {chem_info.get('分子式')}")
        print()
    else:
        print(f"CAS号: {cas_number}")
        print()
        chem_info = None
    
    # 连接数据库
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        print("✓ 数据库连接成功")
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return False
    
    try:
        # 查询化学品ID
        chemical_id = get_chemical_id_by_cas(cursor, cas_number)
        
        if not chemical_id:
            # 如果不存在且有化学品信息，自动创建
            if chem_info:
                print(f"⚠ 数据库中未找到该化学品，自动创建...")
                chemical_id = create_chemical(cursor, chem_info)
                conn.commit()
                print(f"✓ 已创建化学品记录，ID: {chemical_id}")
            else:
                print(f"❌ 找不到CAS号为 {cas_number} 的化学品")
                print("提示: 请先在数据库中添加该化学品的基本信息")
                return False
        else:
            print(f"✓ 找到化学品ID: {chemical_id}")
        
        # 获取或创建MSDS文档
        doc_id = get_or_create_msds_doc(cursor, chemical_id)
        print(f"✓ MSDS文档ID: {doc_id}")
        print()
        
        # 遍历16个部分
        success_count = 0
        for chapter_num in range(1, 17):
            # 查找对应的HTML文件
            pattern = f"{chapter_num:02d}_*.html"
            html_files = list(Path(folder_path).glob(pattern))
            
            if not html_files:
                print(f"⚠ 跳过章节 {chapter_num:02d}: 文件不存在")
                continue
            
            html_path = html_files[0]
            title = MSDS_PARTS.get(chapter_num, f"第{chapter_num}部分")
            
            try:
                # 解析HTML
                content_text, structured_json = parse_html_content(html_path)
                
                # 导入数据库
                import_msds_chapter(
                    cursor, doc_id, chapter_num, 
                    title, content_text, structured_json
                )
                
                success_count += 1
                
            except Exception as e:
                print(f"  ❌ 处理失败: {e}")
        
        # 提交事务
        conn.commit()
        
        print()
        print("=" * 70)
        print(f"导入完成! 成功导入 {success_count}/16 个章节")
        print("=" * 70)
        
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"❌ 导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        cursor.close()
        conn.close()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='将爬取的MSDS数据导入数据库 - 智能版',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 自动识别模式（推荐）⭐
  python import_msds_to_db.py --folder msds_甲苯
  
  # 手动指定CAS号
  python import_msds_to_db.py --folder msds_甲苯 --cas 108-88-3
  
  # 指定数据库密码
  python import_msds_to_db.py -f msds_乙醇无水 -p 你的密码
  
功能说明:
  ✓ 自动从HTML文件提取化学品信息（名称、CAS号、分子式等）
  ✓ 如果数据库中不存在该化学品，自动创建
  ✓ 自动创建或更新MSDS文档和16个章节
  ✓ 完全智能化，只需指定文件夹即可！
  
注意:
  - 文件夹中应包含 01_*.html 到 16_*.html 的文件
  - 如果不提供CAS号，将从01_化学品及企业标识.html中自动提取
        """
    )
    
    parser.add_argument(
        '--folder', '-f',
        required=True,
        help='MSDS文件夹路径（包含16个HTML文件）'
    )
    
    parser.add_argument(
        '--cas', '-c',
        required=False,
        help='化学品CAS号（可选，不提供则自动提取）'
    )
    
    parser.add_argument(
        '--password', '-p',
        default='123456',
        help='数据库密码（默认: 123456）'
    )
    
    args = parser.parse_args()
    
    # 更新数据库密码
    DB_CONFIG['password'] = args.password
    
    # 检查文件夹是否存在
    if not os.path.isdir(args.folder):
        print(f"❌ 文件夹不存在: {args.folder}")
        return 1
    
    # 导入数据（CAS号可选）
    success = import_msds_folder(args.folder, args.cas)
    
    return 0 if success else 1


if __name__ == "__main__":
    import sys
    
    # 检查依赖
    try:
        import pymysql
        from bs4 import BeautifulSoup
    except ImportError:
        print("❌ 缺少依赖库！")
        print("请运行: pip install pymysql beautifulsoup4")
        sys.exit(1)
    
    sys.exit(main())

