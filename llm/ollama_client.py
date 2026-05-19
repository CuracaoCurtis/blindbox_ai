"""
大模型调用模块
负责：调用本地 Ollama 生成推荐解释
依赖：Ollama 已安装并运行，已拉取模型（如 qwen2.5:7b 或 qwen2.5:3b）
"""

import requests
import json
from typing import Dict, List, Any

# ========== 配置区 ==========
# 如果电脑内存小于8GB，把模型改成 "qwen2.5:3b" 或 "tinyllama"
MODEL_NAME = "qwen2.5:1.5b"
OLLAMA_URL = "http://localhost:11434/api/generate"


# ===========================

def ask_llm(prompt: str, timeout: int = 30) -> str:
    """
    发送 prompt 给本地 Ollama，返回回答字符串
    """
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "options": {
            "num_predict": 100,  # 限制回答长度，避免太长
            "temperature": 0.7
        }
    }
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=timeout)
        if response.status_code == 200:
            result = response.json()
            return result['response'].strip()
        else:
            return f"错误：状态码 {response.status_code}"
    except requests.exceptions.Timeout:
        return "大模型响应超时，请稍后再试。"
    except Exception as e:
        return f"调用大模型出错：{str(e)}"


def generate_explanation(user_input: str, profile: Dict[str, Any], recommended_items: List[Dict]) -> str:
    """
    生成推荐解释
    - user_input: 用户最新的一句话
    - profile: 用户画像字典（例如 {"style":"可爱", "max_price":200, ...}）
    - recommended_items: 商品列表，每个商品是字典，必须包含 name 和 price
    返回: 推荐理由字符串
    """
    if not recommended_items:
        return "暂时没有找到符合你偏好的盲盒，试试换个描述吧～"

    # 只取前3个商品，避免prompt太长
    top_items = recommended_items[:3]
    items_text = "\n".join([f"- {item['name']}，{item['price']}元" for item in top_items])

    # 构建简洁的 prompt
    profile_str = ", ".join([f"{k}={v}" for k, v in profile.items() if v is not None])
    prompt = f"""用户说：“{user_input}”
用户偏好：{profile_str}
推荐商品：
{items_text}

请用一句中文解释为什么推荐这些（结合风格、预算、IP等）。回答简洁自然，不超过40字。"""

    reply = ask_llm(prompt)
    # 如果返回的结果太长或为空，用备用文案
    if len(reply) > 80 or not reply:
        return "这几款在风格和预算上都蛮适合你的～"
    return reply


# ========== 测试代码（单独运行本文件时执行） ==========
if __name__ == "__main__":
    print("测试大模型连接...")
    test_prompt = "你好，请简单介绍一下你自己。"
    print(f"问: {test_prompt}")
    res = ask_llm(test_prompt)
    print(f"答: {res}")

    print("\n测试推荐解释生成...")
    test_profile = {"style": "可爱", "max_price": 150}
    test_items = [
        {"name": "Molly 星座系列", "price": 89},
        {"name": "Skullpanda 森林漫游", "price": 129},
    ]
    explanation = generate_explanation("我喜欢可爱的盲盒", test_profile, test_items)
    print(f"推荐理由: {explanation}")