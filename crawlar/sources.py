from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Iterable

from bs4 import BeautifulSoup

from .http import fetch_text
from .normalize import (
    absolute_url,
    clean_name,
    html_to_text,
    looks_like_blindbox,
    parse_embedded_prices,
    parse_float,
)


@dataclass(frozen=True)
class RawProduct:
    source: str
    shop: str
    raw_id: str
    name: str
    raw_price: str
    currency: str
    image_url: str
    description: str
    url: str


@dataclass(frozen=True)
class ShopifySource:
    source: str
    shop: str
    products_json_url: str
    currency: str = "USD"
    max_pages: int = 8
    filter_keywords: bool = False


@dataclass(frozen=True)
class ShoplineSource:
    source: str
    shop: str
    category_url: str
    currency: str = "TWD"
    max_pages: int = 4


SHOPIFY_SOURCES = [
    ShopifySource("stctoys_blind_box", "STC Toys", "https://stctoys.com/collections/blind-box/products.json", "USD", 6),
    ShopifySource("toptoy_blind_box", "TOP TOY", "https://gotoptoy.com/zh/collections/blind-boxes/products.json", "USD", 4),
    ShopifySource("avo_blindbox_all", "AVO Blind Box", "https://blindboxuk.com/zh-hans/collections/all/products.json", "GBP", 8, True),
    ShopifySource("kidrobot_blind_box", "Kidrobot", "https://www.kidrobot.com/collections/blind-box/products.json", "USD", 3),
    ShopifySource("toy_tokyo_blind_box", "Toy Tokyo", "https://www.toytokyo.com/collections/blind-boxes/products.json", "USD", 3),
    ShopifySource("plastic_empire_blind_box", "Plastic Empire", "https://www.plasticempire.com/collections/blind-box/products.json", "USD", 3),
]


SHOPLINE_SOURCES = [
    ShoplineSource("qek888_blind_box", "QEK888", "https://www.qek888.com/ja/categories/%E7%9B%B2%E7%9B%92", "TWD", 5),
    ShoplineSource("ros_blind_box", "ROS Studio", "https://www.ros.com.tw/categories/%E7%9B%B2%E7%9B%92", "TWD", 3),
    ShoplineSource("kiitos_blind_box", "Kiitos Store", "https://www.kiitosstore.com/categories/box", "TWD", 3),
]


def crawl_all(sleep_seconds: float = 0.2) -> list[RawProduct]:
    rows: list[RawProduct] = []
    for source in SHOPIFY_SOURCES:
        rows.extend(crawl_shopify(source, sleep_seconds=sleep_seconds))
    for source in SHOPLINE_SOURCES:
        rows.extend(crawl_shopline(source, sleep_seconds=sleep_seconds))
    rows.extend(crawl_qtoys())
    rows.extend(crawl_52toys_japan())
    rows.extend(crawl_52toys_official_series())
    rows.extend(crawl_maihefun_official_series())
    return rows


def crawl_shopify(source: ShopifySource, sleep_seconds: float = 0.2) -> list[RawProduct]:
    rows: list[RawProduct] = []
    for page in range(1, source.max_pages + 1):
        url = f"{source.products_json_url}?limit=250&page={page}"
        try:
            data = json.loads(fetch_text(url, sleep_seconds=sleep_seconds))
        except Exception as exc:
            print(f"[WARN] {source.source} page {page}: {exc}")
            break
        products = data.get("products", [])
        if not products:
            break
        for product in products:
            title = clean_name(product.get("title"))
            description = html_to_text(product.get("body_html"))
            if source.filter_keywords and not looks_like_blindbox(title, description):
                continue
            product_url = _shopify_product_url(source.products_json_url, product.get("handle"))
            images = product.get("images") or []
            fallback_image = ""
            if images:
                fallback_image = images[0].get("src") or images[0].get("url") or ""
            variants = product.get("variants") or []
            if not variants:
                rows.append(
                    RawProduct(
                        source.source,
                        source.shop,
                        str(product.get("id") or product.get("handle") or title),
                        title,
                        "",
                        source.currency,
                        fallback_image,
                        description,
                        product_url,
                    )
                )
                continue
            for variant in variants:
                variant_title = clean_name(variant.get("title"))
                variant_name = title
                if variant_title and variant_title.lower() not in {"default title", "default"}:
                    variant_name = f"{title} - {variant_title}"
                featured_image = variant.get("featured_image") or {}
                image_url = featured_image.get("src") or fallback_image
                raw_id = str(variant.get("id") or product.get("id") or product.get("handle") or variant_name)
                rows.append(
                    RawProduct(
                        source.source,
                        source.shop,
                        raw_id,
                        variant_name,
                        str(variant.get("price") or ""),
                        source.currency,
                        image_url,
                        description,
                        product_url,
                    )
                )
        if len(products) < 250:
            break
    print(f"[INFO] {source.source}: {len(rows)} raw rows")
    return rows


