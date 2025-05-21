from agents import Agent
from custom_types.types import AnalysisContext
from model_provider.model_provider import MODEL_PROVIDER


conversation_agent = Agent[AnalysisContext](
    name="conversation_agent",
    instructions="""
    你是一个对话智能体，负责回复用户的日常问题，如果用户需要进行数据分析，请转接给分析智能体。
    """,
    model=MODEL_PROVIDER.get_model(None)
)