from agents import Agent
from model_provider.model_provider import MODEL_PROVIDER
from custom_types.types import AnalysisResult


system_prompt = """

"""

description_analysis_agent = Agent[AnalysisResult](
    name="description_analysis_agent",
    instructions=system_prompt,
    model=MODEL_PROVIDER.get_model(None),
    tools=[],
)
