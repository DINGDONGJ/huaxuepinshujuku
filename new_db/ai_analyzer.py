#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI驱动的化学品兼容性分析模块
支持多种后端：本地Ollama / 硅基流动API / OpenAI兼容API
"""

import requests
import json
import time
import os

# ============================================================================
# AI后端配置 - 选择使用哪个后端
# ============================================================================
# 可选值: "ollama", "siliconflow", "openai"
AI_BACKEND = os.environ.get("AI_BACKEND", "siliconflow")  # 默认使用硅基流动API

# ============================================================================
# Ollama 本地配置（推荐，免费且隐私安全）
# ============================================================================
OLLAMA_API_BASE = os.environ.get("OLLAMA_API_BASE", "http://localhost:11434/v1")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:7b")  # 推荐模型
# 其他可用模型：
# - qwen2.5:14b      (需要16GB+ 显存/内存)
# - qwen2.5:32b      (需要32GB+ 显存/内存)
# - llama3.1:8b      (通用模型)
# - deepseek-r1:7b   (推理模型)
# - mistral:7b       (快速响应)

# ============================================================================
# 硅基流动API配置（云端，需要API Key）
# ============================================================================
SILICONFLOW_API_KEY = os.environ.get("SILICONFLOW_API_KEY", "sk-qmquiwutnqvgxmbivsqrnpunwnnmufnpbdptwiqnfczqtpfp")
SILICONFLOW_API_BASE = "https://api.siliconflow.cn/v1"
SILICONFLOW_MODEL = "Qwen/QwQ-32B"  # 云端推理模型

# ============================================================================
# OpenAI兼容API配置（可用于其他兼容服务）
# ============================================================================
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_API_BASE = os.environ.get("OPENAI_API_BASE", "https://api.openai.com/v1")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-3.5-turbo")


def get_api_config():
    """根据AI_BACKEND返回对应的API配置"""
    if AI_BACKEND == "ollama":
        return {
            "api_base": OLLAMA_API_BASE,
            "api_key": "",  # Ollama不需要API Key
            "model": OLLAMA_MODEL,
            "timeout_factor": 1.5,  # 本地模型可能需要更多时间
            "name": "Ollama (本地)"
        }
    elif AI_BACKEND == "siliconflow":
        return {
            "api_base": SILICONFLOW_API_BASE,
            "api_key": SILICONFLOW_API_KEY,
            "model": SILICONFLOW_MODEL,
            "timeout_factor": 2,  # 云端推理模型需要更多时间
            "name": "硅基流动"
        }
    elif AI_BACKEND == "openai":
        return {
            "api_base": OPENAI_API_BASE,
            "api_key": OPENAI_API_KEY,
            "model": OPENAI_MODEL,
            "timeout_factor": 1,
            "name": "OpenAI"
        }
    else:
        # 默认使用Ollama
        return {
            "api_base": OLLAMA_API_BASE,
            "api_key": "",
            "model": OLLAMA_MODEL,
            "timeout_factor": 1.5,
            "name": "Ollama (本地)"
        }


def call_ai_api(messages, temperature=0.7, max_tokens=5000, timeout=None, retry_count=2):
    """
    调用AI API（支持多种后端，带重试机制）
    
    参数:
        messages: 消息列表 [{"role": "user", "content": "..."}]
        temperature: 温度参数，越高越随机
        max_tokens: 最大生成tokens
        timeout: 超时时间（秒），None则根据prompt长度自动计算
        retry_count: 重试次数（默认2次）
    """
    config = get_api_config()
    url = f"{config['api_base']}/chat/completions"
    
    # 构建请求头
    headers = {"Content-Type": "application/json"}
    if config['api_key']:
        headers["Authorization"] = f"Bearer {config['api_key']}"
    
    # 根据prompt长度动态计算超时时间
    if timeout is None:
        prompt_length = len(str(messages))
        base_timeout = 60
        length_factor = max(prompt_length // 1000, 1) * 10
        timeout = int((base_timeout + length_factor) * config['timeout_factor'])
        timeout = max(120, min(timeout, 300))
    
    payload = {
        "model": config['model'],
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False
    }
    
    print(f"🤖 使用AI后端: {config['name']} (模型: {config['model']})")
    
    # 重试机制
    last_error = None
    for attempt in range(retry_count + 1):
        try:
            if attempt > 0:
                wait_time = attempt * 3
                print(f"⚠️  第{attempt}次重试，等待{wait_time}秒...")
                time.sleep(wait_time)
                timeout = int(timeout * 1.5)
            
            response = requests.post(url, headers=headers, json=payload, timeout=timeout)
            response.raise_for_status()
            
            result = response.json()
            
            if 'choices' in result and len(result['choices']) > 0:
                return {
                    'success': True,
                    'content': result['choices'][0]['message']['content'],
                    'usage': result.get('usage', {}),
                    'backend': config['name']
                }
            else:
                return {
                    'success': False,
                    'error': '未获取到有效响应'
                }
        
        except requests.exceptions.ConnectionError as e:
            if AI_BACKEND == "ollama":
                last_error = f'无法连接到Ollama服务，请确保Ollama正在运行 (ollama serve)'
            else:
                last_error = f'API连接失败: {str(e)}'
            if attempt < retry_count:
                continue
            return {
                'success': False,
                'error': last_error
            }
        except requests.exceptions.Timeout as e:
            last_error = f'API请求超时（超时时间: {timeout}秒）'
            if attempt < retry_count:
                continue
            return {
                'success': False,
                'error': last_error
            }
        except requests.exceptions.RequestException as e:
            last_error = f'API请求失败: {str(e)}'
            if attempt < retry_count:
                continue
            return {
                'success': False,
                'error': last_error
            }
        except Exception as e:
            last_error = f'未知错误: {str(e)}'
            if attempt < retry_count:
                continue
            return {
                'success': False,
                'error': last_error
            }
    
    return {
        'success': False,
        'error': f'重试{retry_count}次后仍然失败: {last_error}'
    }


# 保持向后兼容的别名
def call_siliconflow_api(messages, temperature=0.7, max_tokens=5000, timeout=None, retry_count=2):
    """向后兼容的别名函数"""
    return call_ai_api(messages, temperature, max_tokens, timeout, retry_count)


def construct_compatibility_prompt(chemicals_data):
    """
    构建化学品兼容性分析的Prompt（精简版）
    
    参数:
        chemicals_data: 化学品数据列表
    """
    # 构建化学品信息（紧凑格式）
    chem_list = []
    for i, chem in enumerate(chemicals_data, 1):
        ghs = ', '.join(chem.get('ghs_categories', [])[:5]) or '无'
        incomp = ', '.join(chem.get('incompatible', [])[:5]) or '无'
        chem_list.append(
            f"【{i}】{chem['name']} (CAS:{chem.get('cas','?')}, 式:{chem.get('formula','?')})\n"
            f"    GHS: {ghs}\n"
            f"    禁配: {incomp}"
        )
    
    prompt = f"""分析以下{len(chemicals_data)}个化学品的共存安全性：

