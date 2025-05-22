from agents import Agent, ModelSettings
from custom_types.types import AnalysisResult
from model_provider.model_provider import MODEL_PROVIDER
from agent.load_data_agent import load_data_agent
from agent.data_cleaning_agent import data_cleaning_agent
from agent.description_analysis_agent import description_analysis_agent


system_prompt = """
你是一个数据分析智能体，你可以使用工具辅助进行数据分析。

**状态验证**：
1. 确保已读取数据，否则首先读取数据
2. 核验用户清洗需求，除明确无需清洗数据，否则在保证数据已读取的情况下进行清洗。

**行为规范**：
1. 请勿向用户透露工具名称及参数。
2. 只具备已登记工具的能力，请不要向用户提出任何工具之外的能力。
3. 当用户提出任何工具之外的需求时，请向用户解释并拒绝。

**默认流程**：
状态验证 -> 描述性分析
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
        ),
        description_analysis_agent.as_tool(
            tool_name='description_report',
            tool_description='对多个变量进行描述性分析，请输入分析的要求'
        )
    ],
    model_settings=ModelSettings(
        parallel_tool_calls=True
    )
)
