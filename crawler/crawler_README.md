# 盲盒 AI 推荐员 - 角色1数据采集

本目录是项目11的角色1交付：从公开网页和公开 JSON 商品列表采集盲盒商品，生成后续清洗、入库、RAG 检索可直接使用的 CSV。

## 输出文件

- `data/products.csv`：最终交付文件，固定字段为 `id,name,price,image_url,ip,style,description,shop`。
- `data/products_raw.csv`：原始抓取结果，保留 source、url、原始价格和币种，便于排查。
- `data/summary.txt`：行数、来源、IP、风格和价格区间统计。
- `docs/brand_field_guide.md`：品牌/IP 覆盖、字段含义、原始价格和币种展示建议。

`price` 已统一换算为人民币近似值，固定汇率写在 `crawler/normalize.py`：
USD=7.20，GBP=9.10，HKD=0.92，TWD=0.23，JPY=0.050。

## 数据来源

优先覆盖知名品牌和 IP，包括 POP MART/泡泡玛特、TOP TOY、52TOYS、Rolife/Nanci、Finding Unicorn、LABUBU、MOLLY、SKULLPANDA、DIMOO、CRYBABY、三丽鸥、蜡笔小新等。

当前爬虫包含：

- Shopify/公开 JSON：STC Toys、TOP TOY、AVO Blind Box、Kidrobot、Toy Tokyo、Plastic Empire。
- Shopline 商品列表页：QEK888、ROS Studio、Kiitos Store。
- 官方/品牌页：QTOYS、52TOYS Japan、52TOYS China、麦和。

爬虫只访问公开页面，不登录，不抓取需要账号权限的数据。

## 运行

```bash
python -m pip install -r requirements.txt
python scripts/crawl_products.py --target-count 1000 --min-count 100
```

验收：

```bash
python - <<'PY'
import pandas as pd
df = pd.read_csv("data/products.csv")
print(df.shape)
print(df.head())
print(df.columns.tolist())
PY
```

## Git 协作建议

```bash
git init
git add .
git commit -m "role1 crawl blind box products"
git status
```

后续角色2可以直接读取 `data/products.csv` 并写入 MySQL。
