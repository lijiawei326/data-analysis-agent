import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from mcp.server.fastmcp import FastMCP
from custom_types.types import AnalysisContext
from agent_mcp.loader import DataReadParams, loader_agent, ReadMethod
from agent_mcp.analyst import variable_analysis_agent, VariableAnalysisDecision, description_analysis_agent
from agent_mcp.visualization_agent import visualization_agent, correlation_visualization_agent, VisualizationCode
from agents import Runner
import time
import json
import asyncio
import pandas as pd
from utils.utils import remove_think
import pandas as pd
import numpy as np


mcp = FastMCP("AnalysisServer")
USER_AGENT = "analysis-app/1.0"

class Manager:
    def __init__(self) -> None:
        self.context = AnalysisContext()

    async def run(self, read_data_method, read_data_param) -> str:
        print('开始读取数据...')
        self.context.data.data = await self._load_data(read_data_method, read_data_param)
        print(f"数据：\n{self.context.data.data}")
        print('成功读取数据')

        time.sleep(1)

        print('开始清洗数据')
        await self._clean_data()
        print('成功清洗数据')

        print('开始生成分析报告')
        report = await self._descriptive_analysis()
        print('成功生成分析报告')
        return report

        

    async def _load_data(self, read_data_method, read_data_param) -> None:
        match read_data_method:
            case "SQL":
                return await self._load_data_from_sql(read_data_param)
            case "PANDAS":
                return await self._load_data_from_pandas(read_data_param)
            case _:
                raise ValueError(f"Invalid read_data_method: {read_data_method}. Expected 'SQL' or 'PANDAS'")

    async def _load_data_from_sql(self, read_data_param):
        raise NotImplementedError("SQL读取数据功能尚未实现")

    async def _load_data_from_pandas(self, read_data_param):
        from pathlib import Path
        try:
            # 规范化路径处理
            file_path = Path(read_data_param).absolute()
            
            # 检查文件是否存在
            if not file_path.exists():
                raise FileNotFoundError(f"文件不存在: {file_path}")
                
            # 获取文件扩展名（自动推断文件类型）
            file_ext = file_path.suffix.lower()
            
            # 根据扩展名选择读取方法
            match file_ext:
                case ".csv":
                    return pd.read_csv(file_path)
                case ".xlsx" | ".xls":
                    return pd.read_excel(file_path)
                case ".parquet":
                    return pd.read_parquet(file_path)
                case ".json":
                    return pd.read_json(file_path)
                case ".feather":
                    return pd.read_feather(file_path)
                case ".h5" | ".hdf":
                    return pd.read_hdf(file_path)
                case _:
                    raise ValueError(f"不支持的文件类型: {file_ext}")
                    
        except Exception as e:
            raise ValueError(f"从pandas加载数据失败: {str(e)}")
    
    async def _clean_data(self):
        pass

    async def _descriptive_analysis(self):
        all_variables = self.context.data.data.columns.tolist()
        print(f'所有变量：{all_variables}')
        # Run all variable analyses concurrently
        tasks = [
            asyncio.create_task(
                self._generate_analysis_report(variable)
            )
            for variable in all_variables
        ]
        report = ''
        for task in asyncio.as_completed(tasks):
            result = await task
            report += result + '\n\n'

        return report

    async def _get_variable_description(self, series):
        match series.dtype.kind:
            case 'f' | 'i' | 'u':  # 数值型数据（浮点、整数、无符号整数）
                desc = series.describe()
                return {
                    'type': 'numeric',
                    'count': desc['count'],
                    'mean': desc['mean'],
                    'std': desc['std'],
                    'min': desc['min'],
                    '25%': desc['25%'],
                    '50%': desc['50%'],
                    '75%': desc['75%'],
                    'max': desc['max'],
                    'unique': series.nunique(),
                    'missing': series.isna().sum()
                }
                
            case 'b':  # 布尔型数据
                desc = series.value_counts(dropna=False)
                return {
                    'type': 'boolean',
                    'count': len(series),
                    'true_count': desc.get(True, 0),
                    'false_count': desc.get(False, 0),
                    'unique': 2,  # True/False
                    'missing': desc.get(pd.NA, 0)
                }
                
            case 'O' | 'S' | 'U':  # 对象/字符串类型
                return {
                    'type': 'categorical',
                    'count': len(series),
                    'unique': series.nunique(),
                    'top': series.mode().iloc[0] if not series.empty else None,
                    'freq': series.value_counts().iloc[0] if not series.empty else 0,
                    'missing': series.isna().sum()
                }
                
            case 'M':  # 日期时间类型
                desc = series.describe(datetime_is_numeric=True)
                return {
                    'type': 'datetime',
                    'count': desc['count'],
                    'first': desc['first'],
                    'last': desc['last'],
                    'min': desc['min'],
                    'max': desc['max'],
                    'unique': series.nunique(),
                    'missing': series.isna().sum()
                }
                
            case _:  # 其他未知类型
                return {
                    'type': 'unknown',
                    'count': len(series),
                    'unique': series.nunique(),
                    'missing': series.isna().sum()
                }
            
    async def _generate_analysis_report(self, variable_name):
        """
        生成单个变量的分析报告
        """
        # ---------------判断是否进行分析---------------#
        series = self.context.data.data[variable_name]
        values_str = np.array2string(series.values, threshold=np.inf)
        variable_info = json.dumps(
            {
                "variable_name": variable_name,
                "variable_dtype": str(series.dtype),
                "value": (values_str[:10000] + '...（**数据已截断**）'
                         if len(values_str) > 10000 
                         else values_str),
            }
        )

        print(f'变量 {variable_name} 的信息：\n{variable_info}')
        try:
            time.sleep(1)  # 添加1秒延迟
            judge_result = await Runner.run(
                starting_agent=variable_analysis_agent,
                input=variable_info
            )
            judge_result = judge_result.final_output_as(VariableAnalysisDecision)
        except Exception as e:
            print(f'变量 {variable_name} 分析失败：{e}')
            return f'## {variable_name}不进行分析\n原因：{e}'
        # ---------------------分析---------------------#
        print(f"============变量：{variable_name}=============")
        print(f"是否分析：{judge_result.should_analyze}\n原因：{judge_result.reason}")
        if judge_result.should_analyze:
            variable_description_info = json.dumps(
                {
                    "variable_name": variable_name,
                    "variable_description": str(await self._get_variable_description(series))
                }
            )
            time.sleep(1)  # 添加1秒延迟
            single_variable_report = await Runner.run(
                starting_agent=description_analysis_agent,
                input=variable_description_info
            )
            print(f'变量 {variable_name} 的描述报告：\n{single_variable_report.final_output}')
            return remove_think(single_variable_report.final_output)
        else:
            return f'## {variable_name}不进行分析\n原因：{judge_result.reason}'

    async def get_data_summary(self):
        """
        获取数据摘要信息，用于可视化agent
        """
        if self.context.data.data is None:
            raise ValueError("数据尚未加载")
            
        df = self.context.data.data
        summary = {
            'shape': df.shape,
            'columns': df.columns.tolist(),
            'dtypes': {col: str(dtype) for col, dtype in df.dtypes.items()},
            'numeric_columns': df.select_dtypes(include=[np.number]).columns.tolist(),
            'categorical_columns': df.select_dtypes(include=['object', 'category']).columns.tolist(),
            'missing_values': df.isnull().sum().to_dict(),
            'sample_data': df.head().to_dict()
        }
        return summary

    async def generate_visualization_code(self, visualization_request: str):
        """
        生成可视化代码
        """
        if self.context.data.data is None:
            raise ValueError("数据尚未加载")
            
        # 获取数据摘要
        data_summary = await self.get_data_summary()
        
        # 构建输入信息
        input_info = json.dumps({
            'visualization_request': visualization_request,
            'data_summary': data_summary
        })
        
        print(f'可视化请求：{visualization_request}')
        print(f'数据摘要：{data_summary}')
        
        try:
            time.sleep(1)
            result = await Runner.run(
                starting_agent=visualization_agent,
                input=input_info
            )
            viz_code = result.final_output_as(VisualizationCode)
            return viz_code
        except Exception as e:
            print(f'可视化代码生成失败：{e}')
            raise ValueError(f'可视化代码生成失败: {e}')

    async def generate_correlation_visualization_code(self):
        """
        生成相关性分析可视化代码
        """
        if self.context.data.data is None:
            raise ValueError("数据尚未加载")
            
        # 获取数据摘要
        data_summary = await self.get_data_summary()
        
        # 构建输入信息
        input_info = json.dumps({
            'analysis_type': 'correlation',
            'data_summary': data_summary
        })
        
        print(f'生成相关性分析可视化代码')
        print(f'数据摘要：{data_summary}')
        
        try:
            time.sleep(1)
            result = await Runner.run(
                starting_agent=correlation_visualization_agent,
                input=input_info
            )
            viz_code = result.final_output_as(VisualizationCode)
            return viz_code
        except Exception as e:
            print(f'相关性可视化代码生成失败：{e}')
            raise ValueError(f'相关性可视化代码生成失败: {e}')

