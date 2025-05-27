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
from config import get_sort_order, custom_sort_key


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
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"尝试第 {attempt + 1} 次列名映射...")
                result = await Runner.run(
                    starting_agent=column_mapping_agent,
                    input=input
                )
                
                # 获取原始输出
                raw_output = result.final_output
                # print(f"原始输出: {raw_output}")
                
                # 移除思考标签
                cleaned_output = remove_think(raw_output)
                print(f"清理后输出: {cleaned_output}")
                
                # 尝试解析JSON
                try:
                    column_map = json.loads(cleaned_output)
                    print(f"JSON解析成功！映射结果: {column_map}")
                    return column_map
                except json.JSONDecodeError as e:
                    print(f"JSON解析错误 (尝试 {attempt + 1}/{max_retries}): {e}")
                    print(f"错误位置: 行 {e.lineno}, 列 {e.colno}")
                    print(f"尝试解析的内容: {repr(cleaned_output)}")
                    
                    # 尝试修复常见的JSON格式问题
                    try:
                        # 移除可能的前后空白和换行
                        cleaned_output = cleaned_output.strip()
                        
                        # 如果输出不是以{开头，尝试提取JSON部分
                        if not cleaned_output.startswith('{'):
                            # 查找第一个{和最后一个}
                            start_idx = cleaned_output.find('{')
                            end_idx = cleaned_output.rfind('}')
                            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                                cleaned_output = cleaned_output[start_idx:end_idx+1]
                                print(f"提取的JSON部分: {cleaned_output}")
                        
                        column_map = json.loads(cleaned_output)
                        print(f"修复后JSON解析成功！映射结果: {column_map}")
                        return column_map
                    except json.JSONDecodeError as e2:
                        print(f"修复尝试失败: {e2}")
                        
                        # 如果是最后一次尝试，抛出错误
                        if attempt == max_retries - 1:
                            raise ValueError(f"经过 {max_retries} 次尝试，仍无法获得有效的JSON格式输出。最后一次输出: {repr(cleaned_output)}")
                        else:
                            print(f"将进行第 {attempt + 2} 次重试...")
                            continue
                            
            except Exception as e:
                if attempt == max_retries - 1:
                    raise ValueError(f"列名映射失败，经过 {max_retries} 次尝试后仍然出错: {str(e)}")
                else:
                    print(f"第 {attempt + 1} 次尝试出错: {e}，将重试...")
                    continue

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
        
        # 数据清理：确保相关性变量是数值型
        for var in [var1, var2]:
            if var in self.df.columns:
                # 尝试转换为数值型，无法转换的设为NaN
                self.df[var] = pd.to_numeric(self.df[var], errors='coerce')
        
        if group_by_mapped:
            grouped = self.df.groupby(group_by_mapped)
            for keys, group in grouped:
                sub = group[[var1, var2]].dropna()
                key_str = " - ".join(str(k) for k in keys) if isinstance(keys, tuple) else str(keys)
                if sub.shape[0] < 15:
                    result[key_str] = -100
                else:
                    corr = sub[var1].corr(sub[var2])
                    result[key_str] = round(corr, 3) if pd.notna(corr) else None
        else:
            sub = self.df[[var1, var2]].dropna()
            if sub.shape[0] < 15:
                result[f"corr_{var1}_{var2}"] = None
            else:
                corr = sub[var1].corr(sub[var2])
                result[f"corr_{var1}_{var2}"] = round(corr, 3) if pd.notna(corr) else None
        # ----------构造Markdown表格返回-------------- #
        md = self._generate_correlation_table(result, group_by_mapped, var1, var2)
        
        return md

    def _generate_correlation_table(self, result: Dict, group_by_mapped: List[str], var1: str, var2: str) -> str:
        """
        根据分组维度生成不同格式的相关性表格
        """
        if not group_by_mapped:
            # 无分组：简单的单行表格
            title = list(result.keys())[0]
            value = result[title]
            corr_value = "数据不足" if value is None or value == -100 else value
            return f"| 变量组合 | 相关性 |\n|---|---|\n| {var1} vs {var2} | {corr_value} |\n"
        
        elif len(group_by_mapped) == 1:
            # 一维分组：简单的两列表格
            md = f"| {group_by_mapped[0]} | 相关性 |\n|---|---|\n"
            
            # 获取排序规则
            column_name = group_by_mapped[0]
            keys = list(result.keys())
            sort_order = get_sort_order(column_name, keys)
            
            # 应用排序
            if sort_order:
                keys = sorted(keys, key=lambda x: custom_sort_key(x, sort_order))
            else:
                keys = sorted(keys)  # 默认字母排序
            
            for key in keys:
                value = result[key]
                corr_value = "数据不足" if value == -100 else value
                md += f"| {key} | {corr_value} |\n"
            return md
        
        elif len(group_by_mapped) == 2:
            # 二维分组：生成交叉表格
            return self._generate_2d_table(result, group_by_mapped)
        
        else:
            # 三维及以上：生成层次化表格
            return self._generate_hierarchical_table(result, group_by_mapped)

    def _generate_2d_table(self, result: Dict, group_by_mapped: List[str]) -> str:
        """
        生成二维交叉表格
        """
        # 解析结果中的分组键
        rows = set()
        cols = set()
        data_matrix = {}
        
        for key, value in result.items():
            parts = key.split(" - ")
            if len(parts) >= 2:
                row_val, col_val = parts[0], parts[1]
                rows.add(row_val)
                cols.add(col_val)
                data_matrix[(row_val, col_val)] = value
        
        # 应用排序规则
        row_column_name = group_by_mapped[0]
        col_column_name = group_by_mapped[1]
        
        # 获取行排序规则
        row_sort_order = get_sort_order(row_column_name, list(rows))
        if row_sort_order:
            rows = sorted(list(rows), key=lambda x: custom_sort_key(x, row_sort_order))
        else:
            rows = sorted(list(rows))
        
        # 获取列排序规则
        col_sort_order = get_sort_order(col_column_name, list(cols))
        if col_sort_order:
            cols = sorted(list(cols), key=lambda x: custom_sort_key(x, col_sort_order))
        else:
            cols = sorted(list(cols))
        
        # 构建表格头部
        md = f"| {group_by_mapped[0]} \\ {group_by_mapped[1]} |"
        for col in cols:
            md += f" {col} |"
        md += "\n|"
        for _ in range(len(cols) + 1):
            md += "---|"
        md += "\n"
        
        # 构建表格内容
        for row in rows:
            md += f"| {row} |"
            for col in cols:
                value = data_matrix.get((row, col), None)
                if value is None:
                    corr_value = "无数据"
                elif value == -100:
                    corr_value = "数据不足"
                else:
                    corr_value = str(value)
                md += f" {corr_value} |"
            md += "\n"
        
        return md

    def _generate_hierarchical_table(self, result: Dict, group_by_mapped: List[str]) -> str:
        """
        生成层次化表格（适用于三维及以上分组）
        """
        # 构建层次化结构
        hierarchy = {}
        for key, value in result.items():
            parts = key.split(" - ")
            current = hierarchy
            
            # 构建层次结构
            for i, part in enumerate(parts[:-1]):
                if part not in current:
                    current[part] = {}
                current = current[part]
            
            # 最后一层存储相关性值
            last_part = parts[-1] if parts else key
            current[last_part] = value
        
        # 生成表格
        md = "| " + " | ".join(group_by_mapped) + " | 相关性 |\n"
        md += "|" + "---|" * (len(group_by_mapped) + 1) + "\n"
        
        def traverse_hierarchy(current_dict, path=[], level=0):
            # 获取当前层级的排序规则
            if level < len(group_by_mapped):
                column_name = group_by_mapped[level]
                keys = list(current_dict.keys())
                sort_order = get_sort_order(column_name, keys)
                
                if sort_order:
                    keys = sorted(keys, key=lambda x: custom_sort_key(x, sort_order))
                else:
                    keys = sorted(keys)
            else:
                keys = sorted(current_dict.keys())
            
            for key in keys:
                value = current_dict[key]
                current_path = path + [str(key)]
                if isinstance(value, dict):
                    traverse_hierarchy(value, current_path, level + 1)
                else:
                    # 叶子节点，输出相关性值
                    corr_value = "数据不足" if value == -100 else value
                    md_row = "| " + " | ".join(current_path) + f" | {corr_value} |\n"
                    nonlocal md
                    md += md_row
        
        traverse_hierarchy(hierarchy)
        return md


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
    





