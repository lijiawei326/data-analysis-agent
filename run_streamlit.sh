#!/bin/bash

# 相关性分析工具 Streamlit 应用启动脚本

echo "🚀 启动相关性分析工具 Streamlit 应用..."

# 检查是否在虚拟环境中
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "✅ 检测到虚拟环境: $VIRTUAL_ENV"
else
    echo "⚠️  未检测到虚拟环境，尝试使用 uv..."
fi

# 安装依赖
echo "📦 安装 Streamlit 依赖..."
if command -v uv &> /dev/null; then
    uv pip install streamlit plotly
else
    pip install -r requirements_streamlit.txt
fi

# 创建临时目录
mkdir -p temp

# 启动 Streamlit 应用
echo "🌐 启动 Streamlit 应用..."
echo "📍 应用将在 http://localhost:8501 启动"
echo "🔗 MCP 服务器应在 http://localhost:8000 运行"

if command -v uv &> /dev/null; then
    uv run streamlit run streamlit_app.py --server.port 8501 --server.address 0.0.0.0
else
    streamlit run streamlit_app.py --server.port 8501 --server.address 0.0.0.0
fi 