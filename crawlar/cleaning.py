from __future__ import annotations

from collections import Counter
from dataclasses import asdict

import pandas as pd

from .normalize import (
    absolute_url,
    clean_name,
    infer_ip,
    infer_style,
    looks_like_blindbox,
    stable_id,
    to_cny,
)
from .sources import RawProduct


FINAL_COLUMNS = ["id", "name", "price", "image_url", "ip", "style", "description", "shop"]


def raw_to_dataframe(rows: list[RawProduct]) -> pd.DataFrame:
    records = [asdict(row) for row in rows]
    if not records:
        return pd.DataFrame(
            columns=[
                "source",
                "shop",
                "raw_id",
                "name",
                "raw_price",
                "currency",
                "image_url",
                "description",
                "url",
            ]
        )
    return pd.DataFrame(records)


def build_products(raw_df: pd.DataFrame) -> pd.DataFrame:
    cleaned: list[dict[str, object]] = []
    for row in raw_df.to_dict("records"):
        name = clean_name(row.get("name"))
        description = clean_name(row.get("description"))
        shop = clean_name(row.get("shop"))
        image_url = absolute_url(row.get("image_url"), row.get("url") or "")
        price = to_cny(row.get("raw_price"), str(row.get("currency") or "CNY"))
        if not name or not shop or not image_url or price is None or price <= 0:
            continue
        if not looks_like_blindbox(name, description, shop):
            continue
        # Product descriptions on marketplace pages often contain related-product
        # marketing text, so IP extraction trusts the title and shop name first.
        ip = infer_ip(name, shop)
        style = infer_style(name, description, shop)
        source_url = str(row.get("url") or "")
        final_desc = description or name
        if source_url and source_url not in final_desc:
            final_desc = f"{final_desc} 来源: {source_url}"
        cleaned.append(
            {
                "id": stable_id(str(row.get("source") or ""), shop, name, str(row.get("raw_id") or ""), source_url),
                "name": name,
                "price": round(float(price), 2),
                "image_url": image_url,
                "ip": ip,
                "style": style,
                "description": final_desc[:500],
                "shop": shop,
            }
        )

    df = pd.DataFrame(cleaned, columns=FINAL_COLUMNS)
    if df.empty:
        return df

    df["_dedupe_name"] = df["name"].str.lower().str.replace(r"\s+", " ", regex=True).str.strip()
    df["_score"] = (
        df["image_url"].astype(bool).astype(int) * 3
        + df["description"].str.len().fillna(0).clip(upper=500) / 500
        + df["price"].notna().astype(int)
    )
    df = (
        df.sort_values(["_dedupe_name", "shop", "_score"], ascending=[True, True, False])
        .drop_duplicates(subset=["shop", "_dedupe_name", "price"], keep="first")
        .drop(columns=["_dedupe_name", "_score"])
        .sort_values(["shop", "ip", "name"])
        .reset_index(drop=True)
    )
    return df[FINAL_COLUMNS]


def validate_products(df: pd.DataFrame, min_count: int) -> list[str]:
    errors: list[str] = []
    if list(df.columns) != FINAL_COLUMNS:
        errors.append(f"columns mismatch: {list(df.columns)}")
    if len(df) < min_count:
        errors.append(f"only {len(df)} valid rows, expected at least {min_count}")
    if not df["id"].is_unique:
        errors.append("id column is not unique")
    for column in ["name", "price", "image_url", "shop"]:
        if df[column].isna().any() or (df[column].astype(str).str.strip() == "").any():
            errors.append(f"{column} contains empty values")
    if (pd.to_numeric(df["price"], errors="coerce") <= 0).any():
        errors.append("price contains non-positive values")
    return errors


def summary_text(df: pd.DataFrame, raw_df: pd.DataFrame) -> str:
    lines = [
        f"Raw rows: {len(raw_df)}",
        f"Valid products: {len(df)}",
        "",
        "Rows by shop:",
    ]
    shop_counts = Counter(df["shop"].tolist()) if not df.empty else Counter()
    lines.extend(f"- {shop}: {count}" for shop, count in shop_counts.most_common())
    lines.append("")
    lines.append("Top IP:")
    ip_counts = Counter(df["ip"].tolist()) if not df.empty else Counter()
    lines.extend(f"- {ip}: {count}" for ip, count in ip_counts.most_common(15))
    lines.append("")
    lines.append("Top style:")
    style_counts = Counter(df["style"].tolist()) if not df.empty else Counter()
    lines.extend(f"- {style}: {count}" for style, count in style_counts.most_common())
    if not df.empty:
        lines.append("")
        lines.append(f"Price range CNY: {df['price'].min():.2f} - {df['price'].max():.2f}")
    return "\n".join(lines)
