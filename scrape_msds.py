#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
乙醇MSDS数据爬取脚本
从合规化学网获取完整的16部分MSDS数据

使用方法：
    python scrape_msds.py

依赖库：
    pip install requests beautifulsoup4

作者：AI Assistant
日期：2025-10-10
"""

import requests
from bs4 import BeautifulSoup
import time
import os
import sys

# 基础URL
BASE_URL = "http://www.hgmsds.com/weixin/msds-page-details"

# MSDS各部分名称
PARTS = [
    ("0", "01_化学品及企业标识"),
    ("1", "02_危险性概述"),
    ("2", "03_成分组分信息"),
    ("3", "04_急救措施"),
    ("4", "05_消防措施"),
    ("5", "06_泄漏应急处理"),
    ("6", "07_操作处置和储存"),
    ("7", "08_接触控制个体防护"),
    ("8", "09_理化特性"),
    ("9", "10_稳定性和反应性"),
    ("10", "11_毒理学信息"),
    ("11", "12_生态学信息"),
    ("12", "13_废弃处置"),
    ("13", "14_运输信息"),
    ("14", "15_法规信息"),
    ("15", "16_其他信息")
]

# 默认mid参数（乙醇）
DEFAULT_MID = "dmacpg"


def fetch_msds_part(mid, type_id, part_name, output_dir="msds_output"):
    """
    获取MSDS某个部分的内容
    
    参数:
        mid: 化学品ID（从网页URL中获取）
        type_id: 部分编号（0-15）
        part_name: 部分名称（如：01_化学品及企业标识）
        output_dir: 输出目录
    
    返回:
        bool: 是否成功
    """
    print(f"正在获取: {part_name}...", end=" ")
    
    # 构造URL
    url = f"{BASE_URL}?mid={mid}&type={type_id}&tid="
    
    try:
        # 发送请求
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.encoding = 'utf-8'
        
        if response.status_code == 200:
            # 解析HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 提取主要内容
            content_div = soup.find('div', style=lambda value: value and 'margin-left' in value)
            
            if content_div:
                # 创建HTML文件
                html_content = f"""<html><head>
<meta charset="utf-8">
<title>MSDS - {part_name}</title>
<style>
    body {{ 
        font-family: Arial, 'Microsoft YaHei', sans-serif; 
        padding: 20px; 
        max-width: 1000px;
        margin: 0 auto;
    }}
    h1 {{ color: #333; border-bottom: 2px solid #667eea; padding-bottom: 10px; }}
    h2 {{ color: #666; margin-top: 20px; }}
    table {{ 
        border-collapse: collapse; 
        width: 100%; 
        margin: 10px 0; 
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }}
    td, th {{ 
        border: 1px solid #ddd; 
        padding: 12px; 
        text-align: left; 
    }}
    tr:nth-child(even) {{ background-color: #f9f9f9; }}
    tr:hover {{ background-color: #f5f5f5; }}
    .mdp {{ 
        font-weight: bold; 
        color: #555; 
        background-color: #e8f0fe;
        padding: 5px;
        border-radius: 3px;
    }}
    .mdp0 {{
        font-size: 1.2em;
        font-weight: bold;
        color: #667eea;
        margin-top: 20px;
    }}
    .maincondetail {{
        margin: 10px 0;
    }}
    img {{
        max-width: 100%;
        height: auto;
    }}
</style>
</head>
<body>
<h1>{part_name}</h1>
{content_div.prettify()}
<hr>
<footer style="text-align: center; color: #999; margin-top: 30px; font-size: 0.9em;">
    数据来源：合规化学网 (www.hgmsds.com) | 爬取时间：{time.strftime('%Y-%m-%d %H:%M:%S')}
</footer>
</body>
</html>"""
                
                # 确保输出目录存在
                os.makedirs(output_dir, exist_ok=True)
                
                # 保存文件
                filename = os.path.join(output_dir, f"{part_name}.html")
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                
                print(f"✓")
                return True
            else:
                print(f"✗ 未找到内容")
                return False
                
        else:
            print(f"✗ HTTP错误: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"✗ 错误: {str(e)}")
        return False


def scrape_all_parts(mid=DEFAULT_MID, output_dir="msds_output", delay=0.5):
    """
    爬取所有16个部分
    
    参数:
        mid: 化学品ID
        output_dir: 输出目录
        delay: 每次请求之间的延迟（秒）
    """
    print("=" * 70)
    print("MSDS数据爬取脚本")
    print("数据来源: 合规化学网 (www.hgmsds.com)")
    print("=" * 70)
    print(f"化学品ID: {mid}")
    print(f"输出目录: {output_dir}")
    print(f"请求延迟: {delay}秒")
    print("=" * 70)
    print()
    
    success_count = 0
    failed_parts = []
    
    for type_id, part_name in PARTS:
        if fetch_msds_part(mid, type_id, part_name, output_dir):
            success_count += 1
        else:
            failed_parts.append(part_name)
        
        # 延迟，避免请求过快
        time.sleep(delay)
    
    print()
    print("=" * 70)
    print(f"完成! 成功获取 {success_count}/{len(PARTS)} 个部分")
    
    if failed_parts:
        print(f"\n失败的部分 ({len(failed_parts)}个):")
        for part in failed_parts:
            print(f"  - {part}")
    
    print(f"\n文件保存在: {output_dir}/ 目录")
    print("=" * 70)
    
    return success_count == len(PARTS)


def get_mid_from_url(url):
    """
    从URL中提取mid参数
    
    参数:
        url: 完整的MSDS页面URL
    
    返回:
        str: mid参数值，如果找不到返回None
    """
    try:
        from urllib.parse import urlparse, parse_qs
        parsed = urlparse(url)
        query = parse_qs(parsed.query)
        return query.get('mid', [None])[0]
    except:
        return None


def main():
    """
    主函数 - 处理命令行参数
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description='从合规化学网爬取MSDS数据',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 爬取乙醇MSDS（使用默认ID）
  python scrape_msds.py
  
  # 爬取其他化学品（指定mid）
  python scrape_msds.py --mid abcdef
  
  # 指定输出目录
  python scrape_msds.py --output my_msds
  
  # 设置请求延迟（秒）
  python scrape_msds.py --delay 1.0
  
注意:
  - 需要安装依赖: pip install requests beautifulsoup4
  - mid参数可以从化学品详情页URL中获取
  - 建议设置合理的延迟时间，避免请求过快
        """
    )
    
    parser.add_argument(
        '--mid',
        default=DEFAULT_MID,
        help=f'化学品ID（默认: {DEFAULT_MID} - 乙醇）'
    )
    
    parser.add_argument(
        '--output', '-o',
        default='msds_output',
        help='输出目录（默认: msds_output）'
    )
    
    parser.add_argument(
        '--delay', '-d',
        type=float,
        default=0.5,
        help='请求延迟，单位秒（默认: 0.5）'
    )
    
    args = parser.parse_args()
    
    # 开始爬取
    success = scrape_all_parts(
        mid=args.mid,
        output_dir=args.output,
        delay=args.delay
    )
    
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
    
    main()

