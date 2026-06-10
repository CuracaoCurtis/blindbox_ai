"""多轮用户画像解析：AI 优先，确定性规则兜底。"""
import json
import re
from typing import Any, Dict, Iterable, List, Optional


LIST_FIELDS = [
    "preferred_ips",
    "excluded_ips",
    "preferred_styles",
    "excluded_styles",
    "keywords",
    "excluded_keywords",
    "purposes",
]
NUMBER_FIELDS = ["min_price", "max_price", "target_price"]

IP_ALIASES = {
    "MOLLY": ("molly", "茉莉"),
    "SKULLPANDA": ("skullpanda", "骷髅熊猫"),
    "DIMOO": ("dimoo", "蒂莫"),
    "LABUBU / THE MONSTERS": ("labubu", "拉布布", "the monsters"),
    "POP MART": ("pop mart", "popmart", "泡泡玛特", "泡泡瑪特"),
    "52TOYS": ("52toys", "52 toys"),
    "TOP TOY": ("top toy", "toptoy"),
    "SANRIO": ("sanrio", "三丽鸥", "三麗鷗", "hello kitty", "kuromi", "my melody", "cinnamoroll"),
    "DISNEY": ("disney", "迪士尼", "史迪奇", "stitch"),
    "CRAYON SHIN-CHAN": ("crayon shin", "shin-chan", "蜡笔小新", "蠟筆小新"),
    "CRYBABY": ("crybaby", "cry baby"),
    "HIRONO": ("hirono",),
    "PUCKY": ("pucky", "毕奇"),
    "SONNY ANGEL": ("sonny angel",),
    "SMISKI": ("smiski",),
}

STYLE_ALIASES = {
    "可爱风": ("可爱", "可愛", "萌", "cute", "kawaii", "甜美"),
    "治愈系": ("治愈", "療癒", "温暖", "温馨", "放松", "压力大", "心情不好", "healing", "cozy"),
    "潮酷街头": ("酷炫", "帅气", "潮酷", "街头", "潮流", "punk", "cool"),
    "暗黑潮酷": ("暗黑", "哥特", "恐怖", "诡异", "怪物", "幽灵", "dark", "goth"),
    "毛绒挂件": ("毛绒", "毛絨", "毛茸茸", "软乎乎", "挂件", "钥匙扣", "plush", "keychain"),
    "收藏摆件": ("摆件", "擺件", "桌面摆件", "手办", "公仔", "收藏品", "figure", "figurine"),
    "动漫联名": ("动漫", "动画", "聯名", "联名", "anime"),
    "奇幻童话": ("奇幻", "童话", "魔法", "精灵", "fantasy", "fairy"),
    "食玩生活": ("食玩", "咖啡", "甜品", "厨房", "food", "cafe"),
}

PURPOSE_ALIASES = {
    "送礼": ("送礼", "送人", "礼物", "送朋友", "送女朋友", "gift"),
    "自留": ("自留", "自己玩", "自己买"),
    "收藏": ("收藏", "收藏党", "收集"),
    "桌面摆件": ("桌面", "摆件", "装饰", "展示"),
}

KEYWORD_ALIASES = {
    "粉色": ("粉色", "粉红", "pink"),
    "蓝色": ("蓝色", "藍色", "blue"),
    "紫色": ("紫色", "purple"),
    "白色": ("白色", "white"),
    "黑色": ("黑色", "black"),
    "整盒": ("整盒", "端盒", "full tray", "whole box", "full box"),
    "单盒": ("单盒", "單盒", "single box", "random box"),
}

NEGATIVE_WORDS = ("不要", "不喜欢", "不想要", "排除", "避开", "拒绝", "别要")
REPLACE_WORDS = ("换成", "改成", "改为", "只要")
RESET_WORDS = ("重置偏好", "清空偏好", "重新开始", "全部重置")
COMPARE_WORDS = ("比较", "对比", "哪个好", "哪款好", "区别")

CHINESE_NUMBERS = {"一": 1, "二": 2, "两": 2, "三": 3, "四": 4, "五": 5}


