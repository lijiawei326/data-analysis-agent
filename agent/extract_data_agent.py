from tools.extract_data import extract_data
from agents import Agent
from model_provider.model_provider import MODEL_PROVIDER
from custom_types.types import Data


extract_data_agent = Agent[Data](
    name="Extractor",
    instructions="根据用户需求，从指定路径或数据库提取数据",
    tools=[extract_data],
    model=MODEL_PROVIDER.get_model("qwen3:32b")
)
