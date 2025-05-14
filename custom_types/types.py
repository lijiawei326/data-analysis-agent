from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class Data:
    data: Any
    "数据内容"

    washed: bool = False
    "是否清洗"

@dataclass
class AnalysisResult:
    id: str
    "数据分析id"

    text: str
    "数据分析结果文本"

@dataclass
class PictureResult:
    title: str
    "图片名称"

    path: str
    "图片路径"

    description: str = None
    "图片描述"


@dataclass
class AnalysisContext:
    data: Data = field(default_factory=Data)
    result: Dict[str, AnalysisResult] = field(default_factory=dict)
    pics: Dict[str, PictureResult] = field(default_factory=dict)