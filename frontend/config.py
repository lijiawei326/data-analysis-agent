# 智能数据分析系统配置文件

# API配置
API_BASE_URL = "http://localhost:8001"

# Streamlit配置
STREAMLIT_CONFIG = {
    "page_title": "智能数据分析系统",
    "page_icon": "📊",
    "layout": "wide",
    "initial_sidebar_state": "expanded"
}

# 超时设置
TIMEOUT_SETTINGS = {
    "chat_timeout": 300,    # 分析API超时时间（秒）- 增加到5分钟以适应复杂分析
    "status_timeout": 10,   # 状态检查超时时间（秒）
    "reset_timeout": 10,    # 重置对话超时时间（秒）
    "server_timeout": 15    # 服务器管理操作超时时间（秒）
}

# 分析类型配置
ANALYSIS_TYPES_CONFIG = {
    "default_type": "auto",
    "available_types": [
        "auto", "correlation", "regression", "clustering", 
        "classification", "time_series", "descriptive", 
        "statistical_test", "custom"
    ]
}

# UI配置
UI_CONFIG = {
    "max_message_length": 10000,      # 最大消息长度
    "max_conversation_history": 50,   # 最大对话历史条数
    "auto_scroll": True,              # 自动滚动到最新消息
    "show_metadata": True,            # 显示分析元数据
    "enable_quick_settings": True     # 启用快速设置
}

# 默认上下文设置
DEFAULT_CONTEXT = {
    "priority": "normal",
    "timeout": 180,
    "max_retries": 3
} 