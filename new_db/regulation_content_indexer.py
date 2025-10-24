"""
法规内容索引构建器
用于构建法规文本的关键词索引，提高内容匹配性能
"""

import os
import json
import re
from collections import defaultdict
from pathlib import Path

class RegulationContentIndexer:
    """法规内容索引器"""
    
    def __init__(self, md_folder='化学品法规md', index_file='regulation_content_index.json'):
        self.md_folder = os.path.join(os.path.dirname(__file__), md_folder)
        self.index_file = os.path.join(os.path.dirname(__file__), index_file)
        self.index = {
            'metadata': {},  # 文件元数据
            'keyword_index': {},  # 关键词倒排索引
            'stats': {}  # 统计信息
        }
    
    def build_index(self):
        """构建完整索引"""
        print("🔨 开始构建法规内容索引...")
        
        # 遍历所有MD文件
        md_files = list(Path(self.md_folder).rglob('*.md'))
        total = len(md_files)
        print(f"📁 找到 {total} 个法规文件")
        
        for idx, md_path in enumerate(md_files, 1):
            if idx % 50 == 0:
                print(f"   处理进度: {idx}/{total} ({idx*100//total}%)")
            
            self._index_file(md_path)
        
        # 保存索引
        self._save_index()
        print(f"✅ 索引构建完成！共索引 {len(self.index['metadata'])} 个文件")
        print(f"📊 关键词总数: {len(self.index['keyword_index'])}")
    
    def _index_file(self, md_path):
        """索引单个文件"""
        try:
            # 读取文件内容
            with open(md_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 获取相对路径（用于映射到PDF）
            rel_path = os.path.relpath(md_path, self.md_folder)
            # 统一使用正斜杠（兼容web URL）
            rel_path = rel_path.replace('\\', '/')
            pdf_path = rel_path.replace('.md', '.pdf')
            
            # 使用文件名作为标题（最准确）
            title = os.path.basename(md_path).replace('.md', '')
            
            # 存储元数据
            self.index['metadata'][pdf_path] = {
                'title': title,
                'md_path': str(md_path),
                'size': len(content),
                'category': self._get_category(rel_path)
            }
            
            # 提取关键词并建立倒排索引（标题+内容）
            keywords = self._extract_keywords(content, title)
            for keyword in keywords:
                if keyword not in self.index['keyword_index']:
                    self.index['keyword_index'][keyword] = []
                self.index['keyword_index'][keyword].append(pdf_path)
        
        except Exception as e:
            print(f"⚠️  处理文件失败: {md_path}, 错误: {e}")
    
    def _extract_keywords(self, content, title=''):
        """从标题和内容中提取关键词"""
        keywords = set()
        
        # 0. 从标题中提取关键词（高权重）
        if title:
            # 标题分词：按空格、斜杠、冒号分割
            title_words = re.split(r'[/：:\s]+', title)
            for word in title_words:
                word = word.strip()
                if len(word) >= 2:  # 至少2个字符
                    keywords.add(word)
            
            # 特别提取标题中的部分编号（如"第18部分"）
            part_numbers = re.findall(r'第(\d+)部分', title)
            for num in part_numbers:
                keywords.add(f'第{num}部分')
            
            # 提取标题中的标准编号
            standard_codes = re.findall(r'(GB|HG/T|SN/T)\s*\d+', title)
            keywords.update(standard_codes)
        
        # 1. 提取危险性关键词
        hazard_patterns = [
            r'(易燃|易爆|有毒|腐蚀|氧化|爆炸|燃烧|刺激|致癌|致突变)',
            r'(急性毒性|慢性毒性|皮肤腐蚀|眼损伤|呼吸致敏|皮肤致敏)',
            r'(生殖毒性|靶器官毒性|吸入危害|水生环境)',
            r'(类别\s*[1-4A-E])',
        ]
        
        for pattern in hazard_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            keywords.update(matches)
        
        # 2. 提取GHS分类关键词
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
                keywords.add(keyword)
        
        # 3. 提取运输分类关键词
        transport_patterns = [
            r'UN\s*(\d{4})',
            r'联合国编号\s*(\d{4})',
            r'运输危险类别\s*[：:]\s*(\d)',
            r'(海洋污染物)'
        ]
        
        for pattern in transport_patterns:
            matches = re.findall(pattern, content)
            keywords.update(str(m) for m in matches if m)
        
        # 4. 提取理化特性关键词
        property_keywords = ['闪点', '沸点', '熔点', '爆炸极限', '自燃温度', 
                            '蒸气压', '密度', '溶解性', '粘度']
        keywords.update(kw for kw in property_keywords if kw in content)
        
        # 5. 提取法规名称关键词
        regulation_patterns = [
            r'《(.+?)》',
            r'GB\s*\d+[.\-\d]*',
            r'HG/T\s*\d+',
            r'SN/T\s*\d+'
        ]
        
        for pattern in regulation_patterns:
            matches = re.findall(pattern, content)
            keywords.update(matches)
        
        return keywords
    
    def _get_category(self, rel_path):
        """获取法规分类"""
        if '国家标准' in rel_path:
            return '国家标准'
        elif '行业标准' in rel_path:
            return '行业标准'
        elif '法律法规' in rel_path:
            return '法律法规'
        elif '团体标准' in rel_path:
            return '团体标准'
        else:
            return '其他'
    
    def _save_index(self):
        """保存索引到文件"""
        # 计算统计信息
        self.index['stats'] = {
            'total_files': len(self.index['metadata']),
            'total_keywords': len(self.index['keyword_index']),
            'categories': self._count_categories()
        }
        
        with open(self.index_file, 'w', encoding='utf-8') as f:
            json.dump(self.index, f, ensure_ascii=False, indent=2)
        
        print(f"💾 索引已保存到: {self.index_file}")
    
    def _count_categories(self):
        """统计各分类文件数"""
        categories = defaultdict(int)
        for meta in self.index['metadata'].values():
            categories[meta['category']] += 1
        return dict(categories)
    
    def load_index(self):
        """加载索引"""
        if os.path.exists(self.index_file):
            with open(self.index_file, 'r', encoding='utf-8') as f:
                self.index = json.load(f)
            return True
        return False
    
    def search_by_keywords(self, keywords, max_results=20):
        """根据关键词搜索法规"""
        # 统计每个法规的关键词命中数
        file_scores = defaultdict(int)
        
        for keyword in keywords:
            # 精确匹配
            if keyword in self.index['keyword_index']:
                for pdf_path in self.index['keyword_index'][keyword]:
                    file_scores[pdf_path] += 1
            
            # 模糊匹配（包含关系）
            for idx_keyword in self.index['keyword_index']:
                if keyword in idx_keyword or idx_keyword in keyword:
                    for pdf_path in self.index['keyword_index'][idx_keyword]:
                        file_scores[pdf_path] += 0.5
        
        # 按分数排序
        sorted_files = sorted(file_scores.items(), key=lambda x: x[1], reverse=True)
        
        # 返回结果
        results = []
        for pdf_path, score in sorted_files[:max_results]:
            if score >= 1:  # 至少命中一个关键词
                meta = self.index['metadata'].get(pdf_path, {})
                results.append({
                    'file': pdf_path,
                    'title': meta.get('title', ''),
                    'score': score,
                    'category': meta.get('category', ''),
                    'reason': f'内容匹配度：{int(score)}个关键词'
                })
        
        return results


def main():
    """主函数：构建索引"""
    indexer = RegulationContentIndexer()
    indexer.build_index()


if __name__ == '__main__':
    main()

