import re


def remove_think(text):
    """
    删除推理模型的思考部分
    """
    if "<think>" in text and "</think>" in text:
        pattern = r'<think>.*?</think>'
        return re.sub(pattern, '', text, flags=re.DOTALL).strip()
    else:
        return text  # 如果没有找到标签，直接返回原文本