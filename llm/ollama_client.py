import requests
import json

def ask_llm(prompt):
    """发送 prompt 给本地 Ollama，返回回答字符串"""
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": "qwen2.5:1.5b",
        "prompt": prompt,
        "stream": False
    }
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        result = response.json()
        return result['response']
    else:
        return f"错误：{response.status_code}"

# 测试
if __name__ == "__main__":
    print(ask_llm("用一句话推荐一个可爱的盲盒"))


def generate_explanation(user_input, profile, recommended_items):
    """
    user_input: 用户最近一句话（字符串）
    profile: 用户画像字典，例如 {"style":"可爱", "max_price":200}
    recommended_items: 推荐商品列表，每个商品是字典，包含 name, price 等
    返回: 一段自然语言的推荐理由（字符串）
    """
    if not recommended_items:
        return "抱歉，没有找到符合你偏好的盲盒，可以试试调整预算或风格。"

    # 只取前3个商品，避免prompt太长
    top_items = recommended_items[:3]
    items_text = "\n".join([f"- {item['name']}，价格{item['price']}元" for item in top_items])

    prompt = f"""
用户说：“{user_input}”
当前用户偏好：{profile}
推荐的盲盒有：
{items_text}

请用一句或两句中文解释：为什么推荐这些款式？（根据风格、预算、IP匹配来回答）
要求：自然、口语化、不要超过50个字。
"""
    return ask_llm(prompt)