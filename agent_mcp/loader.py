from agents import Agent, Runner
from model_provider.model_provider import MODEL_PROVIDER
from dataclasses import dataclass
from enum import Enum

class ReadMethod(Enum):
    SQL = "SQL"
    PANDAS = "PANDAS"

@dataclass
class DataReadParams:
    method: ReadMethod  # 只能是 ReadMethod.SQL 或 ReadMethod.PANDAS
    "读取方式：`SQL`或`PANDAS`"
    params: str
    "读取参数：SQL查询或文件路径"

loader_agent = Agent(
    name="loader_agent",
    instructions="""
    针对用户输入，提取数据读取参数。
    """,
    model=MODEL_PROVIDER.get_model(None),
    output_type=DataReadParams
)