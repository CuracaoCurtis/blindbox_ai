项目11：盲盒AI推荐员：聊天式兴趣画像与个性化盲盒推荐系统

&#x20;   这是一个面向盲盒消费场景的 AI 智能导购系统。用户不需要自己浏览大量商品，只需要像聊天一样表达自己的偏好，例如喜欢的 IP、预算、风格、颜色、收藏目的、是否接受隐藏款溢价等，系统就能自动建立用户兴趣画像，并从盲盒商品库中推荐合适款式。

技术实现要点：

聊天式偏好采集：通过多轮对话询问预算、IP、风格、用途

用户兴趣画像：将用户偏好结构化为标签，如“可爱风”“治愈系”

商品知识库构建：爬取或整理盲盒商品信息

向量语义检索：将商品描述和用户需求向量化，检索最匹配的盲盒

个性化推荐解释：不只给结果，还解释为什么推荐这个款式，对比推荐		





角色1：爬虫与数据采集（1人）

目标：拿到至少100条盲盒商品数据，存成CSV

data/products.csv 包含字段：

id, name, price, image\_url, ip, style, description, shop

完成标准：至少100条有效数据，CSV文件能被pandas正常读取。



角色1（爬虫）学：

HTTP 请求：浏览器访问网页，其实是发了一个 GET 请求。爬虫就是模拟这个请求拿回 HTML 代码。

HTML 和 CSS 选择器：网页的结构像一棵树，你需要找到商品名字在哪个标签里（比如 <div class="product-name">）。

BeautifulSoup：一个库，帮你从 HTML 中提取数据。

Selenium：有些网页是 JavaScript 动态渲染的，需要用这个库模拟浏览器操作。

学到什么程度：能写一个脚本，输入一个网址，把网页上所有商品名字和价格打印出来。







角色2：数据清洗与预处理（1人）

目标：把爬虫拿到的脏数据变成干净的商品库，存入MySQL。

MySQL中 products 表有100+条记录

提供 db\_config.py 包含数据库连接参数

一个 load\_data.py 脚本，运行即加载CSV到MySQL（方便重复运行）

完成标准：其他成员能通过 mysql.connector 查询到商品。



角色2（数据清洗）学：

pandas：处理表格数据的库，类似 Excel 但用代码操作。

读取 CSV：pd.read\_csv()

查看前5行：df.head()

删除空行：df.dropna()

修改列：df\['price'] = df\['price'].str.replace('¥','')

SQL 基础：数据库查询语言。

建表：CREATE TABLE ...

插入数据：INSERT INTO ...

查询：SELECT \* FROM products WHERE price < 200

学到什么程度：能读取一个 CSV 文件，去掉价格为空的行，把结果存到 MySQL 里。







角色3：RAG检索模块（1人）

目标：输入用户偏好（如风格=可爱，预算<200），返回匹配度最高的前5个商品。

rag/build\_index.py（运行一次建立向量库）

rag/searcher.py 提供 search\_by\_tags(profile) 函数

单元测试：给定一个假profile，能返回商品列表

完成标准：调用函数能在0.5秒内返回推荐商品（不需要大模型参与）。



角色3（RAG 检索）学：

向量和向量检索：把文字变成一堆数字（向量），然后计算哪两个向量最像（距离最近）。比如“可爱”和“萌”的向量会很接近。

Sentence Transformers：一个现成的模型，输入文字，输出向量。

FAISS：一个库，可以快速在一大堆向量里找最相似的几个。

学到什么程度：能写脚本，给 10 句商品描述，再给一句用户需求，找出最相似的商品。







角色4：用户画像模块（1人）

目标：解析用户说的自然语言，更新偏好标签字典。

user\_profile/parser.py 提供 update\_profile(user\_input, current\_profile)

返回 (updated\_profile, ask\_question) 其中ask\_question为None或追问语句

完成标准：给定10句不同用户输入，能正确填充至少5个标签字段。



角色4（用户画像）学：

字符串处理：用户说“我喜欢可爱的”，你需要提取“可爱”这个词。

关键词匹配：if "可爱" in user\_input: style = "可爱"

正则表达式（简单版）：import re; re.findall(r'(\\d+)元', user\_input) 找出“200元”中的200。

字典操作：存储用户的偏好，比如 profile = {"style": None, "budget": 200}。

学到什么程度：能写一个函数，输入一句话，输出一个字典，包含风格、预算、IP。







角色5：大模型集成（1人）

目标：调用本地Ollama，生成推荐解释和友好对话。

llm/ollama\_client.py 包含 generate\_response(prompt) 和 generate\_explanation(...)

确保调用一次耗时不超过5秒（如果太慢，换小模型或减少token）

完成标准：独立运行 generate\_explanation 能返回一句通顺的中文。



角色5（大模型集成）学：

API 调用：大模型像一个在线服务，你发一段文字（prompt），它返回一段文字。

Ollama：一个可以本地运行大模型的工具，不需要联网，免费。

安装后，命令行输入 ollama run qwen 就可以对话。

Python 中用 requests 库调用它的 API。

写 Prompt：给大模型的指令要清晰，例如“请用一句话推荐盲盒，风格要可爱”。

学到什么程度：能用 Python 发请求给 Ollama，并打印出回复。







角色6：前端与整合（1人）

目标：用Streamlit（可选）做出聊天界面，把其他所有人的模块串起来。

main.py 完整代码

能演示至少3轮对话，推荐结果合理

完成标准：启动后，用户输入“我喜欢可爱的，预算200以内”，系统能推荐商品并解释。



角色6（前端+整合）学：

Streamlit：把 Python 代码变成网页界面，不需要写 HTML。

基本控件：st.title() 标题，st.chat\_input() 聊天输入框，st.chat\_message() 显示气泡。

状态管理：st.session\_state 用来记住对话历史和用户画像。

调用其他人的函数：你会写 from user\_profile.parser import update\_profile 然后直接使用。

学到什么程度：能照着官方聊天示例改出一个简单的对话界面。







然后学长建议可以借机学一下git版本管理和合作开发