{chr(10).join(chem_list)}

输出JSON格式：
{{"risk_level":"safe|conditional|incompatible","reason":"原因说明","conditions":"安全措施(仅conditional需要,否则空字符串)","reactions":["化学反应方程式"]}}

说明：
- safe: 安全共存,无明显反应风险
- conditional: 需防护措施可控(如隔离/通风/温控)
- incompatible: 严禁共存,会剧烈反应/爆炸/放毒气

仅输出JSON,勿添加其他文字。"""
    
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
            "content": "你是化学品安全专家，分析化学品共存安全性。严格按JSON格式输出，不要添加额外说明。"
        },
        {
            "role": "user",
            "content": prompt
        }
    ]
    
    # 根据化学品数量动态调整参数
    num_chemicals = len(chemicals_data)
    # 化学品越多，需要的tokens越多，但也要考虑超时风险
    max_tokens = min(3000 + (num_chemicals - 2) * 500, 4000)
    
    result = call_ai_api(messages, temperature=0.3, max_tokens=max_tokens, retry_count=2)
    
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
    
    # 显示当前配置
    config = get_api_config()
    print(f"\n📋 当前AI后端配置:")
    print(f"   后端: {config['name']}")
    print(f"   模型: {config['model']}")
    print(f"   API地址: {config['api_base']}")
    
    # 测试API连接
    test_messages = [
        {
            "role": "user",
            "content": "请用一句话介绍你自己"
        }
    ]
    
    print("\n🔍 测试API连接...")
    result = call_ai_api(test_messages, max_tokens=100)
    
    if result['success']:
        print("✅ API连接成功！")
        print(f"📝 响应: {result['content']}")
        if 'usage' in result and result['usage']:
            print(f"💰 Token使用: {result['usage']}")
    else:
        print(f"❌ API连接失败: {result['error']}")
        if AI_BACKEND == "ollama":
            print("\n💡 提示: 请确保Ollama正在运行")
            print("   启动命令: ollama serve")
            print(f"   拉取模型: ollama pull {OLLAMA_MODEL}")
    
    print("\n" + "=" * 60)

