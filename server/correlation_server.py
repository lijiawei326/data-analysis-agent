"""
相关性分析服务器
支持两变量和多变量相关性分析，包括分组分析和多种计算方法
"""
# TODO: 1. 数据缓存
# TODO: 2. 派生功能外置


import sys
import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass
from enum import Enum
import asyncio
import json
import logging
from functools import lru_cache
import pandas as pd
import numpy as np
from scipy.stats import pearsonr, spearmanr, kendalltau

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))
sys.path.append(str(PROJECT_ROOT / 'frontend'))

from logger_config import create_logger
from agents import Runner
from utils.utils import remove_think
from mcp.server.fastmcp import FastMCP
from custom_types.types import ReadDataParam
from agent_mcp.corr_agent import column_mapping_agent
from config import get_sort_order, custom_sort_key

@dataclass
class CorrelationConfig:
    """相关性分析配置类"""
    min_sample_size: int = 15
    data_insufficient_flag: int = -100
    max_retries: int = 3
    correlation_precision: int = 3
    max_file_size_mb: int = 100
    supported_file_types: List[str] = None
    
    def __post_init__(self):
        if self.supported_file_types is None:
            self.supported_file_types = ['.csv', '.xlsx', '.xls', '.parquet', '.json', '.feather', '.h5', '.hdf']

class CorrelationMethod(Enum):
    """相关性计算方法枚举"""
    PEARSON = "pearson"
    SPEARMAN = "spearman"
    KENDALL = "kendall"

class CorrelationAnalysisError(Exception):
    """相关性分析基础异常"""
    pass

class DataLoadError(CorrelationAnalysisError):
    """数据加载异常"""
    pass

class ColumnMappingError(CorrelationAnalysisError):
    """列名映射异常"""
    pass

class InsufficientDataError(CorrelationAnalysisError):
    """数据不足异常"""
    pass

class DataLoader:
    """数据加载器类"""
    
    def __init__(self, config: CorrelationConfig, logger: logging.Logger):
        self.config = config
        self.logger = logger
    
    async def load_data(self, read_data_method: str, read_data_query: str) -> pd.DataFrame:
        """统一数据加载入口"""
        method_map = {
            "SQL": self._load_from_sql,
            "PANDAS": self._load_from_pandas
        }
        
        if read_data_method not in method_map:
            raise DataLoadError(f"不支持的数据加载方法: {read_data_method}. 支持的方法: {list(method_map.keys())}")
        
        try:
            return await method_map[read_data_method](read_data_query)
        except Exception as e:
            self.logger.error(f"数据加载失败: {e}")
            raise DataLoadError(f"数据加载失败: {str(e)}") from e
    
    async def _load_from_sql(self, query: str) -> pd.DataFrame:
        """SQL数据加载"""
        raise NotImplementedError("SQL数据加载功能待实现")
    
    async def _load_from_pandas(self, file_path: str) -> pd.DataFrame:
        """从文件加载数据"""
        try:
            file_path_obj = Path(file_path).resolve()
            self._validate_file_path(file_path_obj)
            
            file_size_mb = file_path_obj.stat().st_size / (1024 * 1024)
            if file_size_mb > self.config.max_file_size_mb:
                raise DataLoadError(f"文件过大: {file_size_mb:.1f}MB，超过限制 {self.config.max_file_size_mb}MB")
            
            df = self._load_by_file_type(file_path_obj)
            df = self._auto_parse_datetime(df)
            self._validate_dataframe(df)
            
            self.logger.info(f"成功加载数据: {df.shape[0]}行 x {df.shape[1]}列")
            return df
            
        except Exception as e:
            raise DataLoadError(f"文件加载失败: {str(e)}") from e
    
    def _validate_file_path(self, file_path: Path) -> None:
        """文件路径安全验证"""
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        if not file_path.is_file():
            raise ValueError(f"路径不是文件: {file_path}")
        
        if file_path.suffix.lower() not in self.config.supported_file_types:
            raise ValueError(f"不支持的文件类型: {file_path.suffix}. 支持的类型: {self.config.supported_file_types}")
    
    def _load_by_file_type(self, file_path: Path) -> pd.DataFrame:
        """根据文件类型加载数据"""
        file_ext = file_path.suffix.lower()
        
        loader_map = {
            '.csv': lambda: pd.read_csv(file_path),
            '.xlsx': lambda: pd.read_excel(file_path),
            '.xls': lambda: pd.read_excel(file_path),
            '.parquet': lambda: pd.read_parquet(file_path),
            '.json': lambda: pd.read_json(file_path),
            '.feather': lambda: pd.read_feather(file_path),
            '.h5': lambda: pd.read_hdf(file_path),
            '.hdf': lambda: pd.read_hdf(file_path)
        }
        
        if file_ext not in loader_map:
            raise ValueError(f"不支持的文件类型: {file_ext}")
        
        return loader_map[file_ext]()
    
    def _auto_parse_datetime(self, df: pd.DataFrame) -> pd.DataFrame:
        """自动解析时间列"""
        time_patterns = ['时间', '日期', 'datetime', 'time', 'timestamp', 'date', '创建时间', '更新时间']
        
        for col in df.columns:
            if any(pattern in col.lower() for pattern in time_patterns):
                try:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
                    self.logger.debug(f"成功解析时间列: {col}")
                except Exception as e:
                    self.logger.warning(f"时间列解析失败 {col}: {e}")
        
        return df
    
    def _validate_dataframe(self, df: pd.DataFrame) -> None:
        """数据质量验证"""
        if df.empty:
            raise DataLoadError("加载的数据为空")
        
        if df.shape[0] < self.config.min_sample_size:
            self.logger.warning(f"数据行数较少: {df.shape[0]}行，可能影响分析结果")

