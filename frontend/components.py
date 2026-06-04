"""
UI组件：商品卡片、侧边栏、聊天区域
"""
import streamlit as st
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DATA_PATH = PROJECT_ROOT / "data" / "products.csv"

@st.cache_data
def load_products():
    """加载商品数据（缓存）"""
    try:
        df = pd.read_csv(DATA_PATH)
        return df
    except Exception:
        return pd.DataFrame()

def display_product_card(product: dict):
    """显示单个商品卡片（与之前 main.py 中的函数相同）"""
    with st.container():
        cols = st.columns([1, 3])
        with cols[0]:
            image_url = product.get('image_url', '')
            if image_url and image_url.startswith('http'):
                try:
                    st.image(image_url, use_container_width=True)
                except Exception:
                    st.markdown("🎴", help="图片加载失败")
            else:
                ip_emoji = {
                    "Molly": "👧", "POP MART": "🎨", "52TOYS": "🤖",
                    "DISNEY": "🐭", "SANRIO": "🐱", "LABUBU": "👹"
                }
                emoji = ip_emoji.get(product.get('ip', ''), "🎁")
                st.markdown(f"<h1 style='text-align: center;'>{emoji}</h1>", unsafe_allow_html=True)
        with cols[1]:
            st.markdown(f"**{product['name']}**")
            st.markdown(f"💰 **¥{product['price']:.2f}**")
            tags = []
            if product.get('ip'):
                tags.append(f"🏷️ {product['ip']}")
            if product.get('style'):
                tags.append(f"🎨 {product['style']}")
            if tags:
                st.markdown(" ".join(tags))
            if product.get('shop'):
                st.caption(f"🏪 {product['shop']}")
        st.divider()

def render_sidebar(profile: dict):
    """渲染侧边栏，显示用户画像"""
    with st.sidebar:
        st.markdown("## 🧑‍🎨 你的偏好画像")
        style_val = profile.get('style')
        if style_val:
            st.success(f"🎨 风格: {style_val}")
        else:
            st.info("🎨 风格: 未设置")

        ip_val = profile.get('ip')
        if ip_val:
            st.success(f"🏷️ IP偏好: {ip_val}")
        else:
            st.info("🏷️ IP偏好: 未设置")

        max_price = profile.get('max_price', 9999)
        if max_price < 9999:
            st.success(f"💰 预算: ¥{max_price:.0f}以内")
        else:
            st.info("💰 预算: 未设置")

        if profile.get('accept_hidden'):
            st.success("✨ 接受隐藏款溢价")

        purpose = profile.get('purpose')
        if purpose:
            st.success(f"🎯 用途: {purpose}")

        st.divider()
        st.markdown("### 📊 数据统计")
        df = load_products()
        if not df.empty:
            st.metric("📦 商品总数", len(df))
            st.metric("💰 均价", f"¥{df['price'].mean():.0f}")
            st.metric("📏 价格区间", f"¥{df['price'].min():.0f}-{df['price'].max():.0f}")

        st.divider()
        if st.button("🔄 重置所有偏好", use_container_width=True):
            for key in list(profile.keys()):
                if key in ["min_price", "max_price"]:
                    profile[key] = 0 if key == "min_price" else 9999
                elif key == "accept_hidden":
                    profile[key] = False
                else:
                    profile[key] = None
            st.rerun()

def display_chat_messages(messages: list):
    """显示聊天历史（每条消息及其商品卡片）"""
    for msg in messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            if msg.get("items"):
                for item in msg["items"]:
                    display_product_card(item)