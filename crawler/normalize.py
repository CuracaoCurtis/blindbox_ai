from __future__ import annotations

import hashlib
import html
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup


EXCHANGE_TO_CNY = {
    "CNY": 1.0,
    "USD": 7.20,
    "GBP": 9.10,
    "HKD": 0.92,
    "TWD": 0.23,
    "JPY": 0.050,
}


BLINDBOX_KEYWORDS = re.compile(
    r"blind\s*box|blindbox|mystery|surprise|trading|随机|隨機|盲盒|盒玩|抽盒|单抽|單抽|"
    r"pop\s*mart|泡泡|labubu|molly|skullpanda|dimoo|crybaby|hirono|azura|"
    r"finding\s*unicorn|寻找独角兽|尋找獨角獸|shinwoo|nanci|rolife|52toys|toptoy|top toy",
    re.I,
)


IP_RULES: list[tuple[str, tuple[str, ...]]] = [
    ("LABUBU / THE MONSTERS", ("labubu", "the monsters")),
    ("MOLLY", ("molly",)),
    ("SKULLPANDA", ("skullpanda", "skull panda")),
    ("DIMOO", ("dimoo",)),
    ("CRYBABY", ("crybaby", "cry baby")),
    ("HIRONO", ("hirono",)),
    ("AZURA", ("azura",)),
    ("HACIPUPU", ("hacipupu",)),
    ("PUCKY", ("pucky",)),
    ("SWEET BEAN", ("sweet bean",)),
    ("POP MART", ("pop mart", "popmart", "泡泡玛特", "泡泡瑪特")),
    ("52TOYS", ("52toys", "52 toys", "beastbox", "nook", "ninnic", "panda roll", "pandaroll")),
    ("LULU THE PIGGY", ("lulu", "piggy", "罐头猪", "lulu猪", "lulu the piggy")),
    ("TOP TOY", ("top toy", "toptoy")),
    ("ROLIFE / NANCI", ("rolife", "nanci", "若来", "若來")),
    ("FINDING UNICORN", ("finding unicorn", "寻找独角兽", "尋找獨角獸", "shinwoo", "farmer bob")),
    ("SANRIO", ("sanrio", "hello kitty", "kuromi", "my melody", "cinnamoroll", "三丽鸥", "三麗鷗")),
    ("CRAYON SHIN-CHAN", ("crayon shin", "shinchan", "shin-chan", "蜡笔小新", "蠟筆小新")),
    ("DISNEY", ("disney", "stitch", "zootopia", "pixar", "toy story", "迪士尼", "史迪奇", "皮克斯")),
    ("TOM AND JERRY", ("tom and jerry", "tom & jerry", "猫和老鼠", "貓和老鼠")),
    ("DORAEMON", ("doraemon", "哆啦a梦", "哆啦a夢")),
    ("HARRY POTTER", ("harry potter", "哈利波特")),
    ("KIDROBOT", ("kidrobot",)),
    ("TOKIDOKI", ("tokidoki",)),
    ("SONNY ANGEL", ("sonny angel",)),
    ("SMISKI", ("smiski",)),
]


STYLE_RULES: list[tuple[str, tuple[str, ...]]] = [
    ("毛绒挂件", ("plush", "keychain", "pendant", "phone strap", "毛绒", "毛絨", "钥匙扣", "鑰匙扣", "吊饰", "吊飾", "挂件", "掛件")),
    ("可爱风", ("cute", "kawaii", "sweet", "sanrio", "hello kitty", "cinnamoroll", "可爱", "可愛", "萌", "甜")),
    ("治愈系", ("healing", "cozy", "sleep", "dream", "forest", "flower", "garden", "治愈", "療癒", "睡", "梦", "夢", "花园", "花園")),
    ("暗黑潮酷", ("skullpanda", "dark", "horror", "spooky", "monster", "ghost", "goth", "暗黑", "怪物", "幽灵", "幽靈")),
    ("潮酷街头", ("street", "fashion", "cool", "punk", "rock", "urban", "潮", "街头", "街頭", "酷")),
    ("动漫联名", ("anime", "manga", "disney", "sanrio", "crayon", "doraemon", "harry potter", "tom and jerry", "动漫", "動畫", "联名", "聯名")),
    ("奇幻童话", ("fantasy", "fairy", "magic", "unicorn", "wonderland", "童话", "童話", "魔法", "精灵", "精靈")),
    ("食玩生活", ("food", "cafe", "kitchen", "bakery", "wacky mart", "burger", "tea", "coffee", "美食", "厨房", "廚房", "咖啡")),
    ("收藏摆件", ("figure", "figurine", "vinyl", "statue", "art toy", "手办", "手辦", "公仔", "摆件", "擺件")),
]


def html_to_text(value: str | None, max_len: int = 500) -> str:
    if not value:
        return ""
    text = BeautifulSoup(value, "lxml").get_text(" ", strip=True)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_len]


def clean_name(value: str | None) -> str:
    if value is None or value != value:
        value = ""
    text = html.unescape(str(value))
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"<!--.*?-->", "", text)
    return text[:220]


def stable_id(*parts: str) -> str:
    payload = "|".join(parts).encode("utf-8", errors="ignore")
    return hashlib.sha1(payload).hexdigest()[:16]


def absolute_url(value: str | None, base_url: str = "") -> str:
    if value is None or value != value:
        return ""
    value = html.unescape(str(value)).strip()
    if not value:
        return ""
    if value.startswith("//"):
        return "https:" + value
    return urljoin(base_url, value)


def parse_float(value: object) -> float | None:
    if value is None:
        return None
    text = str(value)
    match = re.search(r"(\d+(?:,\d{3})*(?:\.\d+)?)", text)
    if not match:
        return None
    try:
        return float(match.group(1).replace(",", ""))
    except ValueError:
        return None


def to_cny(price: object, currency: str) -> float | None:
    amount = parse_float(price)
    if amount is None:
        return None
    rate = EXCHANGE_TO_CNY.get(currency.upper(), 1.0)
    return round(amount * rate, 2)


def looks_like_blindbox(*parts: str) -> bool:
    text = " ".join(part or "" for part in parts)
    return bool(BLINDBOX_KEYWORDS.search(text))


def infer_ip(*parts: str) -> str:
    text = " ".join(parts).lower()
    for label, needles in IP_RULES:
        if any(needle.lower() in text for needle in needles):
            return label
    return "原创潮玩"


def infer_style(*parts: str) -> str:
    text = " ".join(parts).lower()
    for label, needles in STYLE_RULES:
        if any(needle.lower() in text for needle in needles):
            return label
    return "潮玩盲盒"


def parse_embedded_prices(text: str, default_currency: str) -> list[tuple[float, str]]:
    patterns = [
        (r"NT\$\s*([\d,]+(?:\.\d+)?)", "TWD"),
        (r"HK\$\s*([\d,]+(?:\.\d+)?)", "HKD"),
        (r"US\$\s*([\d,]+(?:\.\d+)?)", "USD"),
        (r"\$\s*([\d,]+(?:\.\d+)?)", default_currency),
        (r"￥\s*([\d,]+(?:\.\d+)?)", "JPY"),
        (r"¥\s*([\d,]+(?:\.\d+)?)", "JPY"),
        (r"([\d,]+)\s*円", "JPY"),
    ]
    found: list[tuple[float, str]] = []
    for pattern, currency in patterns:
        for match in re.finditer(pattern, text):
            amount = parse_float(match.group(1))
            if amount:
                found.append((amount, currency))
    return found