class ColumnMapper:
    """列名映射器类"""
    
    def __init__(self, config: CorrelationConfig, logger: logging.Logger):
        self.config = config
        self.logger = logger
        self._mapping_cache = {}
    
    @lru_cache(maxsize=128)
    async def get_column_mapping(self, 
                                exist_cols: Tuple[str, ...], 
                                intent_cols: Tuple[str, ...]) -> Dict[str, Optional[str]]:
        """获取列名映射"""
        cache_key = (exist_cols, intent_cols)
        if cache_key in self._mapping_cache:
            self.logger.debug("使用缓存的列名映射结果")
            return self._mapping_cache[cache_key]
        
        input_text = f'已有列名：{list(exist_cols)}\n用户意图：{list(intent_cols)}'
        
        for attempt in range(self.config.max_retries):
            try:
                self.logger.info(f"尝试第 {attempt + 1} 次列名映射...")
                
                result = await Runner.run(
                    starting_agent=column_mapping_agent,
                    input=input_text
                )
                
                column_map = self._parse_mapping_result(result.final_output)
                self._mapping_cache[cache_key] = column_map
                
                self.logger.info(f"列名映射成功: {column_map}")
                return column_map
                
            except json.JSONDecodeError as e:
                self.logger.error(f"JSON解析错误 (尝试 {attempt + 1}/{self.config.max_retries}): {e}")
                if attempt == self.config.max_retries - 1:
                    raise ColumnMappingError(f"经过 {self.config.max_retries} 次尝试，仍无法获得有效的JSON格式输出") from e
            except Exception as e:
                self.logger.error(f"列名映射错误 (尝试 {attempt + 1}/{self.config.max_retries}): {e}")
                if attempt == self.config.max_retries - 1:
                    raise ColumnMappingError(f"列名映射失败: {str(e)}") from e
        
        raise ColumnMappingError("列名映射失败：超过最大重试次数")
    
    def _parse_mapping_result(self, raw_output: str) -> Dict[str, Optional[str]]:
        """解析映射结果"""
        cleaned_output = remove_think(raw_output).strip()
        
        try:
            return json.loads(cleaned_output)
        except json.JSONDecodeError:
            pass
        
        start_idx = cleaned_output.find('{')
        end_idx = cleaned_output.rfind('}')
        
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            json_part = cleaned_output[start_idx:end_idx+1]
            try:
                return json.loads(json_part)
            except json.JSONDecodeError:
                pass
        
        raise json.JSONDecodeError(f"无法解析JSON: {cleaned_output}", cleaned_output, 0)