@mcp.tool()
async def analysis_report(read_data_method, read_data_param):
    """
    生成数据分析报告。
    :param read_data_method: 读取数据的方式，包括`SQL`或`PANDAS`
    :param read_data_param: SQL查询语句或文件路径
    """
    manager = Manager()
    try:
        result = await manager.run(read_data_method, read_data_param)
    except Exception as e:
        return f'数据分析报告生成失败: {e}'
    print(result)
    return result


@mcp.tool()
async def generate_visualization_code(read_data_method, read_data_param, visualization_request):
    """
    生成可视化代码。
    :param read_data_method: 读取数据的方式，包括`SQL`或`PANDAS`
    :param read_data_param: SQL查询语句或文件路径
    :param visualization_request: 可视化需求描述
    """
    manager = Manager()
    try:
        # 加载数据
        print('开始读取数据...')
        manager.context.data.data = await manager._load_data(read_data_method, read_data_param)
        print('成功读取数据')
        
        # 生成可视化代码
        viz_code = await manager.generate_visualization_code(visualization_request)
        
        return {
            'success': True,
            'code': viz_code.code,
            'description': viz_code.description,
            'chart_type': viz_code.chart_type
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'可视化代码生成失败: {e}',
            'code': '',
            'description': '',
            'chart_type': ''
        }


