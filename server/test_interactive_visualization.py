"""
交互式可视化系统测试脚本
验证MCP服务器和Agent的基本功能
"""

import asyncio
import json
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# 添加项目路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))
sys.path.append(str(PROJECT_ROOT / 'frontend'))

from custom_types.types import ReadDataParam
from interactive_visualization_server import (
    start_visualization_session, 
    refine_visualization,
    get_session_info,
    list_active_sessions,
    delete_session,
    visualization_with_correlation_table,
    get_correlation_table_only
)

class InteractiveVisualizationTester:
    """交互式可视化系统测试器"""
    
    def __init__(self):
        self.test_data_dir = Path("./test_data")
        self.test_data_dir.mkdir(exist_ok=True)
        self.test_results = []
        
    def create_test_data(self):
        """创建测试数据"""
        print("📊 创建测试数据...")
        
        # 创建相关性分析测试数据
        np.random.seed(42)
        n_samples = 100
        
        # 生成相关的数值数据
        temperature = np.random.normal(25, 5, n_samples)
        humidity = 0.6 * temperature + np.random.normal(40, 8, n_samples)
        pressure = -0.3 * temperature + np.random.normal(1013, 15, n_samples)
        wind_speed = np.random.exponential(10, n_samples)
        
        weather_data = pd.DataFrame({
            'temperature': temperature,
            'humidity': humidity,
            'pressure': pressure,
            'wind_speed': wind_speed,
            'date': pd.date_range('2024-01-01', periods=n_samples, freq='D')
        })
        
        weather_file = self.test_data_dir / "weather_data.csv"
        weather_data.to_csv(weather_file, index=False)
        
        # 创建销售数据
        sales_data = pd.DataFrame({
            'month': pd.date_range('2023-01-01', periods=12, freq='M'),
            'sales': np.random.normal(10000, 2000, 12).astype(int),
            'profit': np.random.normal(2000, 500, 12).astype(int),
            'category': np.random.choice(['A', 'B', 'C'], 12)
        })
        
        sales_file = self.test_data_dir / "sales_data.csv"
        sales_data.to_csv(sales_file, index=False)
        
        print(f"✅ 测试数据已创建:")
        print(f"   - {weather_file}")
        print(f"   - {sales_file}")
        
        return weather_file, sales_file
    
    async def test_correlation_heatmap(self, weather_file):
        """测试相关性热力图功能"""
        print("\n🔥 测试相关性热力图...")
        
        try:
            # 开始相关性分析会话
            result = await start_visualization_session(
                user_request="请对天气数据进行相关性分析并生成热力图",
                read_data_param=ReadDataParam(read_data_query=str(weather_file)),
                correlation_vars=["temperature", "humidity", "pressure", "wind_speed"],
                correlation_method="pearson"
            )
            
            result_data = json.loads(result)
            session_id = result_data["session_id"]
            chart_path = result_data["chart_path"]
            
            print(f"✅ 会话创建成功: {session_id}")
            print(f"✅ 热力图生成: {chart_path}")
            
            # 测试优化功能
            refine_result = await refine_visualization(
                session_id=session_id,
                user_feedback="请使用更明亮的颜色方案，并在热力图中显示相关系数的数值"
            )
            
            refine_data = json.loads(refine_result)
            print(f"✅ 图表优化成功: {refine_data['chart_path']}")
            
            self.test_results.append({
                "test": "correlation_heatmap",
                "status": "success",
                "session_id": session_id,
                "charts": [chart_path, refine_data['chart_path']]
            })
            
            return session_id
            
        except Exception as e:
            print(f"❌ 相关性热力图测试失败: {e}")
            self.test_results.append({
                "test": "correlation_heatmap",
                "status": "failed",
                "error": str(e)
            })
            return None
    
    async def test_basic_visualization(self, sales_file):
        """测试基础可视化功能"""
        print("\n📈 测试基础可视化...")
        
        try:
            # 开始基础可视化会话
            result = await start_visualization_session(
                user_request="请绘制销售趋势的折线图，显示每月的销售额变化",
                read_data_param=ReadDataParam(read_data_query=str(sales_file))
            )
            
            result_data = json.loads(result)
            session_id = result_data["session_id"]
            chart_path = result_data["chart_path"]
            
            print(f"✅ 会话创建成功: {session_id}")
            print(f"✅ 折线图生成: {chart_path}")
            
            # 测试多轮优化
            feedback_list = [
                "请添加利润的第二条线，使用不同颜色",
                "请添加图例和网格线，并增大字体",
                "请改为柱状图显示，按类别分组"
            ]
            
            for i, feedback in enumerate(feedback_list, 1):
                refine_result = await refine_visualization(
                    session_id=session_id,
                    user_feedback=feedback
                )
                refine_data = json.loads(refine_result)
                print(f"✅ 第{i}轮优化成功: {refine_data['chart_path']}")
            
            self.test_results.append({
                "test": "basic_visualization",
                "status": "success",
                "session_id": session_id,
                "iterations": len(feedback_list) + 1
            })
            
            return session_id
            
        except Exception as e:
            print(f"❌ 基础可视化测试失败: {e}")
            self.test_results.append({
                "test": "basic_visualization",
                "status": "failed",
                "error": str(e)
            })
            return None
    
    async def test_session_management(self, session_ids):
        """测试会话管理功能"""
        print("\n⚙️ 测试会话管理...")
        
        try:
            # 测试列出活跃会话
            sessions_result = await list_active_sessions()
            sessions_data = json.loads(sessions_result)
            print(f"✅ 活跃会话数量: {sessions_data['total_sessions']}")
            
            # 测试获取会话信息
            if session_ids:
                for session_id in session_ids:
                    if session_id:
                        info_result = await get_session_info(session_id)
                        info_data = json.loads(info_result)
                        print(f"✅ 会话信息获取成功: {session_id}")
                        print(f"   版本: {info_data.get('current_version', 'N/A')}")
                        print(f"   迭代次数: {info_data.get('total_iterations', 0)}")
            
            self.test_results.append({
                "test": "session_management",
                "status": "success",
                "active_sessions": sessions_data['total_sessions']
            })
            
        except Exception as e:
            print(f"❌ 会话管理测试失败: {e}")
            self.test_results.append({
                "test": "session_management",
                "status": "failed",
                "error": str(e)
            })
    
    async def test_rollback_functionality(self, session_id):
        """测试版本回滚功能"""
        if not session_id:
            return
            
        print("\n🔄 测试版本回滚...")
        
        try:
            # 回滚到第一个版本
            rollback_result = await rollback_to_version(session_id, "v1")
            rollback_data = json.loads(rollback_result)
            print(f"✅ 回滚成功: {rollback_data['chart_path']}")
            
            self.test_results.append({
                "test": "rollback_functionality",
                "status": "success",
                "session_id": session_id
            })
            
        except Exception as e:
            print(f"❌ 版本回滚测试失败: {e}")
            self.test_results.append({
                "test": "rollback_functionality",
                "status": "failed",
                "error": str(e)
            })
    
    async def cleanup_sessions(self, session_ids):
        """清理测试会话"""
        print("\n🧹 清理测试会话...")
        
        for session_id in session_ids:
            if session_id:
                try:
                    await delete_session(session_id)
                    print(f"✅ 会话已删除: {session_id}")
                except Exception as e:
                    print(f"⚠️ 删除会话失败: {session_id}, {e}")
    
    async def test_visualization_with_table(self, weather_file):
        """测试同时获取可视化和相关性表格"""
        print("\n🔥📊 测试可视化 + 相关性表格...")
        
        try:
            # 测试同时获取可视化和表格
            result = await visualization_with_correlation_table(
                user_request="请生成相关性热力图，同时需要查看数据表格",
                read_data_param=ReadDataParam(read_data_query=str(weather_file)),
                correlation_vars=["temperature", "humidity", "pressure", "wind_speed"],
                correlation_method="pearson"
            )
            
            result_data = json.loads(result)
            session_id = result_data["session_id"]
            chart_path = result_data["chart_path"]
            correlation_table = result_data.get("correlation_table", "")
            
            print(f"✅ 可视化会话创建成功: {session_id}")
            print(f"✅ 热力图生成: {chart_path}")
            print(f"✅ 相关性表格获取成功: {len(correlation_table)} 字符")
            
            # 测试仅获取表格
            table_result = await get_correlation_table_only(
                read_data_param=ReadDataParam(read_data_query=str(weather_file)),
                correlation_vars=["temperature", "humidity"],
                correlation_method="spearman"
            )
            
            print(f"✅ 仅表格获取成功: {len(table_result)} 字符")
            
            self.test_results.append({
                "test": "visualization_with_table",
                "status": "success",
                "session_id": session_id,
                "has_chart": bool(chart_path),
                "has_table": bool(correlation_table),
                "table_only": bool(table_result)
            })
            
            return session_id
            
        except Exception as e:
            print(f"❌ 可视化+表格测试失败: {e}")
            self.test_results.append({
                "test": "visualization_with_table",
                "status": "failed",
                "error": str(e)
            })
            return None
    
    def print_test_summary(self):
        """打印测试总结"""
        print("\n" + "="*60)
        print("📋 测试总结")
        print("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["status"] == "success")
        failed_tests = total_tests - passed_tests
        
        print(f"总测试数: {total_tests}")
        print(f"通过: {passed_tests}")
        print(f"失败: {failed_tests}")
        print(f"成功率: {passed_tests/total_tests*100:.1f}%")
        
        print("\n详细结果:")
        for result in self.test_results:
            status_icon = "✅" if result["status"] == "success" else "❌"
            print(f"{status_icon} {result['test']}: {result['status']}")
            if result["status"] == "failed":
                print(f"   错误: {result.get('error', 'Unknown error')}")
        
        if failed_tests == 0:
            print("\n🎉 所有测试通过！交互式可视化系统运行正常。")
        else:
            print(f"\n⚠️ 有{failed_tests}个测试失败，请检查系统配置。")

async def main():
    """主测试函数"""
    print("🚀 启动交互式可视化系统测试")
    print("="*60)
    
    tester = InteractiveVisualizationTester()
    
    try:
        # 1. 创建测试数据
        weather_file, sales_file = tester.create_test_data()
        
        # 2. 测试相关性热力图
        session_id_1 = await tester.test_correlation_heatmap(weather_file)
        
        # 3. 测试基础可视化
        session_id_2 = await tester.test_basic_visualization(sales_file)
        
        # 4. 测试会话管理
        session_ids = [session_id_1, session_id_2]
        await tester.test_session_management(session_ids)
        
        # 5. 测试版本回滚
        await tester.test_rollback_functionality(session_id_2)
        
        # 6. 测试同时获取可视化和相关性表格
        session_id_3 = await tester.test_visualization_with_table(weather_file)
        
        # 7. 清理会话
        session_ids.append(session_id_3)
        await tester.cleanup_sessions(session_ids)
        
        # 8. 打印测试总结
        tester.print_test_summary()
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # 运行测试
    asyncio.run(main()) 