class DerivedFieldGenerator:
    """派生字段生成器类"""
    
    def __init__(self, config: CorrelationConfig, logger: logging.Logger):
        self.config = config
        self.logger = logger
        self.derived_fields = self._initialize_derived_fields()
    
    def _initialize_derived_fields(self) -> Dict[str, Dict[str, Any]]:
        """初始化派生字段定义"""
        return {
            "时间": {
                "depends_on": ["时间"],
                "generate": self._generate_datetime_field,
                "description": "时间字段标准化"
            },
            "季节": {
                "depends_on": ["时间"],
                "generate": self._generate_season_field,
                "description": "根据时间生成季节字段"
            },
            "风向方位": {
                "depends_on": ["风向"],
                "generate": self._generate_wind_direction_field,
                "description": "将风向角度转换为中文方位"
            }
        }
    
    async def generate_required_fields(self, 
                                     df: pd.DataFrame, 
                                     column_map: Dict[str, Optional[str]],
                                     column_mapper: ColumnMapper) -> pd.DataFrame:
        """生成所需的派生字段"""
        df_copy = df.copy()
        generated_fields = set()
        
        # 检查哪些派生字段需要生成
        required_derived_fields = []
        for user_key, mapped_value in column_map.items():
            if mapped_value in self.derived_fields:
                required_derived_fields.append(mapped_value)
        
        self.logger.info(f"需要生成的派生字段: {required_derived_fields}")
        
        for derived_name in required_derived_fields:
            if derived_name in generated_fields:
                continue
                
            derived_info = self.derived_fields[derived_name]
            
            try:
                resolved_deps = await self._resolve_dependencies(
                    df_copy, derived_info["depends_on"], column_map, column_mapper
                )
                
                derived_info["generate"](df_copy, resolved_deps)
                generated_fields.add(derived_name)
                
                self.logger.info(f"成功生成派生字段: {derived_name}")
                
            except Exception as e:
                self.logger.error(f"生成派生字段失败 {derived_name}: {e}")
                raise
        
        return df_copy
    
    async def _resolve_dependencies(self, 
                                  df: pd.DataFrame, 
                                  dependencies: List[str],
                                  column_map: Dict[str, Optional[str]],
                                  column_mapper: ColumnMapper) -> List[str]:
        """解析派生字段依赖"""
        resolved_deps = []
        
        for dep in dependencies:
            # 首先检查column_map中是否有直接映射
            mapped_col = None
            for user_key, mapped_value in column_map.items():
                if user_key == dep:
                    mapped_col = mapped_value
                    break
            
            # 如果没有直接映射，尝试在数据框列中查找
            if not mapped_col:
                if dep in df.columns:
                    mapped_col = dep
                else:
                    # 尝试自动匹配
                    self.logger.info(f"字段 {dep} 不存在，尝试自动匹配...")
                    depend_map = await column_mapper.get_column_mapping(
                        tuple(df.columns), (dep,)
                    )
                    
                    mapped_col = depend_map.get(dep)
                    if not mapped_col:
                        raise ColumnMappingError(f"无法找到依赖字段: {dep}")
            
            if mapped_col not in df.columns:
                raise ColumnMappingError(f"依赖字段不存在于数据中: {dep} -> {mapped_col}")
            
            resolved_deps.append(mapped_col)
            self.logger.info(f"依赖字段解析: {dep} -> {mapped_col}")
        
        return resolved_deps
    
    def _generate_datetime_field(self, df: pd.DataFrame, cols: List[str]) -> None:
        """生成标准化时间字段"""
        if cols:
            df[cols[0]] = pd.to_datetime(df[cols[0]], errors="coerce")
    
    def _generate_season_field(self, df: pd.DataFrame, cols: List[str]) -> None:
        """生成季节字段"""
        if cols:
            df["季节"] = df[cols[0]].dt.month.map(self._get_chinese_season)
    
    def _generate_wind_direction_field(self, df: pd.DataFrame, cols: List[str]) -> None:
        """生成风向方位字段"""
        if cols:
            df["风向方位"] = df[cols[0]].apply(self._get_chinese_wind_direction)
    
    @staticmethod
    def _get_chinese_season(month: int) -> Optional[str]:
        """季节转换函数"""
        if pd.isna(month) or not isinstance(month, (int, float)):
            return None
        
        month = int(month)
        season_map = {
            (3, 4, 5): "春",
            (6, 7, 8): "夏", 
            (9, 10, 11): "秋",
            (12, 1, 2): "冬"
        }
        
        for months, season in season_map.items():
            if month in months:
                return season
        return None
    
    @staticmethod
    def _get_chinese_wind_direction(degree: float) -> Optional[str]:
        """风向转换函数"""
        if pd.isna(degree) or not isinstance(degree, (int, float)):
            return None
        
        degree = degree % 360
        directions = ["北", "东北", "东", "东南", "南", "西南", "西", "西北"]
        idx = int((degree + 22.5) / 45) % 8
        return directions[idx] 

