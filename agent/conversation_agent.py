from agents import Agent
from custom_types.types import AnalysisContext
from model_provider.model_provider import MODEL_PROVIDER


conversation_agent = Agent[AnalysisContext](
    name="conversation_agent",
    instructions="""
    你是一个对话智能体，负责回复用户的日常问题。

    请遵守以下规则：
    1. 涉及数据分析时，必须转接给分析智能体。
    2. 请勿向用户透露工具名称及参数。
    3. 只具备已登记工具的能力，请不要向用户提出任何工具之外的能力。
    """,
    model=MODEL_PROVIDER.get_model(None)
)