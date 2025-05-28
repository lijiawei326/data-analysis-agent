#!/usr/bin/env python3
"""
简化的多轮对话功能测试
"""

import asyncio
import json
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# 添加项目路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))
sys.path.append(str(PROJECT_ROOT / 'frontend'))

from custom_types.types import ReadDataParam

async def test_multi_turn():
    """测试多轮对话功能"""
    print("🚀 测试多轮对话功能")
    print("=" * 40)
    
    # 创建测试数据
    test_dir = Path("./test_simple")
    test_dir.mkdir(exist_ok=True)
    
    # 生成简单的相关数据
    np.random.seed(42)
    data = pd.DataFrame({
        'x': np.random.normal(0, 1, 50),
        'y': np.random.normal(0, 1, 50),
        'z': np.random.normal(0, 1, 50)
    })
    # 让y和x有一定相关性
    data['y'] = data['x'] * 0.5 + data['y'] * 0.5
    
    data_file = test_dir / "test_data.csv"
    data.to_csv(data_file, index=False)
    print(f"📁 测试数据已创建: {data_file}")
    
    try:
        # 导入测试函数
        from interactive_visualization_server import (
            start_visualization_session,
            start_correlation_analysis_only,
            get_correlation_table_from_session,
            visualize_existing_correlation,
            delete_session
        )
        
        print("\n🔄 场景1：先图后表")
        print("-" * 20)
        
        # 第一轮：生成图表
        result1 = await start_visualization_session(
            user_request="请生成x、y、z的相关性热力图",
            read_data_param=ReadDataParam(read_data_query=str(data_file)),
            correlation_vars=["x", "y", "z"],
            include_correlation_table=False
        )
        
        result1_data = json.loads(result1)
        session_id1 = result1_data["session_id"]
        print(f"✅ 图表生成成功: {session_id1}")
        print(f"📊 图表路径: {result1_data['chart_path']}")
        
        # 第二轮：获取表格
        table_result = await get_correlation_table_from_session(session_id1)
        if "失败" not in table_result and "不存在" not in table_result:
            print("✅ 成功获取相关性表格")
            print(f"📋 表格长度: {len(table_result)} 字符")
        else:
            print(f"❌ 获取表格失败: {table_result}")
        
        print("\n🔄 场景2：先表后图")
        print("-" * 20)
        
        # 第一轮：只生成表格
        result2 = await start_correlation_analysis_only(
            read_data_param=ReadDataParam(read_data_query=str(data_file)),
            correlation_vars=["x", "y", "z"],
            correlation_method="pearson"
        )
        
        result2_data = json.loads(result2)
        session_id2 = result2_data["session_id"]
        print(f"✅ 相关性分析完成: {session_id2}")
        print(f"📋 会话类型: {result2_data['session_type']}")
        
        # 第二轮：基于表格生成图表
        viz_result = await visualize_existing_correlation(
            session_id=session_id2,
            visualization_request="请生成热力图"
        )
        
        if viz_result.startswith("{"):
            viz_data = json.loads(viz_result)
            print(f"✅ 图表生成成功: {viz_data['chart_path']}")
        else:
            print(f"❌ 图表生成失败: {viz_result}")
        
        # 清理
        await delete_session(session_id1)
        await delete_session(session_id2)
        print("\n✅ 测试完成，会话已清理")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_multi_turn())
    if success:
        print("\n🎉 多轮对话功能测试通过！")
    else:
        print("\n💥 多轮对话功能测试失败！") 