class CorrelationCalculator:
    """相关性计算器类"""
    
    def __init__(self, config: CorrelationConfig, logger: logging.Logger):
        self.config = config
        self.logger = logger
    
    def calculate_correlation(self, 
                            df: pd.DataFrame,
                            var1: str, 
                            var2: str,
                            group_by: Optional[List[str]] = None,
                            method: CorrelationMethod = CorrelationMethod.PEARSON) -> Dict[str, Union[float, None, int]]:
        """计算两变量相关性"""
        df_clean = self._prepare_data_for_correlation(df, var1, var2, group_by)
        
        if group_by:
            return self._calculate_grouped_correlation(df_clean, var1, var2, group_by, method)
        else:
            return self._calculate_simple_correlation(df_clean, var1, var2, method)
    
    def calculate_correlation_matrix(self, 
                                   df: pd.DataFrame,
                                   variables: List[str],
                                   group_by: Optional[List[str]] = None,
                                   method: CorrelationMethod = CorrelationMethod.PEARSON) -> Dict[str, Any]:
        """计算多变量相关性矩阵"""
        df_clean = self._prepare_data_for_matrix_correlation(df, variables, group_by)
        
        result = {
            "matrix_type": "correlation_matrix",
            "variables": variables,
            "method": method.value
        }
        
        if group_by:
            result["groups"] = self._calculate_grouped_correlation_matrix(df_clean, variables, group_by, method)
        else:
            result["matrix"] = self._calculate_simple_correlation_matrix(df_clean, variables, method)
        
        return result
    
    def _prepare_data_for_matrix_correlation(self, df: pd.DataFrame, variables: List[str], group_by: Optional[List[str]] = None) -> pd.DataFrame:
        """为多变量相关性分析准备数据"""
        df_copy = df.copy()
        
        # 数值化相关性变量
        for var in variables:
            if var in df_copy.columns:
                df_copy[var] = pd.to_numeric(df_copy[var], errors='coerce')
        
        # 确定需要保留的列
        columns_to_keep = variables.copy()
        if group_by:
            columns_to_keep.extend(group_by)
        
        # 只保留需要的列并删除缺失值
        df_clean = df_copy[columns_to_keep].dropna(subset=variables)
        
        self.logger.debug(f"矩阵数据预处理完成: {df_clean.shape[0]}行有效数据，{len(variables)}个变量，保留列: {columns_to_keep}")
        return df_clean
    
    def _calculate_simple_correlation_matrix(self, 
                                           df: pd.DataFrame, 
                                           variables: List[str],
                                           method: CorrelationMethod) -> Dict[Tuple[str, str], Union[float, None]]:
        """计算简单相关性矩阵（无分组）"""
        if df.shape[0] < self.config.min_sample_size:
            self.logger.warning(f"数据量不足: {df.shape[0]}行，小于最小样本数 {self.config.min_sample_size}")
            matrix = {}
            for i, var1 in enumerate(variables):
                for j, var2 in enumerate(variables):
                    if i == j:
                        matrix[(var1, var2)] = 1.0
                    else:
                        matrix[(var1, var2)] = None
            return matrix
        
        try:
            if method == CorrelationMethod.PEARSON:
                corr_matrix = df.corr(method='pearson')
            elif method == CorrelationMethod.SPEARMAN:
                corr_matrix = df.corr(method='spearman')
            elif method == CorrelationMethod.KENDALL:
                corr_matrix = df.corr(method='kendall')
            else:
                corr_matrix = df.corr(method='pearson')
            
            matrix = {}
            for var1 in variables:
                for var2 in variables:
                    if var1 in corr_matrix.index and var2 in corr_matrix.columns:
                        corr_value = corr_matrix.loc[var1, var2]
                        if pd.isna(corr_value):
                            matrix[(var1, var2)] = None
                        else:
                            matrix[(var1, var2)] = round(corr_value, self.config.correlation_precision)
                    else:
                        matrix[(var1, var2)] = None
            
            return matrix
            
        except Exception as e:
            self.logger.error(f"相关性矩阵计算失败: {e}")
            matrix = {}
            for var1 in variables:
                for var2 in variables:
                    matrix[(var1, var2)] = None
            return matrix
    
    def _calculate_grouped_correlation_matrix(self, 
                                            df: pd.DataFrame, 
                                            variables: List[str],
                                            group_by: List[str],
                                            method: CorrelationMethod) -> Dict[str, Dict[Tuple[str, str], Union[float, None]]]:
        """计算分组相关性矩阵"""
        result = {}
        
        try:
            grouped = df.groupby(group_by)
            
            for keys, group in grouped:
                key_str = " - ".join(str(k) for k in keys) if isinstance(keys, tuple) else str(keys)
                
                original_size = group.shape[0]
                group_clean = group[variables].dropna()
                clean_size = group_clean.shape[0]
                
                self.logger.debug(f"分组 {key_str}: 原始数据 {original_size}行, 清洗后 {clean_size}行")
                
                if clean_size < self.config.min_sample_size:
                    self.logger.warning(f"分组 {key_str} 数据不足: 清洗后{clean_size}行 (原始{original_size}行, 最小要求{self.config.min_sample_size}行)")
                    matrix = {}
                    for var1 in variables:
                        for var2 in variables:
                            if var1 == var2:
                                matrix[(var1, var2)] = 1.0
                            else:
                                matrix[(var1, var2)] = self.config.data_insufficient_flag
                    result[key_str] = matrix
                else:
                    try:
                        if method == CorrelationMethod.PEARSON:
                            corr_matrix = group_clean.corr(method='pearson')
                        elif method == CorrelationMethod.SPEARMAN:
                            corr_matrix = group_clean.corr(method='spearman')
                        elif method == CorrelationMethod.KENDALL:
                            corr_matrix = group_clean.corr(method='kendall')
                        else:
                            corr_matrix = group_clean.corr(method='pearson')
                        
                        matrix = {}
                        for var1 in variables:
                            for var2 in variables:
                                if var1 in corr_matrix.index and var2 in corr_matrix.columns:
                                    corr_value = corr_matrix.loc[var1, var2]
                                    if pd.isna(corr_value):
                                        matrix[(var1, var2)] = None
                                    else:
                                        matrix[(var1, var2)] = round(corr_value, self.config.correlation_precision)
                                else:
                                    matrix[(var1, var2)] = None
                        
                        result[key_str] = matrix
                        
                    except Exception as e:
                        self.logger.warning(f"分组 {key_str} 相关性矩阵计算失败: {e}")
                        matrix = {}
                        for var1 in variables:
                            for var2 in variables:
                                matrix[(var1, var2)] = None
                        result[key_str] = matrix
                        
        except Exception as e:
            self.logger.error(f"分组相关性矩阵计算失败: {e}")
            raise
        
        return result
    
    def _prepare_data_for_correlation(self, df: pd.DataFrame, var1: str, var2: str, group_by: Optional[List[str]] = None) -> pd.DataFrame:
        """数据预处理，确保数据适合相关性计算"""
        df_copy = df.copy()
        
        # 数值化相关性变量
        for var in [var1, var2]:
            if var in df_copy.columns:
                df_copy[var] = pd.to_numeric(df_copy[var], errors='coerce')
        
        # 确定需要保留的列
        columns_to_keep = [var1, var2]
        if group_by:
            columns_to_keep.extend(group_by)
        
        # 只保留需要的列并删除缺失值
        df_clean = df_copy[columns_to_keep].dropna(subset=[var1, var2])
        
        self.logger.debug(f"数据预处理完成: {df_clean.shape[0]}行有效数据，保留列: {columns_to_keep}")
        return df_clean
    
    def _calculate_simple_correlation(self, 
                                    df: pd.DataFrame, 
                                    var1: str, 
                                    var2: str,
                                    method: CorrelationMethod) -> Dict[str, Union[float, None]]:
        """计算简单相关性"""
        if df.shape[0] < self.config.min_sample_size:
            return {f"corr_{var1}_{var2}": None}
        
        try:
            corr_value = self._compute_correlation(df[var1], df[var2], method)
            return {f"corr_{var1}_{var2}": round(corr_value, self.config.correlation_precision)}
        except Exception as e:
            self.logger.error(f"相关性计算失败: {e}")
            return {f"corr_{var1}_{var2}": None}
    
    def _calculate_grouped_correlation(self, 
                                     df: pd.DataFrame, 
                                     var1: str, 
                                     var2: str,
                                     group_by: List[str],
                                     method: CorrelationMethod) -> Dict[str, Union[float, None, int]]:
        """计算分组相关性"""
        result = {}
        
        try:
            self.logger.info(f"开始分组相关性计算: var1={var1}, var2={var2}, group_by={group_by}")
            self.logger.info(f"数据框列名: {list(df.columns)}")
            self.logger.info(f"数据框形状: {df.shape}")
            
            # 检查所有需要的列是否存在
            missing_cols = []
            for col in [var1, var2] + group_by:
                if col not in df.columns:
                    missing_cols.append(col)
            
            if missing_cols:
                raise ValueError(f"以下列在数据框中不存在: {missing_cols}")
            
            grouped = df.groupby(group_by)
            self.logger.info(f"分组成功，共有 {len(grouped)} 个分组")
            
            for keys, group in grouped:
                key_str = " - ".join(str(k) for k in keys) if isinstance(keys, tuple) else str(keys)
                original_size = group.shape[0]
                group_clean = group[[var1, var2]].dropna()
                clean_size = group_clean.shape[0]
                
                self.logger.debug(f"分组 {key_str}: 原始数据 {original_size}行, 清洗后 {clean_size}行")
                
                if clean_size < self.config.min_sample_size:
                    result[key_str] = self.config.data_insufficient_flag
                    self.logger.info(f"分组 {key_str} 数据不足: 清洗后{clean_size}行 (原始{original_size}行, 最小要求{self.config.min_sample_size}行)")
                else:
                    try:
                        corr_value = self._compute_correlation(group_clean[var1], group_clean[var2], method)
                        result[key_str] = round(corr_value, self.config.correlation_precision)
                        self.logger.info(f"分组 {key_str} 相关性: {result[key_str]} (基于{clean_size}行数据)")
                    except Exception as e:
                        self.logger.warning(f"分组 {key_str} 相关性计算失败: {e}")
                        result[key_str] = None
                        
        except Exception as e:
            self.logger.error(f"分组相关性计算失败: {e}")
            self.logger.error(f"错误详情: var1={var1}, var2={var2}, group_by={group_by}")
            raise
        
        return result
    
    def _compute_correlation(self, 
                           series1: pd.Series, 
                           series2: pd.Series, 
                           method: CorrelationMethod) -> float:
        """支持多种相关性计算方法"""
        if method == CorrelationMethod.PEARSON:
            corr, _ = pearsonr(series1, series2)
        elif method == CorrelationMethod.SPEARMAN:
            corr, _ = spearmanr(series1, series2)
        elif method == CorrelationMethod.KENDALL:
            corr, _ = kendalltau(series1, series2)
        else:
            corr = series1.corr(series2)
        
        return corr if not pd.isna(corr) else 0.0

