import streamlit as st
import requests
import json
from typing import List, Dict
from config import API_BASE_URL, STREAMLIT_CONFIG, TIMEOUT_SETTINGS

# 页面配置
st.set_page_config(**STREAMLIT_CONFIG)

def call_chat_api(message: str, conversation_history: List[Dict] = None) -> Dict:
    """调用聊天API"""
    if conversation_history is None:
        conversation_history = []
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/chat",
            json={
                "message": message,
                "conversation_history": conversation_history
            },
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

def main():
    # 标题
    st.title("🤖 智能分析对话系统")
    st.markdown("---")
    
    # 初始化会话状态
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "conversation_history" not in st.session_state:
        st.session_state.conversation_history = []
    
    # 侧边栏控制
    with st.sidebar:
        st.header("控制面板")
        
        # 重置对话按钮
        if st.button("🔄 重置对话", use_container_width=True):
            if reset_conversation():
                st.session_state.messages = []
                st.session_state.conversation_history = []
                st.success("对话已重置")
                st.rerun()
        
        st.markdown("---")
        
        # API状态检查
        st.subheader("API状态")
        try:
            response = requests.get(f"{API_BASE_URL}/", timeout=TIMEOUT_SETTINGS["status_timeout"])
            if response.status_code == 200:
                st.success("✅ API连接正常")
            else:
                st.error("❌ API连接异常")
        except:
            st.error("❌ 无法连接到API")
        
        st.markdown("---")
        st.markdown("### 使用说明")
        st.markdown("""
        1. 在下方输入框中输入您的问题
        2. 点击发送或按Enter键提交
        3. 系统将进行智能分析并返回结果
        4. 可以随时点击"重置对话"清空历史
        """)
    
    # 主聊天区域
    chat_container = st.container()
    
    with chat_container:
        # 显示对话历史
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # 用户输入
        if prompt := st.chat_input("请输入您的问题..."):
            # 添加用户消息到历史
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            # 显示用户消息
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # 显示加载状态
            with st.chat_message("assistant"):
                with st.spinner("正在分析中，请稍候..."):
                    # 调用API
                    response = call_chat_api(prompt, st.session_state.conversation_history)
                
                if response:
                    result = response.get("result", "抱歉，没有收到有效回复")
                    
                    # 显示助手回复
                    st.markdown(result)
                    
                    # 添加助手消息到历史
                    st.session_state.messages.append({"role": "assistant", "content": result})
                    
                    # 更新对话历史
                    if "conversation_history" in response:
                        st.session_state.conversation_history = response["conversation_history"]
                else:
                    error_msg = "抱歉，处理您的请求时出现了错误，请稍后重试。"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})

if __name__ == "__main__":
    main() 