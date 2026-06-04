"""
快捷按钮处理逻辑（与 main.py 中的 handle_quick_prompt 类似）
"""
import streamlit as st
from .state import add_message, get_profile, update_profile_state

# 这些函数需要传入实际的画像更新、检索和回复生成逻辑
# 因为会依赖其他模块（user_profile, rag, llm），所以留作回调
def handle_quick_prompt(
    prompt: str,
    update_profile_func,      # 函数：update_profile(user_input, current_profile) -> (new_profile, ask)
    search_func,              # 函数：search_by_tags(profile) -> list[items]
    explain_func              # 函数：generate_explanation(user_input, profile, items) -> str
):
    """
    处理快捷按钮点击，模拟一次完整对话。
    """
    profile = get_profile()
    # 添加用户消息
    add_message("user", prompt)
    # 更新画像
    new_profile, ask = update_profile_func(prompt, profile)
    update_profile_state(new_profile)
    # 检索商品
    recommended = search_func(new_profile)
    # 生成回复
    if ask:
        reply = ask
        reply_items = []
    else:
        if recommended:
            explanation = explain_func(prompt, new_profile, recommended)
            items_text = "\n\n".join([
                f"{i+1}. **{item['name']}** - ¥{item['price']:.2f}"
                for i, item in enumerate(recommended[:5])
            ])
            reply = f"{explanation}\n\n{items_text}"
            reply_items = recommended[:5]
        else:
            reply = "抱歉，没有找到符合的商品～"
            reply_items = []
    add_message("assistant", reply, reply_items)
    st.rerun()