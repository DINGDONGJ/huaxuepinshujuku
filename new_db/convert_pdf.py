#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF转换工具 - 将老旧或不兼容的PDF转换为Web友好格式

使用PyMuPDF (fitz)重新生成PDF，确保：
1. 文本可选择和搜索
2. 与PDF.js完全兼容
3. 字体正确嵌入
4. 优化文件大小
"""

import fitz  # PyMuPDF
import sys
import os
from pathlib import Path


def convert_pdf_for_web(input_path, output_path=None, method='reconstruct'):
    """
    将PDF转换为web友好格式
    
    Args:
        input_path: 输入PDF文件路径
        output_path: 输出PDF文件路径（可选，默认为原文件名_converted.pdf）
        method: 转换方法
            - 'reconstruct': 重建文本层（保持可选择，推荐）
            - 'image': 转为图像+OCR文本层（备用方案）
    
    Returns:
        bool: 转换是否成功
    """
    
    # 检查输入文件
    if not os.path.exists(input_path):
        print(f"❌ 文件不存在: {input_path}")
        return False
    
    # 生成输出文件名
    if output_path is None:
        input_file = Path(input_path)
        output_path = input_file.parent / f"{input_file.stem}_converted.pdf"
    
    print(f"📄 输入文件: {input_path}")
    print(f"📄 输出文件: {output_path}")
    print(f"🔧 转换方法: {method}")
    print("=" * 60)
    
    try:
        # 打开原始PDF
        print("📖 正在打开PDF...")
        doc = fitz.open(input_path)
        total_pages = len(doc)
        print(f"✅ 成功打开，共 {total_pages} 页")
        
        # 创建新的PDF
        print("🆕 正在创建新PDF...")
        new_doc = fitz.open()
        
        # 逐页处理
        for page_num in range(total_pages):
            print(f"⏳ 处理第 {page_num + 1}/{total_pages} 页...", end=" ")
            
            page = doc[page_num]
            
            if method == 'reconstruct':
                # 方法1：重建页面（保持文本可选择）
                # 这是推荐方法，保留原始文本
                
                # 创建新页面
                new_page = new_doc.new_page(
                    width=page.rect.width,
                    height=page.rect.height
                )
                
                # 复制页面内容（包括文本、图像、图形）
                new_page.show_pdf_page(
                    new_page.rect,  # 目标区域
                    doc,  # 源文档
                    page_num  # 源页码
                )
                
                print("✅ 重建完成")
                
            elif method == 'image':
                # 方法2：渲染为图像（备用方案）
                # 当文本层完全损坏时使用
                
                # 创建新页面
                new_page = new_doc.new_page(
                    width=page.rect.width,
                    height=page.rect.height
                )
                
                # 将页面渲染为高清图像
                mat = fitz.Matrix(2, 2)  # 2倍缩放，确保清晰度
                pix = page.get_pixmap(matrix=mat)
                
                # 插入图像
                new_page.insert_image(new_page.rect, pixmap=pix)
                
                # 尝试提取并重新插入文本（用于搜索）
                try:
                    text_dict = page.get_text("dict")
                    blocks = text_dict.get("blocks", [])
                    
                    for block in blocks:
                        if block.get("type") == 0:  # 文本块
                            for line in block.get("lines", []):
                                for span in line.get("spans", []):
                                    text = span.get("text", "")
                                    bbox = span.get("bbox", [])
                                    
                                    if text and bbox:
                                        # 插入不可见文本（用于搜索）
                                        rect = fitz.Rect(bbox)
                                        new_page.insert_text(
                                            rect.tl,
                                            text,
                                            fontsize=span.get("size", 12),
                                            render_mode=3  # 不可见但可搜索
                                        )
                except Exception as e:
                    print(f"⚠️ 文本提取失败: {e}")
                
                print("✅ 图像化完成")
        
        # 设置元数据
        print("\n📝 设置PDF元数据...")
        metadata = doc.metadata
        new_doc.set_metadata({
            "title": metadata.get("title", "转换后的PDF"),
            "author": metadata.get("author", ""),
            "subject": metadata.get("subject", ""),
            "creator": "PyMuPDF PDF Converter",
            "producer": "PyMuPDF",
        })
        
        # 保存新PDF（带优化）
        print("💾 正在保存优化后的PDF...")
        new_doc.save(
            output_path,
            garbage=4,  # 最大垃圾收集
            deflate=True,  # 压缩流
            clean=True,  # 清理未使用对象
            pretty=True,  # 格式化输出
        )
        
        # 关闭文档
        new_doc.close()
        doc.close()
        
        # 显示文件信息
        print("\n" + "=" * 60)
        print("✅ 转换成功！")
        
        original_size = os.path.getsize(input_path)
        new_size = os.path.getsize(output_path)
        
        print(f"📊 原始文件大小: {original_size / 1024:.2f} KB")
        print(f"📊 新文件大小: {new_size / 1024:.2f} KB")
        
        if new_size < original_size:
            reduction = (1 - new_size / original_size) * 100
            print(f"📉 文件减小: {reduction:.1f}%")
        else:
            increase = (new_size / original_size - 1) * 100
            print(f"📈 文件增大: {increase:.1f}%")
        
        print(f"\n✨ 新PDF已保存到: {output_path}")
        print("\n💡 下一步：")
        print("   1. 在Web浏览器中测试新PDF")
        print("   2. 验证文字是否可选择和搜索")
        print("   3. 如果效果好，可以替换原文件")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 转换失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def batch_convert(directory, pattern="*.pdf", method='reconstruct'):
    """
    批量转换目录中的PDF文件
    
    Args:
        directory: PDF文件所在目录
        pattern: 文件匹配模式（默认所有PDF）
        method: 转换方法
    """
    pdf_dir = Path(directory)
    pdf_files = list(pdf_dir.glob(pattern))
    
    if not pdf_files:
        print(f"❌ 在 {directory} 中未找到匹配的PDF文件")
        return
    
    print(f"📁 找到 {len(pdf_files)} 个PDF文件")
    print("=" * 60)
    
    success_count = 0
    for i, pdf_file in enumerate(pdf_files, 1):
        print(f"\n[{i}/{len(pdf_files)}] 正在处理: {pdf_file.name}")
        print("-" * 60)
        
        if convert_pdf_for_web(str(pdf_file), method=method):
            success_count += 1
    
    print("\n" + "=" * 60)
    print(f"✅ 批量转换完成: {success_count}/{len(pdf_files)} 成功")


def main():
    """主函数"""
    
    print("=" * 60)
    print("🔧 PDF转换工具 - Web友好格式转换器")
    print("=" * 60)
    print()
    
    # 默认配置
    default_input = "pdf/高毒物品目录.pdf"
    
    if len(sys.argv) > 1:
        # 命令行模式
        input_file = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else None
        method = sys.argv[3] if len(sys.argv) > 3 else 'reconstruct'
        
        convert_pdf_for_web(input_file, output_file, method)
    else:
        # 交互模式
        print("📝 请选择操作：")
        print("  1. 转换单个PDF文件（高毒物品目录.pdf）")
        print("  2. 批量转换pdf目录下的所有PDF")
        print("  3. 指定其他PDF文件")
        print()
        
        choice = input("请输入选项 (1/2/3，直接回车默认为1): ").strip() or "1"
        
        if choice == "1":
            # 转换高毒物品目录.pdf
            if os.path.exists(default_input):
                convert_pdf_for_web(default_input, method='reconstruct')
            else:
                print(f"❌ 文件不存在: {default_input}")
                print(f"💡 请确保文件在 {os.path.abspath('pdf')} 目录下")
        
        elif choice == "2":
            # 批量转换
            pdf_dir = "pdf"
            if os.path.exists(pdf_dir):
                batch_convert(pdf_dir, pattern="*.pdf")
            else:
                print(f"❌ 目录不存在: {pdf_dir}")
        
        elif choice == "3":
            # 自定义文件
            custom_file = input("请输入PDF文件路径: ").strip()
            if custom_file:
                convert_pdf_for_web(custom_file, method='reconstruct')
            else:
                print("❌ 未输入文件路径")
        
        else:
            print("❌ 无效的选项")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断操作")
    except Exception as e:
        print(f"\n❌ 程序异常: {e}")
        import traceback
        traceback.print_exc()

