import streamlit as st
import requests
import json
from typing import List, Dict, Optional
from config import API_BASE_URL, STREAMLIT_CONFIG, TIMEOUT_SETTINGS
import time

# 页面配置
st.set_page_config(
    page_title="智能数据分析系统",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 分析类型映射
ANALYSIS_TYPES = {
    "auto": "自动选择",
    "correlation": "相关性分析",
    "regression": "回归分析",
    "clustering": "聚类分析", 
    "classification": "分类分析",
    "time_series": "时间序列分析",
    "descriptive": "描述性统计",
    "statistical_test": "统计检验",
    "custom": "自定义分析"
}

def get_system_status() -> Dict:
    """获取系统状态"""
    try:
        response = requests.get(f"{API_BASE_URL}/status", timeout=TIMEOUT_SETTINGS["status_timeout"])
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"获取系统状态失败: {str(e)}")
        return None

def get_all_servers() -> Dict:
    """获取所有服务器列表（包括禁用的）"""
    try:
        response = requests.get(f"{API_BASE_URL}/servers", timeout=TIMEOUT_SETTINGS["status_timeout"])
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        # 如果没有这个API端点，返回None
        return None

def get_supported_analysis_types() -> Dict:
    """获取支持的分析类型"""
    try:
        response = requests.get(f"{API_BASE_URL}/analysis-types", timeout=TIMEOUT_SETTINGS["status_timeout"])
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"获取分析类型失败: {str(e)}")
        return None

def call_analyze_api(
    message: str, 
    conversation_history: List[Dict] = None,
    analysis_type: Optional[str] = None,
    context: Optional[Dict] = None
) -> Dict:
    """调用分析API"""
    if conversation_history is None:
        conversation_history = []
    
    payload = {
        "message": message,
        "conversation_history": conversation_history
    }
    
    if analysis_type and analysis_type != "auto":
        payload["analysis_type"] = analysis_type
    
    if context:
        payload["context"] = context
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/analyze",
            json=payload,
            timeout=TIMEOUT_SETTINGS["chat_timeout"]
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API调用失败: {str(e)}")
        return None

def reset_conversation() -> bool:
    """重置对话"""
    try:
        response = requests.post(f"{API_BASE_URL}/reset", timeout=TIMEOUT_SETTINGS["reset_timeout"])
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        st.error(f"重置对话失败: {str(e)}")
        return False

def enable_server(server_name: str) -> bool:
    """启用服务器"""
    try:
        response = requests.post(f"{API_BASE_URL}/servers/{server_name}/enable", timeout=10)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        st.error(f"启用服务器失败: {str(e)}")
        return False

def disable_server(server_name: str) -> bool:
    """禁用服务器"""
    try:
        response = requests.post(f"{API_BASE_URL}/servers/{server_name}/disable", timeout=10)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        st.error(f"禁用服务器失败: {str(e)}")
        return False

