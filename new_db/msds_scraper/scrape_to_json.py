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

# MSDS 16 sections mapping (Chinese labels)
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
    """Extract complete chemical info and mid parameter from part 1"""
    print("=" * 70)
    print("Analyzing URL...")
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
                # Visit homepage
                print("Visiting homepage...")
                page.goto(decrypt_url, timeout=30000)
                page.wait_for_timeout(1500)
                
                # Click first section
                print("Clicking first section...")
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
                        print(f"[SUCCESS] Clicked: {selector}")
                        break
                    except:
                        continue
                
                if not clicked:
                    print("[ERROR] Unable to click first section")
                    browser.close()
                    return None, None, None, None, None, None, None
                
                # Wait for page load
                page.wait_for_timeout(2000)
                
                # Get current URL and page content
                current_url = page.url
                html_content = page.content()
                
                # Extract mid parameter
                mid_match = re.search(r'[?&]mid=([^&]+)', current_url)
                if mid_match:
                    mid = mid_match.group(1)
                    print(f"[SUCCESS] MID parameter: {mid}")
                else:
                    print("[ERROR] MID parameter not found")
                
                # Parse HTML of first section
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Extract all maincondetail divs (containing label-value pairs)
                main_divs = soup.find_all('div', class_='maincondetail')
                
                for div in main_divs:
                    paragraphs = div.find_all('p')
                    if len(paragraphs) >= 2:
                        label = paragraphs[0].get_text(strip=True)
                        value = paragraphs[1].get_text(strip=True)
                        
                        # Extract values based on labels
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
                            # Aliases may have multiple values, separated by delimiters
                            if value and value.strip():
                                # Support multiple delimiters
                                alias_list = re.split(r'[,，、|；;]', value)
                                aliases = [a.strip() for a in alias_list if a.strip()]
                
                print()
                print("=" * 70)
                print("Extraction Results:")
                print("=" * 70)
                print(f"Chemical Name (CN): {chinese_name or 'Not found'}")
                print(f"CAS Number: {cas_number or 'Not found'}")
                print(f"English Name: {english_name or 'Not found'}")
                print(f"EC Number: {ec_number or 'Not found'}")
                print(f"Formula: {formula or 'Not found'}")
                print(f"Aliases: {', '.join(aliases) if aliases else 'Not found'}")
                print(f"MID: {mid or 'Not found'}")
                print()
                
            finally:
                browser.close()
        
        if not mid:
            print("[ERROR] Cannot get MID, unable to continue scraping")
            return None, None, None, None, None, None, None
        
        return chinese_name, cas_number, english_name, ec_number, formula, aliases, mid
        
    except Exception as e:
        print(f"[ERROR] Info extraction failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None, None, None, None, None, None, None


def download_image(img_url, output_dir, base_url):
    """Download image and return local path"""
    try:
        # Handle relative paths
        if not img_url.startswith('http'):
            img_url = urljoin(base_url, img_url)
        
        # 下载图片
        response = requests.get(img_url, timeout=10)
        if response.status_code != 200:
            return None
        
        # Generate filename (use URL hash to avoid duplicates)
        url_hash = hashlib.md5(img_url.encode()).hexdigest()[:12]
        ext = os.path.splitext(urlparse(img_url).path)[1] or '.png'
        filename = f"{url_hash}{ext}"
        
        # Save image
        images_dir = os.path.join(output_dir, 'images')
        os.makedirs(images_dir, exist_ok=True)
        filepath = os.path.join(images_dir, filename)
        
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        # Return relative path
        return f"images/{filename}"
        
    except Exception as e:
        print(f"  [WARNING] Image download failed: {str(e)}")
        return None


def scrape_msds_part(mid, part_num, output_dir='msds_json'):
    """Scrape single MSDS section content and images"""
    # Correct URL format: type parameter starts from 0 (part 1 = type 0)
    url = f"http://www.hgmsds.com/weixin/msds-page-details?mid={mid}&type={part_num-1}&tid="
    base_url = "http://www.hgmsds.com"
    
    try:
        response = requests.get(url, timeout=15)
        response.encoding = 'utf-8'
        
        if response.status_code != 200:
            return None, []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract text content
        text_content = None
        content_div = soup.find('div', class_='maincontent')
        if content_div:
            text_content = content_div.get_text(separator='\n', strip=True)
        else:
            # Fallback method
            main_divs = soup.find_all('div', class_='maincondetail')
            if main_divs:
                content_parts = []
                for div in main_divs:
                    text = div.get_text(separator='\n', strip=True)
                    if text:
                        content_parts.append(text)
                if content_parts:
                    text_content = '\n\n'.join(content_parts)
        
        # Extract images (focus on part 2 and part 14)
        images = []
        if part_num in [2, 14]:  # 第2部分（危险性概述）和第14部分（运输信息）
            img_tags = soup.find_all('img')
            temp_images = []
            
            for img in img_tags:
                img_src = img.get('src', '')
                img_alt = img.get('alt', '')
                
                # Skip irrelevant images like logos
                if any(skip in img_src.lower() for skip in ['logo', 'qrcode', 'icon']):
                    continue
                
                # Download image
                local_path = download_image(img_src, output_dir, base_url)
                if local_path:
                    image_info = {
                        "url": local_path,
                        "alt": img_alt,
                        "type": "ghs" if part_num == 2 else "transport",
                        "original_url": img_src
                    }
                    temp_images.append(image_info)
            
            # Filter QR codes: exclude last image (usually QR code)
            if len(temp_images) > 1:
                images = temp_images[:-1]  # 只保留除了最后一张之外的所有图片
            else:
                images = temp_images
        
        return text_content, images
        
    except Exception as e:
        print(f"  [WARNING] Request failed: {str(e)}")
        return None, []


def scrape_to_json(url, output_dir='msds_json'):
    """Scrape MSDS and generate JSON file"""
    
    # Extract chemical info
    result = extract_chemical_info(url)
    if result[0] is None:
        print("[ERROR] Cannot extract chemical info, scraping failed")
        return None
    
    chinese_name, cas_number, english_name, ec_number, formula, aliases, mid = result
    
    if not mid:
        print("[ERROR] Cannot extract MID, scraping failed")
        return None
    
    # Use chemical name as default
    if not chinese_name:
        chinese_name = f"Chemical_{mid}"
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Start scraping 16 sections
    print("=" * 70)
    print("Starting MSDS data scraping...")
    print("=" * 70)
    
    msds_chapters = []
    success_count = 0
    
    for part_num in range(1, 17):
        part_title = MSDS_PARTS[part_num]
        print(f"Scraping: Part {part_num} - {part_title}...", end=' ')
        
        content, images = scrape_msds_part(mid, part_num, output_dir)
        
        if content:
            chapter_data = {
                "章节序号": part_num,
                "章节标题": part_title,
                "内容": content
            }
            # Add images to data if exists
            if images:
                chapter_data["图片"] = images
                print(f"[OK] ({len(images)} images)")
            else:
                print("[OK]")
            msds_chapters.append(chapter_data)
            success_count += 1
        else:
            print("[FAIL]")
        
        # Delay to avoid too frequent requests
        time.sleep(0.5)
    
    # Build JSON data structure
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
    
    # Save JSON file
    print()
    print("=" * 70)
    print("Saving JSON file...")
    print("=" * 70)
    
    # Filename: ChemicalName_CASNumber.json
    if cas_number:
        filename = f"{chinese_name}_{cas_number}.json"
    else:
        filename = f"{chinese_name}_{mid}.json"
    
    # Clean illegal characters in filename
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    filepath = os.path.join(output_dir, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(msds_data, f, ensure_ascii=False, indent=2)
    
    print(f"[SUCCESS] JSON file saved: {filepath}")
    print()
    print("Data Statistics:")
    print(f"  - Chemical Name: {chinese_name}")
    print(f"  - CAS Number: {cas_number or 'N/A'}")
    print(f"  - MSDS Chapters: {success_count}/16")
    print(f"  - Aliases Count: {len(aliases)}")
    print()
    
    if success_count < 16:
        print("[WARNING] Some chapters failed to scrape, please check network or website availability")
    else:
        print("[SUCCESS] Scraping complete! You can import this JSON file via Web interface.")
    
    return filepath


def import_to_database(json_file, db_password='1234'):
    """Import JSON data to database"""
    print("=" * 70)
    print("Importing to database...")
    print("=" * 70)
    
    try:
        # Read JSON file
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
            # Check if chemical already exists (by CAS number or Chinese name)
            cas_number = chem_info.get('CAS号')
            chinese_name = chem_info.get('中文名')
            
            if cas_number:
                cursor.execute("SELECT 编号 FROM 化学品 WHERE CAS号 = %s", (cas_number,))
            else:
                cursor.execute("SELECT 编号 FROM 化学品 WHERE 中文名 = %s", (chinese_name,))
            
            existing = cursor.fetchone()
            
            if existing:
                chemical_id = existing[0]
                print(f"[INFO] Chemical exists, updating data (ID: {chemical_id})")
                
                # Update chemical info
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
                
                # Delete old aliases and MSDS data
                cursor.execute("DELETE FROM 化学品别名 WHERE 化学品编号 = %s", (chemical_id,))
                cursor.execute("DELETE FROM MSDS文档 WHERE 化学品编号 = %s", (chemical_id,))
            else:
                print("[INFO] Adding new chemical")
                
                # Insert new chemical
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
            
            # Insert aliases
            for alias in aliases:
                cursor.execute("""
                    INSERT INTO 化学品别名 (化学品编号, 别名)
                    VALUES (%s, %s)
                """, (chemical_id, alias))
            
            # Insert MSDS document
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
            
            # Insert MSDS chapters
            print(f"[INFO] MSDS Document ID: {msds_id}")
            for chapter in chapters:
                # Process image data
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
                print(f"  Inserted chapter {chapter['章节序号']:02d}: {chapter['章节标题']}")
            
            # Commit transaction
            conn.commit()
            
            print()
            print("=" * 70)
            print("[SUCCESS] Database import successful!")
            print("=" * 70)
            print(f"Chemical ID: {chemical_id}")
            print(f"Aliases Count: {len(aliases)}")
            print(f"MSDS Chapters: {len(chapters)}/16")
            print()
            
        except Exception as e:
            conn.rollback()
            print()
            print("=" * 70)
            print(f"[ERROR] Database error: {e}")
            print("=" * 70)
            print("Possible reasons:")
            print("  1. Database not created or not started")
            print("  2. Incorrect database password")
            print("  3. Database name mismatch")
            print()
            print("Solutions:")
            print("  1. Ensure init_simple_db.sql has been run to create database")
            print("  2. Check database password (use --password parameter)")
            print()
            raise
        finally:
            cursor.close()
            conn.close()
            
    except FileNotFoundError:
        print(f"[ERROR] File not found: {json_file}")
        return False
    except json.JSONDecodeError:
        print(f"[ERROR] JSON format error: {json_file}")
        return False
    except Exception as e:
        print(f"[ERROR] Import failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


def main():
    parser = argparse.ArgumentParser(
        description='MSDS Intelligent Scraper + Database Import Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Usage Examples:
  1. Scrape only, save as JSON:
     python scrape_to_json.py "URL"
     
  2. Scrape and import to database:
     python scrape_to_json.py "URL" --import
     
  3. Specify database password:
     python scrape_to_json.py "URL" --import --password yourpass
     
  4. Custom output directory:
     python scrape_to_json.py "URL" --output my_data
        """
    )
    
    parser.add_argument('url', nargs='?', help='MSDS page URL (with decrypt parameter)')
    parser.add_argument('--import', dest='do_import', action='store_true',
                        help='Import to database after scraping')
    parser.add_argument('--password', '-p', default='1234',
                        help='Database password (default: 1234)')
    parser.add_argument('--output', '-o', default='msds_json',
                        help='JSON output directory (default: msds_json)')
    
    args = parser.parse_args()
    
    # Interactive mode if no URL provided
    if not args.url:
        print("=" * 70)
        print("MSDS Intelligent Scraper + Database Import Tool")
        print("=" * 70)
        print()
        url = input("Enter MSDS page URL: ").strip()
        if not url:
            print("[ERROR] URL cannot be empty")
            return
        
        import_choice = input("Import to database directly? (y/N): ").strip().lower()
        do_import = import_choice in ['y', 'yes']
        
        if do_import:
            db_password = input("Database password (default: 1234): ").strip() or '1234'
        else:
            db_password = '1234'
    else:
        url = args.url
        do_import = args.do_import
        db_password = args.password
    
    # Scrape data
    json_file = scrape_to_json(url, args.output)
    
    if not json_file:
        print("[ERROR] Scraping failed")
        sys.exit(1)
    
    # Import to database if needed
    if do_import:
        success = import_to_database(json_file, db_password)
        if success:
            print("[SUCCESS] All done!")
        else:
            print()
            print("[WARNING] JSON file saved, but database import failed")
            print(f"JSON file location: {json_file}")
            print("You can import it later via Web interface")


if __name__ == '__main__':
    main()

