#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能MSDS爬虫 - 自动提取mid和化学品名称

功能：
1. 输入带decrypt的链接
2. 自动提取化学品名称和mid参数
3. 自动创建对应文件夹
4. 直接开始爬取

使用方法：
    python auto_scrape_msds.py "链接"
    
示例：
    python auto_scrape_msds.py "http://www.hgmsds.com/weixin/msds-list-details?decrypt=xxx"

作者：AI Assistant
日期：2025-10-10
"""

import requests
from bs4 import BeautifulSoup
import time
import sys
import os
import re
from urllib.parse import urlparse, parse_qs

# 从scrape_msds导入主要功能
from scrape_msds import scrape_all_parts, PARTS


def extract_chemical_name_and_mid(decrypt_url):
    """
    从decrypt URL中提取化学品名称和mid参数
    
    参数:
        decrypt_url: 带decrypt参数的完整URL
        
    返回:
        tuple: (chemical_name, mid) 如果成功，否则 (None, None)
    """
    print("=" * 70)
    print("智能MSDS爬虫 - 正在分析链接...")
    print("=" * 70)
    print(f"目标URL: {decrypt_url}")
    print()
    
    try:
        # 第1步：访问decrypt URL获取化学品名称
        print("📍 步骤1：访问页面获取化学品信息...")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(decrypt_url, headers=headers, timeout=15)
        response.encoding = 'utf-8'
        
        if response.status_code != 200:
            print(f"❌ 访问失败，HTTP状态码: {response.status_code}")
            return None, None
        
        # 解析页面，提取化学品名称和CAS号
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 查找化学品中文名（在class="cname"的p标签中）
        cname_tag = soup.find('p', class_='cname')
        chemical_name = cname_tag.text.strip() if cname_tag else None
        
        # 查找CAS号（在class="cas"的p标签中）
        cas_tag = soup.find('p', class_='cas')
        cas_number = cas_tag.text.strip() if cas_tag else None
        
        if not chemical_name:
            print("❌ 无法从页面提取化学品名称")
            return None, None
        
        print(f"✓ 化学品名称: {chemical_name}")
        if cas_number:
            print(f"✓ CAS号: {cas_number}")
        print()
        
        # 第2步：构造并访问第一部分的URL来获取mid
        print("📍 步骤2：提取mid参数...")
        
        # 从HTML中提取mid参数（藏在hidden input中）
        mid_input = soup.find('input', {'id': 'mid'})
        
        if mid_input and mid_input.get('value'):
            mid = mid_input.get('value')
            print(f"✓ mid参数: {mid}")
            print()
            return chemical_name, mid
        else:
            print("❌ 无法提取mid参数")
            return None, None
            
    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        return None, None


def sanitize_filename(name):
    """
    清理文件名，移除不合法字符
    
    参数:
        name: 原始名称
        
    返回:
        str: 清理后的名称
    """
    # 移除Windows文件名不允许的字符
    invalid_chars = r'[<>:"/\\|?*]'
    clean_name = re.sub(invalid_chars, '', name)
    
    # 移除前后空格
    clean_name = clean_name.strip()
    
    # 如果名称为空，使用默认名称
    if not clean_name:
        clean_name = "chemical"
    
    return clean_name


def auto_scrape(decrypt_url, output_prefix="msds", delay=0.5):
    """
    自动爬取MSDS数据
    
    参数:
        decrypt_url: 带decrypt参数的URL
        output_prefix: 输出文件夹前缀（默认"msds"）
        delay: 请求延迟（秒）
        
    返回:
        bool: 是否成功
    """
    # 提取化学品名称和mid
    chemical_name, mid = extract_chemical_name_and_mid(decrypt_url)
    
    if not chemical_name or not mid:
        print()
        print("=" * 70)
        print("❌ 提取失败！请检查链接是否正确。")
        print("=" * 70)
        return False
    
    # 创建输出文件夹名称
    safe_name = sanitize_filename(chemical_name)
    output_dir = f"{output_prefix}_{safe_name}"
    
    print("=" * 70)
    print("📊 爬取信息确认")
    print("=" * 70)
    print(f"化学品名称: {chemical_name}")
    print(f"mid参数: {mid}")
    print(f"输出目录: {output_dir}/")
    print(f"请求延迟: {delay}秒")
    print("=" * 70)
    print()
    
    # 开始爬取
    success = scrape_all_parts(mid, output_dir, delay)
    
    return success


def main():
    """
    主函数
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description='智能MSDS爬虫 - 自动提取并爬取',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 直接输入链接（推荐）
  python auto_scrape_msds.py "http://www.hgmsds.com/weixin/msds-list-details?decrypt=xxx"
  
  # 设置延迟
  python auto_scrape_msds.py "链接" --delay 1.0
  
  # 自定义输出前缀
  python auto_scrape_msds.py "链接" --prefix my_msds
  
  # 交互模式（不提供链接时）
  python auto_scrape_msds.py
  
注意:
  - 链接必须是带decrypt参数的完整URL
  - 链接需要用引号括起来
  - 网络连接需要稳定
        """
    )
    
    parser.add_argument(
        'url',
        nargs='?',
        help='化学品MSDS页面URL（带decrypt参数）'
    )
    
    parser.add_argument(
        '--delay', '-d',
        type=float,
        default=0.5,
        help='请求延迟，单位秒（默认: 0.5）'
    )
    
    parser.add_argument(
        '--prefix', '-p',
        default='msds',
        help='输出文件夹前缀（默认: msds）'
    )
    
    args = parser.parse_args()
    
    # 如果没有提供URL，进入交互模式
    if not args.url:
        print("=" * 70)
        print("智能MSDS爬虫 - 交互模式")
        print("=" * 70)
        print()
        print("请粘贴化学品MSDS页面的完整URL")
        print("（URL应该包含 decrypt 参数）")
        print()
        print("示例:")
        print("  http://www.hgmsds.com/weixin/msds-list-details?decrypt=xxx")
        print()
        
        url = input("请输入URL: ").strip()
        
        if not url:
            print("❌ 未输入URL，退出")
            sys.exit(1)
    else:
        url = args.url
    
    # 验证URL
    if 'hgmsds.com' not in url:
        print("❌ URL不正确，必须是合规化学网的链接")
        sys.exit(1)
    
    if 'decrypt' not in url:
        print("❌ URL必须包含decrypt参数")
        print("提示: 这应该是MSDS目录页面的链接，不是详情页")
        sys.exit(1)
    
    print()
    
    # 开始自动爬取
    success = auto_scrape(url, args.prefix, args.delay)
    
    # 退出码
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    # 检查依赖
    try:
        import requests
        from bs4 import BeautifulSoup
    except ImportError:
        print("❌ 缺少依赖库！")
        print("请运行: pip install requests beautifulsoup4")
        sys.exit(1)
    
    # 检查是否能导入scrape_msds
    try:
        from scrape_msds import scrape_all_parts, PARTS
    except ImportError:
        print("❌ 找不到 scrape_msds.py 文件！")
        print("请确保 scrape_msds.py 和本脚本在同一目录下")
        sys.exit(1)
    
    main()

