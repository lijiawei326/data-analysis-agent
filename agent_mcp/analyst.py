from agents import Agent
from dataclasses import dataclass
from model_provider.model_provider import MODEL_PROVIDER



#-------------变量判断-------------#
@dataclass
class VariableAnalysisDecision:
    """变量分析决策结果"""
    variable_name: str
    "需要评估的变量名称"
    reason: str
    "是否建议对该变量进行描述性统计分析的原因"
    should_analyze: bool
    "是否建议对该变量进行描述性统计分析"

variable_analysis_agent = Agent(
    name="变量分析评估器",
    instructions="""
    你是一个数据分析评估专家，负责判断给定的变量是否值得进行描述性统计分析。
    请根据以下原则进行评估：
    1. 像ID、序号等唯一标识符变量不建议分析
    2. 常量或几乎不变的变量不建议分析
    3. 有实际分析意义的分类变量、数值变量建议分析
    4. 包含有意义信息的文本变量可以考虑分析
    
    请仔细评估变量名称的含义和可能的数据特性，给出是否分析的建议。
    """,
    model=MODEL_PROVIDER.get_model(None),
    output_type=VariableAnalysisDecision
)


description_analysis_agent = Agent(
    name="description_analysis_agent",
    instructions="""
    你是一个数据分析专家，负责进行描述性分析。

    输出风格：Markdown
    语言：中文
    """,
    model=MODEL_PROVIDER.get_model(None),
)






