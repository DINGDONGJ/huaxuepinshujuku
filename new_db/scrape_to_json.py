#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MSDS智能爬虫 + JSON转换器 + 数据库导入工具
从第一部分提取完整化学品信息
"""

import requests
from bs4 import BeautifulSoup
import time
import sys
import os
import re
import json
import argparse
from datetime import datetime
import pymysql
from playwright.sync_api import sync_playwright
from urllib.parse import urljoin, urlparse
import hashlib

# MSDS 16个部分的映射
MSDS_PARTS = {
    1: "化学品及企业标识",
    2: "危险性概述",
    3: "成分/组成信息",
    4: "急救措施",
    5: "消防措施",
    6: "泄漏应急处理",
    7: "操作处置与储存",
    8: "接触控制/个体防护",
    9: "理化特性",
    10: "稳定性和反应性",
    11: "毒理学信息",
    12: "生态学信息",
    13: "废弃处置",
    14: "运输信息",
    15: "法规信息",
    16: "其他信息"
}


def extract_chemical_info(decrypt_url):
    """从第一部分提取完整的化学品信息和mid参数"""
    print("=" * 70)
    print("🔍 正在分析链接...")
    print("=" * 70)
    
    chinese_name = None
    cas_number = None
    english_name = None
    ec_number = None
    formula = None
    aliases = []
    mid = None
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            try:
                # 访问首页
                print("正在访问首页...")
                page.goto(decrypt_url, timeout=30000)
                page.wait_for_timeout(1500)
                
                # 点击第一部分
                print("正在点击第一部分...")
                clicked = False
                selectors = [
                    'text=第一部分',
                    'text=化学品及企业标识',
                    'div:has-text("第一部分 化学品及企业标识")'
                ]
                
                for selector in selectors:
                    try:
                        page.click(selector, timeout=5000)
                        clicked = True
                        print(f"✅ 成功点击：{selector}")
                        break
                    except:
                        continue
                
                if not clicked:
                    print("❌ 无法点击第一部分")
                    browser.close()
                    return None, None, None, None, None, None, None
                
                # 等待页面加载
                page.wait_for_timeout(2000)
                
                # 获取当前URL和页面内容
                current_url = page.url
                html_content = page.content()
                
                # 提取mid参数
                mid_match = re.search(r'[?&]mid=([^&]+)', current_url)
                if mid_match:
                    mid = mid_match.group(1)
                    print(f"✅ MID参数: {mid}")
                else:
                    print("❌ 未找到MID参数")
                
                # 解析第一部分的HTML
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # 提取所有 maincondetail div（包含标签-值对）
                main_divs = soup.find_all('div', class_='maincondetail')
                
                for div in main_divs:
                    paragraphs = div.find_all('p')
                    if len(paragraphs) >= 2:
                        label = paragraphs[0].get_text(strip=True)
                        value = paragraphs[1].get_text(strip=True)
                        
                        # 根据标签提取对应的值
                        if '中文名' in label:
                            chinese_name = value
                        elif '英文名' in label:
                            english_name = value
                        elif 'CAS' in label.upper():
                            cas_number = value
                        elif 'EC' in label.upper():
                            ec_number = value
                        elif '分子式' in label:
                            formula = value
                        elif '别名' in label:
                            # 别名可能有多个，用分隔符分开
                            if value and value.strip():
                                # 支持多种分隔符
                                alias_list = re.split(r'[,，、|；;]', value)
                                aliases = [a.strip() for a in alias_list if a.strip()]
                
                print()
                print("=" * 70)
                print("📊 提取结果:")
                print("=" * 70)
                print(f"✅ 化学品名称: {chinese_name or '未找到'}")
                print(f"✅ CAS号: {cas_number or '未找到'}")
                print(f"✅ 英文名: {english_name or '未找到'}")
                print(f"✅ EC编号: {ec_number or '未找到'}")
                print(f"✅ 分子式: {formula or '未找到'}")
                print(f"✅ 别名: {', '.join(aliases) if aliases else '未找到'}")
                print(f"✅ MID: {mid or '未找到'}")
                print()
                
            finally:
                browser.close()
        
        if not mid:
            print("❌ 无法获取MID，无法继续爬取")
            return None, None, None, None, None, None, None
        
        return chinese_name, cas_number, english_name, ec_number, formula, aliases, mid
        
    except Exception as e:
        print(f"❌ 提取信息失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return None, None, None, None, None, None, None


def download_image(img_url, output_dir, base_url):
    """下载图片并返回本地路径"""
    try:
        # 处理相对路径
        if not img_url.startswith('http'):
            img_url = urljoin(base_url, img_url)
        
        # 下载图片
        response = requests.get(img_url, timeout=10)
        if response.status_code != 200:
            return None
        
        # 生成文件名（使用URL的hash避免重复）
        url_hash = hashlib.md5(img_url.encode()).hexdigest()[:12]
        ext = os.path.splitext(urlparse(img_url).path)[1] or '.png'
        filename = f"{url_hash}{ext}"
        
        # 保存图片
        images_dir = os.path.join(output_dir, 'images')
        os.makedirs(images_dir, exist_ok=True)
        filepath = os.path.join(images_dir, filename)
        
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        # 返回相对路径
        return f"images/{filename}"
        
    except Exception as e:
        print(f"  ⚠️  图片下载失败: {str(e)}")
        return None


def scrape_msds_part(mid, part_num, output_dir='msds_json'):
    """爬取单个MSDS部分的内容和图片"""
    # 正确的URL格式：type参数从0开始（第1部分=type 0）
    url = f"http://www.hgmsds.com/weixin/msds-page-details?mid={mid}&type={part_num-1}&tid="
    base_url = "http://www.hgmsds.com"
    
    try:
        response = requests.get(url, timeout=15)
        response.encoding = 'utf-8'
        
        if response.status_code != 200:
            return None, []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 提取文本内容
        text_content = None
        content_div = soup.find('div', class_='maincontent')
        if content_div:
            text_content = content_div.get_text(separator='\n', strip=True)
        else:
            # 备用方法
            main_divs = soup.find_all('div', class_='maincondetail')
            if main_divs:
                content_parts = []
                for div in main_divs:
                    text = div.get_text(separator='\n', strip=True)
                    if text:
                        content_parts.append(text)
                if content_parts:
                    text_content = '\n\n'.join(content_parts)
        
        # 提取图片（重点关注第2部分和第14部分）
        images = []
        if part_num in [2, 14]:  # 第2部分（危险性概述）和第14部分（运输信息）
            img_tags = soup.find_all('img')
            temp_images = []
            
            for img in img_tags:
                img_src = img.get('src', '')
                img_alt = img.get('alt', '')
                
                # 跳过logo等无关图片
                if any(skip in img_src.lower() for skip in ['logo', 'qrcode', 'icon']):
                    continue
                
                # 下载图片
                local_path = download_image(img_src, output_dir, base_url)
                if local_path:
                    image_info = {
                        "url": local_path,
                        "alt": img_alt,
                        "type": "ghs" if part_num == 2 else "transport",
                        "original_url": img_src
                    }
                    temp_images.append(image_info)
            
            # 过滤二维码：排除最后一张图片（通常是二维码）
            if len(temp_images) > 1:
                images = temp_images[:-1]  # 只保留除了最后一张之外的所有图片
            else:
                images = temp_images
        
        return text_content, images
        
    except Exception as e:
        print(f"  ⚠️  请求失败: {str(e)}")
        return None, []


def scrape_to_json(url, output_dir='msds_json'):
    """爬取MSDS并生成JSON文件"""
    
    # 提取化学品信息
    result = extract_chemical_info(url)
    if result[0] is None:
        print("❌ 无法提取化学品信息，爬取失败")
        return None
    
    chinese_name, cas_number, english_name, ec_number, formula, aliases, mid = result
    
    if not mid:
        print("❌ 无法提取MID，爬取失败")
        return None
    
    # 使用化学品名称作为默认值
    if not chinese_name:
        chinese_name = f"化学品_{mid}"
    
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 开始爬取16个部分
    print("=" * 70)
    print("📥 开始爬取MSDS数据...")
    print("=" * 70)
    
    msds_chapters = []
    success_count = 0
    
    for part_num in range(1, 17):
        part_title = MSDS_PARTS[part_num]
        print(f"正在爬取: 第{part_num}部分 - {part_title}...", end=' ')
        
        content, images = scrape_msds_part(mid, part_num, output_dir)
        
        if content:
            chapter_data = {
                "章节序号": part_num,
                "章节标题": part_title,
                "内容": content
            }
            # 如果有图片，添加到数据中
            if images:
                chapter_data["图片"] = images
                print(f"✅ ({len(images)}张图片)")
            else:
                print("✅")
            msds_chapters.append(chapter_data)
            success_count += 1
        else:
            print("❌")
        
        # 延时，避免请求过快
        time.sleep(0.5)
    
    # 构建JSON数据结构
    msds_data = {
        "chemical_info": {
            "中文名": chinese_name,
            "英文名": english_name,
            "CAS号": cas_number,
            "分子式": formula,
            "EC编号": ec_number
        },
        "aliases": aliases if aliases else [],
        "msds_meta": {
            "编制单位": "合规化学网",
            "编制日期": datetime.now().strftime("%Y-%m-%d"),
            "编制依据": "GB/T 16483, GB/T 17519"
        },
        "msds_chapters": msds_chapters
    }
    
    # 保存JSON文件
    print()
    print("=" * 70)
    print("💾 正在保存JSON文件...")
    print("=" * 70)
    
    # 文件名：化学品名_CAS号（或MID）.json
    if cas_number:
        filename = f"{chinese_name}_{cas_number}.json"
    else:
        filename = f"{chinese_name}_{mid}.json"
    
    # 清理文件名中的非法字符
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    filepath = os.path.join(output_dir, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(msds_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ JSON文件已保存: {filepath}")
    print()
    print("📊 数据统计:")
    print(f"  - 化学品名称: {chinese_name}")
    print(f"  - CAS号: {cas_number or 'N/A'}")
    print(f"  - MSDS章节数: {success_count}/16")
    print(f"  - 别名数量: {len(aliases)}")
    print()
    
    if success_count < 16:
        print("⚠️  部分章节爬取失败，请检查网络连接或网站可用性")
    else:
        print("🎉 爬取完成！您可以在Web界面导入此JSON文件。")
    
    return filepath


def import_to_database(json_file, db_password='1234'):
    """导入JSON数据到数据库"""
    print("=" * 70)
    print("📤 正在导入数据库...")
    print("=" * 70)
    
    try:
        # 读取JSON文件
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        chem_info = data.get('chemical_info', {})
        aliases = data.get('aliases', [])
        msds_meta = data.get('msds_meta', {})
        chapters = data.get('msds_chapters', [])
        
        # 连接数据库
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password=db_password,
            database='危化品简化数据库',
            charset='utf8mb4'
        )
        cursor = conn.cursor()
        
        try:
            # 检查化学品是否已存在（通过CAS号或中文名）
            cas_number = chem_info.get('CAS号')
            chinese_name = chem_info.get('中文名')
            
            if cas_number:
                cursor.execute("SELECT 编号 FROM 化学品 WHERE CAS号 = %s", (cas_number,))
            else:
                cursor.execute("SELECT 编号 FROM 化学品 WHERE 中文名 = %s", (chinese_name,))
            
            existing = cursor.fetchone()
            
            if existing:
                chemical_id = existing[0]
                print(f"✅ 化学品已存在，更新数据（ID: {chemical_id}）")
                
                # 更新化学品信息
                cursor.execute("""
                    UPDATE 化学品 
                    SET 中文名 = %s, 英文名 = %s, 分子式 = %s, EC编号 = %s
                    WHERE 编号 = %s
                """, (
                    chinese_name,
                    chem_info.get('英文名'),
                    chem_info.get('分子式'),
                    chem_info.get('EC编号'),
                    chemical_id
                ))
                
                # 删除旧的别名和MSDS数据
                cursor.execute("DELETE FROM 化学品别名 WHERE 化学品编号 = %s", (chemical_id,))
                cursor.execute("DELETE FROM MSDS文档 WHERE 化学品编号 = %s", (chemical_id,))
            else:
                print("✅ 新增化学品")
                
                # 插入新化学品
                cursor.execute("""
                    INSERT INTO 化学品 (CAS号, 中文名, 英文名, 分子式, EC编号)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    cas_number,
                    chinese_name,
                    chem_info.get('英文名'),
                    chem_info.get('分子式'),
                    chem_info.get('EC编号')
                ))
                chemical_id = cursor.lastrowid
            
            # 插入别名
            for alias in aliases:
                cursor.execute("""
                    INSERT INTO 化学品别名 (化学品编号, 别名)
                    VALUES (%s, %s)
                """, (chemical_id, alias))
            
            # 插入MSDS文档
            cursor.execute("""
                INSERT INTO MSDS文档 (化学品编号, 编制单位, 编制日期, 编制依据)
                VALUES (%s, %s, %s, %s)
            """, (
                chemical_id,
                msds_meta.get('编制单位'),
                msds_meta.get('编制日期'),
                msds_meta.get('编制依据')
            ))
            msds_id = cursor.lastrowid
            
            # 插入MSDS章节
            print(f"✅ MSDS文档ID: {msds_id}")
            for chapter in chapters:
                # 处理图片数据
                images_json = None
                if '图片' in chapter and chapter['图片']:
                    images_json = json.dumps(chapter['图片'], ensure_ascii=False)
                
                cursor.execute("""
                    INSERT INTO MSDS章节 (文档编号, 章节序号, 章节标题, 内容, 图片JSON)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    msds_id,
                    chapter['章节序号'],
                    chapter['章节标题'],
                    chapter['内容'],
                    images_json
                ))
                print(f"  插入章节 {chapter['章节序号']:02d}: {chapter['章节标题']}")
            
            # 提交事务
            conn.commit()
            
            print()
            print("=" * 70)
            print("🎉 数据库导入成功！")
            print("=" * 70)
            print(f"化学品ID: {chemical_id}")
            print(f"别名数量: {len(aliases)}")
            print(f"MSDS章节: {len(chapters)}/16")
            print()
            
        except Exception as e:
            conn.rollback()
            print()
            print("=" * 70)
            print(f"❌ 数据库错误: {e}")
            print("=" * 70)
            print("可能的原因：")
            print("  1. 数据库未创建或未启动")
            print("  2. 数据库密码不正确")
            print("  3. 数据库名称不匹配")
            print()
            print("解决方法：")
            print("  1. 确保已运行 init_simple_db.sql 创建数据库")
            print("  2. 检查数据库密码（使用 --password 参数指定）")
            print()
            raise
        finally:
            cursor.close()
            conn.close()
            
    except FileNotFoundError:
        print(f"❌ 文件不存在: {json_file}")
        return False
    except json.JSONDecodeError:
        print(f"❌ JSON格式错误: {json_file}")
        return False
    except Exception as e:
        print(f"❌ 导入失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


def main():
    parser = argparse.ArgumentParser(
        description='MSDS智能爬虫 + 数据库导入工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  1. 只爬取，保存为JSON:
     python scrape_to_json.py "URL"
     
  2. 爬取并直接导入数据库:
     python scrape_to_json.py "URL" --import
     
  3. 指定数据库密码:
     python scrape_to_json.py "URL" --import --password yourpass
     
  4. 自定义输出目录:
     python scrape_to_json.py "URL" --output my_data
        """
    )
    
    parser.add_argument('url', nargs='?', help='MSDS页面URL（带decrypt参数）')
    parser.add_argument('--import', dest='do_import', action='store_true',
                        help='爬取后直接导入数据库')
    parser.add_argument('--password', '-p', default='1234',
                        help='数据库密码（默认：1234）')
    parser.add_argument('--output', '-o', default='msds_json',
                        help='JSON输出目录（默认：msds_json）')
    
    args = parser.parse_args()
    
    # 如果没有提供URL，进入交互模式
    if not args.url:
        print("=" * 70)
        print("MSDS智能爬虫 + 数据库导入工具")
        print("=" * 70)
        print()
        url = input("请输入MSDS页面URL: ").strip()
        if not url:
            print("❌ URL不能为空")
            return
        
        import_choice = input("是否直接导入数据库? (y/N): ").strip().lower()
        do_import = import_choice in ['y', 'yes']
        
        if do_import:
            db_password = input("数据库密码 (默认1234): ").strip() or '1234'
        else:
            db_password = '1234'
    else:
        url = args.url
        do_import = args.do_import
        db_password = args.password
    
    # 爬取数据
    json_file = scrape_to_json(url, args.output)
    
    if not json_file:
        print("❌ 爬取失败")
        sys.exit(1)
    
    # 如果需要导入数据库
    if do_import:
        success = import_to_database(json_file, db_password)
        if success:
            print("✅ 全部完成！")
        else:
            print()
            print("⚠️  JSON文件已保存，但数据库导入失败")
            print(f"JSON文件位置: {json_file}")
            print("您可以稍后通过Web界面导入")


if __name__ == '__main__':
    main()

