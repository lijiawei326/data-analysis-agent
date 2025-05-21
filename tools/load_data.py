from agents import function_tool, RunContextWrapper
import pandas as pd


# @function_tool(name_override="数据读取")
@function_tool()
async def load_data(
    context: RunContextWrapper,    # 隐式参数： 不写进Json Schema
    file_path: str                 # 显式参数： 写进Json Schema
):
    """
    读取指定路径的数据
    :param file_path: 文件路径
    """
    df = pd.read_csv(file_path)
    context.context.data.data = df
    return f'已从{file_path}读取数据, 保存至缓存'