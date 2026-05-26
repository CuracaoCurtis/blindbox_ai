"""
用户画像模块（大模型隐性意图抽取）
负责：解析用户自然语言，更新画像字段，并决定是否追问
"""

import json
from llm.ollama_client import ask_llm  # 调用你的大模型模块


def update_profile(user_input: str, current_profile: dict) -> tuple:
    """
    利用大模型抽取用户偏好，增量更新画像，并返回追问（如果有）。

    参数:
        user_input: 用户本轮输入
        current_profile: 当前画像字典（来自 session state）

    返回:
        (updated_profile, ask_question)
        - updated_profile: 更新后的画像字典
        - ask_question: 如果需要追问，返回问题字符串；否则返回 None
    """
    # 1. 系统提示词（严格控制输出格式）
    system_prompt = (
        "你是一个潮玩盲盒AI导购，负责从用户话语中提取偏好，并更新用户画像。\n"
        "当前支持的字段及处理规则：\n"
        "- style: 风格（如可爱、治愈、酷炫、暗黑）。可根据隐性情绪推导，例如“压力大”→“治愈系”。\n"
        "- ip: IP名称（如 Molly、Skullpanda、Dimoo），没有提及则保留原值。\n"
        "- max_price: 最高预算（数字）。例如“200以内”填200，“不超过100”填100。未提及则保留原值。\n"
        "- accept_hidden: 是否接受隐藏款溢价（布尔值 True/False）。提及“想要隐藏款”、“接受溢价”则为 True。\n"
        "- purpose: 购买目的（如送礼、自留、桌面摆件、收藏）。\n\n"
        "【输出格式要求】\n"
        "严格只返回一个 JSON 字符串，不要包含 ```json 标记或任何额外文字。格式如下：\n"
        "{\n"
        '  "updated_profile": {"style": "...", "ip": "...", "max_price": 数字, "accept_hidden": true/false, "purpose": "..."},\n'
        '  "ask_question": "当 style 或 max_price 关键信息缺失时，这里放一个简短追问；否则填 null"\n'
        "}\n"
        "注意：如果某个字段在输入中没有提及，updated_profile 中就不要包含该字段（或者保留原值，我会合并）。"
    )

    # 2. 组装完整 prompt
    user_prompt = f"当前画像：{json.dumps(current_profile, ensure_ascii=False)}\n用户最新输入：\"{user_input}\"\n请输出 JSON："
    full_prompt = f"{system_prompt}\n\n{user_prompt}"

    try:
        response_text = ask_llm(full_prompt, temperature=0.3, max_tokens=300)
        if not response_text:
            # 大模型无返回，降级返回原画像
            return current_profile, None

        # 3. 清理可能出现的 Markdown 标记
        cleaned = response_text.strip()
        if cleaned.startswith("```"):
            # 去掉 ```json 或 ``` 标记
            cleaned = cleaned.replace("```json", "").replace("```", "").strip()

        data = json.loads(cleaned)

        # 4. 增量更新画像（只更新 LLM 提取到的字段）
        new_profile = current_profile.copy()
        extracted = data.get("updated_profile", {})

        # 字段映射（注意类型转换）
        for key in new_profile.keys():
            if key in extracted and extracted[key] is not None:
                val = extracted[key]
                if key == "max_price":
                    try:
                        new_profile[key] = int(float(val))  # 兼容 "200.0" 或 "200"
                    except (ValueError, TypeError):
                        pass  # 转换失败则保留原值
                elif key == "accept_hidden":
                    if isinstance(val, bool):
                        new_profile[key] = val
                    elif isinstance(val, str):
                        new_profile[key] = val.lower() in ("true", "是", "yes", "1")
                else:
                    new_profile[key] = str(val) if val else None

        ask_question = data.get("ask_question")
        if ask_question in (None, "null", ""):
            ask_question = None

        return new_profile, ask_question

    except json.JSONDecodeError as e:
        print(f"[画像解析] JSON 解析失败: {e}\n原始回复: {response_text}")
        return current_profile, None
    except Exception as e:
        print(f"[画像解析] 未知异常: {e}")
        return current_profile, None


# ========== 本地测试 ==========
if __name__ == "__main__":
    test_profile = {
        "style": None,
        "ip": None,
        "min_price": 0,
        "max_price": 9999,
        "accept_hidden": False,
        "purpose": None
    }
    user_input = "我喜欢可爱的，预算200以内，想要隐藏款"
    new_profile, ask = update_profile(user_input, test_profile)
    print("新画像:", new_profile)
    print("追问:", ask)