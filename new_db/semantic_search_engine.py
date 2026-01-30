#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本地语义搜索引擎
使用 sentence-transformers 实现零成本、高性能的语义搜索
"""

import json
import numpy as np
import os
import pickle
from typing import List, Dict, Tuple
import time

try:
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity
    DEPENDENCIES_AVAILABLE = True
except ImportError:
    DEPENDENCIES_AVAILABLE = False
    print("⚠️  请安装依赖: pip install sentence-transformers scikit-learn")


class LocalSemanticSearchEngine:
    """本地语义搜索引擎"""
    
    # 推荐的中文模型（按性能排序）
    MODELS = {
        'paraphrase-multilingual-MiniLM-L12-v2': {
            'size': '420MB',
            'speed': '快',
            'quality': '好',
            'languages': '50+语言（含中文）',
            'recommended': True
        },
        'paraphrase-multilingual-mpnet-base-v2': {
            'size': '970MB',
            'speed': '中',
            'quality': '很好',
            'languages': '50+语言（含中文）',
            'recommended': False
        },
        'distiluse-base-multilingual-cased-v2': {
            'size': '480MB',
            'speed': '快',
            'quality': '中',
            'languages': '15+语言（含中文）',
            'recommended': False
        }
    }
    
    def __init__(self, model_name='paraphrase-multilingual-MiniLM-L12-v2', cache_dir='semantic_cache', quiet=False):
        """
        初始化语义搜索引擎
        
        参数:
            model_name: 模型名称（推荐使用默认值）
            cache_dir: 缓存目录
            quiet: 静默模式，不输出加载信息
        """
        if not DEPENDENCIES_AVAILABLE:
            raise ImportError("请先安装依赖: pip install sentence-transformers scikit-learn")
        
        self.model_name = model_name
        self.cache_dir = cache_dir
        self.quiet = quiet
        self.embeddings_file = os.path.join(cache_dir, 'embeddings.pkl')
        self.metadata_file = os.path.join(cache_dir, 'metadata.json')
        
        # 创建缓存目录
        os.makedirs(cache_dir, exist_ok=True)
        
        # 加载模型
        if not quiet:
            print(f"📦 正在加载模型: {model_name}")
            print(f"   模型信息: {self.MODELS.get(model_name, {})}")
        
        self.model = SentenceTransformer(model_name)
        
        if not quiet:
            print(f"✅ 模型加载完成")
        
        # 向量缓存
        self.embeddings = {}  # {chemical_id: numpy.array}
        self.metadata = {}    # {chemical_id: {name, cas, aliases, ...}}
        
        # 加载缓存
        self.load_cache()
    
    def load_cache(self):
        """从文件加载缓存的向量"""
        try:
            # 加载向量
            if os.path.exists(self.embeddings_file):
                with open(self.embeddings_file, 'rb') as f:
                    self.embeddings = pickle.load(f)
            
            # 加载元数据
            if os.path.exists(self.metadata_file):
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # 转换键为整数
                    self.metadata = {int(k): v for k, v in data.items()}
        
        except Exception as e:
            if not self.quiet:
                print(f"⚠️  加载缓存失败: {e}")
            self.embeddings = {}
            self.metadata = {}
    
    def save_cache(self):
        """保存向量到文件"""
        try:
            # 保存向量（使用pickle，更高效）
            with open(self.embeddings_file, 'wb') as f:
                pickle.dump(self.embeddings, f)
            
            # 保存元数据（使用JSON，便于查看）
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, ensure_ascii=False, indent=2)
            
            print(f"💾 缓存已保存: {len(self.embeddings)} 个化学品")
        
        except Exception as e:
            print(f"❌ 保存缓存失败: {e}")
    
    def build_index(self, chemicals: List[Dict], batch_size=32):
        """
        批量构建化学品向量索引
        
        参数:
            chemicals: 化学品列表 [{'编号': 1, '中文名': '甲醛', ...}]
            batch_size: 批处理大小（越大越快，但占用更多内存）
        """
        print("=" * 70)
        print(f"🔨 开始构建 {len(chemicals)} 个化学品的语义索引")
        print("=" * 70)
        
        start_time = time.time()
        
        # 准备文本和ID
        texts = []
        ids = []
        
        for chem in chemicals:
            # 构建丰富的文本描述
            text_parts = [
                chem.get('中文名', ''),
                chem.get('英文名', ''),
                chem.get('CAS号', ''),
            ]
            
            # 添加别名
            aliases = chem.get('所有别名', '')
            if aliases and aliases != '-':
                text_parts.append(aliases)
            
            # 添加分子式
            formula = chem.get('分子式', '')
            if formula:
                text_parts.append(formula)
            
            # 合并文本
            text = ' '.join(filter(None, text_parts))
            texts.append(text)
            ids.append(chem['编号'])
            
            # 保存元数据
            self.metadata[chem['编号']] = {
                'name': chem.get('中文名', ''),
                'english_name': chem.get('英文名', ''),
                'cas': chem.get('CAS号', ''),
                'aliases': chem.get('所有别名', ''),
                'formula': chem.get('分子式', '')
            }
        
        # 批量生成向量（比逐个生成快10倍以上）
        print(f"🚀 批量生成向量 (batch_size={batch_size})...")
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=True,
            convert_to_numpy=True
        )
        
        # 保存向量
        for chem_id, embedding in zip(ids, embeddings):
            self.embeddings[chem_id] = embedding
        
        # 保存到文件
        self.save_cache()
        
        elapsed_time = time.time() - start_time
        print("=" * 70)
        print(f"✅ 索引构建完成！")
        print(f"   总耗时: {elapsed_time:.2f}秒")
        print(f"   平均速度: {len(chemicals)/elapsed_time:.1f} 个/秒")
        print(f"   缓存大小: {os.path.getsize(self.embeddings_file)/1024/1024:.2f} MB")
        print("=" * 70)
    
    def add_chemical(self, chemical: Dict):
        """
        增量添加单个化学品
        
        参数:
            chemical: 化学品信息字典
        """
        # 构建文本
        text_parts = [
            chemical.get('中文名', ''),
            chemical.get('英文名', ''),
            chemical.get('CAS号', ''),
            chemical.get('所有别名', ''),
            chemical.get('分子式', '')
        ]
        text = ' '.join(filter(None, text_parts))
        
        # 生成向量
        embedding = self.model.encode(text, convert_to_numpy=True)
        
        # 保存
        chem_id = chemical['编号']
        self.embeddings[chem_id] = embedding
        self.metadata[chem_id] = {
            'name': chemical.get('中文名', ''),
            'english_name': chemical.get('英文名', ''),
            'cas': chemical.get('CAS号', ''),
            'aliases': chemical.get('所有别名', ''),
            'formula': chemical.get('分子式', '')
        }
        
        # 保存到文件
        self.save_cache()
        
        print(f"✅ 已添加化学品: {chemical.get('中文名')} (ID: {chem_id})")
    
    def search(self, query: str, top_k: int = 10, threshold: float = 0.3) -> List[Dict]:
        """
        语义搜索
        
        参数:
            query: 搜索查询（支持自然语言）
            top_k: 返回结果数量
            threshold: 相似度阈值（0-1，低于此值的结果将被过滤）
        
        返回:
            [{'chemical_id': 1, 'score': 0.85, 'name': '甲醛', ...}]
        """
        if not self.embeddings:
            print("⚠️  索引为空，请先构建索引")
            return []
        
        start_time = time.time()
        
        # 1. 生成查询向量
        query_embedding = self.model.encode(query, convert_to_numpy=True)
        
        # 2. 计算相似度
        similarities = {}
        for chem_id, chem_embedding in self.embeddings.items():
            # 余弦相似度
            sim = cosine_similarity(
                query_embedding.reshape(1, -1),
                chem_embedding.reshape(1, -1)
            )[0][0]
            
            # 过滤低相似度结果
            if sim >= threshold:
                similarities[chem_id] = float(sim)
        
        # 3. 排序
        sorted_results = sorted(
            similarities.items(),
            key=lambda x: x[1],
            reverse=True
        )[:top_k]
        
        # 4. 构建返回结果
        results = []
        for chem_id, score in sorted_results:
            meta = self.metadata.get(chem_id, {})
            results.append({
                'chemical_id': chem_id,
                'score': score,
                'name': meta.get('name', ''),
                'english_name': meta.get('english_name', ''),
                'cas': meta.get('cas', ''),
                'aliases': meta.get('aliases', ''),
                'formula': meta.get('formula', '')
            })
        
        elapsed_time = time.time() - start_time
        print(f"🔍 搜索完成: 找到 {len(results)} 个结果 (耗时: {elapsed_time*1000:.0f}ms)")
        
        return results
    
    def get_stats(self) -> Dict:
        """获取索引统计信息"""
        return {
            'total_chemicals': len(self.embeddings),
            'model_name': self.model_name,
            'cache_size_mb': os.path.getsize(self.embeddings_file) / 1024 / 1024 if os.path.exists(self.embeddings_file) else 0,
            'embedding_dimension': len(next(iter(self.embeddings.values()))) if self.embeddings else 0
        }


def main():
    """测试函数"""
    print("=" * 70)
    print("本地语义搜索引擎测试")
    print("=" * 70)
    
    # 初始化引擎
    engine = LocalSemanticSearchEngine()
    
    # 显示统计信息
    stats = engine.get_stats()
    print(f"\n📊 索引统计:")
    print(f"   化学品数量: {stats['total_chemicals']}")
    print(f"   模型: {stats['model_name']}")
    print(f"   向量维度: {stats['embedding_dimension']}")
    print(f"   缓存大小: {stats['cache_size_mb']:.2f} MB")
    
    if stats['total_chemicals'] == 0:
        print("\n⚠️  索引为空，请先运行 build_semantic_index.py 构建索引")
        return
    
    # 测试搜索
    print("\n" + "=" * 70)
    print("测试搜索")
    print("=" * 70)
    
    test_queries = [
        "易燃的液体",
        "有毒化学品",
        "酒精",
        "会爆炸的气体",
        "对皮肤有腐蚀性"
    ]
    
    for query in test_queries:
        print(f"\n🔍 搜索: {query}")
        results = engine.search(query, top_k=5)
        
        if results:
            for i, result in enumerate(results, 1):
                print(f"   {i}. {result['name']} (CAS: {result['cas']}) - 相似度: {result['score']:.3f}")
        else:
            print("   未找到结果")


if __name__ == '__main__':
    main()
