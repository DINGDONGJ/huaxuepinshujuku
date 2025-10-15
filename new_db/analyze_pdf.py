#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF分析工具 - 提取化学品名称和页码
"""

import PyPDF2
import re
import json

def analyze_pdf(pdf_path):
    """分析PDF文件，提取化学品信息"""
    
    print(f"📄 正在分析PDF: {pdf_path}\n")
    
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            
            print(f"📊 PDF基本信息:")
            print(f"   总页数: {len(reader.pages)}")
            
            # 检查是否有书签
            if reader.outline:
                print(f"   ✅ 有书签/大纲 (共 {len(reader.outline)} 个)")
                print("\n📑 书签列表:")
                for i, bookmark in enumerate(reader.outline[:10]):
                    if isinstance(bookmark, dict):
                        print(f"   {i+1}. {bookmark.get('/Title', 'Unknown')}")
            else:
                print(f"   ❌ 没有书签/大纲")
            
            print(f"\n📝 前5页内容预览:")
            print("="*60)
            
            chemicals = []
            cas_pattern = re.compile(r'\b(\d{2,7}-\d{2}-\d)\b')
            
            for page_num in range(min(5, len(reader.pages))):
                page = reader.pages[page_num]
                text = page.extract_text()
                
                print(f"\n--- 第 {page_num + 1} 页 ---")
                print(text[:500])  # 只显示前500字符
                
                # 尝试提取CAS号
                cas_matches = cas_pattern.findall(text)
                if cas_matches:
                    print(f"\n   🔍 发现CAS号: {', '.join(cas_matches[:5])}")
            
            # 扫描所有页面，寻找化学品
            print(f"\n\n🔍 正在扫描所有页面查找化学品...")
            
            all_text = ""
            page_map = {}  # {page_num: text}
            
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                text = page.extract_text()
                all_text += f"\n--- PAGE {page_num + 1} ---\n" + text
                page_map[page_num + 1] = text
                
                # 查找CAS号
                cas_matches = cas_pattern.findall(text)
                for cas in cas_matches:
                    # 尝试找到化学品名称（通常在CAS号前面）
                    lines = text.split('\n')
                    for i, line in enumerate(lines):
                        if cas in line:
                            # 取前面几行作为可能的化学品名称
                            possible_names = lines[max(0, i-3):i+1]
                            chemicals.append({
                                'page': page_num + 1,
                                'cas': cas,
                                'context': '\n'.join(possible_names)
                            })
            
            print(f"   ✅ 共找到 {len(chemicals)} 个可能的化学品条目")
            
            # 保存结果
            output = {
                'total_pages': len(reader.pages),
                'has_bookmarks': bool(reader.outline),
                'chemicals_found': len(chemicals),
                'chemicals': chemicals[:50]  # 只保存前50个
            }
            
            output_file = pdf_path.replace('.pdf', '_analysis.json')
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output, f, ensure_ascii=False, indent=2)
            
            print(f"\n💾 分析结果已保存到: {output_file}")
            
            # 保存完整文本
            text_file = pdf_path.replace('.pdf', '_fulltext.txt')
            with open(text_file, 'w', encoding='utf-8') as f:
                f.write(all_text)
            
            print(f"💾 完整文本已保存到: {text_file}")
            
            return output
            
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == '__main__':
    pdf_path = 'pdf/易制爆危险化学品名录.pdf'
    analyze_pdf(pdf_path)

