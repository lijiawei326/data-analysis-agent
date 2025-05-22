from agents import function_tool
from agents import RunContextWrapper
import pandas as pd
from model_provider.model_provider import MODEL_PROVIDER
from agents import Agent, Runner
from typing import List, Dict
import json
import re
from pydantic import BaseModel
from custom_types.types import Data
import asyncio
from datetime import datetime
from utils.utils import remove_think


describe_data_agent = Agent(
    name="describe_data_agent",
    instructions='基于已有信息对数据进行简短的描述性分析',
    model=MODEL_PROVIDER.get_model(None)
)

report_agent = Agent(
    name="report_agent",
    instructions="""
## 角色定位
您是一个数据分析师，根据已有数据信息和用户需求，智能生成分析报告章节。

## 核心规则
1. **标题规范**
   - 必须且仅能使用`## <变量名称>分析`作为最高级标题
   - 子标题层级自由控制（`###`及以下）

2. **内容原则**
   - 必须包含：
     - 基础特征描述（类型/样本量/缺失值）
     - 关键统计特征
     - 数据质量说明
   - 禁止包含：
     - 与当前变量无关的分析
     - 未经计算的推测性结论

3. **输出要求**
   - 严格使用Markdown风格
   - 数值结果需标明统计方法
   - 专业术语首次出现时括号注释
""",
    model=MODEL_PROVIDER.get_model(None)
)


@function_tool()
async def fetch_data_info(context: RunContextWrapper):
    """
    获取读取到的数据的具体信息
    """
    if context.context.data.data is None:
        return '数据为空，请先读取数据'
    print('#######数据信息########')
    print(context.context.data.data.head())
    print('######################')
    data = context.context.data.data
    info = "数据类型信息：\n"
    for column in data.columns:
        info += f"{column}: {data[column].dtype}\n"
    info += "\n前五条数据：\n"
    info += str(data.head())
    return info


async def analysis_single_variable(context: RunContextWrapper, reason: str, variable: str):
    """
    对一个变量进行分析
    :param reason: 对该变量进行分析的原因
    :param variable: 变量名
    """
    print(f'开始分析{variable}，原因：{reason}')
    variable_data = context.context.data.data[variable]
    try:
        if variable_data.dtype == 'object':
            res =  f'{variable}的计算结果为：\n{variable_data.value_counts()}'
        elif variable_data.dtype == 'int64' or variable_data.dtype == 'float64':
            res = f'{variable}的计算结果为：\n{variable_data.describe()}'
        elif variable_data.dtype == 'datetime64':
            res = f'{variable}的计算结果为：\n{variable_data.describe()}'
        elif variable_data.dtype == 'bool':
            res = f'{variable}的计算结果为：\n{variable_data.value_counts()}'
        elif variable_data.dtype == 'category':
            res = f'{variable}的计算结果为：\n{variable_data.describe()}'
        else:
            res = f'{variable}的计算结果为：\n{variable_data.describe()}'
    except Exception as e:
        return f'## 变量{variable}无法分析，发生错误:{e}'

    report = await Runner.run(
        starting_agent=report_agent,
        input=res
    )
    return report.final_output


class VariableInput(BaseModel):
    variable: str
    reason: str


@function_tool(strict_mode=True)
async def analysis_multiple_variables(context: RunContextWrapper, inputs: List[VariableInput]):
    """
    对多个变量并行进行分析，传入值得分析的变量和该变量值得分析的原因, 返回markdown格式的数据分析报告
    :param inputs: 一个列表，每个元素包含以下字段:
        - variable: 变量名称
        - reason: 该变量值得分析的原因
    :return: 一个markdown格式的数据分析报告
    """
    if context.context.data.data is None:
        return '数据为空，请先读取数据'
    
    # 创建所有变量的分析任务
    tasks = [analysis_single_variable(context, input.reason, input.variable) for input in inputs]
    
    # 并行执行所有任务
    reports = await asyncio.gather(*tasks)
    
    # 处理结果
    description_report = ''
    for report in reports:
        output = remove_think(report)
        description_report += '\n' + output
    
    context.context.result['description_report'] = description_report
    report_path = f'./logs/reports_{datetime.now().strftime("%Y%m%d_%H%M%S")}.md'
    with open(report_path, 'w') as f:
        f.write(description_report)
    return f'变量描述性分析报告已生成，文件路径为：{report_path}\n\n生成内容为：{description_report}'



# class Analyst:
#     def __init__(self):
#         self.report_agent = Agent[Data](
#             name="report_agent",
#             instructions='基于已有信息生成数据分析报告',
#             model=MODEL_PROVIDER.get_model(None)
#         )

#     async def generate_report(self, variable: str, reason: str):
#         res = await Runner.run(
#             starting_agent=self.report_agent,
#             input=f'变量：{variable}，原因：{reason}'
#         )
#         return res.final_output
        
        
        