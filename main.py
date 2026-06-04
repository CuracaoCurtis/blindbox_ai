"""
主程序：Streamlit 聊天界面
整合：用户画像（大模型抽取）、RAG 检索（暂用假函数）、大模型推荐解释
"""

import streamlit as st
import sys
import os

# 确保能导入项目内的模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# ========== 导入真实模块 ==========
from llm.ollama_client import generate_explanation
from user_profile.parser import update_profile   # 使用大模型画像模块

# TODO: 等待 RAG 组员完成后，取消下面注释并删除假函数
# from rag.searcher import search_by_tags

# ========== 临时假函数（等 RAG 同学替换）==========
def search_by_tags_fake(profile, top_k=3):
    """模拟 RAG 检索，返回假商品数据"""
    fake_items = [
        {"name": "Molly 星座系列", "price": 89, "image_url": "", "ip": "Molly", "style": "可爱"},
        {"name": "Skullpanda 森林漫游", "price": 129, "image_url": "", "ip": "Skullpanda", "style": "治愈"},
        {"name": "Dimoo 太空旅行", "price": 99, "image_url": "", "ip": "Dimoo", "style": "可爱"},
    ]
    return fake_items[:top_k]
# =================================================

# ========== Streamlit 页面配置 ==========
st.set_page_config(page_title="盲盒AI导购", page_icon="🎁")
st.title("🎁 盲盒AI智能导购")
st.caption("告诉我你的喜好，我来帮你挑盲盒～")

# ========== 初始化 session_state ==========
if "messages" not in st.session_state:
    st.session_state.messages = []
if "profile" not in st.session_state:
    # 画像字段需与 parser.py 中保持一致
    st.session_state.profile = {
        "style": None,
        "ip": None,
        "min_price": 0,
        "max_price": 9999,
        "accept_hidden": False,
        "purpose": None
    }

# ========== 显示历史对话 ==========
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        # 如果消息包含推荐商品，以卡片形式展示
        if msg.get("items"):
            for item in msg["items"]:
                col1, col2 = st.columns([1, 3])
                with col1:
                    if item.get("image_url"):
                        st.image(item["image_url"], width=80)
                    else:
                        st.write("🎴")  # 占位图
                with col2:
                    st.write(f"**{item['name']}**  ¥{item['price']}")

# ========== 聊天输入框 ==========
user_input = st.chat_input("例如：我喜欢可爱的盲盒，预算200以内，想要隐藏款")

if user_input:
    # 1. 显示用户消息
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    # 2. 更新用户画像（调用大模型抽取模块）
    new_profile, ask = update_profile(user_input, st.session_state.profile)
    st.session_state.profile = new_profile

    # 3. 检索推荐商品（TODO: 替换为真实 RAG 检索）
    # recommended = search_by_tags(st.session_state.profile, top_k=3)
    recommended = search_by_tags_fake(st.session_state.profile, top_k=3)

    # 4. 生成回复
    if ask:
        reply = ask
        reply_items = []
    else:
        # 调用大模型生成推荐解释
        explanation = generate_explanation(user_input, st.session_state.profile, recommended)
        # 组装推荐列表文字
        items_text = "\n".join([f"{i+1}. {item['name']} - ¥{item['price']}" for i, item in enumerate(recommended)])
        reply = f"{explanation}\n\n{items_text}"
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
                    st.write("🎴")
                with col2:
                    st.write(f"**{item['name']}**  ¥{item['price']}")