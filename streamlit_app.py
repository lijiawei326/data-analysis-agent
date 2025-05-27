#!/usr/bin/env python3
"""
相关性分析工具的 Streamlit 前端界面
"""

import streamlit as st
import asyncio
import pandas as pd
import sys
import os
from pathlib import Path
import json
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Optional

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from custom_types.types import ReadDataParam

# 页面配置
st.set_page_config(
    page_title="相关性分析工具",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 标题和描述
st.title("📊 相关性分析工具")
st.markdown("---")
st.markdown("这是一个基于 MCP 的相关性分析工具，支持数据读取、列名映射、分组分析和过滤功能。")

# 侧边栏配置
st.sidebar.header("⚙️ 配置参数")

# 数据源配置
st.sidebar.subheader("📁 数据源")
data_method = st.sidebar.selectbox(
    "数据读取方式",
    ["PANDAS", "SQL"],
    help="选择数据读取方式"
)

if data_method == "PANDAS":
    # 文件上传或路径输入
    upload_option = st.sidebar.radio(
        "数据输入方式",
        ["上传文件", "输入文件路径"]
    )
    
    if upload_option == "上传文件":
        uploaded_file = st.sidebar.file_uploader(
            "选择数据文件",
            type=['csv', 'xlsx', 'xls'],
            help="支持 CSV 和 Excel 文件"
        )
        data_path = None
        if uploaded_file is not None:
            # 保存上传的文件到临时目录
            temp_dir = Path("temp")
            temp_dir.mkdir(exist_ok=True)
            data_path = temp_dir / uploaded_file.name
            with open(data_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.sidebar.success(f"文件已上传: {uploaded_file.name}")
    else:
        data_path = st.sidebar.text_input(
            "数据文件路径",
            value="./data/corr.csv",
            help="输入数据文件的完整路径"
        )
else:
    data_path = st.sidebar.text_area(
        "SQL 查询语句",
        height=100,
        help="输入 SQL 查询语句"
    )

# 分析参数配置
st.sidebar.subheader("🔍 分析参数")

# 相关性变量
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
        "数据读取方式": data_method,
        "数据路径": str(data_path) if data_path else "未设置",
        "相关性变量": correlation_vars,
        "分组变量": group_by if group_by else "无",
        "过滤条件": filters if filters else "无"
    }
    
    config_df = pd.DataFrame(list(config_data.items()), columns=["参数", "值"])
    st.dataframe(config_df, use_container_width=True)

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
                    from server.corr import correlation_analysis
                    
                    read_data_param = ReadDataParam(
                        read_data_method=data_method,
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
                st.session_state.analysis_config = config_data
                
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
        # 创建标签页
        tab1, tab2, tab3, tab4 = st.tabs(["📈 结果概览", "📋 详细数据", "📊 可视化", "📄 Markdown 报告"])
        
        with tab1:
            # 结果概览
            if 'result' in result:
                corr_data = result['result']
                
                # 统计信息
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("分析组数", len(corr_data))
                
                with col2:
                    valid_corrs = [v for v in corr_data.values() if v is not None and v != -100]
                    avg_corr = sum(valid_corrs) / len(valid_corrs) if valid_corrs else 0
                    st.metric("平均相关性", f"{avg_corr:.3f}")
                
                with col3:
                    max_corr = max(valid_corrs) if valid_corrs else 0
                    st.metric("最大相关性", f"{max_corr:.3f}")
                
                with col4:
                    min_corr = min(valid_corrs) if valid_corrs else 0
                    st.metric("最小相关性", f"{min_corr:.3f}")
                
                # 相关性分布
                if valid_corrs:
                    st.subheader("相关性分布")
                    fig = px.histogram(
                        x=valid_corrs,
                        nbins=20,
                        title="相关性系数分布",
                        labels={'x': '相关性系数', 'y': '频数'}
                    )
                    st.plotly_chart(fig, use_container_width=True)
        
        with tab2:
            # 详细数据表格
            if 'result' in result:
                corr_data = result['result']
                
                # 转换为 DataFrame
                df_result = pd.DataFrame([
                    {
                        '分组/变量': key,
                        '相关性系数': value if value not in [None, -100] else "数据不足",
                        '状态': "正常" if value not in [None, -100] else "数据不足"
                    }
                    for key, value in corr_data.items()
                ])
                
                st.dataframe(df_result, use_container_width=True)
                
                # 下载按钮
                csv = df_result.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label="📥 下载结果 (CSV)",
                    data=csv,
                    file_name="correlation_analysis_result.csv",
                    mime="text/csv"
                )
        
        with tab3:
            # 可视化
            if 'result' in result:
                corr_data = result['result']
                valid_data = {k: v for k, v in corr_data.items() if v is not None and v != -100}
                
                if valid_data:
                    # 相关性条形图
                    st.subheader("相关性系数条形图")
                    
                    df_viz = pd.DataFrame([
                        {'组别': k, '相关性': v}
                        for k, v in valid_data.items()
                    ])
                    
                    # 根据数据量选择图表类型
                    if len(df_viz) <= 20:
                        fig = px.bar(
                            df_viz,
                            x='组别',
                            y='相关性',
                            title=f"{correlation_vars[0]} vs {correlation_vars[1]} 相关性分析",
                            color='相关性',
                            color_continuous_scale='RdBu_r'
                        )
                        fig.update_xaxis(tickangle=45)
                    else:
                        fig = px.scatter(
                            df_viz,
                            x=range(len(df_viz)),
                            y='相关性',
                            hover_data=['组别'],
                            title=f"{correlation_vars[0]} vs {correlation_vars[1]} 相关性分析",
                            color='相关性',
                            color_continuous_scale='RdBu_r'
                        )
                        fig.update_xaxis(title="数据点索引")
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # 相关性强度分类
                    st.subheader("相关性强度分类")
                    
                    def classify_correlation(corr):
                        abs_corr = abs(corr)
                        if abs_corr >= 0.7:
                            return "强相关"
                        elif abs_corr >= 0.3:
                            return "中等相关"
                        elif abs_corr >= 0.1:
                            return "弱相关"
                        else:
                            return "几乎无关"
                    
                    classification = {}
                    for k, v in valid_data.items():
                        category = classify_correlation(v)
                        if category not in classification:
                            classification[category] = 0
                        classification[category] += 1
                    
                    fig_pie = px.pie(
                        values=list(classification.values()),
                        names=list(classification.keys()),
                        title="相关性强度分布"
                    )
                    st.plotly_chart(fig_pie, use_container_width=True)
                else:
                    st.warning("⚠️ 没有有效的相关性数据可供可视化")
        
        with tab4:
            # Markdown 报告
            if 'markdown' in result:
                st.subheader("📄 分析报告")
                st.markdown(result['markdown'])
                
                # 下载 Markdown 报告
                st.download_button(
                    label="📥 下载报告 (Markdown)",
                    data=result['markdown'],
                    file_name="correlation_analysis_report.md",
                    mime="text/markdown"
                )

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