def default_profile() -> Dict[str, Any]:
    return {
        "preferred_ips": [],
        "excluded_ips": [],
        "preferred_styles": [],
        "excluded_styles": [],
        "keywords": [],
        "excluded_keywords": [],
        "min_price": None,
        "max_price": None,
        "target_price": None,
        "purposes": [],
        "accept_hidden": None,
    }


def _dedupe(values: Iterable[Any]) -> List[str]:
    result = []
    seen = set()
    for value in values:
        text = str(value).strip()
        key = text.casefold()
        if text and key not in seen:
            seen.add(key)
            result.append(text)
    return result


def _as_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, (tuple, set)):
        return list(value)
    return [value]


def _to_number(value: Any) -> Optional[float]:
    if value in (None, "", "null"):
        return None
    try:
        number = float(value)
        return int(number) if number.is_integer() else round(number, 2)
    except (TypeError, ValueError):
        return None


def _canonicalize(value: Any, alias_map: Dict[str, Iterable[str]]) -> str:
    text = str(value).strip()
    lower = text.casefold()
    for canonical, aliases in alias_map.items():
        if lower == canonical.casefold() or any(lower == alias.casefold() for alias in aliases):
            return canonical
    return text


def normalize_profile(profile: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """标准化画像，并兼容旧版单值字段。"""
    result = default_profile()
    source = profile or {}
    for field in LIST_FIELDS:
        result[field] = _dedupe(_as_list(source.get(field)))
    for field in NUMBER_FIELDS:
        result[field] = _to_number(source.get(field))

    hidden = source.get("accept_hidden")
    result["accept_hidden"] = hidden if isinstance(hidden, bool) else None

    if source.get("ip"):
        result["preferred_ips"] = _dedupe(result["preferred_ips"] + [_canonicalize(source["ip"], IP_ALIASES)])
    if source.get("style"):
        result["preferred_styles"] = _dedupe(
            result["preferred_styles"] + [_canonicalize(source["style"], STYLE_ALIASES)]
        )
    if source.get("purpose"):
        result["purposes"] = _dedupe(result["purposes"] + [str(source["purpose"])])
    return result


def _is_negative(text: str, start: int) -> bool:
    prefix = text[max(0, start - 18):start]
    clause = re.split(r"[，。！？,.;；]", prefix)[-1]
    return any(word in clause for word in NEGATIVE_WORDS)


def _find_aliases(text: str, alias_map: Dict[str, Iterable[str]]) -> Dict[str, bool]:
    found = {}
    lower = text.casefold()
    for canonical, aliases in alias_map.items():
        negative = False
        matched = False
        for alias in aliases:
            index = lower.find(alias.casefold())
            if index >= 0:
                matched = True
                negative = negative or _is_negative(lower, index)
        if matched:
            found[canonical] = negative
    return found


def _add_or_exclude(profile: Dict[str, Any], found: Dict[str, bool], preferred: str, excluded: str) -> None:
    for value, negative in found.items():
        if negative:
            profile[excluded] = _dedupe(profile[excluded] + [value])
            profile[preferred] = [item for item in profile[preferred] if item.casefold() != value.casefold()]
        else:
            profile[preferred] = _dedupe(profile[preferred] + [value])
            profile[excluded] = [item for item in profile[excluded] if item.casefold() != value.casefold()]


def _parse_compare_indices(text: str) -> List[int]:
    indices = []
    for token in re.findall(r"第?\s*([一二两三四五1-5])\s*(?:款|个)", text):
        number = CHINESE_NUMBERS.get(token, int(token) if token.isdigit() else 0)
        if number:
            indices.append(number - 1)
    if not indices and any(word in text for word in COMPARE_WORDS):
        for token in re.findall(r"(?<!\d)([1-5])(?!\d)", text):
            indices.append(int(token) - 1)
    return list(dict.fromkeys(indices))


def _rule_parse(user_input: str, current_profile: Dict[str, Any]) -> Dict[str, Any]:
    text = user_input.strip()
    profile = normalize_profile(current_profile)

    if any(word in text for word in RESET_WORDS):
        return {
            "intent": "reset",
            "profile": default_profile(),
            "ask_question": None,
            "compare_indices": [],
        }

    intent = "compare" if any(word in text for word in COMPARE_WORDS) else "recommend"
    compare_indices = _parse_compare_indices(text)

    ip_found = _find_aliases(text, IP_ALIASES)
    style_found = _find_aliases(text, STYLE_ALIASES)
    keyword_found = _find_aliases(text, KEYWORD_ALIASES)

    if any(word in text for word in REPLACE_WORDS):
        if any(not negative for negative in ip_found.values()):
            profile["preferred_ips"] = []
        if any(not negative for negative in style_found.values()):
            profile["preferred_styles"] = []

    _add_or_exclude(profile, ip_found, "preferred_ips", "excluded_ips")
    _add_or_exclude(profile, style_found, "preferred_styles", "excluded_styles")
    _add_or_exclude(profile, keyword_found, "keywords", "excluded_keywords")

    for purpose, aliases in PURPOSE_ALIASES.items():
        if any(alias.casefold() in text.casefold() for alias in aliases):
            profile["purposes"] = _dedupe(profile["purposes"] + [purpose])

    if re.search(r"(不要|不接受|不想要|排除).{0,6}(隐藏|稀有|secret|hidden)", text, re.I):
        profile["accept_hidden"] = False
    elif re.search(r"(隐藏款|稀有款|secret|hidden|接受溢价)", text, re.I):
        profile["accept_hidden"] = True

    range_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:元)?\s*(?:到|至|[-~～])\s*(\d+(?:\.\d+)?)", text)
    target_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:元|块钱)?\s*(?:左右|上下|附近)", text)
    if range_match:
        low, high = sorted([float(range_match.group(1)), float(range_match.group(2))])
        profile["min_price"] = _to_number(low)
        profile["max_price"] = _to_number(high)
        profile["target_price"] = _to_number((low + high) / 2)
    elif target_match:
        target = float(target_match.group(1))
        profile["target_price"] = _to_number(target)
        profile["max_price"] = _to_number(target * 1.2)
    else:
        max_patterns = [
            r"(?:预算|提高到|改到|最多|最高|不超过|别超过)\D{0,8}(\d+(?:\.\d+)?)",
            r"(\d+(?:\.\d+)?)\s*(?:元|块钱)?\s*(?:以内|以下|内)",
        ]
        for pattern in max_patterns:
            match = re.search(pattern, text)
            if match:
                profile["max_price"] = _to_number(match.group(1))
                break

    min_match = re.search(r"(?:至少|最低|不低于)\D{0,8}(\d+(?:\.\d+)?)|(\d+(?:\.\d+)?)\s*(?:元)?\s*以上", text)
    if min_match:
        profile["min_price"] = _to_number(min_match.group(1) or min_match.group(2))

    ask_question = None
    if intent == "recommend":
        has_preference = any(
            profile[field]
            for field in ["preferred_ips", "preferred_styles", "keywords", "purposes"]
        )
        has_budget = any(profile[field] is not None for field in NUMBER_FIELDS)
        if not has_preference:
            ask_question = "你更偏好哪种风格或 IP？例如可爱、毛绒、Molly 或三丽鸥。"
        elif not has_budget:
            ask_question = "你的预算大概是多少？可以告诉我最高预算或价格区间。"

    return {
        "intent": intent,
        "profile": profile,
        "ask_question": ask_question,
        "compare_indices": compare_indices,
    }


