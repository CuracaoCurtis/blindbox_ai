import json
# 完美复用角色5同学写好的底层调用函数（注意根据实际文件夹大小写调整路径）
from llm.ollama_client import ask_llm


def update_profile(user_input: str, current_profile: dict) -> tuple:
    """
    结合项目实际字段，利用大模型进行隐性意图抽取，并决定是否追问。

    :param user_input: 用户本轮输入的聊天文本
    :param current_profile: 来自 main.py 的 st.session_state.profile
    :return: (updated_profile, ask_question)
    """

    # 1. 严格对照 main.py 的字段结构定制系统提示词
    system_prompt = (
        "你是一个潮玩盲盒领域的AI智能导购，负责分析用户话语中的显性与【隐性意图】，并更新画像。\n"
        "当前系统支持的画像字段及处理规则如下：\n"
        "- style: 风格（需根据情绪隐性推导。如‘压力大’‘不开心’推导为‘治愈系’、‘解压’）\n"
        "- ip: 盲盒IP名称（如：Molly、三丽鸥、Labubu，没有提及则保留原样）\n"
        "- max_price: 用户能接受的最高价格（数字。如‘200以内’填200；未提及或无限制则保留原样）\n"
        "- accept_hidden: 是否接受隐藏款溢价（布尔值 True/False。如提及‘想要隐藏款’、‘无所谓溢价’则为 True）\n"
        "- purpose: 收藏/购买目的（如：送礼、桌面摆件、自留收藏等）\n\n"
        "【输出格式要求】\n"
        "请严格只返回一个标准的 JSON 字符串，绝对不要包含任何 Markdown 标记（如 ```json）。格式如下：\n"
        "{\n"
        '  "updated_profile": {"style": "...", "ip": "...", "max_price": ..., "accept_hidden": ..., "purpose": "..."},\n'
        '  "ask_question": "富有同理心的下一轮追问。如果风格、最高预算等关键信息已齐备，或者用户明确要求看推荐，此处返回 null"\n'
        "}"
    )

    # 2. 组装输入
    user_prompt = f"当前画像状态: {json.dumps(current_profile, ensure_ascii=False)}\n用户最新输入: \"{user_input}\"\n请更新并给出JSON："
    full_prompt = f"{system_prompt}\n\n{user_prompt}"

    try:
        # 3. 直接调用角色5的 ask_llm
        response_text = ask_llm(full_prompt)

        # 容错处理：防止部分小模型不听话带上了 ```json 标记
        if response_text.startswith("```"):
            response_text = response_text.replace("```json", "").replace("```", "").strip()

        result_data = json.loads(response_text)

        # 4. 增量更新画像，防止 LLM 把未提及的字段误擦除
        new_profile = current_profile.copy()
        llm_extracted = result_data.get("updated_profile", {})

        for key in new_profile.keys():
            if key in llm_extracted and llm_extracted[key] is not None:
                # 针对价格和布尔值做基本类型防御
                if key == "max_price":
                    new_profile[key] = int(llm_extracted[key])
                elif key == "accept_hidden":
                    new_profile[key] = bool(llm_extracted[key])
                else:
                    new_profile[key] = str(llm_extracted[key])

        ask_question = result_data.get("ask_question", None)

        # 如果大模型返回的是字符串 "null" 或 None，统一转为 Python 的 None
        if ask_question == "null" or not ask_question:
            ask_question = None

        return new_profile, ask_question

    except Exception as e:
        # 极简降级兜底：大模型万一卡顿或报错，不崩溃，交给下级模块处理
        print(f"[Role 4 Error] 画像解析异常: {e}")
        return current_profile, None