@mcp.tool()
async def generate_correlation_visualization_code(read_data_method, read_data_param):
    """
    生成相关性分析可视化代码。
    :param read_data_method: 读取数据的方式，包括`SQL`或`PANDAS`
    :param read_data_param: SQL查询语句或文件路径
    """
    manager = Manager()
    try:
        # 加载数据
        print('开始读取数据...')
        manager.context.data.data = await manager._load_data(read_data_method, read_data_param)
        print('成功读取数据')
        
        # 生成相关性可视化代码
        viz_code = await manager.generate_correlation_visualization_code()
        
        return {
            'success': True,
            'code': viz_code.code,
            'description': viz_code.description,
            'chart_type': viz_code.chart_type
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'相关性可视化代码生成失败: {e}',
            'code': '',
            'description': '',
            'chart_type': ''
        }


@mcp.tool()
async def get_data_summary_info(read_data_method, read_data_param):
    """
    获取数据摘要信息。
    :param read_data_method: 读取数据的方式，包括`SQL`或`PANDAS`
    :param read_data_param: SQL查询语句或文件路径
    """
    manager = Manager()
    try:
        # 加载数据
        print('开始读取数据...')
        manager.context.data.data = await manager._load_data(read_data_method, read_data_param)
        print('成功读取数据')
        
        # 获取数据摘要
        summary = await manager.get_data_summary()
        
        return {
            'success': True,
            'summary': summary
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'获取数据摘要失败: {e}',
            'summary': {}
        }


if __name__ == '__main__':
    mcp.run(transport='sse')