class TableGenerator:
    """表格生成器类"""
    
    def __init__(self, config: CorrelationConfig, logger: logging.Logger):
        self.config = config
        self.logger = logger
    
    def generate_correlation_table(self, 
                                 result: Dict[str, Union[float, None, int]], 
                                 group_by: List[str], 
                                 var1: str, 
                                 var2: str) -> str:
        """根据分组维度生成相应的表格格式"""
        if not group_by:
            return self._generate_simple_table(result, var1, var2)
        elif len(group_by) == 1:
            return self._generate_1d_table(result, group_by)
        elif len(group_by) == 2:
            return self._generate_2d_table(result, group_by)
        else:
            return self._generate_hierarchical_table(result, group_by)
    
    def generate_correlation_matrix_table(self, 
                                        matrix_result: Dict[str, Any]) -> str:
        """生成相关性矩阵表格"""
        variables = matrix_result["variables"]
        method = matrix_result.get("method", "pearson")
        
        if "groups" in matrix_result:
            return self._generate_grouped_matrix_table(matrix_result["groups"], variables, method)
        else:
            return self._generate_simple_matrix_table(matrix_result["matrix"], variables, method)
    
    def _generate_simple_matrix_table(self, 
                                    matrix: Dict[Tuple[str, str], Union[float, None]], 
                                    variables: List[str],
                                    method: str) -> str:
        """生成简单相关性矩阵表格（无分组）"""
        title = f"相关性矩阵 (方法: {method})\n\n"
        
        md = "| 变量 |"
        for var in variables:
            md += f" {var} |"
        md += "\n|"
        for _ in range(len(variables) + 1):
            md += "---|"
        md += "\n"
        
        for row_var in variables:
            md += f"| {row_var} |"
            for col_var in variables:
                value = matrix.get((row_var, col_var), None)
                formatted_value = self._format_matrix_value(value)
                md += f" {formatted_value} |"
            md += "\n"
        
        return title + md
    
    def _generate_grouped_matrix_table(self, 
                                     groups: Dict[str, Dict[Tuple[str, str], Union[float, None]]], 
                                     variables: List[str],
                                     method: str) -> str:
        """生成分组相关性矩阵表格"""
        title = f"分组相关性矩阵 (方法: {method})\n\n"
        
        md = title
        
        sorted_group_keys = sorted(groups.keys())
        
        for group_key in sorted_group_keys:
            matrix = groups[group_key]
            
            md += f"**{group_key}**\n\n"
            
            md += "| 变量 |"
            for var in variables:
                md += f" {var} |"
            md += "\n|"
            for _ in range(len(variables) + 1):
                md += "---|"
            md += "\n"
            
            for row_var in variables:
                md += f"| {row_var} |"
                for col_var in variables:
                    value = matrix.get((row_var, col_var), None)
                    formatted_value = self._format_matrix_value(value)
                    md += f" {formatted_value} |"
                md += "\n"
            
            md += "\n"
        
        return md
    
    def _format_matrix_value(self, value: Union[float, None, int]) -> str:
        """格式化矩阵中的相关性值"""
        if value is None:
            return "数据不足"
        elif value == self.config.data_insufficient_flag:
            return "数据不足"
        elif isinstance(value, float):
            if value == 1.0:
                return "1.000"
            else:
                return f"{value:.3f}"
        else:
            return str(value)
    
    def _generate_simple_table(self, result: Dict, var1: str, var2: str) -> str:
        """生成简单表格"""
        value = list(result.values())[0]
        corr_value = self._format_correlation_value(value)
        return f"| 变量组合 | 相关性 |\n|---|---|\n| {var1} vs {var2} | {corr_value} |\n"
    
    def _generate_1d_table(self, result: Dict, group_by: List[str]) -> str:
        """生成一维分组表格"""
        md = f"| {group_by[0]} | 相关性 |\n|---|---|\n"
        
        sorted_keys = self._sort_keys(group_by[0], list(result.keys()))
        
        for key in sorted_keys:
            value = result[key]
            corr_value = self._format_correlation_value(value)
            md += f"| {key} | {corr_value} |\n"
        
        return md
    
    def _generate_2d_table(self, result: Dict, group_by: List[str]) -> str:
        """生成二维交叉表格"""
        rows, cols, data_matrix = self._parse_2d_data(result)
        
        sorted_rows = self._sort_keys(group_by[0], list(rows))
        sorted_cols = self._sort_keys(group_by[1], list(cols))
        
        return self._build_2d_table_markdown(sorted_rows, sorted_cols, data_matrix, group_by)
    
    def _generate_hierarchical_table(self, result: Dict, group_by: List[str]) -> str:
        """生成层次化表格"""
        hierarchy = self._build_hierarchy(result)
        
        md = "| " + " | ".join(group_by) + " | 相关性 |\n"
        md += "|" + "---|" * (len(group_by) + 1) + "\n"
        
        def traverse_hierarchy(current_dict: Dict, path: List[str] = None, level: int = 0) -> None:
            if path is None:
                path = []
                
            if level < len(group_by):
                keys = self._sort_keys(group_by[level], list(current_dict.keys()))
            else:
                keys = sorted(current_dict.keys())
            
            for key in keys:
                value = current_dict[key]
                current_path = path + [str(key)]
                
                if isinstance(value, dict):
                    traverse_hierarchy(value, current_path, level + 1)
                else:
                    corr_value = self._format_correlation_value(value)
                    nonlocal md
                    md += "| " + " | ".join(current_path) + f" | {corr_value} |\n"
        
        traverse_hierarchy(hierarchy)
        return md
    
    def _format_correlation_value(self, value: Union[float, None, int]) -> str:
        """统一的相关性值格式化"""
        if value is None:
            return "数据不足"
        elif value == self.config.data_insufficient_flag:
            return "数据不足"
        else:
            return str(value)
    
    def _sort_keys(self, column_name: str, keys: List[str]) -> List[str]:
        """排序逻辑"""
        sort_order = get_sort_order(column_name, keys)
        if sort_order:
            return sorted(keys, key=lambda x: custom_sort_key(x, sort_order))
        else:
            return sorted(keys)
    
    def _parse_2d_data(self, result: Dict) -> Tuple[set, set, Dict]:
        """解析二维数据"""
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
        
        return rows, cols, data_matrix
    
    def _build_2d_table_markdown(self, 
                                rows: List[str], 
                                cols: List[str], 
                                data_matrix: Dict, 
                                group_by: List[str]) -> str:
        """构建二维表格的Markdown"""
        md = f"| {group_by[0]} \\ {group_by[1]} |"
        for col in cols:
            md += f" {col} |"
        md += "\n|"
        for _ in range(len(cols) + 1):
            md += "---|"
        md += "\n"
        
        for row in rows:
            md += f"| {row} |"
            for col in cols:
                value = data_matrix.get((row, col), None)
                corr_value = self._format_correlation_value(value)
                md += f" {corr_value} |"
            md += "\n"
        
        return md
    
    def _build_hierarchy(self, result: Dict) -> Dict:
        """构建层次化数据结构"""
        hierarchy = {}
        
        for key, value in result.items():
            parts = key.split(" - ")
            current = hierarchy
            
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]
            
            last_part = parts[-1] if parts else key
            current[last_part] = value
        
        return hierarchy

