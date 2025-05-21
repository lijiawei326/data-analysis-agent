from agents import Agent, ModelSettings
from tools.data_cleaning import clean_data
from model_provider.model_provider import MODEL_PROVIDER
from custom_types.types import AnalysisResult


system_prompt = """
你是一个数据清洗执行器，当需要清洗数据时，严格按以下规则响应：
1. 直接调用data_leaning工具
2. 完成清洗后转接给下一个智能体
3. 当遇到无法执行的任务时，转接给其他智能体
"""

data_cleaning_agent = Agent[AnalysisResult](
    name="data_cleaning_agent",
    instructions=system_prompt,
    tools=[clean_data],
    model=MODEL_PROVIDER.get_model(None),
    model_settings=ModelSettings(
        tool_choice="auto"
    )
)