def crawl_shopline(source: ShoplineSource, sleep_seconds: float = 0.2) -> list[RawProduct]:
    rows: list[RawProduct] = []
    for page in range(1, source.max_pages + 1):
        url = f"{source.category_url}?page={page}&limit=72"
        try:
            html_text = fetch_text(url, sleep_seconds=sleep_seconds)
        except Exception as exc:
            print(f"[WARN] {source.source} page {page}: {exc}")
            break
        soup = BeautifulSoup(html_text, "lxml")
        cards = soup.select("div.product-item")
        if not cards:
            break
        for card in cards:
            link = card.select_one("a.Product-item") or card.select_one("a[href]")
            ga_product = {}
            if link and link.get("ga-product"):
                try:
                    ga_product = json.loads(link["ga-product"])
                except Exception:
                    ga_product = {}
            title = clean_name(ga_product.get("title") or card.get_text(" ", strip=True))
            text = card.get_text(" ", strip=True)
            prices = parse_embedded_prices(text, source.currency)
            raw_price = str(min((amount for amount, _currency in prices), default=""))
            currency = prices[0][1] if prices else source.currency
            img = card.select_one("img")
            image_url = ""
            if img:
                image_url = img.get("data-src") or img.get("src") or img.get("data-original") or ""
            product_url = absolute_url(link.get("href") if link else "", source.category_url)
            raw_id = str(ga_product.get("id") or product_url or title)
            rows.append(
                RawProduct(
                    source.source,
                    source.shop,
                    raw_id,
                    title,
                    raw_price,
                    currency,
                    absolute_url(image_url, source.category_url),
                    text[:500],
                    product_url,
                )
            )
        if len(cards) < 72:
            break
    print(f"[INFO] {source.source}: {len(rows)} raw rows")
    return rows


def crawl_qtoys() -> list[RawProduct]:
    url = "https://qtoysus.com/product-category"
    try:
        html_text = fetch_text(url)
    except Exception as exc:
        print(f"[WARN] qtoys: {exc}")
        return []
    soup = BeautifulSoup(html_text, "lxml")
    rows: list[RawProduct] = []
    for anchor in soup.select("noscript a[href^='/product/']"):
        text = anchor.get_text(" ", strip=True)
        match = re.match(r"(.+?)\s+—\s+\$(\d+(?:\.\d+)?)", text)
        if not match:
            continue
        name = clean_name(match.group(1))
        price = match.group(2)
        product_url = absolute_url(anchor["href"], url)
        rows.append(
            RawProduct(
                "qtoys_product_category",
                "QTOYS",
                anchor["href"].rsplit("/", 1)[-1],
                name,
                price,
                "USD",
                "",
                "QTOYS official product-category listing; image not provided in noscript list.",
                product_url,
            )
        )
    print(f"[INFO] qtoys_product_category: {len(rows)} raw rows")
    return rows


def crawl_52toys_japan() -> list[RawProduct]:
    base = "https://www.52toys.jp/view/search"
    rows: list[RawProduct] = []
    for page in range(1, 20):
        url = f"{base}?page={page}&search_keyword=BLINDBOX" if page > 1 else f"{base}?search_keyword=BLINDBOX"
        try:
            html_text = fetch_text(url)
        except Exception as exc:
            print(f"[WARN] 52toys_japan page {page}: {exc}")
            break
        soup = BeautifulSoup(html_text, "lxml")
        cards = soup.select("ul.search-item-list li")
        if not cards:
            break
        for card in cards:
            link = card.select_one("a[href]")
            name_el = card.select_one(".search-item-name")
            price_el = card.select_one(".search-item-price")
            img = card.select_one("img")
            name = clean_name(name_el.get_text(" ", strip=True) if name_el else card.get_text(" ", strip=True))
            raw_price = str(parse_float(price_el.get_text(" ", strip=True) if price_el else "") or "")
            image_url = img.get("src") if img else ""
            product_url = absolute_url(link.get("href") if link else "", url)
            rows.append(
                RawProduct(
                    "52toys_japan_search",
                    "52TOYS Japan",
                    product_url.rsplit("/", 1)[-1] or name,
                    name,
                    raw_price,
                    "JPY",
                    image_url,
                    "52TOYS Japan official BLINDBOX search listing.",
                    product_url,
                )
            )
        if len(cards) < 12:
            break
    print(f"[INFO] 52toys_japan_search: {len(rows)} raw rows")
    return rows


def crawl_52toys_official_series() -> list[RawProduct]:
    """Official CN page has IP/series images but no price; keep in raw only."""
    url = "https://www.52toys.com/product/blind_boxes"
    try:
        html_text = fetch_text(url)
    except Exception as exc:
        print(f"[WARN] 52toys_cn_series: {exc}")
        return []
    soup = BeautifulSoup(html_text, "lxml")
    rows = []
    for img in soup.select(".iptab-swiper img[alt], .iptabs-swiper img[alt]"):
        name = clean_name(img.get("alt"))
        if not name:
            continue
        rows.append(
            RawProduct(
                "52toys_cn_series",
                "52TOYS China Official",
                name,
                name,
                "",
                "CNY",
                absolute_url(img.get("src"), url),
                "52TOYS China official blind-box/static-toy IP series; no price shown on the page.",
                url,
            )
        )
    print(f"[INFO] 52toys_cn_series: {len(rows)} raw rows")
    return rows


def crawl_maihefun_official_series() -> list[RawProduct]:
    """A Chinese blind-box brand landing page; no per-SKU price, retained in raw."""
    url = "https://www.maihefun.com/"
    try:
        html_text = fetch_text(url)
    except Exception as exc:
        print(f"[WARN] maihefun_series: {exc}")
        return []
    soup = BeautifulSoup(html_text, "lxml")
    text = soup.get_text(" ", strip=True)
    rows: list[RawProduct] = []
    for match in re.finditer(r"([A-Za-z0-9+\-\s]{2,30}系列)", text):
        name = clean_name(match.group(1))
        rows.append(
            RawProduct(
                "maihefun_series",
                "麦和",
                name,
                name,
                "",
                "CNY",
                "",
                "麦和官方潮玩盲盒品牌页面系列信息；页面未展示单品价格。",
                url,
            )
        )
    print(f"[INFO] maihefun_series: {len(rows)} raw rows")
    return rows


def _shopify_product_url(products_json_url: str, handle: str | None) -> str:
    if not handle:
        return products_json_url
    root = products_json_url.split("/collections/", 1)[0]
    return f"{root}/products/{handle}"

