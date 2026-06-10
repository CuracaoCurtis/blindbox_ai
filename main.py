"""盲盒 AI 智能导购 Streamlit 入口。"""
from typing import Any, Dict, List

import streamlit as st

from rag.recommender import ProductCatalog
from shopping_assistant import AI_STATUS_LABELS, ShoppingAssistant
from user_profile.parser import default_profile, normalize_profile


st.set_page_config(
    page_title="盲盒 AI 智能导购",
    page_icon="🎁",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_resource
def get_assistant() -> ShoppingAssistant:
    return ShoppingAssistant(ProductCatalog())


def initialize_state(assistant: ShoppingAssistant) -> None:
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": (
                    "你好，我是盲盒智能导购。告诉我你喜欢的 IP、风格、预算和用途，"
                    "我会持续记住偏好并推荐商品。推荐后也可以说“比较第一款和第三款”。"
                ),
                "items": [],
            }
        ]
    if "profile" not in st.session_state:
        st.session_state.profile = default_profile()
    if "last_items" not in st.session_state:
        st.session_state.last_items = []
    if "ai_status" not in st.session_state:
        st.session_state.ai_status = assistant.initial_ai_status


def process_prompt(prompt: str, assistant: ShoppingAssistant) -> None:
    text = prompt.strip()
    if not text:
        return

    st.session_state.messages.append({"role": "user", "content": text, "items": []})
    result = assistant.process_message(
        text,
        st.session_state.profile,
        st.session_state.last_items,
    )
    st.session_state.profile = result["profile"]
    st.session_state.ai_status = result["ai_status"]
    if result["intent"] == "reset":
        st.session_state.last_items = []
    elif result["items"]:
        st.session_state.last_items = result["items"]
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": result["reply"],
            "items": result["items"],
        }
    )


def display_product_card(product: Dict[str, Any]) -> None:
    with st.container(border=True):
        image_col, detail_col = st.columns([1, 3])
        with image_col:
            image_url = str(product.get("image_url", ""))
            if image_url.startswith("http"):
                st.image(image_url, use_container_width=True)
            else:
                st.markdown("<h1 style='text-align:center'>🎁</h1>", unsafe_allow_html=True)

        with detail_col:
            st.markdown("**{}**".format(product.get("name", "")))
            st.markdown("**¥{:.2f}**".format(float(product.get("price", 0))))
            tags = [str(product.get("ip", "")), str(product.get("style", ""))]
            st.caption(" · ".join(tag for tag in tags if tag))
            if product.get("reason"):
                st.info(product["reason"])
            if product.get("shop"):
                st.caption("来源店铺：{}".format(product["shop"]))
            product_url = str(product.get("product_url", ""))
            if product_url.startswith("http"):
                if hasattr(st, "link_button"):
                    st.link_button("查看来源商品", product_url)
                else:
                    st.markdown("[查看来源商品]({})".format(product_url))


def _show_list(label: str, values: List[str], excluded: bool = False) -> None:
    if not values:
        return
    prefix = "排除" if excluded else label
    st.markdown("**{}：** {}".format(prefix, "、".join(values)))


def render_sidebar(assistant: ShoppingAssistant) -> None:
    profile = normalize_profile(st.session_state.profile)
    status = st.session_state.ai_status

    with st.sidebar:
        st.markdown("## 导购状态")
        if status == "enabled":
            st.success(AI_STATUS_LABELS[status])
        elif status == "degraded":
            st.warning(AI_STATUS_LABELS[status])
        else:
            st.info(AI_STATUS_LABELS[status])
            st.caption("在项目根目录创建 `.env` 并配置 API 后重启即可启用 AI。")

        st.markdown("## 你的偏好画像")
        _show_list("偏好 IP", profile["preferred_ips"])
        _show_list("排除 IP", profile["excluded_ips"], excluded=True)
        _show_list("偏好风格", profile["preferred_styles"])
        _show_list("排除风格", profile["excluded_styles"], excluded=True)
        _show_list("关键词", profile["keywords"])
        _show_list("排除关键词", profile["excluded_keywords"], excluded=True)
        _show_list("用途", profile["purposes"])

        if profile["min_price"] is not None or profile["max_price"] is not None:
            low = profile["min_price"] if profile["min_price"] is not None else 0
            high = profile["max_price"] if profile["max_price"] is not None else "不限"
            st.markdown("**预算：** ¥{} - ¥{}".format(low, high))
        if profile["target_price"] is not None:
            st.markdown("**目标价：** ¥{}".format(profile["target_price"]))
        if profile["accept_hidden"] is True:
            st.markdown("**隐藏款：** 接受并偏好")
        elif profile["accept_hidden"] is False:
            st.markdown("**隐藏款：** 排除")
        if not any(
            profile[field]
            for field in [
                "preferred_ips",
                "excluded_ips",
                "preferred_styles",
                "excluded_styles",
                "keywords",
                "excluded_keywords",
                "purposes",
            ]
        ) and profile["max_price"] is None:
            st.caption("尚未记录偏好")

        st.divider()
        if st.button("重置所有偏好", use_container_width=True):
            process_prompt("重置偏好", assistant)
            st.rerun()

        st.markdown("### 商品数据")
        dataframe = assistant.catalog.dataframe
        st.metric("商品总数", len(dataframe))
        st.metric("平均价格", "¥{:.0f}".format(dataframe["price"].mean()))

        st.markdown("### 快速尝试")
        quick_prompts = [
            "我喜欢可爱的，预算200以内",
            "想要 Molly 系列，300元左右",
            "不要暗黑风，150元内毛绒送礼",
            "最近压力大，想要治愈系，预算250以内",
            "我是收藏党，预算500以内，想要隐藏款",
        ]
        for prompt in quick_prompts:
            if st.button(prompt, key="quick_" + prompt, use_container_width=True):
                process_prompt(prompt, assistant)
                st.rerun()


def render_messages() -> None:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message["role"] == "assistant":
                st.markdown(message["content"])
            else:
                st.write(message["content"])
            for item in message.get("items") or []:
                display_product_card(item)


def main() -> None:
    try:
        assistant = get_assistant()
    except Exception as exc:
        st.error("商品数据加载失败：{}".format(exc))
        st.stop()

    initialize_state(assistant)
    st.title("🎁 盲盒 AI 智能导购")
    st.caption("支持多轮偏好、排除条件、预算、智能推荐和上一轮商品对比")
    render_sidebar(assistant)
    render_messages()

    user_input = st.chat_input("例如：不要暗黑风，想要三丽鸥毛绒，预算200以内")
    if user_input:
        process_prompt(user_input, assistant)
        st.rerun()


if __name__ == "__main__":
    main()