def _normalize_update_list(field: str, value: Any) -> List[str]:
    values = _as_list(value)
    if field in ("preferred_ips", "excluded_ips"):
        return _dedupe(_canonicalize(item, IP_ALIASES) for item in values)
    if field in ("preferred_styles", "excluded_styles"):
        return _dedupe(_canonicalize(item, STYLE_ALIASES) for item in values)
    return _dedupe(values)


def _apply_ai_data(base: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
    result = dict(base)
    profile = normalize_profile(base["profile"])
    updates = data.get("profile_updates")
    if not isinstance(updates, dict):
        updates = {}

    clear_fields = set(_as_list(data.get("clear_fields")))
    for field in clear_fields:
        if field in LIST_FIELDS:
            profile[field] = []
        elif field in NUMBER_FIELDS or field == "accept_hidden":
            profile[field] = None

    for field, value in updates.items():
        if field in LIST_FIELDS:
            additions = _normalize_update_list(field, value)
            profile[field] = _dedupe(profile[field] + additions)
        elif field in NUMBER_FIELDS:
            profile[field] = _to_number(value)
        elif field == "accept_hidden" and (isinstance(value, bool) or value is None):
            profile[field] = value

    for preferred, excluded in [
        ("preferred_ips", "excluded_ips"),
        ("preferred_styles", "excluded_styles"),
        ("keywords", "excluded_keywords"),
    ]:
        excluded_values = {item.casefold() for item in profile[excluded]}
        profile[preferred] = [
            item for item in profile[preferred] if item.casefold() not in excluded_values
        ]

    result["profile"] = normalize_profile(profile)
    if data.get("intent") in ("recommend", "compare", "reset"):
        result["intent"] = data["intent"]
    if "ask_question" in data:
        question = data.get("ask_question")
        result["ask_question"] = str(question).strip() if question else None
    if isinstance(data.get("compare_indices"), list):
        valid = []
        for value in data["compare_indices"]:
            try:
                index = int(value)
                if 0 <= index <= 4:
                    valid.append(index)
            except (TypeError, ValueError):
                continue
        result["compare_indices"] = list(dict.fromkeys(valid))
    return result


def parse_user_message(user_input: str, current_profile: Dict[str, Any], llm_client=None) -> Dict[str, Any]:
    """解析一轮输入，返回意图、完整画像、追问和 AI 使用状态。"""
    rule_result = _rule_parse(user_input, current_profile)
    rule_result["ai_used"] = False
    rule_result["ai_failed"] = False

    if rule_result["intent"] == "reset" or llm_client is None or not getattr(llm_client, "configured", False):
        return rule_result

    system_prompt = (
        "你是盲盒导购的意图解析器。只输出 JSON，不要输出解释。"
        "intent 只能是 recommend、compare、reset。"
        "profile_updates 只包含本轮明确新增或修改的字段；列表字段输出完整替换值。"
        "可用字段：preferred_ips、excluded_ips、preferred_styles、excluded_styles、keywords、"
        "excluded_keywords、min_price、max_price、target_price、purposes、accept_hidden。"
        "用户说“换成/改成”时把要替换的字段放入 clear_fields。"
        "compare_indices 使用从 0 开始的上一轮商品位置。"
        "信息足以推荐时 ask_question 为 null；否则只问一个最关键问题。"
    )
    user_payload = {
        "current_profile": normalize_profile(current_profile),
        "user_input": user_input,
        "rule_interpretation": {
            "intent": rule_result["intent"],
            "profile": rule_result["profile"],
            "compare_indices": rule_result["compare_indices"],
        },
        "output_example": {
            "intent": "recommend",
            "profile_updates": {"preferred_ips": ["SANRIO"], "max_price": 200},
            "clear_fields": [],
            "compare_indices": [],
            "ask_question": None,
        },
    }
    data = llm_client.chat_json(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
        ],
        temperature=0.0,
        max_tokens=700,
    )
    if not isinstance(data, dict):
        rule_result["ai_failed"] = True
        return rule_result

    result = _apply_ai_data(rule_result, data)
    result["ai_used"] = True
    result["ai_failed"] = False
    return result


def profile_summary(profile: Dict[str, Any]) -> str:
    normalized = normalize_profile(profile)
    parts = []
    if normalized["preferred_ips"]:
        parts.append("IP：" + "、".join(normalized["preferred_ips"]))
    if normalized["preferred_styles"]:
        parts.append("风格：" + "、".join(normalized["preferred_styles"]))
    if normalized["keywords"]:
        parts.append("关键词：" + "、".join(normalized["keywords"]))
    if normalized["max_price"] is not None:
        parts.append("最高预算：¥{}".format(normalized["max_price"]))
    if normalized["target_price"] is not None:
        parts.append("目标价：¥{}".format(normalized["target_price"]))
    if normalized["purposes"]:
        parts.append("用途：" + "、".join(normalized["purposes"]))
    return "；".join(parts) if parts else "暂无明确偏好"