def main():
    # 主标题
    st.title("📊 智能数据分析系统")
    st.markdown("**通用数据分析平台 - 支持相关性分析、回归分析、聚类分析等多种分析功能**")
    st.markdown("---")
    
    # 初始化会话状态
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "conversation_history" not in st.session_state:
        st.session_state.conversation_history = []
    
    # 固定布局：侧边栏始终显示在右边
    col1, col2 = st.columns([4, 1])
    
    # 主聊天区域
    with col1:
        st.header("💬 智能分析对话")
        
        # 显示对话历史
        chat_container = st.container()
        with chat_container:
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
                    
                    # 显示元数据（如果是助手消息且有元数据）
                    if message["role"] == "assistant" and "metadata" in message:
                        metadata = message["metadata"]
                        with st.expander("📊 分析详情"):
                            col_meta1, col_meta2 = st.columns(2)
                            with col_meta1:
                                st.metric("处理时间", metadata.get("processing_time", "N/A"))
                                st.metric("分析模式", metadata.get("analysis_mode", "N/A"))
                            with col_meta2:
                                st.metric("活跃服务器", metadata.get("active_servers", "N/A"))
                                st.metric("时间戳", metadata.get("timestamp", "N/A"))
        
        # 用户输入区域
        st.markdown("---")
        
        # 用户输入
        if prompt := st.chat_input("请输入您的分析需求..."):
            # 添加用户消息到历史
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            # 显示用户消息
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # 显示加载状态
            with st.chat_message("assistant"):
                with st.spinner("🔍 正在进行智能分析，请稍候..."):
                    # 调用API
                    response = call_analyze_api(
                        prompt, 
                        st.session_state.conversation_history,
                        "auto",  # 固定使用自动分析类型
                        {}  # 空的上下文
                    )
                
                if response:
                    result = response.get("result", "抱歉，没有收到有效回复")
                    metadata = response.get("metadata", {})
                    
                    # 显示助手回复
                    st.markdown(result)
                    
                    # 添加助手消息到历史（包含元数据）
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": result,
                        "metadata": metadata
                    })
                    
                    # 更新对话历史
                    if "conversation_history" in response:
                        st.session_state.conversation_history = response["conversation_history"]
                    
                    # 显示成功提示
                    analysis_mode = metadata.get("analysis_mode", "auto")
                    processing_time = metadata.get("processing_time", "N/A")
                    st.success(f"✅ 分析完成 | 模式: {ANALYSIS_TYPES.get(analysis_mode, analysis_mode)} | 耗时: {processing_time}")
                else:
                    error_msg = "❌ 抱歉，处理您的请求时出现了错误，请稍后重试。"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
    
    # 侧边栏控制面板（固定显示在右边）
    with col2:
        # 添加简约的样式
        st.markdown("""
        <style>
        .sidebar-container {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 15px;
            padding: 20px;
            margin: 10px 0;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        }
        .sidebar-title {
            color: white;
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 15px;
            text-align: center;
        }
        .sidebar-button {
            background: rgba(255,255,255,0.2);
            border: 1px solid rgba(255,255,255,0.3);
            border-radius: 10px;
            color: white;
            padding: 8px 16px;
            margin: 5px 0;
            width: 100%;
            transition: all 0.3s ease;
        }
        .sidebar-button:hover {
            background: rgba(255,255,255,0.3);
            transform: translateY(-2px);
        }
        </style>
        """, unsafe_allow_html=True)
        
        # 侧边栏标题
        # st.markdown("**🎛️ 控制面板**")
        st.markdown("""
<div style="font-size: 32px; font-weight: bold; text-align: left;">
    🎛️ 控制面板
</div>
""", unsafe_allow_html=True)
        st.markdown("---")
        
        # 重置对话按钮 - 简约样式
        st.markdown("""
        <style>
        .reset-btn button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
            border: 2px solid rgba(255,255,255,0.3) !important;
            border-radius: 12px !important;
            color: white !important;
            font-weight: 600 !important;
            padding: 12px 20px !important;
            transition: all 0.3s ease !important;
            width: 100% !important;
        }
        .reset-btn button:hover {
            background: linear-gradient(135deg, #764ba2 0%, #667eea 100%) !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4) !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        if st.button("🔄 重置对话", key="reset_conversation"):
            if reset_conversation():
                st.session_state.messages = []
                st.session_state.conversation_history = []
                st.success("对话已重置")
                st.rerun()
        
        st.markdown("---")
        
        # 服务器管理
        st.markdown("**🖥️ 服务器管理**")
        
        # 初始化服务器列表会话状态
        if "known_servers" not in st.session_state:
            st.session_state.known_servers = set()
        
        status_data = get_system_status()
        all_servers_data = get_all_servers()
        
        if status_data:
            # 简化的服务器状态显示
            total_servers = status_data.get("total_servers", 0)
            enabled_servers = status_data.get("enabled_servers", 0)
            overall_status = status_data.get("status", "unknown")
            
            # 状态指示器
            if overall_status == "healthy":
                st.success(f"✅ 系统正常 ({enabled_servers}/{total_servers})")
            else:
                st.warning(f"⚠️ 系统异常 ({enabled_servers}/{total_servers})")
            
            # 获取服务器列表
            servers_to_display = []
            
            # 优先使用all_servers API的结果
            if all_servers_data and "servers" in all_servers_data:
                servers_to_display = all_servers_data["servers"]
            else:
                # 如果没有all_servers API，使用active_servers并结合已知服务器
                active_servers = status_data.get("active_servers", [])
                servers_to_display = active_servers.copy()
                
                # 将当前活跃服务器添加到已知服务器集合
                for server in active_servers:
                    server_name = server.get("server_name", "unknown")
                    st.session_state.known_servers.add(server_name)
                
                # 为已知但不在活跃列表中的服务器创建条目（假设它们被禁用了）
                active_server_names = {s.get("server_name") for s in active_servers}
                for known_server in st.session_state.known_servers:
                    if known_server not in active_server_names:
                        servers_to_display.append({
                            "server_name": known_server,
                            "status": "disabled",
                            "analysis_types": ["unknown"]
                        })
            
            if servers_to_display:
                st.markdown("**服务器列表:**")
                for i, server in enumerate(servers_to_display):
                    server_name = server.get("server_name", "unknown")
                    server_status = server.get("status", "unknown")
                    analysis_types = server.get("analysis_types", [])
                    
                    # 将服务器添加到已知服务器集合
                    st.session_state.known_servers.add(server_name)
                    
                    # 服务器信息显示
                    if server_status == "healthy":
                        status_icon = "✅"
                        status_text = "运行中"
                    elif server_status == "disabled":
                        status_icon = "⏸️"
                        status_text = "已禁用"
                    else:
                        status_icon = "❌"
                        status_text = "离线"
                    
                    st.markdown(f"**{server_name}** {status_icon}")
                    if analysis_types and analysis_types != ["unknown"]:
                        st.caption(f"状态: {status_text} | 类型: {', '.join(analysis_types)}")
                    else:
                        st.caption(f"状态: {status_text}")
                    
                    # 启用和禁用按钮
                    col_enable, col_disable = st.columns(2)
                    with col_enable:
                        # 只有在服务器不是healthy状态时才能启用
                        enable_disabled = (server_status == "healthy")
                        if st.button("🟢 启用", 
                                    key=f"enable_{server_name}_{i}",
                                    help=f"启用 {server_name}",
                                    disabled=enable_disabled,
                                    use_container_width=True):
                            if enable_server(server_name):
                                st.success(f"已启用 {server_name}")
                                st.rerun()
                    
                    with col_disable:
                        # 只有在服务器是healthy状态时才能禁用
                        disable_disabled = (server_status != "healthy")
                        if st.button("🔴 禁用", 
                                    key=f"disable_{server_name}_{i}",
                                    help=f"禁用 {server_name}",
                                    disabled=disable_disabled,
                                    use_container_width=True):
                            if disable_server(server_name):
                                st.success(f"已禁用 {server_name}")
                                st.rerun()
                    
                    # 添加分隔线（除了最后一个）
                    if i < len(servers_to_display) - 1:
                        st.markdown("---")
            else:
                st.info("暂无服务器")
        else:
            st.error("❌ 无法获取服务器状态")

if __name__ == "__main__":
    main() 