"""
交互式可视化系统使用示例
演示如何使用MCP服务器进行数据可视化
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

async def example_correlation_analysis():
    """示例：相关性分析热力图"""
    print("🔥 示例：相关性分析热力图")
    print("-" * 40)
    
    # 需要导入MCP工具函数
    from interactive_visualization_server import (
        start_visualization_session, 
        refine_visualization,
        get_session_info,
        delete_session
    )
    
    # 创建示例数据
    data_dir = Path("./example_data")
    data_dir.mkdir(exist_ok=True)
    
    # 生成相关的变量数据
    np.random.seed(42)
    n = 100
    
    temperature = np.random.normal(25, 5, n)
    humidity = 0.7 * temperature + np.random.normal(40, 8, n)
    pressure = -0.4 * temperature + np.random.normal(1010, 15, n)
    wind_speed = np.random.exponential(8, n)
    
    weather_df = pd.DataFrame({
        'temperature': temperature,
        'humidity': humidity, 
        'pressure': pressure,
        'wind_speed': wind_speed
    })
    
    data_file = data_dir / "weather_example.csv"
    weather_df.to_csv(data_file, index=False)
    print(f"📁 示例数据已创建: {data_file}")
    
    try:
        # 1. 开始相关性分析会话
        print("\n1️⃣ 开始相关性分析会话...")
        result = await start_visualization_session(
            user_request="请对天气数据进行相关性分析，生成热力图展示变量间的相关关系",
            read_data_param=ReadDataParam(read_data_query=str(data_file)),
            correlation_vars=["temperature", "humidity", "pressure", "wind_speed"],
            correlation_method="pearson"
        )
        
        session_info = json.loads(result)
        session_id = session_info["session_id"]
        chart_path = session_info["chart_path"]
        
        print(f"✅ 会话创建成功: {session_id}")
        print(f"📊 热力图已生成: {chart_path}")
        
        # 2. 第一次优化：改进颜色和标注
        print("\n2️⃣ 第一次优化：改进颜色和标注...")
        result = await refine_visualization(
            session_id=session_id,
            user_feedback="请使用蓝红色系颜色方案，并在热力图中显示具体的相关系数数值，字体调大一些"
        )
        
        refine_info = json.loads(result)
        print(f"✅ 优化完成: {refine_info['chart_path']}")
        
        # 3. 第二次优化：调整布局
        print("\n3️⃣ 第二次优化：调整布局...")
        result = await refine_visualization(
            session_id=session_id,
            user_feedback="请增加图表标题'天气变量相关性分析'，并调整图表大小使其更加方正"
        )
        
        refine_info = json.loads(result)
        print(f"✅ 优化完成: {refine_info['chart_path']}")
        
        # 4. 查看会话信息
        print("\n4️⃣ 查看会话信息...")
        info_result = await get_session_info(session_id)
        info = json.loads(info_result)
        print(f"📋 原始需求: {info['original_request']}")
        print(f"📋 当前版本: {info['current_version']}")
        print(f"📋 总迭代次数: {info['total_iterations']}")
        
        # 5. 清理会话
        print("\n5️⃣ 清理会话...")
        await delete_session(session_id)
        print("✅ 会话已清理")
        
        return True
        
    except Exception as e:
        print(f"❌ 相关性分析示例失败: {e}")
        return False

async def example_basic_visualization():
    """示例：基础数据可视化"""
    print("\n📈 示例：基础数据可视化")
    print("-" * 40)
    
    from interactive_visualization_server import (
        start_visualization_session, 
        refine_visualization,
        delete_session
    )
    
    # 创建销售数据示例
    data_dir = Path("./example_data")
    data_dir.mkdir(exist_ok=True)
    
    # 生成销售趋势数据
    dates = pd.date_range('2023-01-01', periods=12, freq='M')
    sales = np.random.normal(10000, 2000, 12).astype(int)
    profit = (sales * 0.2 + np.random.normal(0, 500, 12)).astype(int)
    
    sales_df = pd.DataFrame({
        'month': dates,
        'sales': sales,
        'profit': profit,
        'category': np.random.choice(['电子产品', '服装', '食品'], 12)
    })
    
    data_file = data_dir / "sales_example.csv"
    sales_df.to_csv(data_file, index=False)
    print(f"📁 示例数据已创建: {data_file}")
    
    try:
        # 1. 开始基础可视化会话
        print("\n1️⃣ 开始销售趋势可视化...")
        result = await start_visualization_session(
            user_request="请绘制销售趋势图，显示每月的销售额和利润变化",
            read_data_param=ReadDataParam(read_data_query=str(data_file))
        )
        
        session_info = json.loads(result)
        session_id = session_info["session_id"]
        chart_path = session_info["chart_path"]
        
        print(f"✅ 会话创建成功: {session_id}")
        print(f"📊 折线图已生成: {chart_path}")
        
        # 2. 优化：添加趋势线和样式
        print("\n2️⃣ 添加趋势线和改进样式...")
        result = await refine_visualization(
            session_id=session_id,
            user_feedback="请为销售额和利润都添加趋势线，使用更鲜艳的颜色，并加上图例"
        )
        
        refine_info = json.loads(result)
        print(f"✅ 优化完成: {refine_info['chart_path']}")
        
        # 3. 最终优化：改为柱状图
        print("\n3️⃣ 改为分组柱状图...")
        result = await refine_visualization(
            session_id=session_id,
            user_feedback="请改为分组柱状图，按月份显示销售额和利润，并添加数值标签"
        )
        
        refine_info = json.loads(result)
        print(f"✅ 优化完成: {refine_info['chart_path']}")
        
        # 4. 清理会话
        await delete_session(session_id)
        print("✅ 会话已清理")
        
        return True
        
    except Exception as e:
        print(f"❌ 基础可视化示例失败: {e}")
        return False

async def example_session_management():
    """示例：会话管理功能"""
    print("\n⚙️ 示例：会话管理功能")
    print("-" * 40)
    
    from interactive_visualization_server import (
        start_visualization_session,
        list_active_sessions,
        rollback_to_version,
        delete_session
    )
    
    # 使用之前创建的数据
    data_file = Path("./example_data/weather_example.csv")
    
    try:
        # 1. 创建多个会话
        print("\n1️⃣ 创建多个会话...")
        session_ids = []
        
        for i in range(2):
            result = await start_visualization_session(
                user_request=f"测试会话 {i+1}",
                read_data_param=ReadDataParam(read_data_query=str(data_file))
            )
            session_info = json.loads(result)
            session_ids.append(session_info["session_id"])
            print(f"✅ 会话 {i+1} 创建: {session_info['session_id']}")
        
        # 2. 列出活跃会话
        print("\n2️⃣ 列出活跃会话...")
        sessions_result = await list_active_sessions()
        sessions = json.loads(sessions_result)
        print(f"📋 当前活跃会话数: {sessions['total_sessions']}")
        for session in sessions['sessions']:
            print(f"   - {session['session_id']}: {session['user_request']}")
        
        # 3. 版本回滚测试（使用第一个会话）
        if session_ids:
            print(f"\n3️⃣ 测试版本回滚...")
            session_id = session_ids[0]
            
            # 先做几次修改
            await refine_visualization(session_id, "请调整颜色")
            await refine_visualization(session_id, "请调整大小")
            
            # 回滚到v1
            rollback_result = await rollback_to_version(session_id, "v1")
            rollback_info = json.loads(rollback_result)
            print(f"✅ 回滚成功: {rollback_info['chart_path']}")
        
        # 4. 清理所有会话
        print("\n4️⃣ 清理所有会话...")
        for session_id in session_ids:
            await delete_session(session_id)
            print(f"✅ 会话已删除: {session_id}")
        
        return True
        
    except Exception as e:
        print(f"❌ 会话管理示例失败: {e}")
        return False

async def example_visualization_with_table():
    """示例：同时获取可视化和相关性表格"""
    print("\n🔥📊 示例：可视化 + 相关性表格")
    print("-" * 40)
    
    from interactive_visualization_server import (
        visualization_with_correlation_table,
        get_correlation_table_only,
        delete_session
    )
    
    # 使用之前创建的天气数据
    data_file = Path("./example_data/weather_example.csv")
    
    try:
        # 1. 同时获取可视化和表格
        print("\n1️⃣ 同时获取可视化和相关性表格...")
        result = await visualization_with_correlation_table(
            user_request="请生成天气变量的相关性热力图，我需要同时查看图表和数据表格",
            read_data_param=ReadDataParam(read_data_query=str(data_file)),
            correlation_vars=["temperature", "humidity", "pressure", "wind_speed"],
            correlation_method="pearson"
        )
        
        result_data = json.loads(result)
        session_id = result_data["session_id"]
        chart_path = result_data["chart_path"]
        correlation_table = result_data.get("correlation_table", "")
        
        print(f"✅ 会话创建成功: {session_id}")
        print(f"📊 热力图已生成: {chart_path}")
        print(f"📋 相关性表格:")
        print("=" * 30)
        # 显示表格的前几行
        table_lines = correlation_table.split('\n')[:10]
        for line in table_lines:
            if line.strip():
                print(line)
        if len(correlation_table.split('\n')) > 10:
            print("... (表格内容较长，已截断)")
        print("=" * 30)
        
        # 2. 仅获取相关性表格（不生成图表）
        print("\n2️⃣ 仅获取相关性表格...")
        table_only_result = await get_correlation_table_only(
            read_data_param=ReadDataParam(read_data_query=str(data_file)),
            correlation_vars=["temperature", "humidity", "pressure"],
            correlation_method="spearman"  # 使用不同的方法
        )
        
        print("📋 斯皮尔曼相关性表格:")
        print("=" * 30)
        table_lines = table_only_result.split('\n')[:8]
        for line in table_lines:
            if line.strip():
                print(line)
        print("=" * 30)
        
        # 3. 清理会话
        await delete_session(session_id)
        print("✅ 会话已清理")
        
        return True
        
    except Exception as e:
        print(f"❌ 可视化+表格示例失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def example_multi_turn_conversation():
    """示例：多轮对话中用户需求变化的场景"""
    print("\n💬 示例：多轮对话中用户需求变化")
    print("-" * 40)
    
    from interactive_visualization_server import (
        start_visualization_session,
        start_correlation_analysis_only,
        get_correlation_table_from_session,
        visualize_existing_correlation,
        delete_session
    )
    
    # 使用之前创建的天气数据
    data_file = Path("./example_data/weather_example.csv")
    
    try:
        print("\n🔄 场景1：第一轮要图表，第二轮要表格")
        print("=" * 35)
        
        # 第一轮：用户只要相关性热力图
        print("第一轮对话：用户要相关性热力图")
        result1 = await start_visualization_session(
            user_request="请生成温度、湿度、压力的相关性热力图",
            read_data_param=ReadDataParam(read_data_query=str(data_file)),
            correlation_vars=["temperature", "humidity", "pressure"],
            include_correlation_table=False  # 第一轮不要表格
        )
        
        result1_data = json.loads(result1)
        session_id_1 = result1_data["session_id"]
        chart_path_1 = result1_data["chart_path"]
        has_correlation = result1_data.get("has_correlation_analysis", False)
        
        print(f"✅ 第一轮完成：会话 {session_id_1}")
        print(f"📊 生成图表：{chart_path_1}")
        print(f"📋 包含相关性分析：{has_correlation}")
        
        # 第二轮：用户想要看表格
        print("\n第二轮对话：用户想要查看相关性表格")
        table_result = await get_correlation_table_from_session(session_id_1)
        
        if "会话" not in table_result and "失败" not in table_result:
            print("✅ 成功获取相关性表格：")
            print("=" * 30)
            # 显示表格的前几行
            table_lines = table_result.split('\n')[:8]
            for line in table_lines:
                if line.strip():
                    print(line)
            print("=" * 30)
        else:
            print(f"❌ 获取表格失败：{table_result}")
        
        print("\n🔄 场景2：第一轮要表格，第二轮要图表")
        print("=" * 35)
        
        # 第一轮：用户只要相关性表格
        print("第一轮对话：用户只要相关性分析表格")
        result2 = await start_correlation_analysis_only(
            read_data_param=ReadDataParam(read_data_query=str(data_file)),
            correlation_vars=["temperature", "humidity", "pressure", "wind_speed"],
            correlation_method="spearman"
        )
        
        result2_data = json.loads(result2)
        session_id_2 = result2_data["session_id"]
        session_type_2 = result2_data["session_type"]
        correlation_table = result2_data["correlation_table"]
        
        print(f"✅ 第一轮完成：会话 {session_id_2}")
        print(f"📋 会话类型：{session_type_2}")
        print(f"📊 相关性表格长度：{len(correlation_table)} 字符")
        
        # 第二轮：用户想要生成图表
        print("\n第二轮对话：用户想要基于表格数据生成热力图")
        viz_result = await visualize_existing_correlation(
            session_id=session_id_2,
            visualization_request="请基于已有的相关性数据生成一个漂亮的热力图，使用蓝红色方案"
        )
        
        if viz_result.startswith("{"):
            viz_data = json.loads(viz_result)
            chart_path_2 = viz_data["chart_path"]
            version = viz_data["version"]
            print(f"✅ 成功生成图表：{chart_path_2}")
            print(f"📊 图表版本：{version}")
        else:
            print(f"❌ 生成图表失败：{viz_result}")
        
        print("\n🔄 场景3：灵活的多轮需求变化")
        print("=" * 30)
        
        # 基于现有会话继续对话
        print("继续第二个会话的对话...")
        
        # 第三轮：用户想要再次查看表格（验证数据一致性）
        print("第三轮：再次获取相关性表格验证一致性")
        table_result_3 = await get_correlation_table_from_session(session_id_2)
        
        if "会话" not in table_result_3 and "失败" not in table_result_3:
            print("✅ 成功获取表格，数据一致性验证通过")
            print(f"📊 表格长度：{len(table_result_3)} 字符")
        else:
            print(f"❌ 获取表格失败：{table_result_3}")
        
        # 清理会话
        print("\n🧹 清理测试会话...")
        await delete_session(session_id_1)
        await delete_session(session_id_2)
        print("✅ 所有会话已清理")
        
        return True
        
    except Exception as e:
        print(f"❌ 多轮对话示例失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """主示例函数"""
    print("🚀 交互式可视化系统使用示例")
    print("=" * 50)
    
    results = []
    
    # 运行相关性分析示例
    result1 = await example_correlation_analysis()
    results.append(("相关性分析", result1))
    
    # 运行基础可视化示例
    result2 = await example_basic_visualization()
    results.append(("基础可视化", result2))
    
    # 运行会话管理示例
    result3 = await example_session_management()
    results.append(("会话管理", result3))
    
    # 运行可视化+表格示例
    result4 = await example_visualization_with_table()
    results.append(("可视化+表格", result4))
    
    # 运行多轮对话示例
    result5 = await example_multi_turn_conversation()
    results.append(("多轮对话", result5))
    
    # 总结
    print("\n" + "=" * 50)
    print("📋 示例运行总结")
    print("=" * 50)
    
    success_count = sum(1 for _, success in results if success)
    total_count = len(results)
    
    for name, success in results:
        status = "✅ 成功" if success else "❌ 失败"
        print(f"{status} {name}")
    
    print(f"\n总体成功率: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)")
    
    if success_count == total_count:
        print("\n🎉 所有示例都运行成功！交互式可视化系统工作正常。")
        print("\n💡 提示：")
        print("- 检查 ./example_data/ 目录查看示例数据")
        print("- 检查 ./visualizations/ 目录查看生成的图表")
        print("- 阅读 interactive_visualization_api.md 了解更多API用法")
    else:
        print("\n⚠️ 部分示例失败，请检查系统配置和依赖。")

if __name__ == "__main__":
    asyncio.run(main()) 