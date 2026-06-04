"""
Streamlit Session State 管理
"""
import streamlit as st

DEFAULT_PROFILE = {
    "style": None,
    "ip": None,
    "min_price": 0,
    "max_price": 9999,
    "accept_hidden": False,
    "purpose": None
}

def init_session_state():
    """初始化所有 session_state 变量"""
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "你好！我是盲盒AI导购🤖\n\n告诉我你的偏好，比如：\n• 喜欢的风格（可爱/治愈/酷炫）\n• 预算范围\n• 偏好的IP（Molly/泡泡玛特等）\n\n我会为你推荐合适的盲盒～", "items": []}
        ]
    if "profile" not in st.session_state:
        st.session_state.profile = DEFAULT_PROFILE.copy()

def get_profile() -> dict:
    """获取当前用户画像"""
    return st.session_state.profile

def update_profile_state(new_profile: dict):
    """更新 session_state 中的画像"""
    st.session_state.profile = new_profile

def add_message(role: str, content: str, items: list = None):
    """添加一条消息到历史"""
    st.session_state.messages.append({
        "role": role,
        "content": content,
        "items": items or []
    })