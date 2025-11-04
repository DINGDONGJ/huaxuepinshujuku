#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI驱动的化学品兼容性分析模块
使用硅基流动API
"""

import requests
import json
import time

# 硅基流动API配置
SILICONFLOW_API_KEY = "sk-qmquiwutnqvgxmbivsqrnpunwnnmufnpbdptwiqnfczqtpfp"
SILICONFLOW_API_BASE = "https://api.siliconflow.cn/v1"

# 可选模型列表（按推理能力排序）
MODEL_NAME = "Qwen/QwQ-32B"                      # ✅ QwQ-32B 推理模型，分析能力强
# MODEL_NAME = "deepseek-ai/DeepSeek-R1"        # DeepSeek推理模型
# MODEL_NAME = "Qwen/Qwen2.5-72B-Instruct"      # Qwen最大模型
# MODEL_NAME = "Qwen/Qwen2.5-14B-Instruct"      # 平衡性能和成本
# MODEL_NAME = "Qwen/Qwen2.5-7B-Instruct"       # 默认，性价比高


def call_siliconflow_api(messages, temperature=0.7, max_tokens=2000):
    """
    调用硅基流动API
    
    参数:
        messages: 消息列表 [{"role": "user", "content": "..."}]
        temperature: 温度参数，越高越随机
        max_tokens: 最大生成tokens
    """
    url = f"{SILICONFLOW_API_BASE}/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {SILICONFLOW_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)  # QwQ-32B需要更长时间推理
        response.raise_for_status()
        
        result = response.json()
        
        if 'choices' in result and len(result['choices']) > 0:
            return {
                'success': True,
                'content': result['choices'][0]['message']['content'],
                'usage': result.get('usage', {})
            }
        else:
            return {
                'success': False,
                'error': '未获取到有效响应'
            }
    
    except requests.exceptions.Timeout:
        return {
            'success': False,
            'error': 'API请求超时'
        }
    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'error': f'API请求失败: {str(e)}'
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'未知错误: {str(e)}'
        }


def construct_compatibility_prompt(chemicals_data):
    """
    构建化学品兼容性分析的Prompt
    
    参数:
        chemicals_data: 化学品数据列表
    """
    prompt = f"""你是专业的化学品安全分析专家。请分析以下{len(chemicals_data)}个化学品的共存安全性。

"""
    
    # 添加每个化学品的关键信息
    for i, chem in enumerate(chemicals_data, 1):
        prompt += f"""【化学品{i}】{chem['name']} 
CAS号: {chem.get('cas', '未知')}
分子式: {chem.get('formula', '未知')}

关键安全信息：
- 危险性分类: {', '.join(chem.get('ghs_categories', ['未提供'])[:5])}
- 不相容物质: {', '.join(chem.get('incompatible', ['未提供'])[:5])}
- 危险性概述: {chem.get('chapter2_summary', '未提供')[:200]}
- 稳定性信息: {chem.get('chapter10_summary', '未提供')[:200]}

"""
    
    prompt += """
请生成专业的化学品共存安全性分析报告，必须使用以下JSON格式输出：

```json
{
  "comparison": {
    "similarities": ["相同点1（如：均为易燃液体）", "相同点2"],
    "differences": ["不同点1（如：毒性等级不同）", "不同点2"]
  },
  "compatibility": {
    "risk_level": "极高风险|高风险|中等风险|低风险",
    "can_coexist": true或false,
    "risk_score": 0-100的数值,
    "incompatible_reasons": ["详细原因1", "原因2"],
    "specific_risks": ["具体风险1（如：混合可能引发火灾）", "风险2"]
  },
  "chemical_reactions": [
    {
      "reactants": ["化学品1", "化学品2"],
      "equation": "化学反应方程式（如：2H2 + O2 → 2H2O）",
      "conditions": "反应条件（如：加热、催化剂等）",
      "products": ["生成物1", "生成物2"],
      "danger_level": "剧烈|中等|缓慢|无明显反应",
      "description": "反应描述和危险性说明"
    }
  ],
  "recommendations": {
    "storage": ["存储建议1", "建议2", "建议3"],
    "handling": ["操作建议1", "建议2"],
    "emergency": ["应急措施1", "措施2"]
  },
  "summary": "一句话总结评估结果"
}
```

**分析要求：**
1. 基于MSDS数据进行分析，确保准确性
2. 重点关注：不相容物质、GHS分类、反应性风险
3. 如果发现不相容组合，必须明确指出
4. **重要：如果化学品之间可能发生化学反应，必须写出化学反应方程式**
5. 反应方程式要准确、配平，并说明反应条件和危险性
6. 如果不会发生反应，chemical_reactions 数组留空 []
7. 建议措施要具体、可操作
8. 只输出JSON，不要其他文字

请开始分析：
"""
    
    return prompt


def analyze_compatibility_with_ai(chemicals_data):
    """
    使用AI分析多个化学品的兼容性
    
    参数:
        chemicals_data: 化学品数据列表
    返回:
        分析报告字典
    """
    # 1. 构建Prompt
    prompt = construct_compatibility_prompt(chemicals_data)
    
    # 2. 调用API
    messages = [
        {
            "role": "system",
            "content": "你是专业的化学品安全分析专家，擅长分析化学品的共存安全性。你必须严格按照JSON格式输出分析结果。"
        },
        {
            "role": "user",
            "content": prompt
        }
    ]
    
    result = call_siliconflow_api(messages, temperature=0.3, max_tokens=2000)
    
    if not result['success']:
        return {
            'success': False,
            'error': result['error']
        }
    
    # 3. 解析AI响应
    try:
        content = result['content'].strip()
        
        # 提取JSON部分（可能包含在```json```代码块中）
        if '```json' in content:
            json_start = content.find('```json') + 7
            json_end = content.find('```', json_start)
            json_str = content[json_start:json_end].strip()
        elif '```' in content:
            json_start = content.find('```') + 3
            json_end = content.find('```', json_start)
            json_str = content[json_start:json_end].strip()
        else:
            json_str = content
        
        # 解析JSON
        report = json.loads(json_str)
        
        return {
            'success': True,
            'report': report,
            'raw_response': content,
            'usage': result.get('usage', {})
        }
    
    except json.JSONDecodeError as e:
        return {
            'success': False,
            'error': f'JSON解析失败: {str(e)}',
            'raw_response': result['content']
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'处理响应失败: {str(e)}'
        }


def extract_chapter_summary(chapter_content, max_length=300):
    """
    提取章节摘要
    
    参数:
        chapter_content: 章节完整内容
        max_length: 最大长度
    """
    if not chapter_content:
        return "未提供"
    
    # 简单截取前N个字符
    summary = chapter_content.strip()[:max_length]
    
    # 如果截断了，添加省略号
    if len(chapter_content) > max_length:
        summary += "..."
    
    return summary


# 测试函数
if __name__ == '__main__':
    print("=" * 60)
    print("AI化学品兼容性分析模块测试")
    print("=" * 60)
    
    # 测试API连接
    test_messages = [
        {
            "role": "user",
            "content": "请用一句话介绍你自己"
        }
    ]
    
    print("\n🔍 测试API连接...")
    result = call_siliconflow_api(test_messages, max_tokens=100)
    
    if result['success']:
        print("✅ API连接成功！")
        print(f"📝 响应: {result['content']}")
        if 'usage' in result:
            print(f"💰 Token使用: {result['usage']}")
    else:
        print(f"❌ API连接失败: {result['error']}")
    
    print("\n" + "=" * 60)

