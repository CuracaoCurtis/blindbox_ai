"""旧画像接口兼容层。"""
from llm.client import get_default_client
from user_profile.parser import parse_user_message


def update_profile(user_input: str, current_profile: dict) -> tuple:
    result = parse_user_message(user_input, current_profile, get_default_client())
    return result["profile"], result["ask_question"]