class CorrelationManager:
    """相关性分析管理器"""
    
    def __init__(self, config: CorrelationConfig = None):
        self.config = config or CorrelationConfig()
        self.logger = create_logger(app_name="corr", log_dir="./logs").get_logger()
        
        self.data_loader = DataLoader(self.config, self.logger)
        self.column_mapper = ColumnMapper(self.config, self.logger)
        self.derived_field_generator = DerivedFieldGenerator(self.config, self.logger)
        self.correlation_calculator = CorrelationCalculator(self.config, self.logger)
        self.table_generator = TableGenerator(self.config, self.logger)
    
    async def analyze_correlation(self,
                                read_data_param: ReadDataParam,
                                filters: Optional[Dict[str, str]] = None,
                                group_by: Optional[List[str]] = None,
                                correlation_vars: Optional[List[str]] = None,
                                correlation_method: CorrelationMethod = CorrelationMethod.PEARSON) -> str:
        """主要分析流程，支持两变量和多变量相关性分析"""
        try:
            self._validate_inputs(correlation_vars)
            
            self.logger.info("开始加载数据...")
            df = await self.data_loader.load_data(
                read_data_param.read_data_method, 
                read_data_param.read_data_query
            )
            
            self.logger.info("开始列名映射...")
            column_map = await self._get_all_column_mappings(df, filters, group_by, correlation_vars)
            
            self.logger.info("开始生成派生字段...")
            df = await self.derived_field_generator.generate_required_fields(
                df, column_map, self.column_mapper
            )
            
            self.logger.info("应用过滤条件...")
            df_filtered = self._apply_filters(df, filters, column_map)
            
            print(f'当前df为\n{df}')
            
            # 修复映射逻辑，确保处理None值
            correlation_vars_mapped = []
            for v in correlation_vars:
                mapped_val = column_map.get(v)
                if mapped_val is None:
                    raise ValueError(f"无法找到相关性变量的映射: {v}")
                correlation_vars_mapped.append(mapped_val)
            
            group_by_mapped = []
            if group_by:
                for g in group_by:
                    mapped_val = column_map.get(g)
                    if mapped_val is None:
                        raise ValueError(f"无法找到分组变量的映射: {g}")
                    group_by_mapped.append(mapped_val)
            
            # 验证所有映射的列都存在于数据框中
            all_required_cols = correlation_vars_mapped + group_by_mapped
            missing_cols = [col for col in all_required_cols if col not in df_filtered.columns]
            if missing_cols:
                raise ValueError(f"以下列在数据中不存在: {missing_cols}")
            
            if len(correlation_vars_mapped) == 2:
                self.logger.info("开始计算两变量相关性...")
                var1, var2 = correlation_vars_mapped
                
                correlation_result = self.correlation_calculator.calculate_correlation(
                    df_filtered, var1, var2, group_by_mapped, correlation_method
                )
                
                result_table = self.table_generator.generate_correlation_table(
                    correlation_result, group_by_mapped, var1, var2
                )
            else:
                self.logger.info(f"开始计算{len(correlation_vars_mapped)}变量相关性矩阵...")
                
                matrix_result = self.correlation_calculator.calculate_correlation_matrix(
                    df_filtered, correlation_vars_mapped, group_by_mapped, correlation_method
                )
                
                result_table = self.table_generator.generate_correlation_matrix_table(matrix_result)
            
            self.logger.info("相关性分析完成")
            return result_table
            
        except Exception as e:
            self.logger.error(f"相关性分析失败: {e}")
            raise
    
    def _validate_inputs(self, correlation_vars: Optional[List[str]]) -> None:
        """输入验证"""
        if not correlation_vars or len(correlation_vars) < 2:
            raise ValueError("correlation_vars必须包含至少两个变量")
        if len(correlation_vars) > 10:
            raise ValueError("相关性变量过多，最多支持10个变量")
        
        if len(set(correlation_vars)) != len(correlation_vars):
            raise ValueError("correlation_vars中不能包含重复的变量名")
    
    async def _get_all_column_mappings(self, 
                                     df: pd.DataFrame,
                                     filters: Optional[Dict[str, str]],
                                     group_by: Optional[List[str]],
                                     correlation_vars: List[str]) -> Dict[str, Optional[str]]:
        """获取所有需要的列名映射"""
        all_user_keys = set()
        if filters:
            all_user_keys.update(filters.keys())
        if group_by:
            all_user_keys.update(group_by)
        if correlation_vars:
            all_user_keys.update(correlation_vars)
        
        column_map = await self.column_mapper.get_column_mapping(
            tuple(df.columns), tuple(all_user_keys)
        )
        
        # 处理派生字段映射
        derived_user_keys = [k for k, v in column_map.items() if v is None]
        if derived_user_keys:
            self.logger.info(f"需要处理的派生字段: {derived_user_keys}")
            derived_mapped = await self.column_mapper.get_column_mapping(
                tuple(self.derived_field_generator.derived_fields.keys()),
                tuple(derived_user_keys)
            )
            
            # 正确更新column_map
            for user_key, derived_field in derived_mapped.items():
                if derived_field:
                    column_map[user_key] = derived_field
                    self.logger.info(f"派生字段映射: {user_key} -> {derived_field}")
        
        self.logger.info(f"最终列名映射: {column_map}")
        return column_map
    
    def _apply_filters(self, 
                      df: pd.DataFrame, 
                      filters: Optional[Dict[str, str]], 
                      column_map: Dict[str, Optional[str]]) -> pd.DataFrame:
        """应用过滤条件"""
        if not filters:
            return df
        
        df_filtered = df.copy()
        
        for user_col, filter_value in filters.items():
            mapped_col = column_map.get(user_col)
            if not mapped_col:
                raise ValueError(f"无法找到过滤列: {user_col}")
            
            if mapped_col not in df_filtered.columns:
                raise ValueError(f"过滤列不存在于数据中: {mapped_col}")
            
            try:
                df_filtered = df_filtered[df_filtered[mapped_col] == filter_value]
                self.logger.debug(f"应用过滤条件 {mapped_col}={filter_value}，剩余 {len(df_filtered)} 行")
            except Exception as e:
                raise ValueError(f"应用过滤条件失败 {mapped_col}={filter_value}: {str(e)}") from e
        
        return df_filtered

