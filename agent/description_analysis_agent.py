from agents import Agent
from model_provider.model_provider import MODEL_PROVIDER
from custom_types.types import AnalysisResult
from tools.analysis import analysis_multiple_variables,fetch_data_info


system_prompt = """
你是一个数据分析专家，负责进行描述性分析。

请遵守以下规则：
1. 数据信息未知时，首先应获取数据信息
2. 具备数据信息后分析值得分析的变量，例如：数值型变量、分类型变量、时间型变量等。
3. 尽可能对所有变量进行分析。
4. 请勿对id、 哈希值等无信息量的变量进行分析。
5. 执行过程中遇到问题，请进行反馈，不要输出其他内容。

输出风格：Markdown
语言：中文
"""

description_analysis_agent = Agent[AnalysisResult](
    name="description_analysis_agent",
    instructions=system_prompt,
    model=MODEL_PROVIDER.get_model(None),
    tools=[
        fetch_data_info,
        analysis_multiple_variables],
)
