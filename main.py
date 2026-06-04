"""
盲盒AI智能导购系统 - 使用模块化前端组件
"""
import streamlit as st
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# 导入前端组件
from frontend import (
    init_session_state,
    render_sidebar,
    display_chat_messages,
    get_profile,
    update_profile_state,
    handle_quick_prompt
)

# 导入其他模块
from user_profile.parser import update_profile
from rag.searcher import search_by_tags
from llm.ollama_client import generate_explanation

# 页面配置
st.set_page_config(page_title="盲盒AI智能导购", page_icon="🎁", layout="wide")
st.title("🎁 盲盒AI智能导购")
st.caption("告诉我你的喜好，我来帮你挑盲盒～")

# 初始化 session_state
init_session_state()

# 侧边栏
render_sidebar(get_profile())

# 显示历史消息
display_chat_messages(st.session_state.messages)

# 聊天输入框
user_input = st.chat_input("例如：我喜欢可爱的盲盒，预算200以内")

if user_input:
    # 添加用户消息到界面（临时，后面会正式加入）
    with st.chat_message("user"):
        st.write(user_input)

    # 1. 更新画像
    new_profile, ask = update_profile(user_input, get_profile())
    update_profile_state(new_profile)

    # 2. 检索
    recommended = search_by_tags(new_profile)

    # 3. 生成回复
    if ask:
        reply = ask
        reply_items = []
    else:
        if recommended:
            explanation = generate_explanation(user_input, new_profile, recommended)
            items_text = "\n\n".join([
                f"{i + 1}. **{item['name']}** - ¥{item['price']:.2f}"
                for i, item in enumerate(recommended[:5])
            ])
            reply = f"{explanation}\n\n{items_text}"
            reply_items = recommended[:5]
        else:
            reply = "抱歉，没有找到符合的商品～"
            reply_items = []

    # 保存到 session_state
    st.session_state.messages.append({"role": "assistant", "content": reply, "items": reply_items})
    st.session_state.messages.append({"role": "user", "content": user_input, "items": []})  # 用户消息也要存
    st.rerun()

# 快捷按钮区域（放在侧边栏底部）
st.sidebar.markdown("---")
st.sidebar.markdown("### 🚀 快速尝试")
quick_prompts = [
    "我喜欢可爱的，预算200以内",
    "想要Molly系列，300元左右",
    "最近压力大，想要治愈系的",
    "买来送女朋友，她喜欢毛绒的",
    "我是收藏党，想要稀有款",
]
for prompt in quick_prompts:
    if st.sidebar.button(prompt, key=prompt, use_container_width=True):
        handle_quick_prompt(
            prompt,
            update_profile_func=update_profile,
            search_func=search_by_tags,
            explain_func=generate_explanation
        )