logger = create_logger(app_name="corr", log_dir="./logs").get_logger()
mcp = FastMCP('CorrelationServer')

@mcp.tool()
async def correlation_analysis(
    read_data_param: ReadDataParam,
    filters: Optional[Dict[str, str]] = None,
    group_by: Optional[List[str]] = None,
    correlation_vars: Optional[List[str]] = None,
    correlation_method: str = "pearson",
    # min_sample_size: int = 15,
    # max_file_size_mb: int = 100
) -> str:
    """
    相关性分析工具，支持两变量和多变量相关性分析，可按条件过滤数据、按指定列进行分组，分别计算每组的相关性。请严格传入用户描述的变量名称，不要简化与转换。
    
    :param read_data_param: 数据读取参数
    :param filters: 过滤条件，格式：{列名: 值}
    :param group_by: 分组列，格式：[列名1, 列名2, ...]，可按指定列进行分组，分别计算每组的相关性
    :param correlation_vars: 相关性变量（2-10个变量），格式：[变量1, 变量2, ...]
    :param correlation_method: 相关性计算方法 (pearson/spearman/kendall)
    :return: 相关性分析结果表格（Markdown格式）
    """
    try:
        config = CorrelationConfig(
            # min_sample_size=min_sample_size,
            # max_file_size_mb=max_file_size_mb
        )
        
        try:
            method = CorrelationMethod(correlation_method.lower())
        except ValueError:
            raise ValueError(f"不支持的相关性方法: {correlation_method}. 支持的方法: {[m.value for m in CorrelationMethod]}")
        
        manager = CorrelationManager(config)
        result = await manager.analyze_correlation(
            read_data_param=read_data_param,
            filters=filters,
            group_by=group_by,
            correlation_vars=correlation_vars,
            correlation_method=method
        )
        
        return result
        
    except Exception as e:
        logger.error(f"相关性分析失败: {e}")
        return f"分析失败: {str(e)}"

if __name__ == '__main__':
    mcp.run(transport='sse') 