# 品牌覆盖与字段说明

本文档用于给项目11后续角色说明：当前商品库覆盖了哪些品牌/IP，以及 `products.csv` 的 8 个字段分别代表什么。

## 数据规模

- 最终商品库：`data/products.csv`
- 有效商品数：3939 条
- 原始抓取记录：`data/products_raw.csv`，共 4243 条
- 最终 CSV 固定字段：`id,name,price,image_url,ip,style,description,shop`

## 品牌/IP 覆盖

`ip` 字段是从商品名、店铺名和少量规则中抽取出的推荐标签。它不等同于严格法律意义上的品牌归属，更适合推荐系统做兴趣匹配。

| 品牌/IP | 数量 | 说明 |
|---|---:|---|
| 原创潮玩 | 1682 | 未识别出明确大 IP 的潮玩、动漫周边、小众原创系列 |
| TOP TOY | 743 | TOP TOY 官方/经销商品及相关标题商品 |
| 52TOYS | 332 | 52TOYS、BEASTBOX、NINNIC、Panda Roll 等相关商品 |
| LULU THE PIGGY | 244 | Lulu 猪、罐头猪、Piggy 相关盲盒 |
| POP MART | 148 | 泡泡玛特相关商品；若按标题关键词统计，约 385 条含 POP MART/泡泡玛特 |
| DISNEY | 146 | 迪士尼、史迪奇、疯狂动物城、皮克斯、玩具总动员等 |
| CRAYON SHIN-CHAN | 138 | 蜡笔小新相关商品 |
| SANRIO | 137 | 三丽鸥、Hello Kitty、Kuromi、Cinnamoroll 等 |
| LABUBU / THE MONSTERS | 76 | LABUBU、THE MONSTERS 系列 |
| CRYBABY | 49 | CRYBABY 系列 |
| KIDROBOT | 40 | Kidrobot 盲盒 |
| FINDING UNICORN | 39 | 寻找独角兽、ShinWoo、Farmer Bob 等 |
| HACIPUPU | 36 | HACIPUPU 系列 |
| SKULLPANDA | 31 | SKULLPANDA 系列 |
| MOLLY | 22 | MOLLY 系列 |
| PUCKY | 18 | PUCKY 系列 |
| ROLIFE / NANCI | 16 | Rolife、Nanci、若来相关商品 |
| SONNY ANGEL | 10 | Sonny Angel 系列 |
| SMISKI | 9 | Smiski 系列 |
| DIMOO | 8 | DIMOO 系列 |
| DORAEMON | 8 | 哆啦A梦相关商品 |
| HARRY POTTER | 7 | 哈利波特相关商品 |

## 来源店铺/站点

| 来源 | 数量 | 作用 |
|---|---:|---|
| STC Toys | 2693 | 主要补量来源，包含 POP MART、TOP TOY、52TOYS、Lulu、动漫联名等 |
| AVO Blind Box | 508 | Finding Unicorn、日系潮玩、动漫周边等 |
| TOP TOY | 304 | TOP TOY 官方公开商品列表 |
| 52TOYS Japan | 139 | 52TOYS 日本官方 BLINDBOX 搜索结果 |
| Plastic Empire | 83 | POP MART、Labubu 等潮玩商品 |
| Toy Tokyo | 83 | 海外潮玩/盲盒商品 |
| Kidrobot | 57 | Kidrobot 盲盒商品 |
| ROS Studio | 56 | 台湾 Shopline 潮玩店铺 |
| Kiitos Store | 16 | 台湾 Shopline 盲盒专区 |

## 字段说明

| 字段 | 类型/示例 | 含义 | 用途 |
|---|---|---|---|
| `id` | `64d3f48f22e78691` | 稳定唯一 ID，由来源、店铺、商品名、原始 ID/URL 哈希生成 | MySQL 主键、去重、RAG 返回商品标识 |
| `name` | `BLINDBOX FUWAFUWA...` | 商品名，保留原始标题中的品牌、系列、规格信息 | 前端展示、关键词匹配、向量检索文本 |
| `price` | `71.5` | 统一换算后的人民币价格，单位为 CNY | 预算筛选，例如 `price <= 200` |
| `image_url` | `https://...jpg` | 商品图片 URL，已补全协议/域名 | 前端卡片展示 |
| `ip` | `POP MART`、`52TOYS` | 从商品名/店铺名抽取的品牌或 IP 标签 | 用户画像标签匹配、推荐解释 |
| `style` | `可爱风`、`毛绒挂件` | 从标题和描述关键词抽取出的风格标签 | 推荐过滤、兴趣画像匹配 |
| `description` | `52TOYS Japan official... 来源: https://...` | 清洗后的描述或来源说明，最长约 500 字 | RAG 向量化、推荐解释 |
| `shop` | `STC Toys` | 商品来源店铺/站点 | 展示来源、后续追溯 |

## 关于原始价格和币种

当前 `products.csv` 只有 `price`，这是为了满足角色1约定字段，并且方便角色3按预算直接筛选。这个 `price` 已经换算为人民币，汇率规则在 `crawler/normalize.py` 中：

| 币种 | 换算到 CNY |
|---|---:|
| CNY | 1.00 |
| USD | 7.20 |
| GBP | 9.10 |
| HKD | 0.92 |
| TWD | 0.23 |
| JPY | 0.050 |

原始价格和币种没有丢，保存在 `data/products_raw.csv` 的 `raw_price` 和 `currency` 字段里。当前原始币种分布为：

| 原始币种 | 原始记录数 |
|---|---:|
| USD | 3342 |
| GBP | 509 |
| TWD | 224 |
| JPY | 139 |
| CNY | 29 |

## 最终展示建议

建议前端推荐卡片默认展示人民币价格，例如：

> 约 ¥128.00

原因是用户会用“预算 200 以内”这类条件表达需求，统一人民币价格能让筛选和解释最直接。

不建议在推荐卡片第一层同时展示原始币种，否则界面会变复杂，也容易让用户误解“预算筛选到底按哪个币种算”。但可以在商品详情或小字里展示来源信息，例如：

> 来源：STC Toys，原始价格：USD 17.99，已换算约 ¥129.53

如果后续角色2/6允许扩展数据库字段，推荐新增这些字段：

| 新字段 | 含义 |
|---|---|
| `price_cny` | 人民币换算价格，用于预算筛选 |
| `raw_price` | 来源网站原始价格 |
| `currency` | 原始币种，如 USD、TWD、JPY |
| `source_url` | 商品详情页 URL |

如果必须严格遵守当前 8 列结构，就继续使用 `price` 作为人民币价格，`shop` 和 `description` 用来说明来源。

