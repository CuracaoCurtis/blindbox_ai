"""
前端模块 - UI组件与页面逻辑
"""
from .components import display_product_card, render_sidebar, display_chat_messages
from .state import init_session_state, get_profile, update_profile_state
from .quick_actions import handle_quick_prompt

__version__ = "1.0.0"
__all__ = [
    "display_product_card",
    "render_sidebar",
    "display_chat_messages",
    "init_session_state",
    "get_profile",
    "update_profile_state",
    "handle_quick_prompt",
]