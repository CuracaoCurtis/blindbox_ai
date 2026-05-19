"""
主程序：Streamlit 聊天界面
整合用户画像、RAG检索、大模型推荐解释
"""
import streamlit as st
import sys
import os

# 添加项目根目录到 Python 路径（确保能导入其他模块）
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# ========== 导入各模块（部分模块可能还未完成，用 try-except 保护） ==========
try:
    from llm.ollama_client import generate_explanation
except ImportError:
    # 如果大模型模块没写好，用备用函数
    def generate_explanation(user_input, profile, items):
        return "（大模型模块未就绪）这几款挺适合你的～"

# TODO: 等组员完成以下模块后，取消注释并删除对应的假函数
# from user_profile.parser import update_profile
# from rag.searcher import search_by_tags

# ========== 临时假函数（等组员完成后替换） ==========
def update_profile_fake(user_input, current_profile):
    """假函数：模拟更新用户画像"""
    # 简单关键词匹配示例
    profile = current_profile.copy()
    if "可爱" in user_input:
        profile["style"] = "可爱"
    if "预算" in user_input:
        import re
        match = re.search(r'(\d+)', user_input)
        if match:
            profile["max_price"] = int(match.group(1))
    return profile, None  # 返回新画像和追问（None表示不需要追问）

def search_by_tags_fake(profile, top_k=3):
    """假函数：模拟检索商品"""
    # 返回一些假商品数据
    fake_items = [
        {"name": "Molly 星座系列", "price": 89, "image_url": "", "ip": "Molly", "style": "可爱"},
        {"name": "Skullpanda 森林漫游", "price": 129, "image_url": "", "ip": "Skullpanda", "style": "治愈"},
        {"name": "Dimoo 太空旅行", "price": 99, "image_url": "", "ip": "Dimoo", "style": "可爱"},
    ]
    return fake_items[:top_k]
# ===================================================

# ========== 主界面 ==========
st.set_page_config(page_title="盲盒AI导购", page_icon="🎁")
st.title("🎁 盲盒AI智能导购")
st.caption("告诉我你的喜好，我来帮你挑盲盒～")

# 初始化 session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "profile" not in st.session_state:
    # 初始画像（字段可扩展）
    st.session_state.profile = {
        "style": None,
        "ip": None,
        "min_price": 0,
        "max_price": 9999,
        "accept_hidden": False,
        "purpose": None
    }

# 显示历史对话
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        # 如果消息中包含推荐商品，额外展示卡片（可选）
        if msg.get("items"):
            for item in msg["items"]:
                col1, col2 = st.columns([1, 3])
                with col1:
                    # 如果有图片URL，可以显示；没有则显示占位符
                    if item.get("image_url"):
                        st.image(item["image_url"], width=80)
                    else:
                        st.write("🎴")
                with col2:
                    st.write(f"**{item['name']}**  ¥{item['price']}")

# 输入框
if user_input := st.chat_input("例如：我喜欢可爱的盲盒，预算200以内"):
    # 1. 显示用户消息
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    # 2. 更新用户画像（TODO: 等组员完成模块后，替换为真实函数）
    # new_profile, ask = update_profile(user_input, st.session_state.profile)
    new_profile, ask = update_profile_fake(user_input, st.session_state.profile)
    st.session_state.profile = new_profile

    # 3. 检索推荐商品（TODO: 替换为真实函数）
    # recommended = search_by_tags(st.session_state.profile, top_k=3)
    recommended = search_by_tags_fake(st.session_state.profile, top_k=3)

    # 4. 生成回复
    if ask:
        reply = ask
        reply_items = []
    else:
        # 调用大模型生成推荐解释
        explanation = generate_explanation(user_input, st.session_state.profile, recommended)
        # 构建回复文本
        reply = explanation + "\n\n"
        for idx, item in enumerate(recommended, 1):
            reply += f"{idx}. {item['name']} - ¥{item['price']}\n"
        reply_items = recommended

    # 5. 保存并显示助手回复
    st.session_state.messages.append({
        "role": "assistant",
        "content": reply,
        "items": reply_items
    })
    with st.chat_message("assistant"):
        st.write(reply)
        if reply_items:
            for item in reply_items:
                col1, col2 = st.columns([1, 3])
                with col1:
                    st.write("🎴")  # 占位图
                with col2:
                    st.write(f"**{item['name']}**  ¥{item['price']}")