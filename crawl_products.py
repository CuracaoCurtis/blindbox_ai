#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from crawler.cleaning import build_products, raw_to_dataframe, summary_text, validate_products
from crawler.sources import crawl_all


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Crawl blind-box product data for role 1.")
    parser.add_argument("--target-count", type=int, default=1000, help="Soft target row count; crawler still keeps all valid rows found.")
    parser.add_argument("--min-count", type=int, default=100, help="Hard validation minimum.")
    parser.add_argument("--out-dir", default=str(PROJECT_ROOT / "data"), help="Output directory.")
    parser.add_argument("--sleep", type=float, default=0.2, help="Small delay used between retry attempts.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    raw_rows = crawl_all(sleep_seconds=args.sleep)
    raw_df = raw_to_dataframe(raw_rows)
    products_df = build_products(raw_df)

    raw_path = out_dir / "products_raw.csv"
    products_path = out_dir / "products.csv"
    summary_path = out_dir / "summary.txt"

    raw_df.to_csv(raw_path, index=False, encoding="utf-8-sig")
    products_df.to_csv(products_path, index=False, encoding="utf-8-sig")
    summary = summary_text(products_df, raw_df)
    summary_path.write_text(summary + "\n", encoding="utf-8")

    print(summary)
    if len(products_df) < args.target_count:
        print(f"[WARN] valid rows below soft target {args.target_count}; kept all usable public data found.")
    errors = validate_products(products_df, args.min_count)
    if errors:
        print("[ERROR] Validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"[OK] wrote {products_path}")
    print(f"[OK] wrote {raw_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

