#!/bin/bash

echo "========================================"
echo "  盲盒AI智能导购系统"
echo "========================================"
echo ""

# 切换到脚本所在目录
cd "$(dirname "$0")"

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未找到Python，请先安装Python 3.8+"
    exit 1
fi

# 检查核心依赖
if ! python3 -c "import streamlit, pandas, requests" &> /dev/null; then
    echo "[提示] 正在安装依赖..."
    pip3 install -r requirements.txt
    echo ""
fi

# 直接启动前端
echo "[启动] 正在启动前端界面..."
echo "[提示] 浏览器将自动打开 http://localhost:8501"
echo ""
streamlit run main.py
