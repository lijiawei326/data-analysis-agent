#!/usr/bin/env python3
"""
测试相关性分析工具的修复
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from custom_types.types import ReadDataParam

async def test_correlation_analysis():
    """测试相关性分析功能"""
    
    # 导入相关性分析工具
    from server.corr import correlation_analysis
    
    # 创建测试数据参数
    read_data_param = ReadDataParam(
        read_data_method="PANDAS",
        read_data_query="./data/corr.csv"  # 使用现有的测试文件
    )
    
    # 测试参数 - 使用更简单的测试参数
    filters = None  # 先不使用过滤条件
    group_by = None  # 先不使用分组
    correlation_vars = ["气温(℃)", "风速(m/s)"]  # 使用实际存在的列名
    
    try:
        print("开始测试相关性分析...")
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
    asyncio.run(test_correlation_analysis()) 