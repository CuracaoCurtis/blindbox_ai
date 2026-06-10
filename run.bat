@echo off
chcp 65001 >nul
title 盲盒AI智能导购系统

echo ========================================
echo   盲盒AI智能导购系统
echo ========================================
echo.

cd /d "%~dp0"

:: 检查核心依赖
python -c "import streamlit, pandas, requests" >nul 2>&1
if errorlevel 1 (
    echo [提示] 正在安装依赖...
    pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
    echo.
)

:: 直接启动前端
echo [启动] 正在启动前端界面...
echo [提示] 浏览器将自动打开 http://localhost:8501
echo.
streamlit run main.py

pause
