from tools.load_data import load_data
from agents import Agent
from model_provider.model_provider import MODEL_PROVIDER
from custom_types.types import AnalysisResult
from agents import ModelSettings


system_prompt = """
# 你是一个数据读取智能体，负责读取数据
"""

load_data_agent = Agent[AnalysisResult](
    name="Data_Loader",
    instructions=system_prompt,
    tools=[load_data],
    model=MODEL_PROVIDER.get_model(None),
    model_settings=ModelSettings(
        tool_choice="auto"
    )
)
