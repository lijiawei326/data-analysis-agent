#!/usr/bin/env python3
"""
相关性分析工具的简化 Streamlit 前端界面
"""

import streamlit as st
import asyncio
import sys
import os
from pathlib import Path

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 页面配置
st.set_page_config(
    page_title="相关性分析工具",
    page_icon="📊",
    layout="wide"
)

# 标题
st.title("📊 相关性分析工具")
st.markdown("---")
st.markdown("这是一个基于 MCP 的相关性分析工具，支持数据读取、列名映射、分组分析和过滤功能。")

# 侧边栏
st.sidebar.header("⚙️ 配置参数")

# 数据源
st.sidebar.subheader("📁 数据源")
data_path = st.sidebar.text_input(
    "数据文件路径",
    value="./data/corr.csv",
    help="输入数据文件的完整路径"
)

# 分析参数
st.sidebar.subheader("🔍 分析参数")
correlation_vars_input = st.sidebar.text_input(
    "相关性变量 (用逗号分隔)",
    value="气温,风速",
    help="输入要计算相关性的两个变量名，用逗号分隔"
)

correlation_vars = [var.strip() for var in correlation_vars_input.split(",") if var.strip()] if correlation_vars_input else []

# 分组变量
group_by_input = st.sidebar.text_input(
    "分组变量 (可选，用逗号分隔)",
    help="按指定变量分组计算相关性"
)
group_by = [var.strip() for var in group_by_input.split(",") if var.strip()] if group_by_input else None

# 过滤条件
st.sidebar.subheader("🔽 过滤条件")
filter_enabled = st.sidebar.checkbox("启用过滤条件")
filters = None

if filter_enabled:
    filter_var = st.sidebar.text_input("过滤变量名")
    filter_value = st.sidebar.text_input("过滤值")
    if filter_var and filter_value:
        filters = {filter_var: filter_value}

# 主界面
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📋 分析配置")
    
    # 显示当前配置
    config_data = {
        "数据路径": str(data_path) if data_path else "未设置",
        "相关性变量": correlation_vars,
        "分组变量": group_by if group_by else "无",
        "过滤条件": filters if filters else "无"
    }
    
    for key, value in config_data.items():
        st.write(f"**{key}**: {value}")

with col2:
    st.subheader("🚀 执行分析")
    
    # 验证配置
    can_run = (
        data_path is not None and 
        len(correlation_vars) == 2
    )
    
    if not can_run:
        if not data_path:
            st.error("❌ 请设置数据源")
        if len(correlation_vars) != 2:
            st.error("❌ 请输入恰好两个相关性变量")
    
    # 运行分析按钮
    if st.button("🔍 开始分析", disabled=not can_run, use_container_width=True):
        with st.spinner("正在进行相关性分析..."):
            try:
                # 异步调用相关性分析工具
                async def run_analysis():
                    from custom_types.types import ReadDataParam
                    from server.corr import correlation_analysis
                    
                    read_data_param = ReadDataParam(
                        read_data_method="PANDAS",
                        read_data_query=str(data_path)
                    )
                    
                    result = await correlation_analysis(
                        read_data_param=read_data_param,
                        filters=filters,
                        group_by=group_by,
                        correlation_vars=correlation_vars
                    )
                    
                    return result
                
                # 运行异步函数
                result = asyncio.run(run_analysis())
                
                # 存储结果到 session state
                st.session_state.analysis_result = result
                
                st.success("✅ 分析完成！")
                
            except Exception as e:
                st.error(f"❌ 分析失败: {str(e)}")
                st.exception(e)

# 显示分析结果
if hasattr(st.session_state, 'analysis_result') and st.session_state.analysis_result:
    st.markdown("---")
    st.subheader("📊 分析结果")
    
    result = st.session_state.analysis_result
    
    # 检查是否有错误
    if 'error' in result:
        st.error(f"❌ 分析错误: {result['error']}")
    else:
        # 显示结果
        if 'result' in result:
            st.subheader("📈 相关性结果")
            corr_data = result['result']
            
            # 显示统计信息
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("分析组数", len(corr_data))
            
            with col2:
                valid_corrs = [v for v in corr_data.values() if v is not None and v != -100]
                avg_corr = sum(valid_corrs) / len(valid_corrs) if valid_corrs else 0
                st.metric("平均相关性", f"{avg_corr:.3f}")
            
            with col3:
                max_corr = max(valid_corrs) if valid_corrs else 0
                st.metric("最大相关性", f"{max_corr:.3f}")
            
            # 显示详细结果
            st.subheader("📋 详细结果")
            for key, value in corr_data.items():
                if value is None or value == -100:
                    st.write(f"**{key}**: 数据不足")
                else:
                    st.write(f"**{key}**: {value}")
        
        # 显示 Markdown 报告
        if 'markdown' in result:
            st.subheader("📄 分析报告")
            st.markdown(result['markdown'])

# 页脚
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666;'>
        <p>相关性分析工具 | 基于 MCP 架构 | Powered by Streamlit</p>
    </div>
    """,
    unsafe_allow_html=True
) 