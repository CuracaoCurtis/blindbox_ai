盲盒 AI 智能导购

这是一个基于 Streamlit 的聊天式盲盒导购。系统会持续记录用户的 IP、风格、预算、用途和排除条件，从商品库中召回真实商品，并在配置云端模型后进行意图理解、候选重排和推荐解释。

功能

- 多轮偏好更新，例如“预算提高到 300”“换成三丽鸥”
- 支持否定条件，例如“不要暗黑风”“不接受隐藏款”
- 硬预算过滤、加权排序和同系列去重
- 比较上一轮推荐，例如“比较第一款和第三款”
- OpenAI-compatible 云端 API；未配置或调用失败时自动使用规则模式
- 推荐结果只允许引用商品库中的候选 ID，避免创造不存在的商品

启动

```powershell
pip install -r requirements.txt
streamlit run main.py
```

Windows 也可以直接运行 `run.bat`。

配置 AI

复制 `.env.example` 为 `.env`，填入你使用的 OpenAI-compatible 服务配置：（现在为空）

```dotenv
LLM_BASE_URL=https://api.example.com/v1
LLM_API_KEY=your-api-key
LLM_MODEL=your-model-name
```

`LLM_BASE_URL` 可以是以 `/v1` 结尾的 API 根路径，也可以直接填写完整的 `/chat/completions` 地址。API Key 不会写入日志或页面。

未创建 `.env` 时，应用仍可启动，并会在页面明确显示“AI 未配置，使用规则模式”。

测试

```powershell
python -m unittest discover -s tests -v
```
