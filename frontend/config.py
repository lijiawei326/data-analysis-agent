# 配置文件

# API配置
API_BASE_URL = "http://localhost:8001"

# Streamlit配置
STREAMLIT_CONFIG = {
    "page_title": "智能分析对话系统",
    "page_icon": "🤖",
    "layout": "wide",
    "initial_sidebar_state": "collapsed"
}

# 超时设置
TIMEOUT_SETTINGS = {
    "chat_timeout": 180,  # 聊天API超时时间（秒）
    "status_timeout": 5,  # 状态检查超时时间（秒）
    "reset_timeout": 10   # 重置对话超时时间（秒）
} 