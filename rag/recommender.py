"""可解释的商品召回与排序。"""
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import pandas as pd

from config.settings import settings
from user_profile.parser import IP_ALIASES, KEYWORD_ALIASES, STYLE_ALIASES, normalize_profile


SOURCE_URL_RE = re.compile(r"来源:\s*(https?://[^\s]+)", re.I)
HIDDEN_TERMS = ("hidden", "secret", "rare", "隐藏", "稀有")
BLINDBOX_TERMS = ("blind box", "blindbox", "mystery box", "random box", "盲盒", "盒玩", "随机款")
NON_FIGURE_TERMS = ("badge", "card", "enamel pin", "sticker", "徽章", "卡牌", "贴纸")
UNAVAILABLE_TERMS = ("sold out", "out of stock", "售罄", "缺货", "缺貨")
PURPOSE_TERMS = {
    "送礼": ("gift", "礼物", "可爱", "cute", "sanrio", "disney"),
    "自留": ("blind box", "盲盒", "single", "random"),
    "收藏": ("collect", "收藏", "figure", "hidden", "secret", "整盒"),
    "桌面摆件": ("figure", "figurine", "摆件", "公仔", "vinyl"),
}


def extract_source_url(description: str) -> str:
    match = SOURCE_URL_RE.search(str(description or ""))
    return match.group(1).rstrip("，。),]\"'") if match else ""


def _expanded_terms(value: str, alias_map: Dict[str, Iterable[str]]) -> List[str]:
    for canonical, aliases in alias_map.items():
        if value.casefold() == canonical.casefold():
            return [canonical] + list(aliases)
    return [value]


def _contains_any(text: str, terms: Iterable[str]) -> bool:
    lower = text.casefold()
    return any(str(term).casefold() in lower for term in terms if str(term).strip())


def _safe_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _series_key(product: Dict[str, Any]) -> str:
    if product.get("product_url"):
        return "url:" + product["product_url"].casefold()
    name = str(product.get("name", "")).casefold()
    name = re.split(r"\s+-\s+|\s+[–—]\s+", name)[0]
    name = re.sub(r"\b(single|random|confirmed|hidden|secret|full|whole)\b.*$", "", name)
    return "name:" + re.sub(r"\s+", " ", name).strip()


