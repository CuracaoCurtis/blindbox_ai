"""
大模型调用模块（Ollama 本地版）
负责：底层与 Ollama 通信、生成推荐解释
"""

import requests
import json
import time

# ========== 配置（根据你的实际情况修改）==========
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5:1.5b"  # 如果下载的是 3b，改成 "qwen2.5:3b"
TIMEOUT = 30  # 请求超时（秒）


# ==============================================

def ask_llm(prompt: str, temperature: float = 0.7, max_tokens: int = 200) -> str:
    """
    发送 prompt 给本地 Ollama，返回回答字符串。
    若失败返回空字符串。

    参数:
        prompt: 用户提示词
        temperature: 随机性（0~1）
        max_tokens: 回答最大长度
    """
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": temperature,
            "max_tokens": max_tokens
        }
    }
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=TIMEOUT)
        if response.status_code == 200:
            result = response.json()
            return result.get("response", "").strip()
        else:
            print(f"[Ollama] HTTP 错误 {response.status_code}")
            return ""
    except requests.exceptions.Timeout:
        print("[Ollama] 请求超时，请检查模型是否运行缓慢")
        return ""
    except requests.exceptions.ConnectionError:
        print("[Ollama] 无法连接，请确认 Ollama 已启动（终端输入 ollama serve）")
        return ""
    except Exception as e:
        print(f"[Ollama] 未知错误: {e}")
        return ""


def generate_explanation(user_input: str, profile: dict, recommended_items: list) -> str:
    """
    生成推荐解释（供 main.py 调用）

    参数:
        user_input: 用户本轮输入
        profile: 用户画像字典（例如 {"style":"可爱","max_price":200}）
        recommended_items: 推荐商品列表，每个元素是 dict（至少含 name, price）

    返回:
        推荐理由字符串（不超过 50 字）
    """
    if not recommended_items:
        return "没有找到完全符合你偏好的盲盒，试试调整一下预算或风格吧～"

    # 只取前3个商品，避免 prompt 过长
    top3 = recommended_items[:3]
    items_text = "\n".join(
        f"- {item['name']}（{item.get('price', '?')}元）"
        for item in top3
    )

    prompt = f"""用户说：{user_input}
当前偏好：{profile}
推荐商品：
{items_text}
请用一句中文解释为什么推荐这些（根据风格、预算、IP匹配），不超过40字。"""

    reply = ask_llm(prompt, temperature=0.7, max_tokens=100)
    if reply:
        return reply
    else:
        # 降级方案（大模型挂掉时使用）
        return "这几款在风格和预算上都挺适合你的，可以看看哦～"


# ========== 简单测试（直接运行此文件时执行）==========
if __name__ == "__main__":
    test_profile = {"style": "可爱", "max_price": 200}
    test_items = [
        {"name": "草莓熊盲盒", "price": 89},
        {"name": "Molly 职业系列", "price": 129}
    ]
    explanation = generate_explanation("我喜欢可爱的，预算200以内", test_profile, test_items)
    print("推荐理由:", explanation)