from agents import function_tool, RunContextWrapper
import pandas as pd
import numpy as np


# @function_tool(name_override="数据清洗")
@function_tool()
async def clean_data(context: RunContextWrapper):
    """
    当需要对数据进行清洗时使用该工具, 不需要输入参数。
    """

    if context.context.data.data is None:
        return "未读取数据，请重新读取数据后清洗"
    else:
        print('数据已提取')
    if context.context.data.washed:
        return "数据已完成清洗，不需要重复清洗"
    
    try:
        context.context.data.washed = True
    except Exception as e:
        return f"数据清洗失败，错误信息：{e}"

    import time
    time.sleep(3)
    return "数据已清洗"

# @function_tool
# async def get_data_types(context: RunContextWrapper):
#     """
#     获取数据各字段的数据类型
#     """
#     df = context.context.data.data
#     types = df.dtypes.astype(str).to_dict()
#     return types

# @function_tool
# async def handle_missing_values(context: RunContextWrapper, method: str = "drop", fill_value: float = None):
#     """
#     缺失值处理
#     :param method: 处理方式，'drop'表示删除，'fill'表示填充
#     :param fill_value: 填充值（当method为'fill'时有效）
#     """
#     df = context.context.data.data
#     if method == "drop":
#         df = df.dropna()
#     elif method == "fill" and fill_value is not None:
#         df = df.fillna(fill_value)
#     context.context.data.data = df
#     return f"缺失值已处理，方式：{method}"

# @function_tool
# async def detect_outliers(context: RunContextWrapper, z_thresh: float = 3.0):
#     """
#     使用Z-score方法检测数值型字段的异常值
#     :param z_thresh: Z-score阈值，超过该值视为异常
#     """
#     df = context.context.data.data
#     numeric_cols = df.select_dtypes(include=[np.number]).columns
#     outlier_info = {}
#     for col in numeric_cols:
#         col_zscore = ((df[col] - df[col].mean()) / df[col].std()).abs()
#         outlier_info[col] = df[col_zscore > z_thresh].index.tolist()
#     return outlier_info

# @function_tool
# async def standardize_data(context: RunContextWrapper):
#     """
#     对数值型字段进行标准化（均值为0，方差为1）
#     """
#     df = context.context.data.data
#     numeric_cols = df.select_dtypes(include=[np.number]).columns
#     df[numeric_cols] = (df[numeric_cols] - df[numeric_cols].mean()) / df[numeric_cols].std()
#     context.context.data.data = df
#     return "数值型字段已标准化"

# @function_tool
# async def auto_convert_dates(context: RunContextWrapper):
#     """
#     自动检测并转换日期字段为datetime类型
#     """
#     df = context.context.data.data
#     for col in df.columns:
#         if df[col].dtype == object:
#             try:
#                 df[col] = pd.to_datetime(df[col], errors='raise')
#             except Exception:
#                 continue
#     context.context.data.data = df
#     return "已自动转换日期字段" 