class ProductCatalog:
    """加载商品表并提供硬过滤、加权排序和系列去重。"""

    def __init__(self, data_path: Optional[Path] = None, dataframe: Optional[pd.DataFrame] = None):
        if dataframe is None:
            path = Path(data_path or settings.PRODUCTS_CSV_PATH)
            dataframe = pd.read_csv(path)
        self.dataframe = dataframe.copy()
        self.products = self._prepare_products(self.dataframe)

    @staticmethod
    def _prepare_products(dataframe: pd.DataFrame) -> List[Dict[str, Any]]:
        products = []
        for row in dataframe.fillna("").to_dict("records"):
            product = {
                "id": str(row.get("id", "")),
                "name": str(row.get("name", "")),
                "price": _safe_float(row.get("price")),
                "image_url": str(row.get("image_url", "")),
                "ip": str(row.get("ip", "")),
                "style": str(row.get("style", "")),
                "description": str(row.get("description", "")),
                "shop": str(row.get("shop", "")),
            }
            product["product_url"] = str(row.get("product_url") or extract_source_url(product["description"]))
            product["_search_text"] = " ".join(
                [
                    product["name"],
                    product["ip"],
                    product["style"],
                    product["description"],
                    product["shop"],
                ]
            ).casefold()
            products.append(product)
        return products

    def __len__(self) -> int:
        return len(self.products)

    @staticmethod
    def _matches_named_value(product: Dict[str, Any], field: str, value: str, alias_map) -> bool:
        if str(product.get(field, "")).casefold() == value.casefold():
            return True
        return _contains_any(product["_search_text"], _expanded_terms(value, alias_map))

    def _passes_hard_filters(self, product: Dict[str, Any], profile: Dict[str, Any]) -> bool:
        price = product["price"]
        if profile["min_price"] is not None and price < profile["min_price"]:
            return False
        if profile["max_price"] is not None and price > profile["max_price"]:
            return False
        if any(
            self._matches_named_value(product, "ip", value, IP_ALIASES)
            for value in profile["excluded_ips"]
        ):
            return False
        if any(
            self._matches_named_value(product, "style", value, STYLE_ALIASES)
            for value in profile["excluded_styles"]
        ):
            return False
        if any(
            _contains_any(product["_search_text"], _expanded_terms(value, KEYWORD_ALIASES))
            for value in profile["excluded_keywords"]
        ):
            return False
        if profile["accept_hidden"] is False and _contains_any(product["_search_text"], HIDDEN_TERMS):
            return False
        name_text = str(product.get("name", "")).casefold()
        if _contains_any(name_text, UNAVAILABLE_TERMS):
            return False
        if _contains_any(name_text, NON_FIGURE_TERMS) and not _contains_any(name_text, BLINDBOX_TERMS):
            return False
        return True

    def _score(self, product: Dict[str, Any], profile: Dict[str, Any]) -> Tuple[float, List[str]]:
        score = 0.0
        reasons = []

        for value in profile["preferred_ips"]:
            if str(product["ip"]).casefold() == value.casefold():
                score += 8.0
                reasons.append("匹配偏好 IP {}".format(value))
            elif _contains_any(product["_search_text"], _expanded_terms(value, IP_ALIASES)):
                score += 4.0
                reasons.append("商品信息中包含 {}".format(value))

        for value in profile["preferred_styles"]:
            if str(product["style"]).casefold() == value.casefold():
                score += 5.0
                reasons.append("匹配{}风格".format(value))
            elif _contains_any(product["_search_text"], _expanded_terms(value, STYLE_ALIASES)):
                score += 2.0
                reasons.append("具有{}相关元素".format(value))

        for value in profile["keywords"]:
            if _contains_any(product["_search_text"], _expanded_terms(value, KEYWORD_ALIASES)):
                score += 2.5
                reasons.append("包含关键词 {}".format(value))

        for purpose in profile["purposes"]:
            if _contains_any(product["_search_text"], PURPOSE_TERMS.get(purpose, [purpose])):
                score += 1.2
                reasons.append("适合{}".format(purpose))

        if profile["accept_hidden"] is True and _contains_any(product["_search_text"], HIDDEN_TERMS):
            score += 2.0
            reasons.append("包含隐藏或稀有款信息")

        is_blindbox = _contains_any(product["_search_text"], BLINDBOX_TERMS)
        if is_blindbox:
            score += 1.0
        elif _contains_any(product["_search_text"], NON_FIGURE_TERMS):
            score -= 2.0

        target = profile["target_price"]
        if target and target > 0:
            difference = abs(product["price"] - target) / target
            closeness = max(0.0, 3.0 * (1.0 - min(difference, 1.0)))
            score += closeness
            if difference <= 0.2:
                reasons.append("价格接近目标价")
        elif profile["max_price"] is not None:
            score += 0.4
            reasons.append("符合预算上限")

        if product.get("product_url"):
            score += 0.1
        return round(score, 4), list(dict.fromkeys(reasons))

    def search(self, profile: Dict[str, Any], limit: int = 20) -> List[Dict[str, Any]]:
        normalized = normalize_profile(profile)
        scored = []
        target = normalized["target_price"]

        for product in self.products:
            if not self._passes_hard_filters(product, normalized):
                continue
            score, reasons = self._score(product, normalized)
            item = {key: value for key, value in product.items() if not key.startswith("_")}
            item["score"] = score
            item["match_reasons"] = reasons
            scored.append(item)

        scored.sort(
            key=lambda item: (
                -item["score"],
                abs(item["price"] - target) if target is not None else item["price"],
                item["name"].casefold(),
            )
        )

        results = []
        seen_series = set()
        for item in scored:
            series = _series_key(item)
            if series in seen_series:
                continue
            seen_series.add(series)
            results.append(item)
            if len(results) >= limit:
                break
        return results


def rule_reason(product: Dict[str, Any]) -> str:
    reasons = product.get("match_reasons") or []
    if reasons:
        return "，".join(reasons[:2])
    return "符合当前硬性条件，价格为 ¥{:.2f}".format(product.get("price", 0))
