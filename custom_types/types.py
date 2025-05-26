from dataclasses import dataclass, field
from typing import Any, Dict
from pydantic import BaseModel, Field
from typing_extensions import Literal

@dataclass
class Data:
    data: Any = None
    """数据内容"""

    washed: bool = False
    """是否清洗"""

@dataclass
class AnalysisResult:
    id: str = field(default="")
    """数据分析id"""

    text: str = field(default="")
    """数据分析结果文本"""

@dataclass
class PictureResult:
    title: str = field(default="")
    """图片名称"""

    path: str = field(default="")
    """图片路径"""

    description: str = field(default="")
    """图片描述"""

@dataclass
class AnalysisContext:
    data: Data = field(default_factory=Data)
    result: Dict[str, AnalysisResult] = field(default_factory=dict)
    pics: Dict[str, PictureResult] = field(default_factory=dict)


class ReadDataParam(BaseModel):
    read_data_method: Literal["PANDAS", "SQL"] = Field(description="读取数据方法, 仅限于`SQL`或`PANDAS`")
    read_data_query: str = Field(description="SQL查询语句或文件路径")