import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from typing import Dict, List, Optional, Any
import pandas as pd
import json
from agents import Runner
from utils.utils import remove_think
from mcp.server.fastmcp import FastMCP
from custom_types.types import ReadDataParam
from agent_mcp.corr_agent import column_mapping_agent


mcp = FastMCP('CorrelationServer')

# 示例：中文风向转换函数
def get_chinese_wind_direction(degree: float) -> str:
    if pd.isna(degree):
        return None
    directions = ["北", "东北", "东", "东南", "南", "西南", "西", "西北"]
    idx = int(((degree + 22.5) % 360) / 45)
    return directions[idx]

# 示例：中文季节转换函数
def get_chinese_season(month: int) -> str:
    if pd.isna(month):
        return None
    if month in [3, 4, 5]:
        return "春"
    elif month in [6, 7, 8]:
        return "夏"
    elif month in [9, 10, 11]:
        return "秋"
    else:
        return "冬"

class Manager:
    def __init__(self) -> None:
        self.set_derived_fields()

    def set_derived_fields(self):
        self.derived_fields = {
            "时间": {
                "depends_on": ["时间"],
                "generate": lambda df, cols: df.__setitem__(cols[0], pd.to_datetime(df[cols[0]], errors="coerce"))
            },
            "季节": {
                "depends_on": ["时间"],
                "generate": lambda df, cols: df.__setitem__("季节", df[cols[0]].dt.month.map(get_chinese_season))
            },
            "风向方位": {
                "depends_on": ["风向"],
                "generate": lambda df, cols: df.__setitem__("风向方位", df[cols[0]].apply(get_chinese_wind_direction))
            }
        }
        
    
    async def _load_data(self, read_data_method, read_data_query) -> None:
        match read_data_method:
            case "SQL":
                return await self._load_data_from_sql(read_data_query)
            case "PANDAS":
                return await self._load_data_from_pandas(read_data_query)
            case _:
                raise ValueError(f"Invalid read_data_method: {read_data_method}. Expected 'SQL' or 'PANDAS'")

    async def _load_data_from_sql(self, read_data_query):
        raise NotImplementedError("SQL读取数据功能尚未实现")

    async def _load_data_from_pandas(self, read_data_query):
        from pathlib import Path
        
        def auto_parse_date(df):
            time_cols = ['时间', '日期', 'datetime', 'time', 'timestamp']
            for col in df.columns:
                if col in time_cols:
                    try:
                        df[col] = pd.to_datetime(df[col], errors='coerce')
                    except:
                        pass
            return df
        
        try:
            # 规范化路径处理
            file_path = Path(read_data_query).absolute()
            
            # 检查文件是否存在
            if not file_path.exists():
                raise FileNotFoundError(f"文件不存在: {file_path}")
                
            # 获取文件扩展名（自动推断文件类型）
            file_ext = file_path.suffix.lower()
            
            # 根据扩展名选择读取方法
            match file_ext:
                case ".csv":
                    return auto_parse_date(pd.read_csv(file_path))
                case ".xlsx" | ".xls":
                    return auto_parse_date(pd.read_excel(file_path))
                case ".parquet":
                    return pd.read_parquet(file_path)
                case ".json":
                    return pd.read_json(file_path)
                case ".feather":
                    return pd.read_feather(file_path)
                case ".h5" | ".hdf":
                    return pd.read_hdf(file_path)
                case _:
                    raise ValueError(f"不支持的文件类型: {file_ext}")
                    
        except Exception as e:
            raise ValueError(f"从pandas加载数据失败: {str(e)}")

    async def _get_columns_mapping(self, 
                                   exist_col: List[str],
                                   intent_col: List[str]
                                ) -> Dict[str, Optional[str]]:
        input = f'已有列名：{exist_col}\n用户意图：{intent_col}'
        result = await Runner.run(
            starting_agent=column_mapping_agent,
            input=input
        )
        column_map = json.loads(remove_think(result.final_output))
        return column_map

    async def run(self,
                  read_data_param: ReadDataParam,
                  filters: Optional[Dict[str, str]] = None, 
                  group_by: Optional[List[str]] = None, 
                  correlation_vars: Optional[List[str]] = None
                ) -> Any:
        # ----------读取数据------------#
        read_data_method = read_data_param.read_data_method
        read_data_query = read_data_param.read_data_query
        self.df = await self._load_data(read_data_method, read_data_query)

        print(f'成功读取数据！')
        # ----------映射列名------------ #
        all_user_keys = set()
        if filters:
            all_user_keys.update(filters.keys())
        if group_by:
            all_user_keys.update(group_by)
        if correlation_vars:
            all_user_keys.update(correlation_vars)
        all_user_keys = list(all_user_keys)
        column_map = await self._get_columns_mapping(self.df.columns.tolist(), all_user_keys)

        print(f'列名映射为：\n{column_map}')


        # ----------处理派生字段映射------------ #
        derived_user_keys = [k for k, v in column_map.items() if v is None]
        derived_mapped = {}
        if derived_user_keys:
            derived_mapped = await self._get_columns_mapping(list(self.derived_fields.keys()), derived_user_keys)
            print(f'需要派生的字段：\n{derived_mapped}')
            for k, v in derived_mapped.items():
                if v:
                    column_map[k] = v
        # ----------生成派生字段（仅生成用户需要的）---------- #
        triggered_derived = set()
        for derived_name, derived_info in self.derived_fields.items():
            # 如果不需要派生，则跳过
            if derived_name not in column_map.values():
                continue
            # 如果已经进行过派生计算，则跳过
            if derived_name in triggered_derived:
                continue
            # 对依赖字段进行查找
            resolved_deps = []
            for dep in derived_info["depends_on"]:
                mapped_col = column_map.get(dep, dep)
                if mapped_col not in self.df.columns:
                    print(f'【{mapped_col}】字段不存在，自动匹配中...')
                    depend_on_map = await self._get_columns_mapping(list(self.df.columns), [mapped_col])
                    if not depend_on_map[mapped_col]:
                        return {"error": f"字段【{dep}】映射后为【{mapped_col}】，但在数据中未找到"}
                    else:
                        print(f'【{mapped_col}】字段匹配成功！匹配字段为：{depend_on_map[mapped_col]}')
                        resolved_deps.append(depend_on_map[mapped_col])
                else:
                    resolved_deps.append(mapped_col)
            print(f'派生字段{derived_name}依赖字段为：\n{resolved_deps}')
            derived_info["generate"](self.df, resolved_deps)
            triggered_derived.add(derived_name)
        print(self.df.columns)
        # ----------替换过滤条件------------ #
        filters_mapped = {
            column_map[k]: v for k, v in (filters or {}).items()
        }
        print(f'过滤条件映射为：\n{filters_mapped}')

        # # ----------替换分组列名------------ #
        group_by_mapped = [column_map[g] for g in (group_by or [])]
        correlation_vars_mapped = [column_map[v] for v in (correlation_vars or [])]

        print(f'分组列名映射为：\n{group_by_mapped}')
        print(f'相关性变量映射为：\n{correlation_vars_mapped}')

        if len(correlation_vars_mapped) != 2:
            return {"error": "无法识别两个用于计算相关性的变量，请检查变量名称"}

        var1, var2 = correlation_vars_mapped

        # # ----------过滤数据-------------- #
        for k, v in filters_mapped.items():
            try:
                self.df = self.df[self.df[k] == v]
            except:
                return {"error": f"无法识别过滤条件【{k}】，请检查变量名称:【{v}】"}

        # # ----------计算相关性------------ #
        result = {}
        print(f'开始计算相关性...')
        if group_by_mapped:
            grouped = self.df.groupby(group_by_mapped)
            for keys, group in grouped:
                sub = group[[var1, var2]].dropna()
                key_str = " - ".join(str(k) for k in keys) if isinstance(keys, tuple) else str(keys)
                if sub.shape[0] < 3:
                    result[key_str] = -100
                else:
                    corr = sub[var1].corr(sub[var2])
                    result[key_str] = round(corr, 3) if pd.notna(corr) else None
        else:
            sub = self.df[[var1, var2]].dropna()
            if sub.shape[0] < 3:
                result[f"corr_{var1}_{var2}"] = None
            else:
                corr = sub[var1].corr(sub[var2])
                result[f"corr_{var1}_{var2}"] = round(corr, 3) if pd.notna(corr) else None
        # ----------构造Markdown表格返回-------------- #
        if group_by_mapped:
            md = "| 分组 | 相关性 |\n|---|---|\n"
            for key, value in result.items():
                corr_value = "数据不足" if value == -100 else value
                md += f"| {key} | {corr_value} |\n"
        else:
            title = list(result.keys())[0]
            value = result[title]
            corr_value = "数据不足" if value is None else value
            md = f"| 变量组合 | 相关性 |\n|---|---|\n| {title} | {corr_value} |\n"

        return {"result": result, "markdown": md}


@mcp.tool()
async def correlation_analysis(
    read_data_param: ReadDataParam,
    filters: Optional[Dict[str, str]] = None, 
    group_by: Optional[List[str]] = None, 
    correlation_vars: Optional[List[str]] = None
) -> Dict[str, Optional[float]]:
    """
    获取数据，根据条件计算相关性。
    :param read_data_method: 读取数据的参数
    :param filters: 需要过滤的条件, 格式为：{列名: 值}
    :param group_by: 需要分组的列, 格式为：[列名1, 列名2, ...]
    :param correlation_vars: 需要计算相关性的列, 需要两个变量, 格式为：[列名1, 列名2]
    """
    manager = Manager()
    result = await manager.run(
        read_data_param=read_data_param,
        filters=filters,
        group_by=group_by,
        correlation_vars=correlation_vars
    )
    return result


if __name__ == '__main__':
    mcp.run(transport='sse')
    





