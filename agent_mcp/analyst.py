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
    2. 常量（数据未截断情况下）不建议分析
    3. 有实际分析意义的分类变量、数值变量建议分析
    4. 包含有意义信息的文本变量可以考虑分析
    
    输出格式要求：Your response should be in the form of JSON with the following schema: {'response':{'variable_name': '需要评估的变量名称', 'reason': '是否建议对该变量进行描述性统计分析的原因', 'should_analyze': '是否建议对该变量进行描述性统计分析'}}. 
    ** Do not include any other text and do not wrap the response in a code block (like ```json ```) - just provide the raw json output.**
    语言：简体中文
    """,
    model=MODEL_PROVIDER.get_model(None),
    output_type=VariableAnalysisDecision
)


description_analysis_agent = Agent(
    name="description_analysis_agent",
    instructions="""
    你是一个数据分析专家，负责进行描述性分析报告。
    请遵循以下原则：
    1. **必须以"## 变量：<变量名称> 描述性分析"为标题开头**
    2. 除标题外，只能使用三级标题
    3. 请直接输出报告，不要有其他回复。
    输出风格：Markdown
    语言：中文
    """,
    model=MODEL_PROVIDER.get_model(None),
)






