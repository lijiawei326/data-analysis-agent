#!/usr/bin/env python3
"""
测试相关性分析工具的高级功能（分组和过滤）
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from custom_types.types import ReadDataParam

async def test_advanced_correlation_analysis():
    """测试包含分组和过滤的相关性分析功能"""
    
    # 导入相关性分析工具
    from server.corr import correlation_analysis
    
    # 创建测试数据参数
    read_data_param = ReadDataParam(
        read_data_method="PANDAS",
        read_data_query="./data/corr.csv"
    )
    
    # 测试参数 - 包含分组
    filters = None
    group_by = ["站点名称"]  # 按站点分组
    correlation_vars = ["气温", "PM2.5"]  # 使用简化的列名，测试列名映射
    
    try:
        print("开始测试高级相关性分析（分组）...")
        result = await correlation_analysis(
            read_data_param=read_data_param,
            filters=filters,
            group_by=group_by,
            correlation_vars=correlation_vars
        )
        
        print("测试成功！")
        print(f"结果类型: {type(result)}")
        if 'result' in result:
            print(f"相关性结果数量: {len(result['result'])}")
            # 显示前几个结果
            for i, (key, value) in enumerate(list(result['result'].items())[:3]):
                print(f"  {key}: {value}")
        
        if 'markdown' in result:
            print("\nMarkdown 表格:")
            print(result['markdown'][:500] + "..." if len(result['markdown']) > 500 else result['markdown'])
        
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()

async def test_filtered_correlation_analysis():
    """测试包含过滤条件的相关性分析功能"""
    
    # 导入相关性分析工具
    from server.corr import correlation_analysis
    
    # 创建测试数据参数
    read_data_param = ReadDataParam(
        read_data_method="PANDAS",
        read_data_query="./data/corr.csv"
    )
    
    # 测试参数 - 包含过滤条件
    filters = {"站点名称": "高新科技工业园"}  # 只分析特定站点
    group_by = None
    correlation_vars = ["气温", "风速"]  # 使用简化的列名
    
    try:
        print("\n开始测试过滤条件相关性分析...")
        result = await correlation_analysis(
            read_data_param=read_data_param,
            filters=filters,
            group_by=group_by,
            correlation_vars=correlation_vars
        )
        
        print("测试成功！")
        print(f"结果: {result}")
        
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_advanced_correlation_analysis())
    asyncio.run(test_filtered_correlation_analysis()) 