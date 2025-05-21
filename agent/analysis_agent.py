from agents import Agent, ModelSettings
from custom_types.types import AnalysisResult
from model_provider.model_provider import MODEL_PROVIDER
from agent.load_data_agent import load_data_agent
from agent.data_cleaning_agent import data_cleaning_agent


system_prompt = """
你是一个数据分析智能体，你可以使用工具辅助进行数据分析。

请严格遵守以下规范：
1. 只具备已登记工具的能力，请不要向用户提出任何工具之外的能力。
2. 当用户提出任何工具之外的需求时，请向用户解释并拒绝。
"""


analysis_agent = Agent[AnalysisResult](
    name="analysis_agent",
    instructions=system_prompt,
    model=MODEL_PROVIDER.get_model(None),
    tools=[
        load_data_agent.as_tool(
            tool_name="load_data",
            tool_description="加载数据"
        ),
        data_cleaning_agent.as_tool(
            tool_name="clean_data",
            tool_description="清洗数据"
        )
    ],
    model_settings=ModelSettings(
        parallel_tool_calls=True
    )
)
