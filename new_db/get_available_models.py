#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取硅基流动API支持的所有模型
"""

import requests
import json

SILICONFLOW_API_KEY = "sk-qmquiwutnqvgxmbivsqrnpunwnnmufnpbdptwiqnfczqtpfp"
SILICONFLOW_API_BASE = "https://api.siliconflow.cn/v1"

def get_available_models():
    """获取可用的模型列表"""
    url = f"{SILICONFLOW_API_BASE}/models"
    
    headers = {
        "Authorization": f"Bearer {SILICONFLOW_API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        result = response.json()
        return result
    
    except Exception as e:
        print(f"❌ 获取模型列表失败: {str(e)}")
        return None

def main():
    print("=" * 80)
    print("🔍 查询硅基流动支持的AI模型")
    print("=" * 80)
    print()
    
    result = get_available_models()
    
    if not result:
        return
    
    if 'data' in result:
        models = result['data']
        
        print(f"✅ 共找到 {len(models)} 个可用模型\n")
        
        # 筛选Qwen系列模型
        qwen_models = [m for m in models if 'qwen' in m.get('id', '').lower() or 'qwq' in m.get('id', '').lower()]
        
        # 筛选DeepSeek系列模型
        deepseek_models = [m for m in models if 'deepseek' in m.get('id', '').lower()]
        
        # 显示Qwen系列
        if qwen_models:
            print("【Qwen系列模型】")
            print("-" * 80)
            for i, model in enumerate(qwen_models, 1):
                model_id = model.get('id', 'N/A')
                print(f"{i}. {model_id}")
                if 'owned_by' in model:
                    print(f"   提供商: {model['owned_by']}")
                if model.get('object') == 'model':
                    print(f"   类型: 聊天模型")
                print()
        
        # 显示DeepSeek系列
        if deepseek_models:
            print("\n【DeepSeek系列模型】")
            print("-" * 80)
            for i, model in enumerate(deepseek_models, 1):
                model_id = model.get('id', 'N/A')
                print(f"{i}. {model_id}")
                if 'owned_by' in model:
                    print(f"   提供商: {model['owned_by']}")
                print()
        
        # 显示其他热门模型
        other_models = [m for m in models if 'qwen' not in m.get('id', '').lower() 
                        and 'deepseek' not in m.get('id', '').lower() 
                        and 'qwq' not in m.get('id', '').lower()]
        
        if other_models:
            print("\n【其他模型】")
            print("-" * 80)
            for i, model in enumerate(other_models[:10], 1):  # 只显示前10个
                model_id = model.get('id', 'N/A')
                print(f"{i}. {model_id}")
            
            if len(other_models) > 10:
                print(f"\n... 还有 {len(other_models) - 10} 个模型")
        
        # 保存完整列表到JSON文件
        with open('available_models.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print("\n" + "=" * 80)
        print(f"💾 完整模型列表已保存到: available_models.json")
        print("=" * 80)
    
    else:
        print("❌ 响应格式不正确")
        print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()

