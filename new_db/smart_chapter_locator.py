#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能章节定位器
根据用户查询意图，自动定位到相关的MSDS章节
"""

import re
from typing import Dict, List, Tuple, Optional

class SmartChapterLocator:
    """智能章节定位器"""
    
    # MSDS章节映射
    CHAPTER_MAPPING = {
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
    
    # 关键词到章节的映射
    KEYWORD_TO_CHAPTER = {
        # 第2章：危险性概述
        2: [
            '危险', '危害', '风险', 'GHS', '象形图', '警示词', '危险性',
            '易燃', '易爆', '有毒', '腐蚀', '刺激', '致癌', '致突变'
        ],
        
        # 第3章：成分/组成信息
        3: [
            '成分', '组成', '含量', '浓度', '纯度', '杂质', '配方'
        ],
        
        # 第4章：急救措施
        4: [
            '急救', '中毒', '吸入', '误食', '皮肤接触', '眼睛接触',
            '急救措施', '紧急处理', '医疗', '解毒'
        ],
        
        # 第5章：消防措施
        5: [
            '消防', '灭火', '火灾', '燃烧', '灭火剂', '灭火器',
            '消防员', '防护装备'
        ],
        
        # 第6章：泄漏应急处理
        6: [
            '泄漏', '泄露', '溢出', '应急', '清理', '收集', 
            '泄漏处理', '泄露处理', '应急处理', '环境保护措施',
            '泄漏应急', '溢出处理'
        ],
        
        # 第7章：操作处置与储存
        7: [
            '操作', '处置', '储存', '贮存', '保管', '使用',
            '注意事项', '安全操作', '储存条件', '存放'
        ],
        
        # 第8章：接触控制/个体防护
        8: [
            '防护', '个体防护', '接触控制', '防护装备', 'PPE',
            '手套', '护目镜', '口罩', '防护服', '呼吸防护',
            '工程控制', '通风'
        ],
        
        # 第9章：理化特性
        9: [
            '理化', '物理', '化学', '性质', '特性', '外观', '颜色',
            '气味', '熔点', '沸点', '闪点', '密度', '溶解度',
            '蒸气压', '相对密度', 'pH', '粘度'
        ],
        
        # 第10章：稳定性和反应性
        10: [
            '稳定性', '反应性', '不相容', '禁配物', '分解',
            '聚合', '避免接触', '危险反应', '分解产物'
        ],
        
        # 第11章：毒理学信息
        11: [
            '毒性', '毒理', '毒理学', 'LD50', 'LC50', '急性毒性',
            '慢性毒性', '致癌性', '致突变性', '生殖毒性',
            '靶器官', '吸入危害', '皮肤刺激', '眼刺激'
        ],
        
        # 第12章：生态学信息
        12: [
            '生态', '环境', '生态毒性', '水生', '鱼类', '藻类',
            '生物降解', '生物累积', '土壤', '持久性'
        ],
        
        # 第13章：废弃处置
        13: [
            '废弃', '废弃处置', '废物', '废弃物', '销毁', '回收',
            '废弃物处理', '残余物', '废弃处理'
        ],
        
        # 第14章：运输信息
        14: [
            '运输', 'UN', '联合国编号', '危险货物', '包装',
            '运输类别', '海运', '空运', '陆运', '包装类别'
        ],
        
        # 第15章：法规信息
        15: [
            '法规', '法律', '标准', '规定', '目录', '名录',
            '监管', '限制', '禁止', '许可'
        ]
    }
    
    def __init__(self):
        """初始化定位器"""
        pass
    
    def analyze_query(self, query: str) -> Dict:
        """
        分析用户查询意图
        
        参数:
            query: 用户查询，如"丙醇的毒性"
        
        返回:
            {
                'chemical_name': '丙醇',
                'intent': 'toxicity',
                'target_chapters': [11],
                'keywords': ['毒性']
            }
        """
        result = {
            'chemical_name': None,
            'intent': None,
            'target_chapters': [],
            'keywords': []
        }
        
        # 1. 提取化学品名称（假设在"的"之前）
        if '的' in query:
            parts = query.split('的')
            result['chemical_name'] = parts[0].strip()
            intent_text = '的'.join(parts[1:]).strip()
        else:
            # 没有"的"，整个查询作为化学品名称
            result['chemical_name'] = query.strip()
            return result
        
        # 2. 分析意图并匹配章节（优先匹配更长的关键词）
        matched_chapters = {}  # {chapter_num: (keyword_length, keyword)}
        
        for chapter_num, keywords in self.KEYWORD_TO_CHAPTER.items():
            # 按关键词长度降序排序（优先匹配更长的关键词）
            sorted_keywords = sorted(keywords, key=len, reverse=True)
            
            for keyword in sorted_keywords:
                if keyword in intent_text or keyword in query:
                    # 如果该章节还没有匹配，或者找到了更长的关键词
                    if chapter_num not in matched_chapters or len(keyword) > matched_chapters[chapter_num][0]:
                        matched_chapters[chapter_num] = (len(keyword), keyword)
        
        # 提取章节编号和关键词
        result['target_chapters'] = sorted(list(matched_chapters.keys()))
        result['keywords'] = list(set([kw for _, kw in matched_chapters.values()]))
        
        # 3. 识别常见意图（按优先级顺序，更具体的意图优先）
        if any(kw in intent_text for kw in ['泄漏', '泄露', '溢出', '泄漏处理', '泄露处理']):
            result['intent'] = 'spill'
        elif any(kw in intent_text for kw in ['废弃', '废弃物', '废弃处理']):
            result['intent'] = 'waste'
        elif any(kw in intent_text for kw in ['毒性', '毒理', 'LD50', 'LC50']):
            result['intent'] = 'toxicity'
        elif any(kw in intent_text for kw in ['危险', '危害', '风险']):
            result['intent'] = 'hazard'
        elif any(kw in intent_text for kw in ['理化', '物理', '化学', '性质']):
            result['intent'] = 'properties'
        elif any(kw in intent_text for kw in ['储存', '贮存', '保管', '存放']):
            result['intent'] = 'storage'
        elif any(kw in intent_text for kw in ['运输', 'UN']):
            result['intent'] = 'transport'
        elif any(kw in intent_text for kw in ['急救', '中毒']):
            result['intent'] = 'first_aid'
        elif any(kw in intent_text for kw in ['防护', '个体防护']):
            result['intent'] = 'protection'
        elif any(kw in intent_text for kw in ['消防', '灭火', '火灾']):
            result['intent'] = 'fire'
        elif any(kw in intent_text for kw in ['稳定性', '反应性']):
            result['intent'] = 'stability'
        
        return result
    
    def locate_chapters(self, query: str) -> List[int]:
        """
        根据查询定位相关章节
        
        参数:
            query: 用户查询
        
        返回:
            章节编号列表，如 [11] 表示第11章
        """
        analysis = self.analyze_query(query)
        return analysis['target_chapters']
    
    def get_chapter_name(self, chapter_num: int) -> str:
        """获取章节名称"""
        return self.CHAPTER_MAPPING.get(chapter_num, "未知章节")
    
    def extract_relevant_content(self, chapter_content: str, keywords: List[str], 
                                 context_lines: int = 3) -> List[Dict]:
        """
        从章节内容中提取相关段落
        
        参数:
            chapter_content: 章节完整内容
            keywords: 关键词列表
            context_lines: 上下文行数
        
        返回:
            [{'text': '段落内容', 'line_start': 10, 'line_end': 15, 'keyword': '毒性'}]
        """
        if not keywords or not chapter_content:
            return []
        
        lines = chapter_content.split('\n')
        relevant_sections = []
        
        for i, line in enumerate(lines):
            for keyword in keywords:
                if keyword in line:
                    # 提取上下文
                    start = max(0, i - context_lines)
                    end = min(len(lines), i + context_lines + 1)
                    
                    context = '\n'.join(lines[start:end])
                    
                    relevant_sections.append({
                        'text': context,
                        'line_start': start,
                        'line_end': end,
                        'keyword': keyword,
                        'matched_line': i
                    })
                    break  # 每行只匹配一次
        
        return relevant_sections


def test_locator():
    """测试智能定位器"""
    locator = SmartChapterLocator()
    
    test_cases = [
        "丙醇的毒性",
        "甲醛的危险性",
        "乙醇的理化性质",
        "硫酸的储存条件",
        "氨气的急救措施",
        "苯的运输要求",
        "丙酮的防护措施",
        "甲苯的稳定性",
        "乙醚的生态毒性",
        "氯气的消防措施"
    ]
    
    print("=" * 70)
    print("智能章节定位测试")
    print("=" * 70)
    print()
    
    for query in test_cases:
        analysis = locator.analyze_query(query)
        
        print(f"查询: {query}")
        print(f"  化学品: {analysis['chemical_name']}")
        print(f"  意图: {analysis['intent']}")
        print(f"  目标章节: {analysis['target_chapters']}")
        
        if analysis['target_chapters']:
            chapter_names = [locator.get_chapter_name(ch) for ch in analysis['target_chapters']]
            print(f"  章节名称: {', '.join(chapter_names)}")
        
        print(f"  关键词: {', '.join(analysis['keywords'])}")
        print()


if __name__ == '__main__':
    test_locator()
